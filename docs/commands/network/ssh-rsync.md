---
title: "SSH 与 rsync 速查：登录、传文件、端口转发"
description: "本文是 Linux 命令速查 中「远程登录与传输」的详解。SSH 加固、密钥体系见 Linux 安全指南。 官方文档：OpenSSH 手册 ｜ ssh_config ｜ rsync 文档"
---
# SSH 与 rsync 速查：登录、传文件、端口转发

> 本文是 [Linux 命令速查](/reference/linux-commands#远程登录与传输-ssh-rsync) 中「远程登录与传输」的详解。SSH 加固、密钥体系见 [Linux 安全指南](/guide/linux-security)。
>
> 官方文档：[OpenSSH 手册](https://www.openssh.com/manual.html) ｜ [ssh_config](https://man.openbsd.org/ssh_config) ｜ [rsync 文档](https://rsync.samba.org/documentation.html)

## 一、ssh 登录

| 命令 | 作用 |
|---|---|
| `ssh user@host` | 默认 22 端口登录 |
| `ssh -p 2222 user@host` | 指定端口 |
| `ssh -i ~/.ssh/id_ed25519 user@host` | 指定私钥 |
| `ssh -v user@host` | 打印握手过程（排障用，`-vvv` 更详细） |
| `ssh -J bastion user@inner` | 经跳板机连接内网（ProxyJump） |
| `ssh -t user@host "sudo su -"` | 强制分配终端执行交互命令 |
| `ssh user@host "df -h"` | 远程执行一条命令后退出 |

## 二、密钥与免密

```bash
ssh-keygen -t ed25519 -C "zlm@ops"      # 生成密钥（推荐 ed25519）
ssh-copy-id -i ~/.ssh/id_ed25519.pub user@host   # 把公钥装到目标机
ssh-add ~/.ssh/id_ed25519               # 交给 ssh-agent 管理
```

权限要求（不满足会直接拒绝）：

```bash
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_ed25519 ~/.ssh/authorized_keys
chmod 644 ~/.ssh/id_ed25519.pub
```

## 三、~/.ssh/config：把常用主机写成别名

```text
Host prod-web
    HostName 203.0.113.10
    User ops
    Port 2222
    IdentityFile ~/.ssh/id_ed25519
    ServerAliveInterval 30

Host inner-db
    HostName 10.0.0.12
    User ops
    ProxyJump prod-web
```

之后直接 `ssh prod-web`、`ssh inner-db` 即可。

## 四、端口转发

| 场景 | 命令 | 说明 |
|---|---|---|
| 本地端口转发 | `ssh -L 8080:127.0.0.1:80 user@host` | 访问本机 8080 → 经 SSH 到目标机的 80 |
| 远程端口转发 | `ssh -R 9000:127.0.0.1:3000 user@host` | 把目标机 9000 转发回你本机的 3000 |
| 动态代理 | `ssh -D 1080 user@host` | 起 SOCKS5 代理，浏览器可指向 127.0.0.1:1080 |
| 保持长连接 | `ssh -N -L 8080:127.0.0.1:80 user@host` | 只转发不执行命令 |

> 排障常用：数据库、Redis 只监听 127.0.0.1 时，用 `-L` 临时打通，不要为了省事把端口暴露到公网。

## 五、scp：简单传文件

```bash
scp file.tar.gz user@host:/tmp/                 # 本地 → 远程
scp user@host:/var/log/app.log ./               # 远程 → 本地
scp -r dir/ user@host:/opt/                     # 递归传目录
scp -P 2222 file user@host:/tmp/                # 指定端口（注意是大写 P）
scp -i ~/.ssh/id_ed25519 file user@host:/tmp/   # 指定私钥
```

## 六、rsync：增量同步（推荐）

| 命令 | 作用 |
|---|---|
| `rsync -avz src/ user@host:/data/` | 增量同步，保留权限/时间，压缩传输 |
| `rsync -avz --delete src/ user@host:/data/` | 让目标与源完全一致（**会删目标多余文件**） |
| `rsync -avz --dry-run --delete src/ user@host:/data/` | 先演练，看会删/传哪些 |
| `rsync -avz --exclude '.git' --exclude 'node_modules' src/ host:/data/` | 排除目录 |
| `rsync -avz --partial --progress big.iso host:/data/` | 断点续传 + 进度 |
| `rsync -avz -e "ssh -p 2222" src/ host:/data/` | 指定 SSH 端口 |
| `rsync -avz --bwlimit=10M src/ host:/data/` | 限速，避免打满带宽 |

**尾部斜杠规则（最容易错）：**

```bash
rsync -av src/ host:/data/   # 同步 src 里的“内容” → /data/
rsync -av src  host:/data/   # 同步 src 这个“目录本身” → /data/src/
```

## 七、常见报错与处理

| 报错 | 原因 | 处理 |
|---|---|---|
| `Permission denied (publickey)` | 公钥没装、权限不对、用户不对 | `ssh-copy-id`；检查 `~/.ssh` 700、私钥 600；`ssh -v` 看用了哪把钥匙 |
| `Host key verification failed` | 目标机重装/换 IP，指纹变了 | 确认新指纹后 `ssh-keygen -R host` 删除旧记录 |
| `Connection refused` | SSH 没起、端口不对、防火墙拦 | `systemctl status sshd`；`ss -lntp \| grep 22`；检查安全组/防火墙 |
| `Connection timed out` | 网络不通或被封 | `ping`、`nc -zv host 22`、`mtr host` 逐步定位 |
| `Too many authentication failures` | agent 里钥匙太多，逐个试被拒 | `ssh -o IdentitiesOnly=yes -i 指定私钥` |
| `rsync: command not found` | 目标机没装 rsync | 两端都安装，或改用 `scp` |

## 八、官方文档与相关

- OpenSSH 手册：https://www.openssh.com/manual.html
- ssh / scp 命令手册：https://man.openbsd.org/ssh ｜ https://man.openbsd.org/scp
- ssh_config：https://man.openbsd.org/ssh_config
- rsync 官方文档：https://rsync.samba.org/documentation.html
- rsync 手册页：https://download.samba.org/pub/rsync/rsync.1
- 速查页：[Linux 命令速查](/reference/linux-commands#远程登录与传输-ssh-rsync)
- SSH 安全加固：[Linux 安全指南](/guide/linux-security)
- 端口与连通性：[网络命令速查](/reference/network-commands)
