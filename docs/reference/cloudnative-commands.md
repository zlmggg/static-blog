# 云原生排障命令速查

> 云原生环境（Helm / K8s 进阶排障 / containerd / OpenTelemetry / Grafana LGTM / Cilium-eBPF）常用排障命令速查。
> 基础 kubectl 命令见 [kubectl 命令速查](/reference/kubectl-commands)；概念与部署见 [K8s 系列指南](/guide/container-k8s-01-architecture-cluster) 与 [eBPF 指南](/guide/linux-ebpf)。
> 用法：右侧「本页目录」跳转，或 `Ctrl+K` 搜索；命令可直接复制（把占位符换成你的实际值）。

::: tip 版本基准（2026-09）
本篇命令基于当前稳定版：Helm 4.3、Kubernetes 1.35（临时容器自 1.25 GA）、containerd 2.3、crictl(cri-tools) v1.35、OpenTelemetry Collector v0.162、Grafana Loki 3.7、Tempo 3.0（TraceQL metrics 已 GA）、Cilium 1.20、bpftrace 0.27。版本以各发行版实际安装为准，用 `xx version` 自查。
:::

## Helm（release 排障）

| 命令 | 说明 |
|---|---|
| [`helm list -A`](./cmd-cloudnative/helm-troubleshoot) | 列出所有命名空间已安装的 release |
| [`helm list -n ns`](./cmd-cloudnative/helm-troubleshoot) | 查看指定命名空间 release |
| [`helm status 名`](./cmd-cloudnative/helm-troubleshoot) | 查看 release 状态、资源、最近事件 |
| [`helm get manifest 名`](./cmd-cloudnative/helm-troubleshoot) | 查看该 release 渲染出的全部 K8s 清单 |
| [`helm get values 名`](./cmd-cloudnative/helm-troubleshoot) | 查看生效的 values |
| [`helm get values 名 -a`](./cmd-cloudnative/helm-troubleshoot) | 含默认值的完整 values |
| [`helm history 名`](./cmd-cloudnative/helm-troubleshoot) | 查看 release 修订历史 |
| [`helm rollback 名 <REVISION>`](./cmd-cloudnative/helm-troubleshoot) | 回滚到指定版本 |
| [`helm rollback 名 0`](./cmd-cloudnative/helm-troubleshoot) | 回滚到上一版本 |
| [`helm template chart -f values.yaml`](./cmd-cloudnative/helm-troubleshoot) | 本地渲染模板（不提交集群），排查模板错误 |
| [`helm install 名 chart --dry-run --debug`](./cmd-cloudnative/helm-troubleshoot) | 试运行安装并打印渲染结果与调试信息 |
| [`helm upgrade 名 chart --dry-run`](./cmd-cloudnative/helm-troubleshoot) | 试运行升级，看会变什么 |
| [`helm lint chart`](./cmd-cloudnative/helm-troubleshoot) | 检查 chart 语法/依赖问题 |
| [`helm pull repo/chart --untar`](./cmd-kubectl/helm) | 下载 chart 到本地查看 |
| [`helm push chart.tgz oci://repo`](./cmd-kubectl/helm) | 把 chart 推到 OCI 仓库 |
| [`helm repo add 名 url && helm repo update`](./cmd-kubectl/helm) | 添加并更新仓库索引 |

## kubectl 进阶排障

| 命令 | 说明 |
|---|---|
| [`kubectl describe pod 名`](./cmd-kubectl/describe) | 看事件、调度、探针失败原因 |
| [`kubectl get events -A --sort-by=.metadata.creationTimestamp`](./cmd-cloudnative/kubectl-advanced) | 按时间正序看全集群事件 |
| [`kubectl get events --field-selector type=Warning`](./cmd-cloudnative/kubectl-advanced) | 只看 Warning 事件 |
| [`kubectl top nodes`](./cmd-kubectl/cluster) / [`kubectl top pods -A`](./cmd-kubectl/cluster) | 节点/Pod 资源用量（需 metrics-server） |
| [`kubectl debug 名 -it --image=busybox --target=容器`](./cmd-cloudnative/kubectl-advanced) | 给崩溃/精简容器注入临时调试容器（Ephemeral Container） |
| [`kubectl debug node/节点名 -it --image=ubuntu`](./cmd-cloudnative/kubectl-advanced) | 在节点上起调试 Pod，挂载节点宿主文件系统 /host |
| [`kubectl logs 名 --previous`](./cmd-kubectl/logs) | 看崩溃前那个容器的日志 |
| [`kubectl get --raw /metrics`](./cmd-cloudnative/kubectl-advanced) | 直接抓取组件 metrics（如 apiserver） |
| [`kubectl get --raw /healthz?verbose`](./cmd-cloudnative/kubectl-advanced) | 健康检查详情 |
| [`kubectl cluster-info dump`](./cmd-cloudnative/kubectl-advanced) | 导出集群大量调试信息到当前目录 |
| [`kubectl cordon 节点`](./cmd-cloudnative/kubectl-advanced) | 标记节点不可调度 |
| [`kubectl drain 节点 --ignore-daemonsets --delete-emptydir-data`](./cmd-cloudnative/kubectl-advanced) | 驱逐节点上 Pod（升级前） |
| [`kubectl uncordon 节点`](./cmd-cloudnative/kubectl-advanced) | 恢复节点可调度 |
| [`kubectl auth can-i create pods --as=user`](./cmd-kubectl/auth) | 模拟某账号权限（RBAC 排障） |

## containerd / CRI 运行时

| 命令 | 说明 |
|---|---|
| [`crictl ps`](./cmd-cloudnative/crictl) | 列出运行中的容器（CRI 接口） |
| [`crictl ps -a`](./cmd-cloudnative/crictl) | 含已停止的容器 |
| [`crictl logs 容器ID`](./cmd-cloudnative/crictl) | 查看容器日志 |
| [`crictl logs -f 容器ID`](./cmd-cloudnative/crictl) | 实时跟踪日志 |
| [`crictl inspect 容器ID`](./cmd-cloudnative/crictl) | 容器完整详情（状态、挂载、命令） |
| [`crictl pods`](./cmd-cloudnative/crictl) | 列出 PodSandbox |
| [`crictl stats`](./cmd-cloudnative/crictl) | 容器资源占用实时统计 |
| [`crictl info`](./cmd-cloudnative/crictl) | 运行时与 CRI 配置信息 |
| [`ctr -n k8s.io images ls`](./cmd-cloudnative/ctr) | 用 ctr 列出 containerd 中镜像（k8s 命名空间） |
| [`ctr -n k8s.io containers ls`](./cmd-cloudnative/ctr) | 列出 containerd 容器 |
| [`crictl config runtime-endpoint unix:///run/containerd/containerd.sock`](./cmd-cloudnative/crictl) | 指定运行时端点（切 CRI-O 用 /run/crio/crio.sock） |

> 注意：`docker` 管不到 K8s 容器（除非用 docker-shim）；kubelet 走 CRI，节点排障优先用 [`crictl`](./cmd-cloudnative/crictl)。

## OpenTelemetry Collector

| 命令 / 操作 | 说明 |
|---|---|
| [`otelcol-contrib --config=config.yaml`](./cmd-cloudnative/otelcol) | 启动 Collector（contrib 版含更多组件） |
| [`otelcol --config=config.yaml --validate`](./cmd-cloudnative/otelcol) | 只校验配置是否合法 |
| [`--log-level=debug`](./cmd-cloudnative/otelcol) | 启动参数，打印每个管道的数据细节 |
| `service.telemetry.metrics.address: 0.0.0.0:8888` | 配置 Collector 自身 metrics 端口 |
| [`curl -s localhost:8888/metrics`](./cmd-net/curl) | 查看 Collector 自身处理指标（接收/导出/拒绝条数） |
| [`curl -s localhost:55679/debug/zpages`](./cmd-net/curl) | zpages 页面：看管道活跃 trace、错误（需开启） |
| [`curl -s localhost:8888/debug/pprof/`](./cmd-net/curl) | pprof 性能分析（内存/CPU） |
| `otlphttp://<host>:4318` | HTTP 接收/导出端点（gRPC 为 4317） |
| [`curl -X POST localhost:4318/v1/traces -d @trace.json`](./cmd-net/curl) | 手动投递一条 OTLP 数据验证导出链路 |

> zpages 需在配置里显式开启 `extension: zpages` 并在 `service.extensions` 引用；排导出失败时先看 Collector 自身 metrics 里 `exporter_failed` 是否在涨。

## 日志与链路查询

**Grafana Loki LogQL（日志查询）：**

| 查询 | 说明 |
|---|---|
| [`{job="api"}`](./cmd-cloudnative/logcli) | 按标签选择器选出日志流 |
| [`{job="api"} |= "error"`](./cmd-cloudnative/logcli) | 在日志里过滤含 error 的行 |
| [`{job="api"} \|~ "5[0-9]{2}"`](./cmd-cloudnative/logcli) | 正则匹配 5xx 状态码 |
| [`{job="api"} \| json`](./cmd-cloudnative/logcli) | 把 JSON 日志解析成字段 |
| [`{job="api"} \| label_format level="level"`](./cmd-cloudnative/logcli) | 提取字段为标签 |
| [`rate({job="api"}[5m])`](./cmd-cloudnative/logcli) | 量化函数：日志每秒条数 |
| [`count_over_time({job="api"}[5m])`](./cmd-cloudnative/logcli) | 统计 5 分钟内日志行数 |
| [`sum(rate({job="api"} |= "error"[5m])) by (status)`](./cmd-cloudnative/logcli) | 按状态码聚合错误率 |

**Tempo TraceQL（链路查询）：**

| 查询 | 说明 |
|---|---|
| [`{ resource.service.name = "api" }`](./cmd-cloudnative/tempo) | 按服务选 trace |
| [`{ span.http.status_code >= 500 }`](./cmd-cloudnative/tempo) | 选含 5xx span 的 trace |
| [`{ .error = true }`](./cmd-cloudnative/tempo) | 选出错的 trace |
| [`{ duration > 1s }`](./cmd-cloudnative/tempo) | 选慢 trace |
| [`{ resource.service.name = "api" && span.http.route = "/pay" }`](./cmd-cloudnative/tempo) | 组合条件 |

**Jaeger：**

| 命令 / 操作 | 说明 |
|---|---|
| [`jaeger_query --query.port=16686`](./cmd-cloudnative/tempo) | 启动 Jaeger 查询 UI |
| 浏览器打开 [`http://<host>:16686`](./cmd-cloudnative/tempo) | 按服务/操作/tag 查 trace |
| [`curl localhost:16686/api/traces?service=api`](./cmd-net/curl) | API 方式拉 trace |

## Cilium 与 eBPF

| 命令 | 说明 |
|---|---|
| [`cilium status`](./cmd-cloudnative/cilium) | 查看 Cilium 组件健康与版本 |
| [`cilium status --verbose`](./cmd-cloudnative/cilium) | 含节点、 Hubble 状态详情 |
| [`cilium endpoint list`](./cmd-cloudnative/cilium) | 列出所有端点（Pod）及其身份/策略状态 |
| [`cilium endpoint get <pod>`](./cmd-cloudnative/cilium) | 查看某 Pod 端点详情 |
| [`cilium policy get`](./cmd-cloudnative/cilium) | 查看已导入的网络策略 |
| [`cilium policy validate -f policy.yaml`](./cmd-cloudnative/cilium) | 校验 Cilium 网络策略 |
| [`cilium hubble ui`](./cmd-cloudnative/cilium) | 本地打开 Hubble 可观测 UI |
| [`hubble observe`](./cmd-cloudnative/hubble) | 实时观察 Pod 间流日志（源/目的/协议/ verdict） |
| [`hubble observe --namespace ns --protocol http`](./cmd-cloudnative/hubble) | 按命名空间/协议过滤流 |
| [`cilium connectivity test`](./cmd-cloudnative/cilium) | 跑内置连通性测试套件 |
| `bpftrace -e 'kprobe:vfs_open { printf("open by %s\n", comm); }'` | bpftrace 单行：追踪文件打开 |
| `bpftrace -e 'tracepoint:syscalls:sys_enter_execve { join(args->argv); }'` | 追踪进程启动参数 |
| `bpftrace -l 'kprobe:tcp_*'` | 列出可用探针 |
| `bpftool prog show` | 列出已加载的 eBPF 程序 |
| `bpftool map show` | 列出 eBPF map |

## 网络连通性（网格 / Ingress / 服务）

| 命令 | 说明 |
|---|---|
| [`curl -v http://服务名/路径`](./cmd-net/curl) | 详细 HTTP 请求过程（看 DNS/连接/TLS） |
| [`curl -v --resolve 域名:80:IP http://域名/`](./cmd-net/curl) | 绕过 DNS 直连指定 IP 验证虚拟主机 |
| [`curl -kv https://域名`](./cmd-net/curl) | 跳过证书校验排查 TLS 问题 |
| [`dig 域名 @DNS服务器`](./cmd-net/dig) | DNS 解析排查 |
| [`nslookup 域名`](./cmd-net/dig) | 简易 DNS 查询 |
| [`nc -zv 主机 端口`](./cmd-net/nc-telnet) | 测试 TCP 端口是否通 |
| [`nc -uzv 主机 端口`](./cmd-net/nc-telnet) | 测试 UDP 端口 |
| [`grpcurl -plaintext 主机:端口 list`](./cmd-cloudnative/ingress-mesh) | 列出 gRPC 服务（服务网格排障常用） |
| [`grpcurl -plaintext 主机:端口 包.服务/方法`](./cmd-cloudnative/ingress-mesh) | 直接调用 gRPC 方法 |
| [`kubectl exec`](./cmd-kubectl/exec) -it pod -- nslookup svc | 在 Pod 内验证集群 DNS |
| `ipvsadm -Ln` | 查看 LVS/IPVS 转发规则（kube-probe=ipvs 模式） |

::: warning 生产红线
- `kubectl debug` 注入的临时容器不持久，Pod 重建即消失；排查完即可离开，不要依赖它常驻。
- `--log-level=debug`、`bpftrace` 会产生大量日志/性能开销，生产排障用完即关，不要长期开启。
- `bpftool` / `bpftrace` 在内核态运行，错误探针可能影响节点稳定性，先在测试节点验证。
- drain 节点前确认 Pod 有 PDB 与副本冗余，避免把服务全部驱逐掉。
:::

### 官方文档

- Helm 文档：https://helm.sh/docs/ （Helm 4：https://helm.sh/docs/4.3/）
- Kubernetes 命令参考（kubectl / debug）：https://kubernetes.io/docs/reference/kubectl/ ；临时容器：https://kubernetes.io/docs/tasks/debug/debug-application/debug-running-pod/
- crictl (cri-tools)：https://github.com/kubernetes-sigs/cri-tools
- containerd：https://containerd.io/docs/
- OpenTelemetry Collector：https://opentelemetry.io/docs/collector/
- Grafana Loki 文档与 LogQL：https://grafana.com/docs/loki/latest/query/
- Grafana Tempo 文档与 TraceQL：https://grafana.com/docs/tempo/latest/traceql/
- Jaeger：https://www.jaegertracing.io/docs/
- Cilium：https://docs.cilium.io/ ；Hubble：https://docs.cilium.io/en/stable/observability/hubble/
- bpftrace：https://bpftrace.org/docs/ ；bpftool：https://man7.org/linux/man-pages/man8/bpftool.8.html
