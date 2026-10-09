---
category: 监控
difficulty: 高级
---

# Prometheus 实战 09：容器监控、联邦与长期存储

> **Prometheus 实战系列（共 10 篇）**
> ← 上一篇 [Prometheus 实战 08](./monitor-prometheus-08-more-exporters) ｜ 下一篇 [Prometheus 实战 10](./monitor-prometheus-10-k8s-sop-faq) →
> [返回监控索引](./monitor)

## 阶段八：cAdvisor 容器监控

### 阶段目标

- 理解为什么 Node Exporter 不适合监控容器；
- 用 cAdvisor 采集所有运行中容器的 CPU、内存、网络、文件系统指标；
- 完成 Prometheus 采集与 Grafana 看板。

### 8.1 cAdvisor 简介

- **是什么**：cAdvisor（Container Advisor，容器顾问）是 Google 开源的容器监控守护进程，收集、聚合、处理并导出本机所有运行容器的资源隔离参数、资源使用历史、直方图和网络统计，默认在 8080 端口暴露 `/metrics`。
- **类比**：Node Exporter 是给"整栋房子"装的总电表，cAdvisor 是给房子里每个"集装箱房间"单独装的电表水表。
- **为什么需要**：容器共享宿主机内核、数量多、生命周期短，需要按容器维度统计资源；cAdvisor 通过 Linux 的 cgroups 获取这些数据。

要点：

- 一个 cAdvisor **只监控一台主机**；Kubernetes 中以 DaemonSet 部署到每个节点；
- cAdvisor 内置在 kubelet 中；Kubernetes 1.12 之后移除了 cAdvisor 独立的 4194 端口；
- 项目主页：`https://github.com/google/cadvisor`。

### 8.2 Docker 方式部署 cAdvisor（推荐）

在**运行容器的主机**（如 app01）执行，用户 root。

**第 1 步：准备 Docker**

```bash
apt update && apt -y install docker.io
```

配置镜像加速与日志轮转，编辑 `/etc/docker/daemon.json`：

```json
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://docker.1panel.live",
    "https://hub.rat.dev"
  ],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "3"
  }
}
```

```bash
systemctl restart docker
docker info | grep -A3 'Registry Mirrors'
```

**第 2 步：启动 cAdvisor 容器**

```bash
VERSION=v0.60.6
docker run -d \
  --volume=/:/rootfs:ro \
  --volume=/var/run:/var/run:ro \
  --volume=/sys:/sys:ro \
  --volume=/var/lib/docker/:/var/lib/docker:ro \
  --volume=/dev/disk/:/dev/disk:ro \
  --publish=8080:8080 \
  --detach=true \
  --name=cadvisor \
  --restart=always \
  --privileged \
  --device=/dev/kmsg \
  ghcr.io/google/cadvisor:$VERSION
```

挂载参数解释：

| 挂载 | 作用 |
| --- | --- |
| `/:/rootfs:ro` | 只读挂载宿主机根文件系统，用于识别容器在宿主机上的路径 |
| `/var/run:/var/run:ro` | 读取容器运行时的 socket 等信息 |
| `/sys:/sys:ro` | 读取 cgroups 资源统计（核心数据来源） |
| `/var/lib/docker:/var/lib/docker:ro` | 读取 Docker 容器/镜像层信息 |
| `/dev/disk:/dev/disk:ro` | 读取磁盘设备信息 |

其他参数：`--privileged` 授予特权（cAdvisor 需要访问 cgroups、设备）；`--device=/dev/kmsg` 提供内核日志设备；`ro` 表示只读，保证 cAdvisor 不会改动宿主机。

::: tip
镜像已迁移到 GitHub 容器仓库 `ghcr.io/google/cadvisor`。拉不下来时用国内镜像：`registry.cn-beijing.aliyuncs.com/wangxiaochun/cadvisor:v0.51.0`（第三方同步，版本可能滞后），或通过加速代理拉取。使用 containerd 运行时时，把 `/var/lib/docker` 挂载换成 `/var/lib/containerd`。
:::

**第 3 步：验证**

```bash
ss -lntp | grep 8080
curl -s localhost:8080/metrics | grep -E 'cadvisor_version_info|container_memory_usage_bytes'
```

预期输出（节选）：

```text
cadvisor_version_info{cadvisorRevision="...",cadvisorVersion="v0.60.6",dockerVersion="..."} 1
container_memory_usage_bytes{id="/",image="",name=""} 1.23e+09
```

浏览器访问 `http://【应用服务器IP】:8080/` 能看到 cAdvisor 自带的容器列表界面。

### 8.3 二进制方式（备选）

```bash
cd /usr/local
wget https://github.com/google/cadvisor/releases/download/v0.60.6/cadvisor-v0.60.6-linux-amd64
install cadvisor-v0.60.6-linux-amd64 /usr/local/bin/cadvisor
```

创建服务文件 `/etc/systemd/system/cadvisor.service`：

```text
[Unit]
Description=cAdvisor
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/cadvisor -port=8080
Restart=on-failure
LimitNOFILE=100000

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable --now cadvisor
```

::: warning
cAdvisor 需要读取 cgroups 与设备信息，**不能以普通用户启动（权限不足）**；二进制方式用 root 运行，容器方式用 privileged。
:::

### 8.4 Prometheus 采集

编辑 `/usr/local/prometheus/conf/prometheus.yml` 加：

```yaml
  - job_name: 'cadvisor'
  static_configs:
    - targets:
        - '【应用服务器IP】:8080'
      labels:
        app: cadvisor
```

有多台容器主机就把它们都列进 targets，或用文件发现管理。

```bash
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus
```

验证：Targets 页 cadvisor 目标为 UP。

### 8.5 cAdvisor 常用指标

| 指标 | 类型 | 含义 |
| --- | --- | --- |
| `container_cpu_usage_seconds_total` | counter | 容器累计 CPU 占用时间（秒） |
| `container_cpu_user_seconds_total` | counter | 累计用户态 CPU 时间 |
| `container_cpu_system_seconds_total` | counter | 累计内核态 CPU 时间 |
| `container_cpu_load_average_10s` | gauge | 过去 10 秒容器 CPU 平均负载 |
| `container_cpu_cfs_throttled_seconds_total` | counter | 容器被 CPU 限流（throttle）的累计时间 |
| `container_memory_usage_bytes` | gauge | 容器当前内存使用量 |
| `container_memory_working_set_bytes` | gauge | 工作集内存（**判断 OOM 的主要依据**） |
| `container_memory_max_usage_bytes` | gauge | 历史最大内存使用量 |
| `container_spec_memory_limit_bytes` | gauge | 容器内存限制（未限制为 0） |
| `container_network_receive_bytes_total` | counter | 网络累计接收字节 |
| `container_network_transmit_bytes_total` | counter | 网络累计发送字节 |
| `container_network_receive_errors_total` | counter | 网络接收错误累计 |
| `container_fs_reads_bytes_total` | counter | 文件系统累计读取字节 |
| `container_fs_writes_bytes_total` | counter | 文件系统累计写入字节 |
| `container_start_time_seconds` | gauge | 容器启动时间戳 |
| `machine_cpu_cores` | gauge | 宿主机 CPU 核数 |
| `machine_memory_bytes` | gauge | 宿主机总内存 |

### 8.6 常用 PromQL

**单个容器 CPU 使用率（百分比，按容器名）**：

```promql
sum(rate(container_cpu_usage_seconds_total{image!="",name="【容器名】"}[1m])) by (name) * 100
```

**所有容器 CPU 使用率**：

```promql
sum(rate(container_cpu_usage_seconds_total{image!="",name=~".+"}[1m])) by (name) * 100
```

`{image!=""}` 过滤掉宿主机自身的聚合序列，只保留真正的容器；`name=~".+"` 要求 name 非空。

**容器内存使用率（相对限制值）**：

```promql
container_memory_working_set_bytes{image!=""} / container_spec_memory_limit_bytes{image!=""} * 100
```

::: warning
如果容器启动时**没有设置内存限制**，`container_spec_memory_limit_bytes` 为 0，上面的除法会得到无意义的无穷大或被忽略。生产必须给容器设内存限制（docker `--memory`、compose `mem_limit`/`deploy.resources`）。
:::

**容器网络接收速率（字节/秒）**：

```promql
sum(rate(container_network_receive_bytes_total{image!=""}[1m])) by (name)
```

**容器网络发送速率**：

```promql
sum(rate(container_network_transmit_bytes_total{image!=""}[1m])) by (name)
```

**容器磁盘写入速率**：

```promql
sum(rate(container_fs_writes_bytes_total{image!=""}[1m])) by (name)
```

### 8.7 Grafana 看板

Grafana 导入看板 **193**（经典 Docker 监控）或 **14282**：

```text
https://grafana.com/grafana/dashboards/193
https://grafana.com/grafana/dashboards/14282
```

看板若没有按容器过滤的下拉框，可自定义变量：看板设置 → Variables → New，变量名如 `container_name`，查询用：

```promql
label_values(container_memory_usage_bytes{image!=""}, name)
```

保存后顶部出现容器名下拉框，面板查询里用 `{name=~"$container_name"}` 过滤。

### 8.8 Kubernetes DaemonSet 方式（了解）

cAdvisor 以 DaemonSet 部署到每个节点（含 master，用 tolerations 容忍控制面污点），hostNetwork 使用宿主机网络，挂载宿主机的 /、/var/run、/sys、/var/lib/docker（containerd 环境为 /var/lib/containerd）、/dev/disk。关键结构：

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: cadvisor
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app: cadvisor
  template:
    metadata:
      labels:
        app: cadvisor
    spec:
      tolerations:
        - key: node-role.kubernetes.io/control-plane
          operator: Exists
          effect: NoSchedule
      hostNetwork: true
      restartPolicy: Always
      volumes:
        - name: root
          hostPath: {path: /}
        - name: run
          hostPath: {path: /var/run}
        - name: sys
          hostPath: {path: /sys}
        - name: docker
          hostPath: {path: /var/lib/docker}
        - name: dev
          hostPath: {path: /dev/disk}
      containers:
        - name: cadvisor
          image: ghcr.io/google/cadvisor:v0.60.6
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 8080
          volumeMounts:
            - {name: root, mountPath: /rootfs}
            - {name: run, mountPath: /var/run}
            - {name: sys, mountPath: /sys}
            - {name: docker, mountPath: /var/lib/docker}
            - {name: dev, mountPath: /dev/disk}
```

::: tip
现代 Kubernetes 中 kubelet 已内置 cAdvisor，kube-prometheus-stack 通过采集 kubelet 的 `/metrics/cadvisor` 端点即可获得容器指标，通常不需要再单独部署 cAdvisor DaemonSet——阶段十一详述。
:::

---

### 本阶段命令速查表

```bash
# 启动 cAdvisor（容器方式）
docker run -d --name=cadvisor --restart=always -p 8080:8080 \
  -v /:/rootfs:ro -v /var/run:/var/run:ro -v /sys:/sys:ro \
  -v /var/lib/docker:/var/lib/docker:ro -v /dev/disk:/dev/disk:ro \
  --privileged --device=/dev/kmsg \
  ghcr.io/google/cadvisor:v0.60.6

# 验证
curl -s localhost:8080/metrics | grep cadvisor_version_info

# Prometheus 采集 job 指向 8080
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus

# Grafana 看板
# 193 / 14282
```

---

### 本阶段常见坑与解决

**坑 1：cAdvisor 容器启动即退出**

- 报错/现象：`docker ps` 看不到，`docker logs cadvisor` 报挂载/权限错误。
- 原因：挂载路径不存在；缺少 privileged。
- 解决：确认宿主机挂载源存在；加 `--privileged --device=/dev/kmsg`。

**坑 2：拉取 ghcr.io 镜像超时**

- 报错原样：`Error response from daemon: Head "https://ghcr.io/...": dial tcp ... i/o timeout`。
- 原因：ghcr.io 在国内访问不稳定。
- 解决：用国内同步镜像（如阿里云个人同步仓库）或镜像加速；先在能访问的机器 `docker pull` 后 `docker save` 离线拷贝，再 `docker load`。

**坑 3：指标里把宿主机也当成容器**

- 现象：查询出现 name 为空、id 为 `/` 的超大序列。
- 原因：cAdvisor 同时输出宿主机聚合数据。
- 解决：查询统一加 `{image!=""}` 或 `{name=~".+"}` 过滤。

**坑 4：内存使用率算出来是无穷大/异常**

- 现象：内存面板数据离谱。
- 原因：容器没设内存限制，limit 为 0。
- 解决：给容器设内存限制；或改用相对宿主机总内存计算：`container_memory_working_set_bytes / machine_memory_bytes`。

**坑 5：containerd 环境下容器信息为空**

- 现象：cAdvisor 正常但看不到 containerd 容器。
- 原因：挂载的是 /var/lib/docker，而运行时是 containerd。
- 解决：挂载改为 `/var/lib/containerd:/var/lib/containerd:ro`。

**坑 6：8080 端口冲突**

- 报错原样：`docker: Error response from daemon: driver failed programming external connectivity on endpoint ... Bind for 0.0.0.0:8080 failed: port is already allocated.`
- 原因：宿主机 8080 已被其他服务占用。
- 解决：`ss -lntp | grep 8080` 找到占用者；改用 `-p 其他端口:8080`。

---
## 阶段九：Prometheus 联邦（Federation）

### 阶段目标

- 理解单个 Prometheus 的容量瓶颈；
- 掌握**分层联邦**的配置方法，实现"分节点采集、中心节点汇总"；
- 清楚联邦的能力边界（它不是高可用、不是长期存储）。

### 9.1 联邦说明

- **是什么**：联邦允许一台 Prometheus 从另一台 Prometheus 的 `/federate` 端点抓取数据。下层（从）节点各自采集一批目标，上层（主/中心）节点只从下层节点拉取汇总数据，Grafana 接中心节点。
- **类比**：像公司层级汇报——每个组长（从 Prometheus）统计本组数据，经理（中心 Prometheus）只汇总各组长的报表，不必直接管每个人。
- **为什么需要**：一台 Prometheus 能管理的目标数量有限，目标和序列持续增长后单机压力越来越大；联邦把采集压力分散到多台。

两种模式：

| 模式 | 说明 |
| --- | --- |
| **分层联邦（常用）** | 树形拓扑，上层从大量下层节点拉取**聚合**序列，可扩展到数十个数据中心、百万节点；下层保留实例级明细，上层只存作业级聚合 |
| 跨服务联邦 | 一个服务的 Prometheus 从另一个服务的 Prometheus 拉取选定数据，在单台里同时拥有两个数据集做查询/告警 |

**联邦的能力边界（务必清楚）**：

- 它**不是真正的高可用方案**（中心节点挂了全局视图就没了）；
- 它**不是全量存储**（上层只存匹配到的、通常是聚合后的指标）；
- 查询能力有限，适合做**全局视图和汇总指标**——中心节点只看各集群 CPU、内存、SLA、核心业务指标；
- 想要真正的 HA、全量指标和长期存储，需要 VictoriaMetrics、Thanos 等方案（阶段十讲 VictoriaMetrics）。

### 9.2 实战：分层联邦

#### 9.2.1 规划

在星辰电商环境中扩展两台机器演示联邦：

| 角色 | 地址 |
| --- | --- |
| Prometheus 主（中心）节点 | 【监控服务器IP】（即 monitor，10.0.0.10） |
| 联邦从节点 1 | 【联邦节点1IP】（如 10.0.0.15） |
| 联邦从节点 2 | 【联邦节点2IP】（如 10.0.0.16） |
| Node Exporter（从节点1 负责） | 【Web服务器IP】、【应用服务器IP】 |
| Node Exporter（从节点2 负责） | 【数据库服务器IP】 |

#### 9.2.2 部署各节点

三台 Prometheus 安装方法完全一样，按阶段二的二进制方式在从节点 1、从节点 2 各装一套 Prometheus（版本 3.15.0）；所有被监控主机按阶段二装好 Node Exporter。

#### 9.2.3 配置从节点采集 Node Exporter

**从节点 1** 编辑 `/usr/local/prometheus/conf/prometheus.yml`：

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
scrape_configs:
  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]
  - job_name: "node_exporter"
    static_configs:
      - targets:
          - "【Web服务器IP】:9100"
          - "【应用服务器IP】:9100"
```

**从节点 2** 的 prometheus.yml：

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
scrape_configs:
  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]
  - job_name: "node_exporter"
    static_configs:
      - targets:
          - "【数据库服务器IP】:9100"
```

两台分别检查生效：

```bash
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus
```

验证：各自 Targets 页 node_exporter 目标为 UP，能查到本片区主机的指标。

#### 9.2.4 配置中心节点汇总

`/federate` 端点返回所选时间序列的当前值。必须至少传一个 `match[]` URL 参数（即时向量选择器），多个 match[] 取并集。

在**中心节点（monitor）**编辑 `/usr/local/prometheus/conf/prometheus.yml`，追加两个 job：

```yaml
  - job_name: 'federate-01'
    scrape_interval: 15s
    honor_labels: true
    metrics_path: '/federate'
    params:
      'match[]':
        - '{job="prometheus"}'
        - '{job="node_exporter"}'
        - '{__name__=~"node.*"}'
    static_configs:
      - targets:
          - '【联邦节点1IP】:9090'

  - job_name: 'federate-02'
    scrape_interval: 15s
    honor_labels: true
    metrics_path: '/federate'
    params:
      'match[]':
        - '{job="prometheus"}'
        - '{job="node_exporter"}'
        - '{__name__=~"node.*"}'
    static_configs:
      - targets:
          - '【联邦节点2IP】:9090'
```

逐字段解释：

| 字段 | 作用 |
| --- | --- |
| `metrics_path: /federate` | 从源节点的联邦端点采集（默认采集路径是 /metrics，这里必须改） |
| `honor_labels: true` | **关键**：不覆盖源节点暴露的标签（如 instance、job），否则中心会把目标地址写成从节点地址，数据全乱 |
| `params.match[]` | 选择要拉取哪些序列；**不写 match[] 不会采集任何数据** |
| match 示例 `{job="node_exporter"}` | 只拉该 job 的数据，job 名必须与从节点配置的 job_name 完全匹配 |
| match 示例 `{__name__=~"node.*"}` | 拉所有以 node 开头的指标；多个 match 条件之间是**或（并集）**关系 |

检查生效：

```bash
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus
```

#### 9.2.5 验证

- 中心节点 Targets 页：federate-01、federate-02 为 UP；
- 在中心节点 Graph 查询 `node_os_info`，能看到分布在各从节点后面的所有主机；
- 查询 `up`，能看到从节点及其下属目标；
- Grafana 数据源仍接中心节点，导入 8919 看板，能展示全部主机数据。

#### 9.2.6 从节点扩容

在**从节点 1** 的 node_exporter job 里加新主机：

```yaml
  - job_name: "node_exporter"
    static_configs:
      - targets:
          - "【Web服务器IP】:9100"
          - "【应用服务器IP】:9100"
          - "【新主机IP】:9100"
```

```bash
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus
```

等一个抓取周期，中心节点自动汇总到新主机数据，**中心节点无需改动**——这就是联邦分层带来的扩展性：下层扩容不影响上层。

### 9.3 联邦层级拓扑

![Prometheus 联邦分层拓扑](/guide/diagrams/federation-hierarchy.svg)

::: tip
生产建议：① 中心节点只采集**记录规则产出的聚合指标**（如 `instance:node_cpu:avg_rate5m`），大幅减少上层序列量；② 中心节点可双活（两台采同样的从节点，配合 external_labels 区分）；③ 跨数据中心时从节点部署在各机房本地，中心通过内网专线/VPN 拉取。
:::

---

### 本阶段命令速查表

```bash
# 从节点：正常配置本地采集 job
# 中心节点：联邦 job 四要素
#   metrics_path: /federate
#   honor_labels: true
#   params.match[]: [选择器,...]
#   static_configs.targets: [从节点IP:9090]
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus

# 中心节点验证汇总结果
# Graph 查询 up 或 node_os_info，应看到所有片区主机
```

---

### 本阶段常见坑与解决

**坑 1：中心节点采集不到任何数据**

- 现象：federate 目标 UP，但查不到从节点的业务指标。
- 原因：没配 `match[]`，或 match 的 job 名与从节点 job_name 不一致。
- 解决：至少配一个 match[]；核对 job 名完全一致（大小写敏感）。

**坑 2：中心节点数据的 instance 全变成从节点地址**

- 现象：主机明细数据串了、标签不对。
- 原因：没设 `honor_labels: true`，中心用目标地址（从节点）覆盖了原始 instance 标签。
- 解决：联邦 job 必须 `honor_labels: true`。

**坑 3：metrics_path 忘了改**

- 报错/现象：federate 目标采集报错或数据不对。
- 原因：默认抓 /metrics，拿到的是从节点自身指标而非联邦数据。
- 解决：显式配置 `metrics_path: /federate`。

**坑 4：中心节点序列量爆炸**

- 现象：中心节点很快也扛不住。
- 原因：用 `{__name__=~".+"}` 把从节点全量明细都拉上来了。
- 解决：只拉聚合指标/记录规则结果；分层存储明细与汇总。

**坑 5：误以为联邦做了高可用**

- 现象：中心节点宕机后全局视图丢失。
- 原因：联邦是数据汇总方案，不是 HA。
- 解决：中心双活；真正 HA + 长期存储用 VictoriaMetrics/Thanos（阶段十）。

---
## 阶段十：Prometheus 存储与 VictoriaMetrics

### 阶段目标

- 理解本地 TSDB 的数据组织方式与保留策略；
- 会估算磁盘容量；
- 部署 **VictoriaMetrics 单机版和集群版**作为长期远程存储；
- 完成 Prometheus remote_write/remote_read 与 Grafana 对接。

### 10.1 本地 TSDB

#### 10.1.1 存储机制（三句话）

- Prometheus 内置时序数据库 TSDB：最新数据先放内存（Head 块），同时写预写日志 WAL 防丢失；
- 每 2 小时把内存数据刷成一个不可修改的 Block（块）落盘，后台再把小块压缩合并成大块；
- 超过保留期限的块被删除。

#### 10.1.2 数据目录结构

数据目录默认 `/usr/local/prometheus/data`：

```text
data/
├── 01GH5S5W4PDFXCS40VF7NZCP0G/     # 2 小时块（目录名是 ULID）
│   ├── chunks/                     # 时序数据，段文件如 000001，单段上限 512MB
│   ├── index                       # 索引：按指标名+标签定位序列在 chunks 中的位置
│   ├── meta.json                   # 块元数据（样本数、时间范围、压缩级别）
│   └── tombstones                  # 软删除标记（删除不立即清数据，查询时过滤）
├── chunks_head/                    # 内存 Head 块通过 mmap 映射的近期数据
├── wal/                            # 预写日志，段默认 128MB，含 checkpoint
├── lock
└── queries.active
```

WAL 是"先写日志再改数据"的顺序日志，崩溃后重放 WAL 即可恢复；至少保留 3 个 WAL 段，高流量实例保留更多以覆盖 2 小时原始数据。

#### 10.1.3 本地存储参数

在服务文件 ExecStart 配置：

| 参数 | 作用 |
| --- | --- |
| `--storage.tsdb.path` | 数据目录，默认安装目录下 data |
| `--storage.tsdb.retention.time` | 数据保留时间，默认 15d；如 `30d`、`90d` |
| `--storage.tsdb.retention.size` | 块数据总磁盘上限（不含 WAL），如 `100GB`；**超限先删最旧数据** |
| `--storage.tsdb.wal-compression` | WAL 压缩，默认开启 |

::: warning
retention.time 和 retention.size **任一满足就删旧数据**。retention.size 不是单段文件大小，是所有块的总量。生产建议两个都设：时间兜底 + 空间兜底，防止磁盘被写爆。
:::

#### 10.1.4 磁盘容量估算

公式：

```text
所需磁盘 = 保留秒数 × 每秒摄入样本数 × 每样本字节数
```

Prometheus 本地压缩后每样本约 1～2 字节（Gorilla 压缩），规划时按 2 字节、再乘 2～3 倍冗余（WAL、chunks_head 峰值）较稳妥。

示例：每秒摄入 10000 样本、保留 30 天：

```text
30×86400 秒 × 10000 × 2 字节 ≈ 518 GB（块数据），再留 WAL/Head 冗余
```

磁盘最小尺寸主要取决于 wal 和 chunks_head 的峰值空间（每 2 小时达一次峰值）。

### 10.2 VictoriaMetrics 简介

- **是什么**：VictoriaMetrics（VM）是 Go 实现的、可水平扩展的时序数据库与监控方案，可作为 Prometheus 的长期存储，兼容 Prometheus 查询 API（Grafana 可直接把它当 Prometheus 数据源）。
- **为什么需要**：本地 TSDB 是单点、不支持集群；VM 解决高可用、水平扩展和长期存储，且数据本地持久化，查询性能优于依赖对象存储的 Thanos。
- **版本选择**：数据摄入低于 100 万样本/秒用**单机版**（单机本身不内置告警，告警可用 vmalert）；需要水平拆分、多租户用**集群版**。

官方资源：

```text
官网：https://victoriametrics.com/
文档：https://docs.victoriametrics.com/
单机文档：https://docs.victoriametrics.com/single-server-victoriametrics/
集群文档：https://docs.victoriametrics.com/cluster-victoriametrics/
```

### 10.3 单机版部署

在**监控服务器 monitor**（或独立存储主机）执行，用户 root。

**第 1 步：下载**

```bash
cd /usr/local/src
VM_VERSION=v1.152.0
wget https://github.com/VictoriaMetrics/VictoriaMetrics/releases/download/${VM_VERSION}/victoria-metrics-linux-amd64-${VM_VERSION}.tar.gz
tar xf victoria-metrics-linux-amd64-${VM_VERSION}.tar.gz
mv victoria-metrics-prod /usr/local/bin/
```

::: tip
不要下载 enterprise（企业版，需授权）。GitHub 慢时可在 URL 前加 `https://ghproxy.net/` 等代理。
:::

**第 2 步：用户与目录**

```bash
useradd -r -s /usr/sbin/nologin victoriametrics
mkdir -p /data/victoriametrics
chown victoriametrics:victoriametrics /data/victoriametrics
```

**第 3 步：服务文件**

```bash
cat > /etc/systemd/system/victoriametrics.service <<'EOF'
[Unit]
Description=VictoriaMetrics
Documentation=https://docs.victoriametrics.com/single-server-victoriametrics/
After=network.target

[Service]
Type=simple
User=victoriametrics
Group=victoriametrics
ExecStart=/usr/local/bin/victoria-metrics-prod \
  -httpListenAddr=0.0.0.0:8428 \
  -storageDataPath=/data/victoriametrics \
  -retentionPeriod=6 \
  -loggerTimezone=Asia/Shanghai
Restart=on-failure
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable --now victoriametrics
ss -lntp | grep 8428
```

参数解释：`-httpListenAddr` 监听地址，默认 8428；`-storageDataPath` 数据目录；`-retentionPeriod` 保留时长，不带后缀单位是**月**（如 6 = 6 个月），也支持 h/d/w/y；`-loggerTimezone` 日志时区。

**第 4 步：Prometheus 远程写入**，编辑 `/usr/local/prometheus/conf/prometheus.yml`，与 global 平级加：

```yaml
remote_write:
  - url: http://【监控服务器IP】:8428/api/v1/write
```

```bash
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus
```

**第 5 步：验证**

- VM 自带查询界面：`http://【监控服务器IP】:8428/vmui`，能查到 Prometheus 写入的指标；
- Grafana 添加 Prometheus 类型数据源，URL 填 `http://【监控服务器IP】:8428`，保存测试成功；
- 导入 1860 等看板时选这个数据源，数据正常展示。

Docker 方式（备选）：

```bash
docker run -d --name victoriametrics --restart=always -p 8428:8428 \
  -v /data/victoriametrics:/victoria-metrics-data \
  victoriametrics/victoria-metrics:v1.152.0
```

### 10.4 集群版

#### 10.4.1 组件与端口

| 组件 | 职责 | 端口 |
| --- | --- | --- |
| **vminsert** | 接收写入（实现 remote_write），按指标名+标签一致性哈希分片到 vmstorage；无状态、易扩容 | 8480（HTTP） |
| **vmstorage** | 存储数据（有状态），节点间互不交互，分片与副本由 vminsert/vmselect 处理 | 8482（HTTP）、8400（对 vminsert）、8401（对 vmselect） |
| **vmselect** | 接收查询（实现 remote_read），向各 vmstorage 查询后合并返回；无状态 | 8481（HTTP） |
| vmagent | 替代 Prometheus 做抓取，支持多后端、本地缓存，pull/push 都支持 | 8429 |
| vmalert | 告警/记录规则执行，配合 VM 使用 | 8880 |

多租户端点格式：

```text
写入：http://<vminsert>:8480/insert/<accountID>/prometheus
查询：http://<vmselect>:8481/select/<accountID>/prometheus
```

`<accountID>` 是租户标识（如 0）。副本由 vminsert 的 `-replicationFactor` 控制，生产推荐 2 或 3；副本自动写到哈希环的相邻节点。一个 vmstorage 故障时约丢失 1/N 历史数据（N 为 storage 数），有副本则不丢。

#### 10.4.2 二进制部署（3 节点，每节点跑三个组件）

在**三个节点**（如 10.0.0.201、202、203）分别执行。

**第 1 步：下载集群二进制**

```bash
cd /usr/local/src
VM_VERSION=v1.152.0
wget https://github.com/VictoriaMetrics/VictoriaMetrics/releases/download/${VM_VERSION}/victoria-metrics-linux-amd64-${VM_VERSION}-cluster.tar.gz
tar xf victoria-metrics-linux-amd64-${VM_VERSION}-cluster.tar.gz -C /usr/local/bin/
ls /usr/local/bin/ | grep vm
```

解压得到 `vminsert-prod`、`vmselect-prod`、`vmstorage-prod`。

**第 2 步：vmstorage（每个节点，注意 IP 不同）**

```bash
useradd -r -s /usr/sbin/nologin victoriametrics
mkdir -p /data/vmstorage
chown -R victoriametrics:victoriametrics /data/vmstorage

cat > /etc/systemd/system/vmstorage.service <<'EOF'
[Unit]
Description=VM storage
After=network.target

[Service]
Type=simple
User=victoriametrics
ExecStart=/usr/local/bin/vmstorage-prod \
  -httpListenAddr :8482 \
  -vminsertAddr :8400 \
  -vmselectAddr :8401 \
  -storageDataPath /data/vmstorage \
  -loggerTimezone Asia/Shanghai
Restart=on-failure
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable --now vmstorage
ss -lntp | grep -E '8482|8400|8401'
```

**第 3 步：vminsert（每个节点，storageNode 列全部三个 storage）**

```bash
cat > /etc/systemd/system/vminsert.service <<'EOF'
[Unit]
Description=VM insert
After=network.target

[Service]
Type=simple
User=victoriametrics
ExecStart=/usr/local/bin/vminsert-prod \
  -httpListenAddr :8480 \
  -storageNode=10.0.0.201:8400,10.0.0.202:8400,10.0.0.203:8400 \
  -replicationFactor=2
Restart=on-failure
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable --now vminsert
ss -lntp | grep 8480
```

**第 4 步：vmselect（每个节点）**

```bash
cat > /etc/systemd/system/vmselect.service <<'EOF'
[Unit]
Description=VM select
After=network.target

[Service]
Type=simple
User=victoriametrics
ExecStart=/usr/local/bin/vmselect-prod \
  -httpListenAddr :8481 \
  -storageNode=10.0.0.201:8401,10.0.0.202:8401,10.0.0.203:8401 \
  -dedup.minScrapeInterval=1ms
Restart=on-failure
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable --now vmselect
ss -lntp | grep 8481
```

`-dedup.minScrapeInterval` 用于副本数据去重（replicationFactor>1 时需要）。

集群拓扑：

![VictoriaMetrics 集群拓扑](/guide/diagrams/victoriametrics-cluster.svg)

**第 5 步：Prometheus 对接集群**，编辑 prometheus.yml：

```yaml
remote_write:
  - url: http://10.0.0.201:8480/insert/0/prometheus
  - url: http://10.0.0.202:8480/insert/0/prometheus
  - url: http://10.0.0.203:8480/insert/0/prometheus
remote_read:
  - url: http://10.0.0.201:8481/select/0/prometheus
  - url: http://10.0.0.202:8481/select/0/prometheus
  - url: http://10.0.0.203:8481/select/0/prometheus
```

写多个 remote_write 是为了高可用（任一 vminsert 可用即可写入，配合去重）；也可以只写一个，前面挂负载均衡。

**第 6 步：Grafana 与负载均衡**

Grafana 数据源 URL 填任一 vmselect：`http://10.0.0.201:8481/select/0/prometheus`。生产建议用 HAProxy 对 vmselect（8481）、vminsert（8480）做 TCP 负载均衡，数据源与写入地址统一用 VIP。HAProxy 示例：

```text
listen vmselect-8481
    bind 10.0.0.200:8481
    mode tcp
    server vmselect1 10.0.0.201:8481 check inter 1s fall 3 rise 5
    server vmselect2 10.0.0.202:8481 check inter 1s fall 3 rise 5
    server vmselect3 10.0.0.203:8481 check inter 1s fall 3 rise 5
```

验证：导入 8919、11074、13824 等看板，选 VM 数据源，数据正常；停掉一个 vmstorage，查询与写入仍可用（副本+去重生效）。

::: warning
生产最佳实践：① vmstorage 数量变更必须同步反映到所有 vminsert/vmselect 的 storageNode 列表；② 扩容按"数据多则加 storage、查询多则加 select、写入多则加 insert"；③ storage 数据目录务必挂独立数据盘并做好备份/快照；④ 镜像/二进制不要用 latest，固定版本。
:::

---

### 本阶段命令速查表

```bash
# === 本地保留策略（prometheus 服务文件）===
# --storage.tsdb.retention.time=30d
# --storage.tsdb.retention.size=100GB

# === VM 单机 ===
systemctl enable --now victoriametrics   # 8428
# prometheus.yml: remote_write url .../api/v1/write

# === VM 集群（每节点三服务）===
systemctl enable --now vmstorage vminsert vmselect
# 端口：8480 insert / 8481 select / 8482 storage http / 8400 / 8401

# === 验证 ===
curl -s http://【监控服务器IP】:8428/metrics | grep vm_rows_inserted_total
```

---

### 本阶段常见坑与解决

**坑 1：磁盘很快被写满**

- 现象：Prometheus 数据盘告警/写满。
- 原因：没设 retention 或保留过长；高基数标签导致序列爆炸。
- 解决：设 retention.time + size；排查高基数标签（如把 user_id、request_id 当标签）。

**坑 2：单机 VM 数据没保留够时间**

- 现象：历史数据很快没了。
- 原因：`-retentionPeriod` 不带后缀单位是**月**，但可能误写或磁盘超限触发删除。
- 解决：明确单位（如 `180d`、`6`）；同时检查磁盘空间是否先触顶。

**坑 3：集群写入报 storage 不可达**

- 报错原样：`cannot obtain connection to vmstorage ... dial tcp 10.0.0.201:8400: connect: connection refused`。
- 原因：vmstorage 未启动；8400/8401 端口未放通；storageNode 地址写错。
- 解决：先确保所有 vmstorage 健康；放通端口；核对 storageNode 列表。

**坑 4：副本数据重复展示**

- 现象：同一条数据在 Grafana 出现两份。
- 原因：replicationFactor>1 但 vmselect 没开去重。
- 解决：vmselect 加 `-dedup.minScrapeInterval`（如 1ms 或与抓取间隔一致）。

**坑 5：改了 vmstorage 数量后数据错乱/缺失**

- 现象：扩缩容 storage 后部分序列查不到。
- 原因：vminsert/vmselect 的 storageNode 列表没同步更新。
- 解决：所有 insert/select 同步更新并重启；集群扩缩容按官方文档的分片再平衡流程操作。

**坑 6：下载了 enterprise 版本启动报授权错误**

- 报错原样：启动提示 license required / enterprise feature。
- 原因：误下企业版。
- 解决：下载不带 enterprise 后缀的开源版（victoria-metrics / -cluster 包）。

**坑 7：远程写入后 VM 里没数据**

- 现象：remote_write 配了但 vmui 查不到。
- 原因：URL 路径错（单机用 /api/v1/write，集群用 /insert/0/prometheus）；网络不通。
- 解决：核对端点路径；在 Prometheus 服务器 curl VM 地址验证连通；看 Prometheus 日志 remote_write 报错。

---
