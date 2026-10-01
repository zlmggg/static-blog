# OpenTelemetry Collector 排障详解：otelcol / otelcol-contrib

> 本文是 [云原生排障命令速查](../cloudnative-commands) 中「OpenTelemetry Collector」一组命令的从 0 到 1 详解，本篇一次讲清启动参数（`--config`/`--validate`/`--log-level`）、自身 metrics :8888、zpages :55679、pprof、OTLP 4317/4318，以及 receivers/processors/exporters/connectors 排障思路。
> 目标：Collector 收上来的 traces/metrics/logs 丢了或错了，知道从它自己的哪个端口、哪块配置查起。
> 环境依据：OpenTelemetry Collector v0.162（站内 2026-09 基准）。说明：opentelemetry.io 官方安装页当前示例版本号渲染为 0.132.0（页面长期未更新示例数字），命令行参数与端口映射在各小版本一致；本沙箱未装，端口与参数据官方安装文档核对。

## 一、命令是干什么的

OpenTelemetry Collector 是收/处理/导出遥测数据（trace、metric、log）的中转代理。它用一个 YAML 配置文件描述管道：

- **receivers**（接收端）：数据从哪进来（OTLP、jaeger、prometheus、filelog…）；
- **processors**（处理端）：进来后做什么（批量、采样、属性加工、过滤…）；
- **exporters**（导出端）：发到哪去（OTLP、Prometheus、Loki、Tempo…）；
- **connectors**（连接器）：把一个管道的输出当另一个管道的输入；
- **service**：把上面按 pipeline 串起来，并配 Collector 自身的遥测（metrics/zpages/pprof）。

排障核心问题：「数据到底收没收到、处理了没、导出成功没？」——主要靠 Collector **自己暴露的观测端口**，而不是瞎猜。

> 类比：Collector 像一个「物流中转仓」：receivers 是收货口、processors 是分拣流水线、exporters 是发货口。它自己门口挂了块「经营看板」（:8888 指标）告诉你收了多少、发了多少、退了多少货。

## 二、命令语法

```bash
otelcol [--config=配置文件] [--validate] [--log-level=...] [其他全局flag]
otelcol-contrib [同样的flag]
```

- `otelcol`：官方核心发行版，只含稳定组件；
- `otelcol-contrib`：社区贡献发行版，**组件多得多**（额外 receivers/processors/exporters），生产上常用这个。

最简单：

```bash
otelcol --config=config.yaml
```

## 三、选项全表（对照官方安装/运行文档）

### 1. 启动全局选项

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `--config=FILE` | 指定配置文件（可多个，合并） | 启动必带；systemd 默认 `/etc/otelcol/config.yaml` |
| `--validate` | **只校验配置**是否合法，不真正启动 | 改完 YAML 先校验，别直接重启崩了 |
| `--log-level=LEVEL` | 日志级别：`debug`/`info`/`warn`/`error` | 排障临时开 `debug` 看每条数据细节 |
| `--set k=v` | 命令行覆盖配置里某个值 | 临时改一个 endpoint 不改正文 |
| `--feature-gates=gate` | 开关实验特性 | 用新组件时 |
| `--help` | 看全部 flag | 确认本机版本支持哪些 |

> 安装后 systemd 单元默认带 `--config=/etc/otelcol/config.yaml`；自定义参数写到 `/etc/otelcol/otelcol.conf` 的 `OTELCOL_OPTIONS`。

### 2. Collector 自身暴露的端口（据官方 docker-compose 端口表）

| 端口 | 用途 | 排障时怎么用 |
|---|---|---|
| **4317** | OTLP **gRPC** 接收/导出 | 应用用 gRPC 发数据到这里 |
| **4318** | OTLP **HTTP** 接收/导出 | 应用用 HTTP 发数据到这里（路径 `/v1/traces` 等） |
| **8888** | Collector **自身 Prometheus metrics** | `curl localhost:8888/metrics` 看收/发/拒绝条数 |
| 8889 | Prometheus exporter 自身指标 | 区分「Receiver 指标」与「导出器指标」 |
| 13133 | **health_check** 扩展 | `curl localhost:13133` 看健康 |
| 55679 | **zpages** 扩展 | 浏览器/curl 看管道活跃 trace 与错误 |
| 1888 | **pprof** 扩展（contrib 镜像默认暴露） | 性能采样 |

> 注意：metrics 端口地址在配置 `service.telemetry.metrics.address` 里，默认 `0.0.0.0:8888`；zpages/pprof 要在 `extensions:` 里显式声明并在 `service.extensions` 引用才生效。

### 3. 四类组件的排障关注点

| 组件类 | 排障看什么 |
|---|---|
| receivers | 数据收没收到：自身 metrics 里 `receiver_accepted_spans/metrics_log_records` 是否在涨 |
| processors | 处理丢没丢：`processor_refused/processed` 计数，batch/sampler 行为 |
| exporters | 导出成功没：`exporter_sent_*` 与 `exporter_failed_*`——**导出失败先看 failed 是否在涨** |
| connectors | 跨管道接线是否生效 |

## 四、由浅入深的典型示例

以下命令可直接在 Collector 所在主机/容器内执行；输出为示意。

### 示例 1：启动前先校验配置

```bash
otelcol --config=config.yaml --validate
```

```text
Config validation successful.
```

> YAML 缩进/字段名错时这里会报行号；CI 与改配置后必跑，避免重启才发现。

### 示例 2：前台启动并开 debug 日志

```bash
otelcol --config=config.yaml --log-level=debug
```

> debug 会打印每个管道接收/处理/导出的数据细节，量极大；**生产用完即关**。

### 示例 3：看 Collector 自身处理指标

```bash
curl -s localhost:8888/metrics | grep -E "receiver|exporter" | grep -E "accepted|sent|failed"
```

```text
otelcol_receiver_accepted_spans{...} 1234
otelcol_exporter_sent_spans{...} 1200
otelcol_exporter_send_failed_spans{...} 34
```

> `accepted` 在涨、`sent` 也在涨说明链路通；`failed` 在涨就是后端（Tempo/Loki）拒收或网络问题。

### 示例 4：用 zpages 看活跃 trace 与错误

```bash
curl -s localhost:55679/debug/zpriority 2>/dev/null || curl -s localhost:55679/debug/tracez
```

> zpages 页面列出正在处理的 span 和最近错误；前提是配置里 `extensions: [zpages]` 且 `service.extensions` 包含它。

### 示例 5：抓 pprof 性能画像

```bash
curl -s localhost:1888/debug/pprof/
# 或抓 CPU  profile：
go tool pprof http://localhost:1888/debug/pprof/profile
```

> Collector CPU/内存高时用 pprof 定位是哪个 processor。

### 示例 6：手动投递一条 OTLP 数据验证导出链路

```bash
curl -X POST localhost:4318/v1/traces -H "Content-Type: application/json" -d @trace.json
```

> gRPC 端点是 4317，HTTP 是 4318（路径 `/v1/traces`/`/v1/metrics`/`/v1/logs`）。手动打一条，再去看后端有没有收到，最快定位是「采集端没发」还是「Collector→后端」断了。

### 示例 7：用 --set 临时改导出端点

```bash
otelcol --config=config.yaml --set exporters::otlp::endpoint=tempo-backend:4317
```

> 不改正文 YAML，临时指一个后端验证。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `otelcol --config=c.yaml --validate` | 校验配置 |
| `otelcol-contrib --config=c.yaml` | 启动（组件全） |
| `--log-level=debug` | 临时打细节日志 |
| `curl localhost:8888/metrics` | 看收/发/失败计数 |
| `curl localhost:55679/debug/tracez` | zpages 看活跃 trace |
| `curl localhost:13133` | 健康检查 |
| `curl localhost:4318/v1/traces -d @x.json` | 手动验证 OTLP |

## 六、RHEL 系与 Debian 系差异

Collector 官方为两系都提供 `deb`/`rpm` 包，**配置与命令完全一致**，只是默认配置路径：

- Debian/Ubuntu（deb 包）：`/etc/otelcol/config.yaml`；
- RHEL/Rocky（rpm 包）：同样 `/etc/otelcol/config.yaml`；
- 系统服务名 `otelcol`/`otelcol-contrib`，用 `systemctl restart`、`journalctl -u otelcol` 看日志；
- 发行版仓库里的版本可能旧，生产排障建议用官方 Release 二进制/镜像对齐版本。

## 七、新手易错点

1. **忘了在 `service.extensions` 里引用扩展**：配置了 `zpages`/`pprof`/`health_check` 但没在 service 里挂上，端口就是不通。
2. **4317 是 gRPC、4318 是 HTTP**：应用协议和端点对不上会连不上；HTTP 要带 `/v1/traces` 路径。
3. **`--validate` 通过不代表能跑**：它只校验配置语法；连不连得通后端要靠 metrics。
4. **导出失败先看 `exporter_failed`**：别一上来怀疑采集端；多数丢数据是后端拒收/限流。
5. **危险/开销提示**：`--log-level=debug`、开 pprof、抓 tracez 都有明显性能与日志开销，生产排障用完即关、别长期开。
6. **otelcol vs otelcol-contrib**：用了 contrib 专属 receiver/processor，却拿核心 `otelcol` 启动，会报「未知组件」；组件对号入座。

## 八、相关命令与文档

- 速查页：[云原生排障命令速查](../cloudnative-commands)
- 日志怎么查：[logcli](./logcli)
- 链路怎么查：[tempo](./tempo)
- 可观测体系概念：[OpenTelemetry 指南](../../guide/monitor-opentelemetry)
- 官方文档：https://opentelemetry.io/docs/collector/ ；安装与端口：https://opentelemetry.io/docs/collector/installation/
