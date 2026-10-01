# kubectl describe 命令详解：看资源详情和 Events 排障

> 本文是 [kubectl 命令速查](../kubectl-commands#调试与排障) 中 `kubectl describe` 的从 0 到 1 详解。
> 目标：把 `kubectl describe --help` 里的每个选项讲清楚，多看几遍后，你在服务器上敲 `kubectl describe --help` 就知道该用哪个选项。
> 环境依据：kubectl 客户端，对应 **Kubernetes 1.35**（本机沙箱未安装，选项依据 K8s 官方命令参考核实；示例输出均为「示意，据 K8s 官方文档」）。

## 一、命令是干什么的

`get` 给你的是**一行一个**的简表，`describe` 给你的是**一个资源的完整体检报告**：它的规格、当前状态、关联的控制器，以及最关键的——**Events（事件）**。

Pod 起不来、一直 `Pending`、`CrashLoopBackOff`、探针不过，90% 的答案都藏在 `describe` 末尾的 Events 里。

> 类比：`get` 是看体检表上那几行结论；`describe` 是把整份病历、检查单、医嘱全翻出来读。排障时 `get` 发现"这 Pod 不对"，下一步必然 `describe` 它。

## 二、命令语法

```bash
kubectl describe (-f 文件 | 类型 [名称前缀 | -l 标签] | 类型/名称)
```

- `类型`：如 `pod`、`node`、`deployment`；
- `名称前缀`：给前缀时，先精确匹配全名，匹配不到就把所有以前缀开头的都 describe 出来；
- `-l 标签`：describe 匹配标签的那一批；
- 只读命令，不改集群。

```bash
kubectl describe pod nginx-6f5b9d7c8-x2zqk
```

## 三、选项全表（对照 `kubectl describe --help`）

### 1. 指定 describe 谁

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `类型 名称` | describe 指定类型的某个资源 | 最常用，如 `describe pod xxx` |
| `-f 文件`，`--filename` | describe 文件里指定的资源 | 对着清单查 |
| `-l 标签`，`--selector` | describe 匹配标签的资源 | 如 `describe po -l app=nginx` |
| `-A`，`--all-namespaces` | 跨所有命名空间 | 资源 ns 不明时 |
| `-k 目录`，`--kustomize` | 按 kustomization 目录 | kustomize 管理的资源 |

### 2. 输出控制

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `--show-events=true`（默认开） | 末尾打印相关 Events | 排障核心，**别关**；想不看事件才设 false |
| `-R`，`--recursive` | 递归处理 `-f` 目录 | 目录套目录时 |
| `--chunk-size=500` | 大列表分块 | 资源巨多时分页取 |

## 四、由浅入深的典型示例

### 示例 1：describe 一个 Pod，看完整状态

```bash
kubectl describe pod nginx-6f5b9d7c8-x2zqk
```

输出（示意，据 K8s 官方文档）：

```text
Name:         nginx-6f5b9d7c8-x2zqk
Namespace:    default
Node:         node-2/10.0.0.21
Start Time:   Mon, 29 Sep 2026 10:00:00 +0800
Labels:       app=nginx
Status:       Running
IP:           10.244.1.15
Containers:
  nginx:
    Container ID:   containerd://abc123...
    Image:          nginx:1.27
    State:          Running
      Started:      Mon, 29 Sep 2026 10:01:10 +0800
    Ready:          True
    Restart Count:  0
Conditions:
  Type              Status
  PodScheduled      True
  Initialized       True
  ContainersReady   True
  Ready             True
Events:
  Type    Reason     Age   From               Message
  ----    ------     ----  ----               -------
  Normal  Scheduled  2h    default-scheduler  Successfully assigned default/nginx-xxx to node-2
  Normal  Pulling    2h    kubelet            Pulling image "nginx:1.27"
  Normal  Pulled     2h    kubelet            Successfully pulled image "nginx:1.27"
  Normal  Created    2h    kubelet            Created container nginx
  Normal  Started    2h    kubelet            Started container nginx
```

- 上半部分是规格和状态；
- 下半部分 `Events` 是时间线：调度→拉镜像→建容器→启动，每一步谁干的、成功没成功，都写得明明白白。

### 示例 2：Pod 一直 Pending——看 Events 找原因

```bash
kubectl describe pod my-pending-pod
```

输出（示意，据 K8s 官方文档）：

```text
Events:
  Type     Reason            Age   From               Message
  ----     ------            ----  ----               -------
  Warning  FailedScheduling  30s   default-scheduler  0/3 nodes are available: 3 Insufficient cpu.
```

- `Warning` + `FailedScheduling`：调度器选不出节点，原因是 **CPU 不够**。
- 下一步：扩节点 / 降 requests / 删别的 Pod，而不是反复删这个 Pod。

### 示例 3：CrashLoopBackOff——看 Events 和 State

```bash
kubectl describe pod my-crash-pod
```

输出（示意，据 K8s 官方文档）：

```text
Containers:
  app:
    State:          Waiting
      Reason:       CrashLoopBackOff
    Last State:     Terminated
      Reason:       Error
      Exit Code:    1
    Restart Count:    7
Events:
  Type     Reason     Age                From               Message
  ----     ------     ----               ----               -------
  Warning  BackOff    12s (x over 5m)    kubelet            Back-off restarting failed container app
```

- `Restart Count` 一直在涨、`Last State: Terminated / Exit Code: 1`：容器起来就崩。
- 下一步用 `kubectl logs --previous <pod> -c app` 看它崩之前打的日志（见 [logs 详解](./logs)）。

### 示例 4：探针不过（健康检查失败）

```bash
kubectl describe pod my-probe-pod
```

输出（示意，据 K8s 官方文档）：

```text
Events:
  Type     Reason     Age               From               Message
  ----     ------     ----              ----               -------
  Warning  Unhealthy  2m (x3 over 3m)   kubelet            Readiness probe failed: Get "http://10.244.1.20:8080/ready": dial tcp: connect: connection refused
```

- 就绪探针连不上 `:8080/ready`：要么服务没监听这个端口/路径，要么应用还没起来。
- 这时候 Pod 不会被 Service 选中，外部访问不到。

### 示例 5：describe 节点，看资源和压力

```bash
kubectl describe node node-2
```

输出（示意，据 K8s 官方文档）：

```text
Capacity:
  cpu:                8
  ephemeral-storage:  ...
  memory:             32Gi
Allocatable:
  cpu:                7800m
  memory:             31Gi
System Info:
  Kernel Version:      5.15.0-105-generic
  Container Runtime:  containerd://1.7.18
Conditions:
  Type             Status
  MemoryPressure   False
  DiskPressure     False
  PIDPressure      False
  Ready            True
```

- `Capacity` 是物理总量，`Allocatable` 是真正能给 Pod 用的量；
- `Conditions` 全 `False`（压力类）+ `Ready=True` 才健康。

### 示例 6：按标签 describe 一批

```bash
kubectl describe pods -l app=nginx
```

> 会把 `app=nginx` 的每个 Pod 都 describe 一遍，逐个看 Events。

### 示例 7：用名称前缀批量 describe

```bash
kubectl describe pods nginx
```

> 先找有没有正好叫 `nginx` 的 Pod；没有就把所有名字以 `nginx` 开头的 Pod 都 describe 出来。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `kubectl describe pod 名` | 看 Pod 详情 + Events（**排障首选**） |
| `kubectl describe node 名` | 看节点容量/压力/运行时 |
| `kubectl describe deploy 名` | 看 Deployment 滚动状态 |
| `kubectl describe pod -l app=nginx` | 看标签选中的一批 Pod |
| `kubectl describe pod 名` 末尾 Events | Pending/Crash/探针失败的答案 |

## 六、RHEL 系与 Debian 系差异

`describe` 读的是 apiserver 里的对象，与本机发行版无关，两系**用法一致**。输出里的 `Kernel Version`、`OS Image`、`Container Runtime` 字段会因节点实际系统不同而不同，但命令和字段名不变。

## 七、新手易错点

1. **只看上半部分、不看 Events**：排障的关键在最后 `Events:` 那几行，一定要滚到底。
2. **`Warning` 不是立刻崩**：Events 是历史时间线，旧的 Warning 可能早已恢复，注意看 `Age` 和时间顺序。
3. **Pending 别狂删 Pod**：删了调度器还是选不出节点，要看 `FailedScheduling` 的 Message（资源不足/污点/亲和性）。
4. **CrashLoopBackOff 要看 `--previous` 日志**：describe 只告诉你"崩了"，为什么崩要去看 [logs](./logs)。
5. **describe 是只读的**：不改集群，放心反复看。
6. **一个容器 Pod 不用指定 `-c`**；多容器 Pod describe 会把每个容器都列出来，日志才需要 `-c` 区分。

## 八、相关命令与文档

- 速查页：[kubectl 命令速查](../kubectl-commands#调试与排障)
- 看状态简表：[get 详解](./get)
- 看崩溃前的日志：[logs 详解](./logs)
- 进容器里查：[exec 详解](./exec)
- 概念补课（Pod 生命周期/探针）：[Pod 与服务发现](../../guide/container-k8s-02-pod-service-discovery)
- 官方命令参考：https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands#describe
