---
category: DevOps
difficulty: 中级
---

# 生产配置最佳实践模板（逐项注释"为什么"）

::: tip 本篇定位
把生产里最常配的五类——Nginx、MySQL、Redis、Kubernetes、内核 sysctl——整理成**可整段复制、每行带注释为什么这么设**的模板。抄走后按机器规格改数值即可。不重复各数据/服务专题的原理，这里是"开箱即用的配置基线"。
本篇版本：Nginx 1.30.5（stable）、MySQL 8.4 LTS、Redis 8.x、Kubernetes 1.30+、内核 4.18~7.0。模板为基线，按实际规格调数值。
:::

## 一、Nginx（1.30.5）

```nginx
# /etc/nginx/nginx.conf —— 通用生产基线
user  nginx;
worker_processes auto;          # 等于 CPU 核数；auto 自动探测，别写死 1，多核才能吃满
error_log  /var/log/nginx/error.log warn;
pid        /run/nginx.pid;

events {
    worker_connections 65535;   # 单 worker 最大连接；要和系统 nofile 一起调
    multi_accept on;            # 一次 accept 尽可能多连接，提升突发吞吐
    use epoll;                  # Linux 高并发用 epoll，别用 select
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    sendfile on;                # 内核态零拷贝发文件，比用户态快
    tcp_nopush on;              # 攒满 MSS 再发，配合 sendfile 提升吞吐
    tcp_nodelay on;             # 长连接小消息不延迟发，降低实时延迟
    keepalive_timeout 65;        # 客户端长连接超时，别太短（频繁建连）也别太长（占资源）
    keepalive_requests 1000;     # 单连接可复用请求数，高并发调大，否则老连接被断

    # 压缩：降带宽，JSON/文本响应体积可降 60%+
    gzip on;
    gzip_min_length 1k;          # 太小的不压，省 CPU
    gzip_types text/plain application/json text/css application/javascript;

    # 安全响应头（防常见 Web 攻击，按业务裁剪）
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options SAMEORIGIN;
    add_header X-XSS-Protection "1; mode=block";

    # 限流：见 expert-high-concurrency，这里给基线
    limit_req_zone $binary_remote_addr zone=perip:10m rate=20r/s;

    server {
        listen 443 ssl;
        server_name example.com;

        ssl_certificate     /etc/nginx/ssl/example.crt;
        ssl_certificate_key /etc/nginx/ssl/example.key;
        ssl_protocols       TLSv1.2 TLSv1.3;   # 禁用旧 SSL/TLS1.0/1.1
        ssl_ciphers         HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;
        ssl_session_cache   shared:SSL:10m;     # 会话复用，减少握手开销
        ssl_session_timeout 1d;

        location /api/ {
            limit_req zone=perip burst=40 nodelay;  # 突发 40 个排队
            limit_req_status 429;
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_http_version 1.1;          # 到上游用 HTTP/1.1，才能用 keepalive
            proxy_set_header Connection "";   # 清空 Connection 头，启用上游长连接
        }
    }
}
```

## 二、MySQL（8.4 LTS）

```ini
# /etc/my.cnf —— 专库专用基线（假设 16G 内存、SSD）
[mysqld]
user            = mysql
port            = 3306
datadir         = /var/lib/mysql
socket          = /var/lib/mysql/mysql.sock

# —— 连接 ——
max_connections = 500            # 按连接池总和留余量；别盲目 1000+，每连接都吃内存
back_log        = 1024           # 连接请求排队，要和 somaxconn 对齐

# —— InnoDB 最关键的参数 ——
innodb_buffer_pool_size = 10G    # 专用库给物理内存 50%~70%；把热点数据放内存，最影响性能
innodb_log_file_size    = 2G     # redo 日志；大一点减少刷盘频率，但崩溃恢复变慢
innodb_flush_log_at_trx_commit = 1  # 1=每次事务刷盘最安全；性能敏感可评估 2（宕机丢 1s）
innodb_flush_method     = O_DIRECT # 绕过 OS 缓存，避免和 MySQL 双缓存浪费内存

# —— 慢查询与日志 ——
slow_query_log       = ON
slow_query_log_file  = /var/log/mysql/slow.log
long_query_time      = 1          # 超过 1s 记慢查询，找优化对象
log_error            = /var/log/mysql/error.log

# —— 字符集 ——
character_set_server  = utf8mb4   # utf8mb4 才能存 emoji，别用旧 utf8
collation_server      = utf8mb4_0900_ai_ci

# —— 安全 ——
local_infile         = OFF       # 禁用 load data local，防文件读取
skip_symbolic_links  = ON
```

```bash
# 改完重启并验证
systemctl restart mysqld
mysql -e "SHOW VARIABLES LIKE 'innodb_buffer_pool_size';"
mysql -e "SHOW VARIABLES LIKE 'character_set_server';"
```

## 三、Redis（8.x）

```conf
# /etc/redis/redis.conf —— 基线
bind 0.0.0.0                    # 生产建议绑内网网卡，别裸奔公网
port 6379
protected-mode yes              # 开保护模式，没密码时拒绝外网

# —— 安全（必须）——
requirepass    你的强密码        # 一定要设密码，否则分分钟被挖矿
rename-command FLUSHALL ""      # 禁用危险命令（按需），防误操作/攻击
rename-command CONFIG ""

# —— 内存与淘汰 ——
maxmemory                4gb    # 设上限，别让 Redis 吃满机器内存
maxmemory-policy        allkeys-lru  # 内存满时按 LRU 淘汰；缓存场景必设
maxmemory-samples        5

# —— 持久化（按业务选）——
# RDB：定时快照，恢复快、丢数据多
save 900 1
save 300 10
# AOF：每次写日志，丢数据少、文件大
appendonly yes
appendfsync everysec            # 每秒刷盘，性能与安全折中

# —— 慢日志 ——
slowlog-log-slower-than 10000   # 超过 10ms 记慢日志
slowlog-max-len 128
```

```bash
systemctl restart redis
redis-cli -a 你的强密码 INFO memory | grep used_memory_human
```

## 四、Kubernetes（1.30+）

```yaml
# 一个生产 Deployment 基线（requests/limits/PDB/探针/NetworkPolicy 思路）
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
spec:
  replicas: 3
  template:
    spec:
      containers:
        - name: app
          image: registry.example.com/app:v1.0.0   # 固定 tag，别用 latest
          resources:
            requests:                # 调度依据：保底资源
              cpu: "500m"
              memory: "512Mi"
            limits:                  # 上限：防止一个 Pod 吃满节点
              cpu: "1"
              memory: "1Gi"
          readinessProbe:            # 就绪探针：没好就不接流量
            httpGet: { path: /health, port: 8080 }
            initialDelaySeconds: 5
            periodSeconds: 5
          livenessProbe:             # 存活探针：挂了自动重启
            httpGet: { path: /health, port: 8080 }
            initialDelaySeconds: 15
            periodSeconds: 10
---
# PDB：保证升级/故障时至少留一个副本可用，不被一次全杀
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: app-pdb
spec:
  minAvailable: 1
  selector:
    matchLabels: { app: app }
---
# NetworkPolicy：默认拒绝跨命名空间访问，只放行需要的
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: app-netpol
spec:
  podSelector: { matchLabels: { app: app } }
  policyTypes: ["Ingress"]
  ingress:
    - from:
        - podSelector: { matchLabels: { role: gateway } }
      ports: [{ protocol: TCP, port: 8080 }]
```

> 数值按实际压测调：`requests` 太小会被频繁驱逐，`limits` 太大会 OOMKilled。JVM 应用记得用 `-XX:MaxRAMPercentage=75` 对齐容器 limit。

## 五、内核 sysctl（4.18 ~ 7.0）

```ini
# /etc/sysctl.d/99-prod.conf —— 高并发 Web/DB 通用基线

# —— 文件句柄 ——
fs.file-max = 1048576              # 系统级总句柄上限
# 进程级配合 systemd LimitNOFILE=65535 或 limits.conf

# —— TCP 连接队列 ——
net.core.somaxconn = 65535          # 全连接队列，默认 128 太小，高并发必调
net.ipv4.tcp_max_syn_backlog = 65535  # 半连接队列

# —— TIME_WAIT 与本地端口 ——
net.ipv4.tcp_tw_reuse = 1           # 复用 TIME_WAIT 给新出站连接（安全）
# 注意：不要开 tcp_tw_recycle，新内核已废弃，NAT 环境会丢连接
net.ipv4.ip_local_port_range = 1024 65535  # 客户端出口端口范围，压测/外连多必调

# —— TCP 缓冲区（高 BDP 网络可调大）——
net.core.rmem_default = 262144
net.core.wmem_default = 262144
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216

# —— 内存 overcommit（DB 场景建议）——
vm.overcommit_memory = 1           # Redis 推荐 1；MySQL 场景评估 0/2，按业务

# —— 反向路由校验（容器/多网卡环境按需）——
# net.ipv4.conf.all.rp_filter = 2
```

```bash
sysctl --system                     # 加载所有 /etc/sysctl.d/*.conf
sysctl net.core.somaxconn           # 验证生效
```

## 调参前后对照（基线参考）

| 参数 | 默认 | 基线建议 | 改后收益 |
|---|---|---|---|
| `worker_connections` | 512 | 65535 | 单机并发上限提升 |
| `somaxconn` | 128 | 65535 | 消除 ListenOverflows 丢连接 |
| `innodb_buffer_pool_size` | 128M | 物理内存 50~70% | 热点数据内存命中，查询快数倍 |
| `maxmemory`(Redis) | 无上限 | 4G + LRU | 防止 Redis 吃满机器 |
| `tcp_tw_reuse` | 0 | 1 | 高并发短连接不再端口耗尽 |
| `requests/limits`(K8s) | 不设 | 按压测设 | 节点不被单个 Pod 拖垮 |

::: warning 生产红线
- 所有数值按**实际机器规格和压测结果**调，别照抄——16G 内存和 64G 机器的 buffer_pool 不能一样。
- sysctl 改完用 `sysctl --system` 生效；进程级 nofile 要在 systemd unit 里设，limits.conf 对 systemd 服务常不生效。
- Redis 务必 `requirepass` + 绑内网；MySQL 别开 `local_infile`。
- K8s 镜像 tag 固定具体版本，禁止 `latest`；探针配错会导致服务起不来/频繁重启。
- 改任何生产配置前备份原文件，留回滚命令。
:::

## 相关速查

- Nginx 原理与更多：[Nginx Web 服务](./services-web-nginx)
- MySQL 进阶：[MySQL 数据](./data-mysql)
- Redis 高可用：[Redis](./data-redis)
- K8s 有状态与安全：[StatefulSet 与安全](./container-k8s-04-statefulset-security)
- 内核参数详解：[Linux 内核与 sysctl](./linux-kernel)
- 性能调优全流程：[性能调优实战](./expert-perf-tuning)
- 配置/上线 Checklist：[/reference/ops-checklists](/reference/ops-checklists)

### 官方文档

- Nginx 控制参数：https://nginx.org/en/docs/dirindex.html
- MySQL 8.4 服务参数：https://dev.mysql.com/doc/refman/8.4/en/server-options.html
- Redis 配置：https://redis.io/docs/latest/operate/oss_and_stack/management/config/
- Kubernetes 最佳实践：https://kubernetes.io/docs/concepts/configuration/overview/
- sysctl：https://man7.org/linux/man-pages/man5/sysctl.conf.5.html
