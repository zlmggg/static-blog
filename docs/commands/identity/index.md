---
title: "命令手册 · 用户与权限"
description: "账号与组、提权、文件权限与属性、SELinux 与登录审计。"
---

# 用户与权限

> 命令手册分组 · 返回 [命令手册总览](/commands/)
> 账号与组、提权、文件权限与属性、SELinux 与登录审计。

## 这类命令解决什么

权限是 Linux 安全的第一道门。这一组既管"谁能登录、谁能提权"（useradd/sudo），也管"谁能读写执行哪个文件"（chmod/chown/ACL），还管 SELinux 这层额外约束。排障时"Permission denied"几乎都绕不开本组。

## 学习顺序（入门 → 高级）

1. id / whoami / chmod / chown（先懂权限位）
2. useradd / usermod / passwd（账号生命周期）
3. su / sudo / visudo（提权与授权）
4. umask / getfacl / setfacl（默认权限与细粒度 ACL）
5. chattr / lsattr / SELinux（属性与强制访问控制）

## 本组命令

### 已就绪

- [acl](./acl)
- [audit](./audit)
- [chage](./chage)
- [chattr-lsattr](./chattr-lsattr)
- [chmod](./chmod)
- [chown-chgrp](./chown-chgrp)
- [group](./group)
- [id-whoami](./id-whoami)
- [last](./last)
- [passwd](./passwd)
- [selinux](./selinux)
- [su-sudo](./su-sudo)
- [umask](./umask)
- [useradd](./useradd)

### 规划中（待编写）

`useradd / usermod / userdel`、`groupadd / groupmod / gpasswd`、`passwd`、`chage`、`newgrp`、`su`、`sudo`、`visudo`、`id`、`whoami`、`w / who`、`last / lastlog / lastb`、`chmod`、`chown`、`chgrp`、`umask`、`getfacl / setfacl`、`chattr / lsattr`、`getenforce / setenforce`、`semanage / restorecon / chcon`、`auditctl / ausearch`

::: tip 覆盖与组织原则
查看检测与操作变更并重；同族命令合并成页（如 fdisk/parted/gdisk → 分区工具）；一条命令只有一个主页，跨组互链。
:::

## 命令页模板

一句话用途 + 频率标记 → 高频场景速查（中文，复制即用）→ 参数详解（`--help` 全量中文化，按"每天用 / 偶尔用 / 很少用"分级，标易错点）→ 运维实战示例 → 相关命令 + 官方文档完整链接。
