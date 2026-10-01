# kubectl scale 命令详解：手动扩缩容副本数

> 本文是 [kubectl 命令速查](../kubectl-commands#编辑伸缩与删除) 中 `kubectl scale` 的从 0 到 1 详解。
> 目标：把 `kubectl scale --help` 里的每个选项讲清楚，多看几遍后，你在服务器上敲 `kubectl scale --help` 就知道该用哪个选项。
> 环境依据：kubectl 客户端，对应 **Kubernetes 1.35**（本机沙箱未安装，选项依据 K8s 官方命令参考核实；示例输出均为「示意，据 K8s 官方文档」）。

## 一、命令是干什么的

`scale` 用来**手动把某个工作负载的副本数改成指定值**。流量来了加副本、夜深了减副本，一条命令的事。

- `kubectl scale deploy nginx --replicas=5`：从当前副本数扩到 5；
- 支持 Deployment、ReplicaSet、ReplicationController、StatefulSet。

> 类比：scale 像调水龙头——直接把"要几个 Pod"拨到目标数，控制器负责把现在的数量变成目标数量。它是**手动**的；想按 CPU 自动伸缩要用 HPA（见下文简述）。

## 二、命令语法

```bash
kubectl scale [--resource-version=版本] [--current-replicas=数量] --replicas=N (-f 文件 | 类型 名称)
```

- `--replicas=N`：必填，目标副本数；
- `--current-replicas=N`：可选，前置条件——只有当前副本数正好等于 N 才执行（乐观锁）；
- `-f 文件`：按文件里的资源 scale；
- 可一次 scale 多个资源。

```bash
kubectl scale --replicas=3 deployment/nginx
```

## 三、选项全表（对照 `kubectl scale --help`）

### 1. 目标副本与前置条件

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `--replicas=N` | 目标副本数（必填） | 最核心 |
| `--current-replicas=N` | 前置：当前副本数正好是 N 才缩放 | 避免和别人并发改冲突 |
| `--resource-version=版本` | 前置：资源版本匹配才执行 | 乐观锁防覆盖 |

### 2. 指定 scale 谁

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `类型 名称` | 如 `deploy/nginx`、`sts/web` | 最常用 |
| `-f 文件`，`--filename` | 按文件里的资源 | 对着清单 scale |
| `-l 标签`，`--selector` | scale 匹配标签的资源 | 批量 |
| `--all` | scale 当前 ns 该类型所有资源 | 慎用 |

### 3. 其他

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `--timeout=时长` | 等待 scale 完成的超时 | 如 `--timeout=2m` |
| `--dry-run=client\|server` | 试运行不真正改 | 先看 |
| `-o yaml` | 输出改后的对象 | 核对 |

## 四、由浅入深的典型示例

### 示例 1：把 Deployment 扩到 3 副本

```bash
kubectl scale --replicas=3 deployment/nginx
```

输出（示意，据 K8s 官方文档）：

```text
deployment.apps/nginx scaled
```

### 示例 2：按文件 scale

```bash
kubectl scale --replicas=3 -f foo.yaml
```

> 文件里写的是哪个资源，就 scale 哪个。

### 示例 3：带前置条件的安全 scale

```bash
kubectl scale --current-replicas=2 --replicas=3 deployment/mysql
```

> 只有当 mysql **当前正好是 2 副本**时才改成 3；如果别人已经改成 5 了，这条就不执行，避免覆盖别人的操作。

### 示例 4：一次 scale 多个资源

```bash
kubectl scale --replicas=5 rc/foo rc/bar rc/baz
```

> 三个 RC 一起改成 5。

### 示例 5：缩容到 0（临时停服）

```bash
kubectl scale --replicas=0 deployment/nginx
```

> 副本数 0 = 没有 Pod 跑，等于"停服"但保留 Deployment 配置；要恢复再 scale 回正数。

### 示例 6：scale StatefulSet

```bash
kubectl scale --replicas=3 statefulset/web
```

> StatefulSet 也能 scale，不过它的 Pod 是按序一个个来的。

### 示例 7：scale 后观察

```bash
kubectl scale --replicas=5 deployment/nginx
kubectl get pods -w
```

> scale 完用 `-w` 盯着 Pod 一个个被拉起来。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `kubectl scale deploy/名 --replicas=5` | 扩到 5 副本（**最常用**） |
| `kubectl scale deploy/名 --replicas=0` | 临时停服 |
| `kubectl scale --current-replicas=2 --replicas=3 deploy/mysql` | 带条件安全扩 |
| `kubectl scale sts/web --replicas=3` | 扩 StatefulSet |
| `kubectl scale --replicas=5 rc/a rc/b` | 批量 scale |

## 六、与 HPA（自动伸缩）的关系

`scale` 是**手动**设一个固定副本数；HPA（HorizontalPodAutoscaler）是**自动**按 CPU/内存/自定义指标在 min~max 之间浮动：

```bash
kubectl autoscale deployment foo --min=2 --max=10 --cpu-percent=80
```

- 如果一个 Deployment 已经被 HPA 管着，你再用 `kubectl scale` 手动改副本数，HPA 很快又会把它拉回自己认为合适的值；
- 想手动固定，先 `kubectl delete hpa foo`。

## 七、RHEL 系与 Debian 系差异

scale 操作集群，两系**用法一致**，无发行版差异。

## 八、新手易错点

1. **被 HPA 接管后手动 scale 不生效**：你改成 5，HPA 看 CPU 低又给你缩回去；先删 HPA。
2. **`--replicas=0` 等于停服**：Pod 全删，但 Service/Deployment 还在；不是删 Deployment，别和 `delete` 混。
3. **缩容不是立刻没流量**：滚动终止要等优雅退出，长连接业务要配合 `preStop` 和 `terminationGracePeriodSeconds`。
4. **StatefulSet 缩容从后往前删**：`web-2` 先删、`web-0` 最后删，有状态数据要注意 PVC。
5. **`--current-replicas` 用错会静默不执行**：前置条件不满足时命令"成功"但没改，注意看输出。
6. **scale 不是滚动发布**：改副本数不会换镜像；换镜像用 `set image` / `rollout`（见 [rollout 与 set 详解](./rollout-set)）。

## 九、相关命令与文档

- 速查页：[kubectl 命令速查](../kubectl-commands#编辑伸缩与删除)
- 滚动发布/回滚：[rollout 与 set 详解](./rollout-set)
- 局部改副本数：[patch 详解](./rollout-set)
- 概念补课（工作负载）：[Pod 与服务发现](../../guide/container-k8s-02-pod-service-discovery)
- 官方命令参考：https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands#scale
