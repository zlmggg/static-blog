---
title: "Docker Compose · 单机多容器编排"
description: "Compose 是什么、compose.yaml 完整语法（services/volumes/networks）、常用命令、depends_on 不等于就绪的坑、多服务编排实战。单页四段：理论→部署→功能→实战。"
---

# Docker Compose · 单机多容器编排

> 单页四段：理论 → 部署 → 功能 → 实战。返回 [服务详解 · 容器与编排](/services/container/)。Docker 本体见 [Docker](/services/container/docker/01-理论)。

## 01 · 服务理论

一台机器要跑 nginx + 应用 + redis 三个容器，手动 `docker run` 十条命令很烦，还容易漏参数。**Compose 就是把这一坨写进一个 YAML 文件，一条 `docker compose up -d` 全拉起来。**

它解决的是**单机多容器编排**：定义服务、网络、卷的声明式配置，一键启停。注意边界——Compose 管单机，跨主机的集群编排是 [Kubernetes](/services/container/) 的事。

Docker Engine 29 里 Compose 是官方插件，命令是 `docker compose`（带空格），老的独立二进制 `docker-compose` 已基本淘汰。

## 02 · 部署方案

Compose 随 `docker-compose-plugin` 一起装（见 [Docker 02 · 安装](/services/container/docker/02-部署)），无需单独部署：

```bash
sudo dnf install -y docker-compose-plugin   # RHEL
docker compose version                       # 验证
```

项目目录里放一个 `compose.yaml` 即可，无额外服务端。

## 03 · 功能详解

### compose.yaml 完整语法

```yaml
services:
  web:
    image: nginx:1.27
    ports:
      - "8080:80"
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - web_html:/usr/share/nginx/html
    environment:
      - TZ=Asia/Shanghai
    depends_on:
      - app
    networks:
      - frontend
    restart: always

  app:
    build: ./app                # 本地构建
    image: myapp:1.0
    environment:
      - REDIS_HOST=redis        # 直接用服务名当主机名
    networks:
      - frontend
      - backend
    restart: always

  redis:
    image: redis:7.4
    volumes:
      - redis_data:/data
    networks:
      - backend
    restart: always

volumes:
  web_html:
  redis_data:

networks:
  frontend:
  backend:
```

三大顶层块：`services`（各容器）、`volumes`（命名卷）、`networks`（自定义网络）。Compose 自动建一个默认网络，**服务名就是 DNS 名**——app 里用 `REDIS_HOST=redis` 就能连到 redis 容器，这正是 [Docker 自建 bridge 的 DNS](/services/container/docker/03-功能) 能力。

### 常用命令

```bash
docker compose up -d                  # 后台启动全部
docker compose ps                     # 看状态
docker compose logs -f web            # 跟某服务日志
docker compose exec app sh            # 进某服务容器
docker compose down                   # 停并删容器/网络（-v 连卷一起删）
docker compose up -d --scale app=3    # app 扩到 3 实例（此时 ports 不能写死）
docker compose build                  # 重新构建带 build 的服务
```

## 04 · 实战参考

::: warning depends_on 不等于"对方已就绪"
`depends_on` 只控制**启动顺序**，不保证对方端口已经能连上。redis 容器启动了但还没加载完，app 连过去照样失败。应用启动时连数据库要**自己重试**，不能依赖 Compose 的启动顺序。要真正等就绪，用 healthcheck + `depends_on.condition: service_healthy`。
:::

**典型场景**：本站和实验环境用 Compose 一键拉起 nginx + 应用 + 数据库 + 监控。配置纳入版本管理，`down` 再 `up` 就能重建整套环境。多服务组合的完整落地见 [部署方案](/deploy/) 与 [我的项目](/projects/homelab)。

**常见坑**：

| 现象 | 原因 | 解法 |
|---|---|---|
| 扩容后端口冲突 | --scale 多实例共用写死的宿主端口 | 去掉 ports 或只用 expose |
| 服务连不上 | 不在同一 network | 检查 networks 配置 |
| down -v 后数据没了 | -v 把命名卷也删了 | 数据卷别加 -v |

## 官方文档

- Compose 规范：<https://docs.docker.com/compose/compose-file/>
- Compose CLI：<https://docs.docker.com/reference/cli/docker/compose/>

---

返回 [服务详解 · 容器与编排](/services/container/)。