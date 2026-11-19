---
title: "passwd · 密码管理"
description: "passwd 改密码、锁定解锁、设过期、批量 chpasswd、生成强密码。密码策略与 /etc/shadow，参数中文分级。"
---

# passwd · 密码管理

> 命令手册 · [用户与权限](/commands/identity/) ｜ 频率：偶尔用
> 设密码、锁账号、强制改密。密码哈希存 /etc/shadow，明文绝不落盘。

## 一句话用途

设置/修改用户密码，锁定账号，强制下次登录改密。

## 高频场景速查

```bash
sudo passwd rocky                # 给 rocky 设密码
passwd                           # 改自己的密码
sudo passwd -l rocky             # 锁定（密码前加 !）
sudo passwd -u rocky             # 解锁
sudo passwd -e rocky             # 强制下次登录改密
sudo passwd -S rocky             # 看密码状态
echo 'rocky:请替换为强密码' | sudo chpasswd   # 批量改密
```

## 参数详解

| 参数 | 含义 |
|---|---|
| `-l` / `-u` | 锁定 / 解锁密码 |
| `-e` | 立即过期（强制改密） |
| `-S` | 状态（PS 已设/LK 锁定/NP 无密码） |
| `-n 天数` | 最短使用天数 |
| `-x 天数` | 最长使用天数 |
| `-w 天数` | 过期前警告天数 |
| `-i 天数` | 过期后宽限天数 |

## 运维实战

**新建账号强制改密**：`passwd rocky && passwd -e rocky`，首次登录必须改。
**批量初始化密码**：`chpasswd < users.txt`（每行 `user:pass`），脚本化开账号。
**生成强密码**：`openssl rand -base64 16`。

::: danger 密码安全
密码哈希在 /etc/shadow（仅 root 可读），别 cat 出来贴聊天。脚本里的密码用变量/凭据管理，别硬编码。生产优先 SSH 密钥而非密码登录。
:::

## 相关命令

[useradd](./useradd) · [chage](./chage) 过期策略 · [su/sudo](./su-sudo) · [openssl](/commands/devtools/openssl)

## 官方文档

- passwd：<https://man7.org/linux/man-pages/man1/passwd.1.html>
- shadow：<https://man7.org/linux/man-pages/man5/shadow.5.html>