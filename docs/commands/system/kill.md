---
title: "kill / pkill / pgrep / killall · 进程终止"
description: "kill 发信号（TERM/KILL/HUP）、pkill 按名/模式杀、pgrep 查 PID、killall 按名杀。信号语义与优雅退出，参数中文分级。"
---

# kill / pkill / pgrep / killall · 进程终止

> 命令手册 · [进程与系统](/commands/system/) ｜ 频率：每天用
> 止进程不是只有 kill -9。先 TERM 让进程优雅退出，赖着不走再 KILL。按名字批量杀用 pkill。

## 一句话用途

给进程发信号：优雅停止、强制杀死、重载配置。

## 高频场景速查

```bash
kill 1234                  # 发 TERM（默认15），优雅退出
kill -9 1234               # 发 KILL，强制杀（最后手段）
kill -HUP 1234             # 发 HUP，常用来重载配置
pkill nginx                # 按名杀所有 nginx
pkill -f 'python app.py'   # 按完整命令行匹配杀
pgrep -a nginx             # 查 nginx 的 PID+命令
killall nginx              # 按名杀（同 pkill）
```

## 信号语义（重点）

| 信号 | 编号 | 含义 | 能否捕获 |
|---|---|---|---|
| TERM | 15 | 请求退出（默认） | 能，进程可清理后退出 |
| KILL | 9 | 立即杀死 | **不能**，内核直接终止 |
| HUP | 1 | 挂起/重载配置 | 能 |
| INT | 2 | 中断（Ctrl+C） | 能 |
| STOP | 19 | 暂停 | 不能 |
| CONT | 18 | 恢复暂停 | — |

::: danger 别上来就 -9
`kill -9` 不给进程清理机会——可能丢数据、留临时文件、子进程变孤儿。先 `kill`（TERM）等几秒，确认真的卡死再 -9。数据库/有状态服务尤其要优雅停。
:::

## 参数详解

### kill / pkill / pgrep

| 参数 | 含义 |
|---|---|
| `kill -l` | 列所有信号 |
| `kill -信号名 PID` | 发指定信号 |
| `pkill -f` | 匹配完整命令行 |
| `pkill -u 用户` | 杀某用户的进程 |
| `pgrep -a` | 显示命令行 |
| `pgrep -f` | 匹配完整命令行 |
| `pgrep -u` | 按用户查 |

## 运维实战

**重载 nginx 配置**：`kill -HUP $(cat /run/nginx.pid)` 或 `nginx -s reload`。
**杀残留进程**：`pkill -f 'old-script.sh'` 按命令行精确匹配，避免误杀同名。
**先查后杀**：`pgrep -a node` 看清是哪些再 `pkill -f`，别盲杀。

## 相关命令

[ps](./ps) · [top/htop](./htop) · [systemctl](./systemctl-journalctl) · [nohup/jobs](./nohup-jobs)

## 官方文档

- kill：<https://man7.org/linux/man-pages/man1/kill.1.html>
- pkill/pgrep：<https://man7.org/linux/man-pages/man1/pkill.1.html>
- signal：<https://man7.org/linux/man-pages/man7/signal.7.html>