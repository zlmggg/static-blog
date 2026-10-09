---
category: 监控
difficulty: 中级
---

# Prometheus 实战 04：PromQL 查询与自定义 Exporter

> **Prometheus 实战系列（共 10 篇）**
> ← 上一篇 [Prometheus 实战 03](./monitor-prometheus-03-exporters-grafana) ｜ 下一篇 [Prometheus 实战 05](./monitor-prometheus-05-rules-alertmanager) →
> [返回监控索引](./monitor)

## 阶段三：PromQL 查询语言与自定义 Exporter

### 阶段目标

- 理解四种数据类型（即时向量、范围向量、标量、字符串）；
- 熟练使用标签选择器、范围选择器、offset；
- 分清 Counter、Gauge、Histogram、Summary 四种指标类型及适用场景；
- 会用算术/比较/逻辑运算符、向量匹配、聚合运算、常用函数写出实用查询；
- 能用 Python、Go 开发自定义 Exporter，并在 Grafana 里为自定义指标画图。

所有查询都在 Prometheus 自带界面（`http://【监控服务器IP】:9090`）顶部 **Graph** 页面完成：输入表达式 → 点 **Execute** → 看 Table/Graph。

---

### 3.1 指标数据基础

#### 3.1.1 时间序列与向量

- **时间序列数据**：按时间顺序记录系统状态变化的数据，每个数据称为一个**样本（Sample）**；周期性采集后形成离散的样本序列，这个序列也叫**向量（Vector）**。
- **类比**：把多条序列放在同一坐标系（横轴时间、纵轴序列），就形成一个由数据点组成的矩阵——就像一张每格都有数字的表格。
- Prometheus 靠**指标名 + 标签集**唯一定义一条时间序列：指标名说明"测的是什么属性"，标签是在这个属性上再细分的维度。

#### 3.1.2 数据模型与样本

指标名有两种等价写法：

```text
<metric name>{<label name>=<label value>, …}
{__name__="metric name", <label name>=<label value>, …}
```

第二种把指标名当成一个特殊标签 `__name__`，常用于内部处理和按名字正则匹配。

**每个样本由两部分组成**：

| 组成 | 内容 |
| --- | --- |
| key（键） | 指标名 + 标签 + 时间戳（毫秒精度） |
| value（值） | float64 浮点数 |

务必记住的规则：

- 指标名相同、标签不同 → 不同的时间序列；
- **更改任何标签值（包括增、删标签）都会创建新序列**；
- 标签要尽量稳定，否则图形、告警、记录规则会失效。

---

### 3.2 PromQL 基础

#### 3.2.1 它是什么

PromQL（Prometheus Query Language）是 Prometheus 内置的**函数式表达式语言**，用来实时查找、聚合时序数据。结果可以画图、在表达式浏览器里看表格，或通过 HTTP API 给外部系统用。默认以**当前时间**为基准取数。

#### 3.2.2 四种表达式结果类型

| 类型 | 含义 | 类比 |
| --- | --- | --- |
| **Instant Vector 即时向量** | 同一时间戳下，每条序列各一个样本 | "此刻全班每个人的体温" |
| **Range Vector 范围向量** | 一段时间内，每条序列的一串样本 | "过去一小时每个人每 15 秒的体温" |
| **Scalar 标量** | 一个简单浮点数 | "此刻教室平均体温 36.7" |
| **String 字符串** | 一个简单字符串（当前基本未使用） | 一句话 |

**字面量写法**：

```text
# 字符串：单引号、双引号、反引号都行；反引号里的转义符不生效
"this is a string"
'these are unescaped: \n \t'
`these are not unescaped: \n ' " \t`

# 数字：整数、小数、负数
2      2.43      -2.43
```

#### 3.2.3 使用要点（非常容易报错的地方）

1. **画图只支持即时向量**：Graph 图表面板只能画即时向量；
2. **rate 等速率函数必须吃范围向量**：即 `rate(指标[5m])`，中括号不能少；
3. **范围向量不能直接画图**，否则报错：

```text
Error executing query: invalid expression type "range vector" for range query, must be Scalar or instant Vector
```

所以范围向量几乎总是配合 `rate`、`increase`、`avg_over_time` 等函数使用，函数输出即时向量后才能画图。

#### 3.2.4 数据选择器

通用样式：

```text
metrics_name{标签筛选}[时间范围] offset 偏移量
```

##### 3.2.4.1 即时向量选择器

由"指标名（可选）+ 匹配器（可选，写在 {} 里）"组成，二者至少给一个。

**用法 1：只给指标名，取该指标全部序列的最新值**

```promql
node_filefd_allocated
prometheus_http_requests_total
```

`http_requests_total` 和 `http_requests_total{}` 完全等价。

**用法 2：用 __name__ 按名字匹配多个指标**

```promql
{__name__="prometheus_http_requests_total"}
{__name__=~"^prometheus_http_.*"}
```

`=~` 是正则匹配，第二条能匹配所有以 `prometheus_http_` 开头的指标。

**用法 3：只给匹配器（跨指标名）**

```promql
{method="get"}
```

返回所有带 `method="get"` 标签的序列，可能来自不同指标。

**用法 4：指标名 + 匹配器组合**

```promql
http_requests_total{method="get"}
prometheus_http_requests_total{handler="/-/reload"}
```

**四种匹配器（Matcher）**：

| 操作符 | 含义 | 示例 |
| --- | --- | --- |
| `=` | 精确相等 | `{job="prometheus"}` |
| `!=` | 不相等 | `{instance!="localhost:9090"}` |
| `=~` | 正则匹配（**整串完全匹配，不是包含**） | `{instance=~"10.0.0.(11|12):9100"}` |
| `!~` | 正则不匹配 | `{instance!~"10.0.0.1[0-9]:9100"}` |

匹配规则细节：

- 匹配**空标签值**时，所有"未定义该标签"的序列也符合条件。例如 `http_requests_total{env=""}` 会匹配所有没有 env 标签或 env 为空的序列；
- 正则是**完全锚定**的，必须匹配标签整个值。想表达"以 ge 开头"，要写 `method=~"ge.*"`，只写 `"^ge"` 匹配不到；
- 多值用 `|`（或）：`env=~"staging|testing|development"`；
- 选择器至少包含一个指标名，或一个非空标签条件，**不能写 `{job=~".*"}`、`{job=""}` 这种"全选空条件"**。

正则示例（在你的环境里替换 IP 试）：

```promql
node_memory_MemAvailable_bytes{instance=~"10.0.0.20.:9100"}
node_memory_MemAvailable_bytes{instance=~"10.0.0.20[12]:9100"}
node_memory_MemAvailable_bytes{instance=~"10.0.0.20[1-3]:9100"}
node_memory_MemAvailable_bytes{instance=~"10.0.0.20.*:9100"}
node_memory_MemAvailable_bytes{instance=~"10.0.0.20[0-9]:9100"}
node_memory_MemAvailable_bytes{instance=~"10.0.0.20[^01]:9100"}
node_memory_MemAvailable_bytes{instance!~"10.0.0.20[12]:9100"}
```

正则符号速记：`.` 任意单个字符；`.*` 任意多个字符；`[12]` 是 1 或 2；`[1-3]` 是 1～3；`[^01]` 是除 0、1 外的字符。

##### 3.2.4.2 范围向量选择器

在即时选择器后加 `[时间范围]`：

```promql
prometheus_http_requests_total{job="prometheus"}[5m]
```

读法：过去 5 分钟内该指标的所有样本，以表格呈现。

时间单位：`s` 秒、`m` 分、`h` 时、`d` 天、`w` 周、`y` 年。必须用**整数**，可从大到小串联：`1h30m` 合法，`1.5h` 非法。

::: tip
范围向量里各序列的时间戳不会严格对齐：Prometheus 会把抓取分散在时间点前后以均衡负载。所以 Prometheus 在趋势上准确，但不是分毫不差——这也是它不能用于计费的原因之一。
:::

##### 3.2.4.3 offset 偏移修饰符

offset 改变取数的**时间基准**，紧跟在选择器后面，是一个整体、不能拆开：

```promql
# 此刻该指标的值
prometheus_http_requests_total
# 5 分钟前该指标的值
prometheus_http_requests_total offset 5m
prometheus_http_requests_total{code="200"} offset 5m
# 范围 + 偏移：1 天之前的那 5 分钟数据
http_requests_total[5m] offset 1d
http_requests_total{handler="/metrics"}[5m] offset 3m
```

`[5m] offset 3m` 的含义：以 3 分钟前为终点，往前取 5 分钟的数据。

#### 3.2.5 四种指标类型

先在任意 exporter 上统计一下类型分布，命令（在监控服务器普通终端执行）：

```bash
curl -s http://【监控服务器IP】:9090/metrics | awk '$2=="TYPE"{type[$NF]++}END{for(i in type){print type[i],i}}'
```

参数解释：`awk '$2=="TYPE"'` 挑出第二列是 TYPE 的行，`$NF` 是最后一列（类型名），统计每种类型出现次数。预期输出类似：

```text
74 gauge
7 histogram
12 summary
93 counter
```

##### Counter（计数器）

- **是什么**：单调递增的累计值，只增不减，进程重启时归零重新计数；
- **类比**：像汽车的**总里程表**，只会往上走，熄火重启后小表可能归零但累计逻辑不变；
- **典型指标**：请求总数、错误总数、任务完成数、网络收发包总数。**不能用它表示会减少的值**。

Counter 一般不直接看总数，而配合 `rate`、`irate`、`increase`、`topk` 看变化：

```promql
# 请求总数排名前 3 的序列
topk(3, http_requests_total)
# 2 小时内每秒平均增长速率（平均值，会抹平突发）
rate(http_requests_total[2h])
# 瞬时速率（取范围内最后两个点，能反映突发）
irate(http_requests_total[2h])
```

##### Gauge（仪表盘/瞬时值）

- **是什么**：可任意上下波动的瞬时数值；
- **类比**：像**温度计、体重秤**，当前是多少就是多少，可升可降；
- **典型指标**：CPU 使用率、内存/磁盘剩余、当前并发连接数、队列积压、温度。

Gauge 常做求和、平均、最值，也配合 `predict_linear`（预测）、`delta`（差值）：

```promql
# 2 小时内 CPU 温度的变化量（末值减首值）
delta(cpu_temp_celsius{host="【监控服务器IP】"}[2h])
# 按线性回归预测 4 小时后的值（磁盘容量预警常用）
predict_linear(node_filesystem_free_bytes{mountpoint="/"}[1h], 4*3600)
```

##### Histogram（直方图）

- **是什么**：统计数据**分布**——把观测值按区间（bucket，存储桶）计数，再用函数算分位数；
- **类比**：像统计**考试成绩分布**：0～60 分多少人、60～80 分多少人、80～100 分多少人；
- **典型场景**：请求响应时间分布（0～50ms 多少、50ms～2s 多少、10s 以上多少）、响应大小分布。

Prometheus 的桶是**累积（cumulative）**的：每个桶包含它之前所有桶的样本，因此叫累积直方图，维护成本低。一个 Histogram 指标 `<basename>` 会生成三类序列：

```promql
# 各桶的累计样本数，le（小于等于）是桶的上界；+Inf 桶包含全部样本
<basename>_bucket{le="<上界>"}
# 所有观测值总和
<basename>_sum
# 观测总次数（本质是 Counter）
<basename>_count
```

真实样例：

```text
# TYPE prometheus_tsdb_compaction_chunk_range_seconds histogram
prometheus_tsdb_compaction_chunk_range_seconds_bucket{le="100"} 0
prometheus_tsdb_compaction_chunk_range_seconds_bucket{le="400"} 0
prometheus_tsdb_compaction_chunk_range_seconds_bucket{le="6.5536e+06"} 6028
prometheus_tsdb_compaction_chunk_range_seconds_bucket{le="+Inf"} 6028
prometheus_tsdb_compaction_chunk_range_seconds_sum 1.0734846288e+10
prometheus_tsdb_compaction_chunk_range_seconds_count 6028
```

分位数用 `histogram_quantile()` 在**服务端**估算（假设桶内线性分布，结果是近似值，桶越粗越不准）：

```promql
# 过去 10 分钟请求耗时的第 90 百分位（P90）
histogram_quantile(0.9, rate(prometheus_http_request_duration_seconds_bucket[10m]))
```

##### Summary（摘要）

- **是什么**：和 Histogram 类似，但**分位数在客户端直接算好**并暴露；
- **类比**：Histogram 像老师拿原始成绩自己算百分位；Summary 像课代表提前算好各百分位交给老师；
- **典型指标**：Go GC 停顿时间 `go_gc_duration_seconds`、抓取间隔 `prometheus_target_interval_length_seconds`。

一个 Summary 生成：

```promql
<basename>{quantile="0.5"}      # 客户端算好的中位数
<basename>{quantile="0.9"}      # P90
<basename>{quantile="0.99"}     # P99
<basename>_sum
<basename>_count
```

真实样例：

```text
# HELP go_gc_duration_seconds A summary of the pause duration of garbage collection cycles.
# TYPE go_gc_duration_seconds summary
go_gc_duration_seconds{quantile="0"} 3.4414e-05
go_gc_duration_seconds{quantile="0.5"} 6.5102e-05
go_gc_duration_seconds{quantile="1"} 0.001090964
go_gc_duration_seconds_sum 0.02311494
go_gc_duration_seconds_count 229
```

##### Histogram 与 Summary 对比（高频面试题）

| 对比项 | Histogram | Summary |
| --- | --- | --- |
| 分位数在哪算 | 服务端 PromQL 估算 | 客户端预先算好 |
| 能否聚合后再算分位 | **能**（先聚合桶再 histogram_quantile） | **不能**（分位数无法跨实例聚合） |
| 灵活性 | 任意指定分位数、可改桶 | 只能用客户端定义好的分位点 |
| 查询性能 | 计算消耗服务端资源 | 查询快 |
| 准确度 | 近似，取决于桶粒度 | 对该客户端较准 |
| 资源开销 | 客户端只做分桶，开销小 | 客户端计算分位，开销略大 |

经验：需要**跨实例聚合**（如整个服务的 P99）选 Histogram；只关心单实例、且查询性能敏感可考虑 Summary。

---

### 3.3 PromQL 运算

#### 3.3.1 二元运算符

**算术运算符**：

| 符号 | 含义 |
| --- | --- |
| `+` `-` `*` `/` | 加、减、乘、除 |
| `%` | 取模（余数） |
| `^` | 幂（乘方） |

**比较运算符**：`==`（等于）、`!=`（不等）、`>`、`<`、`>=`、`<=`。

**逻辑/集合运算符**：`and`、`or`、`unless`——**只能在两个即时向量之间使用，标量不能参与**。

**优先级（从高到低）**：

```text
1. ^
2. *  /  %
3. +  -
4. == != <= < >= >
5. and  unless
6. or
```

同级左结合（幂运算右结合）；可用 `()` 改变次序。

**算术运算示例**：

```promql
# GC 平均停顿 = 总停顿 / 次数
go_gc_duration_seconds_sum / go_gc_duration_seconds_count

# 空闲内存换算成 MB
node_memory_MemFree_bytes / (1024 * 1024)

# 可用内存占比（百分比）
node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes * 100

# 内存使用率（百分比）
(node_memory_MemTotal_bytes - node_memory_MemFree_bytes) / node_memory_MemTotal_bytes * 100

# 根分区磁盘使用率（百分比）
(node_filesystem_size_bytes{mountpoint="/"} - node_filesystem_free_bytes{mountpoint="/"}) / node_filesystem_size_bytes{mountpoint="/"} * 100
```

**比较运算示例**：

```promql
# 内存使用率超过 95% 的序列（不满足的序列直接不返回）
(node_memory_MemTotal_bytes - node_memory_MemFree_bytes) / node_memory_MemTotal_bytes > 0.95

# 内存利用率是否超过 80%：加 bool 后不做过滤，满足返回 1、不满足返回 0
(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100 > bool 80

# 请求数超过 1000 时返回 1，否则 0
prometheus_http_requests_total > bool 1000
```

`bool` 的作用：默认比较运算符会**过滤掉**不满足条件的序列；加 `bool` 后不过滤，而是把比较结果写成 0/1，形成新序列——做"状态指示"时用。

**集合运算示例**：

```promql
# 并集 or：两侧序列都保留（标签完全相同的以左侧为准）
node_memory_MemTotal_bytes{instance="10.0.0.104:9100"} or node_memory_MemFree_bytes{instance="10.0.0.105:9100"}

# 交集 and：只保留"在右侧也存在"的左侧序列
node_memory_MemTotal_bytes{instance="10.0.0.101:9100"} and node_memory_MemFree_bytes{instance="10.0.0.104:9100"}

# 补集 unless：从左侧剔除"在右侧也存在"的序列
node_memory_MemTotal_bytes{job="node_exporter"} unless node_memory_MemTotal_bytes{instance="10.0.0.104:9100"}
```

`and`/`or`/`unless` 操作的是完整表达式（向量），不是单个数字。

#### 3.3.2 向量匹配

两侧向量做运算时，默认按"全部标签完全相同"一一配对。标签对不上时用下面关键字调整：

| 关键字 | 作用 |
| --- | --- |
| `on(标签列表)` | 只用列出的标签做匹配 |
| `ignoring(标签列表)` | 匹配时忽略列出的标签 |
| `group_left(标签列表)` | 允许**左多右少**（多对一） |
| `group_right(标签列表)` | 允许**左多右少的反向**（一对多） |

**一对一匹配**：

```promql
# 各方法 500 错误占该方法总请求的比例；忽略 code 标签后按 method 配对
method_code:http_errors:rate5m{code="500"} / ignoring(code) method:http_requests:rate5m
```

示例输入与结果：

```text
method_code:http_errors:rate5m{method="get", code="500"} 24
method_code:http_errors:rate5m{method="post", code="500"} 6
method:http_requests:rate5m{method="get"} 600
method:http_requests:rate5m{method="post"} 120

结果：
{method="get"} 0.04      # 24 / 600
{method="post"} 0.05     # 6 / 120
```

没有 `ignoring(code)` 时，两侧标签集不同（一侧多 code）无法匹配；`put`、`del` 方法在另一侧没有对应项，不会出现在结果里。

**多对一（group_left）**：

```promql
# 左侧每个 method 有 code=500/404 多条，右侧每个 method 一条，用 group_left
method_code:http_errors:rate5m / ignoring(code) group_left method:http_requests:rate5m
```

结果：

```text
{method="get", code="500"} 0.04     # 24 / 600
{method="get", code="404"} 0.05     # 30 / 600
{method="post", code="500"} 0.05    # 6 / 120
{method="post", code="404"} 0.175   # 21 / 120
```

`group_left/right` 括号里还可以列出"需要从另一侧带过来的标签"。一对多把 `group_left` 换成 `group_right` 即可。

#### 3.3.3 聚合运算

聚合运算符（注意：它们**不是函数**，语法上不需要用 by 时直接 `sum(...)`），常见 11 种：

| 运算符 | 作用 |
| --- | --- |
| `sum` | 求和 |
| `min` / `max` | 最小 / 最大值 |
| `avg` | 平均值 |
| `count` | 统计序列条数 |
| `count_values` | 按样本值计数（把值变成新标签） |
| `stddev` / `stdvar` | 标准差 / 方差（衡量波动） |
| `topk` / `bottomk` | 值最大 / 最小的前 k 条序列 |
| `quantile` | 聚合分位数 |

**分组关键字**：

| 关键字 | 含义 |
| --- | --- |
| `by (标签列表)` | 只按列出的标签分组 |
| `without (标签列表)` | 排除列出的标签，按其余所有标签分组 |

两种等价写法：

```promql
sum(node_memory_MemTotal_bytes) by (instance)
sum by (instance) (node_memory_MemTotal_bytes)
```

聚合示例：

```promql
# 显示系统版本
node_os_version
# 统计 Ubuntu 主机数量
count(node_os_version{id="ubuntu"})
# 按版本值计数，新标签名叫 os_version
count_values("os_version", node_os_version)
# 全部主机内存总和
sum(node_memory_MemTotal_bytes)
# 按实例分别求内存总量
sum(node_memory_MemTotal_bytes) by (instance)
# 每台主机的 CPU 核数（system 模式的 CPU 条目数 = 核数）
count(node_cpu_seconds_total{mode="system"}) by (instance)
# 最大请求数，按 handler、instance 分组
max(prometheus_http_requests_total) by (handler, instance)
# 值最大的前 5 条 / 最小的前 5 条
topk(5, prometheus_http_requests_total)
bottomk(5, prometheus_http_requests_total)
# 排除 instance、job 后分组求和
sum(prometheus_http_requests_total) without (instance, job)
# 仅按 mode 分组求和
sum(node_cpu_seconds_total) by (mode)
```

`count_values("os_version", node_os_version)` 的典型结果：

```text
{os_version="22.04"} 4
{os_version="20.04"} 2
```

**占比类查询（注意两侧结构必须匹配）**：

```promql
# /metrics 请求占所有请求的百分比（两侧都聚合成无维度的单值，才能相除）
sum(prometheus_http_requests_total{handler="/metrics", instance="localhost:9090"})
  / sum(prometheus_http_requests_total{instance="localhost:9090"})

# 200 响应占比
sum(prometheus_http_requests_total{code="200", handler="/-/ready"})
  / sum(prometheus_http_requests_total{handler="/-/ready"})

# Nginx 某接口 200 占比
sum(nginx_http_requests_total{path="/api", method="GET", code="200"})
  / sum(nginx_http_requests_total{path="/api", method="GET"})
```

::: warning
下面这种写法会报错或对不上：左侧是带一堆标签的明细序列，右侧是 `sum(...) by (...)` 聚合后的向量，两侧标签结构不同、无法一一匹配，除法没有结果：

```promql
# 错误示范：左明细、右聚合，结构不兼容
prometheus_http_requests_total{code="200"} / sum(prometheus_http_requests_total) by (handler, instance)
```

正确做法：**两侧都先聚合成相同标签维度再相除**（如上一组示例）。
:::

#### 3.3.4 常用功能函数

官方提供约 40 个函数，按类别掌握常用的即可。

**取整与数学**：

```promql
ceil(node_load15 * 10)      # 向上取整
floor(node_load15 * 10)     # 向下取整
round(node_load15 * 10)     # 四舍五入
abs(指标)                    # 绝对值
sqrt(指标)                   # 平方根；ln/log2/log10 对数，exp 指数
```

**Counter 变化类（最高频）**：

```promql
# increase：区间内的增长量（末值减首值）
increase(node_cpu_seconds_total{cpu="0", mode="idle"}[1m])

# CPU 使用率（用 increase 写法，与 rate 等价思路）
(1 - sum(increase(node_cpu_seconds_total{mode="idle"}[1m])) by (instance)
   / sum(increase(node_cpu_seconds_total[1m])) by (instance)) * 100

# rate：区间内每秒平均增量 = (末值-首值)/秒数
rate(node_disk_read_bytes_total[1m])
# 网卡每秒发送 MB
rate(node_network_transmit_bytes_total{device="eth0"}[1m]) / 1024 / 1024

# irate：取区间内最后两个点算瞬时速率
irate(node_disk_read_bytes_total[1m])

# resets：区间内 Counter 被重置（归零）的次数
resets(指标[5m])
```

**rate 与 irate 的区别（高频）**：

| 对比 | rate | irate |
| --- | --- | --- |
| 计算 | 区间所有点算速率后取平均 | 只取最后两个点 |
| 图像 | 平缓，**会削平短时峰值** | 尖锐，能反映突发 |
| 适用 | 缓慢变化的 Counter、告警阈值（避免毛刺误报） | 快速变化的 Counter、看实时峰值 |

经验：**告警用 rate（避免毛刺误报），看实时尖峰用 irate**；irate 的区间建议至少包含 2 个以上样本。

**Gauge 变化类**：

```promql
delta(指标[2h])        # 末值减首值（变化量）
idelta(指标[2h])       # 区间内相邻样本差值的最新一个
deriv(指标[1h])        # 线性回归斜率（每秒变化趋势）
predict_linear(指标[1h], 4*3600)   # 预测 4 小时后的值
holt_winters(指标[30m], 0.5, 0.5)  # 指数平滑，降噪
```

**子区间聚合（_over_time 系列，Gauge/Counter 通用）**：

```promql
min_over_time(指标[5m])
max_over_time(指标[5m])
avg_over_time(指标[5m])
sum_over_time(指标[5m])
count_over_time(指标[5m])
quantile_over_time(0.95, 指标[5m])
stddev_over_time(指标[5m])
stdvar_over_time(指标[5m])
last_over_time(指标[5m])
```

**取样与缺失判断**：

```promql
sort(指标)              # 按值升序
sort_desc(指标)         # 降序
changes(指标[5m])       # 区间内值变化次数
clamp_max(指标, 100)    # 超过 100 的压成 100
clamp_min(指标, 0)      # 小于 0 的抬成 0
scalar(即时向量)        # 取单条序列转成标量
vector(标量)            # 标量转成无标签即时向量
absent(指标)            # 指标存在返回空；不存在返回 1（用于"指标缺失"告警）
absent_over_time(指标[1h])   # 区间内完全没样本时返回 1
```

absent 示例：

```promql
# 指标名写错/没采集时，返回 absent 结果（值为 1），可据此告警
absent(node_memory_SwapTotal_bytes)
```

**时间类函数**：

```promql
time()                # 当前 Unix 时间戳（秒）
hour() minute() month() year()
day_of_month() day_of_week() days_in_month()
timestamp(即时向量)    # 样本自身的时间戳
```

time 示例：

```promql
# 每台主机已运行多少小时
(time() - node_boot_time_seconds) / 3600
# 全部主机运行小时总和
sum(time() - node_boot_time_seconds) / 3600
```

**标签类函数**：

```promql
# label_join：把多个标签值拼成一个新标签
label_join(指标, "新标签", "分隔符", "源标签1", "源标签2")
# label_replace：用正则从源标签提取内容写入新标签
label_replace(指标, "新标签", "替换串", "源标签", "正则")
```

---
### 3.4 定制开发 Exporter

#### 3.4.1 指标的五种提供方式

Prometheus 能监控的指标，来源有：

1. **Prometheus 内置**（自身指标）；
2. **程序仪表（Instrumentation）**：应用自带指标功能，如 Zookeeper、GitLab、Grafana；
3. **额外 Exporter**：第三方翻译程序，如 Node Exporter；
4. **Pushgateway**（短任务）；
5. **自行编程实现**：需要开发能力，自定义业务指标（转化率、下单量等）。

本质上，一个 metric 就是服务启动后自动生成的一个 HTTP URL，访问它就能拿到监控项。生产中大量业务指标（转化率、各渠道下单数）官方没有现成指标，就要自己开发标准的 `/metrics` 接口。

各语言客户端库：

```text
Go:      https://github.com/prometheus/client_golang
Python:  https://github.com/prometheus/client_python
文档:    https://prometheus.github.io/client_python/
Java:    https://github.com/prometheus/client_java
Rust:    https://github.com/prometheus/client_rust
```

#### 3.4.2 Python 实现自定义 Exporter

##### 3.4.2.1 准备环境（推荐 apt 直接装）

在**应用服务器 app01**（示例 10.0.0.12）上执行，用户 root。

```bash
apt update && apt -y install python3 python3-pip python3-flask python3-prometheus-client
mkdir -p /data/code
```

Ubuntu 24.04 仓库已包含 Flask 和 prometheus-client，最省事。

**如果用 pip 安装（22.04 或仓库没有时），先配清华 pip 源**：

```bash
pip3 config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
pip3 install flask prometheus_client
pip3 list | grep -Ei 'flask|prometheus'
```

pip 配置文件实际路径 `/root/.config/pip/pip.conf`，内容：

```ini
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
```

**备选 pip 源（清华不通时）**：阿里云 `https://mirrors.aliyun.com/pypi/simple`。

##### 3.4.2.2 最简三步示例（先建立感性认识）

第 1 步：安装客户端（上一步已装）；
第 2 步：把下面内容存成 `/data/code/three_step.py`：

```python
from prometheus_client import start_http_server, Summary
import random
import time

# 创建一个指标，记录处理耗时和请求
REQUEST_TIME = Summary('request_processing_seconds', 'Time spent processing request')

# 用装饰器给函数计时
@REQUEST_TIME.time()
def process_request(t):
    """模拟处理请求：睡 t 秒"""
    time.sleep(t)

if __name__ == '__main__':
    # 启动 HTTP 服务暴露指标
    start_http_server(8000)
    # 不断产生请求
    while True:
        process_request(random.random())
```

第 3 步：运行并访问 `http://【应用服务器IP】:8000/` 查看指标：

```bash
python3 /data/code/three_step.py
```

##### 3.4.2.3 指标对象的设计方式

prometheus_client 中各类型指标的构造方式（了解参数）：

```python
from prometheus_client import Counter, Gauge, Summary
from prometheus_client.core import CollectorRegistry

class Monitor:
    def __init__(self):
        # 自建收集器注册表
        self.collector_registry = CollectorRegistry(auto_describe=False)

        # Summary：名称、说明、标签列表、注册表
        self.summary_metric = Summary(
            name="summary_metric_name",
            documentation="summary_metric_desc",
            labelnames=("label1", "label2", "label3"),
            registry=self.collector_registry)

        # Gauge
        self.gauge_metric = Gauge(
            name="gauge_metric_name",
            documentation="gauge_metric_desc",
            labelnames=("method", "code", "uri"),
            registry=self.collector_registry)

        # Counter
        self.counter_metric = Counter(
            name="counter_metric_name",
            documentation="counter_metric_desc",
            labelnames=("method", "code", "uri"),
            registry=self.collector_registry)
```

##### 3.4.2.4 完整 Flask 项目（应用接口 + metrics 同端口）

创建 `/data/code/prometheus_metrics_demo.py`：

```python
#!/usr/bin/python3
from prometheus_client import Counter, Summary, generate_latest
from flask import Flask, Response
import time

app = Flask(__name__)

# 创建监控指标
REQUEST_TIME = Summary('request_processing_seconds', 'Time spent processing request')
REQUEST_COUNT = Counter('request_count', 'Total request count')

@app.route('/')
@REQUEST_TIME.time()
def hello():
    REQUEST_COUNT.inc()
    return {"return": "success OK!"}

@app.route('/metrics')
def metrics():
    # 返回 Prometheus 格式指标
    return Response(generate_latest(), mimetype='text/plain')

if __name__ == '__main__':
    # 一个 Flask 同时提供业务接口和 metrics 接口
    app.run(host='0.0.0.0', port=8000)
```

启动：

```bash
python3 /data/code/prometheus_metrics_demo.py
```

预期输出：

```text
 * Serving Flask app 'prometheus_metrics_demo'
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:8000
 * Running on http://10.0.0.12:8000
```

::: warning
Flask 自带的是**开发服务器**，生产环境请用 Gunicorn/uWSGI 等 WSGI 服务器启动，并配 systemd 管理、开机自启。例如：`apt -y install gunicorn && gunicorn -w 4 -b 0.0.0.0:8000 prometheus_metrics_demo:app`。
:::

##### 3.4.2.5 制造访问并观察指标

每访问一次根路径，`request_count_total` 增加 1。写压测脚本 `/data/code/curl_metrics.sh`：

```bash
cat > /data/code/curl_metrics.sh <<'EOF'
#!/bin/bash
while true; do
  sleep_num=$(($RANDOM%3+1))
  curl_num=$(($RANDOM%50+1))
  for c_num in $(seq $curl_num); do
    curl -s http://127.0.0.1:8000 >/dev/null 2>&1
  done
  sleep $sleep_num
done
EOF
chmod +x /data/code/curl_metrics.sh
nohup bash /data/code/curl_metrics.sh >/dev/null 2>&1 &
```

参数解释：`$RANDOM%3+1` 生成 1～3 的随机秒数；`seq N` 生成 1～N；`nohup ... &` 让脚本后台持续跑。

查看自定义指标：

```bash
curl -s http://127.0.0.1:8000/metrics | grep -A3 -E 'request_count|request_processing'
```

预期输出（数值不断增长）：

```text
# HELP request_processing_seconds Time spent processing request
# TYPE request_processing_seconds summary
request_processing_seconds_count 123.0
request_processing_seconds_sum 5.67
# HELP request_count_total Total request count
# TYPE request_count_total counter
request_count_total 123.0
```

##### 3.4.2.6 Prometheus 集成

回到**监控服务器**，编辑 `/usr/local/prometheus/conf/prometheus.yml` 追加：

```yaml
  - job_name: 'my_metric'
    static_configs:
      - targets:
          - '【应用服务器IP】:8000'
        labels:
          app: 'flask_web'
```

检查生效：

```bash
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus
```

浏览器 `http://【监控服务器IP】:9090/targets` 看到 `my_metric` 为 UP；Graph 查 `request_count_total` 有数据。常用速率查询：

```promql
rate(request_count_total{job="my_metric"}[5m])
irate(request_count_total{job="my_metric"}[5m])
```

记得在应用服务器放通 8000 端口（ufw/安全组）。

#### 3.4.3 Golang 实现自定义 Exporter

**第 1 步：安装 Go**

```bash
apt update && apt -y install golang
go version
```

**第 2 步：写代码**，创建 `/data/code/go-exporter/main.go`：

```go
package main

import (
	"net/http"

	"github.com/prometheus/client_golang/prometheus/promhttp"
)

func main() {
	// 在 /metrics 暴露默认注册表
	http.Handle("/metrics", promhttp.Handler())
	http.ListenAndServe(":9527", nil)
}
```

**第 3 步：配置国内 Go 代理并拉依赖**

```bash
cd /data/code/go-exporter
go env -w GOPROXY=https://goproxy.cn,direct
go mod init my_metric
go get github.com/prometheus/client_golang/prometheus/promhttp
go mod tidy
```

参数解释：`GOPROXY=https://goproxy.cn,direct` 用七牛云 Go 代理（`direct` 表示代理没有时回源）；**备选**阿里云 `https://mirrors.aliyun.com/goproxy/`。

**第 4 步：编译运行**

```bash
# 交叉编译环境变量（本机编译可省略）
export CGO_ENABLED=0 GOARCH=amd64 GOOS=linux
go build -o exporter_demo
./exporter_demo
```

验证（另开终端）：

```bash
curl -s http://127.0.0.1:9527/metrics | head -10
```

预期输出：

```text
# HELP go_gc_cycles_automatic_gc_cycles_total Count of completed GC cycles generated by the Go runtime.
# TYPE go_gc_cycles_automatic_gc_cycles_total counter
go_gc_cycles_automatic_gc_cycles_total 0
# HELP go_gc_duration_seconds A summary of the pause duration of garbage collection cycles.
# TYPE go_gc_duration_seconds summary
```

同样在 Prometheus 加一个指向 `【应用服务器IP】:9527` 的 job 即可。

---

### 3.5 基于 PromQL 在 Grafana 做自定义看板

#### 3.5.1 Grafana 基础回顾

- **数据源（Data Source）**：提供数据的存储系统；**仪表盘（Dashboard）**：组织面板（Panel）的容器；
- Grafana 支持 TSDB（Prometheus、InfluxDB）、日志（Loki、ES）、追踪（Jaeger、Zipkin）、SQL（MySQL、PostgreSQL）等数据源；
- 可视化样式有两种来源：**默认可视化类型**，以及用 `grafana-cli` 从插件市场安装的**可视化插件**。

插件市场地址：

```text
https://grafana.com/plugins/
```

#### 3.5.2 面板的操作菜单

把鼠标放到面板标题上，出现小三角，点开：

| 菜单项 | 作用 |
| --- | --- |
| View（快捷键 v） | 全屏查看面板 |
| Edit（快捷键 e） | 编辑面板（最常用） |
| Share | 分享面板（链接/快照/嵌入） |
| Explore（快捷键 x） | 到 Explore 页深入分析 |
| More | 复制、复制为、查看 JSON、导出 CSV、删除等 |

Edit 页底部四个配置图标：

| 图标 | 配置内容 |
| --- | --- |
| Query | 查询表达式（A、B、C 多个查询） |
| Visualize（Visualization） | 图形样式 |
| General | 标题、描述、透明等 |
| Alert | 面板告警（新版 Grafana 已转向统一告警，了解） |

#### 3.5.3 绘图案例：QPS、变化率、平均耗时三条曲线

**需求与对应 PromQL**：

```promql
# 1. 每分钟请求数量（QPS 曲线用速率，这里演示每分钟增量）
increase(request_count_total{job="my_metric"}[1m])

# 2. 每分钟请求量变化率（瞬时速率）
irate(request_count_total{job="my_metric"}[1m])

# 3. 请求处理平均耗时（总耗时 / 次数）
request_processing_seconds_sum{job="my_metric"}
  / request_processing_seconds_count{job="my_metric"}
```

**第 1 个面板的制作步骤**：

1. 点左侧 **+ → Dashboard → Add visualization**，选择 Prometheus 数据源；
2. 在 Query 区把第一条 PromQL 粘到查询框（Metrics）；
3. 设置 **Legend（图例）** 为 `{{instance}}_request_count`；
4. 点查询右侧的"小眼睛/刷新"预览，确认有曲线；
5. 切到 **Visualization**：默认就是 Time series（折线图）；可设置坐标轴、单位（如 none/short）、堆叠等；X 轴 Mode 默认按时间；
6. 切到 **General**：填面板标题；
7. 右上角 **Save dashboard**，命名保存。

::: tip
Legend 里 `{{instance}}` 会被替换成实际标签值；如果标签变量不生效，检查查询是否处于可刷新状态（点一次刷新/小眼睛）。
:::

**追加其余面板**：在 Dashboard 顶部点 **Add → Visualization**（Add panel），重复上面步骤做出第 2、3 个面板。

**调整布局**：拖动面板标题可移动位置；拖面板右下角小三角可改变大小；最后再 Save 一次。

**制作流程总结（通用 SOP）**：

1. 了解业务、分析要展示的指标；
2. 创建 Dashboard；
3. 逐个创建 Panel、写 PromQL；
4. 完善可视化样式、图例、单位；
5. 保存，需要时再加告警。

---

### 本阶段命令速查表

```bash
# === Python Exporter（app01）===
apt -y install python3 python3-pip python3-flask python3-prometheus-client
mkdir -p /data/code
# prometheus_metrics_demo.py 内容见 3.4.2.4，然后：
python3 /data/code/prometheus_metrics_demo.py
# 生产用 gunicorn：
apt -y install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 prometheus_metrics_demo:app

# pip 换源
pip3 config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# === Go Exporter ===
apt -y install golang
go env -w GOPROXY=https://goproxy.cn,direct
cd /data/code/go-exporter
go mod init my_metric
go get github.com/prometheus/client_golang/prometheus/promhttp
go build -o exporter_demo && ./exporter_demo

# === Prometheus 每次改配置 ===
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus

# === 命令行查指标（不打开浏览器）===
curl -s http://127.0.0.1:9100/metrics | grep node_load1
```

**PromQL 速记**：

```promql
# 主机 CPU 使用率（按实例）
100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)
# 内存使用率
(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100
# 根分区使用率
100 * (1 - node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"})
# 系统负载（按 CPU 核数归一）
node_load1 / count by (instance) (node_cpu_seconds_total{mode="idle"})
# QPS
sum by (instance) (rate(request_count_total[5m]))
# P99 延迟
histogram_quantile(0.99, sum by (le) (rate(xxx_bucket[5m])))
```

---

### 本阶段常见坑与解决

**坑 1：范围向量直接画图**

- 报错原样：`invalid expression type "range vector" for range query, must be Scalar or instant Vector`。
- 原因：Graph 只吃即时向量。
- 解决：外面套函数，如 `rate(指标[5m])`、`increase(指标[5m])`、`avg_over_time(指标[5m])`。

**坑 2：rate 忘了加 [区间]**

- 报错原样：`parse error: expected type range vector in call to function "rate", got instant vector`。
- 解决：参数必须是范围向量 `rate(指标[5m])`。

**坑 3：正则写成"包含"逻辑**

- 现象：`{instance=~"10.0.0.1"}` 匹配不到 `10.0.0.11`，或 `{method=~"^ge"}` 匹配不到 `get`。
- 原因：PromQL 正则是整串完全锚定。
- 解决：补 `.*`，如 `instance=~"10.0.0.1.*"`、`method=~"ge.*"`。

**坑 4：Summary 分位数无法聚合**

- 现象：`avg(go_gc_duration_seconds{quantile="0.99"})` 算出来的"全局 P99"没有统计意义。
- 原因：分位数不能跨实例算术平均。
- 解决：需要全局分位请改用 Histogram，聚合桶后用 `histogram_quantile`。

**坑 5：pip / go 拉包超时**

- 报错原样：`ReadTimeoutError: HTTPSConnectionPool(host='pypi.org', port=443): Read timed out`；Go 报 `dial tcp: lookup proxy.golang.org: no such host` 或超时。
- 解决：pip 用清华/阿里源；Go 用 `goproxy.cn`；命令见速查表。

**坑 6：Flask 开发服务器直接上生产**

- 现象：高并发下性能差、警告 `This is a development server`。
- 解决：用 Gunicorn/uWSGI 启动并配 systemd、开机自启、Restart。

**坑 7：Grafana Legend 不显示标签值**

- 现象：图例显示成整条 PromQL 语句。
- 解决：Legend 填 `{{标签名}}`，如 `{{instance}}`，并刷新查询。

**坑 8：除法两侧结构不匹配导致空结果**

- 现象：写了占比查询但没有任何输出，也不报错。
- 原因：左右向量标签集不同、无法配对。
- 解决：两侧用 `sum ... by (相同标签)` 聚合成相同维度，或用 `ignoring/group_left` 明确匹配规则。

**坑 9：自定义指标没写 # TYPE，类型为 untyped**

- 现象：指标存在但类型显示 untyped，部分函数/看板行为异常。
- 解决：客户端库正常使用 Counter/Gauge 对象即可自动生成 TYPE；手写文本时补上 `# TYPE 名字 counter/gauge/...`。

---
