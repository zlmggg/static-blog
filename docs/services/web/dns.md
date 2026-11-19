---
title: "DNS（Bind）· 域名解析服务"
description: "DNS 层级与递归/迭代解析、记录类型、BIND named 正反向解析配置、主从复制与 view 分离解析、转发缓存、dig 排障。单页四段。"
---

# DNS（Bind）· 域名解析服务

> 单页四段：理论 → 部署 → 功能 → 实战。返回 [服务详解 · 接入与网络](/services/web/)。解析命令见 [dig](/commands/network/dig)。

## 01 · 服务理论

DNS 把域名翻译成 IP，是互联网的"电话簿"。它是**分层分布式**系统：根域 → 顶级域（.com）→ 权威域（example.com），每层只管自己那部分。

### 递归 vs 迭代

- **递归**：客户端问本地 DNS"example.com 的 IP 是多少"，本地 DNS 负责一路问到底，把最终答案给客户端（客户端只问一次）。
- **迭代**：本地 DNS 问根，根说"去问 .com"；问 .com，说"去问 example.com 权威"——一步步 referrals，本地 DNS 自己跑完全程。

客户端到本地 DNS 是递归，本地 DNS 到各级服务器是迭代。

### 记录类型

| 记录 | 作用 |
|---|---|
| A / AAAA | 域名 → IPv4 / IPv6 |
| CNAME | 别名 → 另一域名 |
| MX | 邮件交换 |
| NS | 委派子域给哪台权威 |
| TXT | 文本（SPF/验证） |
| PTR | IP → 域名（反向） |
| SOA |  zone 起始授权（序列号/刷新） |

## 02 · 部署方案

```bash
sudo dnf install -y bind bind-utils      # RHEL 系 named
sudo systemctl enable --now named
```

### 正向解析

`/etc/named.conf` 加 zone：

```conf
zone "example.com" IN {
    type master;
    file "example.com.zone";
    allow-update { none; };
};
```

`/var/named/example.com.zone`：

```text
$TTL 86400
@   IN SOA ns1.example.com. admin.example.com. (
        2026111901 ; serial（每次改要递增）
        3600 1800 604800 86400 )
    IN NS  ns1.example.com.
ns1 IN A   10.0.0.10
www IN A   10.0.0.21
api IN CNAME www.example.com.
```

```bash
sudo named-checkconf                       # 校验主配置
sudo named-checkzone example.com /var/named/example.com.zone   # 校验 zone
sudo systemctl reload named
dig @10.0.0.10 www.example.com             # 验证
```

### 反向解析

zone `0.0.10.in-addr.arpa`，PTR 记录把 IP 末位映射回域名。

## 03 · 功能详解

### 主从复制

slave 的 zone `type slave; masters { 10.0.0.10; };`，靠 SOA serial 判断是否更新，AXFR/IXFR 同步。**改 zone 必须递增 serial**，否则从库不更新。

### view 分离解析

按客户端来源返回不同结果（内网用户解析到内网 IP，外网解析到公网 IP）：

```conf
view "internal" {
    match-clients { 10.0.0.0/24; };
    zone "example.com" { type master; file "example.com.internal"; };
};
view "external" {
    match-clients { any; };
    zone "example.com" { type master; file "example.com.external"; };
};
```

### 转发与缓存

`forwarders { 223.5.5.5; };` 把解析转发给上游，本地缓存结果（按 TTL），减少重复查询。

## 04 · 实战参考

**排障用 dig**（见 [dig](/commands/network/dig)）：

```bash
dig www.example.com               # 看 ANSWER 和 TTL
dig +trace www.example.com        # 跟踪完整迭代过程
dig @10.0.0.10 example.com AXFR   # 测主从同步
```

**常见坑**：

| 现象 | 原因 | 解法 |
|---|---|---|
| 从库不更新 | serial 没递增 | 改 zone 递增 serial |
| 解析不到 | zone 文件语法错 | named-checkzone 校验 |
| 反向解析失败 | PTR zone 没配 | 配 in-addr.arpa zone |
| 改了不生效 | TTL 缓存/没 reload | 等 TTL 或 reload named |

## 官方文档

- BIND9：<https://bind9.readthedocs.io/>
- DNS 概念：<https://www.cloudflare.com/learning/dns/what-is-dns/>
- dig：<https://man7.org/linux/man-pages/man1/dig.1.html>

---

返回 [服务详解 · 接入与网络](/services/web/)。