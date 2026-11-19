---
title: "dmesg · 内核环形日志"
description: "dmesg 看内核日志、-T 人类时间、-l err 过滤级别、--follow 实时、排 OOM/硬件错误/驱动问题。内核级排障第一现场，中文详解。"
---

# dmesg · 内核环形日志

> 命令手册 · [进程与系统](/commands/system/) ｜ 频率：偶尔用
> 进程被莫名杀掉（OOM）、磁盘 IO 错误、网卡驱动异常——这些应用日志看不到，得查内核日志 dmesg。

## 一句话用途

查看内核环形缓冲区日志，定位 OOM、硬件错误、驱动与文件系统问题。

## 高频场景速查

```bash
sudo dmesg -T                  # 人类可读时间戳
sudo dmesg -T | tail -50       # 最近50条
sudo dmesg -l err,crit         # 只看错误及以上
sudo dmesg -T | grep -i oom    # 查 OOM 杀进程
sudo dmesg -T | grep -iE 'error|fail|i/o'   # 查硬件/IO错误
sudo dmesg --follow            # 实时跟踪（类似 tail -f）
sudo dmesg -c                  # 看并清空（慎用）
```

## 参数详解

| 参数 | 含义 |
|---|---|
| `-T` | 时间戳转人类可读 |
| `-l 级别` | 过滤级别（emerg/alert/crit/err/warn/notice/info/debug） |
| `-f 设施` | 过滤设施（kern/user/daemon） |
| `--follow` / `-w` | 实时跟踪 |
| `-c` | 打印后清空 |
| `-s 大小` | 缓冲区大小 |

## 运维实战

**进程被杀查 OOM**：`dmesg -T | grep -i 'killed process'` 看到 `Out of memory: Killed process 1234 (java)`——内存不足内核杀的，加内存或调小 JVM。
**磁盘故障**：`dmesg | grep -i 'i/o error'` 看块设备报错，配合 [smartctl](/commands/storage/smartctl) 查盘健康。
**网卡丢包/驱动**：`dmesg | grep -i eth` 看链路 up/down、驱动报错。

::: tip 易错点
dmesg 是环形缓冲，会被新日志覆盖，老问题查不到要看 /var/log/messages 或 journalctl -k。OOM 记录应用日志里没有，必须查内核日志。
:::

## 相关命令

[journalctl -k](./systemctl-journalctl) · [free/vmstat](/commands/observe/) · [smartctl](/commands/storage/smartctl) · [coredumpctl](./coredumpctl)

## 官方文档

- dmesg：<https://man7.org/linux/man-pages/man1/dmesg.1.html>