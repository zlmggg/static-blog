---
title: "coredumpctl · 崩溃转储"
description: "coredumpctl 列/查/导出进程崩溃 core、gdb 分析、core_pattern 配置。排「服务莫名崩溃」，中文详解。"
---

# coredumpctl · 崩溃转储

> 命令手册 · [进程与系统](/commands/system/) ｜ 频率：很少用
> 服务段错误崩溃，systemd 把 core 收进 journal。coredumpctl 找出崩溃记录、导出 core 给 gdb 分析。

## 一句话用途

查看 systemd 收集的进程崩溃转储，导出 core 文件供调试。

## 高频场景速查

```bash
coredumpctl                      # 列所有崩溃记录
coredumpctl list nginx           # 某程序的崩溃
coredumpctl info 1234            # 看某 PID 崩溃详情（含栈）
coredumpctl info nginx           # 最近一次 nginx 崩溃
coredumpctl dump nginx -o core.nginx   # 导出 core 文件
coredumpctl gdb nginx            # 直接进 gdb 调试
```

## 参数详解

| 命令 | 作用 |
|---|---|
| `list` | 列崩溃（时间/PID/信号/程序） |
| `info` | 详情+回溯栈 |
| `dump -o 文件` | 导出 core |
| `gdb` | 调起 gdb 分析 |

## 配置 core 收集

```bash
cat /proc/sys/kernel/core_pattern    # 看 core 去向（|/usr/lib/systemd/systemd-coredump 表示交给 systemd）
ulimit -c unlimited                  # 允许生成 core
```

`/etc/systemd/coredump.conf` 配 Storage=external、ProcessSizeMax 等。

## 运维实战

**服务崩溃定位**：`coredumpctl info nginx` 看信号（SIGSEGV 段错误/SIGABRT 断言）和回溯栈，定位崩在哪。
**导出给开发分析**：`coredumpctl dump app -o /tmp/core.app`，配合二进制与调试符号 gdb 分析。
**看崩溃频率**：`coredumpctl list` 统计某服务反复崩溃的时间规律。

::: tip 易错点
core 可能含敏感数据（内存里的密码/密钥），导出后妥善保管、分析完删除。生产默认 ulimit -c 0 不收 core，排查时临时开。
:::

## 相关命令

[gdb/strace](/commands/observe/) · [dmesg](./dmesg) · [ulimit](./ulimit) · [journalctl](./systemctl-journalctl)

## 官方文档

- coredumpctl：<https://www.freedesktop.org/software/systemd/man/latest/coredumpctl.html>