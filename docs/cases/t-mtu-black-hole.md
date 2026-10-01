---
category: 网络
difficulty: 高级
date: 2022-01-14
---

# MTU 黑洞、MSS 不匹配（2022-01-14）

## 现象

服务器能 `ping` 通小包，但 SSH 登录特别慢、HTTP 大页面打不开、小请求正常。
表现很奇怪：

```bash
ping -c 3 目标IP
# 小 ping 通的，延迟正常
```

```bash
ping -s 1472 -c 3 目标IP
# 大包 ping 不通
# PING 10.0.0.2: 1472 data bytes
# --- 10.0.0.2 ping statistics ---
# 3 packets transmitted, 0 packets received, 100.0% packet loss
```

SSH 上去后敲命令回显很慢，`curl` 小页面通，大页面卡死。

## 环境

- 发行版：Ubuntu 20.04.4 LTS
- 内核：`5.4.0-100-generic`
- 网络：服务器之间走 IPSec VPN 隧道，VPN 接口 MTU 1400
- 物理网卡 MTU 1500

## 定位过程

### 1. 用 ping 二分法找 MTU 边界

不分片、指定包大小：

```bash
# 1472 = 1500 - 28 (IP+ICMP头)
ping -s 1472 -M do -c 3 目标IP
# PING 10.0.0.2: 1472 data bytes
# ping: sendto: Message too long

# 逐步减小
ping -s 1400 -M do -c 3 目标IP
# 通了
ping -s 1450 -M do -c 3 目标IP
# 不通
# 找到临界点在 1400~1450 之间
```

`-M do` 表示 Don't Fragment，包太大就直接报错而不是分片。

### 2. 看本机网卡 MTU

```bash
ip link show eth0
# 2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 ...
ip link show tun0
# 3: tun0: <POINTOPOINT,MULTICAST,NOARP,UP,LOWER_UP> mtu 1400 ...
```

物理网卡 1500，但走 VPN 隧道的接口是 1400。

### 3. 看 TCP MSS 协商

```bash
# 抓包看 MSS
tcpdump -i any -nn 'tcp[tcpflags] & tcp-syn != 0'
# 看到 SYN 包里 MSS 选项
# 10.0.0.1.5000 > 10.0.0.2.22: Flags [S], MSS 1460
# 10.0.0.2.22 > 10.0.0.1.5000: Flags [S.], MSS 1460
```

两端都通告 MSS 1460（= 1500 - 40），但中间 VPN 隧道只能过 1400，实际 1460 的包过不去，被丢弃。

### 4. 确认是 PMTU 黑洞

RFC 1191 说路径上某个设备会发 ICMP Frag Needed 告诉两端"包太大"。
但很多防火墙把 ICMP 类型 3 code 4 给挡了，两端收不到，就一直发大包，一直丢——这就是 PMTU 黑洞。

## 根因

两台服务器之间走 IPSec VPN，VPN 隧道开销 100 字节，实际能过的最大包是 1400。
但物理网卡 MTU 1500，TCP 协商 MSS 1460。1460 + 40 = 1500 > 1400，大包过不去。
防火墙又把 ICMP Frag Needed 挡了，两端不知道要缩小，小请求（小包）通，大请求（大包）卡。

## 解决步骤

### 1. 临时止血：降低本机网卡 MTU

```bash
# 临时改
ip link set dev eth0 mtu 1400

# 永久改，Ubuntu 写 /etc/netplan/00-installer-config.yaml
# network:
#   ethernets:
#     eth0:
#       addresses: [...]
#       mtu: 1400
```

改完立刻 SSH 速度正常。

### 2. 正确做法：MSS Clamping（推荐）

不改本机 MTU，在网关上把 TCP SYN 包里的 MSS 改小，让两端协商出合适的 MSS：

```bash
# 在 VPN 网关上加 iptables 规则
iptables -t mangle -A FORWARD -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmtu
# 或直接写死
iptables -t mangle -A FORWARD -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --set-mss 1360
```

`1360 + 40 + 隧道开销 = 1500`，正好。

### 3. 防火墙放行 ICMP Frag Needed

```bash
iptables -A INPUT -p icmp --icmp-type fragmentation-needed -j ACCEPT
```

让 PMTUD 正常工作。

## 验证与预防

- `ping -s 1472 -M do` 不通、`ping -s 1360 -M do` 通。
- SSH 大命令回显快，HTTP 大页面秒开。
- 监控补：不同方向的 MSS 探测、TCP 重传率。
- 告警阈值：TCP 重传率突增可能就是 MTU 问题。
- 记住：**能 ping 通小包但大应用卡，先 ping -s 二分法测 MTU**。

## 相关

- 命令速查：[网络命令速查](/reference/network-commands)
- 网络方向：[TCP 重传率高](/cases/t-tcp-retransmission)
- 网络方向：[连接超时防火墙](/cases/t-connection-timeout-firewall)
- 存储方向：[NFS Stale file handle](/cases/t-nfs-stale-handle)
