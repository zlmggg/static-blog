---
title: "nohup / jobs / fg / bg · 后台作业"
description: "nohup 脱离终端运行、& 后台、jobs 看作业、fg/bg 前后台切换、disown。SSH 断开任务不中断，中文详解。"
---

# nohup / jobs / fg / bg · 后台作业

> 命令手册 · [进程与系统](/commands/system/) ｜ 频率：偶尔用
> 跑个长任务怕 SSH 断了就停？nohup + & 让它脱离终端。jobs/fg/bg 管理当前 shell 的后台作业。

## 一句话用途

让命令在后台跑、SSH 断开也不停，并在前后台之间切换作业。

## 高频场景速查

```bash
nohup ./backup.sh > backup.log 2>&1 &   # 脱离终端后台跑，输出进日志
jobs                          # 看当前 shell 的作业
jobs -l                       # 带 PID
fg %1                         # 把作业1调回前台
bg %1                         # 让暂停的作业1后台继续
Ctrl+Z                        # 暂停当前前台作业
disown %1                     # 移除作业（脱离 shell，断连不停）
```

## 各命令职责

| 命令 | 作用 |
|---|---|
| `&` | 放后台运行（仍属当前 shell） |
| `nohup` | 忽略 HUP 信号（终端关闭不停） |
| `jobs` | 列当前 shell 作业 |
| `fg %n` | 作业 n 回前台 |
| `bg %n` | 暂停的作业 n 后台继续 |
| `disown` | 从作业表移除，彻底脱离 |

::: tip nohup 与 & 的区别
`&` 只放后台，终端关闭发 HUP 仍会停；`nohup` 忽略 HUP。两者常组合 `nohup cmd &`。输出默认进 nohup.out，建议显式重定向到日志。
:::

## 运维实战

**后台跑备份**：`nohup ./backup.sh > /var/log/backup.log 2>&1 &`，断 SSH 也继续。
**临时挂起再恢复**：编辑时 Ctrl+Z 挂起 vim，`fg` 回来。
**长任务更推荐 tmux**：nohup 看不到实时交互，[tmux/screen](./screen-tmux) 能随时 attach 回会话，更灵活。

## 相关命令

[screen/tmux](./screen-tmux) · [kill](./kill) · [systemctl](./systemctl-journalctl)（常驻服务用这个）

## 官方文档

- nohup：<https://man7.org/linux/man-pages/man1/nohup.1.html>
- Bash 作业控制：<https://www.gnu.org/software/bash/manual/html_node/Job-Control.html>