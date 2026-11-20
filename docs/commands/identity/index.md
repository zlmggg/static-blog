---
title: "命令手册 · 用户与权限"
description: "账号与组、提权、文件权限与属性、SELinux 与登录审计。"
---

# 用户与权限

> 命令手册 · [返回总览](/commands/) ｜ 本组 14 个页面，按功能分类

## 功能

权限是 Linux 安全的第一道门。这一组既管"谁能登录、谁能提权"（useradd/sudo），也管"谁能读写执行哪个文件"（chmod/chown/ACL），还管 SELinux 这层额外约束。排障时"Permission denied"几乎都绕不开本组。

## 类别

### 账号与组

| 命令 | 用途 |
|---|---|
| [useradd](./useradd) | 账号生命周期 |
| [passwd](./passwd) | 密码管理 |
| [chage](./chage) | 密码过期策略 |
| [group](./group) | 组管理 |
| [id-whoami](./id-whoami) | 身份与在线 |

### 提权

| 命令 | 用途 |
|---|---|
| [su-sudo](./su-sudo) | 提权与授权 |

### 文件权限与属性

| 命令 | 用途 |
|---|---|
| [chmod](./chmod) | 改文件和目录的权限位 |
| [chown-chgrp](./chown-chgrp) | 改属主属组 |
| [umask](./umask) | 默认权限掩码 |
| [acl](./acl) | 细粒度 ACL |
| [chattr-lsattr](./chattr-lsattr) | 文件扩展属性 |

### 安全策略与审计

| 命令 | 用途 |
|---|---|
| [selinux](./selinux) | 强制访问控制 |
| [audit](./audit) | 审计规则 |
| [last](./last) | 登录审计 |

::: tip 组织原则
同族命令合并成一页，一条命令只有一个主页；跨组场景用链接指向对应分组。
:::
