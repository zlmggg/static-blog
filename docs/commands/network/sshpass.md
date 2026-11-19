---
title: "sshpass · 非交互 SSH 密码"
description: "sshpass 给 ssh/scp 自动输密码、-p/-f/-e 三种来源。能用密钥就别用它，安全风险与替代方案，中文详解。"
---

# sshpass · 非交互 SSH 密码

> 命令手册 · [网络](/commands/network/) ｜ 频率：很少用
> 老设备不支持密钥、必须密码登录又要脚本化——sshpass 自动喂密码。**但首选密钥免密**。

## 一句话用途

让 ssh/scp/rsync 在非交互环境自动使用密码认证。

## 高频场景速查

```bash
sshpass -p '请替换为强密码' ssh rocky@10.0.0.11 'uptime'
sshpass -f pass.txt ssh rocky@10.0.0.11          # 从文件读密码
sshpass -e ssh rocky@10.0.0.11                   # 从环境变量 SSHPASS 读
sshpass -p '密码' scp file rocky@10.0.0.11:/opt/
sshpass -p '密码' rsync -avz dir rocky@10.0.0.11:/opt/
```

## 参数详解

| 参数 | 含义 |
|---|---|
| `-p 密码` | 直接给密码（**会进 ps/history，最不安全**） |
| `-f 文件` | 从文件读（文件权限 600） |
| `-e` | 从 SSHPASS 环境变量读 |
| `-P 提示` | 自定义密码提示匹配 |

::: danger 安全风险与替代
`-p` 密码暴露在进程列表和 shell 历史，极不安全。即便 -f/-e 也比密钥弱。**首选 [ssh-keygen 密钥免密](/commands/devtools/ssh-keygen)**；批量用 [Ansible](/services/cicd/ansible)（ansible_password 走 vault 加密）。sshpass 只是无密钥老设备的兜底。
:::

## 运维实战

**临时应急老设备**：`sshpass -f /root/.sshpass ssh ...`，密码文件 chmod 600，用完删。
**正确方向**：尽快给设备配密钥，淘汰 sshpass。脚本里别硬编码密码。

## 相关命令

[ssh-keygen](/commands/devtools/ssh-keygen) · [ssh/rsync](./ssh-rsync) · [expect](/commands/shell/expect) · [Ansible](/services/cicd/ansible)

## 官方文档

- sshpass：<https://sourceforge.net/projects/sshpass/>
- man：<https://man7.org/linux/man-pages/man1/sshpass.1.html>