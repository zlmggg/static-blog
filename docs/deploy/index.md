---
title: "部署方案"
description: "部署形态矩阵 + 跨服务组合方案。单服务部署不重复写，链接到服务页部署段；组合方案再往下是我的项目全栈落地。"
---

# 部署方案

> 定位：**找组合方案、按形态快速跳转**。单服务部署不重复写——矩阵每个格子链接到对应服务页的"02 · 部署方案"段；跨服务组合方案才在这里独立成篇。

## 三层递进

**单服务部署（服务页）→ 组合方案（本模块）→ 全栈落地（[我的项目](/projects/)）**。

## 部署形态矩阵

| 服务 | 单机 | 主从/哨兵 | 集群 | 容器化 | K8s |
|---|---|---|---|---|---|
| Nginx | [●](/services/web/nginx/02-部署) | — | — | [●](/services/web/nginx/02-部署) | — |
| MySQL / MariaDB | [●](/services/database/mysql/02-部署) | [●](/services/database/mysql/02-部署) | — | [●](/services/database/mysql/02-部署) | — |
| Redis | [●](/services/database/redis/02-部署) | [●](/services/database/redis/02-部署) | — | [●](/services/database/redis/02-部署) | — |
| Docker | [●](/services/container/docker/02-部署) | — | — | [●](/services/container/docker/02-部署) | — |
| Kubernetes | — | — | [●](/services/container/kubernetes/02-部署) | — | [●](/services/container/kubernetes/02-部署) |
| Elasticsearch | [●](/services/storage-search/elasticsearch/02-部署) | — | [●](/services/storage-search/elasticsearch/02-部署) | [●](/services/storage-search/elasticsearch/02-部署) | — |
| Jenkins | [●](/services/cicd/jenkins/02-部署) | — | — | [●](/services/cicd/jenkins/02-部署) | — |
| Prometheus | [●](/services/observability/prometheus/02-部署) | — | — | [●](/services/observability/prometheus/02-部署) | — |

● = 链接到服务页部署段；— = 该形态未覆盖。

## 跨服务组合方案

::: idx

| 方案 | 组成 | 入口 |
|---|---|---|
| 接入层高可用 | LVS + Keepalived + Nginx | [进入](/deploy/stacks/lb-ha) |
| MySQL 主从 + 读写分离 | 主从复制 + 代理分流 | [进入](/deploy/stacks/mysql-ha) |
| Redis 哨兵集群 | 三节点哨兵自动故障转移 | [进入](/deploy/stacks/redis-sentinel) |
| CI/CD 流水线 | GitLab + Jenkins + Harbor | [进入](/deploy/stacks/cicd-pipeline) |
| 监控告警栈 | Prometheus + Grafana + Alertmanager | [进入](/deploy/stacks/monitor-stack) |
| 日志链路 | Filebeat + Logstash + ES + Kibana | [进入](/deploy/stacks/log-stack) |

:::


::: tip 组合方案再往下
就是完整落地：[我的项目 · 项目架构](/projects/homelab) + [10-实操](/projects/homelab/practice/)。
:::
