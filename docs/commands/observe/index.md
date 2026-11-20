---
title: "命令手册 · 排障观测"
description: "性能瓶颈与异常定位：从系统指标到系统调用、JVM。"
---

# 排障观测

> 命令手册 · [返回总览](/commands/) ｜ 本组 20 个页面，按功能分类

## 功能

当"机器卡了/服务慢了"但不知道卡在哪，就用本组。free/vmstat/sar 看 CPU/内存/IO 大盘，iotop/pidstat 定位到进程，lsof/strace 看句柄与系统调用，perf 看热点。Java 业务还要 jstack/jmap。本组是排障训练场的"工具箱"。

## 类别

### 资源大盘

| 命令 | 用途 |
|---|---|
| [vmstat](./vmstat) | 系统性能大盘 |
| [free](./free) | 内存查看 |
| [/proc](./proc) | 内核指标源头 |
| [glances / atop / dstat](./glances-atop) | 综合监控 |
| [iftop / nethogs](./iftop-nethogs) | 网络流量定位 |

### CPU 与采样

| 命令 | 用途 |
|---|---|
| [perf](./perf) | CPU 热点、调度延迟与性能采样 |
| [pidstat / mpstat](./pidstat-mpstat) | 进程与多核统计 |
| [sar](./sar) | 历史性能回溯 |

### 内存细节

| 命令 | 用途 |
|---|---|
| [pmap / smem / slabtop](./pmap-smem) | 内存细节 |
| [jstack / jmap / jstat](./jvm) | JVM 观测 |

### 磁盘 IO

| 命令 | 用途 |
|---|---|
| [iostat / iotop](./iotop) | IO 性能定位 |
| [fio](./fio) | 磁盘 IO 压测 |
| [ionice](./ionice) | IO 调度优先级 |

### 进程与调用追踪

| 命令 | 用途 |
|---|---|
| [lsof](./lsof) | 查看「哪个进程打开了哪些文件/端口」 |
| [fuser](./fuser) | 查谁占用文件/端口 |
| [strace](./strace) | 跟踪系统调用定位卡顿与报错 |
| [gdb / pstack / strace 补充](./gdb-pstack) | 进程调试 |
| [bpftrace / bcc](./bpftrace) | eBPF 深度观测 |

### 二进制与压测

| 命令 | 用途 |
|---|---|
| [ldd / strings](./ldd-strings) | 二进制分析 |
| [stress-ng](./stress-ng) | 系统压测 |

::: tip 组织原则
同族命令合并成一页，一条命令只有一个主页；跨组场景用链接指向对应分组。
:::
