---
category: 数据
difficulty: 中级
date: 2024-05-28
---

# Kafka 消费积压 / Consumer Lag（2024-05-28）

## 现象

订单数据管道监控告警：某消费组 `order-consumer-group` 的消费延迟（consumer lag）从平时的几百条一路涨到 200 万条，且持续上涨不回落。下游风控、数仓都拿不到实时数据。

```text
# 监控面板
consumer-group: order-consumer-group
current-lag: 2,341,880
lag-rate: +8000/s     -- 每秒还在积压
```

## 环境

| 组件 | 版本 / 配置 |
|---|---|
| 操作系统 | Ubuntu 22.04 |
| Kafka | 3.6.1（3 broker，KRaft 模式，无 ZooKeeper） |
| Topic | `order-events`，12 分区，副本因子 3 |
| 消费组 | `order-consumer-group`，原本 6 个消费实例 |
| 生产者峰值 | 约 5 万条/s |

## 定位过程

### 1. 看消费组总体 lag 分布

```bash
kafka-consumer-groups.sh --bootstrap-server k1:9092 \
  --describe --group order-consumer-group
```

输出：

```text
TOPIC          PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG        CONSUMER-ID
order-events   0          10023300        10024100        800        consumer-1-...
order-events   1          10023100        10025800        2700       consumer-1-...
order-events   2          9900000         10100000        200000     <-- 大量积压
order-events   3          9900500         10100300        199500     <--
...
```

关键发现：

- lag 集中在**部分分区**（分区 2、3、7、9），其他分区消费正常。
- 说明不是整体消费能力不足，而是**个别分区分配不到消费者 / 个别分区处理慢**。

### 2. 看消费者实例数与分区分配

```bash
# 消费组当前成员数
kafka-consumer-groups.sh --bootstrap-server k1:9092 \
  --describe --group order-consumer-group --members --verbose
```

发现：消费组里**只剩 4 个活着的实例**（原本 6 个），有 2 个实例挂了但没被及时踢出。

更关键：**分区数 12，但活跃消费者只有 4 个**——每个消费者扛 3 个分区。正常。问题不在并行度。

### 3. 看消费者日志找卡在哪

```bash
# 进消费实例看日志
kubectl logs deploy/order-consumer --tail=200 | grep -iE "error|rebalance|exception"
```

发现两类日志：

```text
[ERROR] CommitFailedException: Commit cannot be completed since the group has already
        rebalanced and assigned the partitions to another member
[WARN] Member consumer-5-... sending LeaveGroup request due to an unexpected error
```

消费组在**频繁重平衡（rebalance）**：某个消费实例处理太慢触发 `max.poll.interval.ms` 超时，被踢出组，触发全组 rebalance，期间所有分区暂停消费——积压越堆越多。

### 4. 核对消费参数

| 参数 | 当前值 | 问题 |
|---|---|---|
| `max.poll.records` | 500（默认） | 一批拉 500 条，每条处理 50ms，单批要 25s |
| `max.poll.interval.ms` | 300000（默认 5min） | 处理慢时接近超时 |
| 处理逻辑 | 每条消息要调一次风控 HTTP 接口 | 同步调用，单条 RT 高 |
| `session.timeout.ms` | 45000 | 正常 |

根因：消费逻辑里同步调外部 HTTP 接口，单条处理慢，500 条一批拉下来处理时间超过 `max.poll.interval.ms`，被判定"死掉"踢出组，反复 rebalance。

## 根因

| 层级 | 说明 |
|---|---|
| 直接原因 | 消费端同步调用慢外部接口，单批处理超时，反复触发 consumer rebalance，消费组长时间停摆 |
| 放大因素 | lag 上涨后监控告警、人工重启实例又加剧 rebalance |
| 设计因素 | 消费逻辑重、没有异步化/批量下游写入 |

## 解决步骤

### 止血

1. 先扩容消费实例（在分区数允许范围内），临时提升消费能力：

```bash
kubectl scale deploy/order-consumer --replicas=12
# 注意：消费者实例数不要超过分区数（12），超过的会空转
```

2. 如果积压实在追不上，临时新建一个临时 topic + 临时消费组跳过重处理（紧急方案，慎用）。

### 根治

1. **把重处理逻辑异步化**：消费线程只负责拉消息、丢到内存队列/线程池，不要在 `poll` 循环里同步调慢接口：

```text
poll(500条) → 丢到本地有界队列 → 工作线程池异步调风控接口
定期 commit offset（按处理进度）
```

2. 调大 poll 间隔、减少单批拉取量，避免误判死亡：

```properties
max.poll.records=100              # 一次少拉点，快速返回 poll
max.poll.interval.ms=600000      # 放宽到 10min
session.timeout.ms=45000
# 用协作式消费平衡协议（ConsumerRebalanceListener 里异步提交）
partition.assignment.strategy=org.apache.kafka.clients.consumer.CooperativeStickyAssignor
```

> 用 CooperativeStickyAssignor（增量重平衡）代替默认的 RangeAssignor，rebalance 时只迁移受影响分区，不用全组 Stop-The-World。

3. 下游风控接口本身做批量化/性能优化，或用本地缓存减少调用。

## 验证与预防

```bash
kafka-consumer-groups.sh --bootstrap-server k1:9092 \
  --describe --group order-consumer-group
# LAG 应持续下降直到接近 0
```

- 监控：对 consumer-lag 配分级告警（>1万预警、>10万严重）；监控 rebalance 次数。
- 规范：消费逻辑必须轻量，重处理异步化；消费者实例数 ≤ 分区数；上线新消费组先压测。
- 预案：积压应急预案文档化（扩容参数、临时跳数方案）。

## 相关

- 命令速查：[云原生排障命令速查](/reference/cloudnative-commands) ｜ [Linux 命令速查](/reference/linux-commands)
- 同组短文：[集群脑裂](/cases/t-cluster-split-brain) ｜ [Redis 哨兵故障切换](/cases/t-redis-sentinel-failover)
