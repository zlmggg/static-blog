---
category: 网络
difficulty: 初级
date: 2022-08-30
---

# DNS 解析失败：nslookup/dig/resolv.conf（2022-08-30）

## 现象

服务器上访问外部域名报错：

```bash
curl https://www.google.com
# curl: (6) Could not resolve host: www.google.com
```

或者间歇性解析失败：

```bash
ping www.baidu.com
# ping: www.baidu.com: Name or service not known
```

但直接用 IP 访问是通的：

```bash
curl -I http://110.242.68.3   # 百度 IP，通的
```

说明网络本身没问题，是 DNS 解析坏了。

## 环境

- 发行版：Ubuntu 22.04.1 LTS
- 内核：`5.15.0-47-generic`
- 系统解析：systemd-resolved 249
- 上游 DNS：阿里 `223.5.5.5`、114 `114.114.114.114`

## 定位过程

### 1. 先确认系统解析器用的是谁

```bash
cat /etc/resolv.conf
# nameserver 127.0.0.53    <- systemd-resolved
# nameserver 8.8.8.8       <- 或者直接配的
```

注意：Ubuntu 22.04 默认 `/etc/resolv.conf` 是指向 `/run/systemd/resolve/stub-resolv.conf` 的软链，手动改 `/etc/resolv.conf` 会被覆盖。

```bash
systemd-resolve --status
# 或新版：
resolvectl status
```

看 `DNS Servers` 和 `DNS Domain` 配的是什么。

### 2. 用 dig 直接问上游 DNS，绕过系统缓存

```bash
# 问阿里 DNS
dig @223.5.5.5 www.baidu.com +short
# www.a.shifen.com.
# 110.242.68.3

# 问 114
dig @114.114.114.114 www.baidu.com +short
# 110.242.68.3
```

如果直接问上游是通的，说明是本机缓存或 resolv.conf 配置问题。
如果直接问上游也失败，说明上游 DNS 或网络到 DNS 有问题。

### 3. 用 nslookup 对比

```bash
nslookup www.baidu.com
# Server:         127.0.0.53
# Address:        127.0.0.53#53
#
# Non-authoritative answer:
# Name:   www.baidu.com
# Address: 110.242.68.3
```

### 4. 看是不是 hosts 文件被改了

```bash
cat /etc/hosts
```

有时候应用部署脚本会往 `/etc/hosts` 里塞记录，搞错了。

### 5. 看 systemd-resolved 缓存

```bash
resolvectl statistics
# 看 Cache hits / misses

# 清缓存
resolvectl flush-caches
```

### 6. 看是不是 DNS 端口被防火墙拦了

```bash
# DNS 默认 UDP 53
nc -zv 223.5.5.5 53 -u
# Connection refused 或超时 = 到 DNS 的 53 端口不通
```

## 根因

机房出口防火墙上周加了规则，只允许出向 TCP 53，把 UDP 53 挡了。
系统默认用 UDP 查 DNS，全部超时；但因为 `/etc/resolv.conf` 里配了多个 nameserver，偶尔 TCP 回退能成功，表现为间歇性解析失败。

## 解决步骤

### 1. 临时止血

在 `/etc/resolv.conf`（或 systemd-resolved 配置）里加一个本地能通的 DNS：

```
nameserver 223.5.5.5
nameserver 114.114.114.114
options timeout:2 attempts:3
```

Ubuntu 用 systemd-resolved 的话，改 `/etc/systemd/resolved.conf`：

```
[Resolve]
DNS=223.5.5.5 114.114.114.114
```

然后：

```bash
systemctl restart systemd-resolved
```

### 2. 彻底修复

让防火墙放行 UDP 53 出向（DNS 主要走 UDP，TCP 只用于区域传送和大响应）。
如果必须限制，至少允许 UDP 53 到内部 DNS。

### 3. 内部服务用内部 DNS

如果是内网域名，不要去问公网 DNS，直接配内部 DNS 服务器：

```
nameserver 10.0.0.53   # 内部 DNS
search my.local
```

### 4. 应用层面

- 应用启动时预热 DNS 缓存（如 JVM 的 `networkaddress.cache.ttl`）。
- 不要在代码里硬编码 IP。

## 验证与预防

- `dig @223.5.5.5 google.com +short` 返回 IP。
- `getent hosts google.com` 正常解析。
- 监控补：DNS 解析成功率、解析耗时。
- 告警阈值：DNS 解析失败率 > 5% 持续 1 分钟。
- 记住：**`curl: (6) Could not resolve host` 是 DNS 问题，先 dig @上游 再 dig 默认**，分段定位。

## 相关

- 命令速查：[网络命令速查](/reference/network-commands)
- 网络方向：[网络不通丢包](/cases/t-net-unreachable-mtr)
- 网络方向：[端口 Connection refused](/cases/t-port-connection-refused)
- 网络方向：[连接超时防火墙](/cases/t-connection-timeout-firewall)
