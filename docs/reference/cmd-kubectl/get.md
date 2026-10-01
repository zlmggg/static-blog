# kubectl get 命令详解：查看集群里的一切资源

> 本文是 [kubectl 命令速查](../kubectl-commands#资源查看) 中 `kubectl get` 的从 0 到 1 详解。
> 目标：把 `kubectl get --help` 里的每个选项讲清楚，多看几遍后，你在服务器上敲 `kubectl get --help` 就知道该用哪个选项。
> 环境依据：kubectl 客户端，对应 **Kubernetes 1.35**（本机沙箱未安装，选项依据 K8s 官方命令参考核实；示例输出均为「示意，据 K8s 官方文档」）。

## 一、命令是干什么的

`get` 是 kubectl 里**用得最多**的命令，没有之一。它的作用就一句话：**把集群里的某类资源列出来，用表格展示最关键的几列信息**。

- 看 Pod 跑没跑起来：`kubectl get pods`
- 看 Service 暴露了什么端口：`kubectl get svc`
- 看 Deployment 副本数对不对：`kubectl get deploy`
- 导出某个资源的完整 YAML：`kubectl get pod 名 -o yaml`

> 类比：`kubectl get` 就像 Windows 任务管理器 / 文件资源管理器——你想知道"现在有什么、状态咋样"，第一个动作永远是它。它是**只读**的，随便敲，不会改集群。

常用资源缩写（背下来，后面天天用）：

| 缩写 | 全称 | 缩写 | 全称 |
|---|---|---|---|
| `po` | pod | `cm` | configmap |
| `svc` | service | `secret` | secret |
| `deploy` | deployment | `ns` | namespace |
| `ing` | ingress | `pv` | persistentvolume |
| `sts` | statefulset | `pvc` | persistentvolumeclaim |
| `ds` | daemonset | `rs` | replicaset |

## 二、命令语法

```bash
kubectl get [类型] [名称 | -l 标签]... [选项]
```

- `[类型]`：要看哪类资源，可写全称（`pod`）或缩写（`po`）；可一次给多个类型（`po,svc,deploy`）。
- `[名称]`：不给就列该类**全部**；给名字就看那一个；也支持 `类型/名称` 写法（`pod/nginx-xxx`）。
- `[选项]`：控制命名空间、输出格式、过滤、排序、监听等。

默认行为：不加 `-n` 只看**当前命名空间**的资源；加 `-A` 才看所有命名空间。

## 三、选项全表（对照 `kubectl get --help`）

### 1. 看哪个范围（命名空间 / 过滤）

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-n 命名空间`，`--namespace` | 只看指定命名空间 | 资源在别的 ns 时（最常用） |
| `-A`，`--all-namespaces` | 跨**所有**命名空间看 | 想全局看一遍时（如 `get pods -A`） |
| `-l 标签`，`--selector` | 按标签过滤，支持 `=`、`==`、`!=` | 只看 `app=nginx` 的那批 Pod |
| `--field-selector=字段=值` | 按资源**字段**过滤（非标签） | 如 `status.phase=Pending`、`spec.nodeName=node-2` |
| `--show-labels` | 最后加一列，把所有标签列出来 | 想看对象打了哪些标签 |
| `-L 标签键`，`--label-columns` | 把指定标签**提成单独一列** | 如 `-L app,env` 一眼看到每个 Pod 的 app/env |

### 2. 输出格式 `-o`

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-o wide` | 更宽的表格（Pod 显示 IP、所在节点） | 排障定位"Pod 跑在哪台机"（最常用） |
| `-o yaml` | 输出完整 YAML 对象 | 导出配置、改完 apply 回去 |
| `-o json` | 输出完整 JSON 对象 | 给 `jq` 处理、写脚本 |
| `-o name` | 只输出 `类型/名字`，不要表格 | 输出接管道喂给下一条命令 |
| `-o jsonpath=模板` | 用 jsonpath 精确取某个字段 | 如只取 Pod 的 `.status.podIP` |
| `-o custom-columns=...` | 自定义列名=字段 | 只显示你关心的几列 |

### 3. 监听与排序

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-w`，`--watch` | 列出后**持续监听**变化 | 边改边看 Pod 状态切换 |
| `--watch-only` | 不先列，直接监听变化 | 只关心后续事件 |
| `--sort-by=JSONPath` | 按某字段排序 | 如 `--sort-by=.metadata.creationTimestamp` |
| `--no-headers` | 不打印表头 | 输出接 awk/xargs 时 |
| `--show-kind` | 输出里带上资源类型 | 一次看多种资源、分不清谁是谁时 |

### 4. 从文件 / kustomization 取资源

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-f 文件`，`--filename` | 按文件里的资源类型+名字 get | 对着清单查资源 |
| `-k 目录`，`--kustomize` | 按 kustomization 目录 get | 用 kustomize 管理的部署 |
| `-R`，`--recursive` | 递归处理 `-f` 指定的目录 | 目录套目录时 |
| `--chunk-size=500` | 大列表分块返回 | 资源成千上万、单次查询超时 |

## 四、由浅入深的典型示例

### 示例 1：最基础——看当前命名空间的 Pod

```bash
kubectl get pods
```

输出（示意，据 K8s 官方文档）：

```text
NAME                       READY   STATUS    RESTARTS   AGE
nginx-6f5b9d7c8-x2zqk      1/1     Running   0          2h
redis-0                    1/1     Running   0          5d
```

- `READY`：`1/1` 表示这个 Pod 里 1 个容器都 Ready；`0/1` 就是没起来。
- `STATUS`：`Running` 正常；`Pending` 没调度上；`CrashLoopBackOff` 一直崩。
- `RESTARTS`：重启次数，突然变多要警惕。

### 示例 2：跨所有命名空间看 Pod

```bash
kubectl get pods -A
```

输出（示意，据 K8s 官方文档）：

```text
NAMESPACE      NAME                       READY   STATUS    RESTARTS   AGE
default        nginx-6f5b9d7c8-x2zqk      1/1     Running   0          2h
kube-system    coredns-7c9f8d4d5-abcde    1/1     Running   0          10d
kube-system    coredns-7c9f8d4d5-fghij    1/1     Running   0          10d
```

- 多了 `NAMESPACE` 列；系统组件都在 `kube-system` 里。

### 示例 3：指定命名空间

```bash
kubectl get pods -n kube-system
```

> `-n` 是 `-A` 的反面：只盯一个 ns。日常开发都在某个 ns 里操作，用得极多。

### 示例 4：加 `-o wide`，看 Pod IP 和节点

```bash
kubectl get pods -o wide
```

输出（示意，据 K8s 官方文档）：

```text
NAME                    READY   STATUS    RESTARTS   AGE   IP            NODE    NOMINATED NODE   READINESS GATES
nginx-6f5b9d7c8-x2zqk  1/1     Running   0          2h    10.244.1.15   node-2  <none>           <none>
```

- `IP`：Pod 内网 IP；`NODE`：跑在哪台节点上。排网络问题时这俩列必看。

### 示例 5：一次看多种资源

```bash
kubectl get svc,deploy,ingress
```

> 类型之间用逗号隔开，一次把 Service、Deployment、Ingress 都列出来，省得敲三条。

### 示例 6：导出某个 Pod 的完整 YAML

```bash
kubectl get pod nginx-6f5b9d7c8-x2zqk -o yaml
```

> 这是"抄现有配置改一改"的标准做法：`get -o yaml` 拿到底稿，改完 `kubectl apply -f` 回去。想存盘就加 `> pod.yaml`。

### 示例 7：按标签过滤

```bash
kubectl get pods -l app=nginx
```

> 只列出带 `app=nginx` 标签的 Pod。多个条件用逗号：`-l app=nginx,env=prod`（都要满足）。

### 示例 8：按字段过滤（field-selector）

```bash
kubectl get pods --field-selector status.phase=Pending
```

> 标签是你自己打的，字段是对象天生的。这条直接捞出**所有还没调度上的 Pod**，排 Pending 时超好用。

### 示例 9：把标签提成列 + 显示全部标签

```bash
kubectl get pods -L app,env --show-labels
```

> `-L app,env` 把 `app`、`env` 提成两列；`--show-labels` 再附一列全量标签。

### 示例 10：持续监听变化（watch）

```bash
kubectl get pods -w
```

> 会卡住不退出，盯着 Pod 列表实时刷新；另一个终端去删/扩缩容，这里能看到状态跳变。`Ctrl+C` 退出。

### 示例 11：按时间排序看事件/资源

```bash
kubectl get events --sort-by=.metadata.creationTimestamp
```

> 事件默认是乱序的，按 `creationTimestamp` 排序后，最新的事件在最下面，排障从下往上看。

### 示例 12：只输出名字，喂给下一条命令

```bash
kubectl get pods -l app=nginx -o name
```

输出（示意，据 K8s 官方文档）：

```text
pod/nginx-6f5b9d7c8-x2zqk
pod/nginx-6f5b9d7c8-yk7md
```

> `-o name` 只给 `pod/xxx`，配合 `xargs` 批量操作：`kubectl get pods -l app=nginx -o name | xargs kubectl delete`。

### 示例 13：不打印表头，接脚本

```bash
kubectl get pods -n dev --no-headers
```

> 没有表头行，输出每行就是一个 Pod 名，方便 `awk`/`while read` 处理。

### 示例 14：用 jsonpath 精确取 Pod IP

```bash
kubectl get pod nginx-6f5b9d7c8-x2zqk -o jsonpath='{.status.podIP}'
```

> 只打印 `10.244.1.15`，不打印别的。写脚本取字段全靠它。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `kubectl get pods` | 看当前 ns 的 Pod |
| `kubectl get pods -A` | 看所有 ns 的 Pod |
| `kubectl get pods -n ns名` | 看指定 ns |
| `kubectl get pods -o wide` | 看 Pod IP + 节点（**最常用**） |
| `kubectl get pod 名 -o yaml` | 导出 YAML |
| `kubectl get svc,deploy,ing` | 一次看多种资源 |
| `kubectl get pods -l app=nginx` | 按标签过滤 |
| `kubectl get pods --field-selector status.phase=Pending` | 找没调度上的 Pod |
| `kubectl get pods -w` | 实时监听 |
| `kubectl get events --sort-by=.metadata.creationTimestamp` | 按时间看事件 |
| `kubectl get pods -o name` | 只取名字，接管道 |
| `kubectl get all` | 看常用资源一整屏 |

## 六、RHEL 系与 Debian 系差异

`get` 操作的是集群，两系用法**完全一致**。唯一要注意的是：

- 资源缩写（po/svc/deploy…）是 kubectl 内置的，跟操作系统无关；
- 老版本里 `--all-namespaces` 是全称，`-A` 是它的短写，两者等价，1.35 都支持；
- 输出里的 `CONTAINER-RUNTIME`、`OS-IMAGE` 列内容会因节点系统不同而不同，但命令本身不变。

## 七、新手易错点

1. **看不到别的命名空间的 Pod**：默认只看当前 ns，记得加 `-n` 或 `-A`。
2. **`-o wide` 不是万能**：它只对部分资源加列；Pod 才显示 IP/节点，Node 显示的是内核/运行时。
3. **`--sort-by` 要写 JSONPath 路径**：不是随便写字段名，要写 `.metadata.creationTimestamp` 这种点路径。
4. **`-l` 和 `--field-selector` 别混**：`-l` 按标签，`--field-selector` 按对象字段，两者过滤维度不同。
5. **`get` 是只读的，放心敲**：它不会改集群；但别顺手敲成 `delete`。
6. **`-o yaml` 里带 `resourceVersion`、`uid`**：直接拿这份 YAML 去 `apply` 可能冲突，生产建议用 `kubectl apply --prune` 或重新维护干净清单。
7. **资源名别拼错缩写**：`ing` 是 ingress，`sts` 是 statefulset，`ds` 是 daemonset，拼错会报 `the server doesn't have a resource type`。

## 八、相关命令与文档

- 速查页：[kubectl 命令速查](../kubectl-commands#资源查看)
- 看资源详情和 Events：[describe 详解](./describe)
- 看日志：[logs 详解](./logs)
- 删资源：[delete 详解](./delete)
- 概念补课（Pod/Service）：[Pod 与服务发现](../../guide/container-k8s-02-pod-service-discovery)
- 官方命令参考：https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands#get
