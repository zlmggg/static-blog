# Grafana Loki logcli 详解：命令行查日志（LogQL）

> 本文是 [云原生排障命令速查](../cloudnative-commands) 中「日志与链路查询」里 Loki/LogQL 部分的从 0 到 1 详解，本篇一次讲清 `logcli query`、标签选择器、`|=`/`|~`/`json` 解析，以及 `rate`/`count_over_time` 等量化函数。
> 目标：不在 Grafana UI 里点，直接在终端用 LogQL 把某服务最近的错误日志揪出来。
> 环境依据：Grafana Loki 3.7 / LogCLI（站内 2026-09 基准）。本沙箱未装，命令据 Grafana Loki 官方 LogCLI 与 LogQL 文档核对，示例标注「据官方文档」。

## 一、命令是干什么的

Loki 是 Grafana 出的**日志聚合系统**，和 Elastic 不同：它只给日志流打**标签（label）**做索引，日志正文本身不建索引（便宜）。查日志用的查询语言叫 **LogQL**——长得像 PromQL。

`logcli` 是 Loki 官方的命令行客户端，让你在终端/脚本里跑 LogQL，不用开浏览器。典型排障：

- 某服务最近在报什么错？→ `logcli query '{job="api"} |= "error"'`
- 实时跟某个 Pod 的日志？→ `logcli query --tail '{container="api"}'`
- 错误率有多高？→ `rate({job="api"} |= "error"[5m])`

> 类比：Loki 像「只给书贴分类标签、不逐页建索引」的图书馆；LogQL 就是「先按标签挑书架（`{job=...}`），再在书里翻关键词（`|=`）」。`logcli` 是这个图书馆的自助检索终端。

## 二、命令语法

```bash
logcli [全局连接选项] query '<LogQL>' [查询选项]
logcli labels [标签名]
```

- 全局连接：`--addr`（Loki 地址）、`--username`/`--password`（基础认证）、`--tls-skip-verify`；
- 查询选项控制时间范围与输出。

最简单：

```bash
logcli query '{job="api"}'
```

## 三、选项全表（对照官方 LogCLI 文档）

### 1. 全局连接选项

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `--addr=URL` | Loki 地址（也可 `LOKI_ADDR` 环境变量） | 连自托管 Loki |
| `--username`/`--password` | 基础认证 | Loki 开了认证 |
| `--tls-skip-verify` | 跳过 TLS 校验 | 自签证书排障 |
| `-o`，`--output` | 输出格式：`raw`/`json`/`default` | 要机器可读用 `json` |

### 2. `logcli query` 查询选项

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `'<LogQL>'`（位置参数） | LogQL 查询语句 | 核心 |
| `--since=1h`，`-s 1h` | 查最近多久（如 `15m`/`1h`/`24h`） | 限定时间窗（最常用） |
| `--from`/`--to` | 指定起止时间（RFC3339） | 查历史某段 |
| `--tail`，`-f` | **实时跟随**新日志（类似 tail -f） | 盯实时报错 |
| `--limit=N` | 返回最多 N 条（默认 100） | 结果太多时收窄 |
| `--forward` | 按**时间正序**输出（默认倒序，最新在前） | 想从头顺时间线读 |
| `--stats` | 额外打印查询统计（扫了多少字节） | 慢查询优化时 |
| `--step` | 量化函数的聚合步长 | `rate()` 画图/聚合时 |

### 3. LogQL 语法（查询语句本身）

| 写法 | 含义 | 什么场景用 |
|---|---|---|
| `{job="api"}` | **标签选择器**，选出日志流 | 先圈定服务/容器 |
| `{job="api"} |= "error"` | 行过滤：只留含 `error` 的行 | 找错误 |
| `{job="api"} \|~ "5[0-9]{2}"` | 正则过滤：匹配 5xx 状态码 | 模糊匹配 |
| `{job="api"} \|= "" != "health"` | 组合：含某词且不含某词 | 排除健康检查噪音 |
| `{job="api"} \| json` | 把 JSON 日志**解析成字段** | 结构化日志取字段 |
| `{job="api"} \| label_format level="level"` | 提取字段为标签 | 按 level 聚合 |
| `rate({job="api"}[5m])` | 量化函数：每秒日志条数 | 看流量/错误率 |
| `count_over_time({job="api"}[5m])` | 量化函数：窗口内总行数 | 统计日志量 |

## 四、由浅入深的典型示例

以下示例「据官方文档」或示意。

### 示例 1：列出有哪些标签

```bash
logcli labels
logcli labels job
```

```text
job
container
namespace
```

> 不知道标签名时先 `labels` 探一下，再写选择器。

### 示例 2：查某服务最近 15 分钟日志

```bash
logcli query --since=15m '{job="api"}'
```

```text
2026-09-30T10:00:05Z {job="api"}  incoming GET /pay 200
2026-09-30T10:00:06Z {job="api"}  incoming GET /health 200
```

> 默认倒序（最新在前）；加 `--forward` 变正序。

### 示例 3：只看含 error 的行

```bash
logcli query --since=15m '{job="api"} |= "error"'
```

```text
2026-09-30T10:01:11Z {job="api"}  error: connection refused to db:5432
```

> `|=` 是子串过滤；`|~` 才是正则。

### 示例 4：正则匹配 5xx

```bash
logcli query --since=5m '{job="api"} |~ "status=5[0-9]{2}"'
```

> 找所有 5xx 响应。

### 示例 5：实时跟随

```bash
logcli query --tail '{container="api"}'
```

> 像 `kubectl logs -f`，但跨所有副本/按标签聚合。

### 示例 6：解析 JSON 日志并按字段过滤

```bash
logcli query --since=10m '{job="api"} | json | level="error"'
```

```text
{job="api"} {"ts":"...","level":"error","msg":"db timeout","status":500}
```

> `| json` 把每行解析成结构化字段，后面就能用 `level="error"` 这种字段过滤。

### 示例 7：算错误率（量化查询）

```bash
logcli query --step=30s 'sum(rate({job="api"} |= "error"[5m])) by (namespace)'
```

```text
Time series: {namespace="prod"}
[10:00] 0.2
[10:05] 1.7
```

> `rate()` 返回的是时序，不是单行日志；用 `--step` 控制粒度。

### 示例 8：统计日志总量

```bash
logcli query --since=1h 'count_over_time({job="api"}[1h])'
```

> 一小时打了多少行日志。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `logcli query --since=15m '{job="api"}'` | 最近日志 |
| `logcli query -f '{job="api"}'` | 实时跟随 |
| `logcli query '{job="api"} \|= "error"'` | 找错误行 |
| `logcli query '{job="api"} \|~ "5[0-9]{2}"'` | 正则匹配 5xx |
| `logcli query '{job="api"} \| json'` | 解析 JSON |
| `logcli query 'rate({job="api"}[5m])'` | 日志速率 |
| `logcli labels` | 探标签名 |
| `logcli query -o json ...` | 机器可读输出 |

## 六、RHEL 系与 Debian 系差异

logcli 是单个 Go 二进制，**两系用法一致**，只取决于 Loki 服务端版本：

- 两系都从 Grafana 官方 Release 下 `logcli` 二进制；
- 连接方式靠 `--addr` 或 `LOKI_ADDR` 环境变量，与 OS 无关；
- LogQL 语法随 Loki 版本演进，新函数（如新的量化函数）老服务端可能不认，以你连接的 Loki 版本为准。

## 七、新手易错点

1. **先写标签选择器 `{...}` 再过滤正文**：LogQL 必须以标签选择器开头；直接 `|= "error"` 不报标签会扫全量、极慢。
2. **`|=` 是子串、`|~` 是正则**：混用会查不到或语法错。
3. **默认倒序 + 最新在前**：想顺着时间线读加 `--forward`；时间窗用 `--since` 别全量查。
4. **没加时间范围会很慢/超时**：Loki 不索引正文，大范围扫很吃 IO，排障先用 `--since` 收窄。
5. **`| json` 只对 JSON 格式日志有效**：非结构化日志解析不出字段。
6. **危险/开销提示**：宽时间窗 + 高基数标签 + 复杂正则会拖垮 Loki 前端；生产排障别用 `{job=~".+"}` 这种全匹配长时间查，用完即停。

## 八、相关命令与文档

- 速查页：[云原生排障命令速查](../cloudnative-commands)
- Collector 把日志送进来：[otelcol](./otelcol)
- 链路查询：[tempo](./tempo)
- 日志体系概念：[Grafana 监控栈](../../guide/monitor-grafana-stack)
- 官方文档：https://grafana.com/docs/loki/latest/query/ ；LogCLI：https://grafana.com/docs/loki/latest/query/logcli/
