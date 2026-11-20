---
title: "命令手册 · 网络"
description: "连通、端口、DNS、抓包、远程、防火墙与流量，查看与配置并重。"
---

# 网络

> 命令手册 · [返回总览](/commands/) ｜ 本组 31 个页面，按功能分类

## 功能

网络排障有固定套路：先 ping/mtr 看通不通，再 ss 看端口听没听，dig 看解析对不对，tcpdump 抓包看包到没到，最后 firewall-cmd/iptables 看是不是被挡。远程运维靠 ssh/scp/rsync。本组把"诊断"和"配置"两类命令都收齐。

## 类别

### 接口、地址与流量

| 命令 | 用途 |
|---|---|
| [ip-addr-link](./ip-addr-link) | 看清网卡、IP 与 MAC |
| [ifconfig-bridge-networkctl](./ifconfig-bridge-networkctl) | 接口与桥接 |
| [nmcli](./nmcli) | NetworkManager 网络配置 |
| [ethtool](./ethtool) | 网卡速率、双工、丢包与 offload |
| [tc](./tc) | 流量控制 |

### 路由与邻居

| 命令 | 用途 |
|---|---|
| [arp](./arp) | 邻居表 |
| [route](./route) | 路由表（旧） |

### DNS 解析

| 命令 | 用途 |
|---|---|
| [dig](./dig) | 查 DNS 记录 |
| [nslookup-host](./nslookup-host) | DNS 查询 |
| [getent-resolvectl](./getent-resolvectl) | 解析顺序与 hosts 配置 |
| [whois](./whois) | 域名与 IP 归属 |

### 连通与路径

| 命令 | 用途 |
|---|---|
| [ping](./ping) | 连通性测试 |
| [traceroute-mtr](./traceroute-mtr) | 路径追踪 |
| [nc-socat-telnet](./nc-socat-telnet) | 端口与连接测试 |
| [iperf3](./iperf3) | 带宽测试 |
| [nmap](./nmap) | 端口扫描与服务探测 |

### 端口与连接

| 命令 | 用途 |
|---|---|
| [ss](./ss) | 查看端口、连接与进程（替代 netstat） |
| [netstat](./netstat) | 网络统计（旧） |
| [conntrack](./conntrack) | 连接跟踪 |

### 抓包分析

| 命令 | 用途 |
|---|---|
| [tcpdump](./tcpdump) | 命令行抓包 |
| [tshark](./tshark) | 命令行抓包分析 |

### 防火墙

| 命令 | 用途 |
|---|---|
| [iptables](./iptables) | 包过滤规则管理 |
| [nft](./nft) | nftables 防火墙 |
| [firewall-cmd](./firewall-cmd) | firewalld 防火墙 |
| [ufw](./ufw) | Ubuntu 简易防火墙 |
| [ipset](./ipset) | IP 集合 |

### 远程与传输

| 命令 | 用途 |
|---|---|
| [ssh-rsync](./ssh-rsync) | 登录、传文件、端口转发 |
| [scp-sftp](./scp-sftp) | 远程传输 |
| [sshpass](./sshpass) | 非交互 SSH 密码 |
| [curl](./curl) | 万能 HTTP 请求与接口测试 |
| [wget](./wget) | 下载工具 |

::: tip 组织原则
同族命令合并成一页，一条命令只有一个主页；跨组场景用链接指向对应分组。
:::
