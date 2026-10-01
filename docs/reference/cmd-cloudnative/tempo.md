# Grafana Tempo 与 TraceQL 详解：查链路（含 Jaeger API）

> 本文是 [云原生排障命令速查](../cloudnative-commands) 中「日志与链路查询」里 Tempo/TraceQL 与 Jaeger 部分的从 0 到 1 详解，本篇一次讲清 TraceQL 选择器（`{ resource.service.name=... }`、`.error`、`duration`、span 条件、metrics）与 Jaeger（API `/api/traces`、UI 16686）。
> 目标：一次线上慢/错请求，能用 TraceQL 把那条 trace 捞出来、看出哪一跳最慢/最错。
> 环境依据：Grafana Tempo 3.0（站内 2026-09 基准；TraceQL metrics 已 GA）。本沙箱未装，语法据 Grafana Tempo 官方 TraceQL 文档核对，示例标注「据官方文档」。

## 一、命令是干什么的

分布式追踪（tracing）记录一个请求穿过多个服务（api → order → db）的全过程，每一跳叫一个 **span**，整棵 span 树叫一个 **trace**。

- **Tempo**：Grafana 出的 trace 后端，便宜、跟 Grafana/Loki 打通；查询语言叫 **TraceQL**；
- **TraceQL**：像 LogQL/PromQL 一样，用花括号选择器挑 trace，支持按服务、错误、耗时、span 属性过滤；
- **Jaeger**：另一套成熟追踪后端/UI，有自己的查询 API（`:16686/api/...`）。

排障核心问题：「某个慢请求/错误请求到底卡在哪个服务？」→ 用 TraceQL 选出 `error=true` 或 `duration>1s` 的 trace，点开看 span 树。

> 类比：trace 像一次「跨部门工单的流转录像」，每个 span 是一个部门处理的时间戳。TraceQL 就是按「哪个服务、出错没、花了多久」把这盘录像调出来。

## 二、命令语法

TraceQL 不是独立二进制命令，而是在 Grafana Explore / Tempo 查询接口里跑的**查询语句**；命令行/脚本里用 Tempo 或 Jaeger 的 HTTP API 发查询。

```bash
# Tempo TraceQL（通过查询接口/Grafana）
{ 选择条件 }

# Jaeger HTTP API
curl 'http://<tempo|jaeger>:16686/api/traces?service=<服务名>'
```

## 三、TraceQL 选择器语法（对照官方文档）

### 1. 按资源/服务/属性选 trace

| 查询 | 含义 | 什么场景用 |
|---|---|---|
| `{ resource.service.name = "api" }` | 选某服务产生的 trace | 先圈定服务 |
| `{ span.http.route = "/pay" }` | 按 span 的 HTTP 路由选 | 只看某个接口 |
| `{ .error = true }` | 选**出错**的 trace | 找失败请求（最常用） |
| `{ span.http.status_code >= 500 }` | 选含 5xx span 的 trace | 找服务端错误 |
| `{ duration > 1s }` | 选**慢** trace（整根 trace 耗时） | 找慢请求 |
| `{ resource.service.name="api" && span.http.route="/pay" }` | `&&` 组合条件 | 服务 + 接口双重过滤 |

> TraceQL 里：`resource.*` 是 span 所属**资源**标签（service.name、deployment 等）；`span.*` 是 span 自带属性（http.status_code、http.route）；`.` 是简写根。

### 2. TraceQL metrics（从 trace 算指标）

| 查询 | 含义 |
|---|---|
| `rate({ resource.service.name="api" }[5m])` | 每秒钟该服务产生多少 trace |
| `count_over_time({ .error = true }[5m])` | 5 分钟内出错 trace 数 |
| `histogram_quantile(0.99, ...)` | 延迟分位（配合 span 时长） |

> 官方：TraceQL metrics 让你直接用 trace 数据算 Prometheus 风格指标，3.0 已 GA；需 Parquet 块格式（Tempo 默认）。

### 3. Jaeger 查询 API

| 操作 | 含义 |
|---|---|
| `GET /api/services` | 列出有哪些服务 |
| `GET /api/traces?service=X&limit=20` | 查某服务的 trace |
| `GET /api/traces/{traceID}` | 按 trace ID 取整条 |
| UI `http://host:16686` | 浏览器按服务/操作/tag 查 |

## 四、由浅入深的典型示例

以下查询「据官方文档」或示意，在 Grafana Explore / Tempo 查询框执行。

### 示例 1：选出错的 trace

```
{ .error = true }
```

> 排障第一步：把所有失败请求捞出来，定位事故面。

### 示例 2：只看某服务的错误

```
{ resource.service.name = "api" && .error = true }
```

> `&&` 组合：api 服务里出错的 trace。

### 示例 3：找慢请求

```
{ resource.service.name = "api" && duration > 1s }
```

> 找出耗时超过 1 秒的 trace，点开看哪一跳慢。

### 示例 4：按 HTTP 状态码过滤

```
{ span.http.status_code >= 500 }
```

> 找出含 5xx span 的整条 trace。

### 示例 5：组合接口 + 错误

```
{ resource.service.name = "api" && span.http.route = "/pay" && .error = true }
```

> 精准定位：api 服务里 /pay 接口出错的 trace。

### 示例 6：用 TraceQL metrics 看错误率

```
rate({ resource.service.name="api" && .error=true }[5m])
```

> 从 trace 直接算错误率时序，可在 Grafana 里画图/告警。

### 示例 7：Jaeger API 拉某服务 trace

```bash
curl 'http://jaeger-query:16686/api/traces?service=api&limit=20'
```

```text
{"data":[{"traceID":"abc123","spans":[...]}],"total":20,"limit":20,"offset":0}
```

### 示例 8：Jaeger UI

```text
浏览器打开 http://<jaeger-query>:16686
```

> 选 Service → Find Traces → 点某条进 Gantt 图看 span 树。

## 五、高频组合速记

| 查询 | 用途 |
|---|---|
| `{ .error = true }` | 选出错 trace |
| `{ resource.service.name="api" }` | 圈定服务 |
| `{ duration > 1s }` | 找慢 trace |
| `{ span.http.status_code >= 500 }` | 找 5xx |
| `rate({ ... }[5m])` | 从 trace 算速率 |
| `curl ...:16686/api/services` | Jaeger 列服务 |
| 浏览器 `:16686` | Jaeger UI |

## 六、RHEL 系与 Debian 系差异

Tempo/Jaeger 都是服务端组件，查询语句与 OS 无关；两系部署方式不同（容器/systemd）但查询语法一致。注意：

- TraceQL 语法随 Tempo 版本演进，metrics 类查询需 Tempo 3.x + Parquet 后端；
- Jaeger 的查询端口 `16686` 是 query 服务，与 OTLP 接收端口（4317/4318）分开；
- 命令行里用 API 查询时，记得带 `service` 必填参数。

## 七、新手易错点

1. **TraceQL 条件写在花括号里**：`{ .error = true }`，不是 LogQL 那种反引号；多个条件用 `&&`。
2. **`resource.*` 和 `span.*` 别混**：service.name 在 resource 上；http.status_code 在 span 上。写错路径查不到。
3. **TraceQL metrics 需要 Parquet**：老块格式不支持 metrics 查询，报格式错。
4. **Jaeger API 的 `service` 必填**：不带 service 参数查不到东西。
5. **UI 16686 是 query 前端**：它后面连着存储后端；UI 打不开先查 query 服务本身，不是存储。
6. **危险/开销提示**：大时间窗 + 高基数 TraceQL 会扫描大量块、压后端；生产排障先用服务/错误条件收窄，别全量扫。

## 八、相关命令与文档

- 速查页：[云原生排障命令速查](../cloudnative-commands)
- 日志查询：[logcli](./logcli)
- 采集端 Collector：[otelcol](./otelcol)
- 可观测体系：[OpenTelemetry 指南](../../guide/monitor-opentelemetry)
- 官方文档：https://grafana.com/docs/tempo/latest/traceql/ ；Jaeger：https://www.jaegertracing.io/docs/latest/apis/
