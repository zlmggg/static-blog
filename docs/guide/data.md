# 数据与中间件

> 本页聚合 **数据库与常用中间件**的部署、优化、备份和高可用：MySQL、Redis、Kafka、Spring Cloud 全家桶、APISIX / MinIO。

## 文章索引

### 关系型数据库

| 文章 | 解决什么问题 | 状态 |
|---|---|---|
| [MySQL 基础](./data-mysql) | 安装、SQL 基础、用户权限、存储引擎、数据类型 | ✅️ 已完成 |
| [MySQL 进阶与高可用](./data-mysql-advanced) | 索引/EXPLAIN、慢查询、备份恢复、主从复制、MHA/MGR、MyCat、运维排查 | ✅️ 已完成 |

### 缓存与消息队列

| 文章 | 解决什么问题 | 状态 |
|---|---|---|
| [Redis](./data-redis) | 数据类型、持久化、主从 / 哨兵 / Cluster | ✅️ 已完成 |
| [Kafka](./data-kafka) | 架构、部署、主题 / 分区 / 消费者组 | ✅️ 已完成 |

### 微服务与网关

| 文章 | 解决什么问题 | 状态 |
|---|---|---|
| [Spring Cloud 全家桶](./data-spring-cloud) | Nacos（含集群）、Sentinel、Seata、Gateway | ✅️ 已完成 |
| [APISIX 与 MinIO](./data-apisix-minio) | APISIX 路由/插件、MinIO 对象存储 | ✅️ 已完成 |

## 高可用 / 主从复制要点

> 详细方案见对应文章，这里做速查提示：

- **MySQL**：主从复制 / 半同步、MHA、MGR、MyCat 读写分离
- **Redis**：主从、哨兵、Cluster
- **Nacos**：集群（Raft 协议）
- **通用**：脑裂的预防（仲裁节点、双心跳线）

## 命令速查

- 数据库/服务运维命令：[Linux 命令速查](/reference/linux-commands)
