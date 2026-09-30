---
title: Kafka
description: Kafka 高吞吐原理、topic/partition/副本/ISR/消费组/offset、KRaft 部署、topic 管理、生产消费、消费堆积与 lag、消息不丢不重顺序、rebalance 与监控
---

# Kafka

::: tip 本篇定位
理解消息队列**解耦/异步/削峰**和 Kafka **高吞吐原理**，掌握**分区、副本、ISR、消费组、offset**，用 **KRaft** 部署集群，完成 topic 管理、生产消费、消费组运维，并解决**消息丢失/重复/顺序、堆积、rebalance**。
:::

## 先建立全局观：Kafka 为什么吞吐高

| 机制 | 说明 |
|---|---|
| 磁盘顺序写 | 消息追加写（append），顺序写磁盘接近内存速度 |
| 页缓存 Page Cache | 读写依赖 OS 缓存，数据先落缓存 |
| 零拷贝 sendfile | 数据直接从页缓存到网卡，不经过用户态拷贝 |
| 分区并行 | topic 拆分区，多节点多分区并行读写 |
| 批量 + 压缩 | 消息批量发送、按批压缩（snappy/lz4/zstd） |

---

## 一、简介

### 1.1 消息队列的作用

| 作用 | 说明 |
|---|---|
| 解耦 | 生产与消费不直接依赖，独立演进 |
| 异步 | 耗时操作异步处理，快速响应 |
| 削峰填谷 | 突发流量先入队，按消费能力处理，保护下游 |

### 1.2 Kafka 特点与选型

Kafka 是分布式高吞吐、可持久化、可回放的消息与流平台，常用于日志收集、数据管道、大数据、事件驱动、流处理（Kafka Streams）。

| MQ | 特点 | 适合 |
|---|---|---|
| **Kafka** | 吞吐极高、分区并行、可回放、生态 | 日志、大数据、高吞吐管道 |
| RabbitMQ | 路由灵活、确认完善、协议丰富、延迟低 | 业务消息、复杂路由 |
| RocketMQ | 事务/顺序消息、阿里开源 | 电商金融 |
| Pulsar | 存算分离、多租户 | 云原生消息 |

---

## 二、核心概念

| 概念 | 说明 |
|---|---|
| Producer | 生产者，发布消息 |
| Consumer | 消费者，拉取消息 |
| Broker | 一个 Kafka 节点，多节点组成集群 |
| Topic | 消息的逻辑分类 |
| **Partition 分区** | topic 拆成多个分区分布在 broker，是**并行和扩展单位**；消息只在**分区内有序** |
| **Replica 副本** | 每分区一个 **Leader**（读写）、多个 **Follower**（同步、备份） |
| **Consumer Group** | 消费组：一条消息只被组内一个消费者消费；不同组各自消费全量 |
| **Offset** | 消息在分区中的唯一编号；消费位置提交到内部 topic |
| **ISR** | 与 Leader 保持同步的副本集合；故障从 ISR 选新 Leader |
| AR / OSR | 所有副本 / 同步落后的副本；AR = ISR + OSR |
| LEO / HW | 日志末端偏移 / 高水位（HW 之前的消息才对消费者可见） |

> 一个分区在一个消费组内最多被一个消费者消费，消费者数超过分区数会有空闲——**分区数决定消费并行度**。

---

## 三、部署（KRaft 模式）

Kafka 3.3 起 KRaft 生产可用、3.5 弃用 ZooKeeper。KRaft 把元数据 quorum 内置在 Kafka，组件更少。

### 3.1 二进制部署

```bash
# https://kafka.apache.org/downloads 下载 3.9.x（scala 2.13）
tar -xzf kafka_2.13-3.9.0.tgz && cd kafka_2.13-3.9.0

KAFKA_CLUSTER_ID="$(bin/kafka-storage.sh random-uuid)"
bin/kafka-storage.sh format -t "$KAFKA_CLUSTER_ID" -c config/kraft/server.properties
bin/kafka-server-start.sh -daemon config/kraft/server.properties
```

关键配置 `config/kraft/server.properties`：

```properties
process.roles=broker,controller
node.id=1
controller.quorum.voters=1@10.0.0.13:9093,2@10.0.0.14:9093,3@10.0.0.15:9093
listeners=PLAINTEXT://10.0.0.13:9092,CONTROLLER://10.0.0.13:9093
advertised.listeners=PLAINTEXT://10.0.0.13:9092
log.dirs=/data/kafka-logs
num.partitions=3
default.replication.factor=3
min.insync.replicas=2
offsets.topic.replication.factor=3
unclean.leader.election.enable=false
auto.create.topics.enable=false
```

### 3.2 Docker（KRaft）

```bash
docker run -d --name kafka -p 9092:9092 \
  -e KAFKA_NODE_ID=1 \
  -e KAFKA_PROCESS_ROLES=broker,controller \
  -e KAFKA_CONTROLLER_QUORUM_VOTERS=1@localhost:9093 \
  -e KAFKA_LISTENERS=PLAINTEXT://:9092,CONTROLLER://:9093 \
  -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://47.109.132.117:9092 \
  -e KAFKA_CONTROLLER_LISTENER_NAMES=CONTROLLER \
  -e KAFKA_LISTENER_SECURITY_PROTOCOL_MAP=CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT \
  -v /data/kafka:/tmp/kraft-combined-logs \
  apache/kafka:3.9.0
```

> 生产集群至少 3 broker、副本因子 3、controller quorum 配 3 节点。

---

## 四、Topic 管理

```bash
# 创建（分区数、副本因子）
bin/kafka-topics.sh --create --topic test \
  --partitions 3 --replication-factor 3 \
  --bootstrap-server localhost:9092

bin/kafka-topics.sh --list --bootstrap-server localhost:9092

# 详情：Leader、Replicas、ISR
bin/kafka-topics.sh --describe --topic test --bootstrap-server localhost:9092
# PartitionCount、ReplicationFactor、Isr

# 修改（分区只能增加）、删除
bin/kafka-topics.sh --alter --topic test --partitions 6 --bootstrap-server localhost:9092
bin/kafka-topics.sh --delete --topic test --bootstrap-server localhost:9092

# 配置
bin/kafka-configs.sh --entity-type topics --entity-name test \
  --add-config retention.ms=86400000 --bootstrap-server localhost:9092
```

---

## 五、生产与消费

### 5.1 命令行

```bash
# 生产者（开启 key，默认 key/tab/value）
bin/kafka-console-producer.sh --topic test --bootstrap-server localhost:9092 \
  --property parse.key=true --property key.separator=:

# 消费者
bin/kafka-console-consumer.sh --topic test --bootstrap-server localhost:9092 \
  --from-beginning --group g1 \
  --property print.key=true --property key.separator=:
```

### 5.2 客户端关键参数（了解）

- Producer：`acks`（0/1/all）、`retries`、`enable.idempotence`、`compression.type`、`linger.ms`、`batch.size`；
- Consumer：`group.id`、`enable.auto.commit`、`auto.offset.reset`（earliest/latest）、`max.poll.records`；
- key 决定消息进入哪个分区（相同 key 同分区）。

---

## 六、运维

### 6.1 分区与副本

```bash
# 扩分区
bin/kafka-topics.sh --alter --topic test --partitions 6 --bootstrap-server localhost:9092

# 副本重分配：--generate 生成计划 → --execute 执行 → --verify 验证
bin/kafka-reassign-partitions.sh --bootstrap-server localhost:9092 \
  --topics-to-move-json-file topics.json --broker-list "1,2,3" --generate

# 优先副本 Leader 选举（均衡 leader）
bin/kafka-leader-election.sh --bootstrap-server localhost:9092 \
  --election-type preferred --all-topic-partitions
```

### 6.2 消费组与 Lag

```bash
bin/kafka-consumer-groups.sh --list --bootstrap-server localhost:9092
bin/kafka-consumer-groups.sh --describe --group g1 --bootstrap-server localhost:9092
# TOPIC PARTITION CURRENT-OFFSET LOG-END-OFFSET LAG CONSUMER-ID
```

`LAG = LOG-END-OFFSET - CURRENT-OFFSET`，即未消费的积压条数。

```bash
# 重置 offset（组无活跃消费者）
bin/kafka-consumer-groups.sh --group g1 --topic test \
  --reset-offsets --to-earliest --execute --bootstrap-server localhost:9092
# --to-latest / --to-offset n / --to-datetime
```

### 6.3 监控指标

| 指标 | 含义 |
|---|---|
| Consumer Lag | 消费积压（核心告警） |
| UnderReplicatedPartitions | 副本未同步分区（>0 告警） |
| ISR 收缩/扩缩 | 同步异常 |
| ActiveController | 控制器是否唯一 |
| 吞吐 bytes in/out、请求队列、磁盘/CPU | 容量性能 |

---

## 七、可靠性与常见问题

### 7.1 消息不丢失

| 环节 | 措施 |
|---|---|
| 生产端 | `acks=all`、`retries>0`、`enable.idempotence=true` |
| Broker | 副本因子 ≥3、`min.insync.replicas≥2`、`unclean.leader.election.enable=false` |
| 消费端 | 处理完成后**再手动提交** offset |

### 7.2 消息不重复（幂等/精确一次）

- 生产端开启**幂等**（`enable.idempotence=true`，PID+序列号去重）；
- 跨分区/会话用 **Kafka 事务**；
- 消费端做**业务幂等**（唯一键、去重表、状态判断）——offset 提交与处理非原子，重复难完全避免。

### 7.3 消息顺序

- 全局有序用单分区（牺牲并行）；
- 业务有序让相关消息用**相同 key** 路由同分区；
- 单分区单消费者、失败不打乱顺序。

### 7.4 消费堆积

排查消费为何慢（下游 DB/接口、处理逻辑）→ 增加分区 + 消费者（不超分区数）→ 临时扩消费者/批量处理 → 限流保护下游。

### 7.5 频繁 Rebalance

消费者处理过久、心跳超时会被踢出组触发 rebalance。措施：调大 `session.timeout.ms`、`max.poll.interval.ms`，减少单次 poll 处理量，用**静态成员**（group.instance.id）避免重启触发。

---

## 面试自测

1. Kafka 为什么吞吐高？顺序写、页缓存、零拷贝分别解决什么？
2. Partition、Replica、ISR、HW 分别是什么？
3. 为什么消费者数超过分区数会有空闲？
4. KRaft 相比 ZooKeeper 模式有什么优势？
5. 如何保证消息不丢失？min.insync.replicas 和 acks=all 怎么配合？
6. 如何保证消息不重复 / 精确一次？
7. 如何保证消息顺序？
8. 消费堆积怎么排查和处理？什么是 rebalance，如何减少？

## 相关速查

- [Linux 命令速查](/reference/linux-commands)
- Kafka 官方文档：https://kafka.apache.org/documentation/
- KRaft：https://kafka.apache.org/documentation/#kraft
