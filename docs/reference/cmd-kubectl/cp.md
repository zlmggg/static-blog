# kubectl cp 命令详解：在本地和容器之间拷文件

> 本文是 [kubectl 命令速查](../kubectl-commands#调试与排障) 中 `kubectl cp` 的从 0 到 1 详解。
> 目标：把 `kubectl cp --help` 里的每个选项讲清楚，多看几遍后，你在服务器上敲 `kubectl cp --help` 就知道该用哪个选项。
> 环境依据：kubectl 客户端，对应 **Kubernetes 1.35**（本机沙箱未安装，选项依据 K8s 官方命令参考核实；示例输出均为「示意，据 K8s 官方文档」）。

## 一、命令是干什么的

`cp` 在**本机文件系统**和**Pod 内容器**之间拷文件/目录。像 `scp`，但对端是 K8s 里的容器。

- 把本机配置文件送进容器：`kubectl cp ./app.conf mypod:/etc/app/`
- 把容器里的日志/导出文件拉回本机：`kubectl cp mypod:/var/log/app.log ./`

> 类比：`kubectl cp` 像 `docker cp`——在你电脑和容器之间搬文件。底层其实是打包成 tar 流，经 exec 传过去再解包。

## 二、命令语法

```bash
kubectl cp <源文件规格> <目标文件规格>
```

- 文件规格写法：`本地路径` 或 `命名空间/Pod:/路径` 或 `Pod:/路径`；
- 方向由谁在左谁在右决定：左本地右容器 = 上传；左容器右本地 = 下载。

```bash
kubectl cp /tmp/foo mypod:/tmp/bar
```

## 三、选项全表（对照 `kubectl cp --help`）

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `源 目标` | 本地↔容器路径对 | 核心 |
| `-c 容器`，`--container` | 多容器 Pod 指定拷进/拷出哪个容器 | sidecar 时 |
| `--no-preserve` | 不保留原文件的属主和权限 | 容器里权限和本机不同、不想带过去 |
| `--retries=N` | 拷失败重试次数 | 网络不稳时（默认 0 不重试） |

> 重要前置：**容器镜像里必须有 `tar` 二进制**，否则 `kubectl cp` 直接失败。这是官方明确写的限制。

## 四、由浅入深的典型示例

### 示例 1：本机目录拷进 Pod

```bash
kubectl cp /tmp/foo_dir mypod:/tmp/bar_dir
```

> 把本机 `/tmp/foo_dir` 整个目录传到 Pod 的 `/tmp/bar_dir`。

### 示例 2：本机文件拷进指定命名空间的 Pod

```bash
kubectl cp /tmp/foo my-namespace/mypod:/tmp/bar
```

> `命名空间/Pod:/路径` 指定 ns。

### 示例 3：多容器 Pod 指定容器

```bash
kubectl cp /tmp/foo mypod:/tmp/bar -c my-container
```

> Pod 里多个容器时，`-c` 指定拷进哪个。

### 示例 4：从 Pod 拉文件回本机

```bash
kubectl cp my-namespace/mypod:/tmp/foo /tmp/bar
```

> 方向反过来：左是 Pod、右是本地，把容器里的文件拉回本机。

### 示例 5：不保留权限属主

```bash
kubectl cp ./app.conf mypod:/etc/app/app.conf --no-preserve
```

> 容器里的文件属主/权限和本机文件系统无关，加 `--no-preserve` 避免把本机属主带过去。

### 示例 6：用 tar + exec 手动实现（cp 不支持时的替代）

```bash
tar cf - /tmp/foo | kubectl exec -n my-namespace mypod -i -- tar xf - -C /tmp/bar
```

> `kubectl cp` 对软链接、通配符、文件模式保留等高级场景支持有限；这时用 `tar | kubectl exec` 自己控制（官方推荐）。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `kubectl cp 本地文件 pod:/路径` | 上传进容器 |
| `kubectl cp pod:/路径 本地目录` | 从容器下载 |
| `kubectl cp ns/pod:/路径 本地` | 指定 ns 下载 |
| `kubectl cp 本地 pod:/路径 -c 容器` | 指定容器 |
| `tar cf - 文件 \| kubectl exec -i pod -- tar xf - -C 目录` | cp 不支持时的替代 |

## 六、RHEL 系与 Debian 系差异

`kubectl cp` 经 exec+tar 工作，两系**用法一致**。但它依赖两端都有 `tar`：本机一般都有；**容器镜像里要有 `tar`**（精简/distroless 镜像常没有），没有就用示例 6 的 `tar | exec` 或换工具。

## 七、新手易错点

1. **容器里没 `tar` 会失败**：报 tar 相关错误时，先 `kubectl exec pod -- which tar` 确认；没有就用 exec+tar 方案或换带 tar 的镜像。
2. **路径写错方向**：左本地右容器是上传，左容器右本地是下载，别搞反。
3. **多容器 Pod 不指定 `-c`**：默认进第一个容器，可能不是你要的。
4. **软链接/权限保留有坑**：官方明确说高级场景（软链接、通配符、文件模式）用 `kubectl exec` + tar 更靠谱。
5. **拷大文件慢**：cp 走 apiserver，大文件/大批量建议用共享存储（PVC）或镜像构建时打进去。
6. **`--no-preserve` 按需加**：默认保留属主权限，跨文件系统可能不兼容导致权限问题。
7. **它是临时搬文件**：进容器的文件在容器重建后丢失；要持久化用 ConfigMap/Secret/PVC。

## 八、相关命令与文档

- 速查页：[kubectl 命令速查](../kubectl-commands#调试与排障)
- 进容器执行命令：[exec 详解](./exec)
- 概念补课（ConfigMap/PVC 持久化）：[存储与 Ingress](../../guide/container-k8s-03-storage-ingress)
- 官方命令参考：https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands#cp
