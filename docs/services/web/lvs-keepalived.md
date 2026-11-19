---
title: "LVS + Keepalived · 四层负载与高可用 VIP"
description: "四层 vs 七层负载、LVS/IPVS 三种转发模式（NAT/DR/TUN）与 DR 的 ARP 抑制、调度算法、Keepalived VRRP 主备 VIP 漂移原理与配置。单页四段。"
---

# LVS + Keepalived · 四层负载与高可用 VIP

> 单页四段：理论 → 部署 → 功能 → 实战。返回 [服务详解 · 接入与网络](/services/web/)。七层负载见 [Nginx](/services/web/nginx/01-理论)，完整接入层组合见 [接入层高可用](/deploy/stacks/lb-ha)。

## 01 · 服务理论

流量大到一台 Nginx 扛不住、或入口不能有单点时，要在 **TCP/IP 层（四层）** 做负载均衡。把请求比作寄到写字楼的快递：

- **四层（LVS）** 像楼下前台分拣员：只看"目的 IP+端口"直接转给某间办公室，**不拆包看内容**，不知道你寄的是网页还是视频。
- **七层（Nginx）** 像拆包检查员：拆开看 HTTP 的域名/URL/Cookie 再决定转给谁，更聪明但慢、吃资源。

| | 四层 LVS/IPVS | 七层 Nginx |
|---|---|---|
| 看什么 | 目标 IP+端口 | Host/URL/Header |
| 性能 | 极高（内核态转发，百万级 PPS） | 相对低（终止/重建连接） |
| 功能 | 纯转发调度 | 路由/改写/限流/TLS/缓存 |
| 位置 | 机房最前端 | LVS 之后、业务之前 |

现实架构常是 **LVS（四层）→ Nginx（七层）→ 业务**。LVS 内核实现叫 **IPVS**，已内置 Linux 内核，用户态用 `ipvsadm` 配置，在 netfilter 上内核态转发所以极快。这也是 K8s kube-proxy IPVS 模式的底层。

### 三种转发模式

| 模式 | 原理 | RS 回包 | 需同网段 | 性能 |
|---|---|---|---|---|
| VS/NAT | 改目的 IP，回包必经 Director | 经 Director | 可跨 | 一般 |
| **VS/DR**（主力） | 只改二层 MAC，RS 直接回客户端 | 不经 Director | **必须同二层** | 最高 |
| VS/TUN | IP 隧道封装 | 不经 Director | 可跨 | 高 |

**DR 为什么快**：请求过 Director、响应不过，Director 只处理"进门"一半流量，瓶颈小。代价是 Director 和 RS 必须同二层广播域，且要解决 ARP 问题。

## 02 · 部署方案

规划：Director 10.0.0.10，VIP 10.0.0.100，RS1 10.0.0.21 / RS2 10.0.0.22 同网段跑 Nginx 80。

### Director 配 ipvsadm（DR）

```bash
sudo dnf install -y ipvsadm
sudo ip addr add 10.0.0.100/32 dev eth0      # 绑 VIP
sudo sysctl -w net.ipv4.ip_forward=1
sudo ipvsadm -C
sudo ipvsadm -A -t 10.0.0.100:80 -s wlc      # 建虚拟服务，wlc 算法
sudo ipvsadm -a -t 10.0.0.100:80 -r 10.0.0.21:80 -g -w 1   # -g = DR
sudo ipvsadm -a -t 10.0.0.100:80 -r 10.0.0.22:80 -g -w 1
sudo ipvsadm -Ln                             # 查看规则
```

### RS 的 ARP 抑制（DR 关键）

VIP 同时绑在 Director 和 RS 的 lo 上，若 RS 也响应对 VIP 的 ARP，交换机会把包直接送 RS 绕开 Director。让 RS 对 VIP"装聋作哑"：

```bash
# 每台 RS：lo 上绑 VIP + 抑制 ARP
sudo ip addr add 10.0.0.100/32 dev lo
echo 1 | sudo tee /proc/sys/net/ipv4/conf/lo/arp_ignore
echo 2 | sudo tee /proc/sys/net/ipv4/conf/lo/arp_announce
echo 1 | sudo tee /proc/sys/net/ipv4/conf/all/arp_ignore
echo 2 | sudo tee /proc/sys/net/ipv4/conf/all/arp_announce
```

`arp_ignore=1` 只响应目标 IP 是入接口地址的 ARP；`arp_announce=2` 不把 lo 上的 VIP 通告出去。参数要写 sysctl 持久化。

## 03 · 功能详解

### 调度算法

| 算法 | 含义 | 适用 |
|---|---|---|
| rr | 轮询 | RS 性能相近、短连接 |
| wrr | 加权轮询 | RS 性能不均 |
| lc | 最少连接 | 长连接 |
| **wlc** | 加权最少连接（默认） | 大多数生产 |
| sh | 源地址哈希 | 会话粘滞 |

### Keepalived VRRP 高可用

ipvsadm 规则是单点——Director 挂了入口就没了。**Keepalived 用 VRRP 协议做主备 VIP 漂移**：两台 Director 一主一备，主挂了 VIP 自动漂到备。

```conf
# /etc/keepalived/keepalived.conf（主）
vrrp_instance VI_1 {
    state MASTER              # 备机写 BACKUP
    interface eth0
    virtual_router_id 51      # 主备必须一致
    priority 100              # 备机写 90，越大越优先
    advert_int 1
    authentication { auth_type PASS; auth_pass 请替换为强密码 }
    virtual_ipaddress { 10.0.0.100/32 }
}
virtual_server 10.0.0.100 80 {
    delay_loop 6
    lb_algo wlc
    lb_kind DR
    real_server 10.0.0.21 80 { weight 1; TCP_CHECK { connect_port 80 } }
    real_server 10.0.0.22 80 { weight 1; TCP_CHECK { connect_port 80 } }
}
```

Keepalived 既管 VIP 漂移（vrrp_instance），又管 LVS 规则和健康检查（virtual_server），还能给任意 TCP 服务（如 Nginx/HAProxy）做主备。`TCP_CHECK` 探活失败自动摘除 RS。

## 04 · 实战参考

**典型组合**：Keepalived 双机 VIP → LVS DR → 多台 Nginx → 业务。VIP 对外，Director 主备漂移，RS 健康检查自动摘除。完整落地见 [接入层高可用](/deploy/stacks/lb-ha)。

**常见坑**：

| 现象 | 原因 | 解法 |
|---|---|---|
| DR 模式负载乱/包绕开 Director | RS 没抑制 ARP | arp_ignore=1/arp_announce=2 |
| VIP 漂移后不通 | 备机没绑 VIP/规则 | Keepalived 统一管 virtual_server |
| 主备都持 VIP（脑裂） | VRRP 组播被防火墙挡 | 放通 VRRP（协议号 112） |
| RS 跨网段 DR 不工作 | DR 要求同二层 | 改用 TUN 或 NAT |

排障用 [ip-addr-link](/commands/network/ip-addr-link) 看 VIP、[tcpdump](/commands/network/tcpdump) 抓 ARP、[ss](/commands/network/ss) 看连接。

## 官方文档

- LVS：<http://www.linuxvirtualserver.org/>
- ipvsadm：<https://man7.org/linux/man-pages/man8/ipvsadm.8.html>
- Keepalived：<https://keepalived.readthedocs.io/>

---

返回 [服务详解 · 接入与网络](/services/web/)。