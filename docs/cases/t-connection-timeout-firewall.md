---
category: 网络
difficulty: 中级
date: 2021-11-09
---

# 连接超时：安全组/iptables/路由（2021-11-09）

## 现象

客户端访问服务器端口，等了很久才超时：

```bash
curl -v --connect-timeout 5 http://10.0.0.2:8080
# *   Trying 10.0.0.2:8080...
# * After 5000 ms connect timeout
#   Failed to connect to 10.0.0.2 port 8080: Connection timed out
```

和 `Connection refused`（立刻被拒）不同，**timeout 是包发出去石沉大海**。

## 环境

- 发行版：Rocky Linux release 8.4 (Green Obsidian)
- 内核：`4.18.0-305.el8.x86_64`
- 目标：Nginx 监听 80，云服务器在阿里云 ECS
- 客户端：办公网

## 定位过程

### 1. 先在服务器本机自测

```bash
curl -v http://127.0.0.1:80
# 通的，说明 Nginx 本身正常
ss -tlnp | grep :80
# LISTEN 0 128 0.0.0.0:80  0.0.0.0:*  users:(("nginx",pid=1234,fd=6))
```

服务监听正常，本机访问也通。那问题在网络路径上。

### 2. 从客户端看包到哪了

```bash
# 客户端 mtr 到服务器
mtr --report --report-cycles 10 10.0.0.2
# 看哪一跳开始丢包
```

如果中间某跳开始 100% 丢包，说明路由或防火墙在中间挡。

### 3. 在服务器上抓包，看请求到底有没有到

```bash
# 服务器上抓 80 端口的包
tcpdump -i any port 80 -nn
# 然后客户端 curl
# 如果完全看不到包 = 包在前面就被挡了（安全组/上游防火墙）
# 如果看到 SYN 但没回 = 本机 iptables 拦了
# 如果看到 SYN + SYN/ACK 来回 = 应用层问题，不是 timeout
```

### 4. 查云服务器安全组

阿里云/腾讯云/AWS 的安全组是**云平台层面**的防火墙，在操作系统之外。
即使你 iptables 全放通，安全组没开 80 端口，外面一样连不上。

去云控制台 → 安全组 → 入方向规则，确认：
- 协议 TCP、端口 80、源 0.0.0.0/0（或你的办公网 IP）是允许的。

### 5. 查本机 iptables / firewalld

```bash
# firewalld
firewall-cmd --list-all
# public (active)
#   ports: 80/tcp 443/tcp

# iptables
iptables -L INPUT -n -v
# Chain INPUT (policy ACCEPT 100 packets)
# target     prot opt source               destination
# DROP       tcp  --  0.0.0.0/0            0.0.0.0/0            tcp dpt:80
```

看到 `DROP` 规则就是它了。

### 6. 看路由

```bash
ip route
# 默认路由对不对
ip route get 8.8.8.8
# 去办公网的路由有没有
```

## 根因

运维改安全组时，把 80 端口的入方向规则误删了。云平台安全组在操作系统之前就把包 DROP 了，客户端等不到 SYN/ACK，最终 connect timeout。

## 解决步骤

### 1. 临时止血：云安全组放行

去云控制台加规则：入方向 TCP 80 允许 0.0.0.0/0（或办公网 IP）。
加完立刻 `nc -zv 公网IP 80` 验证。

### 2. 本机防火墙放行（如果是 iptables 问题）

```bash
# firewalld
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https
firewall-cmd --reload

# 或 iptables
iptables -I INPUT -p tcp --dport 80 -j ACCEPT
service iptables save
```

### 3. 不要用 DROP 用 REJECT（排障友好）

排障阶段建议把 DROP 改成 REJECT，这样客户端立刻收到 refused，而不是傻等：

```bash
iptables -A INPUT -p tcp --dport 80 -j REJECT --reject-with tcp-reset
```

### 4. 路由问题

如果路由错了：

```bash
# 加默认路由
ip route add default via 192.168.1.1 dev eth0
```

## 验证与预防

- 外部 `nc -zv 公网IP 80` 通了。
- `tcpdump -i any port 80` 能看到 SYN + SYN/ACK + ACK 三次握手。
- 监控补：外部拨测 TCP 连通性。
- 记住：**timeout 三层检查——云安全组 → 本机 firewalld/iptables → 路由**。
- 改安全组后立刻从外部验证，不要改完就走。

## 相关

- 命令速查：[网络命令速查](/reference/network-commands)
- 网络方向：[Connection refused](/cases/t-port-connection-refused)
- 网络方向：[网络不通丢包](/cases/t-net-unreachable-mtr)
- 网络方向：[MTU 黑洞](/cases/t-mtu-black-hole)
