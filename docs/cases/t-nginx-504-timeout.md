---
category: 服务
difficulty: 中级
date: 2023-06-24
---

# Nginx 504 Gateway Timeout（2023-06-24）

## 现象

用户访问接口，等了 60 多秒后 Nginx 返回：

```
504 Gateway Time-out
```

Nginx error.log：

```
2023/06/24 14:00:00 [error] 1234#0: *5678 upstream timed out (110: Connection timed out) while reading response header from upstream, client: 1.2.3.4, server: api.example.com, request: "GET /api/report HTTP/1.1", upstream: "http://127.0.0.1:8080/api/report"
```

和 502 不同，504 是 **Nginx 连上了后端，但后端太慢，超过 Nginx 等的时间还没返回响应头**。

## 环境

- 发行版：Ubuntu 22.04.2 LTS
- 内核：`5.15.0-71-generic`
- Nginx 1.22.1，反向代理到 Tomcat 9.0.74
- 业务：报表接口，要查大量数据

## 定位过程

### 1. 先确认是 Nginx 超时还是后端真慢

```bash
# 从 Nginx 机器直接 curl 后端，看后端多久返回
time curl -v http://127.0.0.1:8080/api/report
# 如果后端本身要 90s，那就是后端慢，Nginx 默认 60s 等不到
```

### 2. 看 Nginx 超时配置

```bash
grep -E "proxy_read_timeout|proxy_connect_timeout|proxy_send_timeout" /etc/nginx/nginx.conf
# 默认 60s
```

| 配置 | 默认 | 含义 |
|---|---|---|
| `proxy_connect_timeout` | 60s | 连后端 TCP 握手超时 |
| `proxy_send_timeout` | 60s | 发请求体给后端超时 |
| `proxy_read_timeout` | 60s | 读后端响应头超时（最常踩） |

### 3. 看后端为什么慢

```bash
# Tomcat 日志
tail -100 /var/log/tomcat/localhost.out
# 慢 SQL、GC、线程池满

# 看后端进程 CPU/IO
top
iostat -x 1
```

### 4. 区分：是后端真的在处理，还是卡死了

```bash
# 看 Tomcat 线程池
jstack <pid> | grep -c "BLOCKED"
# BLOCKED 多说明锁竞争

jstack <pid> | grep "http-nio-8080" | head
# 看请求卡在哪个栈
```

## 根因

报表接口要跑一个全表统计 SQL，没加索引，MySQL 跑了 90 秒才返回。Nginx 默认 `proxy_read_timeout 60s`，60 秒等不到响应头，主动断开，返回 504。

## 解决步骤

### 1. 临时止血：调大 Nginx 超时

`/etc/nginx/nginx.conf` 或站点配置：

```nginx
location /api/report {
    proxy_pass http://tomcat_backend;
    proxy_connect_timeout 10s;
    proxy_send_timeout 120s;
    proxy_read_timeout 120s;   # 关键，从 60s 调到 120s
}
```

```bash
nginx -t && systemctl reload nginx
```

注意：调大超时只是治标，不要把所有接口都调到 300s，会拖垮后端。

### 2. 彻底修复：让后端快起来

- 慢 SQL 加索引：`slow_query_log = 1`，`EXPLAIN` 看执行计划。
- 报表接口加缓存（Redis），不要每次都全表查。
- 异步化：报表接口立刻返回任务 ID，后台跑，轮询结果。

### 3. 后端自己也要超时

Tomcat 也要有超时，不要让一个慢请求占着线程：

`server.xml`：

```xml
<Connector port="8080" protocol="HTTP/1.1"
           connectionTimeout="20000"
           keepAliveTimeout="60000" />
```

### 4. 前端加 loading 和超时提示

不要让用户傻等 60 秒。

## 验证与预防

- 报表接口在 Nginx 超时内能返回。
- 监控补：后端接口响应时间 P99、Nginx 504 比例。
- 告警阈值：接口 P99 > 5s 告警、504 比例 > 0.5%。
- 记住：**504 是后端慢，不是 Nginx 问题**。先让后端快，再考虑调超时。
- 长任务一定要异步化，不要让 HTTP 请求同步等。

## 相关

- 命令速查：[网络命令速查](/reference/network-commands)
- 服务方向：[Nginx 502 Bad Gateway](/cases/t-nginx-502)
- 服务方向：[Tomcat 内存溢出崩溃](/cases/t-tomcat-oom-crash)
- 网络方向：[TCP 重传率高](/cases/t-tcp-retransmission)
