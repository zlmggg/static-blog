---
title: Nginx 实战
description: Nginx 事件模型与安装、配置结构、虚拟主机、location 优先级与 rewrite、反向代理、负载均衡算法、HTTPS/HTTP2、gzip/缓存/限流
---

# Nginx 实战

::: tip 本篇定位
掌握 Nginx **事件模型、多种安装、配置结构与热重载**，会配置**虚拟主机、location/rewrite、反向代理、负载均衡、HTTPS、性能优化与限流**，并能排查常见问题。
:::

## 先建立全局观：Nginx 为什么能扛高并发

- **事件驱动 + 异步非阻塞**：Linux 用 epoll，一个 worker 可同时处理大量连接，无需为每个连接开线程；
- **master / worker 多进程**：一个 master 管理多个 worker，worker 处理请求，可利用多核；
- 内存占用低、静态服务快，擅长反向代理与负载均衡。

```
master（读配置、管理 worker）
 ├─ worker（处理连接）
 ├─ worker
 └─ worker
```

---

## 一、简介与安装

### 1.1 能做什么

静态资源服务、HTTP 反向代理、负载均衡、虚拟主机、HTTPS、缓存、限流、动静分离。

### 1.2 RHEL/Rocky

```bash
sudo dnf install -y nginx
sudo systemctl enable --now nginx
```

### 1.3 Debian/Ubuntu

```bash
sudo apt update && sudo apt install -y nginx
sudo systemctl enable --now nginx
```

### 1.4 Docker（版本锁定）

```bash
docker run -d --name nginx -p 80:80 -p 443:443 \
  -v /data/nginx/nginx.conf:/etc/nginx/nginx.conf:ro \
  -v /data/nginx/conf.d:/etc/nginx/conf.d:ro \
  -v /data/www:/usr/share/nginx/html:ro \
  -v /data/logs/nginx:/var/log/nginx \
  nginx:1.30.5-alpine
```

### 1.5 目录与命令

| 路径 | 说明 |
|---|---|
| /etc/nginx/nginx.conf | 主配置 |
| /etc/nginx/conf.d/*.conf | 子配置（RHEL） |
| /etc/nginx/sites-available、sites-enabled | Debian 风格站点 |
| /usr/share/nginx/html | 默认站点根目录 |
| /var/log/nginx/access.log、error.log | 访问/错误日志 |

```bash
nginx -t                 # 检查配置（改完必做）
nginx -s reload          # 热重载（不断连接）
nginx -s stop/quit       # 快速/优雅停止
systemctl restart nginx
```

---

## 二、配置结构与语法

### 2.1 块结构

```nginx
# 全局块 main：进程用户、worker 数、日志
user  nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;

events {                    # 连接处理
    worker_connections 10240;
    use epoll;
}

http {                      # HTTP 全局
    include       mime.types;
    default_type  application/octet-stream;
    sendfile      on;
    keepalive_timeout 65;
    gzip on;

    server {                # 一个 server = 一个虚拟主机
        listen 80;
        server_name example.com;

        location / {        # 路径匹配
            root /usr/share/nginx/html;
            index index.html;
        }
    }
}
```

### 2.2 语法要点

- 每条指令以 `;` 结尾，块用 `{}`；
- `#` 注释；
- 同一 server 内多个 location；
- 配置错误会导致 reload 失败，**先 nginx -t**。

---

## 三、虚拟主机

一台服务器、一个 Nginx 服务多个站点，靠 server 区分。

### 3.1 基于名称（最常用）

```nginx
server {
    listen 80;
    server_name www.a.com a.com;
    root /data/www/a;
    index index.html;
}

server {
    listen 80;
    server_name www.b.com;
    root /data/www/b;
    index index.html;
}
```

### 3.2 基于端口 / IP

```nginx
server { listen 8080; server_name _; root /data/web8080; }
server { listen 80;   server_name 10.0.0.13; root /data/webip; }
```

### 3.3 目录权限

::: warning 403 Forbidden 常见原因
- 站点根目录或上级目录**没有执行/读取权限**（Nginx 用户需能进入目录）；
- 目录下**没有 index 指定的首页**且未开 autoindex（directory index forbidden）；
- SELinux 拦截（RHEL：`getenforce`，需设目录上下文）。
:::

---

## 四、location 与 rewrite

### 4.1 location 匹配规则

| 修饰符 | 含义 |
|---|---|
| `= /path` | 精确匹配，最高优先 |
| `^~ /path` | 前缀匹配，命中后不再查正则 |
| `~ /path` | 区分大小写正则 |
| `~* /path` | 不区分大小写正则 |
| `/path` | 普通前缀 |
| `/` | 默认 |

**优先级：** `=` > `^~` > 正则（`~`/`~*`，按书写顺序）> 普通前缀（最长优先）。

```nginx
location = /favicon.ico { ... }
location ^~ /static/ { root /data; }
location ~* \.(jpg|png|gif)$ { expires 7d; }
location / { proxy_pass http://backend; }
```

### 4.2 rewrite / return

```nginx
rewrite ^/old/(.*)$ /new/$1 last;
return 301 https://$host$request_uri;
return 403;
```

- flag：`last`（重写后重新匹配 location）、`break`（当前 location 内停止）、`redirect`（302）、`permanent`（301）；
- 简单跳转优先用 `return`，逻辑改写用 rewrite。

---

## 五、反向代理

把请求转发给后端服务（Tomcat、Node、应用），Nginx 对外。

```nginx
location /api/ {
    proxy_pass http://127.0.0.1:8080/;
    proxy_set_header Host              $host;
    proxy_set_header X-Real-IP         $remote_addr;
    proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_connect_timeout 5s;
    proxy_read_timeout    60s;
    proxy_send_timeout    60s;
}
```

::: warning proxy_pass 末尾斜杠
`proxy_pass http://x/;`（带路径/斜杠）会**替换**掉匹配的 location 前缀；不带则保留原 URI。这是最容易踩的坑，要按后端期望路径决定。
:::

后端要获取真实客户端 IP，需正确传 X-Forwarded-For 并在后端配置信任代理。

---

## 六、负载均衡

### 6.1 upstream

```nginx
upstream backend {
    server 10.0.0.21:8080 weight=3;
    server 10.0.0.22:8080 weight=1;
    server 10.0.0.23:8080 backup;     # 备用
    server 10.0.0.24:8080 down;       # 下线
}

server {
    location / { proxy_pass http://backend; }
}
```

### 6.2 算法

| 算法 | 说明 |
|---|---|
| round robin（默认） | 轮询，可配 weight 加权 |
| ip_hash | 按客户端 IP 哈希，**保持会话** |
| least_conn | 分给连接数最少的 |
| hash $key | 按指定 key 哈希（第三方/内置 hash） |
| fair（第三方） | 按响应时间 |

### 6.3 健康与参数

`max_fails=n`、`fail_timeout` 控制失败摘除；被动健康检查；主动健康检查需开源版配合或商业版。

---

## 七、HTTPS 与 HTTP/2

### 7.1 配置

```nginx
server {
    listen 443 ssl;
    http2 on;
    server_name www.sersec.com;

    ssl_certificate     /data/certs/fullchain.pem;
    ssl_certificate_key /data/certs/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;
    ssl_session_cache   shared:SSL:10m;
    ssl_session_timeout 10m;

    location / { root /data/www; index index.html; }
}

# 80 强制跳 HTTPS
server {
    listen 80;
    server_name www.sersec.com;
    return 301 https://$host$request_uri;
}
```

证书可用 acme.sh + Let's Encrypt 自动申请续期（备案/解析完成后）。

---

## 八、性能与限流

### 8.1 静态与压缩

```nginx
gzip on;
gzip_min_length 1k;
gzip_comp_level 5;
gzip_types text/plain text/css application/json application/javascript text/xml;
gzip_vary on;

sendfile on;
tcp_nopush on;
keepalive_timeout 65;
client_max_body_size 20m;
```

### 8.2 缓存与过期

```nginx
location ~* \.(jpg|png|css|js|woff2)$ {
    expires 7d;
    add_header Cache-Control "public";
}
# proxy_cache_path + proxy_cache 可缓存后端响应
```

### 8.3 限流

```nginx
# 请求速率（漏桶）
limit_req_zone  $binary_remote_addr zone=req:10m rate=10r/s;
# 并发连接
limit_conn_zone $binary_remote_addr zone=conn:10m;

server {
    location /api/ {
        limit_req  zone=req burst=20 nodelay;
        limit_conn conn 10;
        proxy_pass http://backend;
    }
}
```

---

## 面试自测

1. Nginx 为什么能处理高并发？master 和 worker 各做什么？
2. nginx -t 和 reload 的作用？改配置为什么要先 -t？
3. location 的匹配优先级？
4. proxy_pass 带不带末尾斜杠有什么区别？
5. Nginx 负载均衡有哪些算法？ip_hash 解决什么？
6. 如何配置 HTTPS 和 HTTP 强制跳转？
7. 403、502 分别常见于什么情况？
8. limit_req 和 limit_conn 的区别？

## 相关速查

- [Linux 命令速查](/reference/linux-commands)
- Nginx 官方文档：https://nginx.org/en/docs/
- Nginx 配置示例（官方）：https://nginx.org/en/docs/example.html
