---
title: "netstat · 网络统计（旧）"
description: "netstat 看连接/路由/接口统计、-tunlp 看监听。已被 ss/ip 取代但老系统常见，与 ss 对照，中文详解。"
---

# netstat · 网络统计（旧）

> 命令手册 · [网络](/commands/network/) ｜ 频率：偶尔用
> 老系统/老教程常用 netstat。新系统推荐 [ss](./ss)（更快）和 [ip](./ip-addr-link)，但 netstat 仍要会认。

## 一句话用途

查看网络连接、路由表、接口统计（传统工具）。

## 高频场景速查

```bash
netstat -tunlp               # 看监听端口+进程（最常用）
netstat -an | grep ESTABLISHED   # 看已建立连接
netstat -rn                  # 路由表（= route -n）
netstat -i                   # 接口统计
netstat -s                   # 协议统计（TCP 重传等）
netstat -ant | awk '{print $6}' | sort | uniq -c   # 连接状态统计
```

## 参数详解

| 参数 | 含义 |
|---|---|
| `-t` | TCP |
| `-u` | UDP |
| `-n` | 数字显示（不解析） |
| `-l` | 只看监听 |
| `-p` | 显示进程（需 root） |
| `-a` | 全部（含监听） |
| `-r` | 路由表 |
| `-i` | 接口 |
| `-s` | 统计 |

## netstat → 新工具对照

| netstat | 替代 |
|---|---|
| `netstat -tunlp` | `ss -tunlp` |
| `netstat -rn` | `ip route` |
| `netstat -i` | `ip -s link` |
| `netstat -s` | `ss -s` / `nstat` |

::: tip 为什么用 ss
netstat 读 /proc 慢，连接多时卡；ss 直接查内核 netlink，快得多。新系统 netstat 可能没装（net-tools 包），ss（iproute2）默认有。
:::

## 运维实战

**老系统查端口**：`netstat -tunlp | grep 8080`。
**统计连接状态**：`netstat -ant | awk '{print $6}' | sort | uniq -c` 看 TIME_WAIT 是否过多。
**查重传**：`netstat -s | grep -i retrans` 看 TCP 重传，判断网络质量。

## 相关命令

[ss](./ss) · [ip](./ip-addr-link) · [route](./route) · [lsof](/commands/observe/lsof)

## 官方文档

- netstat：<https://man7.org/linux/man-pages/man8/netstat.8.html>