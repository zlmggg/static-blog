---
title: "命令手册 · 网络"
description: "连通、端口、DNS、抓包、远程、防火墙与流量，查看与配置并重。"
---

# 网络

> 命令手册分组 · 返回 [命令手册总览](/commands/)
> 连通、端口、DNS、抓包、远程、防火墙与流量，查看与配置并重。

## 这类命令解决什么

网络排障有固定套路：先 ping/mtr 看通不通，再 ss 看端口听没听，dig 看解析对不对，tcpdump 抓包看包到没到，最后 firewall-cmd/iptables 看是不是被挡。远程运维靠 ssh/scp/rsync。本组把"诊断"和"配置"两类命令都收齐。

## 学习顺序（入门 → 高级）

1. ping / mtr / ip（连通与路由）
2. ss / nc（端口与连接）
3. dig / nslookup（DNS）
4. curl / wget（HTTP 验证）
5. ssh / scp / rsync（远程与传输）
6. tcpdump / firewall-cmd / iptables（抓包与防火墙）

## 本组命令

### 已就绪

- [arp](./arp)
- [conntrack](./conntrack)
- [curl](./curl)
- [dig](./dig)
- [ethtool](./ethtool)
- [firewall-cmd](./firewall-cmd)
- [getent-resolvectl](./getent-resolvectl)
- [ifconfig-bridge-networkctl](./ifconfig-bridge-networkctl)
- [ip-addr-link](./ip-addr-link)
- [iperf3](./iperf3)
- [ipset](./ipset)
- [iptables](./iptables)
- [nc-socat-telnet](./nc-socat-telnet)
- [netstat](./netstat)
- [nft](./nft)
- [nmap](./nmap)
- [nmcli](./nmcli)
- [nslookup-host](./nslookup-host)
- [ping](./ping)
- [route](./route)
- [scp-sftp](./scp-sftp)
- [ss](./ss)
- [ssh-rsync](./ssh-rsync)
- [sshpass](./sshpass)
- [tc](./tc)
- [tcpdump](./tcpdump)
- [traceroute-mtr](./traceroute-mtr)
- [tshark](./tshark)
- [ufw](./ufw)
- [wget](./wget)
- [whois](./whois)

### 规划中（待编写）

`ping`、`traceroute / tracepath`、`mtr`、`ip`、`route`、`arp`、`arping`、`ss`、`netstat`、`nc`、`socat`、`telnet`、`dig`、`nslookup`、`host`、`getent`、`resolvectl`、`whois`、`tcpdump`、`tshark`、`ethtool`、`nmcli`、`ifconfig`、`bridge`、`networkctl`、`curl`、`wget`、`ssh`、`scp`、`sftp`、`rsync`、`sshpass`、`firewall-cmd`、`iptables`、`nft`、`ufw`、`ipset`、`conntrack`、`tc`、`iperf3`、`nmap`

::: tip 覆盖与组织原则
查看检测与操作变更并重；同族命令合并成页（如 fdisk/parted/gdisk → 分区工具）；一条命令只有一个主页，跨组互链。
:::

## 命令页模板

一句话用途 + 频率标记 → 高频场景速查（中文，复制即用）→ 参数详解（`--help` 全量中文化，按"每天用 / 偶尔用 / 很少用"分级，标易错点）→ 运维实战示例 → 相关命令 + 官方文档完整链接。
