---
title: "logrotate 配置详解：日志轮转、压缩与清理"
description: "logrotate 负责按天、按大小切分日志并压缩清理。本文给出 Nginx、Java 应用的可用配置，说明 copytruncate 的风险、postrotate 重开文件、-d 干跑和常见不生效原因。"
---

# logrotate 配置详解：日志轮转、压缩与清理

> `logrotate` 不负责收集日志，只负责**切分、压缩、删除旧文件**。应用必须配合重开日志文件（`postrotate` 发信号或 `copytruncate`），否则会出现“日志切走了，进程还在写旧 inode，磁盘继续涨”的情况。

## 配置结构

```text
/etc/logrotate.conf          # 全局默认
/etc/logrotate.d/*           # 各服务独立配置，推荐放这里
/var/lib/logrotate/status    # 上次轮转状态，决定“今天要不要切”
```

全局配置里常见默认项：

```conf
weekly
rotate 4
create
dateext
compress
include /etc/logrotate.d
```

服务自己的配置可以覆盖这些默认值。

## Nginx 示例

```conf
/var/log/nginx/*.log {
    daily
    rotate 14
    missingok
    notifempty
    compress
    delaycompress
    sharedscripts
    postrotate
        [ -f /run/nginx.pid ] && kill -USR1 $(cat /run/nginx.pid)
    endscript
}
```

关键项说明：

| 配置 | 作用 |
|---|---|
| `daily` | 每天轮转；也可以 `weekly`、`monthly`、`size 100M` |
| `rotate 14` | 保留 14 份，超出后删除最旧 |
| `missingok` | 日志不存在时不报错 |
| `notifempty` | 空文件不轮转 |
| `compress` | 轮转后 gzip 压缩 |
| `delaycompress` | 下一次轮转再压缩上一个文件，避免刚切完就压缩导致应用写不了 |
| `sharedscripts` | 多个日志匹配时只执行一次 `postrotate` |
| `postrotate ... endscript` | 切完后通知 Nginx 重开日志 |

没有 `/run/nginx.pid` 时，用 `systemctl reload nginx` 也可以，但 reload 会重新加载配置，生产环境更推荐 `USR1` 只重开日志。

## Java 应用示例

Java 应用常用 Logback/Log4j 自己管理日志，如果交给 `logrotate`，必须确认应用支持重开文件。很多应用不支持 `USR1`，只能用 `copytruncate`：

```conf
/opt/app/logs/*.log {
    daily
    rotate 30
    missingok
    notifempty
    compress
    delaycompress
    copytruncate
}
```

`copytruncate` 的工作方式：

1. 先复制当前日志为 `xxx.log-20260101`。
2. 再把原文件截断为 0 字节。
3. 应用继续写同一个 inode，不需要重开文件。

风险：复制和截断之间写入的日志可能丢失；大文件复制会占用额外磁盘和 I/O。能用应用自身滚动（Logback 的 `RollingFileAppender`）时，优先用应用自身滚动，`logrotate` 只做兜底。

## 按大小与按时间组合

```conf
/var/log/app/*.log {
    size 100M
    rotate 10
    compress
    missingok
    notifempty
    create 0640 app app
}
```

`size` 和 `daily` 同时存在时，`logrotate` 会在满足任一条件时轮转；但 `size` 需要 cron 定时检查，不是实时监控。日志增长很快时，单靠 `daily` 可能一天就写满磁盘，要加 `maxsize`：

```conf
daily
maxsize 500M
```

## 常用调试命令

```bash
# 干跑：只打印会做什么，不实际切文件
logrotate -d /etc/logrotate.d/nginx

# 详细输出
logrotate -v /etc/logrotate.d/nginx

# 强制立即轮转（调试用，会真实切文件）
logrotate -f /etc/logrotate.d/nginx

# 指定状态文件，便于测试
logrotate -d -s /tmp/logrotate.status /etc/logrotate.d/nginx
```

`-d` 输出里重点看：

- `considering log /var/log/nginx/access.log`
- `log needs rotating` 还是 `log does not need rotating`
- `rotating pattern: ...` 和 `renaming ...`
- `running postrotate script`

## 常见不生效原因

| 现象 | 原因 | 处理 |
|---|---|---|
| 到了时间没切 | 状态文件记录今天已切过 | 看 `/var/lib/logrotate/status`，用 `-d` 确认 |
| 文件没到大小不切 | `size` 条件未满足 | 加 `maxsize` 或改用 `daily` |
| 切完磁盘还涨 | 应用没重开文件，仍写旧 inode | 加 `postrotate` 发 `USR1`/`HUP`，或改 `copytruncate` |
| 报权限错误 | `logrotate` 以 root 跑，但目录权限/父目录不可写 | 加 `su root adm` 或调整目录权限 |
| 配置被忽略 | `/etc/logrotate.d` 里有语法错误，整份文件被跳过 | `logrotate -d` 看报错 |
| 压缩文件异常 | `delaycompress` 与 `copytruncate` 混用不当 | 确认应用是否支持重开，尽量用应用自身滚动 |

## 与 systemd/journald 的边界

`logrotate` 管的是文件日志，比如 Nginx、应用自定义日志。`journald` 的日志用 `journalctl` 清理，不要在 `logrotate` 里配 `/var/log/journal`：

```bash
journalctl --disk-usage
journalctl --vacuum-size=500M
journalctl --vacuum-time=14d
```

## 官方文档

- [logrotate(8) man page](https://man7.org/linux/man-pages/man8/logrotate.8.html)
- [logrotate 配置示例（man 页附带的 howto）](https://man7.org/linux/man-pages/man8/logrotate.8.html#EXAMPLES)
