---
title: "reboot / shutdown / poweroff · 开关机"
description: "shutdown 定时/取消关机、reboot 重启、poweroff 断电、systemctl 等价命令。生产安全重启注意事项，中文详解。"
---

# reboot / shutdown / poweroff · 开关机

> 命令手册 · [进程与系统](/commands/system/) ｜ 频率：很少用
> 重启看似简单，生产上要先通知、留缓冲、确认服务能自启。shutdown 比直接 reboot 更可控。

## 一句话用途

安全地重启、关机、断电，支持定时与取消。

## 高频场景速查

```bash
sudo shutdown -h +10 "10分钟后维护关机"   # 10分钟后关机并广播通知
sudo shutdown -c                          # 取消计划关机
sudo shutdown -r now                      # 立即重启
sudo reboot                               # 重启（等价）
sudo poweroff                             # 关机断电
sudo systemctl reboot                     # systemd 方式重启
sudo systemctl poweroff                   # systemd 方式关机
```

## 参数详解

### shutdown

| 参数 | 含义 |
|---|---|
| `-h` | 关机（halt/poweroff） |
| `-r` | 重启 |
| `+N` | N 分钟后 |
| `HH:MM` | 指定时刻 |
| `now` | 立即 |
| `-c` | 取消 |
| 消息 | 广播给在线用户 |

## 运维实战

**生产维护重启**：`shutdown -r +5 "系统维护，5分钟后重启"` 给在线用户缓冲，确认无关键任务再执行。
**重启前检查**：确认关键服务 `systemctl is-enabled` 开机自启，避免重启后服务没起来。
**远程重启防失联**：云主机重启前确认控制台/VNC 可用，万一起不来能救。

::: danger 别在业务高峰直接 reboot
直接 reboot 不给缓冲，可能中断正在写的请求/事务。用 shutdown 定时+通知，数据库先优雅停。重启后验证服务与挂载都正常。
:::

## 相关命令

[systemctl](./systemctl-journalctl) · [uptime](./uptime-uname) · [sync](/commands/storage/) · [fsck](/commands/storage/)

## 官方文档

- shutdown：<https://man7.org/linux/man-pages/man8/shutdown.8.html>
- systemctl：<https://www.freedesktop.org/software/systemd/man/latest/systemctl.html>