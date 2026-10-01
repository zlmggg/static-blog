# docker images / pull / push / rmi / tag / save / load 详解：镜像管理全家桶

> 本文是 [Docker 命令速查](../docker-commands#镜像管理) 中 `images`、`pull`、`push`、`rmi`、`tag`、`save`、`load` 的从 0 到 1 详解，本篇一次讲清这七个"管镜像"的命令。
> 目标：把每个命令的选项讲清楚，多看几遍后，你在服务器上敲 `docker <命令> --help` 就知道该用哪个选项。
> 环境依据：Docker Engine 28.x（docker CLI 28.x），内容寻址镜像存储，containerd 默认运行时；本沙箱未安装 docker，选项与输出据 [Docker 官方命令参考](https://docs.docker.com/reference/cli/docker/image/ls/) 核实，示例输出为示意。

## 一、命令是干什么的

镜像是容器的"安装盘"，这组命令管镜像的一生：

- `docker images`（`docker image ls`）：列出本地有哪些镜像；
- `docker pull`：从仓库（默认 Docker Hub）下载镜像到本地；
- `docker push`：把本地镜像上传到仓库；
- `docker tag`：给镜像再起一个别名/标签（常用于打仓库地址后 push）；
- `docker rmi`：删本地镜像；
- `docker save`：把镜像导出成 tar 文件（离线分发）；
- `docker load`：从 tar 文件导回镜像。

> 类比：`images` 像列出你买了哪些光盘；`pull` 是网购下载到本地；`push` 是把你做的盘上传到网盘；`tag` 是给光盘贴个新标签；`rmi` 是扔光盘；`save/load` 是把光盘拷成 ISO 文件传给没网的机器。

## 二、命令语法

```bash
docker images [选项] [仓库[:标签]]
docker pull   [选项] 名字[:标签|@摘要]
docker push   [选项] 名字[:标签]
docker rmi    [选项] 镜像 [镜像...]
docker tag    源镜像[:标签] 目标镜像[:标签]
docker save   [选项] 镜像 [镜像...]
docker load   [选项]
```

## 三、选项全表

### 1. docker images（列本地镜像）

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-a`，`--all` | 显示所有镜像（含中间层和 dangling） | 默认隐藏了中间层，想看全时 |
| `-q`，`--quiet` | 只输出镜像 ID | 脚本批量删 |
| `-f`，`--filter` | 过滤 | 如 `dangling=true`、`reference=nginx*` |
| `--digests` | 显示镜像摘要（digest） | 想按摘要拉/删时 |
| `--format` | Go 模板自定义列 | 只要仓库名和标签 |
| `--no-trunc` | 不截断镜像 ID | 看完整 sha256 |

常用过滤器：`dangling=true`（悬空镜像）、`before=镜像`、`since=镜像`、`label=...`、`reference=nginx*`。

> **dangling（悬空）镜像**：显示为 `<none>:<none>`，是旧镜像被新 build 顶替标签后留下的"无名"镜像，通常可安全清理。

### 2. docker pull

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-a`，`--all-tags` | 拉仓库下所有标签 | 想要整个仓库的全部版本 |
| `--platform` | 拉多平台镜像里指定平台的 | 如 `--platform linux/arm64` |
| `-q`，`--quiet` | 不打拉取进度 | 脚本里安静拉 |

> 不写标签默认 `:latest`。可用 `名字@sha256:摘要` 拉**固定摘要**的镜像（不可变，不会被动更新）。

### 3. docker push

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-a`，`--all-tags` | 推送该镜像所有标签 | 一次推多个版本号 |
| `--platform` | 只推某个平台的 manifest | 多平台镜像拆着推 |
| `-q`，`--quiet` | 不打进度 | 脚本里 |

> push 之前必须先 `docker tag` 把镜像打上 `仓库地址/命名空间/名字:标签` 的全名，否则推不到 Docker Hub 你的账号下。

### 4. docker rmi（删镜像）

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-f`，`--force` | 强制删（连被多个标签引用的也一起摘标签） | 一个镜像挂了多个标签时 |
| `--no-prune` | 不删未被引用的父层 | 极少用 |
| `--platform` | 只删多平台镜像里某一平台变体 | 省磁盘时 |

> **正在被容器使用的镜像删不掉**（除非 `-f`）；删的是镜像不是容器，先停删容器再删镜像。

### 5. docker tag

没有开关参数，语法就是 `docker tag 源 目标`：

```bash
docker tag 源镜像[:标签] 目标镜像[:标签]
```

> tag 不复制镜像数据，只是多一个名字指向同一份内容，不额外占磁盘。

### 6. docker save / load

| 命令 | 选项 | 含义 |
|---|---|---|
| `save` | `-o FILE`（`--output`） | 写到文件而不是 stdout |
| `save` | `--platform` | 只保存某平台变体 |
| `load` | `-i FILE`（`--input`） | 从文件读，而不是 stdin |
| `load` | `-q` | 不打印加载信息 |
| `load` | `--platform` | 只加载某平台变体 |

> `save` 导出的 tar 里**保留所有标签**，`load` 回来时标签也一起恢复。

## 四、由浅入深的典型示例

### 示例 1：列出本地镜像

```bash
docker images
```

输出（示意，据 Docker 官方文档）：

```text
REPOSITORY   TAG       IMAGE ID       CREATED       SIZE
nginx        latest    6137f817b3cd   2 weeks ago   192MB
postgres     16        746b819f315e   4 days ago    432MB
alpine       latest    c059dbf865a4   3 weeks ago   7.8MB
```

> 同一个镜像若挂了多个标签会显示多行，但 IMAGE ID 相同、SIZE 只算一份。

### 示例 2：按仓库名过滤

```bash
docker images nginx
```

> 只列 nginx 这个仓库的所有标签。`docker images nginx:1.27` 则精确到某个标签。

### 示例 3：拉取镜像（默认 latest）

```bash
docker pull debian
```

输出（示意）：

```text
Using default tag: latest
latest: Pulling from library/debian
e756f3fdd6a3: Pull complete
Digest: sha256:3f1d6c17773a45c97bd8f158d665c9709d7b29ed7917ac934086ad96f92e4510
Status: Downloaded newer image for debian:latest
docker.io/library/debian:latest
```

### 示例 4：拉指定版本标签

```bash
docker pull ubuntu:24.04
```

> 生产环境永远写死标签，别用 `:latest`。

### 示例 5：按摘要拉取（固定版本）

```bash
docker pull ubuntu@sha256:2e863c44b718727c860746568e1d54afd13b2fa71b160f5cd9058fc436217b30
```

> 摘要不可变，每次拉到的都是同一份内容；缺点是不会自动拿到安全更新，要更新得换摘要。

### 示例 6：打标签后推到自己的仓库

```bash
docker tag nginx:latest myregistry.example.com:5000/myteam/web:v1.0
docker push myregistry.example.com:5000/myteam/web:v1.0
```

> tag 那步把本地 nginx 改名成带私有仓库地址的全名，push 才知道往哪传。

### 示例 7：删镜像

```bash
docker rmi nginx:latest
```

输出（示意）：

```text
Untagged: nginx:latest
Deleted: sha256:6137f817b3cd...
```

> 如果一个镜像挂了多个标签，先删标签（Untagged），最后一个标签删掉时才真正 Deleted。

### 示例 8：删悬空镜像（批量）

```bash
docker rmi $(docker images -f "dangling=true" -q)
```

> 清掉那些 `<none>:<none>` 的旧层。更省事的是 `docker image prune`（见 [system-prune](./system-prune)）。

### 示例 9：导出镜像到 tar 文件

```bash
docker save -o nginx.tar nginx:latest
ls -lh nginx.tar
```

输出（示意）：

```text
-rw------- 1 user user 192M Sep 30 10:00 nginx.tar
```

> 离线机器没网时，把镜像 scp 过去再 `docker load`。

### 示例 10：从 tar 文件导入

```bash
docker load -i nginx.tar
```

输出（示意）：

```text
Loaded image: nginx:latest
```

### 示例 11：导出时顺便 gzip 压缩

```bash
docker save myimage:latest | gzip > myimage_latest.tar.gz
```

> 镜像层是压缩的 tar，再 gzip 能小一点。`docker load` 能直接读 gzip/bzip2/xz/zstd 压缩包。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `docker images` | 列本地镜像 |
| `docker images -q` | 只要镜像 ID |
| `docker pull 镜像:标签` | 拉镜像 |
| `docker tag 旧名 仓库/新名:标签` | 改全名准备 push |
| `docker push 仓库/名:标签` | 推镜像 |
| `docker rmi 镜像:标签` | 删镜像 |
| `docker rmi $(docker images -f dangling=true -q)` | 清悬空镜像 |
| `docker save -o x.tar 镜像` | 导出离线包 |
| `docker load -i x.tar` | 导入离线包 |

## 六、RHEL 系与 Debian 系差异

- 命令两系一致；
- **镜像存储位置**：都在 `/var/lib/docker`（overlay2/overlayfs 驱动）；
- **拉取加速**：国内两系都建议配镜像加速器（`/etc/docker/daemon.json` 的 `registry-mirrors`），RHEL 系还要注意 firewalld/SELinux 是否拦了 registry；
- **包名**：`docker-ce-cli` 提供这些命令，RHEL 用 `dnf install docker-ce-cli`，Debian 用 `apt install docker-ce-cli`。

## 七、新手易错点

1. **`docker images` 不显示中间层和 dangling**：想看全加 `-a`；但日常别 `-a`，不然几百个中间层刷屏。
2. **删镜像前先删用它的容器**：有容器在用（哪怕已停止）镜像会被引用，`rmi` 会报错；用 `-f` 能强删但会留下"悬空容器"。
3. **`docker rmi` 不删远程仓库里的镜像**：它只删本地；删远端要登录 registry 用 API/UI。
4. **`tag` 不复制数据**：tag 完 `docker images` 看到两行同一 IMAGE ID，不占双倍空间。
5. **`save` 是镜像、`export` 是容器**：`docker save` 存镜像（含所有层和历史）；`docker export` 存容器文件系统快照（扁平化、丢历史），别搞混。
6. **`latest` 不是"最新"保证**：它只是个普通标签，别人推了新的 `latest` 你本地不会自动更新，要重新 `docker pull`。
7. **push 前要先 login**：推 Docker Hub/私有仓库得先 `docker login`，否则报 unauthorized。
8. **`--platform` 是 28.x 较新特性**：老版本 docker 不支持 `rmi --platform`、`save --platform`，以本机 `--help` 为准。

## 八、相关命令与文档

- 速查页：[Docker 命令速查](../docker-commands#镜像管理)
- 构建镜像：`docker build`（详解见 [build](./build)）
- 清理镜像/系统：`docker system prune`（详解见 [system-prune](./system-prune)）
- 起容器：`docker run`（详解见 [run](./run)）
- 原理与实战：[Docker 实战手册](../../guide/container-docker)
- 官方参考：https://docs.docker.com/reference/cli/docker/image/ls/
