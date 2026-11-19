---
title: "useradd / usermod / userdel · 账号生命周期"
description: "useradd 建账号（-m -s -G -u）、usermod 改组/锁定/改 shell、userdel 删账号。账号管理参数按频率中文分级，含服务账号最佳实践。"
---

# useradd / usermod / userdel · 账号生命周期

> 命令手册 · [用户与权限](/commands/identity/) ｜ 频率：偶尔用
> 建账号、改账号、删账号。运维给服务建专用账号、给人开权限都从这里开始。

## 一句话用途

创建/修改/删除 Linux 用户账号，控制谁能登录、属于哪些组。

## 高频场景速查

```bash
sudo useradd -m -s /bin/bash rocky            # 建账号（-m 建家目录）
sudo useradd -r -s /sbin/nologin nginx        # 服务账号（-r 系统号，禁登录）
sudo usermod -aG wheel rocky                  # 加附加组（-a 追加，别漏！）
sudo usermod -L rocky                         # 锁定账号
sudo usermod -U rocky                         # 解锁
sudo userdel -r tempuser                      # 删账号连家目录
id rocky                                      # 看 uid/gid/组
```

## 参数详解（按频率分级）

### useradd

| 参数 | 含义 |
|---|---|
| `-m` | 创建家目录 |
| `-s shell` | 登录 shell（/bin/bash 或 /sbin/nologin） |
| `-G 组1,组2` | 附加组 |
| `-g 主组` | 主组 |
| `-u UID` | 指定 UID |
| `-r` | 系统账号（UID<1000，无家目录） |
| `-d 路径` | 指定家目录 |
| `-e 日期` | 账号过期日 |

### usermod

| 参数 | 含义 |
|---|---|
| `-aG 组` | **追加**附加组（漏 -a 会覆盖原组！） |
| `-L` / `-U` | 锁定 / 解锁 |
| `-s shell` | 改 shell |
| `-l 新名` | 改登录名 |

### userdel

| 参数 | 含义 |
|---|---|
| `-r` | 连家目录和邮件一起删 |
| `-f` | 强制（ logged in 也删，慎用） |

::: danger usermod -G 必须配 -a
`usermod -G docker rocky` 会把 rocky 的附加组**覆盖**成只剩 docker，丢掉 wheel 等。加组一定 `usermod -aG docker rocky`。
:::

## 运维实战

**给服务建专用账号**：`useradd -r -s /sbin/nologin appuser`，服务用它跑，不给登录 shell，最小权限。
**给人 sudo 权限**：RHEL 系 `usermod -aG wheel rocky`，Debian 系 `usermod -aG sudo rocky`（见 [sudo](./su-sudo)）。

## 相关命令

[groupadd](./group) · [passwd](./passwd) · [chage](./chage) · [id/whoami](./id-whoami) · [chmod](./chmod)

## 官方文档

- useradd：<https://man7.org/linux/man-pages/man8/useradd.8.html>
- usermod：<https://man7.org/linux/man-pages/man8/usermod.8.html>