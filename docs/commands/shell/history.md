---
title: "history 与引用 · 复用历史"
description: "history 查看/搜索历史、!! !n !string 复用、Ctrl+R 反向搜索、!$ 上条末参、HISTCONTROL 去重。提升命令行效率中文详解。"
---

# history 与引用 · 复用历史

> 命令手册 · [Shell 与脚本](/commands/shell/) ｜ 主题页
> 敲过的命令别重敲。history 与 ! 引用让你快速复用、搜索历史命令。

## 一句话用途

查看、搜索、复用历史命令，少敲重复的长命令。

## 高频场景速查

```bash
history                  # 看历史
history 10               # 最近10条
!123                     # 执行第123条
!!                       # 执行上一条（sudo !! 补 sudo）
!ssh                     # 执行最近以 ssh 开头的
!$                       # 上一条的最后一个参数
!*                       # 上一条的所有参数
Ctrl+R                   # 反向搜索历史（输入关键字）
```

## 常用引用

| 引用 | 含义 |
|---|---|
| `!!` | 上一条命令 |
| `!n` | 第 n 条 |
| `!-2` | 倒数第2条 |
| `!str` | 最近以 str 开头 |
| `!?str` | 最近含 str |
| `!$` | 上条末参 |
| `!^` | 上条首参 |
| `!*` | 上条全部参数 |
| `^old^new` | 上条替换 old→new 重跑 |

## 实用技巧

```bash
sudo !!                  # 上条忘加 sudo，补上重跑
mkdir /very/long/path && cd !$    # 建目录后 cd 进去（!$=上条末参）
vim /etc/nginx/nginx.conf
nginx -t -c !$           # 复用刚编辑的配置路径
```

## 历史配置

```bash
HISTSIZE=10000           # 内存保留条数
HISTFILESIZE=20000       # 文件保留条数
HISTCONTROL=ignoredups   # 忽略连续重复
HISTTIMEFORMAT='%F %T '  # 带时间戳
shopt -s histappend      # 追加而非覆盖
```

::: tip 易错点
`!str` 可能匹配到意外的旧命令，执行前先 `history | grep str` 确认，或用 Ctrl+R 交互搜索更安全。含敏感信息（密码）的命令会进历史，用 `HISTCONTROL=ignorespace` + 命令前加空格避免记录。
:::

## 相关主题

[变量](./variables) · [fzf 模糊搜历史](/commands/devtools/fzf-parallel-pv)

## 官方文档

- Bash 历史：<https://www.gnu.org/software/bash/manual/html_node/Bash-History-Facilities.html>