---
category: 监控
difficulty: 中级
---

# Prometheus 实战 07：服务发现与 MySQL/Redis 采集

> **Prometheus 实战系列（共 10 篇）**
> ← 上一篇 [Prometheus 实战 06](./monitor-prometheus-06-alert-notification-ha) ｜ 下一篇 [Prometheus 实战 08](./monitor-prometheus-08-more-exporters) →
> [返回监控索引](./monitor)

## 阶段六：服务发现

### 阶段目标

- 理解为什么静态配置在大规模、动态环境下不够用；
- 掌握**文件、DNS、Consul、Kubernetes API** 四种服务发现；
- 会用 Consul 注册服务并让 Prometheus 自动纳入监控。

### 6.1 服务发现原理

- **是什么**：服务发现让 Prometheus 不再依赖手写的 `static_configs` 目标列表，而是从**服务注册中心**自动获取、检测、分类目标，目标变动（新增、下线）也能自动更新。
- **类比**：静态配置像把朋友电话手抄在本子上，换号了就得手动改；服务发现像通讯录 App，朋友换号自动同步。
- **为什么需要**：Pull 模型必须先知道每个目标的位置。小环境手抄没问题；中大型、云环境里实例频繁增删，静态配置维护不过来。

Prometheus 提供二十多种发现机制，常用的：

| 方式 | 说明 |
| --- | --- |
| 静态服务发现 | `static_configs` 手写 `ip:port` |
| 文件服务发现 | 目标写在 YAML/JSON 文件里，Prometheus 周期重读 |
| DNS 服务发现 | 定期查询一组 DNS 域名（A/AAAA/SRV 记录）发现目标 |
| Consul 服务发现 | 基于 Consul 注册中心动态发现 |
| HTTP 服务发现 | 从返回 static_config 列表的 HTTP 端点（JSON）获取目标，便于接入自定义发现 |
| Kubernetes API 发现 | 把 Node、Service、Endpoint、Pod、Ingress 等资源对象作为目标 |

发现原理分三步：

1. 配置处理模块按 `scrape_configs` 的发现协议生成对应的 Discoverer，各自去发现目标，放入目标列表；
2. DiscoveryManager 每 5 秒检查一次目标列表，有变更就放进同步消息池；
3. scrape 组件监听消息池，reload 后把新目标纳入抓取。

---

### 6.2 文件服务发现

- **是什么**：目标写在 YAML/JSON 文件中，Prometheus 定期重读；不依赖任何平台或第三方，是最简单通用的动态发现。
- **文件来源**：可手写，也可由 Ansible/SaltStack 等配置管理工具、或基于 CMDB 的脚本生成。
- **注意**：不要在原文件上直接边写边存（Prometheus 可能读到写了一半的文件）；正确做法是先写到临时文件再 `mv` 原子替换。

**第 1 步：建目录**

```bash
mkdir -p /usr/local/prometheus/conf/targets
```

**第 2 步：创建目标文件**

`/usr/local/prometheus/conf/targets/prometheus-server.yml`：

```yaml
- targets:
    - '【监控服务器IP】:9090'
  labels:
    app: prometheus-server
    job: prometheus-server
```

`/usr/local/prometheus/conf/targets/node.yml`：

```yaml
- targets:
    - '【监控服务器IP】:9100'
  labels:
    app: prometheus
    job: prometheus
- targets:
    - '【Web服务器IP】:9100'
    - '【应用服务器IP】:9100'
    - '【数据库服务器IP】:9100'
  labels:
    app: node-exporter
    job: node
```

`/usr/local/prometheus/conf/targets/flask.yml`：

```yaml
- targets:
    - '【应用服务器IP】:8000'
  labels:
    app: flask-web
    job: my_metric
```

**第 3 步：在 prometheus.yml 配置发现**

```yaml
scrape_configs:
  - job_name: 'file_sd_prometheus'
    scrape_interval: 10s
    file_sd_configs:
      - files:
          - targets/prometheus-server.yml
        refresh_interval: 10s

  - job_name: 'file_sd_node'
    file_sd_configs:
      - files:
          - targets/node.yml
        refresh_interval: 10s

  - job_name: 'file_sd_flask'
    file_sd_configs:
      - files:
          - targets/flask.yml
        refresh_interval: 10s
```

参数解释：`files` 要加载的文件列表，支持 glob 通配符（如 `targets/*.yml`），相对路径相对于 prometheus.yml 所在目录；`refresh_interval` 重读间隔，默认 5m。

**第 4 步：检查生效**

```bash
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus
```

验证：Targets 页所有目标出现，且带文件里定义的标签。文件发现会自动附加元标签 `__meta_filepath`（文件完整路径），可在 relabel 中使用。

**第 5 步：体验动态增删**

编辑 `node.yml`，加一行新主机（如 `'【新主机IP】:9100'`），保存后等一个 refresh 周期，无需重启 Prometheus，新目标自动出现；删掉某行，目标自动消失。

**JSON 格式**（等价写法，更适合程序生成），`targets/node.json`：

```json
[
  {
    "targets": ["【监控服务器IP】:9100"],
    "labels": {"app": "prometheus", "job": "prometheus"}
  },
  {
    "targets": ["【Web服务器IP】:9100", "【应用服务器IP】:9100"],
    "labels": {"app": "node-exporter", "job": "node"}
  }
]
```

YAML 转 JSON 可用 `jq`、在线工具或 Python，注意 JSON 里字段是 `targets`（带 s）。

---

### 6.3 DNS 服务发现

- **是什么**：定期查询一组 DNS 域名来发现目标，依赖 A、AAAA、SRV 记录；用哪台 DNS 由 Prometheus 服务器的 `/etc/resolv.conf` 决定。
- **SRV 记录**：服务资源记录，说明"某个域名下有哪些服务器、端口、优先级"，格式 `_<服务>._<协议>.<域名> TTL IN SRV 优先级 权重 端口 目标主机`。一条 SRV 记录可对应多台主机，便于批量发现。

#### 6.3.1 部署 DNS（BIND）

在一台主机（可用监控服务器兼任）执行，用户 root：

```bash
apt update && apt -y install bind9 bind9utils bind9-doc bind9-host
named -v
```

**配置正向区域**，追加到 `/etc/bind/named.conf.default-zones`：

```text
zone "magedu.com" {
    type master;
    file "/etc/bind/magedu.com.zone";
};
```

**创建区域文件** `/etc/bind/magedu.com.zone`：

```text
$TTL 604800
@   IN  SOA ns.magedu.com. admin.magedu.com. (
            1        ; Serial（每次修改加 1）
            604800   ; Refresh
            86400    ; Retry
            2419200  ; Expire
            604800 )  ; Negative Cache TTL
    IN  NS  master
master  IN  A   【DNS服务器IP】
node1   IN  A   【Web服务器IP】
node2   IN  A   【应用服务器IP】
node3   IN  A   【数据库服务器IP】
flask   IN  A   【应用服务器IP】
```

检查并生效：

```bash
named-checkconf
named-checkzone magedu.com /etc/bind/magedu.com.zone
rndc reload
systemctl restart named
```

让 Prometheus 服务器使用这台 DNS（netplan 示例 `/etc/netplan/01-netcfg.yaml`）：

```yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    eth0:
      addresses:
        - 【监控服务器IP】/24
      routes:
        - to: default
          via: 【网关IP】
      nameservers:
        addresses: [【DNS服务器IP】]
```

应用并验证解析：

```bash
netplan apply
dig node1.magedu.com
host node1.magedu.com
```

#### 6.3.2 配置 SRV 记录

在 `/etc/bind/magedu.com.zone` 追加（对应上面的 A 记录，端口 9100 是 node_exporter）：

```text
_prometheus._tcp.magedu.com. 1H IN SRV 10 10 9100 node1.magedu.com.
_prometheus._tcp.magedu.com. 1H IN SRV 10 10 9100 node2.magedu.com.
_prometheus._tcp.magedu.com. 1H IN SRV 10 10 9100 node3.magedu.com.
```

字段：`10` 优先级（小的优先）、`10` 权重（同优先级按权重分流）、`9100` 端口、最后是目标主机名。生效：

```bash
rndc reload
host -t srv _prometheus._tcp.magedu.com
```

预期输出：

```text
_prometheus._tcp.magedu.com has SRV record 10 10 9100 node1.magedu.com.
_prometheus._tcp.magedu.com has SRV record 10 10 9100 node2.magedu.com.
_prometheus._tcp.magedu.com has SRV record 10 10 9100 node3.magedu.com.
```

#### 6.3.3 Prometheus 使用 DNS 发现

```yaml
scrape_configs:
  # 单个主机：用 A 记录，需显式指定端口
  - job_name: 'dns_sd_flask'
    dns_sd_configs:
      - names: ['flask.magedu.com']
        type: A
        port: 8000
        refresh_interval: 10s

  # 批量主机：用 SRV 记录（端口从记录里取）
  - job_name: 'dns_sd_node'
    dns_sd_configs:
      - names: ['_prometheus._tcp.magedu.com']
        refresh_interval: 10s
```

参数解释：`names` 要查询的域名列表；`type` 记录类型，默认 SRV（可选 A、AAAA）；非 SRV 时用 `port` 指定端口；`refresh_interval` 默认 30s。

检查生效：

```bash
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus
```

增删 SRV/A 记录后，Ubuntu 有本地 DNS 缓存，必要时清缓存：

```bash
systemctl restart systemd-resolved.service
rndc reload
```

---

### 6.4 Consul 服务发现

#### 6.4.1 Consul 简介

- **是什么**：Consul 是一个服务发现与配置工具，提供服务注册、健康检查、KV 存储、多数据中心支持，自带 Web UI。
- **类比**：微服务互相找不到对方，Consul 就是"公司前台+通讯录"，每个服务报到登记，要找谁问前台，前台还会定期确认人还在不在（健康检查）。
- **为什么需要**：微服务拆分后服务间跨进程、跨机房通信，需要知道对方位置、避开不健康副本。

**关键概念**：

| 概念 | 说明 |
| --- | --- |
| Agent | 每个节点上常驻的守护进程，分 **Client** 和 **Server** 两种模式 |
| Client | 不保存数据，转发 RPC 给 Server，相对无状态 |
| Server | 参与 Raft 选举、维护集群状态与数据；单数据中心建议 3～5 个 |
| Raft | 强一致性协议，保证 Server 间服务注册信息、KV 数据同步与 Leader 选举 |
| Gossip | 节点间成员发现、健康检查、状态广播（最终一致），LAN 池用于机房内、WAN 池跨机房 |

Consul 端口：

| 端口 | 用途 |
| --- | --- |
| 8500 | HTTP API 与 Web UI |
| 8300 | Server RPC（同数据中心 Server 间） |
| 8301 | Serf LAN（同机房节点通信） |
| 8302 | Serf WAN（跨机房 Server 通信） |
| 8600 | DNS 服务 |

#### 6.4.2 部署 Consul

**方式 1：官方仓库安装（Ubuntu）**

```bash
wget -O - https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/hashicorp.list
apt update && apt -y install consul
consul version
```

RHEL 系：

```bash
yum install -y yum-utils
yum-config-manager --add-repo https://rpm.releases.hashicorp.com/RHEL/hashicorp.repo
yum -y install consul
```

**方式 2：二进制安装（推荐，版本可控）**

```bash
cd /usr/local
CONSUL_VERSION=1.22.7
wget https://releases.hashicorp.com/consul/${CONSUL_VERSION}/consul_${CONSUL_VERSION}_linux_amd64.zip
apt -y install unzip
unzip consul_${CONSUL_VERSION}_linux_amd64.zip -d /usr/local/bin/
consul version
```

准备用户、目录：

```bash
id consul &>/dev/null || useradd -r -s /usr/sbin/nologin consul
mkdir -p /data/consul /etc/consul.d
chown -R consul:consul /data/consul /etc/consul.d
```

创建服务文件（单机 Server，注意把 bind 改成本机 IP）：

```bash
cat > /etc/systemd/system/consul.service <<'EOF'
[Unit]
Description="HashiCorp Consul"
Documentation=https://developer.hashicorp.com/consul/docs
Requires=network-online.target
After=network-online.target

[Service]
Type=simple
User=consul
Group=consul
ExecStart=/usr/local/bin/consul agent -server -bind=【监控服务器IP】 -client=0.0.0.0 -ui -bootstrap-expect=1 -data-dir=/data/consul -node=consul -config-dir=/etc/consul.d
KillMode=process
Restart=on-failure
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable --now consul
ss -lntup | grep -E '8500|8600'
```

参数解释：

| 参数 | 作用 |
| --- | --- |
| `-server` | 以 Server 模式运行（否则是 Client） |
| `-bind` | 集群内部通信地址，多网卡必须显式指定 |
| `-client` | HTTP/DNS/RPC 监听地址，默认 127.0.0.1，要对外提供改 0.0.0.0 |
| `-ui` | 启用内置 Web UI（8500） |
| `-bootstrap-expect` | 期望的 Server 数量，达到后才引导集群；单机设 1 |
| `-data-dir` | 状态数据目录 |
| `-node` | 节点名，集群内唯一 |
| `-config-dir` | 配置目录，加载其中 .json/.hcl 文件 |

浏览器访问 `http://【监控服务器IP】:8500` 能看到 Consul UI。

**方式 3：Docker / Compose**

```bash
docker run -d --name consul --restart=always -p 8500:8500 \
  hashicorp/consul:1.22 agent -server -client=0.0.0.0 -bootstrap-expect=1 -ui
```

#### 6.4.3 Consul 集群（了解）

3 个 Server 节点时，第一个节点：

```bash
consul agent -server -bind=【节点1IP】 -client=0.0.0.0 -ui -bootstrap -data-dir=/data/consul -node=node1
```

第二、三个节点（用 `-retry-join` 加入，`-bootstrap-expect 3`）：

```bash
consul agent -server -bind=【节点2IP】 -client=0.0.0.0 -retry-join=【节点1IP】 -bootstrap-expect=3 -data-dir=/data/consul -node=node2
consul agent -server -bind=【节点3IP】 -client=0.0.0.0 -retry-join=【节点1IP】 -bootstrap-expect=3 -data-dir=/data/consul -node=node3
```

查看成员：

```bash
consul members
```

预期输出：

```text
Node    Address          Status  Type    Build    Protocol  DC   Partition  Segment
node1   【节点1IP】:8301  alive   server  1.22.7   2         dc1  default    <all>
node2   【节点2IP】:8301  alive   server  1.22.7   2         dc1  default    <all>
node3   【节点3IP】:8301  alive   server  1.22.7   2         dc1  default    <all>
```

#### 6.4.4 注册与注销服务

**HTTP API 方式**，注册 node1 上的 node_exporter：

```bash
curl -X PUT -d '{
  "id": "node1-exporter",
  "name": "node-exporter",
  "address": "【Web服务器IP】",
  "port": 9100,
  "tags": ["node"],
  "checks": [{"http": "http://【Web服务器IP】:9100/metrics", "interval": "5s"}]
}' http://【监控服务器IP】:8500/v1/agent/service/register
```

也可把 JSON 存成文件再注册：

```bash
curl -X PUT --data @nodes.json http://【监控服务器IP】:8500/v1/agent/service/register
```

健康检查会定期访问 `http://【Web服务器IP】:9100/metrics`，检查失败服务标记为不健康。

**命令行方式**，`node1.json`：

```json
{
  "service": {
    "id": "node1-exporter",
    "name": "node-exporter",
    "address": "node1.magedu.com",
    "port": 9100,
    "tags": ["node"],
    "checks": [{"http": "http://node1.magedu.com:9100/metrics", "interval": "5s"}]
  }
}
```

注册/注销：

```bash
consul services register node1.json
consul services deregister -id node1-exporter
```

HTTP API 注销：

```bash
curl -X PUT http://【监控服务器IP】:8500/v1/agent/service/deregister/node1-exporter
```

常用查询 API：

```bash
curl http://【监控服务器IP】:8500/v1/catalog/datacenters
curl http://【监控服务器IP】:8500/v1/catalog/nodes
curl http://【监控服务器IP】:8500/v1/catalog/services
curl http://【监控服务器IP】:8500/v1/catalog/service/node-exporter
```

#### 6.4.5 Prometheus 使用 Consul 发现

Consul 发现的目标会带元标签：`__meta_consul_address`、`__meta_consul_dc`、`__meta_consul_node`、`__meta_consul_service`、`__meta_consul_service_id`、`__meta_consul_service_address`、`__meta_consul_service_port`、`__meta_consul_tags`。

在 prometheus.yml 加：

```yaml
  - job_name: 'consul'
    honor_labels: true
    consul_sd_configs:
      - server: '【监控服务器IP】:8500'
        # services: []        # 默认发现所有服务；也可指定名称，如 ['node-exporter']
        # tags: ['node']      # 只保留带指定 tag 的服务
        refresh_interval: 30s
    relabel_configs:
      - source_labels: ['__meta_consul_service']
        target_label: 'consul_service'
      - source_labels: ['__meta_consul_dc']
        target_label: 'datacenter'
      - source_labels: ['__meta_consul_tags']
        target_label: 'app'
      # Consul 自身内置服务也叫 consul，但不提供 /metrics，丢弃避免报错
      - source_labels: ['__meta_consul_service']
        regex: 'consul'
        action: drop
```

参数解释：`server` Consul 地址；`services` 要发现的服务名列表，空为全部；`tags` 按标签过滤；`refresh_interval` 默认 30s。

检查生效：

```bash
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus
```

验证：在 Consul 注册一个新服务，几十秒内 Prometheus Targets 页自动出现；注销后自动消失。

---

### 6.5 Kubernetes API 服务发现

- **是什么**：直接对接 Kubernetes API Server，把 Node、Service、Endpoints（含 EndpointSlice）、Pod、Ingress 资源作为目标，每种资源对应一个 **role**。
- **认证**：Prometheus 跑在集群内时，自动使用 Pod 里 `/var/run/secrets/kubernetes.io/serviceaccount/` 的 CA 证书和 Token；集群外可用 `api_server` + kubeconfig/认证信息。

| role | 发现对象 | 典型用途 |
| --- | --- | --- |
| `node` | 每个节点（kubelet） | 采集 kubelet、cAdvisor |
| `pod` | 每个 Pod 的每个容器端口 | 采集业务 Pod |
| `service` | 每个 Service 的端口 | 对 Service 做黑盒监控 |
| `endpoints` / `endpointslice` | 每个 Endpoint 端口 | 采集 Service 后端、API Server |
| `ingress` | 每个 Ingress 的 path | 对 Ingress 做黑盒监控 |

部分常用元标签：

| role | 元标签举例 |
| --- | --- |
| node | `__meta_kubernetes_node_name`、`__meta_kubernetes_node_label_<x>`、`__meta_kubernetes_node_address_<类型>` |
| pod | `__meta_kubernetes_namespace`、`__meta_kubernetes_pod_name`、`__meta_kubernetes_pod_ip`、`__meta_kubernetes_pod_label_<x>`、`__meta_kubernetes_pod_node_name`、`__meta_kubernetes_pod_controller_kind` |
| service | `__meta_kubernetes_service_name`、`__meta_kubernetes_service_cluster_ip`、`__meta_kubernetes_service_port_number`、`__meta_kubernetes_service_type`、`__meta_kubernetes_service_label_<x>` |
| endpoints | `__meta_kubernetes_endpoints_name`、`__meta_kubernetes_endpoint_ready`、`__meta_kubernetes_endpoint_port_name` |
| ingress | `__meta_kubernetes_ingress_name`、`__meta_kubernetes_ingress_scheme`、`__meta_kubernetes_ingress_path` |

**集群内典型配置**（完整示例见官方 `prometheus-kubernetes.yml`）：

```yaml
scrape_configs:
  # API Server：endpoints role，只保留 default/kubernetes 的 https 端口
  - job_name: 'kubernetes-apiservers'
    kubernetes_sd_configs:
      - role: endpoints
    scheme: https
    tls_config:
      ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
    relabel_configs:
      - source_labels: [__meta_kubernetes_namespace, __meta_kubernetes_service_name, __meta_kubernetes_endpoint_port_name]
        action: keep
        regex: default;kubernetes;https

  # 节点 kubelet：通过 API Server 代理访问
  - job_name: 'kubernetes-nodes'
    scheme: https
    tls_config:
      ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
    kubernetes_sd_configs:
      - role: node
    relabel_configs:
      - action: labelmap
        regex: __meta_kubernetes_node_label_(.+)
      - target_label: __address__
        replacement: kubernetes.default.svc:443
      - source_labels: [__meta_kubernetes_node_name]
        target_label: __metrics_path__
        regex: (.+)
        replacement: /api/v1/nodes/${1}/proxy/metrics

  # 业务 Pod：只采集带 prometheus.io/scrape: "true" 注解的 Pod
  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
    tls_config:
      insecure_skip_verify: true
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: 'true'
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
      - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        target_label: __address__
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
      - action: labelmap
        regex: __meta_kubernetes_pod_label_(.+)
```

业务方通过 Pod/Service 注解声明采集方式（这是社区约定）：

| 注解 | 作用 |
| --- | --- |
| `prometheus.io/scrape: "true"` | 是否采集 |
| `prometheus.io/port: "端口"` | 采集端口 |
| `prometheus.io/path: "/metrics"` | 指标路径 |
| `prometheus.io/scheme: "http"` | http/https |

::: tip
生产中通常不会手写这么多 role 配置，而是用 **kube-prometheus-stack**（Helm）或 Prometheus Operator 自动生成，阶段十一详细讲。这里理解 role 与 relabel 的对应关系即可。
:::

---

### 本阶段命令速查表

```bash
# === 文件发现 ===
mkdir -p /usr/local/prometheus/conf/targets
vim /usr/local/prometheus/conf/targets/xxx.yml
# prometheus.yml: file_sd_configs 配 files + refresh_interval
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus

# === DNS（BIND）===
apt -y install bind9
named-checkconf && rndc reload
host -t srv _prometheus._tcp.magedu.com
systemctl restart systemd-resolved.service   # 清本地 DNS 缓存

# === Consul ===
# 二进制
wget https://releases.hashicorp.com/consul/1.22.7/consul_1.22.7_linux_amd64.zip
unzip consul_1.22.7_linux_amd64.zip -d /usr/local/bin/
systemctl enable --now consul
consul members
# 注册 / 注销
consul services register xxx.json
consul services deregister -id 服务ID
curl -X PUT http://【监控服务器IP】:8500/v1/agent/service/deregister/服务ID
```

---

### 本阶段常见坑与解决

**坑 1：改了文件发现目标不生效**

- 现象：编辑目标文件后 Prometheus 没反应。
- 原因：没到 `refresh_interval`；文件 YAML 语法错误；路径写错（相对路径是相对 prometheus.yml）。
- 解决：等待一个周期；`promtool check config` 检查；核对 files 路径。

**坑 2：直接编辑目标文件导致目标时有时无**

- 报错/现象：Targets 页短暂报错或目标不全。
- 原因：Prometheus 正好在你保存的瞬间读到写了一半的文件。
- 解决：写到临时文件再 `mv 临时文件 正式文件`（原子替换）；用脚本生成时也这样做。

**坑 3：DNS 发现不到目标**

- 现象：dns_sd 配置后目标为空。
- 原因：SRV 记录没配对（type 默认 SRV，却只建了 A 记录）；resolv.conf 没用自建 DNS；DNS 缓存。
- 解决：A 记录要配 `type: A` + `port`；确认 `/etc/resolv.conf` 指向自建 DNS；重启 systemd-resolved。

**坑 4：Consul 启动超时/失败**

- 报错原样：`Job for consul.service failed because a timeout was exceeded`；日志 `No known Consul servers`。
- 原因：多网卡没指定 bind；`bootstrap-expect` 数量达不到；client 模式下没有可连的 Server。
- 解决：显式 `-bind=本机IP`；单机用 `-bootstrap-expect=1`；确认 Server 已启动、8300/8301 端口放通。

**坑 5：Consul 里的 consul 服务导致 Targets 报错**

- 报错原样：目标 `server="Consul Agent"` 采集返回 404/连接拒绝。
- 原因：Consul 内置服务注册在 8300/8500，并不暴露 /metrics。
- 解决：relabel 中 drop 掉 `__meta_consul_service = "consul"`（见 6.4.5）。

**坑 6：K8s 发现 403/无权限**

- 报错原样：`server returned HTTP 403 Forbidden`。
- 原因：ServiceAccount 没有对对应资源的 list/watch 权限（RBAC）。
- 解决：给 ServiceAccount 绑定 ClusterRole（get/list/watch nodes、pods、services、endpoints 等）；阶段十一有完整 RBAC 示例。

**坑 7：节点名/服务名含非法字符**

- 报错原样：`Node name "xxx.xxx.com" will not be discoverable via DNS due to invalid characters`。
- 原因：Consul 节点名只允许字母数字和短横线，不能带域名点号。
- 解决：节点名用短横线命名（如 `consul-node1`），不要用完整域名。

---
## 阶段七：各类 Exporter 实战

### 阶段目标

- 掌握 Node Exporter 的高级用法（systemd 服务状态、textfile 自定义指标）；
- 部署并使用 **MySQL、Redis、Nginx、Consul、Java（JMX）、HAProxy、Blackbox** 的 Exporter；
- 每个组件都完成"部署 → 采集 → Grafana 看板"闭环。

Exporter 分三类：**应用内置**（Prometheus、Grafana、Zookeeper、MinIO 等自带指标）、**应用外置**（MySQL、Redis 等需单独装 Exporter）、**定制开发**（阶段三已讲）。

### 7.1 Node Exporter 高级采集

#### 7.1.1 systemd 服务状态采集

- **是什么**：node_exporter 加 `--collector.systemd` 参数后，会采集系统中所有 systemd 服务的状态，指标为 `node_systemd_unit_state`。
- **为什么需要**：可以监控关键服务（nginx、mysql、sshd）是否在运行，服务挂了直接告警，不必为每个服务单独做探测。
- **指标形态**：每个服务有多种状态（active、inactive、failed、activating、deactivating），当前所处状态值为 1，其余为 0。

**第 1 步：修改 node_exporter 服务文件**

在被监控主机（如 web01）编辑 `/etc/systemd/system/node_exporter.service`（若用阶段二的二进制安装路径），把 ExecStart 改为：

```text
ExecStart=/usr/local/node_exporter/bin/node_exporter \
  --collector.systemd \
  --collector.systemd.unit-include=".*(ssh|nginx|mysql|redis|node_exporter).*\.service"
```

参数解释：

| 参数 | 作用 |
| --- | --- |
| `--collector.systemd` | 启用 systemd 采集器 |
| `--collector.systemd.unit-include` | 正则，只采集匹配的服务；不写则采集全部服务（数量多时指标量大） |
| `--collector.systemd.unit-exclude` | 正则，排除匹配的服务 |

::: warning
只显示**已安装**的服务，没安装的不会出现；unit-include/exclude 依赖 `--collector.systemd`，单独写不生效。正则要匹配服务的完整单元名（如 `nginx.service`），所以模式末尾要留 `\.service`。
:::

**第 2 步：重启验证**

```bash
systemctl daemon-reload
systemctl restart node_exporter
curl -s localhost:9100/metrics | grep node_systemd_unit_state
```

预期输出（节选）：

```text
node_systemd_unit_state{name="nginx.service",state="active"} 1
node_systemd_unit_state{name="nginx.service",state="inactive"} 0
node_systemd_unit_state{name="nginx.service",state="failed"} 0
node_systemd_unit_state{name="ssh.service",state="active"} 1
```

**第 3 步：告警规则**（服务异常即告警），创建 `/usr/local/prometheus/rules/systemd_alert_rules.yml`：

```yaml
groups:
  - name: systemd-services
    rules:
      - alert: ServiceIsDown
        expr: node_systemd_unit_state{state="active"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "服务 {{ $labels.name }} 已停止"
          description: "{{ $labels.instance }} 上的 {{ $labels.name }} 非 active 超过 1 分钟"
```

#### 7.1.2 textfile 自定义指标采集器

- **是什么**：textfile 采集器会读取指定目录下的 `*.prom` 文本文件，把文件里写好的指标一并暴露出去（默认已启用）。
- **类比**：像在 node_exporter 门口放一个"意见箱"，你的脚本把数值按格式写成纸条丢进去，node_exporter 帮你上报。
- **为什么需要**：适合采集没有专门 Exporter 的指标——比如备份是否成功、证书剩余天数、硬件 RAID 状态、业务批处理结果，用 shell 脚本就能接入。

**第 1 步：建目录并指定**

```bash
mkdir -p /var/lib/node_exporter/textfile
```

修改 node_exporter 的 ExecStart，追加：

```text
  --collector.textfile.directory=/var/lib/node_exporter/textfile
```

**第 2 步：写一个 .prom 文件**

`/var/lib/node_exporter/textfile/backup.pom`（注意文件名以 .prom 结尾）：

```text
# HELP backup_last_success_timestamp 最近一次备份成功的时间戳
# TYPE backup_last_success_timestamp gauge
backup_last_success_timestamp{job="mysql_backup"} 1770000000
# HELP backup_files_count 当前备份文件数量
# TYPE backup_files_count gauge
backup_files_count 7
```

格式要求：每个指标建议有 `# HELP`（说明）和 `# TYPE`（类型）行；指标名、标签写法和 Prometheus 文本格式一致。

**第 3 步：用脚本生成指标（典型用法）**

创建 `/usr/local/bin/write_backup_metrics.sh`：

```bash
#!/bin/bash
METRIC_DIR=/var/lib/node_exporter/textfile
TMP=${METRIC_DIR}/.backup.prom.tmp

# 查找最近一次备份文件（假设备份放在 /data/backup）
LAST=$(find /data/backup -name '*.sql.gz' -printf '%T@\n' 2>/dev/null | sort -n | tail -1 | cut -d. -f1)
COUNT=$(find /data/backup -name '*.sql.gz' 2>/dev/null | wc -l)
[ -z "$LAST" ] && LAST=0

cat > "$TMP" <<EOF
# HELP backup_last_success_timestamp 最近备份成功时间戳
# TYPE backup_last_success_timestamp gauge
backup_last_success_timestamp ${LAST}
# HELP backup_files_count 备份文件数量
# TYPE backup_files_count gauge
backup_files_count ${COUNT}
EOF
mv "$TMP" ${METRIC_DIR}/backup.prom
```

::: tip
脚本一定要先写临时文件再 `mv` 成 .prom——node_exporter 可能正好在你写文件时读取，原子替换避免读到一半。加计划任务：`crontab -e` 加 `5 * * * * /usr/local/bin/write_backup_metrics.sh`。
:::

重启并验证：

```bash
chmod +x /usr/local/bin/write_backup_metrics.sh
bash /usr/local/bin/write_backup_metrics.sh
systemctl restart node_exporter
curl -s localhost:9100/metrics | grep backup_
```

预期输出：

```text
backup_last_success_timestamp{job="mysql_backup"} 1.77e+09
backup_files_count 7
```

---

### 7.2 MySQL 监控（mysqld_exporter）

- **是什么**：mysqld_exporter 连到 MySQL，把数据库状态（连接数、QPS、慢查询、主从延迟、缓冲池等）转成 Prometheus 指标，默认端口 **9104**。
- **为什么需要**：数据库是业务核心，连接数打满、主从延迟、慢查询激增都要提前发现。

#### 7.2.1 MySQL 端准备

在**数据库服务器 db01** 执行，用户 root。

**第 1 步：安装 MySQL**

```bash
apt update && apt -y install mysql-server
systemctl enable --now mysql
```

**第 2 步：（可选）允许远程连接**

Exporter 与 MySQL 同机则不用改。不同机时编辑 `/etc/mysql/mysql.conf.d/mysqld.cnf`，把原值 `bind-address = 127.0.0.1` 改为 `bind-address = 0.0.0.0`，然后 `systemctl restart mysql`，并放通 3306 端口。

**第 3 步：创建监控用户并授权**

```bash
mysql
```

```sql
CREATE USER 'exporter'@'localhost' IDENTIFIED BY '【exporter用户密码】' WITH MAX_USER_CONNECTIONS 3;
GRANT PROCESS, REPLICATION CLIENT, SELECT ON *.* TO 'exporter'@'localhost';
FLUSH PRIVILEGES;
```

权限解释：`PROCESS` 查看所有线程/连接；`REPLICATION CLIENT` 查看主从状态；`SELECT` 查询各系统库。`MAX_USER_CONNECTIONS 3` 限制监控用户连接数，避免 Exporter 异常时占满数据库连接。

若 Exporter 在其他主机，再建 `'exporter'@'【监控服务器网段】'`（如 `'exporter'@'10.0.0.%'`）并同样授权。

#### 7.2.2 安装 mysqld_exporter

在 db01 执行，用户 root。

**第 1 步：下载解压**

```bash
cd /usr/local
wget https://github.com/prometheus/mysqld_exporter/releases/download/v0.20.0/mysqld_exporter-0.20.0.linux-amd64.tar.gz
tar xf mysqld_exporter-0.20.0.linux-amd64.tar.gz
ln -s mysqld_exporter-0.20.0.linux-amd64 mysqld_exporter
cd mysqld_exporter
mkdir -p bin
mv mysqld_exporter bin/
```

备选（GitHub）：

```text
https://github.com/prometheus/mysqld_exporter/releases/download/v0.20.0/mysqld_exporter-0.20.0.linux-amd64.tar.gz
```

**第 2 步：创建数据源配置** `/usr/local/mysqld_exporter/.my.cnf`：

```ini
[client]
host=127.0.0.1
port=3306
user=exporter
password=【exporter用户密码】
```

收紧权限：

```bash
chmod 640 /usr/local/mysqld_exporter/.my.cnf
id prometheus &>/dev/null || useradd -r -s /usr/sbin/nologin prometheus
chown -R prometheus:prometheus /usr/local/mysqld_exporter
```

**第 3 步：创建服务文件**

```bash
cat > /etc/systemd/system/mysqld_exporter.service <<'EOF'
[Unit]
Description=Prometheus MySQL Exporter
After=network.target

[Service]
Type=simple
User=prometheus
Group=prometheus
ExecStart=/usr/local/mysqld_exporter/bin/mysqld_exporter \
  --config.my-cnf=/usr/local/mysqld_exporter/.my.cnf \
  --web.listen-address=0.0.0.0:9104
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable --now mysqld_exporter
ss -lntp | grep 9104
```

验证：

```bash
curl -s localhost:9104/metrics | grep -E 'mysql_up|mysql_global_status_threads_connected'
```

预期输出：

```text
mysql_up 1
mysql_global_status_threads_connected 8
```

`mysql_up` 为 1 表示 Exporter 成功连上数据库；为 0 说明连接/认证有问题。

#### 7.2.3 Prometheus 采集与 Grafana 看板

在 prometheus.yml 加：

```yaml
  - job_name: 'mysqld_exporter'
    static_configs:
      - targets: ['【数据库服务器IP】:9104']
        labels:
          app: mysql
```

```bash
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus
```

Grafana 导入看板（推荐 17320 中文版，另有 7362、14057、11323）：

```text
https://grafana.com/grafana/dashboards/17320-mysql-overview/
```

#### 7.2.4 Docker Compose 方式

```yaml
version: '3.6'

networks:
  monitoring:
    driver: bridge

volumes:
  mysqld_data: {}

services:
  mysqld:
    image: mysql:8.0
    restart: always
    volumes:
      - mysqld_data:/var/lib/mysql
    environment:
      MYSQL_ROOT_PASSWORD: 【root密码】
    networks:
      - monitoring
    ports:
      - "3306:3306"

  mysqld-exporter:
    image: prom/mysqld-exporter:v0.20.0
    restart: always
    command:
      - --collect.global_status
      - --collect.info_schema.innodb_metrics
      - --collect.engine_innodb_status
      - --collect.binlog_size
    environment:
      DATA_SOURCE_NAME: exporter:【exporter用户密码】@(mysqld:3306)/
    networks:
      - monitoring
    ports:
      - "9104:9104"
    depends_on:
      - mysqld
```

启动后在 MySQL 里创建 exporter 用户（容器网段，如 `'exporter'@'172.%.%.%'`），授权同上。

---

### 7.3 Redis 监控（redis_exporter）

- **是什么**：redis_exporter 连接 Redis，采集内存使用、连接数、命中率、过期/淘汰键、主从等指标，默认端口 **9121**。
- **为什么需要**：Redis 内存满、被 OOM、命中率骤降都会直接影响业务。

#### 7.3.1 Redis 端准备

在 db01（或独立缓存服务器）执行：

```bash
apt update && apt -y install redis-server
```

编辑 `/etc/redis/redis.conf`：

- 原值 `bind 127.0.0.1 -::1`，需要远程访问时改为 `bind 0.0.0.0`；
- 取消注释并设置密码：`requirepass 【Redis密码】`；

```bash
systemctl restart redis-server
```

验证密码生效：

```bash
redis-cli -a 【Redis密码】 ping
```

预期输出：`PEMON`（警告会提示命令行用密码不安全，属正常）。

#### 7.3.2 安装 redis_exporter

**第 1 步：下载解压**

```bash
cd /usr/local
wget https://github.com/oliver006/redis_exporter/releases/download/v1.92.1/redis_exporter-v1.92.1.linux-amd64.tar.gz
tar xf redis_exporter-v1.92.1.linux-amd64.tar.gz
ln -s redis_exporter-v1.92.1.linux-amd64 redis_exporter
cd redis_exporter
mkdir bin
mv redis_exporter bin/
```

**第 2 步：创建服务文件**

```bash
id prometheus &>/dev/null || useradd -r -s /usr/sbin/nologin prometheus
chown -R prometheus:prometheus /usr/local/redis_exporter

cat > /etc/systemd/system/redis_exporter.service <<'EOF'
[Unit]
Description=Prometheus Redis Exporter
After=network.target

[Service]
Type=simple
User=prometheus
Group=prometheus
ExecStart=/usr/local/redis_exporter/bin/redis_exporter \
  -redis.addr=redis://127.0.0.1:6379 \
  -redis.password=【Redis密码】 \
  -web.listen-address=0.0.0.0:9121
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable --now redis_exporter
ss -lntp | grep 9121
```

参数解释：`-redis.addr` Redis 地址（单机或集群节点，集群可逗号分隔多个）；`-redis.password` 密码；无密码可省。多个不同密码的实例可用 `-redis.addr-key`/环境变量 `REDIS_ADDR1` 等方式，见项目文档。

验证：

```bash
curl -s localhost:9121/metrics | grep -E 'redis_up|redis_connected_clients'
```

预期输出：

```text
redis_up 1
redis_connected_clients 1
```

#### 7.3.3 采集与看板

prometheus.yml 加：

```yaml
  - job_name: 'redis_exporter'
    static_configs:
      - targets: ['【数据库服务器IP】:9121']
        labels:
          app: redis
```

```bash
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus
```

Grafana 看板推荐 763、11835、14615：

```text
https://grafana.com/grafana/dashboards/763-redis-dashboard/
```

#### 7.3.4 Kubernetes 方式（了解）

Redis 与 redis_exporter 同 Pod 两个容器（redis_exporter 镜像 `oliver006/redis_exporter:v1.92.1`，端口 9121），再建 Service 暴露；Prometheus 采集该 Service。生产更推荐用 Redis Operator 或在 Pod 注解里声明采集。

---
