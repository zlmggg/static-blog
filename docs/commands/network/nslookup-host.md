---
title: "nslookup / host / getent · DNS 查询"
description: "nslookup/host 查域名解析、getent 走系统解析（含 /etc/hosts/NSS）、resolvectl 看 systemd-resolved。与 dig 互补排解析问题，中文详解。"
---

# nslookup / host / getent · DNS 查询

> 命令手册 · [网络](/commands/network/) ｜ 频率：偶尔用
> dig 最专业，nslookup/host 更简短，getent 走系统真实解析路径（含 hosts 文件）。排"域名解析对不对"。

## 一句话用途

查域名解析结果，验证 DNS 与系统解析是否正常。

## 高频场景速查

```bash
nslookup example.com               # 查 A 记录
nslookup example.com 8.8.8.8       # 指定 DNS 服务器
nslookup -type=MX example.com      # 查 MX
host example.com                   # 简洁查询
host -t MX example.com             # 指定类型
getent hosts example.com           # 走系统解析（含 /etc/hosts）
getent passwd rocky                # 走 NSS 查用户（含 LDAP）
resolvectl status                  # systemd-resolved 状态
resolvectl query example.com       # resolved 查询
```

## 工具区别（重点）

| 工具 | 解析路径 |
|---|---|
| `dig`/`nslookup`/`host` | **直接问 DNS 服务器**（绕过 hosts） |
| `getent hosts` | 走 NSS（/etc/nsswitch.conf：files→dns，**含 hosts**） |
| `resolvectl` | 走 systemd-resolved |

::: tip 为什么 dig 通但程序解析失败
dig 直接问 DNS，程序走 getent/NSS（先查 /etc/hosts、可能受 nsswitch/resolved 影响）。两者结果不一致时，查 /etc/hosts、/etc/nsswitch.conf、/etc/resolv.conf。
:::

## 运维实战

**排解析不一致**：`dig 域名` 与 `getent hosts 域名` 对比，不同就是 hosts/NSS 作怪。
**验证 DNS 服务器**：`nslookup 域名 指定DNS` 看不同 DNS 返回是否一致（污染/缓存）。
**查用户来源**：`getent passwd 用户` 看是本地还是 LDAP/SSSD。

## 相关命令

[dig](./dig) · [ping](./ping) · [/etc/hosts](./getent-resolvectl) · [DNS 服务](/services/web/dns)

## 官方文档

- nslookup：<https://man7.org/linux/man-pages/man1/nslookup.1.html>
- getent：<https://man7.org/linux/man-pages/man1/getent.1.html>
- resolvectl：<https://www.freedesktop.org/software/systemd/man/latest/resolvectl.html>