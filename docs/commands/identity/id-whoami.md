---
title: "id / whoami / w / who · 身份与在线"
description: "id 看 uid/gid/组、whoami 当前用户、w/who 谁在线在干什么、users。排「我是谁/谁登着」必备，参数中文分级。"
---

# id / whoami / w / who · 身份与在线

> 命令手册 · [用户与权限](/commands/identity/) ｜ 频率：每天用
> 确认"我以谁的身份在跑、属于哪些组、还有谁登着这台机"。权限排障第一步常是 id。

## 一句话用途

查当前身份与组归属，看谁在线、在做什么。

## 高频场景速查

```bash
id                       # 当前 uid/gid/所有组
id rocky                 # 查指定用户
whoami                   # 当前有效用户名
groups                   # 当前所属组
w                        # 谁在线+在跑什么+负载
who                      # 谁在线（简洁）
who -b                   # 上次启动时间
users                    # 在线用户名列表
```

## 参数详解

### id

| 参数 | 含义 |
|---|---|
| `-u` | 只输出 UID |
| `-g` | 只输出主组 GID |
| `-G` | 所有组 GID |
| `-n` | 配合 -u/-g 输出名字 |
| `-un` | 当前用户名 |

### w / who

| 命令 | 含义 |
|---|---|
| `w` | 在线用户+终端+来源+在跑的命令+负载 |
| `who` | 在线用户+终端+登录时间 |
| `who -r` | 运行级别 |
| `who -b` | 启动时间 |

## 运维实战

**权限排障第一步**：服务报 Permission denied，先 `id` 看跑服务的用户是谁、在不在需要的组里。
**加组后验证**：`usermod -aG docker rocky` 后 `id rocky` 确认 docker 在列（当前会话需重登）。
**查谁在操作**：`w` 看在线用户和正在跑的命令，排查异常登录。

::: tip 易错点
`whoami` 是有效用户（sudo 后变 root），`who am i` 是登录用户。加组后当前 shell 的 `id` 可能还没更新，要重登或 newgrp。
:::

## 相关命令

[useradd](./useradd) · [su/sudo](./su-sudo) · [last](./last) 历史登录 · [chmod](./chmod)

## 官方文档

- id：<https://man7.org/linux/man-pages/man1/id.1.html>
- w：<https://man7.org/linux/man-pages/man1/w.1.html>