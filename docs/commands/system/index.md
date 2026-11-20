---
title: "命令手册 · 进程与系统"
description: "进程、服务、计划任务、开关机、系统信息与内核参数。"
---

# 进程与系统

### 进程查看

::: cmd

| 命令 | 用途 |
|---|---|
| [ps](./ps) | 查看系统里正在跑哪些进程 |
| [top 与 htop](./top) | 实时进程与资源排序 |
| [htop](./htop) | 交互式进程监控 |

:::

### 进程控制与会话

::: cmd

| 命令 | 用途 |
|---|---|
| [kill / pkill / pgrep / killall](./kill) | 进程终止 |
| [nice / renice / taskset](./nice-renice) | 优先级与绑核 |
| [nohup / jobs / fg / bg](./nohup-jobs) | 后台作业 |
| [ulimit](./ulimit) | 资源限制 |
| [tmux / screen](./screen-tmux) | 会话保持 |

:::

### 服务与日志

::: cmd

| 命令 | 用途 |
|---|---|
| [systemctl 与 journalctl](./systemctl-journalctl) | 服务管理与日志排查 |
| [systemd-analyze](./systemd-analyze) | 启动分析 |
| [dmesg](./dmesg) | 内核环形日志 |
| [coredumpctl](./coredumpctl) | 崩溃转储 |

:::

### 计划任务

::: cmd

| 命令 | 用途 |
|---|---|
| [crontab](./crontab) | 配置定时任务 |
| [at](./at) | 一次性计划任务 |

:::

### 系统信息

::: cmd

| 命令 | 用途 |
|---|---|
| [uptime / uname / lscpu](./uptime-uname) | 系统信息 |
| [dmidecode / lscpu](./lscpu-dmidecode) | 硬件信息 |
| [lspci / lsusb / lsmod / modprobe](./lspci-lsmod) | 设备与内核模块 |
| [hostnamectl / localectl](./hostnamectl) | 主机与本地化 |
| [date / timedatectl](./date-timedatectl) | 时间与时区 |
| [which / whereis / type](./which-whereis) | 定位命令 |

:::

### 环境与内核

::: cmd

| 命令 | 用途 |
|---|---|
| [env / export](./env-export) | 环境变量 |
| [sysctl](./sysctl) | 内核参数调优 |
| [chroot](./chroot) | 切换根目录 |

:::

### 开关机

::: cmd

| 命令 | 用途 |
|---|---|
| [reboot / shutdown / poweroff](./power) | 开关机 |

:::
