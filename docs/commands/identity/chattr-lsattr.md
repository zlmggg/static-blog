---
title: "chattr / lsattr · 文件扩展属性"
description: "chattr +i 不可变（防误删/篡改）、+a 只追加（日志保护）、lsattr 查看。比 chmod 更底层的保护，排「root 也删不掉」，中文详解。"
---

# chattr / lsattr · 文件扩展属性

> 命令手册 · [用户与权限](/commands/identity/) ｜ 频率：很少用
> root 也删不掉某个文件？多半是 chattr +i 锁了。这是比 chmod 更底层的文件系统属性。

## 一句话用途

给文件加"不可修改/只追加"等底层属性，防误删防篡改。

## 高频场景速查

```bash
lsattr file                  # 看扩展属性
sudo chattr +i file          # 不可变：谁都不能改/删/改名（含 root）
sudo chattr -i file          # 解除不可变
sudo chattr +i /etc/resolv.conf   # 防 DNS 配置被覆盖
sudo chattr +a /var/log/audit.log # 只追加：能写不能删改（日志保护）
sudo chattr -R +i /etc/nginx      # 递归锁定配置目录
```

## 常用属性

| 属性 | 含义 |
|---|---|
| `i` | immutable，不可改/删/链接/改名 |
| `a` | append only，只能追加写入 |
| `A` | 不更新 atime（减少 IO） |
| `d` | 不被 dump 备份 |
| `u` | 删除后内容可恢复 |

## 运维实战

**防关键配置被改**：`chattr +i /etc/resolv.conf`，NetworkManager/云初始化也覆盖不了（要先 -i 才能改）。
**日志防篡改**：`chattr +a` 让日志只能追加，攻击者清不了痕迹。
**排"Operation not permitted"**：root 删文件报这个，先 `lsattr` 看有没有 i 属性，`chattr -i` 解除。

::: danger 锁定前先想好
+i 后连 root 都改不了，自动化更新配置的脚本会失败。锁定期要改必须先 -i。别锁了又忘记，排障半天。
:::

## 相关命令

[chmod](./chmod) · [chown](./chown-chgrp) · [SELinux](./selinux) · [lsattr 排障](/cases/)

## 官方文档

- chattr：<https://man7.org/linux/man-pages/man1/chattr.1.html>
- lsattr：<https://man7.org/linux/man-pages/man1/lsattr.1.html>