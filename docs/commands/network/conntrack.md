---
title: "conntrack · 连接跟踪"
description: "conntrack 看 NAT/防火墙的连接跟踪表、-L 列/-D 删/-S 统计。排「NAT 会话满/连接异常」，中文详解。"
---

# conntrack · 连接跟踪

> 命令手册 · [网络](/commands/network/) ｜ 频率：很少用
> 防火墙/NAT 靠连接跟踪表记住每条连接。表满了新连接被丢——高并发网关要懂 conntrack。

## 一句话用途

查看/管理内核连接跟踪表（NAT 与状态防火墙的基础）。

## 高频场景速查

```bash
sudo conntrack -L                  # 列所有跟踪连接
sudo conntrack -L -p tcp --dport 80   # 过滤
sudo conntrack -S                  # 统计（含 drop/insert_failed）
sudo conntrack -C                  # 当前条目数
cat /proc/sys/net/netfilter/nf_conntrack_max     # 表上限
cat /proc/sys/net/netfilter/nf_conntrack_count   # 当前用量
sudo conntrack -D -p tcp --dport 80  # 删某类连接
sudo conntrack -F                  # 清空表（慎用）
```

## 关键指标

| 指标 | 含义 |
|---|---|
| `nf_conntrack_max` | 表容量上限 |
| `nf_conntrack_count` | 当前条目 |
| `insert_failed` | 插入失败（表满） |
| `drop` | 因跟踪失败丢包 |

::: danger 表满丢连接
高并发 NAT/网关 conntrack 表满，dmesg 报 `nf_conntrack: table full, dropping packet`。调大 nf_conntrack_max（[sysctl](/commands/system/sysctl)）+ 缩短 timeout，或不需要跟踪的流量 NOTRACK。
:::

## 运维实战

**排 NAT 网关丢包**：`conntrack -S` 看 insert_failed 是否增长，`dmesg | grep conntrack` 确认表满。
**调优**：`sysctl -w net.netfilter.nf_conntrack_max=1048576` + 调 tcp timeout established。
**查某连接状态**：`conntrack -L -p tcp --dport 3306` 看 NAT 前后地址与状态。

## 相关命令

[iptables](./iptables) · [nft](./nft) · [sysctl](/commands/system/sysctl) · [ss](./ss) · [dmesg](/commands/system/dmesg)

## 官方文档

- conntrack：<https://man7.org/linux/man-pages/man8/conntrack.8.html>
- netfilter：<https://netfilter.org/>