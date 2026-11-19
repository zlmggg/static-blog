---
title: "systemctl 与 journalctl 速查：服务管理与日志排查"
description: "本文是 Linux 命令速查 中「服务与日志」的详解。systemd 的原理、unit 文件写法见 进程与服务指南。 官方文档：systemctl ｜ journalctl"
---
# systemctl 与 journalctl 速查：服务管理与日志排查

> 本文是 [Linux 命令速查](/reference/linux-commands#服务与日志-systemd) 中「服务与日志」的详解。systemd 的原理、unit 文件写法见 [进程与服务指南](/guide/linux-process)。
>
> 官方文档：[systemctl](https://www.freedesktop.org/software/systemd/man/latest/systemctl.html) ｜ [journalctl](https://www.freedesktop.org/software/systemd/man/latest/journalctl.html)

## 一、服务生命周期

| 命令 | 作用 | 说明 |
|---|---|---|
| `systemctl status nginx` | 看状态、最近日志、主 PID | 排障第一条命令 |
| `systemctl start nginx` | 启动 | 不设置开机自启 |
| `systemctl stop nginx` | 停止 | 会按 unit 的 `ExecStop` 优雅停 |
| `systemctl restart nginx` | 重启 | 连接会中断 |
| `systemctl reload nginx` | 重载配置 | 不中断连接，需服务支持 `ExecReload` |
| `systemctl enable nginx` | 开机自启 | 只建立软链，不启动 |
| `systemctl disable nginx` | 取消自启 | 不影响当前运行 |
| `systemctl mask nginx` | 禁止启动（含手动） | 比 disable 更彻底，防误起 |
| `systemctl unmask nginx` | 解除 mask | — |
| `systemctl is-active nginx` | 是否运行 | 脚本判断用，输出 `active/inactive/failed` |
| `systemctl is-enabled nginx` | 是否自启 | 输出 `enabled/disabled/masked` |

## 二、查看与排查

| 命令 | 作用 |
|---|---|
| `systemctl list-units --type=service --state=running` | 列出运行中的服务 |
| `systemctl list-units --type=service --state=failed` | 只看失败的服务 |
| `systemctl --failed` | 失败单元快捷入口 |
| `systemctl list-unit-files --type=service` | 所有已安装服务及自启状态 |
| `systemctl cat nginx` | 查看 unit 文件内容（含 drop-in） |
| `systemctl show nginx -p ActiveState,SubState,MainPID` | 只取关键属性 |
| `systemctl daemon-reload` | 改完 unit 文件后必须执行 |
| `systemctl list-timers --all` | 查看 systemd 定时器及下次触发时间 |
| `systemctl list-dependencies nginx` | 查看依赖关系 |

## 三、journalctl 日志

| 命令 | 作用 |
|---|---|
| `journalctl -u nginx` | 看某个服务的日志 |
| `journalctl -u nginx -f` | 实时跟踪 |
| `journalctl -u nginx --since "10 minutes ago"` | 最近 10 分钟 |
| `journalctl -u nginx --since "2026-11-18 09:00" --until "2026-11-18 10:00"` | 指定时间窗 |
| `journalctl -p err -b` | 本次开机以来的 error 及以上 |
| `journalctl -b -1` | 上一次开机的日志（排查重启前） |
| `journalctl -k` | 只看内核日志（等价 `dmesg` 的持久化版） |
| `journalctl -n 100 --no-pager` | 最后 100 行，不分页 |
| `journalctl -o json-pretty -u nginx` | JSON 结构化输出 |
| `journalctl --disk-usage` | 日志占了多少磁盘 |
| `journalctl --vacuum-time=7d` | 只保留 7 天 |
| `journalctl --vacuum-size=500M` | 限制日志总量 |

> 默认 journal 可能只存在内存（`/run/log/journal`），重启即丢。需要持久化时：`mkdir -p /var/log/journal && systemctl restart systemd-journald`，并在 `/etc/systemd/journald.conf` 设 `Storage=persistent`。

## 四、服务起不来的排查顺序

```bash
systemctl status nginx                 # 1. 看 ActiveState、退出码、最近几行日志
systemctl cat nginx                    # 2. 看 ExecStart 路径、User、Environment
journalctl -u nginx -n 100 --no-pager  # 3. 看完整报错
nginx -t                               # 4. 配置类服务先做语法检查
systemctl daemon-reload                # 5. 改过 unit 文件后重载
systemctl restart nginx                # 6. 再启动
```

常见根因：`ExecStart` 路径写错、端口被占用、配置文件语法错、`User` 无权读文件、SELinux 拦截、unit 改了没 `daemon-reload`。

## 五、systemd 定时器（替代 crontab 的一种选择）

```bash
systemctl list-timers --all
systemctl status backup.timer
journalctl -u backup.service --since today
```

unit 组合：`backup.timer` 负责触发，`backup.service` 负责执行。适合需要开机补跑、依赖管理、日志统一进 journal 的场景。传统 `crontab` 仍是最简方案，见 [crontab](/commands/system/crontab)。

## 六、新手易错点

1. **`enable` 不等于 `start`**：开机自启和当前运行是两件事，通常 `systemctl enable --now nginx` 一起做。
2. **`reload` 不是所有服务都支持**：没有 `ExecReload` 的服务会报 `Job type reload is not applicable`，只能 restart。
3. **改了 unit 文件必须 `daemon-reload`**：否则 systemd 还在用旧配置。
4. **`status` 只显示最近 10 行**：真正排错要看 `journalctl -u`，别只盯 status。
5. **journal 不持久化会丢历史**：生产建议开 persistent，并设置 `SystemMaxUse` 上限。
6. **时区不对会导致日志时间错**：先 `timedatectl` 确认，再看日志。

## 七、官方文档与相关

- systemctl 手册：https://www.freedesktop.org/software/systemd/man/latest/systemctl.html
- journalctl 手册：https://www.freedesktop.org/software/systemd/man/latest/journalctl.html
- systemd unit 配置：https://www.freedesktop.org/software/systemd/man/latest/systemd.unit.html
- journald 配置：https://www.freedesktop.org/software/systemd/man/latest/journald.conf.html
- 速查页：[Linux 命令速查](/reference/linux-commands#服务与日志-systemd)
- 进程与服务：[进程与服务指南](/guide/linux-process)
- 定时任务：[crontab](/commands/system/crontab)
