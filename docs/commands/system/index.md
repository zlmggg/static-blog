---
title: "命令手册 · 进程与系统"
description: "进程、服务、计划任务、开关机、系统信息与内核参数。"
---

# 进程与系统

> 命令手册分组 · 返回 [命令手册总览](/commands/)
> 进程、服务、计划任务、开关机、系统信息与内核参数。

## 这类命令解决什么

这一组管"机器上跑着什么、怎么管它"。systemctl/journalctl 是 systemd 时代的服务与日志入口；ps/top/kill 看进程、止进程；crontab 做定时；sysctl/ulimit 调内核与资源限制。开机慢、服务起不来、僵尸进程都从这里查。

## 学习顺序（入门 → 高级）

1. ps / top / kill（进程三件套）
2. systemctl / journalctl（服务与日志）
3. crontab / at（计划任务）
4. uptime / uname / lscpu（系统信息）
5. free / vmstat 见排障观测
6. sysctl / ulimit / reboot（内核参数与开关机）

## 本组命令

### 已就绪

- [at](./at)
- [chroot](./chroot)
- [coredumpctl](./coredumpctl)
- [crontab](./crontab)
- [date-timedatectl](./date-timedatectl)
- [dmesg](./dmesg)
- [env-export](./env-export)
- [hostnamectl](./hostnamectl)
- [htop](./htop)
- [kill](./kill)
- [lscpu-dmidecode](./lscpu-dmidecode)
- [lspci-lsmod](./lspci-lsmod)
- [nice-renice](./nice-renice)
- [nohup-jobs](./nohup-jobs)
- [power](./power)
- [ps](./ps)
- [screen-tmux](./screen-tmux)
- [sysctl](./sysctl)
- [systemctl-journalctl](./systemctl-journalctl)
- [systemd-analyze](./systemd-analyze)
- [top](./top)
- [ulimit](./ulimit)
- [uptime-uname](./uptime-uname)
- [which-whereis](./which-whereis)

### 规划中（待编写）

`ps`、`top`、`htop`、`kill / pkill / killall / pgrep`、`nice / renice`、`nohup`、`jobs / fg / bg`、`systemctl`、`journalctl`、`crontab`、`at`、`reboot / shutdown / poweroff`、`uptime`、`uname`、`hostnamectl`、`date / timedatectl`、`dmesg`、`sysctl`、`ulimit`、`lscpu`、`dmidecode`、`lspci / lsusb`、`lsmod / modprobe`、`env / export`、`screen / tmux`、`which / whereis`、`taskset`、`systemd-analyze`、`coredumpctl`、`localectl`、`chroot`

::: tip 覆盖与组织原则
查看检测与操作变更并重；同族命令合并成页（如 fdisk/parted/gdisk → 分区工具）；一条命令只有一个主页，跨组互链。
:::

## 命令页模板

一句话用途 + 频率标记 → 高频场景速查（中文，复制即用）→ 参数详解（`--help` 全量中文化，按"每天用 / 偶尔用 / 很少用"分级，标易错点）→ 运维实战示例 → 相关命令 + 官方文档完整链接。
