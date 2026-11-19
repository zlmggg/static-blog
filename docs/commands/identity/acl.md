---
title: "getfacl / setfacl · 细粒度 ACL"
description: "ACL 突破「属主/组/其他」三段限制，给单个用户/组单独授权。getfacl 查看、setfacl 设/-x 删/默认 ACL，参数中文分级。"
---

# getfacl / setfacl · 细粒度 ACL

> 命令手册 · [用户与权限](/commands/identity/) ｜ 频率：很少用
> 传统权限只有"属主/属组/其他"三段。要让"用户 A 可写、用户 B 只读、其他人无"，三段不够，用 ACL。

## 一句话用途

给单个用户或组单独设权限，突破三段式限制。

## 高频场景速查

```bash
getfacl file                       # 看 ACL
sudo setfacl -m u:rocky:rw file    # 给 rocky 读写
sudo setfacl -m g:devops:r file    # 给 devops 组读
sudo setfacl -x u:rocky file       # 删 rocky 的 ACL
sudo setfacl -b file               # 清空所有 ACL
sudo setfacl -R -m u:app:rwx /data # 递归授权
sudo setfacl -d -m u:app:rwx /data # 默认 ACL（新文件继承）
```

## 参数详解

### setfacl

| 参数 | 含义 |
|---|---|
| `-m` | 修改/添加 ACL 条目 |
| `-x` | 删除指定条目 |
| `-b` | 清空全部 ACL |
| `-R` | 递归 |
| `-d` | 设默认 ACL（目录内新建继承） |
| `u:名:权限` | 用户条目 |
| `g:名:权限` | 组条目 |

### getfacl

输出含 `user::`（属主）、`user:名:`（额外用户）、`group::`、`mask::`、`other::`。`ls -l` 权限位末尾有 `+` 表示有 ACL。

::: tip mask 的作用
ACL 的 mask 限制"额外用户/组"的最大权限。setfacl 设了 rw 但 mask 是 r，实际只有 r。chmod 改组权限位会联动改 mask，注意。
:::

## 运维实战

**多用户共享目录**：属主 nginx，但要让 deploy 用户也能写——`setfacl -m u:deploy:rwx /var/www`，不动属主。
**新文件自动继承**：`setfacl -d -m g:devops:rwx /data`，目录里新建文件 devops 组自动有权。

## 相关命令

[chmod](./chmod) · [chown](./chown-chgrp) · [umask](./umask) · [group](./group)

## 官方文档

- setfacl：<https://man7.org/linux/man-pages/man1/setfacl.1.html>
- acl：<https://man7.org/linux/man-pages/man5/acl.5.html>