# Cilium 排障命令详解：status / endpoint / policy / connectivity / monitor

> 本文是 [云原生排障命令速查](../cloudnative-commands) 中「Cilium 与 eBPF」一组命令的从 0 到 1 详解，本篇一次讲清 `cilium status(--verbose)`、`endpoint list/get`、`policy get/validate`、`connectivity test`、`monitor`，以及 Hubble 怎么启用。
> 目标：Cilium 网络插件装完，Pod 之间不通/策略不生效时，用 cilium CLI 从健康、端点、策略三个层面定位。
> 环境依据：Cilium 1.20（官方文档当前渲染 1.20.2，2026-09-15 更新）。本沙箱未装，选项据 Cilium 官方 cmdref 核对，示例标注「据官方文档」。

## 一、命令是干什么的

Cilium 是用 **eBPF** 实现的 K8s 网络/网络策略/可观测插件，跑在每个节点上（cilium-agent DaemonSet）。`cilium` CLI 就是跟节点上的 cilium-agent 对话的工具。

排障三层：

- **整体健康**：`cilium status`——agent、identity、datapath、 Hubble 好不好；
- **端点（endpoint）**：每个 Pod 在 Cilium 里的身份与策略状态；
- **策略（policy）**：导入了哪些网络策略、通不通；
- **连通性自检**：`cilium connectivity test` 跑内置测试套件；
- **实时流量**：`cilium monitor`（更友好的是 [hubble observe](./hubble)）。

> 类比：Cilium 像「用 eBPF 重新写的 kube-proxy + 防火墙 + 流量监控」。`cilium status` 是它的体检报告，`endpoint` 是每个 Pod 的网络身份证，`policy` 是防火墙规则。

## 二、命令语法

```bash
cilium status [flags]
cilium endpoint list | get <端点>
cilium policy get | validate -f FILE
cilium connectivity test [flags]
cilium monitor [filters]
```

- CLI 默认连本机 cilium-agent 的 API；可用 `-H, --host` 指定远程、`--config` 指定配置文件。

最简单：

```bash
cilium status
```

## 三、选项全表（对照官方 cilium_status cmdref）

### 1. `cilium status`

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `--verbose` | 等价于打开所有 `--all-*`（地址/控制器/节点/重定向/集群/健康全列） | 排障看全量（最常用） |
| `--brief` | 只打一行状态 | 脚本里快速判断 |
| `--all-controllers` | 显示全部控制器（不只失败的） | 看控制器是否都健康 |
| `--all-health` | 显示全部健康项（不只失败的） | 全量体检 |
| `--all-nodes` | 显示所有节点（不只本机） | 跨节点看状态 |
| `-o json\|yaml\|jsonpath='{}'` | 机器可读输出 | 脚本采集 |
| `--timeout DURATION` | 健康查询超时（默认 30s） | agent 慢时放大 |
| `-H URI`，`--host=URI` | 连哪个 cilium-agent API | 不在节点上时 |
| `-D`，`--debug` | 调试日志 | CLI 自身排障 |

> status 会报：Daemon 状态、节点列表、kube-proxy 替换模式、Cilium 等版本、Hubble 是否启用、控制器健康。

### 2. endpoint（Pod 端点）

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `cilium endpoint list` | 列所有端点（Pod）及其身份/策略状态 | 看哪些 Pod 已被 Cilium 接管 |
| `cilium endpoint get <pod或ID>` | 看某端点详情（身份、策略、日志状态） | 某个 Pod 网络不通时 |
| `cilium endpoint config <id>` | 端点配置 | 调端点级开关 |

### 3. policy（网络策略）

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `cilium policy get` | 看已导入的 Cilium 网络策略 | 确认策略到底下发没 |
| `cilium policy validate -f FILE` | 校验 CiliumNetworkPolicy 语法 | 提交前校验 |
| `cilium policy import -f FILE` | 导入策略 | 手动下发 |

### 4. 连通性与监控

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `cilium connectivity test` | 跑内置端到端连通性测试套件 | 升级/排障后自检全网格 |
| `cilium monitor` | 实时打印节点上的数据包/调试事件 | 看包走向（更推荐 hubble） |
| `cilium hubble enable` | 启用 Hubble 可观测 | 没装 Hubble 时 |

## 四、由浅入深的典型示例

以下输出「据官方文档」或示意。

### 示例 1：看整体状态（详细）

```bash
cilium status --verbose
```

```text
    /¯¯\
 /¯¯\__/¯¯\    Cilium:             OK
 \__/¯¯\__/    Operator:           OK
 /¯¯\__/¯¯\    Hubble:             disabled
 \__/¯¯\__/
Cluster Pods:         50/50 healthy
Control-plane:        ok
Kube-proxy:           working with kube-proxy (eBPF)
Controlled Deployment: cilium
Cilium version:       1.20.2
```

> 先看 `Cilium: OK`、`Hubble:` 是否启用；不通时这里常提示哪个组件 not OK。

### 示例 2：列所有端点

```bash
cilium endpoint list
```

```text
ENDPOINT   MAC           IDENTITY   INIT   EPHEMERAL   HEALTHWELL   STATUS
10.0.1.5   ae:XX:..      1048577    false  false       true         ready
10.0.2.7   8a:XX:..      1048578    false  false       true         ready
```

> 看每个 Pod 的 IP、identity、status=ready。

### 示例 3：看某个 Pod 端点详情

```bash
cilium endpoint get api-pod-xxx
```

> 输出该 Pod 的安全身份、允许/拒绝的策略、连接跟踪状态。Pod 间被策略挡了，这里看 policy 是否命中。

### 示例 4：校验并查看策略

```bash
cilium policy validate -f my-policy.yaml
cilium policy get
```

```text
Cluster wide: true
[
  { "endpointSelector": {"matchLabels": {"app": "api"}},
    "ingress": [ {"fromEndpoints": [{"matchLabels": {"app": "frontend"}}]} ] }
]
```

> 确认 CiliumNetworkPolicy 已正确下发。

### 示例 5：跑连通性自检

```bash
cilium connectivity test
```

> 它会起一组测试 Pod 跑东西向/策略/服务解析等用例；全绿说明 Cilium 数据面 OK，问题在业务层。

### 示例 6：启用 Hubble

```bash
cilium hubble enable
```

> 之后用 [hubble observe](./hubble) 看 Pod 间流日志。

### 示例 7：monitor 看包（原始）

```bash
cilium monitor --type drop
```

> `--type drop` 只看被丢弃的包——策略误拦时这里能看到谁被谁挡了。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `cilium status --verbose` | 全量健康体检 |
| `cilium endpoint list` | 列 Pod 端点/身份 |
| `cilium endpoint get pod` | 单 Pod 端点详情 |
| `cilium policy get` | 看已下发策略 |
| `cilium policy validate -f p.yaml` | 校验策略 |
| `cilium connectivity test` | 连通性自检 |
| `cilium monitor --type drop` | 看被丢的包 |
| `cilium hubble enable` | 开 Hubble |

## 六、RHEL 系与 Debian 系差异

`cilium` CLI 是单二进制，两系用法一致。差异在部署形态：

- Cilium 通常通过 Helm/operator 装在 K8s 里，CLI 在装了 cilium 的 Pod 或本机用 `cilium`/`hubble` 镜像执行；
- 节点 OS（RHEL vs Ubuntu）主要影响内核版本与 eBPF 能力（如 L7 可见性、kube-proxy replacement 需较新内核）；
- CLI 版本要和集群 Cilium 版本大对齐，跨大版本可能有命令差异。

## 七、新手易错点

1. **`cilium status` 默认不够细**：排障加 `--verbose`，否则只看到 OK 看不到哪个控制器挂了。
2. **Hubble 默认可能没开**：`status` 里 Hubble: disabled 时，`hubble observe` 连不上，先 `cilium hubble enable`。
3. **网络不通先分是「策略挡」还是「数据面挂」**：`cilium monitor --type drop` 看到丢包多是策略；`status` not OK 是数据面。
4. **endpoint 的 identity 要对**：identity 没分配好会导致策略匹配不上。
5. **危险/开销提示**：`cilium monitor`/`connectivity test` 会起测试 Pod、产生流量与日志；生产上 `connectivity test` 慎用，`monitor` 用完即 Ctrl-C。eBPF 程序在内核态跑，错误配置可能影响节点网络，先在测试节点验证。

## 八、相关命令与文档

- 速查页：[云原生排障命令速查](../cloudnative-commands)
- 流日志：[hubble](./hubble)
- eBPF 原理：[Linux eBPF 指南](../../guide/linux-ebpf)
- 服务网格对照：[container-servicemesh 指南](../../guide/container-servicemesh)
- 官方文档：https://docs.cilium.io/ ；https://docs.cilium.io/en/stable/cmdref/cilium_status/
