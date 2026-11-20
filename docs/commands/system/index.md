---
title: "命令手册 · 进程与系统"
description: "进程、服务、计划任务、开关机、系统信息与内核参数。"
---

# 进程与系统

> 命令手册 · [返回总览](/commands/) ｜ 本组 24 个页面，按功能分类

## 功能

这一组管"机器上跑着什么、怎么管它"。systemctl/journalctl 是 systemd 时代的服务与日志入口；ps/top/kill 看进程、止进程；crontab 做定时；sysctl/ulimit 调内核与资源限制。开机慢、服务起不来、僵尸进程都从这里查。

## 类别

### 进程查看

| 命令 | 用途 |
|---|---|
| [ps](./ps) | 查看系统里正在跑哪些进程 |
| [top](./top) | 实时进程与资源排序 |
| [htop](./htop) | 交互式进程监控 |

### 进程控制与会话

| 命令 | 用途 |
|---|---|
| [kill](./kill) | 进程终止 |
| [nice-renice](./nice-renice) | 优先级与绑核 |
| [nohup-jobs](./nohup-jobs) | 后台作业 |
| [ulimit](./ulimit) | 资源限制 |
| [screen-tmux](./screen-tmux) | 会话保持 |

### 服务与日志

| 命令 | 用途 |
|---|---|
| [systemctl-journalctl](./systemctl-journalctl) | 服务管理与日志排查 |
| [systemd-analyze](./systemd-analyze) | 启动分析 |
| [dmesg](./dmesg) | 内核环形日志 |
| [coredumpctl](./coredumpctl) | 崩溃转储 |

### 计划任务

| 命令 | 用途 |
|---|---|
| [crontab](./crontab) | 配置定时任务 |
| [at](./at) | 一次性计划任务 |

### 系统信息

| 命令 | 用途 |
|---|---|
| [uptime-uname](./uptime-uname) | 系统信息 |
| [lscpu-dmidecode](./lscpu-dmidecode) | 硬件信息 |
| [lspci-lsmod](./lspci-lsmod) | 设备与内核模块 |
| [hostnamectl](./hostnamectl) | 主机与本地化 |
| [date-timedatectl](./date-timedatectl) | 时间与时区 |
| [which-whereis](./which-whereis) | 定位命令 |

### 环境与内核

| 命令 | 用途 |
|---|---|
| [env-export](./env-export) | 环境变量 |
| [sysctl](./sysctl) | 内核参数调优 |
| [chroot](./chroot) | 切换根目录 |

### 开关机

| 命令 | 用途 |
|---|---|
| [power](./power) | 开关机 |

::: tip 组织原则
同族命令合并成一页，一条命令只有一个主页；跨组场景用链接指向对应分组。
:::
