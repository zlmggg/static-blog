---
title: "tc · 流量控制"
description: "tc 限速/整形/模拟延迟丢包（netem）、qdisc/class/filter 概念。复现弱网、限制带宽，中文详解。"
---

# tc · 流量控制

> 命令手册 · [网络](/commands/network/) ｜ 频率：很少用
> 限制某接口带宽、模拟弱网（延迟/丢包）测试应用容错——tc（traffic control）干这个。

## 一句话用途

对网卡流量做限速、整形、延迟/丢包模拟。

## 高频场景速查

```bash
# 模拟弱网（测试用）
sudo tc qdisc add dev eth0 root netem delay 100ms 20ms loss 1%
sudo tc qdisc change dev eth0 root netem delay 200ms loss 5%
sudo tc qdisc del dev eth0 root          # 删除恢复

# 限速（TBF）
sudo tc qdisc add dev eth0 root tbf rate 10mbit burst 32kbit latency 400ms
sudo tc qdisc del dev eth0 root

tc qdisc show dev eth0                   # 看当前规则
tc -s qdisc show dev eth0                # 带统计
```

## 核心概念

- **qdisc**（排队规则）：挂在接口上的调度器（netem/tbf/htb/fq_codel）。
- **class**：HTB 等分类别设不同带宽。
- **filter**：把流量分到不同 class（按 IP/端口）。

## netem 参数（弱网模拟）

| 参数 | 含义 |
|---|---|
| `delay 100ms 20ms` | 延迟100±20ms |
| `loss 1%` | 丢包1% |
| `duplicate 0.1%` | 重复包 |
| `reorder` | 乱序 |
| `rate 1mbit` | 限速 |

## 运维实战

**测应用弱网容错**：加 100ms 延迟+1% 丢包，看超时重试/熔断是否正常。
**限制备份带宽**：TBF 限某接口出口，避免占满。
**精细分类限速**：HTB + filter 按 IP/端口给不同带宽（如限制某租户）。

::: danger 远程操作小心
tc 作用在出口，设错可能让 SSH 卡顿/断。先小延迟测试，确认能连再加大。删除 `tc qdisc del dev eth0 root` 恢复。生产限速用 HTB 别用 netem（netem 是测试工具）。
:::

## 相关命令

[ip](./ip-addr-link) · [iperf3](./iperf3) · [ethtool](./ethtool) · [iptables](./iptables)

## 官方文档

- tc：<https://man7.org/linux/man-pages/man8/tc.8.html>
- netem：<https://man7.org/linux/man-pages/man8/tc-netem.8.html>
- LARTC：<https://lartc.org/>