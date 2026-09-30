# Docker 命令速查

> Docker 常用命令速查表。深入原理和实战（镜像构建、网络、Compose 项目）见 [Docker 实战手册](/guide/container-docker)。
> 用法：右侧「本页目录」跳转，或 `Ctrl+K` 搜索。

## 容器生命周期

| 命令 | 说明 |
|---|---|
| `docker run 镜像` | 创建并启动容器 |
| `docker run -d 镜像` | 后台运行（d 守护态） |
| `docker run --name web -p 80:80 nginx` | 指定名称、映射端口 |
| `docker run -it 镜像 /bin/bash` | 交互式进入终端（i 交互、t 终端） |
| `docker run --rm 镜像` | 退出后自动删除容器 |
| `docker ps` | 查看运行中的容器 |
| `docker ps -a` | 查看所有容器（含已停止） |
| `docker start/stop/restart 容器` | 启动 / 停止 / 重启 |
| `docker rm 容器` | 删除容器（需先停止） |
| `docker rm -f $(docker ps -aq)` | 强制删除所有容器 |

## 进入与日志

| 命令 | 说明 |
|---|---|
| `docker exec -it 容器 /bin/bash` | 进入正在运行的容器 |
| `docker logs 容器` | 查看容器日志 |
| `docker logs -f --tail 100 容器` | 实时跟踪最后100行 |
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
| `docker build -t 名称:标签 .` | 根据 Dockerfile 构建镜像 |
| `docker rmi 镜像` | 删除镜像 |
| `docker tag 镜像 用户/镜像:标签` | 给镜像打标签 |
| `docker save -o out.tar 镜像` | 镜像导出为文件 |
| `docker load -i out.tar` | 从文件导入镜像 |
| `docker image prune -a` | 清理悬空/无用镜像 |

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
| `docker compose up -d` | 根据 compose 文件启动所有服务 |
| `docker compose down` | 停止并删除容器、网络 |
| `docker compose ps` | 查看本项目服务状态 |
| `docker compose logs -f` | 查看所有服务日志 |
| `docker compose build` | 构建服务镜像 |
| `docker compose restart 服务` | 重启某个服务 |
| `docker compose exec 服务 bash` | 进入某个服务容器 |
