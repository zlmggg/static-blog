---
title: "ipset · IP 集合"
description: "ipset 建 IP/端口集合配合 iptables 批量匹配、hash:net 网段集合、动态封禁。比逐条 iptables 规则高效，中文详解。"
---

# ipset · IP 集合

> 命令手册 · [网络](/commands/network/) ｜ 频率：很少用
> 要封几千个 IP，逐条 iptables 规则慢且难管。ipset 把 IP 装进集合，iptables 一条规则匹配整个集合。

## 一句话用途

管理 IP/网段/端口集合，供 iptables/nftables 高效批量匹配。

## 高频场景速查

```bash
sudo ipset create blacklist hash:net          # 建网段集合
sudo ipset add blacklist 192.168.1.0/24       # 加网段
sudo ipset add blacklist 10.0.0.5             # 加单 IP
sudo ipset list blacklist                     # 看集合内容
sudo ipset del blacklist 10.0.0.5             # 删条目
sudo ipset test blacklist 10.0.0.5            # 测是否在集合
# iptables 引用集合
sudo iptables -A INPUT -m set --match-set blacklist src -j DROP
sudo ipset flush blacklist                    # 清空
sudo ipset destroy blacklist                  # 销毁
```

## 集合类型

| 类型 | 存什么 |
|---|---|
| `hash:ip` | 单 IP |
| `hash:net` | 网段 |
| `hash:ip,port` | IP+端口 |
| `hash:mac` | MAC |
| `bitmap:ip` | 连续 IP 范围 |

## 运维实战

**动态封禁攻击 IP**：脚本检测异常 IP → `ipset add blacklist IP`，iptables 一条规则全挡，无需逐条加。
**白名单放行**：建 whitelist 集合，iptables 只允许集合内 IP 访问管理端口。
**配合 fail2ban**：fail2ban 用 ipset 动作批量封禁暴破 IP。

::: tip 为什么用 ipset
iptables 几千条规则线性匹配慢；ipset 哈希查找 O(1)，一条规则匹配百万 IP 都快。动态增删集合不用动 iptables 规则。
:::

## 相关命令

[iptables](./iptables) · [nft](./nft) · [firewall-cmd](./firewall-cmd) · [conntrack](./conntrack)

## 官方文档

- ipset：<https://ipset.netfilter.org/>
- man：<https://man7.org/linux/man-pages/man8/ipset.8.html>