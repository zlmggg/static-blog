---
title: "命令手册 · 用户与权限"
description: "账号与组、提权、文件权限与属性、SELinux 与登录审计。"
---

# 用户与权限

### 账号与组

::: cmd

| 命令 | 用途 |
|---|---|
| [useradd / usermod / userdel](./useradd) | 账号生命周期 |
| [passwd](./passwd) | 密码管理 |
| [chage](./chage) | 密码过期策略 |
| [groupadd / gpasswd / newgrp](./group) | 组管理 |
| [id / whoami / w / who](./id-whoami) | 身份与在线 |

:::

### 提权

::: cmd

| 命令 | 用途 |
|---|---|
| [su / sudo / visudo](./su-sudo) | 提权与授权 |

:::

### 文件权限与属性

::: cmd

| 命令 | 用途 |
|---|---|
| [chmod](./chmod) | 改文件和目录的权限位 |
| [chown / chgrp](./chown-chgrp) | 改属主属组 |
| [umask](./umask) | 默认权限掩码 |
| [getfacl / setfacl](./acl) | 细粒度 ACL |
| [chattr / lsattr](./chattr-lsattr) | 文件扩展属性 |

:::

### 安全策略与审计

::: cmd

| 命令 | 用途 |
|---|---|
| [SELinux](./selinux) | 强制访问控制 |
| [auditctl / ausearch](./audit) | 审计规则 |
| [last / lastlog / lastb](./last) | 登录审计 |

:::
