---
category: 监控
difficulty: 中级
---

# Prometheus 实战 05：标签、记录规则与 Alertmanager

> **Prometheus 实战系列（共 10 篇）**
> ← 上一篇 [Prometheus 实战 04](./monitor-prometheus-04-promql-exporter) ｜ 下一篇 [Prometheus 实战 06](./monitor-prometheus-06-alert-notification-ha) →
> [返回监控索引](./monitor)

## 阶段四：标签管理

### 阶段目标

- 分清默认标签、应用标签、自定义标签，以及 `__` 私有标签的作用；
- 理解指标从"被发现"到"入库"的完整生命周期；
- 说清 `relabel_configs` 与 `metric_relabel_configs` 的本质区别；
- 熟练使用 replace、keep、drop、labelmap、labeldrop、hashmod 等动作完成过滤目标、删除指标、改写标签。

---

### 4.1 标签简介

标签的核心功能是**对数据分组和分类、过滤筛选**。常见管理场景：

1. 删除不必要的指标；
2. 从指标中删除敏感或不需要的标签；
3. 添加、编辑、修改标签值或标签格式。

标签按来源分三类：

| 分类 | 来源 | 形式 | 例子 |
| --- | --- | --- | --- |
| 默认标签 | Prometheus 内置 | `__keyname__` | `__address__`、`__scheme__` |
| 应用标签 | 被监控应用内置 | `keyname` | Node Exporter 的 `cpu`、`mode` |
| 自定义标签 | 用户自己定义 | `keyname` | static_configs 里 labels 写的 `env` |

#### 4.1.1 添加自定义标签

在 job 的 `static_configs` 里用 `labels` 给整组目标附加标签：

```yaml
scrape_configs:
  - job_name: 'node_exporter'
    static_configs:
      - targets: ['【Web服务器IP】:9100', '【应用服务器IP】:9100', '【数据库服务器IP】:9100']
        labels:
          node: "worker node"
          type: "test"
  - job_name: 'zookeeper'
    static_configs:
      - targets: ['【应用服务器IP】:7000']
        labels: {app: 'zookeeper', type: 'dev'}
```

YAML 中标签既可以写成缩进的字典格式，也可以写成一行 `{键: '值'}`，两种都合法。改完 `promtool check config` + `systemctl reload prometheus`，在 Targets 页能看到新标签。

---

### 4.2 指标的生命周期

#### 4.2.1 私有标签

私有标签以 `__` 开头，承载监控目标的默认元数据：

| 私有标签 | 含义 |
| --- | --- |
| `__address__` | 目标地址 `host:port` |
| `__scheme__` | 请求协议 http/https |
| `__metrics_path__` | 指标 URL 路径，默认 `/metrics` |
| `__param_<name>` | URL 查询参数（如果有） |
| `__meta_*` | 服务发现产生的元数据（不同发现机制各不同） |

#### 4.2.2 Prometheus 数据处理流程

1. 每个 `scrape_interval`，Prometheus 检查要执行的 Job；
2. Job 按"发现配置"生成 target 列表——**服务发现**；
3. 服务发现返回 target 列表，元数据标签都以 `__meta_` 开头；同时设置 `__scheme__`、`__address__`、`__metrics_path__`，URL 参数以 `__param_` 开头；
4. 对发现的每个目标，执行 **relabel_configs（重新标记目标）**：
   - 把元数据标签里的信息附加到指标上；
   - 过滤目标（决定这个 target 采不采）；
5. 执行数据抓取；
6. 抓取来的指标在**保存前**执行 **metric_relabel_configs（重新标记指标）**：
   - 删除不必要的指标；
   - 删除敏感标签；
   - 添加、修改标签；
7. 指标写入 TSDB。

两个默认行为要记住：

- 指标上的 `instance` 标签默认值来自 `__address__`；
- relabel 完成后，所有 `__` 开头的标签都会被**移除**；relabel 过程中需要临时存值，请用 `__tmp` 前缀，避免与内置标签冲突。

---

### 4.3 relabel_configs 与 metric_relabel_configs 的区别

| 区别 | relabel_configs | metric_relabel_configs |
| --- | --- | --- |
| 执行时机 | **抓取之前**，服务发现之后 | **抓取之后、入库之前**（最后一步） |
| 针对对象 | **target 目标本身** | target 上的 **metric 指标** |
| 典型用途 | 过滤目标、改写地址/协议/路径、补充标签 | 删除指标/标签、修改指标标签 |
| drop 的含义 | 整个目标不采（Targets 页直接看不到/不抓） | 只丢弃匹配指标，目标仍在采 |

一句话：**relabel 决定"采谁、怎么采"；metric_relabel 决定"采回来的哪些指标留、怎么改"**。

---

### 4.4 配置字段与动作详解

#### 4.4.1 通用字段

```yaml
scrape_configs:
  - job_name: 'prometheus'
    relabel_configs:
      - source_labels: [标签名, ...]
        separator: ';'          # 把多个 source_labels 的值串联时的分隔符，默认 ;
        regex: '(.*)'           # 对串联后的值做匹配，默认 (.*)
        replacement: '$1'       # 替换值，默认 $1（正则第 1 个捕获组）
        target_label: '标签名'   # replace/hashmod 时写入的目标标签
        action: 'replace'       # 动作，默认 replace
```

| 字段 | 作用 |
| --- | --- |
| `source_labels` | 参与处理的源标签列表 |
| `separator` | 多个源标签值拼接的分隔符 |
| `regex` | 匹配标签值（replace/keep/drop）或标签名（labelmap/labeldrop）的正则 |
| `replacement` | 写入的新值，支持 `$1`、`${1}` 捕获组引用 |
| `target_label` | 被写入/创建的标签名 |
| `action` | 执行的动作 |

#### 4.4.2 动作（action）一览

| action | 作用 |
| --- | --- |
| **replace**（默认） | 源标签值拼接后匹配 regex，用 replacement 给 target_label 赋值；标签不存在则新建 |
| **keep** | 拼接值匹配 regex 才保留，否则丢弃 |
| **drop** | 拼接值匹配 regex 就丢弃，否则保留（与 keep 相反） |
| **hashmod** | 对源标签拼接值做 hash（配合 `modulus` 字段），结果写入 target_label，常用于**分片** |
| **labelmap** | regex 匹配**标签名**，把匹配到的标签复制成 `replacement` 指定的新标签名，**旧标签保留** |
| **labelkeep** | regex 匹配标签名才保留（白名单），其余删除 |
| **labeldrop** | regex 匹配标签名就删除（黑名单） |
| **lowercase / uppercase** | 把源标签拼接值转成小/大写写入 target_label |
| **keepequal / dropequal** | 按源标签与目标标签值是否相等保留/丢弃（高级，少用） |

::: warning
labeldrop/labelkeep 会真的删标签，而**标签是序列唯一性约束**：删标签后若两条序列变得完全相同，系统会出问题。改/加标签会创建新序列。务必想清楚再删。
:::

#### 4.4.3 全局外部标签 external_labels

`global` 段可设置外部标签，用于与外部系统通信（联邦、远程存储、Alertmanager）时附加到序列/告警上：

```yaml
global:
  external_labels:
    cluster: 'chengdu-prod'
    replica: 'prometheus-a'
```

典型用途：双机高可用时用 `replica` 区分两台 Prometheus；多集群联邦/远程存储时用 `cluster` 标识来源集群。

---

### 4.5 标签管理案例

#### 4.5.1 案例 1：生成 endpoint 标签

把协议、地址、路径拼成完整访问端点：

```yaml
scrape_configs:
  - job_name: 'node_exporter'
    static_configs:
      - targets: ['【Web服务器IP】:9100', '【应用服务器IP】:9100', '【数据库服务器IP】:9100']
    relabel_configs:
      - source_labels: [__scheme__, __address__, __metrics_path__]
        regex: '(http|https)(.*)'
        separator: ''
        target_label: 'endpoint'
        replacement: '${1}://${2}'
        action: replace
```

要点：`separator: ''`（空串）让三个标签值无分隔符拼接；正则两个捕获组分别拿到协议和"地址+路径"，replacement 拼成 `http://10.0.0.11:9100/metrics` 写入新标签 endpoint。

#### 4.5.2 案例 2：labelmap 改名 + labeldrop 删旧标签

```yaml
    relabel_configs:
      # 第一步：把 job、app 标签复制成 job_name、app_name，旧标签仍在
      - regex: '(job|app)'
        replacement: '${1}_name'
        action: labelmap
      # 第二步：删除原来的 job、app 标签
      - regex: '(job|app)'
        action: labeldrop
      # 第三步：再把 endpoint 的值复制给新标签 myendpoint
      - source_labels: [endpoint]
        target_label: 'myendpoint'
```

注意规则**按顺序执行**：先 labelmap 复制、再 labeldrop 删旧，顺序反了就复制不到。

#### 4.5.3 案例 3：删除 go 开头的指标

```yaml
scrape_configs:
  - job_name: 'node_exporter'
    static_configs:
      - targets: ['【Web服务器IP】:9100']
    metric_relabel_configs:
      - source_labels: [__name__]
        regex: 'go.*'
        action: drop
```

要点：删**指标**用 `metric_relabel_configs`；`__name__` 代表指标名。reload 后新采集的数据里不再有 `go_*` 指标（已经存进 TSDB 的历史数据不受影响）。

删除 Node Exporter 网络收包指标，完整配置如下（把 regex 换成 `node_network_receive.*`）：

```yaml
scrape_configs:
  - job_name: 'node_exporter'
    static_configs:
      - targets: ['【Web服务器IP】:9100']
    metric_relabel_configs:
      - source_labels: [__name__]
        regex: 'node_network_receive.*'
        action: drop
```

replace 示例（把 id 标签中 `/` 开头的值替换成固定串写入新标签）：

```yaml
    metric_relabel_configs:
      - source_labels: [id]
        regex: '/.*'
        replacement: '123456'
        target_label: 'replace_id'
```

#### 4.5.4 案例 4：Kubernetes endpoints 重新打签

下面是 K8s 动态环境的经典 relabel（完整 K8s 采集见阶段十一）：

```yaml
  - job_name: 'kubernetes-service-endpoints'
    kubernetes_sd_configs:
      - role: endpoints
    relabel_configs:
      # 只采集注解 prometheus.io/scrape: "true" 的服务
      - source_labels: [__meta_kubernetes_service_annotation_prometheus_io_scrape]
        action: keep
        regex: 'true'
      # 注解 prometheus.io/scheme 覆盖协议
      - source_labels: [__meta_kubernetes_service_annotation_prometheus_io_scheme]
        action: replace
        target_label: __scheme__
        regex: '(https?)'
      # 注解 prometheus.io/path 覆盖指标路径
      - source_labels: [__meta_kubernetes_service_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: '(.+)'
      # 注解 prometheus.io/port 覆盖采集端口
      - source_labels: [__address__, __meta_kubernetes_service_annotation_prometheus_io_port]
        action: replace
        target_label: __address__
        regex: '([^:]+)(?::\d+)?;(\d+)'
        replacement: '$1:$2'
      # 把服务的 K8s 原生标签提升为指标标签
      - action: labelmap
        regex: '__meta_kubernetes_service_label_(.+)'
      # 命名空间、服务名固定标签
      - source_labels: [__meta_kubernetes_namespace]
        action: replace
        target_label: 'kubernetes_namespace'
      - source_labels: [__meta_kubernetes_service_name]
        action: replace
        target_label: 'kubernetes_name'
```

这套注解（`prometheus.io/scrape|scheme|path|port`）是 K8s 服务暴露指标的通用约定，阶段十一还会用到。

#### 4.5.5 案例 5：Consul 发现目标后的 relabel

```yaml
  - job_name: 'consul'
    honor_labels: true
    consul_sd_configs:
      - server: '【Consul服务器IP】:8500'
        services: []
    relabel_configs:
      - source_labels: [__meta_consul_service]
        target_label: 'consul_service'
      - source_labels: [__meta_consul_dc]
        target_label: 'datacenter'
      - source_labels: [__meta_consul_tags]
        target_label: 'app'
      # Consul 自身服务没有 metrics，丢弃
      - source_labels: [__meta_consul_service]
        regex: 'consul'
        action: drop
```

Consul 服务发现的完整内容见阶段六。

---

### 本阶段命令速查表

```bash
# 编辑配置
vim /usr/local/prometheus/conf/prometheus.yml

# 固定两步：检查 + 生效
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus

# 命令行验证某标签/指标是否还在
curl -s http://【监控服务器IP】:9090/metrics | grep -c 'go_'
curl -s http://【Web服务器IP】:9100/metrics | grep node_load1
```

**常用 relabel 片段速记**：

```yaml
# 只采指定目标（relabel，抓取前）
relabel_configs:
  - source_labels: [__address__]
    regex: '10\.0\.0\.(11|12):9100'
    action: keep

# 丢弃指定指标（metric_relabel，入库前）
metric_relabel_configs:
  - source_labels: [__name__]
    regex: 'go_.*'
    action: drop

# 分片：对地址 hash 后取模（两台 Prometheus 各采一半）
relabel_configs:
  - source_labels: [__address__]
    modulus: 2
    target_label: __tmp_hash
    action: hashmod
  - source_labels: [__tmp_hash]
    regex: '0'        # 第二台写 1
    action: keep
```

---

### 本阶段常见坑与解决

**坑 1：把 relabel_configs 当 metric_relabel_configs 用**

- 现象：想删某个指标，写在 relabel_configs 里，结果要么不生效、要么整个目标消失。
- 原因：relabel 作用于 target、在抓取前，此时还没有指标可删；`__name__` 也尚未确定。
- 解决：删指标/改指标标签一律写 `metric_relabel_configs`；过滤目标才用 `relabel_configs`。

**坑 2：正则少写 .*，keep/drop 不生效**

- 现象：`regex: 'go'` 想删所有 go 指标，结果只删了名字恰好叫 go 的。
- 原因：正则整串匹配，`go` 只匹配字面量 go。
- 解决：写 `go.*`；需要前后缀时显式写全。

**坑 3：labeldrop 删标签导致序列冲突**

- 报错/现象：删标签后查询出现重复样本，日志报 `duplicate sample for timestamp`。
- 原因：标签是序列唯一约束，删成相同标签后两条序列撞车。
- 解决：去掉该 labeldrop 规则；确需删除，先确认不会让序列失去区分度。

**坑 4：规则顺序写反**

- 现象：先 labeldrop 再 labelmap，复制不出新标签。
- 原因：relabel 严格按书写顺序执行，源标签已被删就匹配不到。
- 解决：先复制/改名、后删除；改完逐条 promtool 检查。

**坑 5：__tmp 临时标签与内置标签冲突**

- 现象：临时值覆盖了系统标签，行为异常。
- 解决：临时存储统一用 `__tmp` 前缀命名（如 `__tmp_hash`），不要自创其他 `__` 开头标签。

**坑 6：reload 后以为历史数据也被删了**

- 现象：配了 drop 指标规则，但 Grafana 里还能看到过去的 go 指标。
- 原因：metric_relabel 只影响**新采集**的数据，已入库的历史数据要等保留期过期或手动删除。
- 解决：这是正常现象；如需立即清理历史数据，用 TSDB 管理接口（阶段十）或等过期。

---
## 阶段五：记录规则与告警

### 阶段目标

- 会写**记录规则**，把复杂查询预先算好；
- 理解告警从"规则计算"到"通知到人"的完整链路；
- 部署并配置 **Alertmanager**，实现去重、分组、路由、抑制、静默；
- 打通**邮件、企业微信、钉钉**三种通知渠道；
- 掌握 Alertmanager 高可用集群的搭建。

告警是监控系统最有价值的部分：人不可能 24 小时盯屏，程序自动巡检并报警，是业务稳定性的决定性保障。

---

### 5.1 记录规则

#### 5.1.1 规则简介

Prometheus 支持两类规则：**记录规则（Recording Rules）**和**告警规则（Alerting Rules）**。它们写在 YAML 文件里，通过主配置的 `rule_files` 加载，由 Prometheus 按 `evaluation_interval` 周期执行。

```yaml
rule_files:
  - "first_rules.yml"
  - "second_rules.yml"
  - "../rules/*.yml"
```

相对路径是相对于 `prometheus.yml` 所在目录。改规则后让 Prometheus 重新加载：

```bash
promtool check rules 规则文件.yml
systemctl reload prometheus
```

`promtool check rules` 语法正确时打印解析后的规则并以状态码 0 退出；有错误时打印错误并以 1 退出。

#### 5.1.2 记录规则说明

- **是什么**：记录规则把一个 PromQL 表达式预先、周期性地跑一遍，把结果存成一组**新的时间序列**。
- **类比**：像给一长串命令起"别名"——以后直接用短名字拿结果，不用每次重算。
- **为什么需要**：复杂查询（跨很多序列聚合）实时跑会有延迟，仪表盘每次刷新都重复算同样的表达式很浪费；预计算结果查询速度快得多，告警规则也可以直接引用。

**规则文件语法**：

```yaml
groups:
  - name: example              # 规则组名，必须唯一
    interval: 10s              # 本组评估间隔，默认取 global.evaluation_interval
    limit: 0                   # 记录规则：最多生成多少条序列；告警规则：最多多少条告警，默认 0 不限制
    rules:
      - record: job:http_inprogress_requests:sum    # 新指标名（推荐 命名空间:指标:粒度 三段式，冒号分隔）
        expr: sum(http_inprogress_requests) by (job)   # 要执行的 PromQL
        labels:                                  # 给结果附加的标签（可选）
          标签名: 标签值
```

::: tip
记录规则生成的指标名推荐用冒号三段式，如 `instance:node_cpu:avg_rate5m`，表示"按 instance 维度、node_cpu 指标、5 分钟平均速率"，一眼看出来源与粒度。冒号是规则专用，自己手写指标不要用。
:::

#### 5.1.3 记录规则案例

**案例 1：给 Flask 应用的"平均处理耗时"做预计算**

原始表达式很长：

```promql
request_processing_seconds_sum{job="my_metric"} / request_processing_seconds_count{job="my_metric"}
```

创建规则文件 `/usr/local/prometheus/rules/prometheus_record_rules.yml`：

```yaml
groups:
  - name: myrules
    rules:
      - record: request_process_per_time
        expr: request_processing_seconds_sum{job="my_metric"} / request_processing_seconds_count{job="my_metric"}
        labels:
          app: flask
          role: web
      - record: request_count_per_minute
        expr: increase(request_count_total{job="my_metric"}[1m])
        labels:
          app: flask
          role: web
```

检查并在主配置加载：

```bash
promtool check rules /usr/local/prometheus/rules/prometheus_record_rules.yml
```

预期输出：

```text
Checking /usr/local/prometheus/rules/prometheus_record_rules.yml
  SUCCESS: 2 rules found
```

编辑 `/usr/local/prometheus/conf/prometheus.yml`，确认有：

```yaml
rule_files:
  - "../rules/*.yml"
```

整体检查并生效：

```bash
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus
```

预期输出：

```text
Checking /usr/local/prometheus/conf/prometheus.yml
  SUCCESS: 1 rule files found
SUCCESS: /usr/local/prometheus/conf/prometheus.yml is valid prometheus config file syntax
Checking /usr/local/prometheus/rules/prometheus_record_rules.yml
  SUCCESS: 2 rules found
```

验证：等一两个评估周期后，在 Graph 查 `request_process_per_time` 能直接拿到结果；Status → Rules 页能看到这两条规则及其状态。Grafana 面板以后直接用新指标名即可，刷新明显变快。

**案例 2：系统主机相关指标的记录规则**

创建 `/usr/local/prometheus/rules/node_record_rules.yml`：

```yaml
groups:
  - name: custom_rules
    interval: 5s
    rules:
      # 每台主机 CPU 使用率（百分比）
      - record: instance:node_cpu:avg_rate5m
        expr: 100 - avg by (instance) (irate(node_cpu_seconds_total{job="node_exporter", mode="idle"}[5m])) * 100
      # 每台主机内存使用率（百分比）
      - record: instance:node_memory_used:percent
        expr: 100 - (100 * node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)
      # 根分区剩余百分比
      - record: instance:root:node_filesystem_free_percent
        expr: 100 * node_filesystem_free_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}
```

**案例 3：MySQL 相关记录规则**（阶段七用到，先放在这里）

创建 `/usr/local/prometheus/rules/mysql_record_rules.yml`：

```yaml
groups:
  - name: mysqld_rules
    rules:
      # 主从延迟秒数（考虑手工配置的 SQL 延迟）
      - record: instance:mysql_slave_lag_seconds
        expr: mysql_slave_status_seconds_behind_master - mysql_slave_status_sql_delay
      # 心跳法计算的主从延迟
      - record: instance:mysql_heartbeat_lag_seconds
        expr: mysql_heartbeat_now_timestamp_seconds - mysql_heartbeat_stored_timestamp_seconds
      # 事务速率（commit + rollback）
      - record: job:mysql_transactions:rate5m
        expr: sum without (command) (rate(mysql_global_status_commands_total{command=~"(commit|rollback)"}[5m]))
```

---

### 5.2 告警原理与 Alertmanager 部署

#### 5.2.1 告警链路总览

Prometheus 的告警能力分成**两个独立部分**：

1. **Prometheus 端**：定义**告警规则（Alert Rule）**，周期计算表达式；条件满足并持续 `for` 时长后，把告警**发送给 Alertmanager**；
2. **Alertmanager 端**：管理这些告警——**去重、分组、路由、静默、抑制**，最终通过邮件、企业微信、钉钉、Webhook 等渠道发出通知。

数据流向：

![Prometheus 告警链路](/guide/diagrams/alerting-flow.svg)

#### 5.2.2 Alertmanager 的五大特性

| 特性 | 作用 |
| --- | --- |
| **去重 Deduplication** | 多个相同告警只保留一条（高可用多实例场景尤其重要） |
| **分组 Grouping** | 把相似告警合并成一条通知。例如一台主机宕机可能同时触发几十条告警，分组后只发一条，避免告警风暴、便于定位 |
| **路由 Route** | 按标签把告警送到不同接收人/媒介（critical 发给管理层、warning 发给运维） |
| **抑制 Inhibition** | 某条告警存在时，压制由它引发的其他告警（主机挂了，就不必再报这台主机上的服务异常） |
| **静默 Silence** | 按标签在指定时间内不发通知，常用于例行维护；在 Web 页面设置 |

#### 5.2.3 二进制部署 Alertmanager

在**监控服务器 monitor** 上执行，用户 root。

**第 1 步：下载解压**

```bash
cd /usr/local
wget https://github.com/prometheus/alertmanager/releases/download/v0.34.1/alertmanager-0.34.1.linux-amd64.tar.gz
tar xf alertmanager-0.34.1.linux-amd64.tar.gz
ln -s alertmanager-0.34.1.linux-amd64 alertmanager
cd alertmanager
mkdir -p bin conf data
mv alertmanager amtool bin/
mv alertmanager.yml conf/
```

备选（GitHub）：

```text
https://github.com/prometheus/alertmanager/releases/download/v0.34.1/alertmanager-0.34.1.linux-amd64.tar.gz
```

`amtool` 是 Alertmanager 的命令行工具，可以检查配置、管理静默、查询告警。

**第 2 步：建用户、授权**

```bash
id prometheus &>/dev/null || useradd -r -s /usr/sbin/nologin prometheus
chown -R prometheus:prometheus /usr/local/prometheus/ /usr/local/alertmanager/
```

**第 3 步：创建服务文件**

```bash
cat > /etc/systemd/system/alertmanager.service <<'EOF'
[Unit]
Description=Prometheus Alertmanager
Documentation=https://prometheus.io/docs/alerting/alertmanager/
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=prometheus
Group=prometheus
ExecStart=/usr/local/alertmanager/bin/alertmanager \
  --config.file=/usr/local/alertmanager/conf/alertmanager.yml \
  --storage.path=/usr/local/alertmanager/data \
  --web.listen-address=0.0.0.0:9093 \
  --cluster.listen-address=0.0.0.0:9094
ExecReload=/bin/kill -HUP $MAINPID
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

参数解释：

| 参数 | 作用 |
| --- | --- |
| `--config.file` | 配置文件路径 |
| `--storage.path` | 告警/静默状态存储目录 |
| `--web.listen-address` | Web UI 与 API 端口，默认 9093；**建议显式写 0.0.0.0** |
| `--cluster.listen-address` | 集群 Gossip 通信端口，默认 9094，高可用必用 |

**第 4 步：启动、验证**

```bash
systemctl daemon-reload
systemctl enable --now alertmanager
ss -lntup | grep -E '9093|9094'
```

预期输出：

```text
tcp LISTEN 0 4096 *:9093 *:* users:(("alertmanager",pid=...))
tcp LISTEN 0 4096 *:9094 *:* users:(("alertmanager",pid=...))
udp UNCONN 0 4096 *:9094 *:* users:(("alertmanager",pid=...))
```

9093 是 Web/API 端口，9094 是集群端口（TCP+UDP）。浏览器访问 `http://【监控服务器IP】:9093` 能看到 Alertmanager 界面。

#### 5.2.4 Prometheus 对接 Alertmanager

编辑 `/usr/local/prometheus/conf/prometheus.yml` 的 `alerting` 段：

```yaml
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - '【监控服务器IP】:9093'
```

也支持文件发现写法：

```yaml
alerting:
  alertmanagers:
    - file_sd_configs:
        - files:
            - targets/alertmanager*.yaml
```

对应 `/usr/local/prometheus/conf/targets/alertmanager.yaml`：

```yaml
- targets:
    - '【监控服务器IP】:9093'
  labels:
    app: alertmanager
```

检查生效：

```bash
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus
```

建议同时把 Alertmanager 自身纳入监控，在 `scrape_configs` 加：

```yaml
  - job_name: 'alertmanager'
    static_configs:
      - targets: ['【监控服务器IP】:9093']
```

#### 5.2.5 Alertmanager 配置文件结构

配置文件路径：`/usr/local/alertmanager/conf/alertmanager.yml`，共**五个模块**：

| 模块 | 作用 |
| --- | --- |
| `global` | 全局配置：SMTP 邮件、企业微信 API、解析超时等 |
| `templates` | 通知模板文件路径 |
| `route` | 路由树根节点，定义分组与默认接收者 |
| `receivers` | 接收者列表，每个接收者配置邮件/微信/Webhook |
| `inhibit_rules` | 抑制规则 |

检查配置文件：

```bash
amtool check-config /usr/local/alertmanager/conf/alertmanager.yml
```

预期输出：

```text
Checking '/usr/local/alertmanager/conf/alertmanager.yml'  SUCCESS
Found:
  - global config
  - route
  - 1 inhibit rules
  - 1 receivers
  - 0 templates
  SUCCESS
```

`global` 段常用参数：

| 参数 | 作用 |
| --- | --- |
| `resolve_timeout` | 多长时间没再收到告警就标记为 resolved（恢复），默认 5m |
| `smtp_smarthost` | SMTP 服务器地址:端口 |
| `smtp_from` | 发件人地址 |
| `smtp_auth_username/password` | SMTP 登录名与授权码 |
| `smtp_require_tls` | 是否要求 TLS，默认 true；用 25 端口非加密时设 false |
| `wechat_api_url` | 企业微信 API 地址 |
| `wechat_api_corp_id` | 企业 ID |
| `wechat_api_secret` | 应用 Secret |

`route` 段常用参数：

| 参数 | 作用 | 推荐值 |
| --- | --- | --- |
| `receiver` | **默认接收者，必填**，否则启动失败 | — |
| `group_by` | 按哪些标签分组，如 `['alertname','cluster']` | — |
| `group_wait` | 首次收到一组告警后等多久再发（等同组其他告警到齐） | 10～30s |
| `group_interval` | 同组新增告警合并通知的最小间隔 | 5m |
| `repeat_interval` | 未恢复告警重复提醒的间隔 | 至少 3h |
| `continue` | 匹配后是否继续匹配后续子路由，默认 false | — |
| `routes` | 子路由列表 | — |

::: warning
`repeat_interval` 不要设得太短（如 10 秒）：邮件渠道发送过于频繁会被 SMTP 服务器拒绝，也会对接收人造成轰炸。生产建议 3～4 小时。
:::

---
### 5.3 告警规则

#### 5.3.1 告警规则语法

告警规则与记录规则写在同样的 groups 结构里，一条告警规则由以下部分组成：

```yaml
groups:
  - name: example
    rules:
      - alert: HighRequestLatency          # 告警名称（会成为 alertname 标签）
        expr: job:request_latency_seconds:mean5m{job="myjob"} > 0.5   # 布尔条件表达式
        for: 10m                           # 条件持续多久才真正告警，默认 0
        labels:                            # 附加标签（路由分组靠它）
          severity: warning
          project: myproject
        annotations:                       # 注释信息（通知正文用，不参与匹配）
          summary: "Instance {{ $labels.instance }} 请求延迟过高"
          description: "{{ $labels.instance }} job {{ $labels.job }} 延迟已超过 0.5s 达 10 分钟，当前值 {{ $value }}"
```

字段解释：

| 字段 | 作用 |
| --- | --- |
| `alert` | 告警名称，要能直接表达告警内容 |
| `expr` | PromQL 条件，有结果（条件成立）即为异常 |
| `for` | 条件持续满足这么久才告警；期间状态为 **pending**，之后 **firing**。应大于抓取间隔，避免偶发抖动误报 |
| `labels` | 告警标签，`severity` 是约定俗成的级别标签 |
| `annotations` | 通知里展示的详情；`{{ $labels.x }}` 取标签值，`{{ $value }}` 取触发值 |

表达式太复杂时，建议先用记录规则预计算，告警规则直接引用记录结果，避免实时计算延迟。

社区有大量现成告警规则（强烈推荐参考）：

```text
https://samber.github.io/awesome-prometheus-alerts/
```

**Node Exporter 常用告警规则**（完整版见上面链接，这里给核心几条），创建 `/usr/local/prometheus/rules/node_alert_rules.yml`：

```yaml
groups:
  - name: node-exporter
    rules:
      # 主机宕机（目标采集失败）
      - alert: HostDown
        expr: up{job="node_exporter"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "主机宕机 (instance {{ $labels.instance }})"
          description: "{{ $labels.instance }} 已无法采集超过 1 分钟"

      # 可用内存不足 10%
      - alert: HostOutOfMemory
        expr: node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes * 100 < 10
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "内存不足 (instance {{ $labels.instance }})"
          description: "可用内存低于 10%，当前值 = {{ $value }}"

      # CPU 使用率超过 80%
      - alert: HostHighCpuLoad
        expr: 100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[2m])) * 100) > 80
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "CPU 使用率过高 (instance {{ $labels.instance }})"
          description: "CPU 使用率 > 80%，当前值 = {{ $value }}"

      # CPU iowait 超过 5%（说明磁盘或网络成瓶颈）
      - alert: HostCpuHighIowait
        expr: avg by (instance) (rate(node_cpu_seconds_total{mode="iowait"}[5m])) * 100 > 5
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "CPU iowait 过高 (instance {{ $labels.instance }})"
          description: "iowait > 5%，当前值 = {{ $value }}"

      # 磁盘可用空间不足 10%
      - alert: HostOutOfDiskSpace
        expr: (node_filesystem_avail_bytes * 100) / node_filesystem_size_bytes < 10
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "磁盘空间不足 (instance {{ $labels.instance }})"
          description: "{{ $labels.mountpoint }} 可用空间低于 10%，当前值 = {{ $value }}"

      # conntrack 连接跟踪表使用超过 80%
      - alert: HostConntrackLimit
        expr: node_nf_conntrack_entries / node_nf_conntrack_entries_limit > 0.8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "conntrack 表接近上限 (instance {{ $labels.instance }})"
          description: "连接跟踪条目超过上限的 80%，当前值 = {{ $value }}"
```

#### 5.3.2 告警的三种状态

在 Prometheus 的 Alerts 页面可看到：

| 状态 | 含义 |
| --- | --- |
| **Inactive** | 条件未触发，一切正常 |
| **Pending** | 条件已触发，但还没满足 `for` 持续时间，不发通知 |
| **Firing** | 条件触发且持续足够时间，已发送给 Alertmanager |

#### 5.3.3 邮件告警案例

**第 1 步：开启邮箱 SMTP 授权码**

在邮箱网页后台开启 SMTP 服务并生成**授权码**（注意是授权码，不是邮箱登录密码）。QQ 邮箱、163 邮箱、企业邮箱后台都有"POP3/SMTP 服务"开关，开启后按提示用手机发短信获取授权码。

**第 2 步：编写告警规则**

创建 `/usr/local/prometheus/rules/flask_alert_rules.yml`：

```yaml
groups:
  - name: flask_web
    rules:
      - alert: InstanceDown
        expr: up{job="my_metric"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Instance {{ $labels.instance }} 停止工作"
          description: "{{ $labels.instance }} job {{ $labels.job }} 已经停止 1 分钟以上"
```

**第 3 步：配置 Alertmanager 邮件**

编辑 `/usr/local/alertmanager/conf/alertmanager.yml`（以 163 邮箱、25 端口非加密为例）：

```yaml
global:
  resolve_timeout: 1m
  smtp_smarthost: 'smtp.163.com:25'
  smtp_from: '【你的发件邮箱】'
  smtp_auth_username: '【你的发件邮箱】'
  smtp_auth_password: '【邮箱授权码】'
  smtp_hello: '163.com'
  smtp_require_tls: false

route:
  group_by: ['alertname', 'cluster']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 3h
  receiver: 'email'

receivers:
  - name: 'email'
    email_configs:
      - to: '【收件邮箱】'
        send_resolved: true
```

参数解释：`send_resolved: true` 表示故障恢复后也发一封标题带 `[Resolved]` 的恢复通知。

检查并重启：

```bash
amtool check-config /usr/local/alertmanager/conf/alertmanager.yml
systemctl restart alertmanager
```

**第 4 步：验证**

停掉 Flask 应用（在 app01 上 `Ctrl+C` 或停止服务），等待 1 分钟以上：

- Prometheus Alerts 页：`InstanceDown` 从 Pending 变 Firing；
- Alertmanager 页面：能看到这条告警；
- 收件邮箱：收到告警邮件；
- 恢复 Flask 后：收到恢复邮件。

::: tip
QQ 邮箱如用 465 端口（SSL），需要保留 TLS 相关配置（`smtp_require_tls: true`）；用 25 端口非加密时设 false。若 25 端口被云厂商封禁（部分云厂商默认封禁 25 端口防垃圾邮件），改用 465/587 端口。
:::

---

