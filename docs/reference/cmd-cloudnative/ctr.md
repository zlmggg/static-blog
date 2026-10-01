# ctr 命令详解：containerd 原生调试工具（与 crictl 的区别）

> 本文是 [云原生排障命令速查](../cloudnative-commands) 中「containerd / CRI 运行时」的从 0 到 1 详解，本篇一次讲清 `ctr -n k8s.io images/containers/tasks/content`，并说清它和 `crictl` 到底什么区别。
> 目标：节点上 containerd 排障时，知道什么时候用 `crictl`、什么时候得用 `ctr`，以及为什么 `ctr images ls` 默认啥都看不到。
> 环境依据：containerd 2.3（站内 2026-09 基准）。本沙箱未装，选项据 containerd 官方 getting-started 文档核对，示例标注「据官方文档」。

## 一、命令是干什么的

`ctr` 是 **containerd 自带的原生命令行工具**，直接用 containerd 的 gRPC API 操作它。官方文档原话：`ctr` 是 **"For debugging only"**（仅供调试），没有像 `docker`/`nerdctl` 那样的友好封装。

containerd 里有几个核心概念，理解了 `ctr` 就懂了：

- **命名空间（namespace）**：containerd 是多租户的，资源按命名空间隔离。**K8s 用的命名空间叫 `k8s.io`**；`ctr` 默认用 `default`，所以不加 `-n k8s.io` 你啥都看不到；
- **image（镜像）**：拉下来、解压好的镜像；
- **container（容器）**：一个**元数据对象**（资源、配置挂在它身上），本身不跑进程；
- **task（任务）**：真正**活着跑的进程**。container 可以反复起停 task。

> 类比：`crictl` 是「走 CRI 标准协议的节点排障工具」，看到的是 kubelet 视角；`ctr` 是「直接扒 containerd 内核的调试器」，能看到命名空间、内容寻址、snapshot 这些 CRI 不暴露的底层细节。日常优先 `crictl`，它查不动了再上 `ctr`。

## 二、命令语法

```bash
ctr [全局选项] 子命令 [子命令选项]
```

- 全局最关键：`-n, --namespace`（指定命名空间，K8s 场景几乎必加 `k8s.io`）；
- 子命令分组：`images`、`containers`、`tasks`、`content`、`snapshots`、`namespaces`、`leases`。

最简单（但要看 K8s 内容得加命名空间）：

```bash
ctr -n k8s.io images ls
```

## 三、选项全表（对照 containerd 官方文档）

### 1. 全局 / 命名空间

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-n NS`，`--namespace=NS` | 指定 containerd 命名空间 | **K8s 排障必加 `-n k8s.io`**（否则空） |
| `--address SOCK` | containerd socket（默认 `/run/containerd/containerd.sock`） | socket 不在默认路径时 |
| `--debug` | 打印底层 gRPC 细节 | 排 ctr 本身问题 |

### 2. `ctr images`：镜像

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `ctr images ls` | 列命名空间内镜像 | 看节点上有哪些镜像 |
| `ctr images pull REF` | 拉镜像 | 手动预拉（含 `--plain-http` 等） |
| `ctr images tag SRC DST` | 给镜像打标签 | 改引用名 |
| `ctr images export FILE REF` | 把镜像导出成 tar | 离线拷镜像 |
| `ctr images import FILE` | 导入 tar 镜像 | 无网络环境装镜像 |
| `ctr images rm REF` | 删镜像 | 清理磁盘 |
| `ctr images mount REF MOUNT` | 把镜像根fs挂到目录 | 不启动容器直接看镜像里的文件 |

### 3. `ctr containers` 与 `ctr tasks`

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `ctr containers ls` | 列**容器（元数据对象）** | 看 containerd 里建了哪些容器 |
| `ctr containers info ID` | 容器详情 | 看配置 |
| `ctr tasks ls` | 列**正在跑的任务（进程）** | 看哪些进程真活着 |
| `ctr tasks ps ID` | 看容器里的进程 | 排容器内进程 |
| `ctr tasks kill ID` | 杀任务 | 手动停 |

> 关键：`ctr containers ls` 列出来的不一定在跑；真正活着的进程要看 `ctr tasks ls`。这就是官方强调的「container 是元数据、task 是活进程」。

### 4. `ctr content` / `snapshots`（底层排障）

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `ctr content ls` | 列内容寻址存储里的 blobs | 镜像层/拉取损坏排查 |
| `ctr snapshots ls` | 列 snapshot（容器可写层） | 磁盘占用、层问题 |
| `ctr namespaces ls` | 列所有命名空间 | 确认 K8s 用的是 `k8s.io` |

## 四、由浅入深的典型示例

以下示例输出「据官方文档」或示意。

### 示例 1：先看有哪些命名空间

```bash
ctr namespaces ls
```

```text
NAME
default
k8s.io
```

> 确认 `k8s.io` 存在。K8s 的一切都在这个命名空间里。

### 示例 2：列 K8s 命名空间里的镜像

```bash
ctr -n k8s.io images ls
```

```text
REF                                                      TYPE                                                      DIGEST        SIZE      PLATFORMS
registry.k8s.io/pause:3.9                                application/vnd.docker.distribution.manifest.v2+json      sha256:e6f... 747.0 kB   linux/amd64
docker.io/library/nginx:latest                           application/vnd.docker.distribution.manifest.v2+json      sha256:e47... 191.0 MB  linux/amd64
```

> 忘了 `-n k8s.io` 时这里基本是空的——这是新手最常踩的坑。

### 示例 3：列容器 vs 列任务

```bash
ctr -n k8s.io containers ls
ctr -n k8s.io tasks ls
```

```text
CONTAINER                                 IMAGE    RUNTIME
b25b4f26e3429...                          docker.io/library/nginx:latest   io.containerd.runc.v2

TASK                                      PID      STATUS
b25b4f26e3429...                          31024    RUNNING
```

> `containers ls` 是对象，`tasks ls` 才是活进程 + PID。用那个 PID 去节点上 `ps`/`strace`。

### 示例 4：手动拉一个镜像（官方示例）

```bash
ctr images pull docker.io/library/redis:alpine
ctr run docker.io/library/redis:alpine redis
```

> 这是 containerd 官方文档里的例子：`ctr` 自己 pull、自己 run。注意这种 `ctr run` 建的容器在 `default` 命名空间，K8s 看不见。

### 示例 5：导出/导入镜像做离线迁移

```bash
ctr -n k8s.io images export nginx.tar docker.io/library/nginx:latest
# 拷到另一台机器后：
ctr -n k8s.io images import nginx.tar
```

> 内网/隔离环境迁移镜像常用。

### 示例 6：不启动容器，直接看镜像里有什么文件

```bash
ctr images mount docker.io/library/nginx:latest /tmp/nginx-root
ls /tmp/nginx-root
# 看完卸载
ctr images unmount /tmp/nginx-root
```

> 镜像里没有 shell、但你想看它带了哪些配置文件时，这个技巧很有用。

### 示例 7：看内容层 / snapshot 占空间

```bash
ctr -n k8s.io content ls | head
ctr -n k8s.io snapshots ls | head
```

> 节点磁盘满了、怀疑镜像层没清时，从 content/snapshots 层找大块。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `ctr namespaces ls` | 看命名空间 |
| `ctr -n k8s.io images ls` | K8s 节点上的镜像 |
| `ctr -n k8s.io containers ls` | 容器对象 |
| `ctr -n k8s.io tasks ls` | 活进程 + PID |
| `ctr images pull/export/import` | 拉/导出/导入镜像 |
| `ctr images mount REF 目录` | 不启动看镜像内容 |
| `crictl ps`（对比） | 走 CRI 看容器（首选） |

## 六、RHEL 系与 Debian 系差异

`ctr` 随 containerd 一起安装，**两系用法一致**。差别只在 socket 路径与安装来源：

- socket 默认都是 `/run/containerd/containerd.sock`；
- RHEL/Rocky 与 Ubuntu 上 containerd 包名不同（`containerd.io` 由 Docker 分发），但 `ctr` 子命令完全一致；
- containerd 2.x 里 `io.containerd.runc.v2` 是默认 runtime；老 1.x 才有 v1。

### ctr 与 crictl 怎么选

| 维度 | `crictl` | `ctr` |
|---|---|---|
| 走什么接口 | CRI（kubelet 同一条路） | containerd 原生 API |
| 定位 | 节点排障首选 | 更底层的调试 |
| 命名空间 | 自动只看 `k8s.io` | 要手动 `-n k8s.io` |
| 能看到 | PodSandbox、容器、日志 | 镜像层、content、snapshot、task PID |

## 七、新手易错点

1. **不加 `-n k8s.io` 就啥都没有**：这是 ctr 第一大坑。K8s 资源全在 `k8s.io` 命名空间。
2. **`containers ls` ≠ 在跑**：对象在不代表进程活着；要看 `tasks ls`。
3. **别用 ctr 去管 K8s 日常容器**：官方明确 ctr 是调试工具，用它 `ctr run` 出来的容器 kubelet 不认识，别和 K8s 混着玩。
4. **`ctr images ls` 和 `crictl images` 视图不同**：ctr 按命名空间、带 manifest type；crictl 走 CRI。日常排障优先 crictl。
5. **危险提示**：`ctr images rm`、`ctr snapshots` 操作直接作用于 containerd 存储；误删 `k8s.io` 里的镜像/snapshot 会让 Pod 重建失败。生产节点上操作前先确认对象，别 `rm` 通配。
6. **containerd 自身 metrics**：默认在 `127.0.0.1:1338/v1/metrics`，排 containerd 性能时可抓。

## 八、相关命令与文档

- 速查页：[云原生排障命令速查](../cloudnative-commands)
- 走 CRI 的首选排障工具：[crictl](./crictl)
- Pod 调试：[kubectl-advanced](./kubectl-advanced)
- 官方文档：https://containerd.io/docs/ ；getting-started：https://github.com/containerd/containerd/blob/main/docs/getting-started.md
