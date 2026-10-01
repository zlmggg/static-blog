# kubectl exec 命令详解：进到容器里执行命令

> 本文是 [kubectl 命令速查](../kubectl-commands#调试与排障) 中 `kubectl exec` 的从 0 到 1 详解。
> 目标：把 `kubectl exec --help` 里的每个选项讲清楚，多看几遍后，你在服务器上敲 `kubectl exec --help` 就知道该用哪个选项。
> 环境依据：kubectl 客户端，对应 **Kubernetes 1.35**（本机沙箱未安装，选项依据 K8s 官方命令参考核实；示例输出均为「示意，据 K8s 官方文档」）。

## 一、命令是干什么的

`exec` 用来**在 Pod 里的某个容器中执行命令**。最常见的就是 `-it` 进去开个 shell，像 SSH 到容器里一样手查。

- 进去看容器里的文件：`kubectl exec -it pod -- bash`
- 不进去，直接跑一条命令拿结果：`kubectl exec pod -- date`

> 类比：`kubectl exec` 像 `docker exec`——不用真的 SSH 到节点，kubectl 通过 apiserver + kubelet 帮你把命令送进容器执行。

## 二、命令语法

```bash
kubectl exec (POD | 类型/名称) [-c 容器] [flags] -- 命令 [参数...]
```

- `--` 前面是 kubectl 的选项，`--` 后面才是**容器里要跑的命令**；
- `-c`：多容器 Pod 指定哪个；
- `-i -t`：交互终端（开 shell 必备）。

```bash
kubectl exec mypod -- date
```

## 三、选项全表（对照 `kubectl exec --help`）

### 1. 在哪个容器执行

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `POD` | 指定 Pod | 最常用 |
| `类型/名称` | 如 `deploy/mydeployment`、`svc/myservice` | 不关心具体 Pod，自动选一个 |
| `-c 容器`，`--container` | 指定多容器 Pod 里的哪个容器 | sidecar 时分容器 |
| `-f 文件`，`--filename` | 从文件取资源 | 较少用 |

### 2. 交互与输出

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-i`，`--stdin` | 把标准输入送进容器 | 开交互 shell 必备 |
| `-t`，`--tty` | 分配伪终端（TTY） | 配合 `-i`，否则 shell 不刷新 |
| `-q`，`--quiet` | 只打印远程会话输出 | 少打提示 |
| `--pod-running-timeout=时长` | 等 Pod 起来的超时 | Pod 还没 Ready 时 |

## 四、由浅入深的典型示例

### 示例 1：在容器里跑一条非交互命令

```bash
kubectl exec mypod -- date
```

输出（示意，据 K8s 官方文档）：

```text
Tue Sep 30 02:00:00 UTC 2026
```

> 不进 shell，直接在容器里跑 `date` 拿结果。

### 示例 2：进容器开交互式 shell（最常用）

```bash
kubectl exec -it mypod -- bash
```

输出（示意，据 K8s 官方文档）：

```text
root@mypod:/#
```

> `-i` 保持输入、`-t` 分配终端，进去就是容器里的 bash。`exit` 退出。

### 示例 3：多容器 Pod 指定容器

```bash
kubectl exec mypod -c ruby-container -- date
```

> Pod 里有多个容器时，`-c` 指定进哪个；不指定默认第一个（或 `default-container` 注解指定的）。

### 示例 4：容器里没有 bash，用 sh

```bash
kubectl exec -it mypod -- sh
```

> 很多精简镜像（distroless、alpine）没有 bash，只有 `sh`；连 sh 都没有的镜像就 exec 不进去，用 `kubectl debug`。

### 示例 5：看容器里的进程/文件

```bash
kubectl exec mypod -- ls -t /usr
```

> 注意：容器里的命令如果自己也带 `-i`、`-t` 这类参数，必须用 `--` 隔开，否则 kubectl 会当成自己的选项。

### 示例 6：对 Deployment 管的 Pod 执行

```bash
kubectl exec deploy/mydeployment -- date
```

> 不用先找 Pod 名，直接 `deploy/名`，kubectl 自动选它管的一个 Pod。

### 示例 7：把容器里的环境变量打出来

```bash
kubectl exec mypod -- env
```

> 进不去交互时，用这条非交互看容器拿到了哪些环境变量。

## 五、与 run / debug 的区别

| 命令 | 作用对象 | 典型用途 |
|---|---|---|
| `kubectl exec` | **已经在跑的** Pod/容器 | 进去查现场、跑命令 |
| `kubectl run` | **新起**一个 Pod | 临时跑个镜像 |
| `kubectl debug` | 给运行中的 Pod 加**临时调试容器**（ephemeral container，1.25 GA） | 原容器镜像里没工具、又不想重启它时 |

- exec 要求容器里有你要跑的命令（如 `sh`）；
- 原容器是 distroless、连 sh 都没有，用 `kubectl debug mypod -it --image=busybox` 挂个调试容器进去。

## 六、高频组合速记

| 命令 | 用途 |
|---|---|
| `kubectl exec -it pod名 -- bash` | 进容器开 shell（**最常用**） |
| `kubectl exec -it pod名 -- sh` | 精简镜像用 sh |
| `kubectl exec pod名 -- 命令` | 非交互跑命令 |
| `kubectl exec pod名 -c 容器 -- 命令` | 多容器指定容器 |
| `kubectl exec deploy/名 -- 命令` | 对工作负载执行 |

## 七、RHEL 系与 Debian 系差异

exec 经 apiserver 进容器，与本机发行版无关，两系**用法一致**。差异在容器镜像本身：基础镜像有没有 bash/sh、有没有你要的工具，决定你能不能 exec 进去。

## 八、新手易错点

1. **忘了 `--`**：`kubectl exec mypod bash` 可能把 bash 当成 kubectl 自己的参数报错；容器命令前一定加 `--`。
2. **只加 `-i` 不加 `-t`**：开 shell 会显示异常（不刷新、没有提示符）；交互用 `-it` 一起加。
3. **镜像里没有 bash**：报 `exec: "bash": executable file not found`，换 `sh` 或用 `kubectl debug`。
4. **distroless 镜像 exec 不进去**：连 sh 都没有，用 `kubectl debug` 挂临时容器。
5. **exec 进去改的东西不持久**：容器重启后改动丢失；要持久化改镜像或挂 PVC/ConfigMap。
6. **多容器 Pod 不指定 `-c`**：默认进第一个容器，可能不是你想看的那个。
7. **`exit` 退出 exec 不影响容器**：只是断开你的会话，容器继续跑。

## 九、相关命令与文档

- 速查页：[kubectl 命令速查](../kubectl-commands#调试与排障)
- 看日志：[logs 详解](./logs)
- 临时调试容器：`kubectl debug`（见官方参考）
- 文件拷贝：[cp 详解](./cp)
- 概念补课：[Pod 与服务发现](../../guide/container-k8s-02-pod-service-discovery)
- 官方命令参考：https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands#exec
