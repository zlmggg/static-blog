---
title: "Harbor · 企业私有镜像仓库"
description: "Harbor 是什么与组件架构、离线安装包/Helm 部署、镜像推拉完整流程、HTTP insecure 配置、proxy cache 代理缓存、GC 与漏洞扫描运维。单页四段。"
---

# Harbor · 企业私有镜像仓库

> 单页四段：理论 → 部署 → 功能 → 实战。返回 [服务详解 · 容器与编排](/services/container/)。Docker 镜像基础见 [Docker](/services/container/docker/01-理论)。

## 01 · 服务理论

Docker Hub 国内访问不稳，公司也不可能把镜像传公网。**Harbor 是企业自建的私有镜像仓库**：带 Web 界面、项目权限、镜像漏洞扫描、跨集群复制、LDAP 集成。

它本质是在开源 OCI Distribution（registry）外面套了一层管理壳，主要组件：

| 组件 | 职责 |
|---|---|
| core（portal + api） | Web 和 API 入口 |
| registry | 真正存镜像的 OCI 仓库 |
| jobservice | 复制、GC 等异步任务 |
| database（PostgreSQL） | 项目、用户、权限元数据 |
| redis | 缓存 |
| trivy | 镜像漏洞扫描 |

理解组件就知道：Harbor 不是单一进程，而是一组服务（所以官方用 Compose/Helm 部署）。当前稳定版 v2.15.x（以 GitHub releases 为准）。

## 02 · 部署方案

### 离线安装包（内网推荐）

自带所有镜像 tar，适合内网：

```bash
# 从 github.com/goharbor/harbor/releases 下载 harbor-offline-installer-v2.15.x.tgz
tar xzf harbor-offline-installer-v2.15.x.tgz
cd harbor
cp harbor.yml.tmpl harbor.yml
# 编辑 harbor.yml：hostname、http 端口、admin 初始密码、数据盘位置
./install.sh
```

前置依赖：本机要有 Docker 和 docker compose。

### K8s 上用 Helm

```bash
helm repo add harbor https://helm.goharbor.io
helm install harbor harbor/harbor -n harbor --create-namespace
```

::: tip 数据盘
数据目录默认 `/data/registry`，一定要挂大盘——镜像很占空间。
:::

## 03 · 功能详解

### 完整推拉流程

```bash
# 1. Web 登录 → 新建项目（如 library，公开或私有）
# 2. 本机登录
docker login harbor.internal.local:80 -u admin
# 3. 打标签（前缀必须是 Harbor 地址/项目）
docker tag nginx:1.27 harbor.internal.local:80/library/nginx:1.27
# 4. 推送
docker push harbor.internal.local:80/library/nginx:1.27
# 5. 别的机器拉取
docker login harbor.internal.local:80
docker pull harbor.internal.local:80/library/nginx:1.27
```

### HTTP 非 HTTPS 仓库

Harbor 走纯 HTTP 内网地址时，Docker 客户端默认拒绝。在每个客户端 `/etc/docker/daemon.json` 加：

```json
{ "insecure-registries": ["harbor.internal.local:80"] }
```

然后 `sudo systemctl restart docker`。生产建议上 HTTPS（harbor.yml 配证书），insecure 只用于纯内网测试。

## 04 · 实战参考

### proxy cache 代理缓存（生产推荐）

Harbor 自带**代理缓存项目**：把 docker.io / gcr.io / quay.io 缓存到内网，全公司共享。这是 [Docker 04 · 镜像加速](/services/container/docker/04-实战) 里"生产可用"的首选方案——比公共加速器稳定可控，拉过一次就缓存在内网。

### 日常运维要点

- **定期 GC**：Web 上跑"垃圾回收"，清理被删除但还占盘的镜像层。
- **漏洞扫描**：开启 Trivy，可配置 block 高危镜像。
- **机器人账号**：项目按团队划分，CI/CD 用 robot account，别把 admin 密码到处塞。
- **跨集群复制**：多机房用 replication 策略同步镜像。

完整 CI/CD 链路里 Harbor 承接"构建好的镜像"，见 [部署方案](/deploy/) 与 [我的项目 · 项目架构](/projects/homelab)。

## 官方文档

- Harbor 文档：<https://goharbor.io/docs/>
- 安装：<https://goharbor.io/docs/latest/install-config/>
- 代理缓存：<https://goharbor.io/docs/latest/working-with-projects/project-configuration/configure-proxy-cache/>

---

返回 [服务详解 · 容器与编排](/services/container/)。