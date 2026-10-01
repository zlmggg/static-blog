---
category: Linux
difficulty: 中级
date: 2022-10-27
---

# Too many open files：文件句柄耗尽（2022-10-27）

## 现象

Nginx 日志里大量报错，业务间歇性 502：

```
socket() failed (24: Too many open files) while connecting to upstream
```

Java 应用报错：

```
java.net.SocketException: Too many open files
```

MySQL 报错：

```
ERROR 2024 (HY000): Should have thrown an error now
Can't open file: './mydb/mytable.MYI' (errno: 24)
```

重启服务能恢复一阵，跑几个小时又犯。

## 环境

- 发行版：Rocky Linux release 8.6 (Green Obsidian)
- 内核：`4.18.0-372.9.1.el8.x86_64`
- Nginx 1.22.0，MySQL 8.0.30
- 业务：Nginx 反向代理 + 后端 Java 服务

## 定位过程

### 1. 先看进程当前打开了多少 fd，上限是多少

```bash
# 找到 nginx master 进程 PID
master_pid=$(cat /run/nginx.pid)

# 当前打开的 fd 数
ls /proc/$master_pid/fd | wc -l

# 硬限制和软限制
cat /proc/$master_pid/limits | grep "open files"
# Max open files  1024  4096  files
```

软限制 4096，但 fd 数已经 4090 了，快爆了。

### 2. 看这些 fd 都是什么

```bash
ls -l /proc/$master_pid/fd | awk '{print $NF}' | sort | uniq -c | sort -rn | head
#  3800 socket:[123456]   <- 大量 socket
#   100 /var/log/nginx/access.log
#    50 /etc/nginx/...
```

大量 `socket:[xxx]` 说明是连接没释放，fd 泄漏在网络连接上。

### 3. 全系统统计谁在占 fd

```bash
# 用 lsof 按进程汇总
lsof -n | awk '{print $2,$1}' | sort | uniq -c | sort -rn | head
#  4096 1234 nginx
#  1024 5678 java
```

### 4. 看系统级别的 fd 上限

```bash
cat /proc/sys/fs/file-nr
#  12345  0  600000
# 第一个数：已分配的 fd
# 第二个数：空闲的
# 第三个数：系统总上限
```

系统级 60 万够用，是单进程的 ulimit 不够。

## 根因

Nginx worker 处理短连接时，后端 Java 服务响应慢，连接一直处于 `CLOSE_WAIT`，Nginx 这边的 fd 不释放。同时 `nginx.conf` 里没调 `worker_rlimit_nofile`，默认软限制 1024/4096 被打满。

## 解决步骤

### 1. 临时止血：立刻提高上限

```bash
# 对正在跑的 nginx master 进程，直接改（不用重启）
prlimit --pid $master_pid --nofile=65535:65535

# 验证
cat /proc/$master_pid/limits | grep "open files"
```

### 2. 永久修复：调 ulimit

方式 A：在 nginx 配置里直接写（推荐，对 nginx 生效）：

`/etc/nginx/nginx.conf` 顶层：

```
worker_rlimit_nofile 65535;

events {
    worker_connections  65535;
    use epoll;
    multi_accept on;
}
```

方式 B：systemd service 里配：

`/etc/systemd/system/nginx.service.d/override.conf`：

```
[Service]
LimitNOFILE=65535
```

然后：

```bash
systemctl daemon-reload
systemctl restart nginx
```

方式 C：全局 `/etc/security/limits.conf`：

```
*  soft  nofile  65535
*  hard  nofile  65535
```

注意：systemd 启动的服务不读 `/etc/security/limits.conf`，必须用方式 A 或 B。

### 3. 修根因：CLOSE_WAIT 泄漏

```bash
ss -s
# TCP:   estab 1234 ...
netstat -an | grep CLOSE_WAIT | wc -l
```

CLOSE_WAIT 堆积说明后端应用没正确 close 连接。去后端 Java 服务查连接池配置，是不是 HTTP 连接没设超时。

## 验证与预防

- 修复后 `ls /proc/$(cat /run/nginx.pid)/fd | wc -l` 稳定在几百，不再随时间上涨。
- 监控补：进程 fd 使用率（`/proc/<pid>/fd` 数量 / limits 里的 Max open files）。
- 告警阈值：fd 使用率 > 70% 预警，> 90% 紧急。
- 记住：**`Too many open files` 不是改 ulimit 就完了，一定要看 fd 都被谁占了**，socket 堆积通常是连接泄漏。

## 相关

- 命令速查：[Linux 命令速查](/reference/linux-commands)
- 网络方向：[TCP 重传率高](/cases/t-tcp-retransmission)
- 磁盘方向：[磁盘空间写满](/cases/t-disk-space-full)
- 服务方向：[Nginx 502 Bad Gateway](/cases/t-nginx-502)
