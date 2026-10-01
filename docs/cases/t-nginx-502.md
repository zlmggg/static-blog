---
category: 服务
difficulty: 中级
date: 2022-12-11
---

# Nginx 502 Bad Gateway（2022-12-11）

## 现象

用户访问网站，Nginx 返回 502：

```
<html>
<head><title>502 Bad Gateway</title></head>
<body>
<center><h1>502 Bad Gateway</h1></center>
<hr><center>nginx/1.20.1</center>
</body>
</html>
```

Nginx error.log 里：

```
2022/12/11 10:00:00 [error] 1234#0: *5678 connect() failed (111: Connection refused) while connecting to upstream, client: 1.2.3.4, server: api.example.com, request: "GET /api/foo HTTP/1.1", upstream: "http://127.0.0.1:9000/api/foo"
```

或者：

```
2022/12/11 10:00:01 [error] 1234#0: *5678 upstream prematurely closed connection while reading response header from upstream
```

## 环境

- 发行版：Rocky Linux release 8.6 (Green Obsidian)
- 内核：`4.18.0-372.9.1.el8.x86_64`
- Nginx 1.20.1，反向代理到本机 PHP-FPM 9000 端口
- PHP-FPM 7.4.33

## 定位过程

### 1. 先看 error.log 里的具体错误

502 不是一种病，是一类症状。先看错误码：

| error.log 关键字 | 含义 | 去哪查 |
|---|---|---|
| `Connection refused` | upstream 没起 | PHP-FPM/后端进程挂了 |
| `connect() failed (111: Connection refused)` | 端口没监听 | 后端服务没启动 |
| `upstream prematurely closed connection` | 后端进程崩了 | PHP-FPM 池崩溃/segfault |
| `recv() failed (104: Connection reset by peer)` | 后端 RST | 后端 panic/SELinux |
| `no live upstreams` | 所有后端都被摘了 | [LB 后端被摘](/cases/t-lb-backend-ejected) |

### 2. 确认后端进程在不在

```bash
# 看 PHP-FPM
ps -ef | grep php-fpm
systemctl status php-fpm
# active (running) 还是 failed？

# 看 9000 端口监听
ss -tlnp | grep :9000
# LISTEN 0 128 127.0.0.1:9000  0.0.0.0:*  users:(("php-fpm",pid=1234,fd=7))
```

如果没监听，就是 PHP-FPM 挂了。

### 3. 从 Nginx 机器直接 curl 后端

```bash
curl -v http://127.0.0.1:9000
# 如果 refused，后端没起
# 如果 hang 住，后端慢
```

### 4. 看 PHP-FPM 慢日志和错误日志

```bash
tail -50 /var/log/php-fpm/www-error.log
# 或
tail -50 /var/log/php-fpm/www-slow.log
```

### 5. 检查 SELinux

```bash
getenforce
# Enforcing

# Nginx 能不能连 PHP-FPM 9000
ausearch -m avc -ts recent | grep httpd
```

## 根因

PHP-FPM 进程池被慢请求打满，新请求进来没 worker 处理，`listen.backlog` 队列满后内核直接 RST，Nginx 收到 RST 返回 502。参考 [PHP-FPM 502](/cases/t-phpfpm-502)。

另一个常见根因：后端 Java/PHP 进程 OOM 被 kill，端口没人监听。

## 解决步骤

### 1. 临时止血：重启后端

```bash
systemctl restart php-fpm
systemctl status php-fpm
ss -tlnp | grep :9000
```

立刻恢复，但不治本。

### 2. 彻底修复：根据根因

如果是 PHP-FPM 池打满（参考 [PHP-FPM 502](/cases/t-phpfpm-502)）：

```
; /etc/php-fpm.d/www.conf
pm = dynamic
pm.max_children = 20
pm.start_servers = 5
pm.min_spare_servers = 2
pm.max_spare_servers = 8
pm.max_requests = 500
request_terminate_timeout = 30s
```

如果是后端进程 OOM：
- 加内存或修泄漏（参考 [OOM Killer](/cases/t-memory-leak-oom)）。

如果是 SELinux 拦了：

```bash
setsebool -P httpd_can_network_connect 1
```

### 3. Nginx 层加超时和重试

```nginx
location /api/ {
    proxy_pass http://backend;
    proxy_connect_timeout 5s;
    proxy_read_timeout 30s;
    proxy_next_upstream error timeout http_502 http_503;
    proxy_next_upstream_tries 2;
}
```

`proxy_next_upstream` 让 Nginx 在一台后端 502 时自动切下一台。

### 4. 加后端健康检查

```nginx
upstream backend {
    server 127.0.0.1:9000 max_fails=3 fail_timeout=10s;
}
```

## 验证与预防

- `curl -I http://localhost/api/foo` 返回 200。
- error.log 不再有 502 错误。
- 监控补：502 状态码比例、PHP-FPM 进程数、后端存活。
- 告警阈值：502 比例 > 1% 持续 1 分钟。
- 记住：**502 = Nginx 连不上/读不到后端，先看 error.log 的具体错误码**。

## 相关

- 命令速查：[网络命令速查](/reference/network-commands)
- 服务方向：[Nginx 504 Gateway Timeout](/cases/t-nginx-504-timeout)
- 服务方向：[PHP-FPM 进程池打满](/cases/t-phpfpm-502)
- 网络方向：[Connection refused](/cases/t-port-connection-refused)
