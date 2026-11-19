---
title: "traceroute / mtr · 路径追踪"
description: "traceroute 看经过的每一跳、mtr 持续统计每跳丢包与延迟。定位「网络卡在哪一跳」，中文详解。"
---

# traceroute / mtr · 路径追踪

> 命令手册 · [网络](/commands/network/) ｜ 频率：偶尔用
> ping 知道通不通，traceroute/mtr 知道**卡在哪一跳**。跨机房/跨国访问慢，逐跳看延迟和丢包。

## 一句话用途

追踪到目标经过的路由跳数，定位延迟/丢包发生在哪一跳。

## 高频场景速查

```bash
traceroute 10.0.0.11         # 逐跳追踪（默认 UDP）
traceroute -I 10.0.0.11      # 用 ICMP（穿透某些防火墙）
traceroute -T -p 443 host    # 用 TCP 443（最贴近真实业务）
traceroute -n 10.0.0.11      # 不解析主机名（快）
mtr 10.0.0.11                # 交互式持续统计每跳
mtr -r -c 100 10.0.0.11      # 报告模式发100包
mtr -T -P 443 host           # TCP 模式
```

## traceroute vs mtr

| | traceroute | mtr |
|---|---|---|
| 方式 | 一次性逐跳 | 持续采样统计 |
| 输出 | 每跳3个探测延迟 | 每跳丢包率+平均/最好/最差延迟 |
| 适合 | 快速看路径 | 定位间歇丢包 |

## 结果解读

- 每跳 `* * *`：该跳不响应探测（可能禁 ICMP/UDP，不一定断）。
- **某跳之后延迟突增/丢包**：问题在那跳或之后链路。
- 中间跳丢包但末跳正常：中间设备限速 ICMP，**不影响转发**，别误判。

::: tip 看末跳不看中间
中间路由器对探测包限速会显示丢包，但只要**最终目标**丢包率低、延迟正常，链路就是好的。判断以末跳为准。
:::

## 运维实战

**跨地域访问慢**：`mtr -r -c 100 目标` 看哪跳延迟突增，定位是本地出口、运营商骨干还是对端机房。
**TCP 业务追踪**：`traceroute -T -p 443` 用业务端口，避免 UDP/ICMP 被挡导致误判。
**DNS 解析慢**：traceroute -n 跳过解析，排除 DNS 干扰。

## 相关命令

[ping](./ping) · [ip/route](./ip-addr-link) · [dig](./dig) · [tcpdump](./tcpdump)

## 官方文档

- traceroute：<https://man7.org/linux/man-pages/man8/traceroute.8.html>
- mtr：<https://man7.org/linux/man-pages/man8/mtr.8.html>