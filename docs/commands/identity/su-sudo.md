---
title: "su / sudo / visudo · 提权与授权"
description: "su 切换用户、sudo 临时提权、visudo 安全编辑 sudoers、最小化授权（命令级/NOPASSWD）、wheel 组。提权安全中文详解。"
---

# su / sudo / visudo · 提权与授权

> 命令手册 · [用户与权限](/commands/identity/) ｜ 频率：每天用
> 日常别用 root 登录，需要时 sudo 提权。sudo 能精确授权"某人只能跑某命令"，比给 root 密码安全得多。

## 一句话用途

切换用户身份、临时以 root 执行命令、安全地配置谁有权提权。

## 高频场景速查

```bash
su - rocky                 # 切到 rocky（- 加载其环境）
sudo systemctl restart nginx    # 单条命令提权
sudo -i                    # 切到 root 交互 shell
sudo -u appuser whoami     # 以指定用户执行
sudo -l                    # 看自己有哪些 sudo 权限
sudo visudo                # 安全编辑 sudoers（带语法校验）
```

## su vs sudo

| | su | sudo |
|---|---|---|
| 需要的密码 | 目标用户的 | 自己的 |
| 授权粒度 | 整个身份 | 可精确到命令 |
| 审计 | 难追溯 | 每条记日志 |
| 推荐 | 少用 | 日常首选 |

`su -` 的 `-` 很重要：加载目标用户的完整环境（PATH/家目录），不加会带着原环境变量出问题。

## visudo 授权（最小化）

```text
# /etc/sudoers.d/ops（用 visudo -f 编辑）
rocky ALL=(ALL) ALL                  # 完全 sudo（需密码）
%wheel ALL=(ALL) ALL                 # wheel 组完全 sudo
deploy ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart nginx   # 只许免密重启 nginx
ops ALL=(root) /usr/bin/journalctl, /usr/bin/systemctl status *  # 只许查日志/状态
```

::: danger 用 visudo 别直接编辑
直接 `vim /etc/sudoers` 写错语法会让**所有人无法 sudo**（甚至锁死）。`visudo` 保存前校验语法，错了不让存。子配置放 `/etc/sudoers.d/`，`visudo -f /etc/sudoers.d/ops`。
:::

## 运维实战

**给部署账号最小权限**：只授权重启特定服务，不给全 root。
**自动化免密**：CI/Ansible 用 `NOPASSWD:` 限定命令，避免交互输密码。
**给人开权限**：加 wheel/sudo 组而非共享 root 密码，离职删号即收回。

## 相关命令

[useradd/usermod](./useradd) · [passwd](./passwd) · [id](./id-whoami) · [Ansible become](/services/cicd/ansible)

## 官方文档

- sudoers：<https://man7.org/linux/man-pages/man5/sudoers.5.html>
- sudo：<https://www.sudo.ws/docs/man/>