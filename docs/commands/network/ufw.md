---
title: "ufw · Ubuntu 简易防火墙"
description: "ufw 启停/放行/拒绝端口、allow/deny、按应用配置、limit 防暴破。Debian/Ubuntu 的 iptables 前端，中文详解。"
---

# ufw · Ubuntu 简易防火墙

> 命令手册 · [网络](/commands/network/) ｜ 频率：偶尔用
> Ubuntu 的简易防火墙前端（底层 iptables/nftables）。比裸 iptables 好上手，几条命令搞定放行。

## 一句话用途

用简单命令管理 Ubuntu 防火墙规则。

## 高频场景速查

```bash
sudo ufw status verbose            # 看状态与规则
sudo ufw enable                    # 启用（先放行 SSH！）
sudo ufw disable                   # 停用
sudo ufw allow 22/tcp              # 放行 SSH
sudo ufw allow 80,443/tcp          # 放行多端口
sudo ufw allow from 10.0.0.0/24 to any port 3306   # 限定源
sudo ufw deny 3306                 # 拒绝
sudo ufw delete allow 80/tcp       # 删规则
sudo ufw limit 22/tcp              # 限连接频率（防暴破）
sudo ufw app list                  # 看应用profile
sudo ufw allow 'Nginx Full'        # 按应用放行
```

## 参数详解

| 命令 | 含义 |
|---|---|
| `allow 端口/协议` | 放行 |
| `deny 端口` | 拒绝（静默丢） |
| `reject 端口` | 拒绝（回 ICMP） |
| `limit 端口` | 限频（6次/30秒触发挡） |
| `from IP to any port N` | 限定源 |
| `delete 规则` | 删除 |
| `status numbered` | 带编号（便于删） |

::: danger 启用前先放行 SSH
远程 `ufw enable` 前**必须先 `ufw allow 22`**，否则默认 deny incoming 会把你 SSH 断掉锁在外面。
:::

## 运维实战

**Web 服务器**：`ufw allow 22,80,443/tcp && ufw enable`。
**数据库只对内网**：`ufw allow from 10.0.0.0/24 to any port 3306`，不对公网开。
**防 SSH 暴破**：`ufw limit 22/tcp` 限制连接频率。

## 相关命令

[iptables](./iptables) · [firewall-cmd](./firewall-cmd) · [nft](./nft) · [ss](./ss)

## 官方文档

- ufw：<https://manpages.ubuntu.com/manpages/noble/en/man8/ufw.8.html>
- Ubuntu 防火墙：<https://ubuntu.com/server/docs/firewalls>