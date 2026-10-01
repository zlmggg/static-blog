---
category: 网络
difficulty: 中级
date: 2023-09-16
---

# 负载均衡后端被健康检查摘除（2023-09-16）

## 现象

Nginx 负载均衡后面挂了 3 台后端，监控显示后端健康检查失败率上升，Nginx 日志里大量 `no live upstreams`：

```
2023/09/16 10:00:00 [error] 1234#0: *5678 no live upstreams while connecting to upstream,
client: 1.2.3.4, server: api.example.com, request: "GET /api/foo HTTP/1.1",
upstream: "http://backend/api/foo"
```

或者云负载均衡（SLB/ALB）控制台显示某台后端 ECS 被标记为"异常"，流量不转发过去。

业务表现为：接口偶发 502/503，且只打到某几台机器时出问题。

## 环境

- 负载均衡：Nginx 1.22.1（自建），3 台后端
- 后端：Ubuntu 22.04.2 LTS，内核 `5.15.0-78-generic`，Tomcat 9.0.75
- 健康检查：Nginx 被动健康检查（max_fails=2, fail_timeout=10s）

## 定位过程

### 1. 先看 Nginx upstream 配置

```bash
grep -A10 upstream /etc/nginx/nginx.conf
# upstream backend {
#     server 10.0.0.1:8080 max_fails=2 fail_timeout=10s;
#     server 10.0.0.2:8080 max_fails=2 fail_timeout=10s;
#     server 10.0.0.3:8080 max_fails=2 fail_timeout=10s;
# }
```

`max_fails=2`：10 秒内失败 2 次，就把这台后端摘 10 秒。

### 2. 看 Nginx 日志里哪台后端在报错

```bash
grep "upstream" /var/log/nginx/error.log | grep -oP 'upstream: "http://\K[^:]+' | sort | uniq -c
#  1000 10.0.0.1:8080
#    50 10.0.0.2:8080
#    30 10.0.0.3:8080
```

10.0.0.1 报错最多，重点查它。

### 3. 直接从 Nginx 机器 curl 后端

```bash
curl -v http://10.0.0.1:8080/health
# 看是 connection refused（后端没起）、timeout（后端慢）、还是 500（应用错）
```

### 4. 看后端应用日志

```bash
# 后端机器上
tail -100 /var/log/tomcat/catalina.out
# 看是不是 OOM、Full GC、线程池满
```

### 5. 看是被动摘除还是主动健康检查失败

Nginx 默认是**被动**健康检查（只有真正请求失败才计数），不是主动探活。
云负载均衡一般是主动健康检查（定期 GET /health）。

- 被动摘除：说明真有用户请求失败了。
- 主动摘除：可能 /health 接口本身有问题。

```bash
# 看后端 /health 接口
curl http://10.0.0.1:8080/health
# 应该 200 OK，几 ms 返回
```

## 根因

10.0.0.1 这台 Tomcat 频繁 Full GC（一次 5 秒），期间所有请求超时。Nginx 被动健康检查连续 2 次超时，把它摘除 10 秒。GC 完后又恢复，流量打回来又 Full GC，循环。监控看到这台机器间歇性被摘。

## 解决步骤

### 1. 临时止血

把问题后端从 upstream 里先摘掉，让流量打到健康的机器：

```nginx
upstream backend {
    server 10.0.0.1:8080 down;   # 先停掉
    server 10.0.0.2:8080 max_fails=2 fail_timeout=10s;
    server 10.0.0.3:8080 max_fails=2 fail_timeout=10s;
}
```

```bash
nginx -t && systemctl reload nginx
```

### 2. 修后端

去 10.0.0.1 查 Tomcat Full GC 问题：

```bash
# 看 GC 日志
jstat -gcutil <pid> 1s 10
# Old 区是不是 100% 后才 Full GC

# 调大堆
# 启动参数 -Xmx4g -Xms4g
```

参考 [Tomcat 内存溢出](/cases/t-tomcat-oom-crash)。

### 3. 优化健康检查配置

Nginx 被动检查太粗糙，建议：

```nginx
upstream backend {
    server 10.0.0.1:8080 max_fails=3 fail_timeout=15s;
    server 10.0.0.2:8080 max_fails=3 fail_timeout=15s;
    server 10.0.0.3:8080 max_fails=3 fail_timeout=15s;
    # 最少保留 1 台
    queue 10s;
}
```

更精细的主动健康检查需要 Nginx Plus 或 OpenResty：

```nginx
# OpenResty lua-resty-checkups
```

### 4. 后端做优雅停机

发版时不要直接 kill，让负载均衡先摘流量再停：

```bash
# Tomcat 接 SIGTERM 后会先停接收新请求，处理完旧请求再退出
kill -TERM <pid>
```

## 验证与预防

- 修复后 Nginx error.log 不再有 `no live upstreams`。
- 后端健康检查连续 24 小时无失败。
- 监控补：每台后端的健康检查失败次数、upstream 响应时间。
- 告警阈值：任何一台后端被摘除立刻告警。
- 记住：**后端被摘不是负载均衡的问题，是后端真的有问题**，去查后端。

## 相关

- 命令速查：[网络命令速查](/reference/network-commands)
- 服务方向：[Nginx 502 Bad Gateway](/cases/t-nginx-502)
- 服务方向：[Nginx 504 Gateway Timeout](/cases/t-nginx-504-timeout)
- 服务方向：[Tomcat 内存溢出崩溃](/cases/t-tomcat-oom-crash)
