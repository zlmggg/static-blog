---
title: "Dockerfile 指令速查：从 FROM 到 HEALTHCHECK"
description: "本文是 Docker 命令速查 中「Dockerfile」的详解。只讲指令怎么写、层怎么缓存、多阶段怎么用；docker build 的参数（-f、--build-arg、--target、--platform）见 docker build。 官方文档：Dockerfile reference"
---
# Dockerfile 指令速查：从 FROM 到 HEALTHCHECK

> 本文是 [Docker 命令速查](../docker-commands#dockerfile-与镜像构建) 中「Dockerfile」的详解。只讲**指令怎么写、层怎么缓存、多阶段怎么用**；`docker build` 的参数（`-f`、`--build-arg`、`--target`、`--platform`）见 [docker build](./build)。
>
> 官方文档：[Dockerfile reference](https://docs.docker.com/reference/dockerfile/)

## 一、最小可用 Dockerfile

```dockerfile
FROM ubuntu:24.04

RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .
EXPOSE 8080
CMD ["/app/server"]
```

```bash
docker build -t app:1.0 .
docker run --rm -p 8080:8080 app:1.0
```

## 二、指令全表

### 基础与元信息

| 指令 | 作用 | 关键点 |
|---|---|---|
| `FROM` | 指定基础镜像，必须是第一条指令（`ARG` 除外） | 生产别用 `latest`，锁具体版本 |
| `ARG` | 构建期变量 | 只在构建阶段存在；`FROM` 前的 `ARG` 可在 `FROM` 里用 |
| `ENV` | 运行期环境变量 | 会写进镜像；不要放密钥 |
| `WORKDIR` | 设置工作目录 | 目录不存在会自动创建；后续 `RUN/COPY/CMD` 都相对它 |
| `USER` | 切换运行用户 | 生产建议非 root；需先 `RUN useradd` |
| `LABEL` | 镜像元数据 | 如 `org.opencontainers.image.version` |

### 文件与构建

| 指令 | 作用 | 关键点 |
|---|---|---|
| `COPY` | 从构建上下文复制文件 | 支持 `--chown`；路径相对**上下文**，不是 Dockerfile 所在目录 |
| `ADD` | 复制 + 自动解压 tar + 支持 URL | 除非需要解压/远程下载，否则优先 `COPY` |
| `RUN` | 构建时执行命令 | shell 形式 `/bin/sh -c`；exec 形式 `["cmd","arg"]` 不经过 shell |
| `ONBUILD` | 留给下游镜像触发的指令 | 基础镜像常用，普通业务镜像少用 |

### 运行与健康检查

| 指令 | 作用 | 关键点 |
|---|---|---|
| `CMD` | 默认启动命令 | `docker run` 末尾参数会**覆盖** CMD；exec 形式才能正确接收信号 |
| `ENTRYPOINT` | 固定入口 | `docker run` 参数作为它的追加参数；exec 形式优先 |
| `EXPOSE` | 声明监听端口 | 只是文档/元数据，不实际映射端口 |
| `VOLUME` | 声明数据卷 | 运行时会创建匿名卷；业务数据建议用 `-v` 显式挂载 |
| `STOPSIGNAL` | 停止容器时发送的信号 | 默认 `SIGTERM`；需要优雅退出时确认 |
| `HEALTHCHECK` | 健康检查 | `--interval`、`--timeout`、`--retries`；配合 `docker ps` 的 health 状态 |

### 多阶段

| 写法 | 作用 |
|---|---|
| `FROM golang:1.24 AS builder` | 给阶段命名 |
| `COPY --from=builder /out/app /app` | 从前面阶段复制产物 |
| `COPY --from=0 ...` | 按序号引用阶段 |
| `FROM scratch` | 空基础镜像，只放静态二进制 |

## 三、CMD 与 ENTRYPOINT 怎么选

| 场景 | 写法 | 结果 |
|---|---|---|
| 只想给默认命令，允许运行时替换 | `CMD ["nginx","-g","daemon off;"]` | `docker run 镜像 bash` 会变成跑 bash |
| 固定入口，参数可追加 | `ENTRYPOINT ["/app/server"]` | `docker run 镜像 --port=9000` 追加参数 |
| 固定入口 + 默认参数 | `ENTRYPOINT ["/app/server"]` + `CMD ["--port=8080"]` | 运行时不传参用 CMD，传参覆盖 CMD |

> **信号坑**：`CMD ["/app/server"]` 是 exec 形式，PID 1 就是 server，能收到 `SIGTERM`；写成 `CMD /app/server` 会套一层 `/bin/sh -c`，信号可能传不到，容器停得慢甚至被 `SIGKILL`。

## 四、多阶段构建：把编译环境和运行环境分开

```dockerfile
# 阶段 1：编译
FROM golang:1.24 AS builder
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o /out/app ./cmd/app

# 阶段 2：运行（体积小、攻击面小）
FROM alpine:3.20
RUN apk add --no-cache ca-certificates tzdata
WORKDIR /app
COPY --from=builder /out/app /app/app
USER 65532:65532
EXPOSE 8080
ENTRYPOINT ["/app/app"]
```

多阶段的收益：最终镜像只保留运行需要的文件，编译工具链、源码、缓存都不进产物。

## 五、层缓存与构建速度

Docker 按指令逐层缓存，**任何一层变了，它后面的层全部失效**。常用顺序：

```dockerfile
COPY go.mod go.sum ./        # 依赖清单先拷贝
RUN go mod download          # 依赖不变就命中缓存
COPY . .                     # 源码后拷贝
RUN go build -o /out/app ./cmd/app
```

规则：

1. 变化少的放前面，变化多的放后面。
2. 一条 `RUN` 里合并 `apt update && install && rm -rf /var/lib/apt/lists/*`，清理必须在同一层。
3. `.dockerignore` 排除 `.git`、`node_modules`、`dist`、密钥、日志，减少上下文传输。
4. 需要强制重建时用 `docker build --no-cache`，不要日常滥用。

## 六、BuildKit 的密钥与挂载

不要把密钥写进 `ENV` 或 `RUN` 参数，会留在层历史里。BuildKit 支持构建期挂载：

```dockerfile
# syntax=docker/dockerfile:1

RUN --mount=type=secret,id=npmrc \
    NPM_CONFIG_USERCONFIG=/run/secrets/npmrc \
    npm ci
```

```bash
docker build --secret id=npmrc,src=$HOME/.npmrc -t app:1.0 .
```

同理可用 `--mount=type=ssh` 拉私有仓库、`--mount=type=cache` 缓存包管理器目录。

## 七、常见报错与易错点

| 现象 | 原因 | 处理 |
|---|---|---|
| `COPY failed: no such file or directory` | 路径相对构建上下文，不是 Dockerfile 位置 | 确认 `docker build` 末尾的上下文路径，或调整 `COPY` 源路径 |
| `exec format error` | 镜像架构和宿主机不一致 | 用 `docker buildx build --platform linux/amd64` 构建 |
| `Permission denied` | `USER` 非 root 但文件属主不对 | `COPY --chown=user:group`，或调整目录权限 |
| 容器启动后立刻退出 | `CMD` 是后台进程或写错路径 | 看 `docker logs`；前台运行；确认可执行文件存在 |
| 镜像越来越大 | 每层都留了缓存/临时文件 | 合并 `RUN` 并在同一层清理；用多阶段 |
| 改了代码但构建没变化 | 缓存命中或 `.dockerignore` 排除了文件 | `--no-cache` 验证；检查 `.dockerignore` |
| 密钥出现在 `docker history` | 写进了 `ENV/RUN` | 改用 `--mount=type=secret`，并重建镜像 |

## 八、官方文档与相关

- Dockerfile 参考：https://docs.docker.com/reference/dockerfile/
- 构建最佳实践：https://docs.docker.com/build/building/best-practices/
- BuildKit 与 buildx：https://docs.docker.com/build/
- `.dockerignore`：https://docs.docker.com/build/building/context/#dockerignore-files
- 速查页：[Docker 命令速查](../docker-commands#dockerfile-与镜像构建)
- 构建命令详解：[docker build](./build)
- Compose 文件与子命令：[docker compose](./compose)
