---
title: "tmux 与 screen 命令详解：远程会话保持与多窗口"
description: "本文是 Linux 命令速查 中远程运维工具的补充；tmux 和 screen 解决同一个问题：SSH 断线后，远程机器上的任务不跟着断。 目标：会开会话、会断线重连、会分屏看日志，知道 tmux 和 screen 的按键差异。"
---
# tmux 与 screen 命令详解：远程会话保持与多窗口

> 本文是 [Linux 命令速查](../linux-commands#进程控制) 中远程运维工具的补充；`tmux` 和 `screen` 解决同一个问题：SSH 断线后，远程机器上的任务不跟着断。
> 目标：会开会话、会断线重连、会分屏看日志，知道 tmux 和 screen 的按键差异。

## 一、为什么需要终端复用器

直接 SSH 到服务器跑一个长任务，网络一抖、笔记本合盖、VPN 掉线，SSH 会话断开，前台进程收到 SIGHUP 就没了。`nohup` 能让单个命令忽略 HUP，但不能解决：

- 任务跑起来后想回去看输出；
- 同时开几个窗口看不同日志；
- 分屏一边 `tail -f` 一边执行命令；
- 多人协作看同一个会话。

终端复用器在服务器上常驻一个 server 进程，你的窗口只是“ attach 上去的客户端”；客户端断了，会话和里面的进程还在。

## 二、tmux 基础

### 1. 会话管理

```bash
# 新建一个名为 ops 的会话
tmux new -s ops

# 列出所有会话
tmux ls

# 重新接入
tmux attach -t ops
# 简写
tmux a -t ops

# 从会话里脱离（也可以按 Ctrl-b 再按 d）
tmux detach

# 杀掉整个会话
tmux kill-session -t ops
```

`tmux new -s ops` 进入后，底部会出现状态栏，说明你已经在 tmux 会话里。此时直接关终端窗口，会话仍然存在；下次 `tmux attach -t ops` 就能回到原来的画面。

### 2. 窗口与窗格

tmux 的默认前缀键是 `Ctrl-b`（按下后松开，再按下一个键）。

| 操作 | 按键 / 命令 |
|---|---|
| 新建窗口 | `Ctrl-b c` |
| 下一个/上一个窗口 | `Ctrl-b n` / `Ctrl-b p` |
| 按编号切窗口 | `Ctrl-b 0` … `Ctrl-b 9` |
| 重命名窗口 | `Ctrl-b ,` |
| 关闭当前窗口 | `Ctrl-b &`（会确认） |
| 垂直分屏 | `Ctrl-b %` |
| 水平分屏 | `Ctrl-b "` |
| 在窗格间切换 | `Ctrl-b ↑↓←→` 或 `Ctrl-b o` |
| 当前窗格全屏/还原 | `Ctrl-b z` |
| 关闭当前窗格 | `Ctrl-b x`（会确认） |
| 调整窗格布局 | `Ctrl-b Space` |
| 进入复制模式 | `Ctrl-b [` |

复制模式里用方向键或 `vi` 键位移动，`Space` 开始选择，`Enter` 复制；粘贴用 `Ctrl-b ]`。

### 3. 常用配置

`~/.tmux.conf`：

```tmux
# 鼠标支持：滚轮翻历史、点选窗格
set -g mouse on

# 历史滚动缓冲行数
set -g history-limit 50000

# 窗口和窗格编号从 1 开始
set -g base-index 1
setw -g pane-base-index 1

# 状态栏刷新间隔
set -g status-interval 5

# 重新加载配置：Ctrl-b r
bind r source-file ~/.tmux.conf \; display-message "tmux.conf reloaded"
```

改完在 tmux 里按 `Ctrl-b r`，或退出重进。注意 `set -g mouse on` 在部分终端里会占用鼠标选择，复制时按住 `Shift` 再拖选。

### 4. 把输出落盘

排查时想让 tmux 里的输出同时写文件：

```bash
# 在 tmux 会话里执行，把当前窗格输出追加到日志
tmux pipe-pane -o 'cat >> ~/ops-session.log'

# 关闭 pipe
tmux pipe-pane
```

抓取当前屏幕最后 10000 行：

```bash
tmux capture-pane -S -10000 -p > /tmp/screen.txt
```

这两个命令在脚本里很有用：会话跑完，日志也留下来了。

## 三、screen 基础

`screen` 更老，但很多最小化系统默认就有，SSH 到旧机器时经常只能用它。

```bash
# 新建会话
screen -S ops

# 列出会话
screen -ls

# 重新接入
screen -r ops

# 脱离：Ctrl-a 再按 d
# 在会话里执行 detach
screen -d -r ops   # 从别的终端强制接管
```

screen 的前缀键是 `Ctrl-a`：

| 操作 | 按键 |
|---|---|
| 新建窗口 | `Ctrl-a c` |
| 下一个/上一个窗口 | `Ctrl-a n` / `Ctrl-a p` |
| 窗口列表 | `Ctrl-a "` |
| 关闭当前窗口 | `Ctrl-a k` |
| 水平分屏 | `Ctrl-a S` |
| 垂直分屏 | `Ctrl-a |` |
| 切换分屏区域 | `Ctrl-a Tab` |
| 脱离会话 | `Ctrl-a d` |

screen 的分屏和窗口管理不如 tmux 顺手，日常新机器优先 tmux；只有对方机器没装 tmux、又不能装包时再用 screen。

## 四、tmux 和 screen 怎么选

| 维度 | tmux | screen |
|---|---|---|
| 默认安装 | 较新发行版常见，但不如 screen 普遍 | 很多最小化系统自带 |
| 分屏 | 原生支持好，快捷键统一 | 支持，但操作更绕 |
| 配置 | `~/.tmux.conf`，社区方案多 | `~/.screenrc` |
| 脚本化 | `tmux ls/attach/capture-pane` 好用 | `screen -ls/-r` 够用 |
| 协作 | 支持多客户端 attach 同一会话 | 也支持，但体验一般 |

结论：新环境用 tmux；老系统、临时排障用 screen；不要把两者嵌套在一起开，容易把前缀键搞乱。

## 五、常见坑

1. **前缀键按法不对**：`Ctrl-b` 是“按下再松开”，不是按住不放和 `c` 一起按。
2. **在 tmux 里再开 tmux**：会出现两层状态栏，前缀键要按两次；先 `echo $TMUX` 确认自己在不在会话里。
3. **关终端不等于杀会话**：直接关窗口只是 detach；要结束任务得在会话里 `exit` 或 `tmux kill-session`。
4. **`tmux ls` 看不到会话**：可能用了不同的 socket 名（`tmux -L name`）或不同用户；`ps -ef | grep tmux` 查一下。
5. **复制模式不会用**：先 `Ctrl-b [` 进入复制模式，再移动/选择；直接鼠标拖选在开启 mouse 后可能失效。
6. **screen 的 `Ctrl-a` 和 shell 行首快捷键冲突**：在 screen 里按 `Ctrl-a` 会被 screen 截获，想给 shell 发 `Ctrl-a` 要按两次。
7. **长期会话占资源**：会话里的进程不会自动退出，巡检完记得清理不用的会话。

## 六、最小工作流

```bash
# 1. 上机先开一个会话
tmux new -s ops

# 2. 分屏：左边看日志，右边执行命令
# Ctrl-b %
# Ctrl-b → 切到右边

# 3. 断线后回来
tmux attach -t ops

# 4. 收尾
exit
```

## 官方文档

- [tmux man page](https://man7.org/linux/man-pages/man1/tmux.1.html)
- [GNU Screen 手册](https://www.gnu.org/software/screen/manual/screen.html)
