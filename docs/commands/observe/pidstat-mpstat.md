---
title: "pidstat / mpstat · 进程与多核统计"
description: "pidstat 按进程看 CPU/IO/内存/上下文切换、mpstat 看每核 CPU。定位「哪个进程/哪个核」忙，sysstat 套件，中文详解。"
---

# pidstat / mpstat · 进程与多核统计

> 命令手册 · [排障观测](/commands/observe/) ｜ 频率：偶尔用
> top 看整体，pidstat 精确到每个进程的 CPU/IO/内存/上下文切换；mpstat 看每个核是否均衡。

## 一句话用途

按进程采样资源使用，按 CPU 核看负载分布。

## 高频场景速查

```bash
pidstat 2                # 每进程 CPU（需 sysstat）
pidstat -d 2             # 每进程 IO
pidstat -r 2             # 每进程内存（缺页）
pidstat -w 2             # 每进程上下文切换
pidstat -u -p 1234 2     # 只看某进程 CPU
mpstat -P ALL 2          # 每核 CPU 使用率
```

## pidstat 选项

| 选项 | 看什么 |
|---|---|
| `-u` | CPU（默认） |
| `-d` | IO（kB_rd/s kB_wr/s） |
| `-r` | 内存（minflt/s majflt/s VSZ RSS） |
| `-w` | 上下文切换（cswch/s nvcswch/s） |
| `-t` | 线程级 |
| `-p PID` | 指定进程 |

## mpstat 关键列

`%usr %sys %iowait %irq %soft %idle` 每核分开。某核 %soft 高可能是网卡中断集中在那核（看 /proc/interrupts）。

## 运维实战

**找 CPU 高的线程**：`pidstat -t -p PID 2` 看哪个线程忙，配合 [jstack](./jvm) 定位 Java 线程。
**上下文切换过高**：`pidstat -w` 看 nvcswch/s（非自愿切换高=被抢占，CPU 竞争激烈）。
**多核不均衡**：`mpstat -P ALL` 发现一核满其他闲，可能中断绑定或单线程瓶颈。

## 相关命令

[vmstat](./vmstat) · [iostat/iotop](./iotop) · [top/htop](/commands/system/htop) · [sar](./sar) · [perf](./perf)

## 官方文档

- pidstat：<https://man7.org/linux/man-pages/man1/pidstat.1.html>
- mpstat：<https://man7.org/linux/man-pages/man1/mpstat.1.html>