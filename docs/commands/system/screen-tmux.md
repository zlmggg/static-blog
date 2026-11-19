---
title: "tmux / screen · 会话保持"
description: "tmux 新建/分离/恢复会话、窗口与面板分屏、screen 基础。SSH 断开任务不丢、多窗口运维，中文详解。"
---

# tmux / screen · 会话保持

> 命令手册 · [进程与系统](/commands/system/) ｜ 频率：每天用
> 运维跑长任务/多窗口操作的神器：会话与终端解耦，SSH 断了 attach 回来一切还在。比 nohup 灵活得多。

## 一句话用途

创建可分离/恢复的终端会话，断网不丢任务，一个窗口分屏干多件事。

## tmux 高频速查

```bash
tmux new -s ops              # 建名为 ops 的会话
tmux ls                      # 列会话
tmux attach -t ops           # 恢复会话
tmux kill-session -t ops     # 杀会话
# 会话内快捷键（前缀 Ctrl+b）：
# Ctrl+b d   分离（detach，任务继续）
# Ctrl+b c   新窗口
# Ctrl+b %   左右分屏
# Ctrl+b "   上下分屏
# Ctrl+b 方向键  切面板
# Ctrl+b [   进入滚动/复制模式
```

## screen 基础

```bash
screen -S ops                # 建会话
screen -ls                   # 列会话
screen -r ops                # 恢复
# Ctrl+a d   分离
# Ctrl+a c   新窗口
```

## tmux vs screen

| | tmux | screen |
|---|---|---|
| 分屏 | 强（面板灵活） | 较弱 |
| 脚本化 | 好 | 一般 |
| 默认前缀 | Ctrl+b | Ctrl+a |
| 推荐 | 首选 | 老系统兜底 |

## 运维实战

**长任务不怕断网**：`tmux new -s deploy` 里跑部署，Ctrl+b d 分离，回家 `tmux attach -t deploy` 接着看。
**多机对照**：分屏同时 ssh 几台机器，对比输出。
**批量同步操作**：tmux  synchronize-panes 让输入同时发到所有面板（小心，确认目标一致）。

::: tip 易错点
分离（detach）不是退出——任务还在后台跑。`exit` 或杀会话才真正结束。会话名有意义（ops/deploy），别一堆 unnamed 找不到。
:::

## 相关命令

[nohup/jobs](./nohup-jobs) · [ssh](/commands/network/ssh-rsync) · [Ansible](/services/cicd/ansible)

## 官方文档

- tmux：<https://github.com/tmux/tmux/wiki>
- screen：<https://www.gnu.org/software/screen/manual/>