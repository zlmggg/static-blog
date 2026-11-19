---
title: "date / timedatectl · 时间与时区"
description: "date 格式化/计算时间、timedatectl 看设时区与 NTP 同步、chrony 校时。日志时间戳与证书有效期都靠时间准，中文详解。"
---

# date / timedatectl · 时间与时区

> 命令手册 · [进程与系统](/commands/system/) ｜ 频率：偶尔用
> 时间不准会坑惨运维：日志对不上、证书误判过期、分布式时序乱。date 取/算时间，timedatectl 管时区与同步。

## 一句话用途

获取/格式化/计算时间，设置时区，确认时间同步状态。

## 高频场景速查

```bash
date                              # 当前时间
date '+%F %T'                     # 2026-11-19 14:30:00
date +%s                          # Unix 时间戳
date -d '2026-11-19' +%s          # 指定日期转时间戳
date -d @1763532600               # 时间戳转日期
date -d '+7 days' '+%F'           # 7天后
date -d 'yesterday' '+%F'         # 昨天
timedatectl                       # 看时区/NTP同步状态
sudo timedatectl set-timezone Asia/Shanghai   # 设时区
sudo timedatectl set-ntp true     # 启 NTP 同步
```

## date 格式符

| 符 | 含义 |
|---|---|
| `%F` | 年-月-日 |
| `%T` | 时:分:秒 |
| `%s` | Unix 时间戳 |
| `%Y %m %d` | 年 月 日 |
| `%H %M %S` | 时 分 秒 |
| `%u` | 星期几（1-7） |

## 时间同步

```bash
timedatectl timesync-status       # systemd-timesyncd 状态
chronyc sources                   # chrony 源（RHEL 默认）
chronyc tracking                  # 偏差
sudo systemctl enable --now chronyd
```

::: warning 生产必须校时
时间漂移会导致日志混乱、Kerberos/证书校验失败、分布式数据不一致。所有节点统一 NTP（chrony），时区统一 Asia/Shanghai 或 UTC。
:::

## 运维实战

**日志按日期切割**：`logfile="app-$(date +%F).log"`。
**算证书剩余天数**：`echo $(( ($(date -d "$expiry" +%s) - $(date +%s)) / 86400 ))`。
**脚本耗时**：`start=$(date +%s); ...; echo $(( $(date +%s) - start ))秒`。

## 相关命令

[uptime](./uptime-uname) · [crontab](./crontab) · [openssl 证书](/commands/devtools/openssl) · [hwclock](./power)

## 官方文档

- date：<https://man7.org/linux/man-pages/man1/date.1.html>
- timedatectl：<https://man7.org/linux/man-pages/man1/timedatectl.1.html>