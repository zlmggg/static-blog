# docker info / version / system df / system prune 详解：看系统状态与清理磁盘

> 本文是 [Docker 命令速查](../docker-commands#系统与清理) 中 `docker info`、`docker version`、`docker system df`、`docker system prune` 的从 0 到 1 详解，本篇一次讲清这四个"看整体 + 大扫除"的命令。
> 目标：把每个命令的选项讲清楚，多看几遍后，你在服务器上敲 `docker <命令> --help` 就知道该用哪个选项。
> 环境依据：Docker Engine 28.x（docker CLI 28.x），containerd 默认运行时；本沙箱未安装 docker，选项与输出据 [Docker 官方命令参考](https://docs.docker.com/reference/cli/docker/system/prune/) 核实，示例输出为示意。

## 一、命令是干什么的

这组命令管"Docker 整机状态"：

- `docker version`：看 Client 和 Server 各组件版本号；
- `docker info`：看 Docker 服务器的全貌（存储驱动、网络插件、容器数、镜像数、运行时、内核等）；
- `docker system df`：看 Docker 占了多少磁盘（镜像/容器/卷分别多少）；
- `docker system prune`：一键清掉没用的容器、网络、悬空镜像、构建缓存（**危险，重点**）。

> 类比：`version` 是看软件版本号；`info` 是打开"系统信息"面板；`system df` 是看 Docker 这个 App 占了多少硬盘；`system prune` 是手机上的"清理缓存"——很爽，但别误删照片。

## 二、命令语法

```bash
docker version        [选项]
docker info           [选项]
docker system df      [选项]
docker system prune   [选项]
```

## 三、选项全表

### 1. docker version

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-f`，`--format` | Go 模板只取某段版本 | 如只要 Server 版本 |

> 注意区分：`docker version` 打 Client+Server 两段；`docker --version`（或 `-v`）只打一个简短 CLI 版本号。

### 2. docker info

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-f`，`--format` | Go 模板/JSON 输出 | 脚本里解析 |

### 3. docker system df

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-v`，`--verbose` | 详细列出每个镜像/容器/卷占多少 | 想知道谁在吃磁盘 |
| `--format` | 自定义表格列 | 精简输出 |

### 4. docker system prune（重点危险）

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-a`，`--all` | 删所有**没被容器使用**的镜像（不只悬空） | 想大清理时 |
| `--volumes` | 连**匿名卷**一起删 | **会删数据，慎加** |
| `-f`，`--force` | 不提示直接删 | 脚本里（生产环境别用） |
| `--filter` | 按时间/标签过滤 | 如 `until=24h` 只删 24 小时前的 |

> 默认 `prune` 删：停止的容器、没用的网络、悬空（dangling）镜像、构建缓存。**默认不动命名卷**（保护数据）。

## 四、由浅入深的典型示例

### 示例 1：看版本（Client + Server）

```bash
docker version
```

输出（示意，据 Docker 官方文档）：

```text
Client: Docker Engine - Community
 Version:    28.5.1
 API version: 1.51
 Go version: go1.24.8
 OS/Arch:    linux/amd64

Server: Docker Engine - Community
 Engine:
  Version:    28.5.1
  API version: 1.51 (minimum version 1.24)
  containerd:
   Version: v1.7.25
  runc:
   Version: 1.2.4
```

> Client 连不上 Server 时，只会打印 Client 段，Server 段报错——这是判断"dockerd 起没起"的最快方法。

### 示例 2：只要 Server 版本

```bash
docker version --format '{{.Server.Version}}'
```

输出（示意）：

```text
28.5.1
```

### 示例 3：看 Docker 整体信息

```bash
docker info
```

输出（节选示意）：

```text
Client:
 Version:    28.5.1

Server:
 Containers: 14
  Running: 3
  Stopped: 10
 Images: 52
 Storage Driver: overlayfs
 Cgroup Driver: cgroupfs
 Cgroup Version: 2
 Default Runtime: runc
 containerd version: 71909c1814...
 Kernel Version: 6.5.x
 Operating System: Ubuntu 24.04 LTS
 Docker Root Dir: /var/lib/docker
```

> 排障常看：`Storage Driver`、`Cgroup Version`、`Default Runtime`、`Docker Root Dir`、`Insecure Registries`、`Registry Mirrors`。

### 示例 4：看 Docker 占了多少磁盘

```bash
docker system df
```

输出（示意，据 Docker 官方文档）：

```text
TYPE            TOTAL   ACTIVE  SIZE      RECLAIMABLE
Images          5       2       16.43MB   11.63MB (70%)
Containers      2       0       212B      212B (100%)
Local Volumes   2       1       36B       0B (0%)
Build Cache     18      0       45.2MB    45.2MB (100%)
```

> `RECLAIMABLE` 列就是 prune 能帮你回收多少。

### 示例 5：详细看谁在吃磁盘（`-v`）

```bash
docker system df -v
```

> 会列出每个镜像、每个容器、每个卷的具体大小，配合 `docker images` / `docker ps` 定位大文件。

### 示例 6：最基础的清理（有确认提示）

```bash
docker system prune
```

输出（示意）：

```text
WARNING! This will remove:
 - all stopped containers
 - all networks not used by at least one container
 - all dangling images
 - unused build cache
Are you sure you want to continue? [y/N] y
Deleted Containers:
f44f9b81948b...
Total reclaimed space: 1.84kB
```

> 会先弹警告让你输 `y`。**这一步默认不删卷、不删有用镜像**，相对安全。

### 示例 7：大清理——连没在用的镜像也删（`-a`）

```bash
docker system prune -a
```

> 加 `-a` 后，**所有当前没被容器跑着的镜像都会被删**，包括你手动 pull 下来但暂时没用的 nginx、alpine 等。下次跑要重新 pull。

### 示例 8：连匿名卷一起删（`--volumes`，危险）

```bash
docker system prune -a --volumes
```

输出（示意）：

```text
WARNING! This will remove:
 - all stopped containers
 - all networks not used by at least one container
 - all anonymous volumes not used by at least one container
 - all images without at least one container associated to them
 - all build cache
Are you sure? [y/N]
```

> **这条命令会删数据库里没被容器引用的匿名卷数据**。如果你的数据放在匿名卷里且容器刚好停了，数据直接没。生产环境加 `--volumes` 前必须确认数据都在命名卷或 bind mount 里。

### 示例 9：只删超过 24 小时的（`--filter`）

```bash
docker system prune --filter "until=24h"
```

> 只清理 24 小时前就已经没人用的资源，避免误删刚起的东西。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `docker version` | 看客户端/服务端版本 |
| `docker info` | 看 Docker 全貌 |
| `docker system df` | 看磁盘占用 |
| `docker system df -v` | 详细看谁占磁盘 |
| `docker system prune` | 安全清理（有提示） |
| `docker system prune -a` | 连没用镜像一起清 |
| `docker system prune -af` | 不提示直接清（脚本用，**危险**） |
| `docker builder prune` | 只清构建缓存（不动容器镜像） |

## 六、RHEL 系与 Debian 系差异

- 命令两系一致；
- **Docker Root Dir**：默认都是 `/var/lib/docker`；RHEL 系若 `/var` 分区小，建议把 Docker 数据目录迁到大盘（改 `daemon.json` 的 `data-root`）；
- **cgroup 驱动**：RHEL 7/8 老系统可能 `cgroupfs`，新系统两系都 `systemd`+cgroup v2，`docker info` 里能看到；
- **包名**：两系都是 `docker-ce` 包提供这些命令。

## 七、新手易错点

1. **`docker system prune -a --volumes` 是 Docker 头号危险命令**：它会删停止的容器、没用的镜像、没被引用的匿名卷。数据库容器停了但卷里有数据时，加 `--volumes` 直接清空数据。**生产环境敲之前先 `docker system df -v` 看清楚。**
2. **`-f` 跳过确认提示**：`docker system prune -f` 不问 y/N 直接删，脚本里好用，手动在生产别加。
3. **`prune` 不删命名卷**：默认连匿名卷都不删；要删卷必须显式加 `--volumes`，这是保护设计。
4. **`docker version` Server 段连不上 = dockerd 没起**：先 `sudo systemctl status docker` 看服务状态。
5. **`docker system df` 里 Build Cache 经常很大**：CI/CD 构建多了能占几十 G，单独清用 `docker builder prune`。
6. **prune 不会动运行中的容器**：正在跑的容器、它们用的镜像和卷都受保护；安全边界是"没人用的"。
7. **`docker info` 里 Registry Mirrors 没配好会 pull 慢**：国内服务器记得配加速器，不然拉镜像超时。

## 八、相关命令与文档

- 速查页：[Docker 命令速查](../docker-commands#系统与清理)
- 删容器：`docker rm`（详解见 [lifecycle](./lifecycle)）
- 删镜像：`docker rmi`（详解见 [images](./images)）
- 删卷：`docker volume rm/prune`（详解见 [volume](./volume)）
- 看容器资源占用：`docker stats`（详解见 [stats](./stats)）
- 原理与实战：[Docker 实战手册](../../guide/container-docker)
- 官方参考：https://docs.docker.com/reference/cli/docker/system/prune/
