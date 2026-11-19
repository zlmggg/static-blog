---
title: "命令手册 · 排障观测"
description: "性能瓶颈与异常定位：从系统指标到系统调用、JVM。"
---

# 排障观测

> 命令手册分组 · 返回 [命令手册总览](/commands/)
> 性能瓶颈与异常定位：从系统指标到系统调用、JVM。

## 这类命令解决什么

当"机器卡了/服务慢了"但不知道卡在哪，就用本组。free/vmstat/sar 看 CPU/内存/IO 大盘，iotop/pidstat 定位到进程，lsof/strace 看句柄与系统调用，perf 看热点。Java 业务还要 jstack/jmap。本组是排障训练场的"工具箱"。

## 学习顺序（入门 → 高级）

1. free / vmstat / uptime（先看大盘）
2. top / pidstat / iotop（定位进程）
3. lsof / strace（句柄与系统调用）
4. sar / perf（历史与热点）
5. jstack / jmap（JVM）
6. stress-ng / fio（压测复现）

## 本组命令

### 已就绪

- [bpftrace](./bpftrace)
- [fio](./fio)
- [free](./free)
- [fuser](./fuser)
- [gdb-pstack](./gdb-pstack)
- [glances-atop](./glances-atop)
- [iftop-nethogs](./iftop-nethogs)
- [ionice](./ionice)
- [iotop](./iotop)
- [jvm](./jvm)
- [ldd-strings](./ldd-strings)
- [lsof](./lsof)
- [perf](./perf)
- [pidstat-mpstat](./pidstat-mpstat)
- [pmap-smem](./pmap-smem)
- [proc](./proc)
- [sar](./sar)
- [strace](./strace)
- [stress-ng](./stress-ng)
- [vmstat](./vmstat)

### 规划中（待编写）

`free`、`vmstat`、`pidstat`、`mpstat`、`sar`、`iotop`、`iftop`、`nethogs`、`glances`、`atop`、`dstat`、`nmon`、`lsof`、`fuser`、`strace`、`perf`、`pmap`、`slabtop`、`smem`、`ldd`、`strings`、`gdb / pstack`、`/proc 解读`、`JVM 观测 jstack / jmap / jstat`、`stress-ng`、`fio`、`bpftrace / bcc`、`ionice`

::: tip 覆盖与组织原则
查看检测与操作变更并重；同族命令合并成页（如 fdisk/parted/gdisk → 分区工具）；一条命令只有一个主页，跨组互链。
:::

## 命令页模板

一句话用途 + 频率标记 → 高频场景速查（中文，复制即用）→ 参数详解（`--help` 全量中文化，按"每天用 / 偶尔用 / 很少用"分级，标易错点）→ 运维实战示例 → 相关命令 + 官方文档完整链接。
