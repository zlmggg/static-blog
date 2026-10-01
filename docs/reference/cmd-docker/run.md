# docker run 命令详解：一条命令把容器跑起来

> 本文是 [Docker 命令速查](../docker-commands#容器生命周期) 中 `docker run` 的从 0 到 1 详解。
> 目标：把 `docker run --help` 里的每个选项讲清楚，多看几遍后，你在服务器上敲 `docker run --help` 就知道该用哪个选项。
> 环境依据：Docker Engine 28.x（docker CLI 28.x），Compose v2 插件形式的 `docker compose`，容器运行时默认为 containerd；本沙箱未安装 docker，所有选项与输出均据 [Docker 官方命令参考](https://docs.docker.com/reference/cli/docker/container/run/) 核实，示例输出为示意。

## 一、命令是干什么的

`docker run` 是 Docker 里**最高频、也最复杂**的一条命令：它做了两件事——先 `create`（在镜像上盖一层可写层，造出一个容器），再 `start`（把里面的主进程拉起来）。一条命令同时完成"建容器"和"启动容器"。

- 不带选项：用给定镜像起一个容器，跑完主命令就退出；
- 加 `-d`：扔到后台跑；
- 加 `-it`：交互式进容器终端；
- 加一堆 `-p / -v / -e / --name`：把端口、目录、环境变量、名字都配齐。

> 类比：`docker run` 就像"从一张系统安装盘（镜像）开机"，你传的每个选项都是开机时的 BIOS/启动参数——挂哪块盘（`-v`）、开哪几个口（`-p`）、用哪个用户登录（`-u`）、内存给多大（`-m`）。

## 二、命令语法

```bash
docker run [选项] 镜像 [命令] [参数...]
```

- `[选项]`：控制容器怎么跑（后台/交互/名字/端口/挂载/资源限制等），最多；
- `镜像`：必填，用哪个镜像起容器，可带 `:标签` 或 `@摘要`；
- `[命令] [参数...]`：可选，覆盖镜像里自带的启动命令（Dockerfile 里的 `CMD`）；不写就用镜像默认命令。

最简单的用法：

```bash
docker run nginx
```

## 三、选项全表（对照 `docker run --help`）

`docker run` 选项上百个，下面按**功能分组**讲最常用的。短选项与等价长选项放同一格。完整列表见[官方参考](https://docs.docker.com/reference/cli/docker/container/run/)。

### 1. 跑起来的方式：前台还是后台

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-d`，`--detach` | 后台运行，打印容器 ID | 起 nginx、数据库等常驻服务（极常用） |
| `-i`，`--interactive` | 保持 STDIN 打开 | 想往容器里输命令时（常配 `-t`） |
| `-t`，`--tty` | 分配一个伪终端 | 想要一个像 `bash` 那样的终端提示符（常配 `-i`） |
| `--rm` | 容器退出后**自动删掉** | 跑一次性任务、调试容器，不留垃圾 |
| `--attach`，`-a` | 只 attach 指定的 STDIN/STDOUT/STDERR | 精细化控制 attach 哪些流 |
| `--sig-proxy` | 把收到的信号代理给主进程（默认 true） | 极少改 |
| `--detach-keys` | 定义 detach 快捷键 | 默认 `Ctrl-P Ctrl-Q`，想改时用 |

### 2. 起个什么名字、跟谁通信

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `--name` | 给容器起名字 | 后续用名字而不是 ID 操作容器（极常用） |
| `--network` | 把容器接到哪个网络 | 多容器互通时接自定义 bridge（见 [network](./network)） |
| `--network-alias` | 在网络里给容器起别名 | 同网络其他容器用别名解析到它 |
| `-h`，`--hostname` | 容器内的主机名 | 想看 `hostname` 命令输出时 |
| `--dns` | 自定义容器 DNS 服务器 | 默认 DNS 不够用、内网 DNS 时 |
| `--add-host` | 往容器 `/etc/hosts` 加条目 | 容器内写死某个域名解析 |
| `--link` | 老版链接到别的容器（已过时） | 新项目用自定义网络 + DNS 替代 |
| `-l`，`--label` | 给容器打元数据标签 | 批量筛选、按标签管理 |

### 3. 对外暴露端口

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-p`，`--publish` | 把容器端口映射到宿主机 | 如 `-p 8080:80`，宿主机 8080 转容器 80（极常用） |
| `-P`，`--publish-all` | 把镜像 `EXPOSE` 的所有端口映射到宿主机随机端口 | 不想自己挑端口时 |
| `--expose` | 声明容器监听端口（不映射到宿主机） | 配合 `-P`，或同网络内容器间访问 |

### 4. 挂载目录与数据

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-v`，`--volume` | 挂载卷或 bind mount | `-v 宿主机路径:容器路径` 或 `-v 卷名:容器路径`（见 [volume](./volume)） |
| `--mount` | 同上但语法更明确 | `--mount type=bind,source=...,target=...` |
| `--volumes-from` | 继承另一个容器的所有挂载 | 多容器共享同一份数据 |
| `--tmpfs` | 挂一个内存临时目录 | 缓存类、不留痕的数据 |
| `--read-only` | 容器根文件系统只读 | 安全加固，只允许写挂载点 |

### 5. 环境变量与工作目录

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-e`，`--env` | 设环境变量 | 如 `-e MYSQL_ROOT_PASSWORD=xxx`（极常用） |
| `--env-file` | 从文件读一批环境变量 | 变量多、不想写一长串 `-e` |
| `-w`，`--workdir` | 容器内默认工作目录 | 让进程在指定目录里跑 |
| `--entrypoint` | 覆盖镜像的 ENTRYPOINT | 强行改镜像的入口程序 |
| `--user`，`-u` | 以哪个用户跑（名字或 UID） | 不想用 root 跑时 |

### 6. 重启策略与生命周期

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `--restart` | 退出后的重启策略 | `no`（默认）/`on-failure`/`always`/`unless-stopped`（服务必加） |
| `--stop-signal` | 停止容器发什么信号 | 镜像 STOPSIGNAL 不合适时 |
| `--stop-timeout` | 停止前等几秒再 SIGKILL | 优雅关闭需要更久时 |
| `--cidfile` | 把容器 ID 写到文件 | 脚本自动化取 ID |

### 7. 资源限制

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `--cpus` | 能用几个 CPU | 如 `--cpus=1.5` 限 1.5 核 |
| `-c`，`--cpu-shares` | CPU 相对权重 | 抢 CPU 时谁多谁少（相对值） |
| `--cpuset-cpus` | 绑死到哪几个 CPU 核 | 如 `--cpuset-cpus=0,1` |
| `-m`，`--memory` | 内存上限 | 如 `-m 512m`，防一个容器吃光内存 |
| `--memory-swap` | 内存+swap 总上限 | 设 `-1` 表示不限 swap |
| `--pids-limit` | 容器内进程数上限 | 防 fork 炸弹 |
| `--device` | 把宿主机设备给容器 | 如显卡、串口 |
| `--gpus` | 把 GPU 给容器 | 跑 AI/训练镜像 |
| `--blkio-weight` | 磁盘 IO 相对权重 10~1000 | 限制磁盘争抢 |

### 8. 安全与隔离

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `--privileged` | 给容器几乎全部宿主机权限 | 危险！跑 Docker-in-Docker 等特殊场景才用 |
| `--cap-add` / `--cap-drop` | 单独加/删 Linux capability | 比 `--privileged` 精细，推荐 |
| `--security-opt` | 安全选项（seccomp/AppArmor/SELinux） | 加固或绕过默认策略 |
| `--pid` / `--ipc` / `--uts` / `--userns` | 共享宿主机/别的容器的命名空间 | 调试、特殊共享场景 |
| `--init` | 在容器里跑一个 init 进程回收僵尸进程 | 主进程不是 init 时推荐加 |

### 9. 镜像拉取与平台

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `--pull` | 跑之前是否重新拉镜像 | `always`/`missing`(默认)/`never` |
| `--platform` | 指定多平台镜像里用哪个 | 如 `--platform linux/amd64` |
| `-q`，`--quiet` | 拉镜像时不打进度 | 脚本里安静跑 |

> 说明：`docker run` 还有 `--cgroup-parent`、`--sysctl`、`--ulimit`、`--shm-size`、`--storage-opt` 等高级选项，日常很少用，用到时查[官方参考](https://docs.docker.com/reference/cli/docker/container/run/)即可。

## 四、由浅入深的典型示例

### 示例 1：最简启动（前台跑，跑完就退）

```bash
docker run hello-world
```

输出（示意，据 Docker 官方文档）：

```text
Hello from Docker!
This message shows that your installation appears to be working correctly.
...
```

> 这条命令做了：找本地有没有 `hello-world` 镜像 → 没有就去 Docker Hub 拉 → 起容器跑里面的程序 → 打印这段话 → 进程退出、容器停止。

### 示例 2：后台跑一个 nginx（`-d` + `--name` + `-p`）

```bash
docker run --name web -d -p 8080:80 nginx:alpine
```

输出（示意）：

```text
4bed76d3ad428b889c56c1ecc2bf2ed95cb08256db22dc5ef5863e1d03252a19
```

- `--name web`：容器叫 `web`；
- `-d`：后台跑，只打印一串容器 ID；
- `-p 8080:80`：宿主机 8080 端口 → 容器 80 端口，浏览器访问 `http://服务器IP:8080` 就能看到 nginx。

### 示例 3：交互式进容器终端（`-it`）

```bash
docker run -it --name box alpine sh
```

进入后是容器里的 shell：

```text
/ #
```

- `-i`：保持标准输入开着；
- `-t`：分配一个伪终端，才有提示符；
- 最后那个 `sh` 是覆盖镜像默认命令，启动一个 shell；
- 输入 `exit` 退出，容器随之停止。

### 示例 4：退出后自动删容器（`--rm`）

```bash
docker run --rm -it alpine sh
```

> `--rm` 表示这个容器一退出就自动删掉，不占磁盘。调试一次性命令时强烈推荐，避免满屏 `<none>` 垃圾容器。

### 示例 5：挂目录 + 设环境变量

```bash
docker run -d \
  --name mydb \
  -p 3306:3306 \
  -v mysql-data:/var/lib/mysql \
  -e MYSQL_ROOT_PASSWORD=S3cret \
  mysql:8.4
```

- `-v mysql-data:/var/lib/mysql`：把名为 `mysql-data` 的卷挂到容器数据目录，数据不随容器删而丢；
- `-e MYSQL_ROOT_PASSWORD=...`：通过环境变量给 MySQL 设 root 密码。

### 示例 6：指定工作目录、入口程序、运行用户

```bash
docker run --rm \
  -w /app \
  -u 1000:1000 \
  --entrypoint python \
  python:3.12-single --version
```

- `-w /app`：容器内默认目录是 `/app`；
- `-u 1000:1000`：以 UID/GID 1000 身份跑，不用 root；
- `--entrypoint python`：把镜像入口改成 `python`；后面的 `--version` 作为它的参数。

### 示例 7：限制 CPU 和内存

```bash
docker run -d --name limited \
  --cpus="1.5" \
  -m 512m \
  nginx:alpine
```

- `--cpus=1.5`：最多用 1.5 个核；
- `-m 512m`：内存上限 512MB，超了会被 OOM 杀掉。
> 生产环境多容器共用一台机器时，**一定要加资源限制**，否则一个失控容器能把整机拖垮。

### 示例 8：开机自启的重启策略（`--restart`）

```bash
docker run -d --name web --restart=always -p 8080:80 nginx:alpine
```

`--restart` 四种取值：

| 取值 | 含义 |
|---|---|
| `no`（默认） | 退出就不管了 |
| `on-failure` | 非正常退出才重启（可加次数） |
| `always` | 不管怎么退都重启，连 Docker 重启后也会自动拉起 |
| `unless-stopped` | 类似 always，但你手动 stop 后不会再被自动拉起 |

> 跑在生产服务器上的服务容器，几乎都要加 `--restart=always` 或 `unless-stopped`。

### 示例 9：接自定义网络，靠容器名互相访问

```bash
docker network create mynet
docker run -d --name db --network mynet nginx:alpine
docker run --rm --network mynet busybox:latest ping -c 2 db
```

输出（示意）：

```text
PING db (172.18.0.2): 56 data bytes
64 bytes from 172.18.0.2: seq=0 ttl=64 time=0.073 ms
64 bytes from 172.18.0.2: seq=1 ttl=64 time=0.411 ms
```

> 关键：**只有在用户自定义网络里**，容器之间才能用容器名当 DNS 名字互访；默认 `bridge` 网络没有这个 DNS 功能。

### 示例 10：bind mount 挂宿主机代码目录做开发

```bash
docker run --rm -it \
  -v "$PWD":/app \
  -w /app \
  node:20-alpine sh
```

> 把当前宿主机目录挂到容器 `/app`，容器里改代码和宿主机实时同步，省得每次改完都重新 build。

### 示例 11：只读根文件系统 + 临时目录

```bash
docker run --rm \
  --read-only \
  --tmpfs /tmp \
  nginx:alpine
```

> 根目录只读，只有 `/tmp` 可写，安全加固场景常用。

## 五、高频组合速记

实际工作中基本就这几个组合，记住即可：

| 命令 | 用途 |
|---|---|
| `docker run -d --name x -p 8080:80 nginx` | 后台起服务并映射端口（**最常用**） |
| `docker run -it --rm alpine sh` | 临时进一个干净容器玩一下，退出即删 |
| `docker run -d --name x --restart=always 镜像` | 开机自启的常驻服务 |
| `docker run --rm -v "$PWD":/app -w /app 镜像` | 挂本地目录进容器做开发 |
| `docker run -d -e KEY=val -v 卷:/data 镜像` | 带环境变量和持久化数据 |
| `docker run --rm --network mynet 镜像 ping 容器名` | 验证自定义网络里的 DNS 互通 |
| `docker run --rm --cpus=1 -m 512m 镜像` | 起一个资源受限的测试容器 |

## 六、RHEL 系与 Debian 系差异

`docker run` 命令本身**在 RHEL/Rocky 与 Ubuntu/Debian 上用法完全一致**，差异只在"怎么装 Docker"和默认运行时：

- **包名与安装**：
  - RHEL/Rocky（dnf）：配置 Docker 官方 yum 源后 `sudo dnf install docker-ce docker-ce-cli containerd.io`，再 `sudo systemctl enable --now docker`；
  - Debian/Ubuntu（apt）：配置官方 apt 源后 `sudo apt install docker-ce docker-ce-cli containerd.io`，再 `sudo systemctl enable --now docker`。
- **运行时**：Docker Engine 28.x 默认用 **containerd** 作为容器运行时（`docker info` 里 `Runtimes: io.containerd.runc.v2`，`Default Runtime: runc`）；不再像早期版本那样默认依赖 `dockerd` 直接管容器。
- **SELinux（RHEL 系特有）**：RHEL 开了 SELinux 时，bind mount 宿主机目录可能被拦截，需要加 `--security-opt label=disable` 或给目录打正确的 SELinux 标签（`:z`/`:Z`）；Debian 系默认没 SELinux，没这问题。
- **用户组**：两系都建议把自己加进 `docker` 组（`sudo usermod -aG docker $USER`），免每次 `sudo`。

## 七、新手易错点

1. **`-it` 和 `-d` 不要同时用**：`-d` 是后台，`-it` 是交互终端，语义冲突。想进后台容器用 `docker exec -it`（见 [exec](./exec)）。
2. **`-p 80:80` 左边是宿主机、右边是容器**：写反了会访问不到；宿主机端口被占会启动失败。
3. **不加 `--name` 会拿到随机名字**：如 `vibrant_cannon`，后面命令还得 `docker ps` 去抄，很麻烦，服务容器一定 `--name`。
4. **`-v 卷名:/容器路径` 才是持久化；`-v /容器路径`（匿名卷）退出不删但名字随机**：重要数据要么用命名卷，要么用 bind mount（见 [volume](./volume)）。
5. **`--privileged` 极其危险**：等于把宿主机 root 直接给容器，容器被攻破=宿主机被攻破。能用 `--cap-add` 精确授权就别用它。
6. **镜像名不写标签默认 `:latest`**：`latest` 不代表"最新"，只是个普通标签，生产环境一定要写死版本标签。
7. **端口映射只对 `bridge` 网络有意义**：`--network=host` 时容器直接用宿主机网络栈，`-p` 会被忽略（或报错）。
8. **`docker run` 后退出的容器不会自动消失**：会停在 `Exited` 状态占磁盘，定期用 `docker container prune` 清理（见 [system-prune](./system-prune)）。

## 八、相关命令与文档

- 速查页：[Docker 命令速查](../docker-commands)
- 只建不起：`docker create`（详解见 [lifecycle](./lifecycle)）
- 进正在跑的容器：`docker exec`（详解见 [exec](./exec)）
- 看容器日志：`docker logs`（详解见 [logs](./logs)）
- 删容器：`docker rm`（详解见 [lifecycle](./lifecycle)）
- 网络与端口原理：`docker network`（详解见 [network](./network)）
- 数据持久化：`docker volume`（详解见 [volume](./volume)）
- 系统清理：`docker system prune`（详解见 [system-prune](./system-prune)）
- 原理与实战：[Docker 实战手册](../../guide/container-docker)
- 官方参考：https://docs.docker.com/reference/cli/docker/container/run/
