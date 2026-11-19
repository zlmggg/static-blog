---
title: "ping · 连通性测试"
description: "ping 测 ICMP 连通与延迟、-c 次数/-i 间隔/-s 包大小/-W 超时、丢包率判断。网络排障第一步，中文详解。"
---

# ping · 连通性测试

> 命令手册 · [网络](/commands/network/) ｜ 频率：每天用
> 网络不通先 ping。它发 ICMP 回显请求，看通不通、延迟多大、丢不丢包。

## 一句话用途

测试到目标的网络连通性、往返延迟与丢包率。

## 高频场景速查

```bash
ping 10.0.0.11               # 持续 ping（Ctrl+C 停）
ping -c 4 10.0.0.11          # 发4个包就停
ping -c 4 -i 0.2 10.0.0.11   # 间隔0.2秒（快测）
ping -c 100 -i 0.1 10.0.0.11 # 100包看丢包率
ping -s 1400 10.0.0.11       # 大包（测 MTU/分片）
ping -W 2 10.0.0.11          # 每包超时2秒
ping -6 ipv6.example.com     # IPv6
```

## 参数详解

| 参数 | 含义 |
|---|---|
| `-c N` | 发 N 个包后停 |
| `-i 秒` | 发包间隔（默认1，root 可<0.2） |
| `-s 字节` | 包大小（默认56+8头=64） |
| `-W 秒` | 单包超时 |
| `-w 秒` | 总超时 |
| `-q` | 只看汇总 |
| `-f` |  flood（root，压测慎用） |

## 结果解读

- **time=**：往返延迟（RTT），局域网<1ms，同城几 ms，跨国几十~几百 ms。
- **packet loss**：丢包率，>0 就要查（链路/拥塞/防火墙）。
- **ttl**：经过的路由跳数推断（Linux 默认64，每经一跳减1）。

::: tip ping 不通≠网络不通
很多服务器/防火墙**禁 ICMP**，ping 不通但 TCP 端口通。ping 不通时用 [ss/nc/curl](./nc-socat-telnet) 测具体端口确认。ping 通也不代表应用层正常。
:::

## 运维实战

**分层排查**：先 ping 网关（本地链路）→ ping 远端 IP（路由）→ ping 域名（DNS）。哪步断查哪层。
**测丢包**：`ping -c 200 -i 0.1 目标` 看 loss%，间歇丢包多为拥塞或链路质量。
**测 MTU**：`ping -s 1472 -M do 目标`（不分片），不通说明路径 MTU 小于1500。

## 相关命令

[traceroute/mtr](./traceroute-mtr) · [ip](./ip-addr-link) · [ss](./ss) · [dig](./dig) · [arp](./arp)

## 官方文档

- ping：<https://man7.org/linux/man-pages/man8/ping.8.html>