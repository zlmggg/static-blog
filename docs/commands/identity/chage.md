---
title: "chage · 密码过期策略"
description: "chage 查看/设置密码有效期、过期警告、账号失效日、强制改密。等保合规的密码策略落地，参数中文分级。"
---

# chage · 密码过期策略

> 命令手册 · [用户与权限](/commands/identity/) ｜ 频率：很少用
> 密码多久过期、过期前几天警告、账号哪天失效——等保/安全合规要求用 chage 落地。

## 一句话用途

查看和设置用户密码的有效期与账号过期策略。

## 高频场景速查

```bash
sudo chage -l rocky              # 看当前密码策略
sudo chage -M 90 rocky           # 密码最长 90 天
sudo chage -m 7 rocky            # 最短 7 天（防立即改回）
sudo chage -W 14 rocky           # 过期前 14 天警告
sudo chage -d 0 rocky            # 强制下次登录改密
sudo chage -E 2026-12-31 rocky   # 账号该日失效
```

## 参数详解

| 参数 | 含义 |
|---|---|
| `-l` | 列出当前策略 |
| `-M 天数` | 密码最长有效天数 |
| `-m 天数` | 最短天数 |
| `-W 天数` | 过期前警告 |
| `-I 天数` | 过期后宽限（之后锁定） |
| `-d 日期` | 上次改密日（0=强制改） |
| `-E 日期` | 账号失效日 |

## 运维实战

**等保密码策略**：`chage -M 90 -m 7 -W 14 rocky`，90 天必须改、7 天内不能改回、提前 14 天提醒。
**临时账号到期自动失效**：`chage -E 2026-12-31 contractor`，外包账号到期自动不能用。
**全局默认**：改 `/etc/login.defs` 的 PASS_MAX_DAYS 等，新建账号默认生效。

## 相关命令

[passwd](./passwd) · [useradd](./useradd) · [last](./last) 登录审计

## 官方文档

- chage：<https://man7.org/linux/man-pages/man1/chage.1.html>
- login.defs：<https://man7.org/linux/man-pages/man5/login.defs.5.html>