---
category: 服务
difficulty: 中级
date: 2021-10-19
---

# PHP-FPM 进程池打满导致 502（2021-10-19）

## 现象

网站间歇性 502，高峰时段尤其明显。Nginx error.log：

```
2021/10/19 10:00:00 [error] 1234#0: *5678 connect() failed (111: Connection refused) while connecting to upstream, upstream: "fastcgi://127.0.0.1:9000"
```

或者：

```
2021/10/19 10:00:01 [error] 1234#0: *5678 recv() failed (104: Connection reset by peer) while reading response header from upstream
```

PHP-FPM 日志：

```
[19-Oct-2021 10:00:00] WARNING: [pool www] server reached pm.max_children setting (10), consider raising it
```

## 环境

- 发行版：CentOS Linux release 7.9.2009 (Core)
- 内核：`3.10.0-1160.el7.x86_64`
- Nginx 1.20.1，PHP-FPM 7.4.24
- PHP 进程池配置：`pm.max_children = 10`

## 定位过程

### 1. 看 PHP-FPM 慢日志

```bash
tail -50 /var/log/php-fpm/www-slow.log
```

里面一堆请求耗时 30s+，都是同一个接口。

### 2. 看当前 PHP-FPM 进程数

```bash
ps -ef | grep php-fpm | grep -v grep | wc -l
# 11 个（1 master + 10 child）
# 正好等于 pm.max_children，全在忙
```

### 3. 看 PHP-FPM 状态页

先确保开了 status：

`/etc/php-fpm.d/www.conf`：

```
pm.status_path = /status
```

`/etc/nginx/conf.d/php-status.conf`：

```nginx
location /fpm-status {
    fastcgi_pass 127.0.0.1:9000;
    fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
    include fastcgi_params;
    allow 127.0.0.1;
    deny all;
}
```

```bash
curl http://127.0.0.1/fpm-status
# pool:                 www
# process manager:      dynamic
# start time:           19/Oct/2021:10:00:00 +0800
# start since:          3600
# accepted conn:        10000
# listen queue:         50      <- 这里 >0 说明积压了
# max listen queue:     100
# listen queue len:     128
# idle processes:       0       <- 没有空闲 worker
# active processes:     10      <- 全在忙
# total processes:      10
# max active processes: 10      <- 历史峰值
# max children reached: 5       <- 达到上限 5 次
```

`idle processes: 0` + `listen queue > 0` = 池打满了。

### 4. 看每个 PHP 进程占多少内存

```bash
ps -ylC php-fpm --sort:rss
# 每个 worker RSS 约 80M
# 10 个 worker = 800M
```

算一下：`pm.max_children = 可用内存 / 每个进程内存`。

## 根因

一个慢 SQL 接口没有索引，每个请求占一个 PHP-FPM worker 长达 20 秒。高峰期并发上来，10 个 worker 全被慢请求占住，新请求排在 `listen backlog` 队列里，队列满后内核 RST，Nginx 收到 RST 返回 502。

## 解决步骤

### 1. 临时止血

```bash
# 重启 PHP-FPM 释放卡住的 worker
systemctl restart php-fpm
```

### 2. 调大进程池（临时）

`/etc/php-fpm.d/www.conf`：

```
pm = dynamic
pm.max_children = 30
pm.start_servers = 10
pm.min_spare_servers = 5
pm.max_spare_servers = 15
pm.max_requests = 500
request_terminate_timeout = 30s
```

算一下：每个 worker 80M，30 个 = 2.4G，机器 8G 内存够。

```bash
systemctl restart php-fpm
```

### 3. 彻底修复：修慢请求

- 慢 SQL 加索引。
- 慢接口加缓存。
- 不要让 PHP 同步做耗时操作，丢队列异步处理。

### 4. 加 request_terminate_timeout

```
request_terminate_timeout = 30s
```

单个请求超过 30 秒直接杀掉，不让它长期占 worker。

### 5. Nginx 层 fastcgi 超时

```nginx
location ~ \.php$ {
    fastcgi_pass 127.0.0.1:9000;
    fastcgi_read_timeout 30s;
    fastcgi_send_timeout 30s;
}
```

## 验证与预防

- `curl http://127.0.0.1/fpm-status` 看 `idle processes > 0`，`listen queue = 0`。
- 监控补：PHP-FPM active/idle 进程数、listen queue、慢请求数。
- 告警阈值：`max children reached` 事件、listen queue > 0。
- 记住：**PHP-FPM 502 先看慢日志和 status 页，不是简单加 max_children**。

## 相关

- 命令速查：[Linux 命令速查](/reference/linux-commands)
- 服务方向：[Nginx 502 Bad Gateway](/cases/t-nginx-502)
- 服务方向：[Nginx 504 Gateway Timeout](/cases/t-nginx-504-timeout)
- 权限方向：[Permission denied](/cases/t-permission-ownership)
