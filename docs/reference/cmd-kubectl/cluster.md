# 集群与节点命令详解：cluster-info / get nodes / top nodes / version

> 本文是 [kubectl 命令速查](../kubectl-commands#集群与节点) 中 `cluster-info`、`get nodes`、`top nodes`、`version` 的从 0 到 1 详解。
> 目标：把这几个"刚连上集群最先敲"的命令讲清楚，多看几遍后，你在服务器上敲 `kubectl --help` 就知道该用哪个选项。
> 环境依据：kubectl 客户端，对应 **Kubernetes 1.35**（本机沙箱未安装 kubectl，全部选项依据 K8s 官方命令参考核实；下文示例输出均为「示意，据 K8s 官方文档」）。

## 一、命令是干什么的

刚装好 kubectl、配好 kubeconfig 时，你心里头几个最朴素的问题是：

- 我连上的这个集群，控制面在哪、有哪些自带服务？——`kubectl cluster-info`
- 集群里有几台机器（节点）？各自健康吗？跑在哪？——`kubectl get nodes`
- 这些节点 CPU / 内存到底用了多少？——`kubectl top nodes`
- 我本地的 kubectl 和集群的 apiserver 版本分别是多少？——`kubectl version`

这一组命令都是**只读、安全、不会改动集群**的，第一次接触集群时随便敲，放心用。

> 类比：`cluster-info` 像问物业"小区大门和水泵房在哪"；`get nodes` 像看"小区有几栋楼、每栋住没住人"；`top nodes` 像看"每栋楼现在电表水表走了多少"；`version` 像确认"你手里的对讲机和小区广播是不是一个频段"。

## 二、命令语法

这一节是四条命令，各自语法：

```bash
kubectl cluster-info [dump] [flags]
kubectl get nodes [(-o|--output=)wide] [-l 标签] [flags]
kubectl top node [NODE名] [-l 标签] [flags]
kubectl version [--client] [-o yaml|json]
```

- `cluster-info`：不带参数就打印控制面地址与集群服务；子命令 `dump` 会把整个集群状态导出做排障。
- `get nodes`：不给名字就列**所有**节点；给名字就看单台。
- `top node`：依赖 metrics-server，不给名字列全部节点。
- `version`：不带参数同时打印客户端和服务端版本。

最简单的起步三连：

```bash
kubectl cluster-info
kubectl get nodes
kubectl version
```

## 三、选项全表（对照 `kubectl --help`）

### 1. cluster-info

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `dump`（子命令） | 把集群当前状态（含各 Pod 日志）整体导出 | 集群出问题、要把现场打包给别人排查时 |
| `--output-directory=目录`（dump 专用） | 把 dump 结果写成文件目录而不是打到屏幕 | 导出到 `/tmp/xxx` 打包带走时 |
| `--namespaces=ns1,ns2`（dump 专用） | 只 dump 指定命名空间 | 默认只 dump 当前命名空间 + kube-system，想收窄范围时 |
| `-A`，`--all-namespaces`（dump 专用） | dump 所有命名空间 | 出问题范围不明、全量收现场时 |

### 2. get nodes

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-o wide` | 多列显示：内部 IP、操作系统、内核、容器运行时 | 排查"这台机什么内核/运行时"时（最常用） |
| `-o yaml` / `-o json` | 输出节点完整对象 | 看节点污点、资源容量、labels 细节时 |
| `-l 标签`，`--selector` | 按标签过滤节点 | 只看某一类节点（如 `-l node-role.kubernetes.io/worker=`） |
| `--show-labels` | 把节点所有标签最后单列出来 | 想看清节点打了哪些标签时 |
| `--selector='!node-role.kubernetes.io/control-plane'` | 排除控制面节点 | 只看工作节点时 |

### 3. top node

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| （无短选项）`--sort-by=cpu\|memory` | 按 CPU 或内存排序 | 找最吃资源的节点时 |
| `-l 标签`，`--selector` | 按标签过滤节点 | 只统计某组节点时 |
| `--no-headers` | 不打印表头 | 输出接脚本处理时 |
| `--show-capacity` | 按 Capacity 而非 Allocatable 显示容量口径 | 想看节点物理总量而非可分配量时 |

> 注意：`kubectl top` 系列**必须**集群里装了 metrics-server，否则报 `error: Metrics API not available`。

### 4. version

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `--client`（`-c` 的全局语义不同，此处用长选项） | 只打印客户端版本，不连集群 | 离线只想知道自己装的 kubectl 版本时 |
| `-o yaml` / `-o json` | 用结构化格式打印版本 | 脚本解析版本号时 |
| ~~`--short`~~ | **已移除** | 老版本 `--short` 单行打印，1.35 已没有，勿再用 |

> 版本差异提醒：老教程里的 `kubectl version --short`（单行输出 `Client Version: ... Server Version: ...`）在新版已被移除；现在 `kubectl version` 默认就是带 `Client Version / Kustomize Version / Server Version` 三段的多行输出。

## 四、由浅入深的典型示例

### 示例 1：看控制面在哪、有哪些集群服务

```bash
kubectl cluster-info
```

输出（示意，据 K8s 官方文档）：

```text
Kubernetes control plane is running at https://1.2.3.4:6443
CoreDNS is running at https://1.2.3.4:6443/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy
```

- 第一行告诉你 apiserver 地址；
- 后面列出打了 `kubernetes.io/cluster-service=true` 标签的集群自带服务（如 CoreDNS）。

### 示例 2：列出所有节点，看状态

```bash
kubectl get nodes
```

输出（示意，据 K8s 官方文档）：

```text
NAME     STATUS   ROLES           AGE   VERSION
node-1   Ready    control-plane    40d   v1.35.0
node-2   Ready    worker           40d   v1.35.0
node-3   Ready    worker           39d   v1.35.0
```

逐列看：

- `STATUS`：`Ready` 表示节点正常接收 Pod；`NotReady` 表示节点出问题（kubelet 挂了、资源不够等）。
- `ROLES`：`control-plane` 是控制面，`worker` 是工作节点。
- `AGE`：节点加入集群多久。
- `VERSION`：节点上 kubelet 的版本。

### 示例 3：加 `-o wide` 看节点更多细节

```bash
kubectl get nodes -o wide
```

输出（示意，据 K8s 官方文档）：

```text
NAME     STATUS   ROLES    AGE   VERSION   INTERNAL-IP   OS-IMAGE             KERNEL-VERSION   CONTAINER-RUNTIME
node-2   Ready    worker   40d   v1.35.0   10.0.0.21     Ubuntu 22.04.4 LTS   5.15.0-105-generic   containerd://1.7.18
```

- `INTERNAL-IP`：节点内网 IP，出问题登节点时用得上；
- `OS-IMAGE` / `KERNEL-VERSION`：操作系统和内核版本；
- `CONTAINER-RUNTIME`：容器运行时（containerd / dockershim 等），排障时先确认这个。

### 示例 4：看节点实时资源占用（需 metrics-server）

```bash
kubectl top nodes
```

输出（示意，据 K8s 官方文档）：

```text
NAME     CPU(cores)   CPU%   MEMORY(bytes)   MEMORY%
node-1   340m         8%     4123Mi          26%
node-2   1120m        28%    8890Mi          56%
node-3   210m         5%     3011Mi          19%
```

- `CPU(cores)`：`340m` = 0.34 核（m 是 millicore，1000m=1 核）；
- `CPU%`：占用占节点可分配 CPU 的百分比；
- `MEMORY%`：内存占用百分比。哪个节点飘红（接近 100%）就是瓶颈。

### 示例 5：按内存排序找最吃内存的节点

```bash
kubectl top nodes --sort-by=memory
```

> 内存占用最高的节点排在最上面；`--sort-by=cpu` 则按 CPU 排。

### 示例 6：看客户端 / 服务端版本

```bash
kubectl version
```

输出（示意，据 K8s 官方文档）：

```text
Client Version: v1.35.0
Kustomize Version: v5.9.0
Server Version: v1.35.0
```

- `Client Version`：你本地 kubectl 的版本；
- `Kustomize Version`：内置 kustomize 的版本；
- `Server Version`：apiserver 的版本。
- 生产上建议客户端与服务端版本差不超过一个小版本（k8s 支持 ±1 个 minor 版本 skew）。

### 示例 7：只看客户端版本（离线也行）

```bash
kubectl version --client
```

> 断网或 apiserver 挂了时，加 `--client` 就不会去连集群，只打印本地版本。

### 示例 8：把集群现场导出用于排障

```bash
kubectl cluster-info dump --all-namespaces --output-directory=/tmp/cluster-state
```

> 会在 `/tmp/cluster-state` 下生成一堆文件，含各命名空间、各 Pod 的状态与日志，打包发给同事即可。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `kubectl cluster-info` | 看控制面地址与集群服务 |
| `kubectl get nodes` | 看节点是否 Ready |
| `kubectl get nodes -o wide` | 看节点 IP/内核/运行时（**最常用**） |
| `kubectl get nodes -l node-role.kubernetes.io/worker=` | 只看工作节点 |
| `kubectl top nodes` | 看节点 CPU/内存占用 |
| `kubectl top nodes --sort-by=cpu` | 按 CPU 排序找瓶颈 |
| `kubectl version` | 看客户端/服务端版本 |
| `kubectl version --client` | 只看本地版本 |

## 六、RHEL 系与 Debian 系差异

这一组命令操作的是**集群**，不是本机某个软件包，所以 RHEL/Rocky 与 Ubuntu/Debian 上的用法**完全一致**，区别只在两点：

- kubectl 安装方式不同：RHEL 系用 `dnf`、Debian 系用 `apt` 加官方仓库装，命令本身一模一样；
- `top nodes` 依赖 metrics-server：**有没有装 metrics-server 取决于集群**，跟你本机是哪个发行版无关；没装就报 Metrics API not available，不是系统差异。

## 七、新手易错点

1. **`kubectl top` 报错不是你命令写错**：报 `Metrics API not available` 是集群没装 metrics-server，先装它（或用 `kubectl describe nodes` 看 requests/limits 间接估算）。
2. **`STATUS=NotReady` 的节点别硬删 Pod**：先 `kubectl describe node <名>` 看 Conditions，多半是 kubelet 或网络问题。
3. **`--short` 用不了了**：老博客里的 `kubectl version --short` 在 1.35 已移除，直接 `kubectl version` 即可，别再加 `--short`。
4. **版本对不上会出怪事**：客户端和服务端差太多（如客户端 1.35、服务端 1.28）时，新字段可能不被识别，排障先 `kubectl version` 确认。
5. **`get nodes` 是只读的**：随便敲，不会改集群；但一旦换成 `cordon` / `drain` / `delete` 就是高危操作，见 [delete 详解](./delete)。
6. **`cluster-info dump` 输出巨大**：会拉很多日志，别直接打到屏幕，务必加 `--output-directory`。

## 八、相关命令与文档

- 速查页：[kubectl 命令速查](../kubectl-commands#集群与节点)
- 看节点上跑了哪些 Pod：[get 详解](./get)
- 节点资源占用更高频的是看 Pod：`kubectl top pods`（见 [get 详解](./get) 同目录）
- 集群架构概念补课：[K8s 架构与集群](../../guide/container-k8s-01-architecture-cluster)
- 官方命令参考：https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands
