---
title: "route · 路由表（旧）"
description: "route 看/加/删静态路由、-n 数字显示、默认网关。已被 ip route 取代但需会认，中文详解。"
---

# route · 路由表（旧）

> 命令手册 · [网络](/commands/network/) ｜ 频率：很少用
> 老工具，看/改路由表。新系统用 [ip route](./ip-addr-link)，但 route 输出要会认。

## 一句话用途

查看和配置静态路由、默认网关（传统方式）。

## 高频场景速查

```bash
route -n                       # 看路由表（数字，不解析）
sudo route add -net 192.168.2.0/24 gw 10.0.0.254    # 加静态路由
sudo route add default gw 10.0.0.1                  # 加默认网关
sudo route del -net 192.168.2.0/24                  # 删路由
```

## 输出解读

```text
Destination     Gateway         Genmask         Flags Metric Iface
0.0.0.0         10.0.0.1        0.0.0.0         UG    100    eth0
10.0.0.0        0.0.0.0         255.255.255.0   U     100    eth0
```

- `Destination 0.0.0.0` + `UG`：默认路由（G=网关）。
- `Gateway 0.0.0.0`：直连网段（不经网关）。
- Flags：U 启用、G 网关、H 主机路由。

## route → ip 对照

| route | ip 替代 |
|---|---|
| `route -n` | `ip route` |
| `route add -net X gw Y` | `ip route add X via Y` |
| `route add default gw Y` | `ip route add default via Y` |
| `route del -net X` | `ip route del X` |

::: tip 临时 vs 持久
route/ip route 加的路由重启失效。持久化用 nmcli（ipv4.routes）或 networkd 配置。多网卡注意默认路由冲突（metric 小的优先）。
:::

## 运维实战

**加内网静态路由**：访问另一网段经指定网关 `ip route add 192.168.2.0/24 via 10.0.0.254`。
**排默认路由**：`ip route` 看 default 走哪个网关，多网卡时确认出口对不对。
**策略路由**：多出口用 ip rule + 多路由表（route 做不到）。

## 相关命令

[ip](./ip-addr-link) · [nmcli](./nmcli) · [netstat](./netstat) · [traceroute/mtr](./traceroute-mtr)

## 官方文档

- route：<https://man7.org/linux/man-pages/man8/route.8.html>
- ip-route：<https://man7.org/linux/man-pages/man8/ip-route.8.html>