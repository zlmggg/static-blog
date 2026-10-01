---
category: 架构
difficulty: 高级
date: 2022-07-09
---

# 集群脑裂（Split-Brain）通用排查（2022-07-09）

## 现象

一套基于 ZooKeeper 选主的服务集群，在一次机房核心交换机抖动后，出现了**两个自认为是 leader 的节点**同时对外提供服务，业务侧出现数据错乱、重复消费。

```text
# 两个节点都宣称自己是 leader
node-A: I am the LEADER (I won the ZK election)
node-B: I am the LEADER (I won the ZK election)
# 业务日志
duplicate delivery to queue: msg_id=88213  (A 和 B 都在投递)
```

类似问题也出现在 Redis Sentinel（双主）、etcd（双 master）等靠 quorum 选主的系统。

## 环境

| 组件 | 版本 / 配置 |
|---|---|
| 操作系统 | CentOS 7.9 |
| 协调服务 | ZooKeeper 3.7.1（3 节点） |
| 业务服务 | 自研任务调度集群，3 节点，靠 ZK 临时节点选主 |
| 触发事件 | 核心交换机抖动，节点间网络分区 ~40s |

## 定位过程

### 1. 确认是不是真脑裂

先看每个节点自报的角色：

```bash
# 业务节点本地状态
curl -s http://node-A:8080/role
# => leader
curl -s http://node-B:8080/role
# => leader    -- 两个 leader！
curl -s http://node-C:8080/role
# => follower
```

### 2. 看 ZooKeeper 视角下谁是真正的 leader

```bash
# 连接 ZK 看选主临时节点
echo "ls /election" | zkCli.sh -node zk1
# 看 /election 下谁是抢到临时节点的那个

# 看每个 ZK 节点自己的角色
echo "stat" | nc zk1 2181 | grep Mode
echo "stat" | nc zk2 2181 | grep Mode
echo "stat" | nc zk3 2181 | grep Mode
```

关键：ZK 本身在网络分区下，**只有 quorum（3 台里 2 台）那一侧**能继续对外服务、产生新 leader。

### 3. 复盘分区时发生了什么

```bash
# 看 ZK 与业务节点的日志时间线
grep -E "LEADING|FOLLOWING|Session expired|ConnectionLoss" /var/log/zookeeper/*.out
```

时间线：

| 时间 | 事件 |
|---|---|
| T+0 | 交换机抖动，node-A 所在网段与 ZK 多数派（zk2/zk3）失联 |
| T+0 | node-B/C 与 ZK 多数派还通，ZK 认为原 leader 掉线 |
| T+15s | ZK 在多数派一侧选出 node-B 为新 leader |
| T+15~40s | **node-A 与 ZK 断连，但它自己进程还活着**，内存里仍认为自己是 leader，继续对外发任务 |
| T+40s | 网络恢复，node-A 的 ZK 会话过期，才意识到自己被废了 |

根因：node-A 与 ZK 断开后，**没有主动"自杀"或拒绝服务"**，导致在它还以为自己是 leader 的 25 秒里，和 node-B 双主并存。

## 根因

| 层级 | 说明 |
|---|---|
| 直接原因 | 网络分区导致 ZK 选主切换，但旧 leader 节点在与 ZK 断连期间没有自我隔离，继续对外服务 |
| 协议原因 | 应用只在"连上 ZK"时选主，缺少"**与 ZK 断连就立刻放弃 leader 身份**"的 fencing 机制 |
| 通用规律 | 脑裂 = 网络分区 + 旧主不及时卸任；quorum 只能保证"多数派一侧有唯一 leader"，管不到少数派那侧的旧主 |

## 解决步骤

### 止血

1. 立刻人工摘除旧主 node-A 的流量（防火墙/负载均衡摘掉），只留 node-B 服务：

```bash
# 在 LB/防火墙把 node-A 从后端列表摘除
iptables -A INPUT -p tcp --dport 8080 -s 0.0.0.0/0 -j DROP   # 粗暴隔离
```

2. 让 node-A 进程退出 leader 状态，重启重新加入集群。

### 根治

1. ** fencing（隔离）机制**：应用监听 ZK 会话状态，一旦 `SessionExpired` / `ConnectionLoss`，立刻放弃 leader 身份、拒绝一切写请求：

```text
# 伪代码：ZK 连接状态监听
onStateChanged(KeeperState state):
    if state == Expired or state == Disconnected:
        becomeFollower()       # 立刻降级
        stopAllWrites()         # 拒绝写
        # 可选：自杀 exit(1) 让 systemd 重启重新选主
```

2. **资源层 fencing（更硬核）**：leader 对外操作时带一个 epoch/ fencing token，下游（如数据库、分布式锁）只接受 epoch 最大的写：

```text
新 leader 的 epoch=2 > 旧 leader 的 epoch=1
旧 leader 哪怕还活着，写请求因为 epoch 过期被下游拒绝
```

3. 正确配置 quorum：奇数节点（3/5），跨故障域部署，保证分区时多数派存活。

4. 业务侧做好**幂等**：即使短暂双主重复投递，下游也要能去重，不产生脏数据。

## 验证与预防

```bash
# 故障注入演练：iptables 隔离 leader 与 ZK，观察旧主是否自动卸任
# 三个节点 /role 应在任何时刻只有一个 leader
```

- 监控：双 leader 检测（定时巡检各节点 role）；ZK 会话过期事件告警。
- 规范：所有靠 quorum 选主的服务必须实现 fencing + 断连即降级。
- 演练：定期做网络分区故障演练，验证脑裂防护有效。

## 相关

- 命令速查：[网络命令速查](/reference/network-commands) ｜ [Linux 命令速查](/reference/linux-commands)
- 同组短文：[Redis 哨兵故障切换](/cases/t-redis-sentinel-failover) ｜ [Kafka 消费积压](/cases/t-kafka-consumer-lag)
