# docker exec 命令详解：进到正在跑的容器里执行命令

> 本文是 [Docker 命令速查](../docker-commands#进入与日志) 中 `docker exec` 的从 0 到 1 详解。
> 目标：把 `docker exec --help` 里的每个选项讲清楚，多看几遍后，你在服务器上敲 `docker exec --help` 就知道该用哪个选项。
> 环境依据：Docker Engine 28.x（docker CLI 28.x），容器运行时默认为 containerd；本沙箱未安装 docker，选项与输出据 [Docker 官方命令参考](https://docs.docker.com/reference/cli/docker/exec/) 核实，示例输出为示意。

## 一、命令是干什么的

`docker exec` 用来在**一个已经在运行的容器里**再开一个新进程，最常见的用途是**登录进容器里排障**：容器跑着一个 nginx 主进程，你想进去看看配置文件、查日志、装个工具，就 `docker exec -it 容器名 sh`。

关键认知：

- 它是**往运行中的容器里"塞"一个新命令**，不是启动新容器；
- 这个新命令依赖容器主进程（PID 1）活着，容器停了它也没了；
- 它和 `docker run -it` 的区别：`run` 是新建容器，`exec` 是进已有容器。

> 类比：容器是一栋正在营业的写字楼（主进程是前台）；`docker exec` 就是你有钥匙，从侧门进去再开一间办公室办事，而不是在隔壁再盖一栋楼。

## 二、命令语法

```bash
docker exec [选项] 容器 命令 [参数...]
```

- `[选项]`：控制是否交互、用哪个用户、在哪个目录跑；
- `容器`：必填，目标容器名或 ID；
- `命令 [参数...]`：必填，要在容器里跑什么，比如 `sh`、`bash`、`ls /var/log`。

> 注意：`exec` 后面跟的必须是**一个可执行文件**，不能直接写一串 shell 拼接。想跑复合命令要包一层 `sh -c "..."`。

## 三、选项全表（对照 `docker exec --help`）

### 1. 交互与后台

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-i`，`--interactive` | 保持 STDIN 打开 | 想要交互 shell 时（常配 `-t`） |
| `-t`，`--tty` | 分配伪终端 | 想要提示符时（常配 `-i`） |
| `-d`，`--detach` | 后台跑这个 exec 命令 | 在容器里后台起个任务，不阻塞当前终端 |
| `--detach-keys` | 自定义 detach 快捷键 | 改默认 detach 键时 |

### 2. 运行环境

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-e`，`--env` | 给这次 exec 进程设环境变量 | 临时加个变量跑命令 |
| `--env-file` | 从文件读环境变量 | 变量多时 |
| `-u`，`--user` | 以哪个用户跑（名字或 UID） | 想以非 root 身份进容器 |
| `-w`，`--workdir` | 在容器里哪个目录下跑命令 | 不想从根目录开始时 |
| `--privileged` | 给这个 exec 命令额外权限 | 排障需要挂载/调试时（慎用） |

## 四、由浅入深的典型示例

### 示例 1：先进一个容器，再 exec 进去

```bash
docker run --name mycontainer -d -it alpine /bin/sh
docker exec -it mycontainer sh
```

进入后看到容器内 shell：

```text
/ #
```

- 第一条：起一个叫 `mycontainer` 的 alpine 容器，后台跑着一个 `sh`；
- 第二条：在这个容器里再开一个交互 shell，你就进去了；
- 输入 `exit` 只退出这次 exec，**不会停掉容器**。

### 示例 2：在容器里跑一条非交互命令

```bash
docker exec mycontainer ls /etc
```

输出（示意）：

```text
alpine-release  hosts    motd    protocols   ssl
apk            init.conf  modules  resolv.conf  sysctl.conf
...
```

> 不需要进 shell，直接让容器执行 `ls /etc` 并把结果打印到宿主机终端。

### 示例 3：后台在容器里建个文件（`-d`）

```bash
docker exec -d mycontainer touch /tmp/execWorks
```

> `-d` 让 `touch` 在容器里后台跑，当前终端不等它。适合丢个后台任务。

### 示例 4：给 exec 进程临时设环境变量（`-e`）

```bash
docker exec -e VAR_A=1 -e VAR_B=2 mycontainer env
```

输出（示意）：

```text
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
HOSTNAME=f64a4851eb71
VAR_A=1
VAR_B=2
HOME=/root
```

> 这些变量**只对这一次 exec 出来的进程有效**，不影响容器里其他进程，也不写进镜像。

### 示例 5：指定工作目录（`-w`）

```bash
docker exec -it -w /root mycontainer pwd
```

输出（示意）：

```text
/root
```

> 默认 exec 从容器的工作目录（Dockerfile `WORKDIR` 或 run 的 `-w`）开始；用 `-w` 临时换目录。

### 示例 6：以指定用户身份进容器（`-u`）

```bash
docker exec -it -u www-data mycontainer sh
```

> 容器里跑的进程是 root，但你想以 `www-data` 身份排障时用。容器里得真有这个用户。

### 示例 7：在容器里跑复合命令（要包 sh -c）

```bash
docker exec -it mycontainer sh -c "echo a && echo b"
```

输出（示意）：

```text
a
b
```

> 直接写 `docker exec -it mycontainer "echo a && echo b"` 是**错的**——Docker 会把 `echo a && echo b` 当成一个文件名去找，找不到。必须用 `sh -c "..."` 包一层。

### 示例 8：exec 一个 paused 容器会失败

```bash
docker pause mycontainer
docker exec mycontainer sh
```

输出（示意）：

```text
Error response from daemon: Container mycontainer is paused,
unpause the container before exec
```

> 容器被 `docker pause` 冻结后，没法往里 exec，得先 `docker unpause`。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `docker exec -it 容器 sh` | 进容器开 shell（**最常用**，alpine 用 sh） |
| `docker exec -it 容器 bash` | 进容器开 bash（debian/ubuntu 镜像用） |
| `docker exec -it -u root 容器 sh` | 以 root 身份进（默认常就是 root） |
| `docker exec 容器 命令` | 在容器里跑一条命令看输出 |
| `docker exec -w /app 容器 ls` | 在指定目录下跑命令 |
| `docker exec -e K=v 容器 env` | 带临时环境变量跑 |

## 六、与 docker run 的区别（重点）

新手最容易混淆这俩，一张表说清：

| 维度 | `docker run -it 镜像 sh` | `docker exec -it 容器 sh` |
|---|---|---|
| 对象 | 用镜像**新建**一个容器 | 在**已存在、在跑**的容器里开进程 |
| 容器名 | 新起一个名字（或随机名） | 用已有容器名 |
| 退出后 | 容器跟着停（不加 `--rm` 则停在 Exited） | 只退出这次 shell，容器继续跑 |
| 何时用 | 第一次启动、一次性容器 | 进正在运行的服务容器排障 |

> 经验法则：**服务已经用 `run -d` 跑起来了，想进去看东西，用 `exec`，不要再 `run` 一个新容器**。

## 七、RHEL 系与 Debian 系差异

- 命令本身两系一致；
- **镜像里有没有 shell**：很多精简镜像（如 `distroless`、`scratch` 类）里**连 `sh` 都没有**，`docker exec -it 容器 sh` 会报 `exec: "sh": executable file not found`。这跟宿主机是 RHEL 还是 Debian 无关，取决于镜像；
- **`bash` vs `sh`**：Debian/Ubuntu 基础镜像一般有 `bash`；Alpine 只有 `sh`。进不去就先试 `sh` 再试 `bash`。

## 八、新手易错点

1. **容器没在跑就 exec 不进去**：`exec` 要求容器处于 `running` 状态。已停止的容器先 `docker start`。
2. **`sh` 和 `bash` 别搞混**：Alpine 没有 bash，写 `bash` 会报错；反过来 debian 镜像里 `sh` 也能用。
3. **退出 exec 不会停容器**：`exit` 只关你这次开的 shell，主进程还在跑。别和 `docker run -it` 搞混——后者退出容器就停。
4. **复合命令要 `sh -c "..."`**：直接 `docker exec 容器 "cd /x && y"` 会报找不到可执行文件。
5. **`-it` 别漏**：想交互却只写 `-i` 或 `-t`，要么没提示符要么输入回显不对。交互就 `-it` 一起加。
6. **exec 进去看到的文件系统是容器当前状态**：但 exec 新建的进程**不会被自动重启**，容器重启后你 exec 进去改过的临时文件（非挂载卷）就没了。
7. **不要用 exec 去"改配置"然后重启期望生效**：改容器内文件是临时的；要持久化得改镜像或挂卷（见 [volume](./volume)）。

## 九、相关命令与文档

- 速查页：[Docker 命令速查](../docker-commands#进入与日志)
- 起容器：`docker run`（详解见 [run](./run)）
- 看容器日志：`docker logs`（详解见 [logs](./logs)）
- 看容器进程：`docker top`（详解见 [ps-inspect](./ps-inspect)）
- 容器生命周期：`docker start/stop/rm`（详解见 [lifecycle](./lifecycle)）
- 原理与实战：[Docker 实战手册](../../guide/container-docker)
- 官方参考：https://docs.docker.com/reference/cli/docker/exec/
