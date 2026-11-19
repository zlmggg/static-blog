---
title: "Docker 命令速查"
description: "Docker 常用命令速查表。深入原理和实战（镜像构建、网络、Compose 项目）见 Docker 实战手册。 用法：右侧「本页目录」跳转，或 Ctrl+K 搜索。"
---
# Docker 命令速查

> Docker 常用命令速查表。深入原理和实战（镜像构建、网络、Compose 项目）见 [Docker 实战手册](/services/container/docker/01-理论)。
> 用法：右侧「本页目录」跳转，或 `Ctrl+K` 搜索。

## 容器生命周期

| 命令 | 说明 |
|---|---|
| [`docker run 镜像`](./cmd-docker/run) | 创建并启动容器 |
| [`docker run -d 镜像`](./cmd-docker/run) | 后台运行（d 守护态） |
| [`docker run --name web -p 80:80 nginx`](./cmd-docker/run) | 指定名称、映射端口 |
| [`docker run -it 镜像 /bin/bash`](./cmd-docker/run) | 交互式进入终端（i 交互、t 终端） |
| [`docker run --rm 镜像`](./cmd-docker/run) | 退出后自动删除容器 |
| `docker ps` | 查看运行中的容器 |
| `docker ps -a` | 查看所有容器（含已停止） |
| `docker start/stop/restart 容器` | 启动 / 停止 / 重启 |
| `docker rm 容器` | 删除容器（需先停止） |
| `docker rm -f $(docker ps -aq)` | 强制删除所有容器 |

## 进入与日志

| 命令 | 说明 |
|---|---|
| `docker exec -it 容器 /bin/bash` | 进入正在运行的容器 |
| [`docker logs 容器`](./cmd-docker/logs) | 查看容器日志 |
| [`docker logs -f --tail 100 容器`](./cmd-docker/logs) | 实时跟踪最后100行 |
| `docker inspect 容器` | 查看容器详细信息（JSON） |
| `docker cp 容器:/路径 ./本地` | 容器与宿主机间复制文件 |
| `docker stats` | 实时查看容器资源占用 |
| `docker top 容器` | 查看容器内进程 |

## 镜像管理

| 命令 | 说明 |
|---|---|
| `docker images` | 列出本地镜像 |
| `docker pull 镜像:标签` | 拉取镜像 |
| `docker push 镜像` | 推送镜像到仓库 |
| [`docker build -t 名称:标签 .`](./cmd-docker/build) | 根据 Dockerfile 构建镜像 |
| `docker rmi 镜像` | 删除镜像 |
| `docker tag 镜像 用户/镜像:标签` | 给镜像打标签 |
| `docker save -o out.tar 镜像` | 镜像导出为文件 |
| `docker load -i out.tar` | 从文件导入镜像 |
| `docker image prune -a` | 清理悬空/无用镜像 |
| `docker login 仓库地址` | 登录镜像仓库（push 前必须） |
| `docker logout` | 退出仓库登录 |

## Dockerfile 与镜像构建

| 命令 / 知识点 | 说明 |
|---|---|
| [Dockerfile 指令速查](./cmd-docker/dockerfile) | `FROM / RUN / COPY / CMD / ENTRYPOINT / HEALTHCHECK` 全表 |
| [`FROM 镜像 AS builder`](./cmd-docker/dockerfile) | 多阶段构建，编译环境与运行环境分离 |
| [`COPY --from=builder`](./cmd-docker/dockerfile) | 只把产物复制进最终镜像 |
| [`RUN --mount=type=secret`](./cmd-docker/dockerfile) | 构建期密钥，不落进层历史 |
| [`.dockerignore`](./cmd-docker/dockerfile) | 排除 `.git`、`node_modules`、密钥，缩小上下文 |
| [`docker buildx build --platform`](./cmd-docker/build) | 跨平台构建 amd64/arm64 |
| [`docker build --build-arg`](./cmd-docker/build) | 传构建期变量 |

## 网络

| 命令 | 说明 |
|---|---|
| `docker network ls` | 列出网络 |
| `docker network create 名称` | 创建网络 |
| `docker network connect 网络 容器` | 容器接入网络 |
| `docker network disconnect 网络 容器` | 断开网络 |
| `docker network inspect 网络` | 查看网络详情 |

**网络模式：** `bridge`（默认）、`host`（共享宿主机网络）、`none`（无网络）、`container`（共享另一容器网络）。

## 存储卷

| 命令 | 说明 |
|---|---|
| `docker volume ls` | 列出数据卷 |
| `docker volume create 名称` | 创建数据卷 |
| `docker volume inspect 名称` | 查看卷详情 |
| `docker volume rm 名称` | 删除卷 |
| `-v 宿主机路径:容器路径` | 挂载（bind mount） |
| `-v 卷名:容器路径` | 挂载数据卷 |

## 系统与清理

| 命令 | 说明 |
|---|---|
| `docker info` | Docker 系统信息 |
| `docker version` | 版本信息 |
| `docker system df` | 磁盘占用情况 |
| `docker system prune -af` | 清理所有无用资源（容器/镜像/网络） |

## Docker Compose

| 命令 | 说明 |
|---|---|
| [`docker compose up -d`](./cmd-docker/compose) | 根据 compose 文件启动所有服务 |
| [`docker compose up -d --build`](./cmd-docker/compose) | 改了代码后重建镜像再启动 |
| [`docker compose down`](./cmd-docker/compose) | 停止并删除容器、网络 |
| [`docker compose config`](./cmd-docker/compose) | 校验并展开最终的 compose 配置 |
| [`docker compose ps`](./cmd-docker/compose) | 查看本项目服务状态 |
| [`docker compose logs -f`](./cmd-docker/compose) | 查看所有服务日志 |
| [`docker compose build`](./cmd-docker/compose) | 构建服务镜像 |
| [`docker compose restart 服务`](./cmd-docker/compose) | 重启某个服务 |
| [`docker compose exec 服务 bash`](./cmd-docker/compose) | 进入某个服务容器 |
| [compose.yaml 核心字段](./cmd-docker/compose) | `services / image / build / ports / volumes / environment / depends_on` |

> `services`、`image`、`build`、`ports`、`volumes`、`environment`、`depends_on` 的写法和坑，见 [docker compose 详解](./cmd-docker/compose)。

<!-- merged-command-pitfalls:start -->
## 命令坑点索引

> 原先逐条拆开的单命令详解已合并到本手册；下面只保留每条命令最容易踩的坑，完整选项和示例不再单独成页。
> 需要看某条命令的完整用法时，先在上方速查表找到它，再看本节对应行。

| 命令 | 最容易踩的坑 | 官方文档 |
|---|---|---|
| `docker cp` | 冒号别写反：docker cp web:/etc ./bak 是"容器→本地"；docker cp ./bak web:/etc 是"本地→容器"。 | — |
| `docker create / start / stop / restart / rm` | docker rm 默认删不了运行中的容器：会报错，要么先 stop，要么 -f 强删。 | — |
| `docker exec` | 容器没在跑就 exec 不进去：exec 要求容器处于 running 状态。 | — |
| `docker images / pull / push / rmi / tag / save / load` | docker images 不显示中间层和 dangling：想看全加 -a；但日常别 -a，不然几百个中间层刷屏。 | — |
| `docker info / version / system df / system prune` | docker system prune -a --volumes 是 Docker 头号危险命令：它会删停止的容器、没用的镜像、没被引用的匿名卷。 | — |
| `docker network` | 默认 bridge 没有 DNS：在默认 bridge 网络里，容器间只能用 IP 互访，用容器名解析不通。 | — |
| `docker ps / inspect / top` | docker ps 默认只看运行中：找不到容器先加 -a，别以为容器没了。 | — |
| `docker stats` | 不加 --no-stream 会一直刷新：以为卡死了，其实是在流式刷，Ctrl+C 退出。 | — |
| `docker volume` | docker rm -v 只删匿名卷，不删命名卷：命名卷要单独 docker volume rm，这是 Docker 故意保护数据。 | — |

<!-- merged-command-pitfalls:end -->

## 相关问答

- 镜像、网络、容器异常排查：[容器与 Kubernetes 问题](/guide/container#常见问题-faq)

## 官方文档

- Docker CLI 参考：https://docs.docker.com/reference/cli/docker/
- Dockerfile 参考：https://docs.docker.com/reference/dockerfile/
- 构建最佳实践：https://docs.docker.com/build/building/best-practices/
- Compose 文件规范：https://docs.docker.com/compose/compose-file/
- Compose CLI：https://docs.docker.com/reference/cli/docker/compose/
