---
title: "iperf3 · 带宽测试"
description: "iperf3 测两点间 TCP/UDP 带宽、-R 反向、-P 并行、-u UDP 测丢包抖动。验证网络吞吐与质量，中文详解。"
---

# iperf3 · 带宽测试

> 命令手册 · [网络](/commands/network/) ｜ 频率：很少用
> 两台机器之间到底能跑多少带宽？iperf3 一端起服务一端打流，测 TCP/UDP 吞吐、丢包、抖动。

## 一句话用途

测量两点间网络带宽、丢包率与抖动。

## 高频场景速查

```bash
# 服务端（被测端）
iperf3 -s                          # 起服务（默认5201端口）
iperf3 -s -p 5202                  # 指定端口

# 客户端（打流端）
iperf3 -c 10.0.0.11                # 测 TCP 上行带宽
iperf3 -c 10.0.0.11 -R             # 反向（测下行）
iperf3 -c 10.0.0.11 -P 4           # 4并行流（压满带宽）
iperf3 -c 10.0.0.11 -t 30          # 测30秒
iperf3 -c 10.0.0.11 -u -b 100M     # UDP 100M（测丢包/抖动）
```

## 参数详解

| 参数 | 含义 |
|---|---|
| `-s` | 服务端 |
| `-c 主机` | 客户端连服务端 |
| `-R` | 反向（服务端发） |
| `-P N` | 并行流数 |
| `-t 秒` | 持续时间 |
| `-u` | UDP |
| `-b 带宽` | UDP 目标带宽 |
| `-p 端口` | 端口 |

## 结果解读

- **TCP**：看 sender/receiver 的 Bitrate（实际吞吐）。
- **UDP**：看 Jitter（抖动）、Lost/Total Datagrams（丢包率）。
- 千兆网卡 TCP 应接近 940Mbps；远低于则查链路/网卡/驱动。

## 运维实战

**验收新链路**：两机房 iperf3 测带宽是否达标称专线。
**排查吞吐低**：`-P 4` 多流压测，单流低可能是 TCP 窗口/延迟限制（长肥管道）。
**测 UDP 质量**：`-u -b 目标带宽` 看丢包抖动，语音/视频业务关心。

::: tip 易错点
iperf3 服务端默认只接受一个客户端，测完要重启或 -D 后台。防火墙需放行 5201。测的是两点间，别在业务高峰打满带宽影响生产。
:::

## 相关命令

[ethtool](./ethtool) · [ping/mtr](./traceroute-mtr) · [ss](./ss) · [tc 限速](./tc) · [fio 磁盘](/commands/observe/fio)

## 官方文档

- iperf3：<https://iperf.fr/iperf-doc.php>
- man：<https://man7.org/linux/man-pages/man1/iperf3.1.html>