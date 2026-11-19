---
title: "scp / sftp · 远程传输"
description: "scp 远程复制文件/目录、-P 端口/-r 递归/-C 压缩、sftp 交互式传输。与 rsync 对比，中文详解。"
---

# scp / sftp · 远程传输

> 命令手册 · [网络](/commands/network/) ｜ 频率：偶尔用
> 基于 SSH 的安全文件传输。scp 一条命令拷贝，sftp 交互式浏览传输。大量/增量同步用 rsync。

## 一句话用途

通过 SSH 在本地与远程间安全复制文件。

## 高频场景速查

```bash
scp app.tar.gz rocky@10.0.0.11:/opt/         # 本地→远程
scp rocky@10.0.0.11:/var/log/app.log ./      # 远程→本地
scp -r ./dir rocky@10.0.0.11:/opt/           # 递归目录
scp -P 2222 file rocky@10.0.0.11:/opt/       # 指定 SSH 端口（大写 P）
scp -C bigfile rocky@10.0.0.11:/opt/         # 压缩传输
scp rocky@h1:/f rocky@h2:/f                  # 远程→远程
sftp rocky@10.0.0.11                         # 交互式（put/get/ls/cd）
```

## 参数详解

| 参数 | 含义 |
|---|---|
| `-r` | 递归目录 |
| `-P 端口` | SSH 端口（**大写**，小写 p 是保留时间） |
| `-C` | 压缩 |
| `-i 密钥` | 指定私钥 |
| `-l 限速` | 限带宽（Kbit/s） |
| `-q` | 静默 |

## scp vs rsync vs sftp

| | scp | rsync | sftp |
|---|---|---|---|
| 增量同步 | 否（全量） | **是** | 否 |
| 交互浏览 | 否 | 否 | 是 |
| 大量/重复同步 | 慢 | 快 | 慢 |
| 简单一次性 | 方便 | 方便 | 繁琐 |

::: tip 大文件/频繁同步用 rsync
scp 每次全量传，rsync 只传差异（[rsync](./ssh-rsync)）。备份/部署频繁同步用 rsync -avz --progress。新版 OpenSSH 的 scp 底层已改用 sftp 协议。
:::

## 运维实战

**部署传包**：`scp -P 22 app.tar.gz rocky@目标:/opt/`。
**拉日志排查**：`scp rocky@目标:/var/log/app.log ./`。
**批量分发**：配合 [ssh-keygen](/commands/devtools/ssh-keygen) 免密 + for/parallel，或直接用 [Ansible copy](/services/cicd/ansible)。

## 相关命令

[ssh/rsync](./ssh-rsync) · [ssh-keygen](/commands/devtools/ssh-keygen) · [wget](./wget) · [Ansible](/services/cicd/ansible)

## 官方文档

- scp：<https://man.openbsd.org/scp>
- sftp：<https://man.openbsd.org/sftp>