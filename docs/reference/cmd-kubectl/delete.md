# kubectl delete 命令详解：删资源（高危，务必看清再回车）

> 本文是 [kubectl 命令速查](../kubectl-commands#编辑伸缩与删除) 中 `kubectl delete` 的从 0 到 1 详解。
> 目标：把 `kubectl delete --help` 里的每个选项讲清楚，多看几遍后，你在服务器上敲 `kubectl delete --help` 就知道该用哪个选项。
> 环境依据：kubectl 客户端，对应 **Kubernetes 1.35**（本机沙箱未安装，选项依据 K8s 官方命令参考核实；示例输出均为「示意，据 K8s 官方文档」）。

## 一、命令是干什么的

`delete` 用来**删除集群里的资源**。它是 kubectl 里**最危险**的命令之一——删错了线上服务直接挂。但删 Pod 往往不致命（控制器会重建），删 Deployment/Service/Namespace 才是大事。

> 类比：`delete` 像 `rm`，但删的是集群里跑着的服务。务必像对待 `rm -rf` 一样敬畏它。

## 二、命令语法

```bash
kubectl delete (-f 文件 | -k 目录 | 类型 [(名称 | -l 标签 | --all)])
```

- 三种方式：按文件删、按"类型+名称"删、按标签删；
- 一次只能用一种指定方式（文件 / 类型+名 / 类型+标签）；
- 支持优雅删除（grace period）。

```bash
kubectl delete pod nginx-xxx
```

## 三、选项全表（对照 `kubectl delete --help`）

### 1. 删谁

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `类型 名称` | 删指定类型的指定资源 | 如 `delete pod nginx-xxx` |
| `-f 文件`，`--filename` | 按清单里的类型+名删 | `delete -f nginx.yaml` |
| `-k 目录`，`--kustomize` | 按 kustomization 删 | kustomize 管理的整套 |
| `-l 标签`，`--selector` | 删匹配标签的资源 | `delete pods -l app=nginx` |
| `--all` | 删当前 ns 该类型**所有** | 慎用 |
| `--field-selector=字段=值` | 按字段删 | 如删所有 Pending Pod |
| `-A`，`--all-namespaces` | 跨命名空间 | 慎用 |

### 2. 删除方式（高危区）

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `--now` | 立即删除（等价 grace-period=1） | 不等优雅退出 |
| `--grace-period=秒` | 优雅等待秒数；只有配 `--force` 才能设 0 | 给业务留收尾时间 |
| `--force` | **绕过优雅删除、立刻从 API 移除** | 节点挂了 Pod 删不掉时（危险） |
| `--cascade=background\|orphan\|foreground` | 级联删除策略 | 是否连从属资源（如 RS/Pod）一起删 |
| `--wait`（默认 true） | 等到资源真消失才返回 | 默认等；`--wait=false` 不等 |
| `--timeout=时长` | 等待删除超时 | 如 `--timeout=30s` |
| `--ignore-not-found` | 资源不存在也当成功 | 脚本里防报错 |
| `-o name` | 只打印被删资源名 | 精简输出 |

## 四、由浅入深的典型示例

### 示例 1：删一个 Pod

```bash
kubectl delete pod nginx-6f5b9d7c8-x2zqk
```

输出（示意，据 K8s 官方文档）：

```text
pod "nginx-6f5b9d7c8-x2zqk" deleted
```

> 由 Deployment 管的 Pod 删了会被自动重建一个新的——所以"删 Pod"常用来强制重启。

### 示例 2：按文件删

```bash
kubectl delete -f nginx.yaml
```

> 文件里有什么就删什么，和 `apply -f` 对应。

### 示例 3：按标签删

```bash
kubectl delete pods -l app=nginx
```

> 删掉所有 `app=nginx` 的 Pod。

### 示例 4：删 Deployment（连带它的 Pod）

```bash
kubectl delete deployment nginx
```

> 默认 `--cascade=background`：删 Deployment 时连带把它管的 RS、Pod 一起删掉。**这是真删服务**。

### 示例 5：优雅删除 vs 立即

```bash
kubectl delete pod foo --now
kubectl delete pod foo --grace-period=60
```

- `--now`：grace-period=1，赶紧删；
- `--grace-period=60`：给容器 60 秒优雅收尾（在途请求处理完）再删。

### 示例 6：节点挂了，强删 Pod（危险）

```bash
kubectl delete pod foo --force --grace-period=0
```

> 官方警告：`--force` 不等进程真正结束就移除，可能导致**多个副本同时运行、写共享存储的数据不一致**。只有确定 Pod 所在节点已死、或业务能容忍多副本并发时才用。

### 示例 7：按字段删（删所有 Pending Pod）

```bash
kubectl delete pods --field-selector status.phase=Pending
```

> 把没调度上的 Pod 一次清掉。

### 示例 8：删命名空间（核弹级）

```bash
kubectl delete namespace dev
```

> 会把这个 ns 里**所有**资源（Pod、Svc、Deploy、Secret…）全删掉。删之前千看万看。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `kubectl delete pod 名` | 删 Pod（会被重建，常用于重启） |
| `kubectl delete -f 文件.yaml` | 按清单删 |
| `kubectl delete pods -l app=nginx` | 按标签删 Pod |
| `kubectl delete deploy 名` | 删 Deployment（连带 Pod） |
| `kubectl delete pod 名 --now` | 立即删 |
| `kubectl delete ns 名` | 删命名空间（**核弹，慎之又慎**） |
| `kubectl delete pod 名 --force --grace-period=0` | 节点死了强删（危险） |

## 六、RHEL 系与 Debian 系差异

delete 操作集群，两系**用法一致**，无发行版差异。

## 七、新手易错点（高危必读）

1. **删 Pod 不等于删服务**：由 Deployment/RS 管的 Pod 删了会被重建；要真停服务得删 Deployment。
2. **`delete namespace` 是核弹**：整个 ns 里所有资源灰飞烟灭，删前 `kubectl get all -n 名` 先看清楚。
3. **`--force` 可能数据不一致**：官方明确警告强删可能让同一 Pod 在另一处还活着、写共享存储导致脏数据。
4. **`--all` 别乱加**：`kubectl delete pods --all` 会把当前 ns Pod 全删，配合 `-A` 全集群删，事故级。
5. **delete 不做 resourceVersion 检查**：你提交删除的瞬间别人刚改过这个资源，改动会随资源一起没掉。
6. **删 CRD 后缓存可能 6 小时不刷新**：删完 CRD 想立刻 `get` 看不到，跑一次 `kubectl api-resources` 刷新。
7. **删前先 `get` 确认**：养成习惯——`kubectl get deploy 名` 看一眼确实是它，再 `delete`。
8. **级联删除默认开**：删 Deployment 默认连 Pod 一起删；想保留 Pod 才需 `--cascade=orphan`，一般别碰。

## 八、相关命令与文档

- 速查页：[kubectl 命令速查](../kubectl-commands#编辑伸缩与删除)
- 扩缩容而不是删：[scale 详解](./scale)
- 声明式对齐删除（prune）：[apply 与 create 详解](./apply-create)
- 概念补课：[K8s 架构与集群](../../guide/container-k8s-01-architecture-cluster)
- 官方命令参考：https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands#delete
