---
category: 网络
difficulty: 中级
date: 2021-05-11
---

# 网络不通 / 丢包 / 高延迟：ping/mtr 分段定位（2021-05-11）

## 现象

用户反馈访问业务网站很慢，或者偶尔超时。从服务器 A 访问服务器 B（跨机房），`ping` 延迟从正常的 5ms 飙到 200ms，甚至丢包：

```bash
ping -c 10 10.0.0.2
# PING 10.0.0.2: 56 data bytes
# 64 bytes: icmp_seq=0 ttl=64 time=5.1 ms
# 64 bytes: icmp_seq=1 ttl=64 time=210.3 ms
# 64 bytes: icmp_seq=2 ttl=64 time=5.0 ms
# --- 10.0.0.2 ping statistics ---
# 10 packets transmitted, 8 packets received, 20.0% packet loss
# round-trip min/avg/max/stddev = 5.0/80.5/210.3/90.2 ms
```

需要判断到底是哪一段链路出了问题。

## 环境

- 发行版：CentOS Linux release 7.9.2009 (Core)
- 内核：`3.10.0-1160.el7.x86_64`
- 网络：两台服务器跨机房，中间经过三层路由
- 工具：iputils-ping、mtr 0.92

## 定位过程

### 1. 先确认是"完全不通"还是"慢/丢包"

```bash
ping -c 10 目标IP
# 100% loss = 完全不通，去看路由/防火墙
# 部分 loss = 链路质量问题，用 mtr 分段查
# 通但延迟高 = 带宽拥塞或路由绕路
```

### 2. 用 mtr 逐跳看是哪一段丢包

`mtr` 比 `traceroute` 强在它会持续测每一跳的丢包率：

```bash
mtr --report --report-cycles 20 10.0.0.2
```

输出示例：

```
HOST: web-server1         Loss%   Snt   Last   Avg  Best  Wrst StDev
  1.|-- 192.168.1.1        0.0%    20    0.3   0.4   0.2   0.8   0.2
  2.|-- 10.1.0.1           0.0%    20    1.2   1.5   1.0   2.1   0.3
  3.|-- 10.2.0.1          20.0%    20   80.0  75.0  70.0  95.0   8.0
  4.|-- 10.0.0.2           0.0%    20    5.0   5.2   4.8   6.0   0.4
```

**关键技巧**：看 mtr 结果时，**从有丢包的那一跳往后看**。
如果第 3 跳 20% 丢包，但第 4 跳（目标）0% 丢包，那第 3 跳的丢包是它对 ICMP 限速，不是真丢包。
如果第 3 跳 20% 丢包，第 4 跳也 20%，那就是第 3 跳真的在丢包。

### 3. 看路由怎么走的

```bash
ip route get 10.0.0.2
# 10.0.0.2 via 192.168.1.1 dev eth0 src 192.168.1.10
# cache
```

如果路由绕路了（比如去上海的包先绕到广州），延迟自然高。

### 4. 看本机网卡有没有错包

```bash
ip -s link show eth0
# RX: bytes  packets  errors  dropped  overrun  mcast
# TX: bytes  packets  errors  dropped  carrier  collsns
# errors/dropped 不为 0 就要查
```

```bash
ethtool eth0 | grep -i speed
# Speed: 10000Mb/s   确认协商速率对不对
```

### 5. 看 TCP 层有没有重传

```bash
nstat -az | grep -i retrans
# TcpExtTCPRetransFail  1234  0.0
# TcpExtTCPSpuriousDetrans 50  0.0
```

重传率高说明链路真的有丢包，去看 [TCP 重传](/cases/t-tcp-retransmission)。

## 根因

跨机房链路中间的某台路由器（第 3 跳）上联端口被打满，ICMP 和部分业务包被丢。mtr 看到第 3 跳开始 20% 丢包，到目标也 20%，定位到运营商链路问题，报给运营商处理。

## 解决步骤

### 1. 临时止血

- 如果是到某条链路拥塞，临时切备用线路（如果有 BGP/双链路）。
- 业务层加超时和重试，不要让一个请求卡死。

### 2. 彻底修复

- 报给运营商/IDC，提供 mtr 报告和时间点。
- 如果是自己的路由器，查端口带宽：`iftop -i eth0`、`nload`。
- 考虑加 QoS，把重要业务流量优先级提高。

### 3. 长期

- 重要机房之间拉专线。
- 用多线 BGP，单条链路出问题自动切。

## 验证与预防

- 修复后 `mtr --report --report-cycles 50` 全链路 0 丢包，延迟稳定。
- 监控补：黑盒拨测（从外部 ping/mtr 关键节点）、本机房到各业务节点的延迟和丢包率。
- 告警阈值：丢包率 > 1% 持续 1 分钟、延迟 > 50ms 告警。
- 记住：**mtr 看丢包要看"从哪一跳开始往后都丢"，单跳丢包可能是 ICMP 限速**。

## 相关

- 命令速查：[网络命令速查](/reference/network-commands)
- 网络方向：[TCP 重传率高](/cases/t-tcp-retransmission)
- 网络方向：[MTU 黑洞](/cases/t-mtu-black-hole)
- 网络方向：[连接超时 vs Connection refused](/cases/t-connection-timeout-firewall)
