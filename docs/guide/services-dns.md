---
title: DNS 域名解析
description: DNS 层级与递归迭代、记录类型、BIND（RHEL named / Debian bind9）正反向解析、主从复制、view 分离、转发缓存、dig/nslookup/host 排障
---

# DNS 域名解析

::: tip 本篇定位
理解 DNS **域名层级、递归/迭代解析、各类记录**，用 BIND 搭建**正向/反向解析、主从复制、view 分离、转发缓存**，并用 **dig/nslookup/host** 排障。
:::

## 先建立全局观：域名是怎么变成 IP 的

```
你输入 www.sersec.com
   → 本地 DNS（递归解析器）
   → 问根"."（返回 .com 顶级域地址）
   → 问 .com（返回 sersec.com 权威服务器地址）
   → 问 sersec.com 权威（返回 www 的 IP）
   → 本地 DNS 缓存结果并返回给你
```

- **递归查询**：你把问题交给本地 DNS，由它负责问到底、返回最终答案；
- **迭代查询**：本地 DNS 依次向根、顶级域、权威服务器询问，每级返回"你去问下一个"。

DNS 主要用 **UDP 53**（快）；区域传输和超大响应用 **TCP 53**。

---

## 一、DNS 基础

### 1.1 域名层级

```
        . （根域 root）
       / \
    .com .cn ...        顶级域 TLD
     |
  sersec.com            二级域（可注册的主体）
     |
  www.sersec.com        子域/主机
```

### 1.2 记录类型

| 记录 | 作用 | 例子 |
|---|---|---|
| **A** | 域名 → IPv4 | www → 47.109.132.117 |
| AAAA | 域名 → IPv6 | |
| **CNAME** | 域名别名 → 另一域名 | cdn → xxx.com |
| **MX** | 邮件服务器（带优先级） | |
| **NS** | 指定该域的权威 DNS 服务器 | |
| **PTR** | IP → 域名（反向解析） | |
| **SOA** | 起始授权，区域主服务器/管理员/序列号/计时 | 每个区域开头 |
| TXT | 文本（SPF、域名验证） | |
| SRV | 服务记录 | |
| CAA | 限定可签发证书的 CA | |

---

## 二、BIND 安装

### 2.1 RHEL/Rocky（服务名 named）

```bash
sudo dnf install -y bind bind-utils
sudo systemctl enable --now named
# 主配置 /etc/named.conf；区域文件 /var/named/
```

### 2.2 Debian/Ubuntu（服务名 bind9）

```bash
sudo apt install -y bind9 bind9utils dnsutils
sudo systemctl enable --now bind9
# /etc/bind/named.conf、named.conf.options、named.conf.local；区域 /etc/bind/
```

### 2.3 配置结构

- 主配置：监听、允许查询、转发、包含区域；
- 区域文件：具体记录。

RHEL `/etc/named.conf` 关键：

```conf
options {
    listen-on port 53 { any; };
    allow-query     { any; };
    recursion yes;
};
zone "sersec.com" IN {
    type master;
    file "sersec.com.zone";
    allow-update { none; };
};
```

Debian 在 `named.conf.local` 写 zone，options 写在 `named.conf.options`。

---

## 三、正向解析

### 3.1 区域文件

RHEL：`/var/named/sersec.com.zone`（Debian：`/etc/bind/db.sersec.com`）：

```conf
$TTL 86400
@   IN  SOA   ns.sersec.com. admin.sersec.com. (
            2026092801 ; Serial  序列号（每次修改 +1）
            3600       ; Refresh
            1800       ; Retry
            604800     ; Expire
            86400 )    ; Minimum TTL
    IN  NS    ns.sersec.com.
    IN  MX 10 mail.sersec.com.
ns  IN  A     47.109.132.117
www IN  A     47.109.132.117
mail IN A     47.109.132.117
cdn IN  CNAME www.sersec.com.
```

### 3.2 验证

```bash
# RHEL
named-checkconf
named-checkzone sersec.com /var/named/sersec.com.zone
sudo systemctl reload named

# Debian
sudo named-checkzone sersec.com /etc/bind/db.sersec.com
sudo systemctl reload bind9
```

::: warning 最常见错误
- 完整域名（FQDN）结尾**漏了点 `.`**，会被自动补成相对名；
- 改了记录**没加 Serial**，从库不更新；
- 区域文件属主/权限不对（RHEL 应为 root 或 named，按发行版要求）。
:::

---

## 四、反向解析

### 4.1 区域声明

```conf
# 网段 47.109.132.0/24，反向域写反：132.109.47.in-addr.arpa
zone "132.109.47.in-addr.arpa" IN {
    type master;
    file "132.109.47.zone";
};
```

### 4.2 反向区域文件

`/var/named/132.109.47.zone`：

```conf
$TTL 86400
@ IN SOA ns.sersec.com. admin.sersec.com. (
      2026092801 3600 1800 604800 86400 )
  IN NS ns.sersec.com.
117 IN PTR www.sersec.com.      -- 47.109.132.117
```

```bash
named-checkzone 132.109.47.in-addr.arpa /var/named/132.109.47.zone
```

反向解析常用于邮件服务器信誉、日志反查。

---

## 五、主从复制

主从通过**区域传输**同步：全量 **AXFR**、增量 **IXFR**；主库 Serial 增大后通知（NOTIFY）从库拉取。

**主库：**

```conf
zone "sersec.com" IN {
    type master;
    file "sersec.com.zone";
    allow-transfer { 10.0.0.14; };   -- 只允许从库
    also-notify    { 10.0.0.14; };
};
```

**从库（10.0.0.14）：**

```conf
zone "sersec.com" IN {
    type slave;
    masters { 10.0.0.13; };
    file "slaves/sersec.com.zone";    -- 存可写目录
};
```

::: danger 安全
`allow-transfer` 必须限制为从库 IP，若配成 `any`，任何人都能 axfr 拉走你整个域的所有记录（信息泄露，也是常见扫描点）。
:::

---

## 六、view 分离解析

让**内网和外网**对同一域名解析到不同结果（如 www 内网→内网 IP、外网→公网 IP）。

```conf
view "internal" {
    match-clients { 10.0.0.0/8; localhost; };
    zone "sersec.com" IN {
        type master;
        file "sersec-internal.zone";
    };
};

view "external" {
    match-clients { any; };
    zone "sersec.com" IN {
        type master;
        file "sersec-external.zone";
    };
};
```

> 使用 view 后，所有 zone 都必须放进某个 view，不能有游离在 view 外的 zone。

---

## 七、转发与缓存

本机不解析、把请求转给上游 DNS（如公共/云厂商 DNS）：

```conf
options {
    forwarders { 223.5.5.5; 223.6.6.6; };   -- 阿里
    forward first;     -- first: 先转发，失败再自己迭代；only: 只转发
};
```

转发可针对特定域（zone forward），缓存能减少重复查询、加快解析。

---

## 八、客户端工具与排障

### 8.1 dig（最常用）

```bash
dig www.sersec.com                  # 完整输出
dig @10.0.0.13 www.sersec.com       # 指定 DNS 服务器
dig -t MX sersec.com                # 指定记录类型
dig -x 47.109.132.117               # 反向解析
dig www.sersec.com +short           # 只看结果
dig www.sersec.com +trace           # 跟踪完整迭代路径
```

输出关注：`status: NOERROR`、`ANSWER SECTION`、TTL。

### 8.2 nslookup / host

```bash
nslookup www.sersec.com 10.0.0.13
host www.sersec.com
```

### 8.3 常见问题

| 现象 | 方向 |
|---|---|
| 解析不到 | 服务状态、UDP/TCP 53、allow-query、区域配置 |
| 改记录不生效 | Serial 没加、缓存 TTL 未到、没 reload |
| 从库不同步 | allow-transfer、NOTIFY、网络、Serial |
| SERVFAIL | 看日志，区域文件/语法错误、上游不可达 |

---

## 面试自测

1. 描述一次完整的域名解析过程，递归和迭代的区别？
2. A、CNAME、MX、NS、PTR、SOA 记录分别做什么？
3. 区域文件里 Serial 的作用？为什么改记录要加序列号？
4. 主从 DNS 如何同步？AXFR 和 IXFR？allow-transfer 为什么不能 any？
5. view 分离解析解决什么问题？
6. dig -x、+trace、@服务器分别怎么用？

## 相关速查

- [Linux 命令速查](/reference/linux-commands)
- BIND 文档（ISC）：https://bind9.readthedocs.io/
- dig 手册：https://man7.org/linux/man-pages/man1/dig.1.html
