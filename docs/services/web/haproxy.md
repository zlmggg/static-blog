---
title: "HAProxy · 专业负载均衡器"
description: "HAProxy 的四层/七层负载、frontend/backend/listen 配置模型、balance 调度算法与健康检查、stats 监控页、与 Nginx/LVS 的选型、Keepalived 高可用。单页四段。"
---

# HAProxy · 专业负载均衡器

> 单页四段：理论 → 部署 → 功能 → 实战。返回 [服务详解 · 接入与网络](/services/web/)。对比 [Nginx](/services/web/nginx/01-理论)、[LVS+Keepalived](/services/web/lvs-keepalived)。

## 01 · 服务理论

HAProxy 是**专业负载均衡器**，专注做一件事：把流量高效、可靠地分到后端。它同时支持四层（TCP）和七层（HTTP），以**稳定、健康检查强、负载算法丰富**著称，很多大厂用它做入口负载。

和 Nginx/LVS 的分工：

| | HAProxy | Nginx | LVS |
|---|---|---|---|
| 定位 | 专业负载 |  Web 服务器+负载 | 内核四层负载 |
| 七层能力 | 强（ACL/路由） | 强（还能做 Web/缓存） | 无 |
| 四层性能 | 高（用户态） | 中 | 极高（内核态） |
| 健康检查 | 非常完善 | 一般 | 简单 |

一句话：要纯负载 + 精细健康检查选 HAProxy；要 Web 服务 + 负载一体选 Nginx；要极致四层性能选 LVS。

## 02 · 部署方案

```bash
sudo dnf install -y haproxy        # RHEL 系
sudo systemctl enable --now haproxy
```

配置 `/etc/haproxy/haproxy.cfg`，三段模型：

```conf
global
    maxconn 50000
    log /dev/log local0

defaults
    mode http
    timeout connect 5s
    timeout client 30s
    timeout server 30s
    option httplog

frontend web_in
    bind *:80
    default_backend web_servers

backend web_servers
    balance roundrobin
    option httpchk GET /health
    server web1 10.0.0.21:80 check inter 2s fall 3 rise 2
    server web2 10.0.0.22:80 check inter 2s fall 3 rise 2

listen stats
    bind *:8404
    stats enable
    stats uri /stats
```

`frontend` 定义入口（bind 端口），`backend` 定义后端池（server + 健康检查），`listen` 是 frontend+backend 合体（常用于 stats）。改完 `haproxy -c -f` 校验再 reload。

## 03 · 功能详解

### balance 调度算法

- `roundrobin`：加权轮询（默认）。
- `leastconn`：最少连接，适合长连接。
- `source`：源 IP 哈希，会话粘滞。
- `uri`：按 URI 哈希，缓存场景。

### 健康检查

`check inter 2s fall 3 rise 2`：每 2 秒探一次，连续 3 次失败摘除、2 次成功恢复。`option httpchk GET /health` 做七层接口探活（比 TCP 探活更能反映业务真实健康）。

### 七层 ACL 路由

```conf
frontend web_in
    bind *:80
    acl is_api path_beg /api
    use_backend api_servers if is_api
    default_backend web_servers
```

按路径/域名/Header 分流，类似 Nginx location。

## 04 · 实战参考

**高可用**：HAProxy 本身单点，配 [Keepalived](/services/web/lvs-keepalived) 双机 VIP 漂移。stats 页（8404/stats）实时看后端健康与连接数，是排障第一入口。

**常见坑**：

| 现象 | 原因 | 解法 |
|---|---|---|
| 后端全 down | 健康检查路径错/超时太短 | 核对 httpchk 路径、调 timeout |
| 503 无后端可用 | 所有 server 被摘 | 看 stats 页健康状态 |
| 长连接分配不均 | 用了 roundrobin | 改 leastconn |

完整接入层组合见 [接入层高可用](/deploy/stacks/lb-ha)。

## 官方文档

- HAProxy：<https://www.haproxy.com/documentation/>
- 配置手册：<https://docs.haproxy.org/>
- 健康检查：<https://www.haproxy.com/documentation/haproxy-configuration-manual/latest/#4.2-option%20httpchk>

---

返回 [服务详解 · 接入与网络](/services/web/)。