---
title: "iftop / nethogs · 网络流量定位"
description: "iftop 看连接级实时流量、nethogs 按进程看带宽。排「谁在占带宽/流量跑哪了」，中文详解。"
---

# iftop / nethogs · 网络流量定位

> 命令手册 · [排障观测](/commands/observe/) ｜ 频率：偶尔用
> 带宽被占满，是谁干的？iftop 看哪些连接在跑流量，nethogs 直接告诉你是哪个进程。

## 一句话用途

实时看网络流量：iftop 按连接，nethogs 按进程。

## 高频场景速查

```bash
sudo iftop -i eth0           # 看 eth0 的连接流量
sudo iftop -i eth0 -n        # 不解析主机名（快）
sudo iftop -i eth0 -P        # 显示端口
sudo nethogs eth0            # 按进程看带宽
sudo nethogs -d 2 eth0       # 2秒刷新
```

## iftop vs nethogs

| | iftop | nethogs |
|---|---|---|
| 维度 | 连接（源↔目的） | 进程 |
| 回答 | 流量去哪了 | 谁在用流量 |
| 场景 | 看异常连接/外联 | 揪占带宽的进程 |

## iftop 界面

三列流量：最近 2s/10s/40s 平均。底部 TX/RX 累计。按 `P` 显示端口、`n` 切 DNS、`t` 切显示模式。

## 运维实战

**带宽被占满**：先 `nethogs` 看哪个进程（备份？被入侵挖矿？），再 `iftop` 看它连哪。
**异常外联排查**：iftop 看到连陌生境外 IP 大流量，可能入侵，结合 [ss](/commands/network/ss)/[last](/commands/identity/last) 溯源。
**确认备份占带宽**：nethogs 看到 rsync 占满，错峰或限速（rsync --bwlimit）。

::: tip 易错点
两者都需 root（抓包/读进程网络）。iftop 看的是流经网卡的流量，本机 loopback 通信不一定显示。容器网络需进对应 netns 或看宿主 veth。
:::

## 相关命令

[ss](/commands/network/ss) · [tcpdump](/commands/network/tcpdump) · [sar -n DEV](./sar) · [ip](/commands/network/ip-addr-link)

## 官方文档

- iftop：<https://man7.org/linux/man-pages/man8/iftop.8.html>
- nethogs：<https://github.com/raboof/nethogs>