# docker volume 详解：数据卷 ls / create / inspect / rm / prune

> 本文是 [Docker 命令速查](../docker-commands#存储卷) 中 `docker volume` 各子命令的从 0 到 1 详解，本篇一次讲清 `ls`、`create`、`inspect`、`rm`、`prune`，以及 named volume 与 bind mount 的区别。
> 目标：把每个子命令的选项讲清楚，多看几遍后，你在服务器上敲 `docker volume <子命令> --help` 就知道该用哪个选项。
> 环境依据：Docker Engine 28.x（docker CLI 28.x），本地卷默认存放在 `/var/lib/docker/volumes`，containerd 默认运行时；本沙箱未安装 docker，选项与输出据 [Docker 官方命令参考](https://docs.docker.com/reference/cli/docker/volume/ls/) 核实，示例输出为示意。

## 一、命令是干什么的

容器是"一次性"的：容器删了，里面写的文件就没了。要让数据**在容器删除/重建后还在**，就得用 volume（数据卷）。`docker volume` 这组命令专门管理这些独立于容器生命周期的数据：

- `docker volume ls`：列出所有数据卷；
- `docker volume create`：建一个命名卷；
- `docker volume inspect`：看卷的详情（存在宿主机哪个路径）；
- `docker volume rm`：删卷；
- `docker volume prune`：一键清掉没人用的卷。

> 类比：容器像租的酒店房间（退房就清空），volume 像你自己租的储物柜——房间退了，柜子里的东西还在，下一个房间接着用。

### named volume vs bind mount（重点）

Docker 挂载数据有两种方式，都用 `-v`，但写法和语义不同：

| 写法 | 类型 | 谁管目录 | 适合场景 |
|---|---|---|---|
| `-v 卷名:/容器路径` | **named volume** | Docker 在 `/var/lib/docker/volumes/` 里管 | 数据库数据、Docker 全托管 |
| `-v /宿主机绝对路径:/容器路径` | **bind mount** | 你自己指定宿主机目录 | 挂代码做开发、挂配置文件 |
| `-v /容器路径`（左边没东西） | **匿名卷** | Docker 自动起名 | 容器内部临时数据 |

> 经验法则：**生产数据库用 named volume；开发改代码用 bind mount；别用匿名卷存重要数据**（名字随机，事后找不到）。

## 二、命令语法

```bash
docker volume ls       [选项]
docker volume create   [选项] [卷名]
docker volume inspect  [选项] 卷 [卷...]
docker volume rm       [选项] 卷 [卷...]
docker volume prune    [选项]
```

## 三、选项全表

### 1. docker volume ls

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-f`，`--filter` | 过滤 | `dangling=true`（没人用的）、`name=xxx`、`driver=local` |
| `--format` | Go 模板自定义列 | 只要卷名和驱动 |
| `-q`，`--quiet` | 只输出卷名 | 脚本批量删 |

### 2. docker volume create

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-d`，`--driver` | 卷驱动，默认 `local` | 用 NFS/块存储等外部驱动时 |
| `--label` | 打元数据标签 | 批量管理 |
| `-o`，`--opt` | 驱动专属参数 | 如 `type=nfs`、`device=...` |

> 不写卷名 Docker 会自动生成一个随机名字。

### 3. docker volume inspect

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-f`，`--format` | Go 模板抠字段 | 只要 Mountpoint |

### 4. docker volume rm

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-f`，`--force` | 强制删卷 | 卷还被容器引用时慎用 |

> **正在被容器使用的卷删不掉**（即使容器已停止，只要还引用着）。

### 5. docker volume prune

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-a`，`--all` | 删所有没人用的卷（不只匿名卷） | 连命名卷也清（**危险**） |
| `-f`，`--force` | 不提示直接删 | 脚本里 |
| `--filter` | 按标签过滤 | 只删带某标签的 |

> 默认 `prune` 只删**匿名卷**；加 `-a` 才会动命名卷——命名卷里可能是数据库数据，**生产环境别随便加 -a**。

## 四、由浅入深的典型示例

### 示例 1：列出所有卷

```bash
docker volume ls
```

输出（示意，据 Docker 官方文档）：

```text
DRIVER    VOLUME NAME
local     mysql-data
local     rosemary
local     7f3a...（匿名卷，一长串哈希名）
```

### 示例 2：创建命名卷

```bash
docker volume create hello
```

输出（示意）：

```text
hello
```

### 示例 3：用卷起容器

```bash
docker run -d -v hello:/world busybox ls /world
```

> 第一次用 `hello:/world` 时，`hello` 卷若不存在 Docker 会自动帮你建。

### 示例 4：看卷在宿主机哪

```bash
docker volume inspect hello
```

输出（示意）：

```json
[
  {
    "CreatedAt": "2026-09-30T10:00:00Z",
    "Driver": "local",
    "Mountpoint": "/var/lib/docker/volumes/hello/_data",
    "Name": "hello",
    "Scope": "local"
  }
]
```

> 卷在宿主机的真实路径就是 `Mountpoint`，可以直接在宿主机 `ls /var/lib/docker/volumes/hello/_data` 看里面的文件。

### 示例 5：只要挂载路径（`--format`）

```bash
docker volume inspect --format '{{ .Mountpoint }}' hello
```

输出（示意）：

```text
/var/lib/docker/volumes/hello/_data
```

### 示例 6：bind mount 挂宿主机目录（对比 named volume）

```bash
docker run -d \
  -v /home/me/mycode:/app \
  -w /app \
  node:20-alpine
```

> 左边是**宿主机绝对路径**，右边是容器路径。宿主机改代码容器里立刻看到，开发时常用。

### 示例 7：用 --mount 显式写法（更清晰）

```bash
docker run -d \
  --mount type=volume,source=mysql-data,target=/var/lib/mysql \
  mysql:8.4
```

等价于 `-v mysql-data:/var/lib/mysql`。`--mount` 语法更长但更明确，适合写脚本。

### 示例 8：删一个卷

```bash
docker volume rm hello
```

输出（示意）：

```text
hello
```

### 示例 9：清理没人用的卷

```bash
docker volume prune
```

输出（示意）：

```text
WARNING! This will remove anonymous local volumes not used by at least one container.
Are you sure you want to continue? [y/N] y
Deleted Volumes:
7f3a...
Total reclaimed space: 36 B
```

> 默认只清匿名卷。加 `-a` 会连命名卷一起清，**三思**。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `docker volume ls` | 看所有卷 |
| `docker volume create 名字` | 建命名卷 |
| `docker volume inspect 名字` | 看卷在宿主机哪 |
| `docker volume rm 名字` | 删卷 |
| `docker volume prune` | 清匿名卷 |
| `docker run -v 卷名:/容器路径` | 挂命名卷 |
| `docker run -v /宿主机路径:/容器路径` | bind mount |

## 六、RHEL 系与 Debian 系差异

- 命令两系一致；
- **bind mount 的 SELinux 标签**：RHEL 系开 SELinux 时，bind mount 进容器的目录可能因 SELinux 标签不对而被容器内进程拒绝访问，要加 `:z`（共享）或 `:Z`（私有重标签）：`-v /host/path:/container/path:z`。Debian 系默认无 SELinux，不需要；
- **卷存储路径**：两系都在 `/var/lib/docker/volumes`；
- **NFS 卷**：`docker volume create -d local -o type=nfs -o device=:/path -o o=addr=x.x.x.x,rw` 两系语法一致。

## 七、新手易错点

1. **`docker rm -v` 只删匿名卷，不删命名卷**：命名卷要单独 `docker volume rm`，这是 Docker 故意保护数据。
2. **`docker volume prune -a` 是危险操作**：会把"当前没被容器引用"的命名卷也删掉——如果你数据库容器停了但卷还想留着，别加 `-a`。
3. **bind mount 左边必须是绝对路径**：`-v ./mydir:/app` 的 `./mydir` 在某些 Docker 版本会被当成"卷名"而不是路径，写成绝对路径最稳。
4. **容器删了卷还在**：`docker rm` 不加 `-v` 时卷（含命名卷）保留；想彻底清数据用 `docker volume rm`。
5. **匿名卷名字是哈希**：`docker run -v /data` 产生的卷名字是一长串随机哈希，事后很难知道哪个是哪个，重要数据别用匿名卷。
6. **卷在被引用时删不掉**：哪怕容器是 Exited 状态，只要它还引用着这个卷，`rm` 就报错；先 `docker rm` 那个容器。
7. **bind mount 会覆盖容器内目录**：挂上去之后，容器内原路径下镜像自带的文件会被"遮住"，不是删了，是被 bind 暂时盖掉。

## 八、相关命令与文档

- 速查页：[Docker 命令速查](../docker-commands#存储卷)
- 起容器挂卷：`docker run -v`（详解见 [run](./run)）
- 一键清理：`docker system prune --volumes`（详解见 [system-prune](./system-prune)）
- 容器间共享卷：`--volumes-from`（见 [run](./run)）
- 原理与实战：[Docker 实战手册](../../guide/container-docker)
- 官方参考：https://docs.docker.com/reference/cli/docker/volume/ls/
