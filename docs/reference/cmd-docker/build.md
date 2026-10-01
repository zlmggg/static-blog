# docker build 命令详解：用 Dockerfile 把代码打包成镜像

> 本文是 [Docker 命令速查](../docker-commands#镜像管理) 中 `docker build` 的从 0 到 1 详解。
> 目标：把 `docker build --help` 里的每个选项讲清楚，多看几遍后，你在服务器上敲 `docker build --help` 就知道该用哪个选项。
> 环境依据：Docker Engine 28.x，`docker build` 已由 **BuildKit** 后端执行（Buildx），containerd 默认运行时；本沙箱未安装 docker，选项与输出据 [Docker 官方 buildx build 参考](https://docs.docker.com/reference/cli/docker/buildx/build/) 核实，示例输出为示意。

## 一、命令是干什么的

`docker build` 读取一个叫 `Dockerfile` 的文本文件，里面一行行写着"从哪个基础镜像出发、COPY 哪些文件、RUN 什么命令、暴露哪个端口、启动什么进程"，build 命令就把这些步骤一层一层执行，最后产出一个可 `docker run` 的镜像。

- 末尾的 `.` 是**构建上下文**（当前目录），Docker 会把整个目录打包传给构建后端；
- `-t` 给产物起名字标签；
- `-f` 指定 Dockerfile 路径（不在当前目录时）。

> 类比：Dockerfile 是菜谱，`docker build` 是照菜谱炒菜，末尾的 `.` 是"食材都在这个厨房里"，`-t` 是给这盘菜贴的菜名牌。

> **BuildKit 说明**：Docker Engine 23.0 起 `docker build` 默认就用 BuildKit（通过 buildx），不再需要手动 `DOCKER_BUILDKIT=1`。旧版那个经典的 `Step 1/12 : RUN ...` 输出风格在 BuildKit 下变成了带缓存命中、并行执行的进度视图。

## 二、命令语法

```bash
docker build [选项] PATH | URL | -
```

- `PATH`（最常用 `.`）：构建上下文目录，Dockerfile 里 `COPY ./xxx` 的相对路径都相对它；
- `-t`：给镜像打 `名字:标签`；
- `-f`：指定 Dockerfile（默认找 `PATH/Dockerfile`）。

## 三、选项全表（对照 `docker build --help`）

### 1. 产物命名与文件位置

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-t`，`--tag` | 产物镜像名:标签 | 如 `-t myapp:v1`（极常用） |
| `-f`，`--file` | 指定 Dockerfile 路径 | Dockerfile 不叫默认名/不在上下文根时 |
| `--iidfile` | 把产物镜像 ID 写到文件 | CI 脚本里取 ID |
| `--label` | 给镜像加元数据标签 | 记录谁建的、什么版本 |

### 2. 构建变量与缓存

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `--build-arg` | 传 Dockerfile 里 `ARG` 变量 | 如代理、版本号（极常用） |
| `--no-cache` | 构建时**不用**任何缓存 | 怀疑缓存脏了、强制全新构建时 |
| `--pull` | 构建前重新拉基础镜像 | 想确保用最新 base 镜像 |
| `--cache-from` / `--cache-to` | 从外部/往外部存构建缓存 | CI 加速跨机构建 |

### 3. 多阶段与目标

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `--target` | 只构建到多阶段里的某一阶段 | 多阶段构建时只编译不打包最终镜像 |
| `--platform` | 构建指定平台的镜像 | 如 `--platform linux/arm64`（在 x86 机器上交叉构建） |

### 4. 输出方式

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-o`，`--output` | 输出到指定位置 | `--output type=docker,dest=...` 或 `type=local,dest=./out` |
| `--load` | 构建完加载进本地 docker 镜像列表 | 多平台 buildx 默认不自动 load 时用 |
| `--push` | 构建完直接推到仓库 | 多平台镜像推 registry 时 |
| `-q`，`--quiet` | 只打印最终镜像 ID | CI 里安静构建 |
| `--progress` | 进度输出风格 | `plain` 看完整构建日志，`auto`(默认) 交互式 |

### 5. 其它

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `--add-host` | 构建容器里加 hosts 条目 | 构建时要访问固定域名 |
| `--secret` | 注入构建机密（不进镜像层） | 传 token/密码又怕写进镜像 |
| `--ssh` | 把 SSH agent socket 给构建用 | 构建时要从私有 git 仓库拉代码 |
| `--network` | RUN 步骤用什么网络 | 默认 `default`；要访问宿主机服务时设 `host` |
| `--shm-size` | 构建容器的 /dev/shm 大小 | 构建需要大共享内存时 |

## 四、由浅入深的典型示例

### 示例 1：最基本的构建

```bash
docker build -t myapp:v1 .
```

输出（示意）：

```text
[+] Building 2.3s (6/6) FINISHED
 => [internal] load build definition from Dockerfile
 => => transferring dockerfile: 32B
 => [1/2] FROM docker.io/library/python:3.12-slim
 => [2/2] COPY . /app
 => exporting to image
 => => exporting layers
 => => writing image sha256:abc123...
 => => naming to docker.io/library/myapp:v1
```

> 末尾 `.` 表示用当前目录做构建上下文。构建完 `docker images` 就能看到 `myapp:v1`。

### 示例 2：指定 Dockerfile（`-f`）

```bash
docker build -f docker/Dockerfile.prod -t myapp:v1 .
```

> 项目里同时有 `Dockerfile.dev`、`Dockerfile.prod` 时用 `-f` 选。

### 示例 3：传构建变量（`--build-arg`）

```bash
docker build --build-arg APP_VERSION=2.1.0 -t myapp:v2.1 .
```

> Dockerfile 里要有 `ARG APP_VERSION` 才能接住；`ARG` 变量不写进最终镜像，和 `ENV` 不同。

### 示例 4：不用缓存强制重建（`--no-cache`）

```bash
docker build --no-cache -t myapp:v1 .
```

> 怀疑某一层缓存是脏的（比如 apt 源缓存了旧包）时用。

### 示例 5：只构建到多阶段的某一步（`--target`）

Dockerfile 片段：

```dockerfile
FROM golang:1.22 AS builder
WORKDIR /src
COPY . .
RUN go build -o /app/server .

FROM debian:12-slim
COPY --from=builder /app/server /app/server
CMD ["/app/server"]
```

只编译不打最终镜像：

```bash
docker build --target builder -t myapp:builder .
```

> 调试编译阶段、或跑测试时常用 `--target`。

### 示例 6：交叉构建别的平台（`--platform`）

```bash
docker build --platform linux/arm64 -t myapp:arm64 .
```

> 在 x86 服务器上构建 arm64 镜像（需要 buildx 多平台支持，可能要 QEMU）。

### 示例 7：构建完直接推仓库（`--push`）

```bash
docker buildx build --platform linux/amd64,linux/arm64 \
  -t myregistry.example.com/myteam/myapp:v1 --push .
```

> 多平台镜像不能 `--load` 进本地 docker（本地只有一个架构），直接 `--push` 到 registry。

### 示例 8：看完整构建日志（`--progress plain`）

```bash
docker build --progress plain -t myapp:v1 .
```

> BuildKit 默认把每层输出折叠成一行，想看 `RUN` 命令的完整 stdout/stderr 就用 `plain`。

### 示例 9：用 .dockerignore 排除不该进上下文的文件

`.dockerignore` 文件内容：

```text
node_modules
.git
*.log
dist
```

> 放在构建上下文根目录，作用和 `.gitignore` 类似：告诉 Docker 这些文件别打包进上下文。**不写的话 `node_modules`、`.git` 几百 MB 全被发给构建后端，又慢又容易把密钥COPY 进镜像**。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `docker build -t 名字:标签 .` | 最常用构建 |
| `docker build -f xx/Dockerfile -t 名字 .` | 指定 Dockerfile |
| `docker build --build-arg K=v -t 名字 .` | 带构建变量 |
| `docker build --no-cache -t 名字 .` | 强制全新构建 |
| `docker build --target 阶段 -t 名字 .` | 只建到某阶段 |
| `docker build --progress plain .` | 看完整日志 |
| `docker buildx build --push -t 仓库/名:标签 .` | 多平台直接推 |

## 六、RHEL 系与 Debian 系差异

- 命令两系一致；
- **BuildKit 依赖**：两系装 `docker-ce` 都自带 buildx 插件；
- **交叉构建**：在 x86 机器上构建 arm64 需要装 QEMU 用户态翻译（`apt install qemu-user-static` / `dnf install qemu-user-static`），命令本身一样；
- **构建缓存目录**：默认在 `/var/lib/docker/buildkit`，两系路径相同。

## 七、新手易错点

1. **末尾的 `.` 不能忘**：它是构建上下文。写成 `docker build -t myapp` 会报错"需要 context 路径"。
2. **`.dockerignore` 很重要**：不写的话 `.git`、`node_modules`、本地密钥全被打进上下文，既慢又有泄露风险。
3. **`--build-arg` 和 `docker run -e` 不是一回事**：`build-arg` 只在构建时存在，不写进镜像运行环境；运行时变量用 `run -e`。
4. **BuildKit 下 `--load` 才进本地镜像列表**：多平台 buildx build 默认只产出 manifest，不 `--load` 的话 `docker images` 看不到。
5. **`--no-cache` 很慢**：它跳过所有层缓存，生产 CI 别滥用，出问题再用。
6. **Dockerfile 里 COPY 的路径相对的是上下文，不是 Dockerfile 位置**：Dockerfile 在子目录但上下文是 `.`，COPY 路径仍相对 `.`。
7. **构建上下文太大是常见卡点**：如果 build 卡在 `transferring context` 很久，八成是上下文里有大目录，去补 `.dockerignore`。
8. **别把密钥写进 Dockerfile 的 RUN**：会留在层历史里，`docker history` 能翻出来。要用 `--secret`。

## 八、相关命令与文档

- 速查页：[Docker 命令速查](../docker-commands#镜像管理)
- 拉/推/删镜像：`docker images/pull/push/rmi`（详解见 [images](./images)）
- 起容器：`docker run`（详解见 [run](./run)）
- Compose 里构建：`docker compose build`（详解见 [compose](./compose)）
- 原理与实战：[Docker 实战手册](../../guide/container-docker)
- 官方参考：https://docs.docker.com/reference/cli/docker/buildx/build/
