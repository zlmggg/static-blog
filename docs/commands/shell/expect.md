---
title: "expect · 自动化交互"
description: "expect 自动应答交互式命令（spawn/expect/send）、ssh 自动登录、批量改密码场景。能用密钥就别用 expect，中文详解。"
---

# expect · 自动化交互

> 命令手册 · [Shell 与脚本](/commands/shell/) ｜ 主题页
> 有些命令非要交互输入（密码、确认），脚本卡住。expect 模拟"看到什么就答什么"。**但能用密钥/免交互就别用它**。

## 一句话用途

自动应答交互式提示，让必须人工输入的命令也能脚本化。

## 基本结构

```tcl
#!/usr/bin/expect -f
set timeout 20
set host [lindex $argv 0]
spawn ssh rocky@$host                 # 启动交互进程
expect {
  "yes/no" { send "yes\r"; exp_continue }   # 首次连接确认
  "password:" { send "$env(SSHPASS)\r" }    # 输密码
}
expect "$ "                           # 等提示符
send "uptime\r"
send "exit\r"
expect eof
```

| 命令 | 含义 |
|---|---|
| `spawn` | 启动要交互的命令 |
| `expect` | 等待匹配的输出 |
| `send` | 发送应答（\r 回车） |
| `exp_continue` | 继续匹配下一轮 |
| `set timeout` | 超时秒数 |
| `interact` | 交还控制权给人 |

## 运维实战

**批量改密码**（无密钥的老设备）：expect 循环 ssh 登录跑 passwd。
**自动确认**：某些安装脚本反复问 yes，expect 自动应答。

::: warning 优先免交互方案
expect 把密码写进脚本/环境，有泄露风险，且匹配脆弱（提示变了就失败）。**首选**：SSH 用[密钥免密](/commands/devtools/ssh-keygen)、命令用 `-y`/`--non-interactive`、配置用预设文件。expect 只是实在没免交互手段时的兜底。
:::

## 相关主题

[ssh-keygen 免密](/commands/devtools/ssh-keygen) · [Ansible](/services/cicd/ansible) · [变量](./variables)

## 官方文档

- expect：<https://core.tcl-lang.org/expect/index>
- man expect：<https://man7.org/linux/man-pages/man1/expect.1.html>