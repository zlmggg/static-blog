---
title: "/proc 解读 · 一切指标的源头"
description: "/proc 伪文件系统：cpuinfo/meminfo/loadavg/PID/status/fd/limits/net。top/free/ss 的数据都来自这，看懂它排障不靠猜，中文详解。"
---

# /proc 解读 · 一切指标的源头

> 命令手册 · [排障观测](/commands/observe/) ｜ 主题页
> top/free/vmstat/ss 的数据全来自 /proc。它是内核暴露的伪文件系统，直接读它能看到最原始的状态。

## 一句话用途

直接读内核暴露的进程与系统状态，理解上层工具的数据来源。

## 系统级文件

```bash
cat /proc/loadavg          # 负载（uptime 的来源）
cat /proc/meminfo          # 内存详情（free 的来源）
cat /proc/cpuinfo          # CPU 详情
cat /proc/stat             # CPU 累计计数（vmstat 算百分比用）
cat /proc/interrupts       # 中断分布（看网卡中断绑哪核）
cat /proc/net/tcp          # TCP 连接（ss 的来源）
cat /proc/mounts           # 挂载
cat /proc/sys/...          # 可调内核参数（sysctl 的来源）
```

## 进程级（/proc/PID/）

```bash
cat /proc/1234/status      # 进程状态（VmRSS/Threads/State）
cat /proc/1234/limits      # 资源限制（ulimit 实际值）
ls /proc/1234/fd | wc -l   # 打开的文件句柄数
cat /proc/1234/cmdline     # 启动命令（tr '\0' ' '）
cat /proc/1234/environ     # 环境变量
ls -l /proc/1234/cwd       # 工作目录
ls -l /proc/1234/exe       # 可执行文件路径
cat /proc/1234/io          # 进程 IO 计数
cat /proc/1234/maps        # 内存映射
```

## 关键字段

| 文件/字段 | 含义 |
|---|---|
| `status: VmRSS` | 进程常驻内存 |
| `status: State` | R 运行/S 睡眠/D 不可中断/Z 僵尸 |
| `limits: Max open files` | 句柄上限 |
| `fd/` 数量 | 已用句柄 |
| `loadavg` 第4列 | 运行/总进程数 |

## 运维实战

**排句柄泄漏**：`ls /proc/PID/fd | wc -l` 持续增长 = 泄漏，`ls -l /proc/PID/fd` 看开的是什么。
**确认进程实际限制**：`cat /proc/PID/limits` 比 ulimit 准（ulimit 看的是当前 shell）。
**找僵尸进程**：`ps` 看 Z 状态，/proc/PID/status 的 State 确认，杀父进程回收。
**D 状态查 IO**：State=D 的进程在等 IO，cat /proc/PID/wchan 看卡在哪个内核函数。

::: tip 为什么直接读 /proc
工具可能没装、版本不对、或采样有延迟。/proc 永远在、最原始。脚本里取精确值（如句柄数）直接读它最可靠。
:::

## 相关命令

[free](./free) · [vmstat](./vmstat) · [lsof](./lsof) · [ss](/commands/network/ss) · [ulimit](/commands/system/ulimit)

## 官方文档

- proc：<https://man7.org/linux/man-pages/man5/proc.5.html>
- 内核文档：<https://www.kernel.org/doc/html/latest/filesystems/proc.html>