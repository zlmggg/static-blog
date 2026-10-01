# docker ps / inspect / top 详解：看容器列表、查细节、看进程

> 本文是 [Docker 命令速查](../docker-commands#进入与日志) 中 `docker ps`、`docker inspect`、`docker top` 的从 0 到 1 详解，本篇一次讲清这三个"看容器"的命令。
> 目标：把每个命令的选项讲清楚，多看几遍后，你在服务器上敲 `docker <命令> --help` 就知道该用哪个选项。
> 环境依据：Docker Engine 28.x（docker CLI 28.x），containerd 默认运行时；本沙箱未安装 docker，选项与输出据 [Docker 官方命令参考](https://docs.docker.com/reference/cli/docker/container/ls/) 核实，示例输出为示意。

## 一、命令是干什么的

三个"查看"类命令，分工不同：

- `docker ps`：**列出容器清单**（哪些在跑、哪些停了、用了什么镜像、映射了哪些端口）；
- `docker inspect`：**扒某个容器/镜像/网络/卷的全部底层细节**（一大坨 JSON，或用 `--format` 抠出某一个字段）；
- `docker top`：看**容器里当前正在跑的进程**（相当于在容器里跑了个 `ps`）。

> 类比：`ps` 是宿舍门口的住宿名单；`inspect` 是某个人的全套档案；`top` 是趴窗户看那个人此刻在干嘛。

## 二、命令语法

```bash
docker ps     [选项]
docker inspect [选项] 对象 [对象...]
docker top    容器 [ps 选项]
```

- `ps`：不跟容器，列清单；
- `inspect`：跟容器/镜像/网络/卷的名字或 ID，可多个；
- `top`：跟一个容器，后面还能接 `ps` 的参数（如 `-ef`）。

## 三、选项全表

### 1. docker ps（列容器）

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-a`，`--all` | 显示**所有**容器（默认只显示运行中） | 看停止的容器（极常用） |
| `-q`，`--quiet` | 只输出容器 ID | 配合脚本批量删/操作（极常用） |
| `-f`，`--filter` | 按条件过滤 | 如 `status=exited`、`name=web` |
| `-n N`，`--last N` | 显示最近创建的 N 个容器（含所有状态） | 只关心最近几个 |
| `-l`，`--latest` | 只显示最新创建的那个容器 | 刚 run 完想找它 |
| `--format` | Go 模板自定义列 | 只要 ID 和名字 |
| `--no-trunc` | 不截断输出（COMMAND、ID 全显示） | 命令太长被省略号截断时 |
| `-s`，`--size` | 显示容器可写层占了多少磁盘 | 看哪个容器在涨磁盘 |

常用 `--filter` 取值：

| 过滤器 | 作用 |
|---|---|
| `status=running\|exited\|paused\|created\|dead` | 按状态筛 |
| `name=xxx` | 名字包含 xxx |
| `ancestor=镜像` | 用了某个镜像的容器 |
| `exited=0\|137` | 按退出码筛（137 多为被 OOM/SIGKILL 杀） |
| `publish=80` / `expose=8080` | 发布/暴露了某端口的 |
| `health=healthy\|unhealthy\|starting` | 按健康检查结果筛 |
| `before=容器` / `since=容器` | 在某容器之前/之后创建的 |
| `volume=卷名` / `network=网络名` | 挂了某卷/接了某网络的 |

### 2. docker inspect（扒细节）

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-f`，`--format` | 用 Go 模板只抠出想要的字段 | 如只要 IP、只要状态（极常用） |
| `-s`，`--size` | 对容器额外显示可写层大小 | 看容器磁盘占用 |
| `--type` | 指定对象类型（`container/image/network/volume/...`） | 名字重名时消歧义 |

> `inspect` 默认输出一大段 JSON。新手别硬翻，用 `-f` 抠字段最爽。

### 3. docker top

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `[ps OPTIONS]` | 后面可接宿主机 `ps` 的参数 | 如 `docker top web -ef` |

> `docker top` 没有自己的开关，它本质是把 `ps` 跑到容器的 PID namespace 里。

## 四、由浅入深的典型示例

### 示例 1：看正在跑的容器（默认）

```bash
docker ps
```

输出（示意）：

```text
CONTAINER ID  IMAGE         COMMAND                  CREATED         STATUS         PORTS                  NAMES
4bed76d3ad42  nginx:alpine  "/docker-entrypoint.…"  5 seconds ago   Up 5 seconds   0.0.0.0:8080->80/tcp   web
```

逐列：容器 ID（短）、镜像、启动命令、创建时间、运行状态、端口映射、容器名。

### 示例 2：看所有容器含已停止（`-a`）

```bash
docker ps -a
```

> 不加 `-a` 只看 running；加了才能看到 Exited/Created 的容器。排障"我的容器哪去了"先加 `-a`。

### 示例 3：只要容器 ID（`-q`，脚本必备）

```bash
docker ps -q
```

输出（示意）：

```text
4bed76d3ad42
a1b2c3d4e5f6
```

> 常配合 `docker rm $(docker ps -aq)` 批量操作（见 [lifecycle](./lifecycle)）。

### 示例 4：按状态过滤（`--filter`）

```bash
docker ps -a --filter "status=exited"
```

> 列出所有已停止的容器。再如 `--filter "exited=137"` 找出被 SIGKILL 杀掉的（常见于 OOM）。

### 示例 5：按镜像过滤（`ancestor`）

```bash
docker ps --filter "ancestor=nginx:alpine"
```

> 列出所有用了 nginx:alpine 镜像的容器。

### 示例 6：不截断看完整启动命令（`--no-trunc`）

```bash
docker ps --no-trunc
```

> COMMAND 列默认显示 `/docker-entrypoint.…` 省略号，加 `--no-trunc` 看全。

### 示例 7：自定义输出列（`--format`）

```bash
docker ps --format "table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Ports}}"
```

输出（示意）：

```text
CONTAINER ID  NAMES  STATUS                  PORTS
4bed76d3ad42  web    Up 5 seconds            0.0.0.0:8080->80/tcp
```

> 可用字段：`.ID` `.Image` `.Command` `.Status` `.Names` `.Ports` `.Mounts` `.Networks` `.Labels` `.Size` 等。

### 示例 8：inspect 抠出容器状态

```bash
docker inspect --format '{{.State.Status}}' web
```

输出（示意）：

```text
running
```

### 示例 9：inspect 抠出容器 IP

```bash
docker inspect --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' web
```

输出（示意）：

```text
172.17.0.2
```

### 示例 10：inspect 看端口绑定、镜像名

```bash
docker inspect --format '{{.Config.Image}}' web
docker inspect --format '{{range $p, $conf := .NetworkSettings.Ports}}{{$p}} -> {{(index $conf 0).HostPort}}{{end}}' web
```

输出（示意）：

```text
nginx:alpine
80/tcp -> 8080
```

### 示例 11：inspect 某个字段本身是结构体，用 json 打印

```bash
docker inspect --format '{{json .Config}}' web
```

> 直接拿到 `.Config` 整段 JSON，不用肉眼翻整坨输出。

### 示例 12：名字重名时指定类型（`--type`）

```bash
docker inspect --type=volume myvolume
```

> 容器和卷可能同名，加 `--type=volume/container/network/image` 消歧义。

### 示例 13：看容器里在跑什么进程（`docker top`）

```bash
docker top web
```

输出（示意）：

```text
UID    PID   PPID  C  STIME  TTY    TIME      CMD
root   8123  7890  0  10:00  ?      00:00:00  nginx: master process
nginx  8130  8123  0  10:00  ?      00:00:00  nginx: worker process
```

> 这里的 PID 是**宿主机视角的 PID**（不是容器内的），可以直接拿去宿主机 `strace`/`gdb`。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `docker ps` | 看运行中容器 |
| `docker ps -a` | 看所有容器 |
| `docker ps -q` | 只要 ID（脚本用） |
| `docker ps -a --filter status=exited -q` | 找出所有停掉的容器 ID |
| `docker inspect -f '{{.State.Status}}' 容器` | 只看状态 |
| `docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' 容器` | 只看 IP |
| `docker inspect -f '{{.Config.Image}}' 容器` | 只看镜像 |
| `docker top 容器` | 看容器内进程 |

## 六、RHEL 系与 Debian 系差异

- 命令两系一致；
- **`docker top` 看到的 PID**：是宿主机 PID，两系都可直接在宿主机用 `ps`/`ls -l /proc/<pid>` 查；
- **SELinux**：RHEL 系下 inspect 输出里会有 `.ProcessLabel`/`.MountLabel` 字段，Debian 系没有，这是 SELinux 上下文，排权限问题时看它。

## 七、新手易错点

1. **`docker ps` 默认只看运行中**：找不到容器先加 `-a`，别以为容器没了。
2. **`inspect` 输出是 JSON 数组**：哪怕只查一个对象，也是 `[ {...} ]`；用 `-f` 模板时直接写字段路径即可，模板会对数组里每个元素执行。
3. **`.State.Status` 的值**：`running`/`exited`/`paused`/`created`/`restarting`/`dead`；`dead` 是"没删干净的僵尸容器"，只能 rm 不能 start。
4. **`docker top` 对停止的容器无效**：容器没跑就没进程可列。
5. **`--filter` 多个同 key 是 OR，不同 key 是 AND**：别记错逻辑。
6. **`-q` 配合 `xargs` 批量删很危险**：`docker rm $(docker ps -aq)` 会把所有容器 ID 列出来，运行中的不加 `-f` 会报错，加了 `-f` 就全杀了。
7. **`--no-trunc` 才看得到完整 ID**：默认只显示前 12 位，脚本里要用全 ID 时加它。

## 八、相关命令与文档

- 速查页：[Docker 命令速查](../docker-commands#进入与日志)
- 起停删容器：`docker run/stop/rm`（详解见 [run](./run) / [lifecycle](./lifecycle)）
- 进容器：`docker exec`（详解见 [exec](./exec)）
- 资源占用：`docker stats`（详解见 [stats](./stats)）
- 看镜像清单：`docker images`（详解见 [images](./images)）
- 原理与实战：[Docker 实战手册](../../guide/container-docker)
- 官方参考：https://docs.docker.com/reference/cli/docker/container/ls/
