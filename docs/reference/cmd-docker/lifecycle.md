# docker create / start / stop / restart / rm 详解：容器的一生

> 本文是 [Docker 命令速查](../docker-commands#容器生命周期) 中 `create`、`start`、`stop`、`restart`、`rm` 的从 0 到 1 详解，本篇一次讲清这五个"管容器生死"的命令。
> 目标：把每个命令的选项讲清楚，多看几遍后，你在服务器上敲 `docker <命令> --help` 就知道该用哪个选项。
> 环境依据：Docker Engine 28.x（docker CLI 28.x），容器运行时默认为 containerd；本沙箱未安装 docker，选项与输出据 [Docker 官方命令参考](https://docs.docker.com/reference/cli/docker/container/) 核实，示例输出为示意。

## 一、命令是干什么的

这五个命令合起来管一个容器的"生老病死"：

- `docker create`：**只建不跑**——在镜像上盖一层可写层，造出一个容器，状态是 `created`；
- `docker start`：把一个（已建或已停的）容器**拉起来**；
- `docker stop`：**优雅停止**——先发 SIGTERM，宽限期到了再 SIGKILL；
- `docker restart`：先 stop 再 start；
- `docker rm`：**删除容器**（不是删镜像），删了就没了。

> 类比：`create` 像把电脑开机线插好但不通电；`start` 像按电源键；`stop` 像点"开始菜单→关机"（先存盘再断电）；`restart` 像重启；`rm` 像把整机当废品搬走。

`docker run` 其实就是 `create` + `start` 两步合一（见 [run](./run)）。

## 二、命令语法

```bash
docker create [选项] 镜像 [命令] [参数...]
docker start    [选项] 容器 [容器...]
docker stop     [选项] 容器 [容器...]
docker restart  [选项] 容器 [容器...]
docker rm       [选项] 容器 [容器...]
```

- `create` 的选项几乎和 `run` 一样（名字、端口、挂载、环境变量等都在这一步定）；
- `start/stop/restart/rm` 的参数都是**容器名或容器 ID**，可以一次给多个；
- `rm` 默认只能删**已停止**的容器，想删运行中的要加 `-f`。

## 三、选项全表

### 1. docker create（只列与 run 的关系，常用选项见 run）

`create` 的选项和 `run` 基本一致（`--name`、`-p`、`-v`、`-e`、`--network`、`--restart`、`--cpus`、`-m`、`-u` 等），完整表见 [run](./run) 第三节。它和 `run` 的唯一区别：**建完不启动**，初始状态是 `created`。

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `--pull` | 建之前是否拉镜像 | `always`/`missing`(默认)/`never` |

> 既然选项一样，为什么还要用 `create`？它适合"先把容器配置准备好，稍后再 start"，或者配合 `--volumes-from` 先建一个纯数据容器。日常 90% 场景直接用 `docker run` 即可。

### 2. docker start

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-a`，`--attach` | 启动后 attach 到 STDOUT/STDERR 并转发信号 | 想边启动边看日志 |
| `-i`，`--interactive` | 同时 attach 容器的 STDIN | 启动后直接交互 |
| `--checkpoint` | 从检查点恢复（实验特性） | 极少用 |
| `--detach-keys` | 自定义 detach 快捷键 | 改默认 detach 键时 |

### 3. docker stop / docker restart

这俩选项完全一样：

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-s`，`--signal` | 停止时发什么信号 | 默认 SIGTERM，可改 `SIGKILL` 或数字 9 |
| `-t`，`--timeout` | 宽限多少秒后强制杀（默认 Linux 10 秒） | 服务优雅关闭需要更久时加大 |

> `stop` 的过程：先发 SIGTERM → 等 `-t` 秒 → 还没退就发 SIGKILL。`restart` = 先 `stop` 再 `start`。

### 4. docker rm

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-f`，`--force` | 强制删除**正在运行**的容器（发 SIGKILL） | 运行中的容器也要删（慎用） |
| `-v`，`--volumes` | 同时删掉容器挂载的**匿名卷** | 清干净不留数据残留 |
| `-l`，`--link` | 删除老版 `--link` 建立的网络链接 | 老项目维护时用 |

> 注意：`-v` 只删**匿名卷**（没名字的），**命名卷（`-v 名字:/path`）不会被删**，这是 Docker 故意保护数据的设计。

## 四、由浅入深的典型示例

### 示例 1：create 再 start（拆开 run 的两步）

```bash
docker create -i -t --name mybox alpine
docker start --attach -i mybox
```

输出（示意）：

```text
6d8af538ec541dd581ebc2a24153a28329acb5268abe5ef868c1f1a261221752
/ #
```

> 这等价于 `docker run -it --name mybox alpine`。拆开的好处是容器配置提前定好，什么时候 `start` 都行。

### 示例 2：停掉一个正在跑的容器

```bash
docker stop web
```

输出（示意）：

```text
web
```

> 默认等 10 秒；想立刻杀就 `docker stop -t 0 web`。

### 示例 3：优雅关闭给 30 秒

```bash
docker stop -t 30 web
```

> 数据库这类服务收到 SIGTERM 后要刷盘、关连接，10 秒可能不够，加长到 30 秒更安全。

### 示例 4：重启容器

```bash
docker restart web
```

> 等价于 `docker stop web && docker start web`。改了配置想让它生效时常用（注意：改 `docker run` 选项不能靠 restart，必须删了重建）。

### 示例 5：删除一个已停止的容器

```bash
docker rm web
```

输出（示意）：

```text
web
```

### 示例 6：强制删除正在运行的容器（`-f`）

```bash
docker rm -f web
```

> 直接发 SIGKILL 干掉容器再删，不给它优雅退出机会。**生产环境慎用**，可能丢未刷盘的数据。

### 示例 7：删容器时连匿名卷一起删（`-v`）

```bash
docker rm -v hello
```

> 假设容器是 `docker create -v awesome:/foo -v /bar --name hello redis`，`docker rm -v hello` 后：命名卷 `awesome`（挂在 `/foo`）保留，匿名卷 `/bar` 被删。

### 示例 8：批量清理所有已退出容器

```bash
docker rm $(docker ps --filter status=exited -q)
```

或用管道：

```bash
docker ps --filter status=exited -q | xargs docker rm
```

> `docker ps -q` 只输出容器 ID，配合 `$(...)` 或 `xargs` 批量删。更省事的是 `docker container prune`（见 [system-prune](./system-prune)）。

### 示例 9：一次停掉、重启、删多个容器

```bash
docker stop web db cache
docker restart web db cache
docker rm web db cache
```

> 这些命令都支持一次给多个容器名/ID，空格隔开。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `docker start web` | 启动已停止的容器 |
| `docker stop web` | 优雅停止 |
| `docker restart web` | 重启 |
| `docker rm web` | 删已停容器 |
| `docker rm -f web` | 强删运行中容器 |
| `docker stop $(docker ps -q)` | 停掉所有运行中容器 |
| `docker rm $(docker ps -aq)` | 删所有容器（**危险**） |
| `docker ps -a --filter status=exited -q \| xargs docker rm` | 批量清已退出容器 |

## 六、RHEL 系与 Debian 系差异

这五个命令本身**两系完全一致**。细微差别：

- **停止宽限时间**：Linux 容器默认 10 秒、Windows 容器 30 秒，与发行版无关；
- **systemd 集成**：两系都是 `systemctl start/stop docker` 管整个 Docker 服务；用 `--restart=always` 的容器会随 Docker 服务开机自启；
- **SELinux**：RHEL 系下若 bind mount 了带 SELinux 标签的目录，stop/rm 不受影响，但起容器时可能需要 `:z`/`:Z` 标签（见 [run](./run) 差异段）。

## 七、新手易错点

1. **`docker rm` 默认删不了运行中的容器**：会报错，要么先 `stop`，要么 `-f` 强删。
2. **`docker rm` 删的是容器不是镜像**：删完容器镜像还在；删镜像用 `docker rmi`（见 [images](./images)）。
3. **`docker rm -v` 不删命名卷**：别以为加了 `-v` 数据就清干净了，命名卷要单独 `docker volume rm`（见 [volume](./volume)）。
4. **`docker restart` 改不了 `run` 时的选项**：比如你 run 时漏了 `-p`，restart 多少次都不会多出端口映射，必须 `rm` 后重新 `run`。
5. **`docker rm $(docker ps -aq)` 是危险操作**：连运行中的容器也会列出来，但不加 `-f` 会报错；加了 `-f` 就**无差别杀掉所有容器**，生产环境别手滑。
6. **stop 不是 kill**：`docker stop` 先发 SIGTERM 给主进程收拾残局，`docker kill` 才直接 SIGKILL。要优雅关应用用 stop。
7. **created 状态的容器也算"已建"**：`docker create` 完没 start 的容器，`docker ps -a` 才看得到，`docker ps`（不带 `-a`）看不到。

## 八、相关命令与文档

- 速查页：[Docker 命令速查](../docker-commands#容器生命周期)
- 一条命令建+起：`docker run`（详解见 [run](./run)）
- 看容器状态：`docker ps`（详解见 [ps-inspect](./ps-inspect)）
- 进容器排障：`docker exec`（详解见 [exec](./exec)）
- 一键清理：`docker system prune`（详解见 [system-prune](./system-prune)）
- 原理与实战：[Docker 实战手册](../../guide/container-docker)
- 官方参考：https://docs.docker.com/reference/cli/docker/container/rm/
