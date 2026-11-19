---
title: "服务详解"
description: "按企业场景分 7 组 22 服务，统一四段模板：理论→部署→功能→实战。单服务部署就在服务页内。"
---

# 服务详解

> 定位：**学一个服务从原理到实战**。按企业服务器场景分组，每个服务同一套四段模板；单服务的部署方案就在服务页内，[部署方案](/deploy/) 模块只做索引与跨服务组合，不重复。

## 七组全景

| 分组 | 覆盖 | 入口 |
|---|---|---|
| 接入与网络 | Nginx · LVS · HAProxy · DNS（Bind） | [进入](/services/web/) |
| 数据库与缓存 | MySQL · Redis | [进入](/services/database/) |
| 中间件 | Nacos · Kafka · RabbitMQ | [进入](/services/middleware/) |
| 容器与编排 | Docker · Docker · Kubernetes · Helm · Harbor | [进入](/services/container/) |
| 存储与搜索 | MinIO · Elasticsearch | [进入](/services/storage-search/) |
| CI/CD 与自动化 | GitLab · Jenkins · Ansible | [进入](/services/cicd/) |
| 监控与日志 | Prometheus · Grafana · Alertmanager · ELK | [进入](/services/observability/) |

## 统一四段模板

**01 服务理论** → **02 部署方案** → **03 功能详解** → **04 实战参考**。大服务拆四篇，小服务单页四段，侧边栏顺序全站一致。

## 内容边界

- 服务专属命令（docker/kubectl/mysql/redis-cli）归本模块"功能详解"，不在 [命令手册](/commands/)。
- 单服务部署归本模块"部署方案"段；跨服务组合归 [部署方案](/deploy/)。
- FAQ 归"实战参考"，与 [故障与排障](/cases/) 互链。
