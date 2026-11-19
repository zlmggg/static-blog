---
title: "nft · nftables 防火墙"
description: "nftables 表/链/规则语法、nft list ruleset、与 iptables 关系、firewalld 后端。新一代包过滤，中文详解。"
---

# nft · nftables 防火墙

> 命令手册 · [网络](/commands/network/) ｜ 频率：很少用
> nftables 是 iptables 的继任者（RHEL 8+/Debian 10+ 默认后端）。语法更统一，一套管 IPv4/IPv6/桥接。

## 一句话用途

用统一的 nft 语法管理包过滤/NAT/流量控制。

## 高频场景速查

```bash
sudo nft list ruleset                  # 看全部规则
sudo nft list tables                   # 看所有表
sudo nft add table inet filter         # 建表
sudo nft add chain inet filter input '{ type filter hook input priority 0; policy drop; }'
sudo nft add rule inet filter input tcp dport 22 accept    # 放行 SSH
sudo nft add rule inet filter input ct state established,related accept
sudo nft flush ruleset                 # 清空（慎用，会断 SSH）
```

## 核心概念

- **table**：族（ip/ip6/inet/arp/bridge/netdev）+ 名。inet 同时管 v4/v6。
- **chain**：挂到 hook（input/output/forward/prerouting/postrouting），设 policy。
- **rule**：匹配条件 + 动作（accept/drop/reject）。
- **set**：集合，批量匹配 IP/端口（比逐条规则高效）。

## 与 iptables/firewalld 关系

| 工具 | 角色 |
|---|---|
| `nft` | 原生 nftables 前端 |
| `iptables-nft` | iptables 语法翻译到 nftables |
| `firewalld` | 高层管理，后端用 nftables |

::: danger 别混用直接 nft 与 firewalld
firewalld 在管时直接 nft flush 会清空它的规则。用 firewalld 就 firewall-cmd，要裸 nft 就停 firewalld。远程操作先放行 SSH 再设 drop policy。
:::

## 运维实战

**看真实规则**：firewalld 底层规则 `nft list ruleset` 能看到全貌。
**高性能批量封禁**：用 set 装大量 IP，一条规则匹配，比 iptables 逐条快。
**排防火墙**：`nft list chain inet filter input` 看 input 链具体规则与计数。

## 相关命令

[iptables](./iptables) · [firewall-cmd](./firewall-cmd) · [ipset](./ipset) · [conntrack](./conntrack)

## 官方文档

- nftables：<https://netfilter.org/projects/nftables/>
- nft man：<https://man7.org/linux/man-pages/man8/nft.8.html>