---
title: "ssh-keygen / ssh-copy-id · 密钥与免密"
description: "ssh-keygen 生成 ed25519/rsa 密钥对、ssh-copy-id 分发公钥免密、改 passphrase、看指纹。批量运维免密登录基础，参数中文分级。"
---

# ssh-keygen / ssh-copy-id · 密钥与免密

> 命令手册 · [开发与效率](/commands/devtools/) ｜ 频率：偶尔用
> 免密登录是批量运维（Ansible/脚本）的前提。生成密钥对、把公钥分发到目标机。

## 一句话用途

生成 SSH 密钥对，把公钥贴到目标机实现免密登录。

## 高频场景速查

```bash
ssh-keygen -t ed25519 -C "ops@control"        # 生成密钥（推荐 ed25519）
ssh-copy-id rocky@10.0.0.11                   # 分发公钥到目标机
ssh rocky@10.0.0.11                           # 之后免密登录
ssh-keygen -lf ~/.ssh/id_ed25519.pub          # 看公钥指纹
ssh-keygen -p -f ~/.ssh/id_ed25519            # 改 passphrase
```

## 参数详解

### ssh-keygen

| 参数 | 含义 |
|---|---|
| `-t ed25519` | 密钥类型（推荐，短且安全） |
| `-t rsa -b 4096` | RSA 4096（兼容老系统） |
| `-C 注释` | 注释（标识用途） |
| `-f 路径` | 指定密钥文件 |
| `-N 短语` | 设 passphrase（空=无密码） |
| `-lf` | 看指纹 |
| `-p` | 改 passphrase |

### ssh-copy-id

| 参数 | 含义 |
|---|---|
| `-i 公钥` | 指定要分发的公钥 |
| `-p 端口` | 目标 SSH 端口 |

## 运维实战

**批量免密**（控制节点到所有目标）：

```bash
ssh-keygen -t ed25519 -N "" -f ~/.ssh/id_ed25519
for ip in 10.0.0.11 10.0.0.12 10.0.0.13; do
  ssh-copy-id -o StrictHostKeyChecking=accept-new rocky@$ip
done
```

之后 Ansible/脚本即可免密批量执行。多机操作统一在控制节点用 ansible。

::: tip 易错点
私钥（id_ed25519）**绝不外传**，权限须 600；公钥（.pub）才分发。生产密钥建议设 passphrase + ssh-agent，别图省事全空密码。
:::

## 相关命令

[ssh/scp/rsync](/commands/network/ssh-rsync) · [Ansible](/services/cicd/ansible) · [git](./git)

## 官方文档

- ssh-keygen：<https://man.openbsd.org/ssh-keygen>
- ssh-copy-id：<https://man.openbsd.org/ssh-copy-id>