---
title: "uptime / uname / lscpu · 系统信息"
description: "uptime 看负载与运行时间、uname 内核/架构、lscpu CPU 拓扑、/etc/os-release 发行版。快速摸清一台机器，中文详解。"
---

# uptime / uname / lscpu · 系统信息

> 命令手册 · [进程与系统](/commands/system/) ｜ 频率：每天用
> 登录一台陌生机器，先 uptime/uname/lscpu 摸清：跑了多久、负载多高、什么内核、几核 CPU。

## 一句话用途

快速了解系统运行时长、负载、内核版本、CPU 与发行版信息。

## 高频场景速查

```bash
uptime                    # 运行时间+负载（1/5/15分钟）
uptime -p                 # 只看运行时长（pretty）
uname -a                  # 全部系统信息
uname -r                  # 内核版本
uname -m                  # 架构（x86_64/aarch64）
lscpu                     # CPU 拓扑（核数/线程/NUMA）
nproc                     # 可用核数
cat /etc/os-release       # 发行版与版本
hostnamectl               # 主机名+系统+内核（见 hostnamectl）
```

## 负载怎么看（重点）

uptime 输出 `load average: 0.5, 1.2, 3.0`（1/5/15 分钟平均）：

- 负载 ≈ 核数：满载但没排队。
- 负载 > 核数：有进程在等 CPU（或等 IO，Linux 负载含 D 状态）。
- 4 核机器负载 4 算满，负载 8 算过载。

::: tip 负载高不一定是 CPU
Linux 负载包含**不可中断睡眠（D 状态，多在等 IO）**的进程。负载高但 CPU 空闲，多半是 IO 瓶颈——用 [vmstat/iostat](/commands/observe/) 看 wa 和磁盘。
:::

## lscpu 关键字段

| 字段 | 含义 |
|---|---|
| `CPU(s)` | 逻辑核总数 |
| `Core(s) per socket` | 每颗物理核数 |
| `Thread(s) per core` | 每核线程（2=超线程） |
| `NUMA node(s)` | NUMA 节点数 |
| `Model name` | CPU 型号 |

## 运维实战

**判断要不要扩容**：负载持续 > 核数且 CPU 忙，加核；wa 高则查 IO。
**编译并行数**：`make -j$(nproc)` 按核数并行。
**确认架构装包**：`uname -m` 是 aarch64 就别下 x86_64 的包。

## 相关命令

[top/htop](./htop) · [free/vmstat](/commands/observe/) · [hostnamectl](./hostnamectl) · [dmidecode](./lscpu-dmidecode)

## 官方文档

- uptime：<https://man7.org/linux/man-pages/man1/uptime.1.html>
- lscpu：<https://man7.org/linux/man-pages/man1/lscpu.1.html>