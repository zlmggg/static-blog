---
title: "arp / arping / ip neigh · 邻居表"
description: "arp 看 IP-MAC 映射、arping 探测/检测 IP 冲突、ip neigh 现代替代。排「同网段不通/IP 冲突」，中文详解。"
---

# arp / arping / ip neigh · 邻居表

> 命令手册 · [网络](/commands/network/) ｜ 频率：很少用
> 同网段通信靠 ARP 把 IP 解析成 MAC。IP 冲突、网关 MAC 不对、同网段不通——查邻居表。

## 一句话用途

查看/管理 IP 到 MAC 的映射（ARP 邻居表），检测 IP 冲突。

## 高频场景速查

```bash
arp -n                       # 看 ARP 表（数字显示）
ip neigh                     # 现代替代（推荐）
ip neigh show 10.0.0.1       # 看某 IP 的 MAC
arping -c 3 10.0.0.11        # ARP 探测某 IP
arping -D -c 3 10.0.0.11     # 检测 IP 冲突（-D 重复地址检测）
sudo ip neigh flush all      # 清空邻居表
sudo arp -d 10.0.0.11        # 删某条 ARP
```

## 参数详解

### arp / ip neigh

| 命令 | 含义 |
|---|---|
| `arp -n` | 数字显示 ARP 表 |
| `arp -d IP` | 删除条目 |
| `arp -s IP MAC` | 静态绑定 |
| `ip neigh` | 邻居表（含状态） |
| `ip neigh flush` | 清空 |

邻居状态：REACHABLE（可达）/STALE（过期）/DELAY/PROBE/FAILED。

### arping

| 参数 | 含义 |
|---|---|
| `-c N` | 发 N 个 |
| `-D` | 重复地址检测（冲突返回非0） |
| `-I 接口` | 指定网卡 |

## 运维实战

**检测 IP 冲突**：配 IP 前 `arping -D -c 3 拟用IP`，有回应说明已被占用。
**同网段不通**：`ip neigh` 看目标 MAC 是否 FAILED/ incomplete，可能 ARP 被挡或主机 down。
**网关 MAC 异常**：ARP 表网关 MAC 不对，可能 ARP 欺骗，静态绑定或查网络。
**换网卡后不通**：清 ARP 缓存 `ip neigh flush all` 让重新解析。

## 相关命令

[ip](./ip-addr-link) · [ping](./ping) · [ethtool](./ethtool) · [tcpdump](./tcpdump)

## 官方文档

- arp：<https://man7.org/linux/man-pages/man8/arp.8.html>
- ip-neighbour：<https://man7.org/linux/man-pages/man8/ip-neighbour.8.html>
- arping：<https://man7.org/linux/man-pages/man8/arping.8.html>