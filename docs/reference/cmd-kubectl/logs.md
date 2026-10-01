# kubectl logs 命令详解：看容器日志、排查崩溃

> 本文是 [kubectl 命令速查](../kubectl-commands#调试与排障) 中 `kubectl logs` 的从 0 到 1 详解。
> 目标：把 `kubectl logs --help` 里的每个选项讲清楚，多看几遍后，你在服务器上敲 `kubectl logs --help` 就知道该用哪个选项。
> 环境依据：kubectl 客户端，对应 **Kubernetes 1.35**（本机沙箱未安装，选项依据 K8s 官方命令参考核实；示例输出均为「示意，据 K8s 官方文档」）。

## 一、命令是干什么的

`logs` 用来**打印容器的标准输出日志**。容器里的程序把日志打到 stdout/stderr，kubelet 收集起来，`kubectl logs` 就是把它拉到你屏幕上。

- Pod 起不来、CrashLoopBackOff：`describe` 告诉你"崩了"，`logs` 告诉你"为什么崩"；
- 服务报错想现场看：`logs -f` 实时跟踪；
- 多容器 Pod：用 `-c` 指定看哪个容器。

> 类比：`kubectl logs` 像远程登录到那台机器，tail 一下应用日志。区别是你不用知道 Pod 跑在哪台节点上，kubectl 帮你找到 kubelet 去取。

## 二、命令语法

```bash
kubectl logs [-f] [-p] (POD | 类型/名称) [-c 容器]
```

- `POD`：Pod 名；也支持 `deployment/名`、`job/名` 这种写法，kubectl 自动选它管的一个 Pod。
- `-c 容器`：多容器 Pod 时指定看哪个；单容器可省略。
- 只读命令。

```bash
kubectl logs nginx-6f5b9d7c8-x2zqk
```

## 三、选项全表（对照 `kubectl logs --help`）

### 1. 看哪个 Pod / 哪个容器

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `POD` | 指定 Pod 名 | 最常用 |
| `类型/名称` | 如 `deploy/nginx`、`job/hello` | 不关心具体哪个 Pod，看工作负载即可 |
| `-c 容器`，`--container` | 指定多容器 Pod 里的哪个容器 | sidecar/init 同 Pod 时分容器看 |
| `-l 标签`，`--selector` | 看匹配标签的 Pod 的日志 | 不指定具体 Pod 时 |
| `--all-containers=true` | 一个 Pod 里所有容器的日志都打出来 | sidecar 多时省事 |

### 2. 看多少 / 看哪段

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `--tail=行数` | 只打最后 N 行 | 日志巨多，只要尾部（如 `--tail=20`） |
| `--since=时长` | 只看最近多久，如 `5s`、`2m`、`1h` | 只关心最近一小时 |
| `--since-time=RFC3339` | 只看某时间点之后 | 精确到时刻排障 |
| `--limit-bytes=字节` | 最多返回多少字节日志 | 日志超大、怕刷屏 |
| `--timestamps` | 每行日志前加时间戳 | 想看每条日志几点打的 |
| `--prefix` | 每行加 Pod 名/容器名前缀 | 多 Pod 混看时分清谁是谁 |

### 3. 持续跟踪与历史容器

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-f`，`--follow` | 持续跟踪，不退出，新日志实时打出来 | 线上盯日志（最常用） |
| `-p`，`--previous` | 看**上一个**已终止容器的日志 | CrashLoopBackOff 后看上一次崩溃的日志 |
| `--max-log-requests=N` | 用 `-l` 选多个 Pod 时最多并发跟几个（默认 5） | 标签选中 Pod 太多时控制并发 |
| `--ignore-errors` | 跟踪时遇到错误不中断 | 批量跟日志、个别 Pod 挂了不影响 |

## 四、由浅入深的典型示例

### 示例 1：看单容器 Pod 的日志

```bash
kubectl logs nginx-6f5b9d7c8-x2zqk
```

输出（示意，据 K8s 官方文档）：

```text
10.244.1.1 - - [29/Sep/2026:10:05:21 +0800] "GET / HTTP/1.1" 200 612 "-" "curl/7.81.0"
10.244.1.2 - - [29/Sep/2026:10:05:22 +0800] "GET /healthz HTTP/1.1" 200 2 "-" "kube-probe/1.35"
```

> 就是容器 stdout 的内容，原样打出来。

### 示例 2：实时跟踪日志（最常用）

```bash
kubectl logs -f nginx-6f5b9d7c8-x2zqk
```

> 加 `-f` 后命令不退出，有新日志就打出来，像 `tail -f`。`Ctrl+C` 退出。

### 示例 3：只看最后 20 行

```bash
kubectl logs --tail=20 nginx-6f5b9d7c8-x2zqk
```

> 容器跑了几天、日志几十万行，`--tail=20` 只要末尾，秒出。

### 示例 4：只看最近一小时

```bash
kubectl logs --since=1h nginx-6f5b9d7c8-x2zqk
```

> 时间相关，不用翻历史。`--since=2m` 就是最近两分钟。

### 示例 5：看崩溃前上一个容器的日志（排 CrashLoop 关键）

```bash
kubectl logs -p nginx-crash-xxx -c app
```

> 容器在不停重启，当前容器的日志可能是空的；`-p`（`--previous`）看上一个已经退出的容器，它崩之前打的报错才是关键。

### 示例 6：多容器 Pod 指定容器

```bash
kubectl logs nginx-6f5b9d7c8-x2zqk -c nginx
```

> Pod 里有 nginx 和一个 sidecar 时，`-c nginx` 只看 nginx 容器，不看 sidecar。

### 示例 7：看一个 Pod 里所有容器的日志

```bash
kubectl logs nginx-6f5b9d7c8-x2zqk --all-containers=true
```

> 不加 `-c` 又想全包，就用 `--all-containers`。

### 示例 8：按标签批量跟踪日志

```bash
kubectl logs -f -l app=nginx --all-containers=true
```

> `app=nginx` 的所有 Pod 日志一起跟。默认最多并发跟 5 个，超了用 `--max-log-requests` 调大。

### 示例 9：看 Deployment 管的 Pod 日志

```bash
kubectl logs deploy/nginx -c nginx
```

> 不用先 `get pods` 找到具体 Pod 名，直接 `deploy/nginx`，kubectl 自动选一个 Pod。

### 示例 10：日志带时间戳和前缀

```bash
kubectl logs -f nginx-xxx --timestamps --prefix
```

输出（示意，据 K8s 官方文档）：

```text
default/nginx-6f5b9d7c8-x2zqk/nginx 2026-09-29T10:05:21.123Z 10.244.1.1 - - "GET / HTTP/1.1" 200 612
```

> 多 Pod 混看时，`--prefix` 让你知道这行来自哪个 Pod 哪个容器。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `kubectl logs pod名` | 看当前日志 |
| `kubectl logs -f pod名` | 实时跟踪（**最常用**） |
| `kubectl logs --tail=20 pod名` | 只看最后 20 行 |
| `kubectl logs --since=1h pod名` | 看最近一小时 |
| `kubectl logs -p pod名 -c 容器` | 看上一个崩溃容器 |
| `kubectl logs pod名 -c 容器` | 多容器指定容器 |
| `kubectl logs -f -l app=nginx --all-containers` | 标签批量跟踪 |
| `kubectl logs deploy/nginx` | 直接看工作负载日志 |

## 六、RHEL 系与 Debian 系差异

`logs` 取的是 kubelet 收集的容器 stdout，与本机发行版无关，两系**用法一致**。唯一相关的差异在节点侧：容器运行时是 containerd 还是别的、日志驱动怎么配，会影响"日志从哪来"，但 `kubectl logs` 命令本身不变。

## 七、新手易错点

1. **CrashLoopBackOff 看当前日志是空的**：一定要加 `-p`（`--previous`）看上一个崩溃容器的日志。
2. **多容器 Pod 不指定 `-c`**：默认看第一个容器，可能不是你想看的那个 sidecar。
3. **`-f` 卡住不退**：它是持续跟踪，不是卡死；`Ctrl+C` 退出。
4. **日志只在容器没删时可查**：Pod 被删重建后，旧容器日志就没了；需要长期留存请接 Loki/EFK 等日志系统。
5. **`--since` 和 `--since-time` 二选一**：别同时用。
6. **`logs` 是只读的**：不改集群，放心看。
7. **任务里提到的 `--max-log-chars` 不是真实 flag**：官方对应的是 `--limit-bytes`（按字节限制），别按博客里的 `--max-log-chars` 敲。

## 八、相关命令与文档

- 速查页：[kubectl 命令速查](../kubectl-commands#调试与排障)
- 看 Pod 为什么崩：[describe 详解](./describe)
- 进容器里手查：[exec 详解](./exec)
- 实时把本地端口对到 Pod：[port-forward 详解](./port-forward)
- 概念补课：[Pod 与服务发现](../../guide/container-k8s-02-pod-service-discovery)
- 官方命令参考：https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands#logs
