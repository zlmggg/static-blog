---
category: 容器
difficulty: 初级
date: 2024-01-22
---

# Docker 镜像拉取失败（2024-01-22）

## 现象

服务器上拉镜像一直失败，`docker pull` 各种报错：

```text
docker pull nginx:1.25
Error response from daemon: Get "https://registry-1.docker.io/v2/":
  dial tcp 34.194.156.193:443: connect: connection timed out
```

有时是另一种错：

```text
Error response from daemon: pull access denied for xxx, repository does not exist or may require 'docker login': denied: requested access to the resource is denied
```

## 环境

| 组件 | 版本 |
|---|---|
| 操作系统 | Ubuntu 22.04 LTS |
| Docker | 24.0.7 |
| 环境 | 国内机房，无公网直连 Docker Hub 能力 |
| 私有仓库 | harbor.internal（公司内网 Harbor） |

## 定位过程

### 1. 先分清是哪一类"拉取失败"

按报错关键词分类：

| 报错关键词 | 根因方向 |
|---|---|
| `connection timed out` / `timeout` | 网络到 Docker Hub 不通，需配镜像加速 |
| `no such host` / `dns` | DNS 解析失败 |
| `pull access denied` / `docker login` | 认证问题 / 镜像不存在 / tag 写错 |
| `http: server gave HTTP response to HTTPS client` | 私有仓库是 HTTP，Docker 默认走 HTTPS |
| `no space left` | 磁盘满（见 [存储驱动](/cases/t-docker-storage-driver)） |

### 2. 网络类：测试到 registry 的连通性

```bash
# 测能不能通 Docker Hub
curl -I https://registry-1.docker.io/v2/ --max-time 5
# 超时 → 网络不通

# 测 DNS
nslookup registry-1.docker.io

# 测到私有 Harbor
curl -k -I https://harbor.internal/v2/ --max-time 5
```

本次公网到 Docker Hub 直接超时——典型的国内拉 Docker Hub 被墙/慢。

### 3. 认证类：私有仓库没登录

```bash
# 看已登录的仓库
cat ~/.docker/config.json
# 拉私有镜像前先登录
docker login harbor.internal
```

报 `pull access denied` 时，确认：
- 镜像地址拼写对不对（`harbor.internal/project/nginx:1.25`）
- tag 存不存在（Harbor 控制台看 tag 列表）
- 有没有 `docker login` 且账号有该项目权限。

### 4. HTTP 仓库：Docker 拒绝明文 HTTP

老的内网 registry 是 HTTP 时，Docker 默认只许 HTTPS：

```text
http: server gave HTTP response to HTTPS client
```

需要把该仓库加入 insecure-registries 白名单。

## 根因

| 层级 | 说明 |
|---|---|
| 直接原因 | 国内服务器直连 Docker Hub 超时，需要配置镜像加速器 |
| 次要 | 偶发私有仓库未登录 / HTTP 仓库未加白名单 |

## 解决步骤

### 止血

1. 先配镜像加速器（`/etc/docker/daemon.json`）：

```json
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://dockerproxy.net"
  ]
}
```

```bash
sudo systemctl restart docker
docker pull nginx:1.25
```

> 公共加速器时常失效，建议优先用公司自建 Harbor 代理缓存（proxy cache），稳定性最高。

2. 如果是私有 Harbor，先登录再拉：

```bash
docker login harbor.internal
docker pull harbor.internal/base/nginx:1.25
```

### 根治

1. 内网 HTTP 仓库加白名单（如有老 registry）：

```json
{
  "insecure-registries": ["registry.internal:5000"]
}
```

2. 公司内部统一走 **Harbor 作为代理缓存**：把 Docker Hub / GCR / Quay 的镜像都通过 Harbor 代理拉取，业务侧只对内网 Harbor 拉镜像，既快又稳：

```bash
# Harbor 里建一个 proxy 项目代理 dockerhub
docker pull harbor.internal/proxy/library/nginx:1.25
```

3. 把常用基础镜像预先同步到 Harbor，避免每次都走外网。

## 验证与预防

```bash
docker info | grep -A5 "Registry Mirrors"   # 加速器生效
docker pull nginx:1.25                        # 成功
```

- 规范：生产环境禁止直连 Docker Hub，统一走内网 Harbor 代理缓存。
- 排查套路：先看报错关键词归类（超时/认证/HTTP/磁盘），再对症处理。
- 运维：加速器失效时及时更换，监控节点拉镜像成功率。

## 相关

- 命令速查：[Docker 命令速查](/reference/docker-commands) ｜ [网络命令速查](/reference/network-commands)
- 同组短文：[dockerd 启动失败](/cases/t-docker-daemon-fail) ｜ [存储驱动 overlay2](/cases/t-docker-storage-driver) ｜ [容器网络不通](/cases/t-docker-network-bridge)
