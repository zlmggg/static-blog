---
title: "命令手册 · 网络"
description: "连通、端口、DNS、抓包、远程、防火墙与流量，查看与配置并重。"
---

# 网络

### 接口、地址与流量

::: cmd

| 命令 | 用途 |
|---|---|
| [ip addr 与 ip link](./ip-addr-link) | 看清网卡、IP 与 MAC |
| [ifconfig / bridge / networkctl](./ifconfig-bridge-networkctl) | 接口与桥接 |
| [nmcli](./nmcli) | NetworkManager 网络配置 |
| [ethtool](./ethtool) | 网卡速率、双工、丢包与 offload |
| [tc](./tc) | 流量控制 |

:::

### 路由与邻居

::: cmd

| 命令 | 用途 |
|---|---|
| [arp / arping / ip neigh](./arp) | 邻居表 |
| [route](./route) | 路由表（旧） |

:::

### DNS 解析

::: cmd

| 命令 | 用途 |
|---|---|
| [dig](./dig) | 查 DNS 记录 |
| [nslookup / host / getent](./nslookup-host) | DNS 查询 |
| [系统解析配置](./getent-resolvectl) | 解析顺序与 hosts 配置 |
| [whois](./whois) | 域名与 IP 归属 |

:::

### 连通与路径

::: cmd

| 命令 | 用途 |
|---|---|
| [ping](./ping) | 连通性测试 |
| [traceroute / mtr](./traceroute-mtr) | 路径追踪 |
| [nc / socat / telnet](./nc-socat-telnet) | 端口与连接测试 |
| [iperf3](./iperf3) | 带宽测试 |
| [nmap](./nmap) | 端口扫描与服务探测 |

:::

### 端口与连接

::: cmd

| 命令 | 用途 |
|---|---|
| [ss](./ss) | 查看端口、连接与进程（替代 netstat） |
| [netstat](./netstat) | 网络统计（旧） |
| [conntrack](./conntrack) | 连接跟踪 |

:::

### 抓包分析

::: cmd

| 命令 | 用途 |
|---|---|
| [tcpdump](./tcpdump) | 命令行抓包 |
| [tshark](./tshark) | 命令行抓包分析 |

:::

### 防火墙

::: cmd

| 命令 | 用途 |
|---|---|
| [iptables](./iptables) | 包过滤规则管理 |
| [nft](./nft) | nftables 防火墙 |
| [firewall-cmd](./firewall-cmd) | firewalld 防火墙 |
| [ufw](./ufw) | Ubuntu 简易防火墙 |
| [ipset](./ipset) | IP 集合 |

:::

### 远程与传输

::: cmd

| 命令 | 用途 |
|---|---|
| [SSH 与 rsync](./ssh-rsync) | 登录、传文件、端口转发 |
| [scp / sftp](./scp-sftp) | 远程传输 |
| [sshpass](./sshpass) | 非交互 SSH 密码 |
| [curl](./curl) | 万能 HTTP 请求与接口测试 |
| [wget](./wget) | 下载工具 |

:::
