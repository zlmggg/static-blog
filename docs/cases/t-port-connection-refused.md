---
category: 网络
difficulty: 初级
date: 2020-03-17
---

# Connection refused：端口不通（2020-03-17）

## 现象

从客户端访问服务器的某个端口，立刻被拒：

```bash
curl -v http://10.0.0.2:8080
# * Connected to 10.0.0.2 (10.0.0.2) port 8080 (#0)
# * Connection refused
#   Failed to connect to 10.0.0.2 port 8080: Connection refused
```

或者：

```bash
telnet 10.0.0.2 8080
# Trying 10.0.0.2...
# telnet: Unable to connect to remote host: Connection refused
```

注意是 **refused**（立刻被拒），不是 timeout（等半天超时）。

## 环境

- 发行版：CentOS Linux release 7.7.1908 (Core)
- 内核：`3.10.0-1062.el7.x86_64`
- 目标服务：Java 应用监听 8080
- 客户端：同网段另一台机器

## 定位过程

### 1. 先分清 refused 和 timeout

| 现象 | 含义 | 去哪查 |
|---|---|---|
| `Connection refused` | 包到了服务器，但服务器上没人监听这个端口 | 服务起没起、监听地址对不对 |
| `Connection timed out` | 包根本没到服务器，或被防火墙 DROP | 防火墙/路由，看 [超时那篇](/cases/t-connection-timeout-firewall) |

refused 是内核回了 RST，说明网络是通的，端口没服务。

### 2. 在服务器上确认服务有没有监听

```bash
ss -tunlp | grep 8080
# 应该看到类似：
# LISTEN  0  128  *:8080  *:*  users:(("java",pid=1234,fd=10))
```

如果什么都没有，说明服务没起或没监听对端口。

```bash
# 确认服务进程在不在
ps -ef | grep java
systemctl status myapp
```

### 3. 关键：看监听地址是 127.0.0.1 还是 0.0.0.0

```bash
ss -tlnp | grep 8080
# LISTEN 0 128 127.0.0.1:8080  *:*  users:(("java",pid=1234,fd=10))
#              ^^^^^^^^^^^ 只监听本地回环，外部当然连不上！
```

这是最高频的坑：应用配了 `server.address=127.0.0.1`，只能本机访问。

正确的应该是：

```
LISTEN 0 128 0.0.0.0:8080  *:*    # 所有网卡都能连
# 或
LISTEN 0 128 10.0.0.2:8080  *:*   # 只绑指定网卡
```

### 4. 从服务器本机自测

```bash
curl -v http://127.0.0.1:8080
curl -v http://10.0.0.2:8080
```

- 本机 127.0.0.1 通、本机 IP 不通 → 监听地址问题（绑了 127.0.0.1）。
- 本机都不通 → 服务没起来。
- 本机都通、外部不通 → 防火墙问题（那就是 timeout 方向了）。

### 5. 看防火墙

```bash
# CentOS 7
firewall-cmd --list-ports
iptables -L -n | grep 8080
```

注意：防火墙 DROP 是 timeout，不是 refused。如果防火墙 REJECT 才是 refused。

## 根因

Java 应用的 `application.properties` 里配了 `server.address=127.0.0.1`，服务只监听回环地址，外部请求到了服务器内核，内核发现这个端口没人对外监听，直接回 RST，客户端看到 Connection refused。

## 解决步骤

### 1. 临时止血

如果服务没起，先拉起来：

```bash
systemctl start myapp
systemctl status myapp
```

如果监听地址错了，改配置：

`application.properties`：

```properties
server.address=0.0.0.0
# 或
server.address=10.0.0.2
server.port=8080
```

重启服务：

```bash
systemctl restart myapp
```

### 2. 确认监听正确

```bash
ss -tlnp | grep 8080
# LISTEN 0 128 0.0.0.0:8080  *:*  users:(("java",pid=2345,fd=10))
```

### 3. 防火墙放行

```bash
firewall-cmd --permanent --add-port=8080/tcp
firewall-cmd --reload
```

### 4. 从外部验证

```bash
# 从客户端
nc -zv 10.0.0.2 8080
# Connection to 10.0.0.2 8080 port [tcp/*] succeeded!
```

## 验证与预防

- 外部 `nc -zv` 通了。
- 部署脚本里检查 `ss -tlnp` 确认监听地址。
- 监控补：端口 TCP 连通性黑盒探测（每分钟从外部 nc 一下）。
- 告警阈值：端口不可达立刻告警。
- 记住：**refused = 端口没监听，timeout = 被防火墙挡**，先分清这两个再排查。

## 相关

- 命令速查：[网络命令速查](/reference/network-commands)
- 网络方向：[连接超时防火墙](/cases/t-connection-timeout-firewall)
- 网络方向：[DNS 解析失败](/cases/t-dns-resolution-fail)
- 服务方向：[Nginx 502 Bad Gateway](/cases/t-nginx-502)
