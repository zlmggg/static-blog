---
title: "服务详解 · 容器与编排"
description: "镜像、容器、编排与私有仓库。"
---

# 容器与编排

> 服务详解分组 · 返回 [服务全景](/services/)
> 镜像、容器、编排与私有仓库。

## 组内选型导读

云原生底座。Docker 管镜像与容器，Compose 管多容器，K8s 管编排调度，Helm 管 K8s 包，Harbor 管私有镜像。kubectl/docker 专属命令在各自"功能详解"段。

## 本组服务

::: idx

| 服务 | 篇幅 | 入口 |
|---|---|---|
| Docker | 四篇 | [进入](/services/container/docker/01-理论) |
| Docker Compose | 单页 | [进入](/services/container/compose) |
| Kubernetes | 四篇 | [进入](/services/container/kubernetes/01-理论) |
| Helm | 单页 | [进入](/services/container/helm) |
| Harbor | 单页 | [进入](/services/container/harbor) |

:::


## 统一四段模板

每个服务同一套顺序：**01 服务理论**（是什么/核心概念/架构/选型）→ **02 部署方案**（单机→主从→集群/容器化，环境→步骤→验证）→ **03 功能详解**（日常使用 + 专属命令中文详解 + 配置参数）→ **04 实战参考**（企业场景/FAQ/官方文档）。

::: tip 粒度规则
大服务（标"四篇"）一个目录四篇；小服务（标"单页"）一页四段。单服务部署写在服务页内，[部署方案](/deploy/) 只做索引与跨服务组合，不重复。
:::
