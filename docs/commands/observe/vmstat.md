---
title: "vmstat · 系统性能大盘"
description: "vmstat 看进程队列 r/b、内存 si/so、IO bi/bo、CPU us/sy/wa/id。一条命令看清瓶颈在 CPU/内存/IO，中文详解。"
---

# vmstat · 系统性能大盘

> 命令手册 · [排障观测](/commands/observe/) ｜ 频率：每天用
> 机器卡了不知道卡哪？vmstat 一屏看清：是 CPU 忙、内存换页、还是 IO 等待。排障第一眼看它。

## 一句话用途

采样系统整体性能：进程队列、内存换页、磁盘 IO、CPU 分布。

## 高频场景速查

```bash
vmstat 2 5               # 每2秒一次，共5次（第一行是开机均值，忽略）
vmstat -w 2              # 宽输出更易读
vmstat -s                # 统计摘要
vmstat -d                # 磁盘统计
```

## 关键列解读（重点）

```text
procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----
 r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st
 2  0      0  1.2g   200m   8.0g    0    0    10    50  300  500 15  5 78  2  0
```

| 列 | 含义 | 异常信号 |
|---|---|---|
| `r` | 等 CPU 的进程数 | > 核数 = CPU 不够 |
| `b` | 不可中断睡眠（等 IO） | 持续 >0 = IO 瓶颈 |
| `si/so` | swap 换入/换出 | 持续 >0 = 内存不足 |
| `bi/bo` | 块设备读/写 | 高 = IO 繁忙 |
| `us` | 用户态 CPU | 高 = 应用计算密集 |
| `sy` | 内核态 CPU | 高 = 系统调用/中断多 |
| `wa` | 等 IO 的 CPU | 高 = IO 瓶颈 |
| `id` | 空闲 | — |
| `st` | 被虚拟化偷走 | 高 = 云主机超卖 |

## 瓶颈判断套路

- **r 高 + us 高**：CPU 不够，应用计算密集 → 加核/优化代码。
- **b 高 + wa 高**：IO 瓶颈 → [iostat/iotop](./iotop) 查磁盘。
- **si/so 持续非0**：内存不足在换页 → 加内存。
- **sy 高**：内核态忙，可能中断/上下文切换多 → 看 in/cs。
- **st 高**：云主机被宿主抢 CPU → 换规格/独享。

## 运维实战

**快速定位**：`vmstat 2` 看几秒，r/b/si/so/wa 哪个异常就往哪查。
**确认 IO 等待**：wa 高 + b 高，转 iostat 看 %util 和 await。

## 相关命令

[free](./free) · [iostat/iotop](./iotop) · [pidstat/mpstat](./pidstat-mpstat) · [sar](./sar) · [top](/commands/system/top)

## 官方文档

- vmstat：<https://man7.org/linux/man-pages/man8/vmstat.8.html>