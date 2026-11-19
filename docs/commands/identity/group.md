---
title: "groupadd / gpasswd / newgrp · 组管理"
description: "groupadd 建组、groupmod 改名改 GID、gpasswd 管理组成员、newgrp 切换主组。组是批量授权的单位，参数中文分级。"
---

# groupadd / gpasswd / newgrp · 组管理

> 命令手册 · [用户与权限](/commands/identity/) ｜ 频率：偶尔用
> 组是批量授权的单位——给组授权，组里的人都生效。建组、加人、切组。

## 一句话用途

创建用户组、管理组成员、临时切换当前主组。

## 高频场景速查

```bash
sudo groupadd devops                 # 建组
sudo groupadd -g 2000 devops         # 指定 GID
sudo gpasswd -a rocky devops         # 加用户进组
sudo gpasswd -d rocky devops         # 从组移除
sudo groupmod -n ops devops          # 改组名
getent group devops                  # 看组成员
newgrp devops                        # 临时切换主组（当前会话）
```

## 参数详解

### groupadd / groupmod

| 参数 | 含义 |
|---|---|
| `groupadd -g GID` | 指定 GID |
| `groupadd -r` | 系统组 |
| `groupmod -n 新名` | 改组名 |
| `groupmod -g GID` | 改 GID |

### gpasswd

| 参数 | 含义 |
|---|---|
| `-a 用户` | 加成员 |
| `-d 用户` | 删成员 |
| `-M 用户1,用户2` | 批量设成员（覆盖） |
| `-A 用户` | 设组管理员 |

## 运维实战

**按团队授权目录**：建 devops 组，`chgrp -R devops /data && chmod -R 2775 /data`（setgid 让新文件继承组），组内成员都能读写。
**docker 免 sudo**：`gpasswd -a rocky docker`，重新登录后 docker 命令免 sudo（见 [Docker](/services/container/docker/02-部署)）。

::: tip 易错点
加组后**当前会话不生效**，要重新登录或 `newgrp 组名` 切换。`id` 看到的组才是当前生效的。
:::

## 相关命令

[useradd/usermod](./useradd) · [chown/chgrp](./chown-chgrp) · [id](./id-whoami) · [chmod](./chmod)

## 官方文档

- groupadd：<https://man7.org/linux/man-pages/man8/groupadd.8.html>
- gpasswd：<https://man7.org/linux/man-pages/man1/gpasswd.1.html>