---
category: 网络
difficulty: 高级
date: 2023-07-21
---

# TCP 重传率高、拥塞定位（2023-07-21）

## 现象

监控显示业务接口延迟偶尔飙高，错误率上升。服务器 `nstat` 看到 TCP 重传率高：

```bash
nstat -az | grep -i retrans
# TcpExtTCPRetransFail       12345    0.0
# TcpExtTCPRetrans           67890    0.0
# TcpExtTCPSynRetrans       1234     0.0
```

客户端 `ss -s`：

```bash
ss -s
# TCP:   1234 (estab 500, closed 7345, orphaned 10, timewait 300)
# Transport Total IP IP6
# TCP      1500  1200  300
# RACK     50    40    10
# TCPReno  10    8     2
```

业务表现为：接口 P99 从 50ms 涨到 2s，偶发超时。

## 环境

- 发行版：Rocky Linux release 9.2 (Blue Onyx)
- 内核：`5.14.0-284.11.1.el9.x86_64`
- 业务：Nginx 1.24.0 反向代理，后端 MySQL 8.0.33
- 网卡：eth0 万兆，光纤直连

## 定位过程

### 1. 先算重传率

```bash
# 看 TCP 总段数和重传段数
nstat -az | grep -E "Tcp:|TcpExtTCPRetrans"
# Tcp:SegsOut                  1000000    0.0
# TcpExtTCPRetrans              20000     0.0
# 重传率 = 20000/1000000 = 2%，超过 0.5% 就不正常
```

### 2. 看是哪条连接在重传

```bash
# 看每条连接的重传统计
ss -ti state established
```

输出示例（关键看 `retrans:` 和 `rtt:`）：

```
ESTAB  0  500  10.0.0.2:443  10.0.0.5:5555
  cubic wscale:7,7 rto:204 rtt:2.5/1.5 mss:1448 pmtu:1500 rcvmss:1448 advmss:1448 cwnd:10 bytes_sent:10000 bytes_acked:9900 bytes_retrans:500 segs_out:200 segs_in:150 retrans:5/20 rseq/...
```

`retrans:5/20` 表示 20 个段里重传了 5 个。

### 3. 看网卡有没有错包

```bash
ip -s link show eth0
# RX: bytes  packets  errors  dropped  overrun  mcast
# TX: bytes  packets  errors  dropped  carrier  collsns
# errors/dropped/collsns 不为 0 就要查
```

```bash
ethtool -S eth0 | grep -iE "error|drop|crc"
# rx_crc_errors: 100    <- CRC 错误多，线缆或光模块问题
```

### 4. 看软中断分布

```bash
cat /proc/interrupts | grep eth0
# 如果某一队列中断特别高，RSS 没配好
mpstat -P ALL 1
# 看软中断 si 是不是集中在某颗核
```

### 5. 抓包看具体重传

```bash
tcpdump -i eth0 -w /tmp/tcp.pcap host 10.0.0.5 and port 3306
# 然后用 Wireshark 打开，Analyze -> Expert Information 看重传
```

### 6. 区分是"对端慢"还是"链路丢包"

- 如果 `rtt` 很大且波动大，是对端处理慢。
- 如果 `rtt` 正常但 `retrans` 高，是链路丢包。
- 如果 `cwnd`（拥塞窗口）被压得很低，说明内核在降速。

## 根因

机房交换机上联端口光模块老化，导致 TCP 段在传输中损坏，接收方校验和失败丢弃，发送方超时重传。重传率 2%，业务延迟被重传超时（RTO 200ms+）拉高，P99 暴涨。

## 解决步骤

### 1. 临时止血

- 如果是到某个对端重传高，临时切备用线路。
- 应用层加超时和重试，不要让一次重传放大成用户超时。

### 2. 彻底修复：换硬件

```bash
ethtool -S eth0 | grep -i crc
# CRC 错误持续增长 = 光模块/网线问题，换
```

换光模块/网线/交换机端口后，CRC 错误归零，重传率降到 0.1% 以下。

### 3. 优化 TCP 参数（软件层）

`/etc/sysctl.conf`：

```
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
net.ipv4.tcp_congestion_control = bbr
net.core.default_qdisc = fq
```

```bash
sysctl -p
```

开 BBR 拥塞控制，在有一定丢包的链路上吞吐更好。

### 4. 网卡多队列

```bash
# 确认多队列开了
ethtool -l eth0
# 如果 Combined 只有 1，改成和 CPU 核数一致
ethtool -L eth0 combined 8
```

## 验证与预防

- 修复后 `nstat` 重传率 < 0.1%。
- `ethtool -S eth0` 的 CRC 错误不再增长。
- 监控补：TCP 重传率、网卡 CRC 错误数、软中断 CPU 使用率。
- 告警阈值：重传率 > 0.5% 持续 1 分钟、CRC 错误增长。
- 记住：**重传率高先查网卡硬件（CRC/光模块），再查软件参数**。

## 相关

- 命令速查：[网络命令速查](/reference/network-commands)
- 网络方向：[网络不通丢包](/cases/t-net-unreachable-mtr)
- 网络方向：[MTU 黑洞](/cases/t-mtu-black-hole)
- 服务方向：[Nginx 504 Gateway Timeout](/cases/t-nginx-504-timeout)
