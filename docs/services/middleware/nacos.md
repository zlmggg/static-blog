---
title: "Nacos · 注册与配置中心"
description: "微服务为什么需要注册/配置中心、Nacos 服务注册发现与健康检查、配置管理与动态刷新、命名空间/分组/DataId 模型、AP/CP 与 Raft 集群部署。单页四段。"
---

# Nacos · 注册与配置中心

> 单页四段：理论 → 部署 → 功能 → 实战。返回 [服务详解 · 中间件](/services/middleware/)。

## 01 · 服务理论

微服务拆成几十上百个服务后，两个问题：**调用谁**（服务实例 IP 动态变化，不能写死）和**配置怎么管**（每个服务一堆配置，改一处要重启一片）。

- **注册中心**：服务启动时把自己的地址注册上去，调用方从注册中心查可用实例——解决"我知道调用谁"。
- **配置中心**：配置集中存放，改了动态推给服务，不用重启——解决"配置统一管理"。

Nacos 把这两件事合一（Naming + Configuration），是 Spring Cloud Alibaba 的核心。对比 K8s 的 [Service/CoreDNS](/services/container/kubernetes/01-理论)：K8s 在平台层做服务发现，Nacos 在应用层做，还多了配置中心能力。

### AP 还是 CP

Nacos 支持两种一致性：临时实例用 **Distro（AP）**保可用（注册中心宁可返回旧地址也不能不可用），持久实例/配置用 **Raft（CP）**保一致。注册中心场景通常 AP 更合适。

## 02 · 部署方案

### 单机（开发）

```bash
# 下载解压，单机模式启动
sh bin/startup.sh -m standalone
```

默认 8848 端口，控制台 `http://10.0.0.40:8848/nacos`（默认 nacos/nacos，**生产必改**）。

### 集群（生产）

集群用外部 MySQL 存配置（各节点共享），`conf/application.properties` 配 `spring.datasource.platform=mysql` + 数据库连接，`conf/cluster.conf` 列各节点 IP:8848，逐节点 `sh bin/startup.sh`。前面挂 [Nginx](/services/web/nginx/01-理论)/VIP 做入口。Raft 保证配置一致，节点数建议 3+。

## 03 · 功能详解

### 配置模型三层

- **Namespace**：环境隔离（dev/test/prod）。
- **Group**：业务分组（默认 DEFAULT_GROUP）。
- **DataId**：具体配置集，通常 `服务名-环境.yaml`。

定位一条配置 = Namespace + Group + DataId。

### 服务注册与发现

服务引入 nacos-discovery 依赖，配 `spring.cloud.nacos.discovery.server-addr`，启动自动注册。调用方用 DiscoveryClient 或 OpenFeign 按服务名拿实例列表。Nacos 靠心跳做健康检查，临时实例失联自动摘除。

### 配置动态刷新

引入 nacos-config，配 `spring.cloud.nacos.config.server-addr` + DataId，`@RefreshScope` 标注的 Bean 在配置变更时自动刷新，不用重启。

## 04 · 实战参考

**典型用法**：dev/test/prod 用 Namespace 隔离，公共配置放共享 DataId（`shared-configs`），服务私有配置放各自 DataId。改配置在控制台发布，服务秒级生效。

**常见坑**：

| 现象 | 原因 | 解法 |
|---|---|---|
| 服务注册不上 | server-addr 错/网络不通 | 核对地址、curl 8848 |
| 配置不刷新 | 没加 @RefreshScope | 标注 Bean |
| 集群配置不一致 | 没用共享 MySQL | 集群配外部数据库 |
| 实例频繁上下线 | 心跳超时/网络抖 | 调心跳间隔、查网络 |

## 官方文档

- Nacos：<https://nacos.io/docs/latest/what-is-nacos/>
- 集群部署：<https://nacos.io/docs/latest/guide/admin/cluster-mode-quick-start/>
- Spring Cloud Alibaba：<https://sca.aliyun.com/>

---

返回 [服务详解 · 中间件](/services/middleware/)。