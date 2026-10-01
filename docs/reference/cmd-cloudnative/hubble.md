# Hubble observe 详解：实时看 Pod 间网络流

> 本文是 [云原生排障命令速查](../cloudnative-commands) 中「Cilium 与 eBPF」里 Hubble 部分的从 0 到 1 详解，本篇一次讲清 `hubble observe`（`--namespace`/`--protocol`/`--verdict`/`--http-path`/`-f`）、Hubble Relay 与 UI、以及流（flow）字段。
> 目标：Pod A 调 Pod B 不通/被拒时，用 hubble 实时看到这条流是通是断、走的什么协议、哪一跳被策略挡了。
> 环境依据：Cilium 1.20 自带 Hubble（官方文档 1.20.2，2026-09-15 更新）。本沙箱未装，选项据 Cilium/Hubble 官方文档核对，示例标注「据官方文档」。

## 一、命令是干什么的

Hubble 是 Cilium 自带的**网络可观测**组件：它把 Cilium 在内核里看到的每一条 Pod 间流量（源/目的、协议、 verdict：转发还是丢、HTTP 状态码）抽成「流（flow）」事件，供你实时观察。

- `hubble` CLI 默认连**本节点** cilium-agent 暴露的 Hubble API（unix socket）；
- 要跨节点看全集群，得部署 **Hubble Relay**，CLI 指向 Relay；
- **Hubble UI** 是 Web 服务依赖图。

排障问题：「这个请求到底发出去没有？是被网络策略 DROP 了，还是对端没起？」→ `hubble observe` 实时抓流。

> 类比：`cilium monitor` 是内核级原始包日志；Hubble 是它的「人话版」——直接告诉你 `谁(pod) -> 谁(pod)，TCP/HTTP，通了还是被拒，HTTP 几几几`。

## 二、命令语法

```bash
hubble observe [过滤选项] [--follow]
hubble list / hubble status / hubble ui
```

- 默认打印最近一段时间的流；加 `-f`/`--follow` 持续跟；
- 用 `-n` 指定命名空间、`-p` 指定协议、`--verdict` 指定结论。

最简单：

```bash
hubble observe
```

## 三、选项全表（对照官方 Hubble 文档）

### 1. `hubble observe` 过滤选项

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-f`，`--follow` | 持续**跟随**新流（不退出） | 实时盯（最常用） |
| `-n NS`，`--namespace=NS` | 只看某命名空间的流 | 收窄范围 |
| `-p PROTO`，`--protocol=PROTO` | 按协议过滤：`TCP`/`UDP`/`HTTP`/`DNS`/`ICMP` | 只看 HTTP 层 |
| `--verdict=VERDICT` | 按结论过滤：`FORWARDED`/`DROPPED`/`ERROR` | **只看被 DROP 的**（排策略最有用） |
| `--http-path=/x` | 按 HTTP 路径过滤 | 只看某个接口 |
| `--http-status=500` | 按 HTTP 状态码 | 找 5xx |
| `--type` | 流类型（L3/L4/L7） | 分层看 |
| `--label key=value` | 按源/目的标签过滤 | 按服务选 |
| `--last=N` | 看最近 N 条流（不 follow） | 先看历史几条 |
| `--since=1m` | 看最近多久的流 | 时间窗 |
| `-o FORMAT`，`--output` | 输出 `table`/`json`/`compact` | 要机器可读用 `json` |
| `--host=ADDR` | 连哪个 Hubble/Relay 地址 | 跨节点/连 Relay |

### 2. Hubble 配套命令

| 命令 | 作用 |
|---|---|
| `hubble status` | 确认 CLI 与 Hubble API/Relay 连通 |
| `hubble list nodes` | 列出 Hubble 可见的节点 |
| `hubble ui` | 本地起端口转发打开 Hubble UI |

## 四、由浅入深的典型示例

以下输出「据官方文档」或示意。

### 示例 1：先确认 Hubble 通

```bash
hubble status
```

```text
Healthcheck via gRPC client to localhost:4244: OK
Current/Max Flows: 1234/65535 (1.9%)
```

> 连不上就是 Hubble API 没起/relay 没配。

### 示例 2：实时看全节点流

```bash
hubble observe --follow
```

```text
Nov 30 10:00:01.123: frontend-xxx:54324 -> api-yyy:8080 TCP FORWARDED (TCP Flags: SYN)
Nov 30 10:00:01.124: api-yyy:8080 -> frontend-xxx:54324 TCP FORWARDED (TCP Flags: SYN, ACK)
Nov 30 10:00:01.130: frontend-xxx:54324 -> api-yyy:8080 HTTP GET /api/pay => 200 (0.1ms)
```

> 每条流告诉你：时间、源 Pod:端口 → 目的 Pod:端口、协议、verdict。

### 示例 3：只看被丢的包（策略误拦）

```bash
hubble observe --follow --verdict DROPPED
```

```text
... frontend-xxx -> db-zzz:5432 TCP DROPPED (Policy denied)
```

> 看到 `DROPPED (Policy denied)` 就是网络策略挡的；去 Cilium 策略里放行。

### 示例 4：只看某命名空间的 HTTP 流

```bash
hubble observe --follow --namespace prod --protocol http
```

> 过滤到 prod 命名空间、只看 L7 HTTP。

### 示例 5：按 HTTP 路径过滤

```bash
hubble observe --follow --namespace prod --http-path /pay
```

> 只看打向 /pay 的请求及其状态码。

### 示例 6：JSON 输出喂脚本

```bash
hubble observe --last=100 -o json
```

```text
{"flow":{"source":{"namespace":"prod","pod_name":"frontend"},"destination":{"namespace":"prod","pod_name":"api"},"l4":{"TCP":{}},"verdict":"FORWARDED"}}
```

### 示例 7：跨节点连 Relay

```bash
hubble observe --follow --host=hubble-relay.kube-system:4245 --namespace prod
```

> 不装 Relay 时只能看本节点流；装了 Relay 后 `--host` 指向 Relay，看全集群。

### 示例 8：打开 UI

```bash
hubble ui
```

> 自动端口转发并在浏览器打开 Hubble 服务依赖图。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `hubble status` | 确认连通 |
| `hubble observe -f` | 实时看流 |
| `hubble observe -f --verdict DROPPED` | 只看被拒 |
| `hubble observe -f -n prod -p http` | 命名空间+HTTP |
| `hubble observe -f --http-path /pay` | 看某接口 |
| `hubble observe --last=100 -o json` | 历史流 JSON |
| `hubble ui` | 打开依赖图 |

## 六、RHEL 系与 Debian 系差异

Hubble 随 Cilium 部署在 K8s 内，`hubble` CLI 用法与 OS 无关。差异在：

- 单机 Hubble API 监听 unix socket（CLI 默认连）；跨节点必须 Hubble Relay；
- CLI 版本要和 Cilium 版本大对齐；
- 节点 OS 内核版本影响能观测到的 L7 信息（HTTP 可见性需相应内核/Cilium 能力）。

## 七、新手易错点

1. **只能看本节点流**：不装 Relay，`hubble observe` 只看到本 cilium-agent 的流量；跨节点查要配 Relay。
2. **连不上先 `hubble status`**：多半是 Hubble 没启用或 relay 地址不对。
3. **`--verdict DROPPED` 是排策略神器**：请求不通先抓 DROPPED，区分「策略挡」还是「对端没起」。
4. **flow 里的 Pod 名是源/目的工作负载**：看清楚方向，别把请求方向读反。
5. **HTTP 流需要 L7 可见性开启**：没开时 `--protocol http` 抓不到应用层路径，只有 TCP 五元组。
6. **危险/开销提示**：`observe -f` 持续打流、量大；生产排障加好过滤（命名空间/verdict/protocol），用完即 Ctrl-C，别裸跑全量。

## 八、相关命令与文档

- 速查页：[云原生排障命令速查](../cloudnative-commands)
- Cilium 整体排障：[cilium](./cilium)
- 服务网格网络对照：[container-servicemesh 指南](../../guide/container-servicemesh)
- eBPF：[Linux eBPF 指南](../../guide/linux-ebpf)
- 官方文档：https://docs.cilium.io/en/stable/observability/hubble/
