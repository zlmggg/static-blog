---
title: "Kafka · 高吞吐消息与流平台"
description: "消息队列解耦/异步/削峰、Kafka 高吞吐三原理（顺序写/页缓存/零拷贝）、topic/partition/副本/ISR/消费组/offset、KRaft 部署、消费堆积 lag 与 rebalance、消息不丢不重顺序。单页四段。"
---

# Kafka · 高吞吐消息与流平台

> 单页四段：理论 → 部署 → 功能 → 实战。返回 [服务详解 · 中间件](/services/middleware/)。日志管道常配 [ELK](/services/observability/elk)。

## 01 · 服务理论

消息队列解决三件事：**解耦**（生产消费互不依赖）、**异步**（非核心流程丢队列慢慢处理）、**削峰**（洪峰先堆队列，消费端按能力拉）。

Kafka 是分布式高吞吐、可持久化、可回放的消息与流平台，常用于日志收集、数据管道、事件驱动。和 RabbitMQ 的分工：Kafka 吞吐极高、分区并行、可回放，适合日志/大数据；RabbitMQ 路由灵活、确认完善、延迟低，适合业务消息复杂路由。

### 为什么吞吐高（三个原理）

- **顺序写磁盘**：消息追加写日志文件，顺序 IO 比随机 IO 快几个数量级。
- **页缓存**：写先入 OS page cache，读也常命中缓存，避免频繁磁盘 IO。
- **零拷贝**：消费时用 sendfile 把数据从页缓存直接送网卡，跳过用户态拷贝。

### 核心概念

| 概念 | 含义 |
|---|---|
| Broker | 一个 Kafka 节点 |
| Topic | 消息类别 |
| Partition | topic 的分区，并行与扩展单位，每分区有序 |
| Replica / ISR | 分区副本；ISR 是跟得上领导的同步副本集合 |
| Consumer Group | 消费组，组内每分区只被一个消费者消费 |
| Offset | 消费位移，记录消费到哪 |

**分区是并行关键**：topic 分多区，消费组内消费者分摊分区，加消费者（不超过分区数）就能提吞吐。

## 02 · 部署方案

Kafka 3.3 起 **KRaft** 生产可用、3.5 弃用 ZooKeeper——元数据 quorum 内置，组件更少。

```bash
# 下载解压后，KRaft 模式初始化
KAFKA_CLUSTER_ID=$(bin/kafka-storage.sh random-uuid)
bin/kafka-storage.sh format -t $KAFKA_CLUSTER_ID -c config/kraft/server.properties
bin/kafka-server-start.sh config/kraft/server.properties
```

`server.properties` 关键：`process.roles=broker,controller`、`node.id`、`controller.quorum.voters`（集群各节点）、`listeners`、`log.dirs`（数据盘）。集群各节点 node.id 唯一、quorum.voters 一致。

## 03 · 功能详解

```bash
# topic 管理
bin/kafka-topics.sh --create --topic logs --partitions 3 --replication-factor 2 --bootstrap-server 10.0.0.31:9092
bin/kafka-topics.sh --list --bootstrap-server 10.0.0.31:9092
# 生产消费
bin/kafka-console-producer.sh --topic logs --bootstrap-server 10.0.0.31:9092
bin/kafka-console-consumer.sh --topic logs --from-beginning --bootstrap-server 10.0.0.31:9092
# 消费组 lag
bin/kafka-consumer-groups.sh --describe --group mygroup --bootstrap-server 10.0.0.31:9092
```

`--describe` 看每个分区的 CURRENT-OFFSET / LOG-END-OFFSET / **LAG**（堆积量），lag 持续涨说明消费跟不上。

## 04 · 实战参考

### 消息不丢不重顺序

- **不丢**：生产端 `acks=all`（ISR 全确认）+ 重试；broker `replication-factor>=2`、`min.insync.replicas>=2`；消费端手动提交 offset（处理完再提交）。
- **不重**：acks=all + 幂等生产者（`enable.idempotence=true`）防网络重试重复；跨分区/会话用 Kafka 事务。
- **顺序**：单分区内有序；要全局顺序只能单分区（牺牲并行），或按业务 key 哈希到固定分区保局部顺序。

### 消费堆积与 rebalance

| 现象 | 原因 | 解法 |
|---|---|---|
| lag 持续涨 | 消费慢/消费者少 | 加消费者（≤分区数）、优化处理 |
| 频繁 rebalance | 消费者超时/会话不稳 | 调 max.poll.interval.ms、减单次拉取量 |
| 消息丢失 | acks=1/异步提交 | acks=all + 手动提交 |
| 重复消费 | 提交前崩溃 | 幂等生产 + 业务去重 |

rebalance 是消费组内分区重新分配，期间短暂停消费，频繁 rebalance 会拖垮吞吐。

## 官方文档

- Kafka：<https://kafka.apache.org/documentation/>
- KRaft：<https://kafka.apache.org/documentation/#kraft>
- 消费者配置：<https://kafka.apache.org/documentation/#consumerconfigs>

---

返回 [服务详解 · 中间件](/services/middleware/)。