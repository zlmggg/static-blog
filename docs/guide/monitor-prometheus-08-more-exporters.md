---
category: 监控
difficulty: 中级
---

# Prometheus 实战 08：Nginx/JMX/Blackbox 等 Exporter

> **Prometheus 实战系列（共 10 篇）**
> ← 上一篇 [Prometheus 实战 07](./monitor-prometheus-07-discovery-exporters) ｜ 下一篇 [Prometheus 实战 09](./monitor-prometheus-09-container-federation-storage) →
> [返回监控索引](./monitor)

### 7.4 Nginx 监控

Nginx 自身不暴露指标，有三种实现：

| 方式 | 原理 | 适用场景 |
| --- | --- | --- |
| **nginx-prometheus-exporter（推荐）** | 官方 exporter 采集 Nginx 的 stub_status 状态页 | 绝大多数 Nginx，无需重新编译 |
| nginx-lua-prometheus | Lua 库在 Nginx 内直接记录指标，需 lua-nginx-module（OpenResty） | 需要按 URI/维度细分的场景 |
| nginx-vts + nginx-vts-exporter | 编译加 vts 模块输出 JSON 状态，exporter 采集 | 需要虚拟主机维度流量统计 |

#### 7.4.1 方式一：nginx-prometheus-exporter

**第 1 步：开启 stub_status**

在 web01 安装 Nginx：

```bash
apt update && apt -y install nginx
```

创建 `/etc/nginx/conf.d/status.conf`：

```nginx
server {
    listen 8888;
    server_name localhost;

    location /basic_status {
        stub_status;
        access_log off;
        allow 127.0.0.1;
        allow 10.0.0.0/8;
        deny all;
    }
}
```

也可以直接在默认站点 `/etc/nginx/sites-enabled/default` 的 server 块里加 `location /basic_status { stub_status; }`。

生效并查看：

```bash
nginx -t
systemctl reload nginx
curl 127.0.0.1:8888/basic_status
```

预期输出：

```text
Active connections: 1
server accepts handled requests
 3 3 3
Reading: 0 Writing: 1 Waiting: 0
```

字段含义：`Active connections` 当前活跃连接数；`accepts` 已接受的总连接；`handled` 已处理的总连接（正常与 accepts 相等，差值即被丢弃的连接）；`requests` 总请求数；`Reading` 正在读请求头的连接；`Writing` 正在返回响应的连接；`Waiting` 等待中的空闲连接（keepalive）。

**第 2 步：启动 exporter 容器**

```bash
docker run -d --name nginx-exporter --restart=always -p 9113:9113 \
  nginx/nginx-prometheus-exporter:1.5.3 \
  --nginx.scrape-uri=http://【Web服务器IP】:8888/basic_status
```

参数解释：`--nginx.scrape-uri` stub_status 页面地址（Exporter 要能访问到，注意上面 allow 放行）。默认监听 9113。

验证：

```bash
curl -s localhost:9113/metrics | grep -E 'nginx_up|nginx_connections_active|nginx_http_requests_total'
```

预期输出：

```text
nginx_connections_accepted 3
nginx_connections_active 1
nginx_connections_handled 3
nginx_connections_reading 0
nginx_connections_waiting 0
nginx_connections_writing 1
nginx_http_requests_total 3
nginx_up 1
```

**第 3 步：采集与看板**

prometheus.yml 加：

```yaml
  - job_name: 'nginx_exporter'
    static_configs:
      - targets: ['【Web服务器IP】:9113']
        labels:
          app: nginx
```

```bash
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus
```

Grafana 看板 11199、14900：

```text
https://grafana.com/grafana/dashboards/11199-nginx/
```

**Docker Compose 一体化**（Nginx + exporter）：

```yaml
version: '3.6'

networks:
  monitoring:
    driver: bridge

services:
  nginx:
    image: nginx:1.27
    restart: always
    volumes:
      - ./nginx/stub_status-server.conf:/etc/nginx/conf.d/stub_status-server.conf:ro
    networks:
      - monitoring
    ports:
      - "80:80"

  nginx-exporter:
    image: nginx/nginx-prometheus-exporter:1.5.3
    restart: always
    command:
      - '--nginx.scrape-uri=http://nginx:8080/stub_status'
    networks:
      - monitoring
    ports:
      - "9113:9113"
    depends_on:
      - nginx
```

`stub_status-server.conf` 里 server 监听 8080，location 为 `/stub_status { stub_status; }`。

#### 7.4.2 方式二：nginx-lua-prometheus（了解）

使用 OpenResty 或编译了 lua-nginx-module 的 Nginx，`lua_shared_dict prometheus_metrics 10m;` 定义共享内存，init_by_lua 初始化计数器（请求总数、延迟直方图等），log_by_lua 里逐请求记录，再用一个 content_by_lua location 调用 `prom:collect()` 输出指标。项目地址：

```text
https://github.com/knyar/nginx-lua-prometheus
```

#### 7.4.3 方式三：nginx-vts（了解）

编译 Nginx 时 `--add-module=/path/nginx-module-vts`，http 块加 `vhost_traffic_status_zone;`，status location 用 `vhost_traffic_status_display` 暴露 HTML/JSON（`/status/format/json`）；nginx-vts-exporter 用 `-nginx.scrape_uri=http://nginx/status/format/json` 采集，默认端口 9913，Grafana 看板 2949。

```text
https://github.com/vozlt/nginx-module-vts
https://github.com/hnlq715/nginx-vts-exporter
```

---

### 7.5 Consul 监控（consul_exporter）

- **是什么**：consul_exporter 调用 Consul API，把各节点、服务的健康状态转为指标，默认端口 **9107**。
- **为什么需要**：Consul 作为注册中心，其自身及被注册服务的健康状态需要被监控。

**第 1 步：下载解压**（在 Consul 主机或独立主机）

```bash
cd /usr/local
wget https://github.com/prometheus/consul_exporter/releases/download/v0.13.0/consul_exporter-0.13.0.linux-amd64.tar.gz
tar xf consul_exporter-0.13.0.linux-amd64.tar.gz
ln -s consul_exporter-0.13.0.linux-amd64 consul_exporter
cd consul_exporter
mkdir bin
mv consul_exporter bin/
```

**第 2 步：创建服务文件**

```bash
id consul &>/dev/null || useradd -r -s /usr/sbin/nologin consul
chown -R consul:consul /usr/local/consul_exporter

cat > /etc/systemd/system/consul_exporter.service <<'EOF'
[Unit]
Description=Prometheus Consul Exporter
After=network.target

[Service]
Type=simple
User=consul
ExecStart=/usr/local/consul_exporter/bin/consul_exporter \
  --consul.server=http://127.0.0.1:8500 \
  --web.listen-address=:9107
Restart=always

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable --now consul_exporter
```

Exporter 与 Consul 不同机时，`--consul.server` 指向实际地址。

验证：

```bash
curl -s localhost:9107/metrics | grep -E 'consul_catalog_services|consul_catalog_service_node_healthy'
```

预期输出：

```text
consul_catalog_service_node_healthy{node="consul",service_id="consul",service_name="consul"} 1
consul_catalog_services 5
```

采集：prometheus.yml 加 job 指向 `【Consul服务器IP】:9107`。Grafana 看板 12049。

---

### 7.6 Java 应用监控（JMX Exporter）

- **是什么**：JMX Exporter 以 **Java Agent** 方式随 Java 应用启动，把 JVM（内存、GC、线程）和应用通过 JMX 暴露的 MBean 转成 Prometheus 指标，端口由启动参数指定（如 9527）。
- **JMX 是什么**：Java 管理扩展，是 Java 应用标准的管理/监控接口，Tomcat、Kafka、Spring 等都通过它暴露内部状态。
- **为什么需要**：JVM 堆内存、GC 频率、线程数是 Java 应用排障与容量规划的核心依据。

JMX Exporter 有两种用法：**javaagent 模式（推荐，随应用启动）**和 standalone HTTP Server 模式（独立进程远程拉取 JMX）。

#### 7.6.1 准备 Java 环境（以 Tomcat 为例）

包安装（Ubuntu 24.04 是 tomcat10，22.04 是 tomcat9）：

```bash
apt update && apt -y install tomcat10
systemctl enable --now tomcat10
ss -lntp | grep 8080
```

#### 7.6.2 部署 JMX Exporter

**第 1 步：下载 agent jar 与配置**

```bash
mkdir -p /opt/jmx_exporter
cd /opt/jmx_exporter
wget https://github.com/prometheus/jmx_exporter/releases/download/1.6.0/jmx_prometheus_javaagent-1.6.0.jar
wget -O tomcat.yml https://raw.githubusercontent.com/prometheus/jmx_exporter/1.6.0/examples/tomcat.yml
```

::: tip
1.1.0 之后的新版 jar 只在 GitHub Releases 发布（Maven Central 上该制品最新只到 1.0.1）。GitHub 下载慢时，在 URL 前加 `https://ghproxy.net/` 等代理，或在能访问的机器下载后拷贝。
:::

配置文件 `tomcat.yml` 定义如何把 MBean 转成指标（节选，完整文件从上面地址获取）：

```yaml
lowercaseOutputLabelNames: true
lowercaseOutputName: true
rules:
  - pattern: 'Catalina<type=GlobalRequestProcessor, name=\"(\w+-\w+)-(\d+)\"><>(\w+):'
    name: tomcat_$3_total
    labels:
      port: "$2"
      protocol: "$1"
    help: Tomcat global $3
    type: COUNTER
  - pattern: 'Catalina<type=ThreadPool, name="(\w+-\w+)-(\d+)"><>(currentThreadCount|currentThreadsBusy|keepAliveCount):'
    name: tomcat_threadpool_$3
    labels:
      port: "$2"
      protocol: "$1"
    type: GAUGE
```

字段解释：`pattern` 匹配 MBean 名称的正则，括号捕获组用 `$1/$2...` 引用；`name` 生成的指标名；`labels` 从捕获组生成标签；`type` 指标类型；`lowercaseOutputName/Labels` 把输出统一成小写（避免大小写不一致的重复序列）。

**第 2 步：让 Tomcat 加载 agent**

包安装的 Tomcat，编辑 `/usr/share/tomcat10/bin/catalina.sh`，在文件靠前位置（OS support 注释附近）加一行：

```bash
JAVA_OPTS="-javaagent:/opt/jmx_exporter/jmx_prometheus_javaagent-1.6.0.jar=9527:/opt/jmx_exporter/tomcat.yml"
```

格式：`-javaagent:jar路径=端口:配置文件路径`。端口 9527 是 agent 暴露指标的端口。

**第 3 步：重启验证**

```bash
systemctl restart tomcat10
ps aux | grep jmx_prometheus
ss -lntp | grep 9527
curl -s localhost:9527/metrics | grep -E 'jvm_memory_used_bytes|tomcat_requestcount_total'
```

预期输出（节选）：

```text
jvm_memory_used_bytes{area="heap",id="G1 Eden Space"} 1.234567E7
tomcat_requestcount_total{port="8080",protocol="http-bio"} 15
```

**第 4 步：采集与看板**

prometheus.yml 加：

```yaml
  - job_name: 'java_tomcat'
    static_configs:
      - targets: ['【应用服务器IP】:9527']
        labels:
          app: tomcat
```

Grafana 看板 8704、14845（导入后把面板的 job 变量改成实际 job 名）：

```text
https://grafana.com/grafana/dashboards/8704-jvm/
```

#### 7.6.3 其他 Java 应用的通用做法

- **Spring Boot**：更推荐直接引入 `micrometer-registry-prometheus`，应用原生暴露 `/actuator/prometheus`，无需 JMX agent；
- **Kafka / ZooKeeper / 其他中间件**：同样把 `-javaagent:...jar=端口:配置.yml` 加进启动脚本（Kafka 加在 `KAFKA_OPTS`），配置文件用仓库 examples 目录下对应的 kafka.yml、zookeeper.yml；
- **二进制 Tomcat**：把 jar 和 yml 放进 `tomcat/bin/`，在 `catalina.sh` 加 JAVA_OPTS，`catalina.sh stop && catalina.sh start` 即可。

---

### 7.7 HAProxy 监控

两种方式：**haproxy_exporter 采集状态页 CSV**，或 **HAProxy 2.x 内置 Prometheus 输出**。

#### 7.7.1 方式一：haproxy_exporter

**第 1 步：开启 HAProxy 状态页**

```bash
apt update && apt -y install haproxy
```

编辑 `/etc/haproxy/haproxy.cfg`，加：

```text
listen stats
    mode http
    bind 0.0.0.0:9999
    stats enable
    stats uri /haproxy-status
    stats auth admin:【状态页密码】
```

重启：

```bash
systemctl restart haproxy
curl -u admin:【状态页密码】 http://127.0.0.1:9999/haproxy-status;csv | head -2
```

`;csv` 后缀让状态页输出 CSV，exporter 解析的就是它。

**第 2 步：部署 exporter**

```bash
cd /usr/local
wget https://github.com/prometheus/haproxy_exporter/releases/download/v0.15.0/haproxy_exporter-0.15.0.linux-amd64.tar.gz
tar xf haproxy_exporter-0.15.0.linux-amd64.tar.gz
ln -s haproxy_exporter-0.15.0.linux-amd64 haproxy_exporter
cd haproxy_exporter
mkdir bin
mv haproxy_exporter bin/
```

创建服务文件：

```bash
id prometheus &>/dev/null || useradd -r -s /usr/sbin/nologin prometheus
chown -R prometheus:prometheus /usr/local/haproxy_exporter

cat > /etc/systemd/system/haproxy_exporter.service <<'EOF'
[Unit]
Description=Prometheus HAProxy Exporter
After=network.target

[Service]
Type=simple
User=prometheus
ExecStart=/usr/local/haproxy_exporter/bin/haproxy_exporter \
  --haproxy.scrape-uri="http://admin:【状态页密码】@127.0.0.1:9999/haproxy-status;csv" \
  --web.listen-address=:9101
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable --now haproxy_exporter
```

也支持 socket 方式：`--haproxy.scrape-uri=unix:/run/haproxy/admin.sock`。

验证：

```bash
curl -s localhost:9101/metrics | grep -E 'haproxy_up|haproxy_frontend_http_requests_total'
```

采集：prometheus.yml 加 job 指向 9101。Grafana 看板 2428。

#### 7.7.2 方式二：HAProxy 内置 /metrics（推荐）

Ubuntu 22.04/24.04 包安装的 HAProxy 2.4+ 默认编译了 Prometheus 支持（`USE_PROMEX=1`，`haproxy -vv` 可确认）。在 frontend 里加一行：

```text
frontend stats
    bind *:9999
    stats enable
    stats uri /haproxy-status
    http-request use-service prometheus-exporter if { path /metrics }
```

重启后直接访问：

```bash
systemctl restart haproxy
curl -s http://127.0.0.1:9999/metrics | grep haproxy_frontend
```

Prometheus 直接采集 `【HAProxyIP】:9999` 的普通 job 即可，无需 exporter。Grafana 看板 12693（注意内置方式与 exporter 方式的看板不通用）。

---

### 7.8 Blackbox 黑盒监控

- **是什么**：blackbox_exporter 从**外部**探测目标——HTTP/HTTPS 返回码与内容、TCP 端口连通、DNS 解析、ICMP（ping）、gRPC、TLS 证书，默认端口 **9115**。
- **类比**：不像其他 Exporter 站在机器"屋里"看内部指标，黑盒监控像在"门外"敲门，验证用户实际能不能访问。
- **为什么需要**：服务进程活着不代表用户能访问（防火墙、DNS、证书过期、首页报错都可能出问题），黑盒探测模拟真实访问，是可用性的最后一道验证。

#### 7.8.1 部署 blackbox_exporter

**第 1 步：下载解压**（部署在监控服务器 monitor）

```bash
cd /usr/local
wget https://github.com/prometheus/blackbox_exporter/releases/download/v0.28.0/blackbox_exporter-0.28.0.linux-amd64.tar.gz
tar xf blackbox_exporter-0.28.0.linux-amd64.tar.gz
ln -s blackbox_exporter-0.28.0.linux-amd64 blackbox_exporter
cd blackbox_exporter
mkdir -p bin conf
mv blackbox_exporter bin/
mv blackbox.yml conf/
```

**第 2 步：配置模块** `/usr/local/blackbox_exporter/conf/blackbox.yml`：

```yaml
modules:
  http_2xx:
    prober: http
    timeout: 5s
    http:
      valid_http_versions: ["HTTP/1.1", "HTTP/2.0"]
      valid_status_codes: []        # 空表示接受 2xx
      method: GET
      preferred_ip_protocol: ip4
  http_post_2xx:
    prober: http
    http:
      method: POST
  tcp_connect:
    prober: tcp
    timeout: 5s
  dns_udp:
    prober: dns
    timeout: 5s
    dns:
      query_name: "www.magedu.com"
      query_type: "A"
      valid_rcodes: [NOERROR]
  icmp:
    prober: icmp
    timeout: 5s
```

模块（module）= 一套探测方式定义；常用 prober：`http`、`tcp`、`dns`、`icmp`、`grpc`。HTTP 模块还支持：`fail_if_ssl`/`fail_if_not_ssl`（要求必须不是/必须是 HTTPS）、`fail_if_body_matches_regexp`（正文匹配正则则失败，可检测页面报错文案）、TLS 证书校验等。

**第 3 步：创建服务文件**

::: warning
ICMP 探测需要发送原始套接字（raw socket）。普通用户运行需要相应权限；最简单稳妥的方式是以 root 运行 blackbox_exporter，或给二进制授予 CAP_NET_RAW 能力：`setcap cap_net_raw,cap_net_admin=eip /usr/local/blackbox_exporter/bin/blackbox_exporter`，再用普通用户运行。
:::

```bash
cat > /etc/systemd/system/blackbox_exporter.service <<'EOF'
[Unit]
Description=Prometheus Blackbox Exporter
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/blackbox_exporter/bin/blackbox_exporter \
  --config.file=/usr/local/blackbox_exporter/conf/blackbox.yml \
  --web.listen-address=:9115
Restart=on-failure
LimitNOFILE=100000

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable --now blackbox_exporter
ss -lntp | grep 9115
```

**第 4 步：先用浏览器/URL 手工验证模块**

访问（先探测本机 9115 自己）：

```text
http://【监控服务器IP】:9115/probe?target=www.baidu.com&module=http_2xx
```

页面返回 `probe_success 1` 表示探测成功；失败时返回 `probe_success 0` 并附带 `probe_*` 诊断指标（如 DNS 解析失败、超时）。

#### 7.8.2 Prometheus 配置黑盒采集

黑盒采集的 relabel 套路是固定的，**三类探测都一样**：把目标地址从 `__address__` 挪到 `__param_target`（作为 probe 的 target 参数），再把 `__address__` 改成 blackbox_exporter 自身地址。

**ICMP（ping 连通性）**：

```yaml
  - job_name: 'blackbox-icmp'
    metrics_path: /probe
    params:
      module: [icmp]
    static_configs:
      - targets:
          - '【Web服务器IP】'
          - '【应用服务器IP】'
          - '【数据库服务器IP】'
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: 【监控服务器IP】:9115
```

**TCP 端口连通**：

```yaml
  - job_name: 'blackbox-tcp'
    metrics_path: /probe
    params:
      module: [tcp_connect]
    static_configs:
      - targets:
          - '【Web服务器IP】:80'
          - '【数据库服务器IP】:3306'
          - '【数据库服务器IP】:6379'
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: 【监控服务器IP】:9115
```

**HTTP/HTTPS 网站**：

```yaml
  - job_name: 'blackbox-http'
    metrics_path: /probe
    params:
      module: [http_2xx]
    static_configs:
      - targets:
          - 'http://【Web服务器IP】'
          - 'https://www.baidu.com'
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: url
      - target_label: __address__
        replacement: 【监控服务器IP】:9115
```

检查生效：

```bash
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus
```

验证：Targets 页出现各探测目标，`probe_success` 为 1。HTTPS 目标还会自动得到 `probe_tls_version_info`、`probe_ssl_earliest_cert_expiry`（证书最早到期时间）等指标。

**黑盒告警规则**，创建 `/usr/local/prometheus/rules/blackbox_alert_rules.yml`：

```yaml
groups:
  - name: blackbox
    rules:
      - alert: BlackboxProbeFailed
        expr: probe_success == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "探测失败：{{ $labels.instance }}"
          description: "目标 {{ $labels.instance }} 探测失败超过 1 分钟"

      - alert: SSLCertExpiringSoon
        expr: (probe_ssl_earliest_cert_expiry - time()) / 86400 < 30
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "证书即将过期：{{ $labels.instance }}"
          description: "证书剩余有效期不足 30 天"
```

Grafana 看板 9965、13587：

```text
https://grafana.com/grafana/dashboards/9965-blackbox-exporter/
```

#### 7.8.3 Docker Compose 方式

```yaml
version: '3.6'
services:
  blackbox_exporter:
    image: prom/blackbox-exporter:v0.28.0
    restart: always
    volumes:
      - ./blackbox.yml:/etc/blackbox_exporter/blackbox.yml:ro
    command:
      - '--config.file=/etc/blackbox_exporter/blackbox.yml'
    ports:
      - "9115:9115"
```

容器里做 ICMP 探测需加 `cap_add: [NET_RAW, NET_ADMIN]`。

---

### 本阶段命令速查表

| 组件 | 端口 | 关键配置/命令 |
| --- | --- | --- |
| node systemd | 9100 | `--collector.systemd --collector.systemd.unit-include="..."` |
| node textfile | 9100 | `--collector.textfile.directory=/var/lib/node_exporter/textfile` |
| mysqld_exporter | 9104 | `--config.my-cnf=/usr/local/mysqld_exporter/.my.cnf` |
| redis_exporter | 9121 | `-redis.addr=redis://127.0.0.1:6379 -redis.password=...` |
| nginx exporter | 9113 | `--nginx.scrape-uri=http://IP:8888/basic_status` |
| consul_exporter | 9107 | `--consul.server=http://127.0.0.1:8500` |
| JMX agent | 9527 | `-javaagent:jar=9527:配置.yml` |
| haproxy_exporter | 9101 | `--haproxy.scrape-uri=".../haproxy-status;csv"` |
| blackbox | 9115 | `--config.file=blackbox.yml`，采集固定 relabel 三件套 |

```bash
# 通用验证三连
ss -lntp | grep 端口
curl -s localhost:端口/metrics | grep 组件_up
promtool check config /usr/local/prometheus/conf/prometheus.yml && systemctl reload prometheus
```

---

### 本阶段常见坑与解决

**坑 1：mysqld_exporter 的 mysql_up 为 0**

- 报错/现象：`mysql_up 0`，日志 `Error 1045: Access denied for user 'exporter'@...`。
- 原因：密码错、用户 host 不匹配、权限不足。
- 解决：核对 .my.cnf；确认 exporter 连接来源 IP 对应的用户已创建并授权（PROCESS、REPLICATION CLIENT、SELECT）。

**坑 2：redis_exporter 指标为空/redis_up 为 0**

- 报错/现象：日志 `NOAUTH Authentication required` 或 `dial tcp ... connect: connection refused`。
- 原因：没配密码/密码错；bind 限制；端口不通。
- 解决：`-redis.password` 与 requirepass 一致；确认 bind 0.0.0.0、放通 6379。

**坑 3：Nginx exporter 报 404/连接拒绝**

- 报错/现象：`nginx_up 0`，日志 `Unexpected status code 404`。
- 原因：stub_status 没开或 URI 写错；访问被 deny。
- 解决：确认 location、curl 状态页有输出；放行 exporter 来源 IP。

**坑 4：JMX agent 启动后应用起不来**

- 报错原样：`Error opening zip file or JAR manifest missing : /opt/jmx_exporter/jmx_prometheus_javaagent-1.6.0.jar`。
- 原因：jar 路径错/下载不完整；配置文件路径错。
- 解决：核对 jar 与 yml 绝对路径、重新下载；`java -jar` 前先确认文件非空。

**坑 5：JMX 指标名重复/大小写混乱**

- 现象：同一指标出现大小写两套序列，看板数据分裂。
- 原因：未开 lowercaseOutputName/lowercaseOutputLabelNames。
- 解决：配置文件开头设置两者为 true。

**坑 6：ICMP 探测全部失败**

- 报错/现象：`probe_success 0`，日志 `socket: permission denied`。
- 原因：普通用户无 raw socket 权限。
- 解决：root 运行，或 `setcap cap_net_raw,cap_net_admin=eip blackbox_exporter`；容器加 NET_RAW capability。

**坑 7：黑盒目标全部失败，但 exporter 本身正常**

- 报错/现象：所有 probe 目标 0，手工访问 exporter URL 报 `probe_dns_lookup_time_seconds` 相关错误。
- 原因：监控服务器 DNS 解析不了目标；目标被防火墙拦；relabel 写错（target 没传对）。
- 解决：在监控机上 curl/ping 目标自查；核对 relabel 三件套顺序。

**坑 8：textfile 指标不出现**

- 报错/现象：.prom 文件写了但 metrics 里没有。
- 原因：目录没配对、文件后缀不是 .prom、文件正在写（临时文件被读到报错）、指标格式错误。
- 解决：核对 `--collector.textfile.directory`；临时文件写完再 mv；看 node_exporter 日志里的 textfile 解析报错。

**坑 9：HAProxy 内置 /metrics 不输出**

- 报错/现象：访问 /metrics 返回状态页而非指标。
- 原因：未编译 USE_PROMEX，或没配 `http-request use-service prometheus-exporter`。
- 解决：`haproxy -vv | grep PROMEX`；frontend 加对应行；否则改用 exporter 方式。

---
