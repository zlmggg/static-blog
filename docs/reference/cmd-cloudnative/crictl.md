# crictl 命令详解：节点上看 K8s 容器的官方工具

> 本文是 [云原生排障命令速查](../cloudnative-commands) 中「containerd / CRI 运行时」一组命令的从 0 到 1 详解，本篇一次讲清 `crictl ps/pods/logs/inspect/images/stats/info/exec/port-forward` 与 `config runtime-endpoint`。
> 目标：kubelet 通过 CRI 跟容器运行时打交道；节点上排查 Pod/容器时，`docker` 往往管不到，得用 `crictl`——看完本篇你就知道每个选项干嘛。
> 环境依据：crictl（cri-tools）v1.35（站内 2026-09 基准），对接 containerd 2.3。本沙箱未装，选项据 cri-tools 官方文档（GitHub raw）核对，示例标注「据官方文档」。

## 一、命令是干什么的

Kubernetes 节点上，kubelet **不直接**调 containerd 的原生 API，而是走 **CRI**（容器运行时接口）这个标准协议。`crictl` 就是 kubernetes-sigs 提供的、**通过 CRI 跟运行时对话**的 CLI，专门用来在节点上调试容器。

- 为什么不直接用 `docker`？因为 K8s 1.24+ 弃用 dockershim 后，节点跑的是 containerd/CRI-O，`docker` 命令根本看不到 kubelet 起的容器（它们在 `k8s.io` 命名空间里）。
- 排障场景：Pod 一直 `ContainerCreating`、容器 crashlooping、节点上镜像没拉下来、想看容器真实启动命令和挂载——这些都得到节点上用 `crictl`。

> 类比：`kubectl` 是你在集群外面「遥控」；`crictl` 是你登录到某个节点上，直接对着那个节点的运行时「近身排查」。它就是「节点版的 docker ps / docker logs」，但走的是 CRI。

## 二、命令语法

```bash
crictl [全局选项] 子命令 [子命令选项] [参数]
```

- 全局最关键的是 `--runtime-endpoint`（怎么连上运行时）；
- 子命令：`ps`、`pods`、`logs`、`inspect`、`images`、`stats`、`info`、`exec`、`port-forward`、`config` 等。

最简单：

```bash
crictl ps
```

## 三、选项全表（对照官方 crictl.md）

### 1. 全局选项（连哪个运行时）

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-r SOCK`，`--runtime-endpoint=SOCK` | CRI 运行时地址 | 默认会自动试 containerd/crio/cri-dockerd；显式指定最稳 |
| `-i SOCK`，`--image-endpoint=SOCK` | 镜像服务地址（缺省跟 runtime 一致） | 镜像端点单独不同时 |
| `-c FILE`，`--config=FILE` | 配置文件（默认 `/etc/crictl.yaml`） | 把端点写进配置，免每次手敲 |
| `-t SEC`，`--timeout=SEC` | 连接超时（默认 2s） | 运行时卡时放大 |
| `-D`，`--debug` | 打印 CRI 请求/响应细节 | 怀疑 CRI 调用本身有问题时 |

> 官方说明：默认自动探测三个 socket（`/run/containerd/containerd.sock`、`/run/crio/crio.sock`、`/var/run/cri-dockerd.sock`）的行为已废弃，建议始终显式配 `runtime-endpoint`。

### 2. 列容器 / 列 Pod

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `crictl ps` | 列**运行中**容器（类似 `docker ps`） | 节点上看现在跑着哪些容器 |
| `crictl ps -a` | `--all`，含**已退出**的容器 | crashloop 时看退出容器 |
| `crictl ps -q` | `--quiet`，只输出容器 ID | 脚本里喂给 `rm`/`logs` |
| `crictl ps --state=EXITED` | 按状态过滤 | 只看已退出的 |
| `crictl ps --pod-id=xxx` | 只看某个 Pod 沙箱里的容器 | 定位具体 Pod |
| `crictl pods` | 列 **PodSandbox**（Pod 沙箱/网络命名空间） | 看 Pod 级别的状态，不是容器级 |

### 3. 日志 / 详情 / 镜像

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `crictl logs 容器ID` | 打印容器日志 | 容器在跑但行为不对 |
| `crictl logs -f 容器ID` | `--follow`，实时跟踪日志 | 像 `kubectl logs -f` |
| `crictl logs --tail=200 容器ID` | 只看最后 N 行 | 日志刷屏时 |
| `crictl logs --timestamps` | 日志带时间戳 | 对齐时间点 |
| `crictl inspect 容器ID` | 容器完整 JSON 详情（状态、挂载、命令、PodSandbox） | 看容器真实启动命令/挂载（最有用） |
| `crictl inspectp PodID` | 看 PodSandbox 详情 | Pod 网络/沙箱问题 |
| `crictl images` | 列节点上已拉取的镜像 | 排查镜像在不在节点上 |
| `crictl images --filter reference=nginx` | 按镜像名正则过滤 | 镜像太多时 |
| `crictl inspecti 镜像` | 看镜像详情/挂载信息 | 镜像层问题 |

### 4. 资源 / 信息 / 进容器 / 端口转发

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `crictl stats` | 容器 CPU/内存实时占用 | 节点上看哪个容器吃资源（不需 metrics-server） |
| `crictl info` | 运行时与 CRI 配置信息（版本、sandbox 配置） | 确认节点跑的是 containerd 还是 CRI-O、版本 |
| `crictl exec -it 容器ID 命令` | 在运行中容器里执行命令 | 容器里没 kubectl 时近身调试 |
| `crictl port-forward PodID 本地:远端` | 把本地端口转发到 Pod | 不经过 apiserver 直连排障 |
| `crictl config runtime-endpoint SOCK` | 读取/设置端点（`--get/--set/--list`） | 切换 CRI-O：`unix:///run/crio/crio.sock` |

## 四、由浅入深的典型示例

以下示例输出「据官方文档」。

### 示例 1：先确认连上了哪个运行时

```bash
crictl info
```

```text
{
  "status": {
    "conditions": [
      { "type": "RuntimeReady", "status": true },
      { "type": "NetworkReady", "status": true }
    ]
  },
  "config": { "containerd": {} }
}
```

> 先 `info` 确认 RuntimeReady=true，再干别的；连不上就是 socket/权限问题。

### 示例 2：列运行中容器

```bash
crictl ps
```

```text
CONTAINER           IMAGE               CREATED             STATE               NAME                ATTEMPT             POD ID
b25b4f26e3429       busybox:latest      14 seconds ago      Running             busybox             0                   158d7a6665ff3
```

> 注意列：`NAME` 是容器名、`POD ID` 归属哪个 PodSandbox。

### 示例 3：含已退出容器，找 crashloop

```bash
crictl ps -a
```

```text
CONTAINER ID        IMAGE               CREATED             STATE               NAME                ATTEMPT
3e025dd50a72d       busybox             32 seconds ago      Exited              busybox             0
```

> `STATE=Exited` 且 `ATTEMPT` 在涨，就是 crashloop，再 `crictl logs` 看为什么退。

### 示例 4：实时跟日志

```bash
crictl logs -f <容器ID>
```

> 等价 `kubectl logs -f`，但直接在节点上、走 CRI，apiserver 挂了也能看。

### 示例 5：inspect 看容器真实启动命令和挂载

```bash
crictl inspect <容器ID>
```

> 输出大段 JSON，重点看 `.status`（退出码、原因）、`.config.command/args`（真实启动命令）、`.mounts`（挂载了哪些宿主路径）。Pod 行为诡异时这里常能看到注入的环境变量/挂载。

### 示例 6：列节点上的镜像

```bash
crictl images
```

```text
IMAGE                                              TAG                 IMAGE ID            SIZE
registry.k8s.io/pause                               3.9                 e6f1816883972       750kB
docker.io/library/nginx                             latest              e4720093a3c13       191MB
```

> `ImagePullBackOff` 时先在节点上 `crictl images` 确认镜像到底拉下来没有。

### 示例 7：看容器资源占用

```bash
crictl stats
```

```text
CONTAINER           CPU %               MEM                 DISK              INODES
b25b4f26e3429       0.01                1.2MB               0B                0
```

> 不依赖 metrics-server，直接在节点看 CPU/内存。

### 示例 8：配置运行时端点

```bash
crictl config runtime-endpoint unix:///run/containerd/containerd.sock
# 或写进 /etc/crictl.yaml：
cat /etc/crictl.yaml
```

```text
runtime-endpoint: unix:///run/containerd/containerd.sock
image-endpoint: unix:///run/containerd/containerd.sock
timeout: 2
debug: false
```

> 切到 CRI-O 就把端点改成 `unix:///run/crio/crio.sock`。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `crictl info` | 确认运行时就绪 |
| `crictl ps -a` | 看运行中+已退出容器 |
| `crictl ps -q` | 只取 ID（脚本用） |
| `crictl pods` | 看 PodSandbox |
| `crictl logs -f ID` | 实时日志 |
| `crictl inspect ID` | 真实命令/挂载/退出码 |
| `crictl images` | 节点上有哪些镜像 |
| `crictl stats` | 容器资源占用 |
| `crictl exec -it ID sh` | 进容器 |

## 六、RHEL 系与 Debian 系差异

命令本身两系一致，差别在**默认 socket 与包名**：

- RHEL/Rocky：容器运行时常为 containerd，端点 `/run/containerd/containerd.sock`；
- Ubuntu/Debian：同上；若用 CRI-O 则 `/run/crio/crio.sock`；
- 包名：cri-tools 在 Debian 系叫 `cri-tools`，RHEL 系通过对应仓库安装；
- 官方提示：默认自动探测端点已废弃，建议两系都显式写 `/etc/crictl.yaml`，省得每次探测超时。

## 七、新手易错点

1. **`docker ps` 看不到 K8s 容器**：kubelet 走 CRI，必须 `crictl ps`；别在节点上狂敲 docker 找不到东西。
2. **`crictl ps` 默认只看 Running**：退出的容器要 `-a`；crashloop 一定加 `-a`。
3. **连不上多半是 socket/权限**：`crictl` 要 root 或组权限访问 `/run/containerd/containerd.sock`；端点用 `-r` 显式指定。
4. **`ps` 里的 ID 是容器 ID，不是 Pod 名**：logs/inspect 都吃容器 ID；用 `--pod-id` 关联。
5. **crictl 只在节点上用**：它不认识 kubeconfig、不做调度，就是节点本地排障工具。
6. **危险提示**：`crictl rm/stop/start` 直接操作容器，会真实停掉 Pod 内容器；别在生产随便 `crictl rm` 一个正在服务的容器，kubelet 可能不重建（它只管自己创建的）。优先用 kubectl。

## 八、相关命令与文档

- 速查页：[云原生排障命令速查](../cloudnative-commands)
- 更底层的 containerd 原生工具：[ctr](./ctr)
- Pod 调试入口：[kubectl-advanced](./kubectl-advanced)
- 基础 kubectl：[kubectl 命令速查](../kubectl-commands)
- 官方文档：https://github.com/kubernetes-sigs/cri-tools/blob/master/docs/crictl.md ；https://kubernetes.io/docs/tasks/debug/debug-cluster/crictl/
