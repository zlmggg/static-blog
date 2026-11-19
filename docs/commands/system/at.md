---
title: "at · 一次性计划任务"
description: "at 在指定时间执行一次任务、atq 看队列、atrm 删除、batch 空闲时跑。与 crontab 周期任务的区别，中文详解。"
---

# at · 一次性计划任务

> 命令手册 · [进程与系统](/commands/system/) ｜ 频率：很少用
> crontab 是"每天/每周重复"，at 是"某个时间点跑一次"。今晚 2 点执行一次维护脚本，用 at。

## 一句话用途

在未来某个时间点执行一次命令（不重复）。

## 高频场景速查

```bash
at 02:00                          # 交互输入命令，Ctrl+D 结束
at now + 30 minutes               # 30分钟后
at 14:00 2026-11-20               # 指定日期时刻
echo '/opt/backup.sh' | at 02:00  # 非交互
atq                               # 看待执行队列
atrm 3                            # 删除任务3
at -c 3                           # 看任务3的内容
batch                             # 系统空闲时跑（负载低）
```

## 时间表达

| 写法 | 含义 |
|---|---|
| `now + 1 hour` | 1小时后 |
| `02:00` | 今天/明天2点 |
| `midnight` / `noon` | 午夜/中午 |
| `tomorrow` | 明天 |
| `2026-11-20` | 指定日期 |

## at vs crontab

| | at | crontab |
|---|---|---|
| 频率 | 一次 | 周期重复 |
| 场景 | 临时维护 | 日常巡检/备份 |
| 管理 | atq/atrm | crontab -l/-e |

## 运维实战

**一次性夜间维护**：`echo '/opt/migrate.sh >> /var/log/migrate.log 2>&1' | at 02:00`。
**错峰跑重活**：`batch` 让任务在负载低时自动跑，不抢业务资源。

::: tip 易错点
at 需要 atd 服务运行（`systemctl enable --now atd`）。at 任务的环境变量与登录 shell 不同，脚本里用绝对路径。/etc/at.allow / at.deny 控制谁能用。
:::

## 相关命令

[crontab](./crontab) 周期任务 · [systemd timer](./systemctl-journalctl) · [nohup](./nohup-jobs)

## 官方文档

- at：<https://man7.org/linux/man-pages/man1/at.1.html>