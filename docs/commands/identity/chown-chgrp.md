---
title: "chown / chgrp · 改属主属组"
description: "chown 改文件属主/属组、-R 递归、--reference 参照、chgrp 改组。与 chmod 配合管「谁的+什么权限」，参数中文分级。"
---

# chown / chgrp · 改属主属组

> 命令手册 · [用户与权限](/commands/identity/) ｜ 频率：偶尔用
> chmod 管"什么权限"，chown 管"是谁的"。文件属主属组错了，权限位再对也访问不了。

## 一句话用途

改文件/目录的属主和属组，让正确的用户拥有它。

## 高频场景速查

```bash
sudo chown rocky file                # 改属主
sudo chown rocky:devops file         # 改属主+属组
sudo chown :devops file              # 只改属组
sudo chown -R nginx:nginx /var/www   # 递归改（部署常用）
sudo chgrp -R devops /data           # 递归改组
sudo chown --reference=a.txt b.txt   # 照 a 的属主属组设 b
```

## 参数详解

| 参数 | 含义 |
|---|---|
| `用户:组` | 同时改属主属组 |
| `用户.` 或 `用户:` | 改属主并把组设为该用户主组 |
| `:组` | 只改组 |
| `-R` | 递归 |
| `--reference=参照文件` | 照参照设 |
| `-h` | 改符号链接本身（默认改目标） |
| `--from=旧主` | 仅当前属主匹配才改 |

::: danger chown -R 别乱用
`chown -R root:root /` 会改整个系统属主，可能搞坏服务。递归只针对明确目录（如 /var/www），别对 / 或 /etc 乱递归。
:::

## 运维实战

**部署后改属主**：网站文件解压后 `chown -R nginx:nginx /var/www/app`，让 nginx 能读。
**数据目录给服务账号**：`chown -R mysql:mysql /var/lib/mysql`。
**批量对齐属主**：`chown --reference=ref.txt *.conf` 让一批配置属主一致。

## 相关命令

[chmod](./chmod) 权限位 · [group](./group) · [umask](./umask) · [id](./id-whoami)

## 官方文档

- chown：<https://man7.org/linux/man-pages/man1/chown.1.html>
- chgrp：<https://man7.org/linux/man-pages/man1/chgrp.1.html>