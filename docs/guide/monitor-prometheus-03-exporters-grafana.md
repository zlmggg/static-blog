---
category: 监控
difficulty: 初级
---

# Prometheus 实战 03：主机采集、Grafana 与 Pushgateway

> **Prometheus 实战系列（共 10 篇）**
> ← 上一篇 [Prometheus 实战 02](./monitor-prometheus-02-server-deploy) ｜ 下一篇 [Prometheus 实战 04](./monitor-prometheus-04-promql-exporter) →
> [返回监控索引](./monitor)

### 2.3 Node Exporter：采集主机指标

Node Exporter 是部署在**每一台被监控机器**上的小程序，专门采集 CPU、内存、磁盘、网络、文件系统等主机层面的指标，监听 9100 端口。

- **类比**：它像给每台机器配的"体检员"，Prometheus 这位"医生"定期来找它要体检报告。
- **为什么需要它**：Prometheus 只会说 HTTP，读不懂内核数据；Node Exporter 负责读 `/proc`、`/sys` 并翻译成 Prometheus 格式。
- **不装会怎样**：不装它，Prometheus 拿不到任何主机指标，Targets 里该目标 DOWN。

以下操作在**每台被监控主机**（web01、app01、db01……）上执行，用户为 root。

#### 2.3.1 二进制安装

**第 1 步：下载解压**

```bash
cd /usr/local
wget https://github.com/prometheus/node_exporter/releases/download/v1.12.1/node_exporter-1.12.1.linux-amd64.tar.gz
tar xf node_exporter-1.12.1.linux-amd64.tar.gz
ln -s node_exporter-1.12.1.linux-amd64 node_exporter
cd node_exporter
mkdir -p bin
mv node_exporter bin/
```

备选（GitHub）：

```text
https://github.com/prometheus/node_exporter/releases/download/v1.12.1/node_exporter-1.12.1.linux-amd64.tar.gz
```

**第 2 步：建用户、授权**

```bash
id prometheus &>/dev/null || useradd -r -s /usr/sbin/nologin prometheus
chown -R prometheus:prometheus /usr/local/node_exporter/
```

`id prometheus &>/dev/null || ...` 的意思是：先查 prometheus 用户是否存在，不存在（`||` 左边失败）才执行后面的创建命令，避免重复建用户报错。

**第 3 步：认识采集器 collector**

Node Exporter 靠一个个 collector 采集不同类数据。启用用 `--collector.<名字>`，禁用用 `--no-collector.<名字>`。查看全部：

```bash
/usr/local/node_exporter/bin/node_exporter --help | grep -E 'collector\.(cpu|meminfo|diskstats|filesystem|netdev)' | head -10
```

默认已启用的主要采集器：

| collector | 采集内容 |
| --- | --- |
| cpu | CPU 使用时间 |
| meminfo | 内存 |
| diskstats | 磁盘 IO |
| filesystem | 文件系统容量 |
| netdev / netclass / netstat | 网卡流量、网络协议栈 |
| loadavg | 系统负载 |
| time / uname / stat | 时间、内核版本等 |
| pressure | PSI 资源压力（CPU/内存/IO 等待） |

**第 4 步：创建服务文件**

```bash
cat > /etc/systemd/system/node_exporter.service <<'EOF'
[Unit]
Description=Prometheus Node Exporter
After=network-online.target

[Service]
Type=simple
User=prometheus
Group=prometheus
ExecStart=/usr/local/node_exporter/bin/node_exporter \
  --web.listen-address=0.0.0.0:9100 \
  --collector.filesystem.mount-points-exclude='^/(dev|proc|run/credentials/.+|sys|var/lib/docker/.+)($|/)'
ExecReload=/bin/kill -HUP $MAINPID
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

参数解释：`--collector.filesystem.mount-points-exclude` 用正则排除虚拟/容器挂载点，避免把 `/proc`、容器内部目录等无意义的文件系统算进磁盘指标。

::: warning
不要随意加 `--no-collector.uname`：禁用 uname 采集器会导致 Grafana 主机看板无法显示该主机的内核、机器信息。
:::

**第 5 步：启动、验证**

```bash
systemctl daemon-reload
systemctl enable --now node_exporter
systemctl is-active node_exporter
ss -lntp | grep 9100
```

预期输出：

```text
active
LISTEN 0 4096 *:9100 *:* users:(("node_exporter",pid=2195,fd=3))
```

本机抓一把指标验证：

```bash
curl -s http://localhost:9100/metrics | grep -E 'node_cpu_seconds_total|node_memory_MemTotal_bytes' | head -5
```

预期输出（数值不同正常）：

```text
# HELP node_cpu_seconds_total Seconds the CPUs spent in each mode.
# TYPE node_cpu_seconds_total counter
node_cpu_seconds_total{cpu="0",mode="idle"} 12345.67
# HELP node_memory_MemTotal_bytes Memory information field MemTotal_bytes.
node_memory_MemTotal_bytes 4.14e+09
```

浏览器访问 `http://【被监控主机IP】:9100/metrics` 能看到整页指标即成功。记得放通 9100 端口（ufw/防火墙/安全组）。

#### 2.3.2 容器方式安装 Node Exporter

官方推荐的容器启动（用主机网络和 PID 命名空间，才能读到宿主机真实数据）：

```bash
docker run -d \
  --name node_exporter \
  --restart=always \
  --net="host" \
  --pid="host" \
  -v "/:/host:ro,rslave" \
  prom/node-exporter:v1.12.1 \
  --path.rootfs=/host
```

参数解释：`--net="host"` 直接用宿主机网络（9100 直接在宿主机监听）；`--pid="host"` 共享宿主机进程视图；`-v "/:/host:ro,rslave"` 把宿主机根目录只读挂进容器，`rslave` 保证后续新挂载能同步看到。

Docker Compose 写法（桥接网络版）：

```yaml
services:
  node-exporter:
    image: prom/node-exporter:v1.12.1
    container_name: node-exporter
    restart: always
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--path.rootfs=/host'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
```

::: tip
YAML 里写 `$` 要写成 `$$`（Compose 会把 `$$` 转义成一个 `$`），所以正则里的 `($|/)` 在 compose 文件里写成 `($$|/)`。
:::

#### 2.3.3 Kubernetes 中以 DaemonSet 安装

DaemonSet（守护进程集）能在每个节点上自动跑一个 Pod，正适合 Node Exporter。完整 K8s 概念阶段十一细讲，这里先给出可用清单。

`node-exporter-ds.yaml`：

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: prometheus-node-exporter
  namespace: monitoring
  labels:
    app: prometheus
    component: node-exporter
spec:
  selector:
    matchLabels:
      app: prometheus
      component: node-exporter
  template:
    metadata:
      labels:
        app: prometheus
        component: node-exporter
    spec:
      hostNetwork: true
      hostPID: true
      tolerations:
        - effect: NoSchedule
          key: node-role.kubernetes.io/control-plane
          operator: Exists
      volumes:
        - name: proc
          hostPath:
            path: /proc
        - name: sys
          hostPath:
            path: /sys
        - name: rootfs
          hostPath:
            path: /
      containers:
        - image: prom/node-exporter:v1.12.1
          name: prometheus-node-exporter
          args:
            - --path.procfs=/host/proc
            - --path.sysfs=/host/sys
            - --path.rootfs=/host
          ports:
            - name: metrics
              containerPort: 9100
              hostPort: 9100
          volumeMounts:
            - mountPath: /host/proc
              name: proc
            - mountPath: /host/sys
              name: sys
            - mountPath: /host
              name: rootfs
          livenessProbe:
            tcpSocket:
              port: 9100
            initialDelaySeconds: 5
          readinessProbe:
            httpGet:
              path: /metrics
              port: 9100
            initialDelaySeconds: 5
```

参数解释：`tolerations` 是"容忍"——默认 Pod 不调度到控制平面节点，这里声明容忍该污点，让 Node Exporter 也能在控制节点采集；`livenessProbe`/`readinessProbe` 是存活/就绪健康检查（生产必配）。

再配一个无头 Service 便于 Prometheus 发现：

```yaml
apiVersion: v1
kind: Service
metadata:
  name: prometheus-node-exporter
  namespace: monitoring
  labels:
    app: prometheus
    component: node-exporter
spec:
  clusterIP: None
  selector:
    app: prometheus
    component: node-exporter
  ports:
    - name: metrics
      port: 9100
      targetPort: 9100
      protocol: TCP
```

应用：

```bash
kubectl create namespace monitoring
kubectl apply -f node-exporter-ds.yaml
kubectl -n monitoring get pod -o wide
```

预期输出：每个节点一个 `prometheus-node-exporter` Pod，状态 `Running 1/1`。

#### 2.3.4 Node Exporter 常用指标速览

| 指标前缀 | 含义 |
| --- | --- |
| `node_boot_time_seconds` | 系统启动时刻（1970 年以来秒数） |
| `node_cpu_seconds_total` | CPU 各模式（idle/system/user/iowait 等）累计秒数 |
| `node_disk_*` | 磁盘 IO（读写次数、字节、耗时） |
| `node_filesystem_*` | 文件系统总量、可用量 |
| `node_load1 / load5 / load15` | 1/5/15 分钟平均负载 |
| `node_memory_*` | 内存总量、可用、缓存、swap |
| `node_network_*` | 网卡收发字节、包数、错误、丢包 |
| `node_time_seconds` | 当前系统时间 |
| `go_*` / `process_*` | exporter 自身 Go 运行时、进程指标 |

---

### 2.4 Prometheus 采集 Node Exporter

回到**监控服务器 monitor**，把三台业务主机加进 Prometheus。

**第 1 步：编辑配置**

用 vim 打开 `/usr/local/prometheus/conf/prometheus.yml`，在 `scrape_configs` 段已有 job 之后追加：

```yaml
  - job_name: 'node_exporter'
    metrics_path: /metrics
    scheme: http
    static_configs:
      - targets:
          - '【Web服务器IP】:9100'
          - '【应用服务器IP】:9100'
          - '【数据库服务器IP】:9100'
        labels:
          env: 'prod'
```

完整有效配置检查：

```bash
grep -Ev '^ *#|^$' /usr/local/prometheus/conf/prometheus.yml
```

**第 2 步：检查语法、生效**

```bash
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus
```

预期输出：

```text
Checking /usr/local/prometheus/conf/prometheus.yml
  SUCCESS: /usr/local/prometheus/conf/prometheus.yml is valid prometheus config file syntax
```

**第 3 步：在界面验证**

浏览器打开：

```text
http://【监控服务器IP】:9090/targets
```

预期结果：出现 `node_exporter` 分组，下面三个 Endpoint，State 全为 **UP**。鼠标放到 Labels 上能看到 `__meta`/`__address__` 等内部标签（`__` 开头是系统保留标签）；点 Endpoint 链接可直接跳到该主机的 metrics 页面。

如果是 DOWN，点 Endpoint 前的报错提示，按本阶段末尾"常见坑"排查（90% 是端口没放通或服务没起）。

---

### 2.5 Grafana：把数据画成大屏

Grafana 是开源的可视化套件，支持 Prometheus、MySQL、ES 等几十种数据源，提供海量现成看板模板，默认监听 3000 端口。

- **类比**：Prometheus 是埋头记账的会计，Grafana 是把账本画成图表大屏的"美工"。
- **为什么需要它**：Prometheus 自带界面不能保存图表、不好看；Grafana 能做仪表盘、大屏、权限、共享。
- **不装会怎样**：只能在 Prometheus 里临时查，没有可长期使用的监控大屏。

#### 2.5.1 安装 Grafana

在**监控服务器 monitor** 上执行，用户 root。

**方式一：官方包安装（推荐，地址国内可访问）**

```bash
cd /usr/local/src
wget https://dl.grafana.com/oss/release/grafana_13.2.2_amd64.deb
apt -y install ./grafana_13.2.2_amd64.deb
```

参数解释：`install ./文件名.deb` 会自动解决依赖（比 `dpkg -i` 更省心，本地文件路径前的 `./` 不能省）。这是开源版（OSS）安装包。

**备选：清华镜像站**（官方地址慢时用，包名带构建时间戳）：

```bash
wget https://mirrors.tuna.tsinghua.edu.cn/grafana/apt/pool/main/g/grafana/grafana_13.2.2_34846740809_linux_amd64.deb
apt -y install ./grafana_13.2.2_34846740809_linux_amd64.deb
```

启动并设开机自启：

```bash
systemctl daemon-reload
systemctl enable --now grafana-server
systemctl is-active grafana-server
ss -lntp | grep 3000
```

预期输出：

```text
active
LISTEN 0 4096 *:3000 *:* users:(("grafana-server",pid=35383,fd=8))
```

**RHEL 系**：下载 `.rpm` 包（`https://dl.grafana.com/oss/release/grafana-13.2.2-1.x86_64.rpm`），用 `yum -y localinstall 包名` 安装，服务名同样是 `grafana-server`。

**方式二：Docker 安装**

```bash
docker run -d \
  --name grafana \
  --restart=always \
  -p 3000:3000 \
  -v grafana_data:/var/lib/grafana \
  grafana/grafana:13.2.2
```

参数解释：Grafana 数据（数据源、看板、用户）存在容器内 `/var/lib/grafana`，用命名卷持久化。

#### 2.5.2 首次登录

浏览器访问：

```text
http://【监控服务器IP】:3000
```

第 1 步：输入初始用户名 `admin`、初始密码 `admin`，点 **Log in**；
第 2 步：进入修改密码页，输入新密码并确认（学习图省事也可继续用 admin，点 Submit；**生产必须改成强密码**）；
第 3 步：进入 Grafana 首页。

#### 2.5.3 添加 Prometheus 数据源

第 1 步：点首页的 **Add your first data source**（或左侧菜单 Connections / Data sources → Add data source）；
第 2 步：在数据源列表里选 **Prometheus**；
第 3 步：在 Settings 页填写：

| 配置项 | 填什么 |
| --- | --- |
| Prometheus server URL | `http://【监控服务器IP】:9090`（Grafana 和 Prometheus 同机也可填 `http://localhost:9090`，但容器版 Grafana 的 localhost 指容器自身，要用宿主机 IP） |
| 其他项 | 全部保持默认 |

第 4 步：拉到最下面点 **Save & test**；
预期结果：出现绿色提示 `Successfully queried the Prometheus API.`。如果报 `Error reading Prometheus`，检查 URL、Prometheus 是否在跑、端口是否放通。

#### 2.5.4 导入主机看板模板

Grafana 社区有大量现成模板，模板用数字 ID 标识，模板市场地址：

```text
https://grafana.com/grafana/dashboards/
```

第 1 步：左侧菜单 **Dashboards → New → Import**；
第 2 步：在 "Import via grafana.com" 输入框填模板 ID，点 **Load**；
第 3 步：选择数据源为刚才添加的 Prometheus，点 **Import**。

推荐模板（都可直接导入）：

| 模板 ID | 说明 |
| --- | --- |
| **1860** | Node Exporter 经典主机看板（英文，最常用） |
| **8919** | Node Exporter 中文主机看板 |
| 11074 | Node Exporter 精简看板 |
| 13978 | Node Exporter 现代看板 |

预期结果：导入后立刻看到 CPU、内存、磁盘、网络的实时图表。

::: warning
导入看板时注意三点：① 模板 ID 要和 exporter 版本匹配，版本差太多会有面板 `No data`；② 一定要选对 Prometheus 数据源；③ Grafana 时间和服务器时间误差超过几秒也可能不显示数据，确保时间同步已配置。
:::

#### 2.5.5 把 Grafana 自身纳入监控

Grafana 内置了 `/metrics` 指标接口。在 Prometheus 配置里追加一个 job：

```yaml
  - job_name: 'grafana'
    static_configs:
      - targets: ['【监控服务器IP】:3000']
```

检查生效：

```bash
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus
```

在 Grafana 添加数据源时的 **Dashboards** 标签页可导入内置的 Grafana 指标看板（Grafana metrics），即可查看 Grafana 自身的请求量、耗时、在线用户等状态。

---

### 2.6 监控 Zookeeper（内置指标）

有些软件自带 Prometheus 指标功能（称为内置仪表 Instrumentation），Zookeeper 从 3.6 起内置了 Prometheus Metrics Provider，不用额外装 exporter。

**第 1 步：开启内置 Prometheus 指标**

配置文件路径：`/usr/local/zookeeper/conf/zoo.cfg`（以实际安装路径为准），在文件末尾加入（默认配置里有这几行的注释，取消注释即可）：

```properties
metricsProvider.className=org.apache.zookeeper.metrics.prometheus.PrometheusMetricsProvider
metricsProvider.httpHost=0.0.0.0
metricsProvider.httpPort=7000
metricsProvider.exportJvmInfo=true
```

参数解释：`httpHost=0.0.0.0` 监听所有网卡；`httpPort=7000` 指标端口；`exportJvmInfo=true` 同时输出 JVM 指标。

重启：

```bash
systemctl restart zookeeper
ss -lntp | grep 7000
curl -s http://localhost:7000/metrics | head -5
```

**第 2 步：Prometheus 加 job**

```yaml
  - job_name: 'zookeeper'
    static_configs:
      - targets: ['【Zookeeper服务器IP】:7000']
```

```bash
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus
```

**第 3 步：Grafana 导入看板**

模板市场搜索 zookeeper，导入 ID **10465**（导入步骤同 2.5.4，注意选对数据源/集群名），即可看到 Zookeeper 监控图。

---
### 2.7 Pushgateway：采集短任务自定义指标

Pushgateway 是一个"指标暂存柜"：短生命周期的脚本/任务在退出前把指标**推**给它，Prometheus 再从它那里**拉**。

- **类比**：像快递柜——你（短任务）下班早，怕快递员（Prometheus）上门没人，就把包裹先放进快递柜，快递员按柜子编号统一取。
- **为什么需要它**：批处理、定时任务可能在 Prometheus 两次抓取之间就结束了，Pull 模式抓不到。
- **不学会卡在哪**：企业里"每日报表脚本跑没跑成功""数据同步任务处理了多少条"这类需求，没有它做不了。

数据流向：

![Pushgateway 数据流向](/guide/diagrams/pushgateway-flow.svg)

#### 2.7.1 适用场景与缺点

**适用场景**：

1. 批处理/定时任务：每日报表、数据同步、定时清理脚本；
2. 极短生命周期任务：CI/CD 临时容器、Serverless 函数；
3. 无法暴露 HTTP 端点的隔离环境；
4. 老旧/闭源应用，用外部脚本取数后推送；
5. 作为多个任务指标的统一聚合入口。

**缺点（生产须知）**：

- Pushgateway 是单点，挂了则所有推送数据丢失（可部署多实例）；
- **失去 up 自动存活监控**：推送方机器宕机，Pushgateway 仍保留旧值，不会自动变 0；
- 指标会一直保留到被覆盖或手动删除，容易产生过期数据；
- 它不做数据校验，脚本采错了也照单全收。

::: warning
再次强调：**主机指标绝不用 Pushgateway**，只用 Node Exporter；Pushgateway 只接收短任务、批处理指标。
:::

#### 2.7.2 二进制安装 Pushgateway

在**监控服务器 monitor** 上执行，用户 root。

**第 1 步：下载解压**

```bash
cd /usr/local
wget https://github.com/prometheus/pushgateway/releases/download/v1.11.3/pushgateway-1.11.3.linux-amd64.tar.gz
tar xf pushgateway-1.11.3.linux-amd64.tar.gz
ln -s pushgateway-1.11.3.linux-amd64 pushgateway
cd pushgateway
mkdir -p bin
mv pushgateway bin/
chown -R prometheus:prometheus /usr/local/pushgateway/
```

备选（GitHub）：

```text
https://github.com/prometheus/pushgateway/releases/download/v1.11.3/pushgateway-1.11.3.linux-amd64.tar.gz
```

**第 2 步：创建服务文件（含持久化）**

```bash
cat > /etc/systemd/system/pushgateway.service <<'EOF'
[Unit]
Description=Prometheus Pushgateway
After=network-online.target

[Service]
Type=simple
User=prometheus
Group=prometheus
ExecStart=/usr/local/pushgateway/bin/pushgateway \
  --web.listen-address=0.0.0.0:9091 \
  --persistence.file=/usr/local/pushgateway/data/persistence \
  --persistence.interval=5m
ExecReload=/bin/kill -HUP $MAINPID
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
mkdir -p /usr/local/pushgateway/data
chown -R prometheus:prometheus /usr/local/pushgateway/data
```

参数解释：`--persistence.file` 指定持久化文件，重启后推送的指标不丢（留空则只存内存）；`--persistence.interval=5m` 至少每 5 分钟写一次盘。

**第 3 步：启动、验证**

```bash
systemctl daemon-reload
systemctl enable --now pushgateway
systemctl is-active pushgateway
ss -lntp | grep 9091
```

预期输出：

```text
active
LISTEN 0 4096 *:9091 *:* users:(("pushgateway",pid=3001,fd=7))
```

浏览器访问 `http://【监控服务器IP】:9091` 能看到 Pushgateway 页面（此时还没有指标）。

Docker 安装（备选）：

```bash
docker run -d --name pushgateway --restart=always -p 9091:9091 prom/pushgateway:v1.11.3
```

#### 2.7.3 配置 Prometheus 采集 Pushgateway

在 Prometheus 配置中追加：

```yaml
  - job_name: 'pushgateway'
    honor_labels: true
    scrape_interval: 10s
    static_configs:
      - targets: ['【监控服务器IP】:9091']
```

参数解释：**`honor_labels: true` 很关键**——推送方已经在数据里带了 `job`、`instance` 标签，设为 true 时 Prometheus 尊重并保留这些原始标签；设为 false（默认）时，Prometheus 会把原始标签改名为 `exported_job`、`exported_instance`，再用自己的 job/instance 覆盖。采集 Pushgateway 一般设 true。

检查生效：

```bash
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus
```

也支持文件服务发现写法（阶段六细讲）：

```yaml
  - job_name: pushgateway
    honor_labels: true
    file_sd_configs:
      - files:
          - targets/pushgateway/*.json
        refresh_interval: 5m
```

对应目标文件 `/usr/local/prometheus/conf/targets/pushgateway/test.json`：

```json
[
  {
    "targets": ["【监控服务器IP】:9091"]
  }
]
```

#### 2.7.4 客户端推送数据

**推送 URL 格式**：

```text
http://【Pushgateway地址】:9091/metrics/job/<job名>/[<标签名>/<标签值>/]...
```

URL 路径里的 `job/<job名>` 必填；后面可以跟任意组标签（如 `instance/<实例名>`），它们会成为指标的标签。

**示例 1：推送单个指标**

在任意一台业务机器上执行（普通用户即可，能联网到 Pushgateway 就行）：

```bash
echo "some_metric 3.14" | curl --data-binary @- http://【监控服务器IP】:9091/metrics/job/some_job
```

参数解释：`echo "指标名 值"` 生成一行 Prometheus 文本；`|` 管道把它交给 curl；`--data-binary @-` 表示把标准输入（`@-`）原样作为请求体发送。没提供类型时该指标为 untyped。

**示例 2：推送带类型、标签的多条指标**

```bash
cat <<'EOF' | curl --data-binary @- http://【监控服务器IP】:9091/metrics/job/some_job/instance/some_instance
# TYPE some_metric counter
some_metric{label="val1"} 42
# TYPE another_metric gauge
# HELP another_metric Just an example.
another_metric 2398.283
EOF
```

参数解释：`cat <<'EOF' ... EOF` 是一次性生成多行文本（EOF 加引号可避免内部符号被转义）；`# TYPE` 声明类型、`# HELP` 写说明，虽可省但建议写。

**示例 3：用主机 IP 作为 instance 推送**

```bash
echo "age 18" | curl --data-binary @- http://【监控服务器IP】:9091/metrics/job/pushgateway/instance/$(hostname -I | awk '{print $1}')
```

参数解释：`$(命令)` 会先执行里面的命令并替换为结果；`hostname -I` 取本机所有 IP，`awk '{print $1}'` 取第一个。

**删除指标**：

```bash
# 删除某 job 下某 instance 的全部指标
curl -X DELETE http://【监控服务器IP】:9091/metrics/job/some_job/instance/some_instance

# 删除某 job 下全部指标（注意：不含显式指定 instance 的分组）
curl -X DELETE http://【监控服务器IP】:9091/metrics/job/some_job
```

也可以在 Pushgateway 网页上点 **Delete Group** 删除。清空所有指标需要启动时加 `--web.enable-admin-api`，再调用：

```bash
curl -X PUT http://【监控服务器IP】:9091/api/v1/admin/wipe
```

#### 2.7.5 通用推送脚本与定时执行

下面脚本把"当前登录用户数"作为指标周期推送，可按需改成任意指标。

创建脚本 `/usr/local/bin/pushgateway_metric.sh`：

```bash
cat > /usr/local/bin/pushgateway_metric.sh <<'EOF'
#!/bin/bash
METRIC_NAME=login_number
METRIC_VALUE_CMD="who | wc -l"
METRIC_TYPE=gauge
METRIC_HELP="login user number"

PUSHGATEWAY_HOST=【监控服务器IP】:9091
EXPORTED_JOB=pushgateway_job
INSTANCE=$(hostname -I | awk '{print $1}')
SLEEP_TIME=10

push_metric() {
  while true; do
    VALUE=$(eval "$METRIC_VALUE_CMD")
    cat <<INNER | curl --data-binary @- http://${PUSHGATEWAY_HOST}/metrics/job/${EXPORTED_JOB}/instance/${INSTANCE}
# HELP ${METRIC_NAME} ${METRIC_HELP}
# TYPE ${METRIC_NAME} ${METRIC_TYPE}
${METRIC_NAME} ${VALUE}
INNER
    sleep $SLEEP_TIME
  done
}

push_metric
EOF
chmod +x /usr/local/bin/pushgateway_metric.sh
bash /usr/local/bin/pushgateway_metric.sh
```

参数解释：`chmod +x` 加可执行权限；脚本里 while 循环每 10 秒推一次；`eval "$METRIC_VALUE_CMD"` 执行取数命令。按 `Ctrl+C` 停止。

生产中更推荐**让任务自己在结束时推一次**，并配合计划任务。例如每日凌晨统计脚本执行完后推送结果；或用 crontab 周期推送，编辑计划任务：

```bash
crontab -e
```

加入一行（每 5 分钟推一次登录用户数）：

```cron
*/5 * * * * echo "login_number $(who | wc -l)" | curl --data-binary @- http://【监控服务器IP】:9091/metrics/job/login_check/instance/$(hostname -I | awk '{print $1}')
```

#### 2.7.6 验证数据

第 1 步：浏览器打开 Pushgateway 页面 `http://【监控服务器IP】:9091`，能看到推送的指标分组和值；
第 2 步：Prometheus 侧 `http://【监控服务器IP】:9090/targets` 中 pushgateway 为 UP；
第 3 步：在 Prometheus Graph 或 Grafana 里查询 `some_metric`、`login_number` 能看到值，即整条链路打通。

---

### 本阶段命令速查表

```bash
# === 系统初始化（root）===
apt update && apt -y install wget curl tar vim lsof chrony
timedatectl set-timezone Asia/Shanghai
systemctl enable --now chrony

# === Prometheus 二进制 ===
cd /usr/local
wget https://github.com/prometheus/prometheus/releases/download/v3.15.0/prometheus-3.15.0.linux-amd64.tar.gz
tar xf prometheus-3.15.0.linux-amd64.tar.gz
ln -s prometheus-3.15.0.linux-amd64 prometheus
cd prometheus && mkdir -p bin conf data
mv prometheus promtool bin/ && mv prometheus.yml conf/
useradd -r -s /usr/sbin/nologin prometheus
chown -R prometheus:prometheus /usr/local/prometheus/
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl daemon-reload && systemctl enable --now prometheus

# === Node Exporter（每台被监控机）===
cd /usr/local
wget https://github.com/prometheus/node_exporter/releases/download/v1.12.1/node_exporter-1.12.1.linux-amd64.tar.gz
tar xf node_exporter-1.12.1.linux-amd64.tar.gz
ln -s node_exporter-1.12.1.linux-amd64 node_exporter
# 服务文件见 2.3，然后：
systemctl daemon-reload && systemctl enable --now node_exporter

# === Grafana ===
cd /usr/local/src
wget https://dl.grafana.com/oss/release/grafana_13.2.2_amd64.deb
apt -y install ./grafana_13.2.2_amd64.deb
systemctl enable --now grafana-server

# === Pushgateway ===
cd /usr/local
wget https://github.com/prometheus/pushgateway/releases/download/v1.11.3/pushgateway-1.11.3.linux-amd64.tar.gz
tar xf pushgateway-1.11.3.linux-amd64.tar.gz
ln -s pushgateway-1.11.3.linux-amd64 pushgateway
# 服务文件见 2.7，然后：
systemctl daemon-reload && systemctl enable --now pushgateway

# === 每次改配置固定两步 ===
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus

# === 推送 / 删除指标 ===
echo "some_metric 3.14" | curl --data-binary @- http://【监控服务器IP】:9091/metrics/job/some_job
curl -X DELETE http://【监控服务器IP】:9091/metrics/job/some_job
```

---

### 本阶段常见坑与解决

**坑 1：命令不存在（command not found）**

- 新手做法：照着敲 `wget`、`tar`、`ss`，系统提示找不到。
- 报错原样：`bash: wget: command not found`。
- 根本原因：最小化安装的镜像不带这些工具。
- 解决：

```bash
apt -y install wget curl tar iproute2
```

RHEL 系：`yum -y install wget curl tar iproute`。
- 预防：初始化时先执行 2.0.2 的工具安装。

**坑 2：权限不足（Permission denied）**

- 报错原样：`mkdir: cannot create directory '/usr/local/xxx': Permission denied`；或服务写数据时报 `open data/xxx: permission denied`。
- 根本原因：普通用户无权写系统目录；或服务用户对数据目录没有属主权限。
- 解决：系统级操作切 root（`sudo -i`）；目录授权：

```bash
chown -R prometheus:prometheus /usr/local/prometheus/
```

- 预防：先想清楚"这条命令该用谁执行"，服务目录安装后立即 chown。

**坑 3：端口被占用（Address already in use）**

- 报错原样：`listen tcp 0.0.0.0:9090: bind: address already in use`。
- 根本原因：已有进程占用该端口（常见于 apt 装过又装二进制、容器和宿主重复）。
- 解决：

```bash
ss -lntp | grep 9090
# 查到 PID 后停掉旧进程：
systemctl stop prometheus
# 或停掉旧容器：
docker rm -f prometheus
```

- 预防：同一台机器上一种方式只装一套；先查端口再启动。

**坑 4：YAML 配置语法错误**

- 报错原样：`yaml: unmarshal errors: cannot unmarshal ... ` 或 `parsing YAML file prometheus.yml: yaml: line 12: did not find expected '-' indicator`。
- 根本原因：Tab 缩进、缩进层级不对、冒号后没空格。
- 解决：用 `promtool check config 路径` 定位行号，改空格缩进（推荐 2 空格），通过后再 reload。
- 预防：编辑器开启"显示空白字符"，只复制手册里完整配置块。

**坑 5：空目录挂载覆盖了容器内默认配置**

- 新手做法：`-v /opt/prometheus:/etc/prometheus` 挂载一个空目录。
- 现象：容器启动即退出，日志报 `Error: unable to load config file: open /etc/prometheus/prometheus.yml: no such file`。
- 根本原因：绑定挂载会用宿主机目录**整体覆盖**容器内目录，空目录把默认配置盖没了。
- 解决：先在宿主机目录放好 `prometheus.yml`，或先 `docker cp` 拷出默认配置；只挂单个文件也行：`-v /etc/prometheus.yml:/etc/prometheus/prometheus.yml`。
- 预防：挂载前确认宿主机源路径里有内容。

**坑 6：容器启动后立刻退出（Exited）**

- 报错/现象：`docker ps -a` 显示 Exited (1)，`docker logs prometheus` 有配置/路径错误。
- 根本原因：配置文件不存在、参数写错、数据目录权限不对。
- 解决：`docker logs --tail 50 prometheus` 看具体原因，按对应坑修复后 `docker rm -f prometheus` 重新 run。
- 预防：启动命令里加 `--restart=always`，但**更要先排掉根因**，否则会反复重启。

**坑 7：国内源/加速器配错**

- 报错原样：`Cannot initiate the connection to mirrors.xxx:80 ... Connection timed out`；拉镜像 `Error response from daemon: Get ...: net/http: TLS handshake timeout`。
- 根本原因：源地址写错、加速器失效。
- 解决：apt 源用手册里的阿里云/清华地址；daemon.json 里删掉失效加速器、保留可用的，`systemctl restart docker`。
- 预防：安装包优先从 GitHub Releases 下载（慢则加 ghproxy 代理前缀）；容器加速器多配两个做备份。

**坑 8：安全组/防火墙没放端口**

- 报错原样：浏览器 `10.0.0.10 拒绝了连接请求`；本地 curl 正常、外部不行。
- 根本原因：ufw/firewalld/云安全组未放行。
- 解决：

```bash
ufw allow 9090/tcp        # Ubuntu
firewall-cmd --add-port=9090/tcp --permanent && firewall-cmd --reload   # RHEL
```

云服务器再到控制台安全组加规则。
- 预防：按 2.0.4 端口表一次性放齐。

**坑 9：服务只监听 127.0.0.1**

- 报错/现象：`ss -lntp` 显示 `127.0.0.1:9090`，外部访问被拒。
- 根本原因：监听地址绑了回环地址，只接受本机连接。
- 解决：启动参数显式加 `--web.listen-address=0.0.0.0:9090`，重启服务。
- 预防：所有需要外部访问的服务都监听 `0.0.0.0`。

**坑 10：日志撑爆磁盘**

- 现象：磁盘 100%、服务异常；容器 json 日志无限增长。
- 根本原因：没配日志轮转。
- 解决：daemon.json 配置 `log-opts`（[见第 2 篇 2.1.6](./monitor-prometheus-02-server-deploy)）；已撑大先清：

```bash
sh -c 'truncate -s 0 /var/lib/docker/containers/*/*-json.log'
```

- 预防：部署 Docker 时就配好单文件大小与份数。

**坑 11：时间不同步导致图不显示/告警延迟**

- 现象：Grafana 面板 No data，机器时间与实际差几分钟以上。
- 解决：

```bash
timedatectl set-timezone Asia/Shanghai
systemctl enable --now chrony
```

- 预防：把时间同步纳入主机初始化必做项。

**坑 12：中文乱码**

- 现象：页面、输出中文显示为问号或方块。
- 根本原因：未设置 UTF-8 字符集。
- 解决：

```bash
apt -y install locales
locale-gen en_US.UTF-8 zh_CN.UTF-8
export LANG=en_US.UTF-8
```

- 预防：系统初始化时安装 UTF-8 locale。

**坑 13：honor_labels 没开，标签变成 exported_ 前缀**

- 现象：推送的指标上 `job` 标签变成了 `pushgateway`，原始 job 变成 `exported_job`，查询对不上。
- 根本原因：默认 honor_labels=false，Prometheus 用自己的标签覆盖。
- 解决：pushgateway 的 job 配置加 `honor_labels: true`，reload。
- 预防：记住采集 Pushgateway 必开此项。

**坑 14：Pushgateway 旧数据误导**

- 现象：任务早已失败/下线，Grafana 仍显示最后一次推的值。
- 根本原因：Pushgateway 不自动删数据。
- 解决：任务逻辑里失败时推 0/异常状态，或结束时主动 DELETE 对应分组；定期清理。
- 预防：推送脚本设计好"过期与删除"逻辑，别只推一次就不管。

---
