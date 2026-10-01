---
category: 数据
difficulty: 高级
date: 2023-10-16
---

# Redis 哨兵故障切换异常 / 主从漂移（2023-10-16）

## 现象

Redis 主库所在机房网络抖动后，哨兵本应自动把从库提升为主库，但切换后出现诡异状态：客户端写入报错，且 `INFO replication` 显示旧主库"复活"后又变回了主——**出现两个主库（脑裂）**。

```text
# 应用侧
WRONGPASS / READONLY You can't write against a read only replica

# 哨兵日志
+monitor master mymaster 10.0.7.10 6379
+sdown master mymaster 10.0.7.10
+odown master mymaster 10.0.7.10 #quorum 2/2
+new-master 10.0.7.11
```

## 环境

| 组件 | 版本 / 配置 |
|---|---|
| 操作系统 | Debian 11 |
| Redis | 7.0.12 |
| 架构 | 1 主（10.0.7.10） + 2 从（.11 / .12） + 3 哨兵 |
| `sentinel monitor` | `mymaster 10.0.7.10 6379 2`（quorum=2） |
| 客户端 | Lettuce，按哨兵自动发现主 |

## 定位过程

### 1. 看哨兵视角下的主是谁

```bash
redis-cli -p 26379 SENTINEL masters
redis-cli -p 26379 SENTINEL replicas mymaster
```

### 2. 分别连三个节点看 replication 角色

```bash
for ip in 10.0.7.10 10.0.7.11 10.0.7.12; do
  echo "=== $ip ==="
  redis-cli -h $ip INFO replication | grep -E "role|master_host|master_port"
done
```

输出（异常状态）：

```text
=== 10.0.7.10 ===
role:master              -- 旧主还认为自己是主！
=== 10.0.7.11 ===
role:master              -- 新主也被哨兵提为 master
=== 10.0.7.12 ===
role:slave  master_host=10.0.7.11
```

`.10` 和 `.11` 同时是 master——脑裂了。

### 3. 读哨兵日志找切换过程

```bash
tail -100 /var/log/redis/sentinel.log
```

关键时间线：

| 时间 | 事件 |
|---|---|
| T+0s | 网络抖动，哨兵多数派认为 .10 主观下线（sdown→odown） |
| T+15s | 哨兵选出 .11 为新主，客户端切到 .11 |
| T+30s | 网络恢复，.10 恢复与哨兵通信，但**它自己仍是 master** |
| T+30s | 哨兵通知 .10 降级为 slave 指向 .11，.10 才追赶数据 |

问题在于：切换期间，**旧主 .10 没有立刻被隔离**，客户端如果还连旧主写入，这些写就丢了（.10 降级后会用 .11 的数据覆盖）。

### 4. 检查 quorum 与 down-after 配置

```bash
redis-cli -p 26379 SENTINEL config-get mymaster down-after-milliseconds
redis-cli -p 26379 SENTINEL config-get mymaster quorum
```

```text
down-after-milliseconds: 30000   -- 30s 才判定下线，偏长
quorum: 2
```

3 个哨兵 quorum=2 本身没问题，但没有配置**自动故障转移后的重确认**和**客户端刷新**保护。

## 根因

| 层级 | 说明 |
|---|---|
| 直接原因 | 网络分区期间旧主未被及时隔离，哨兵选出新主后旧主"复活"仍接受写入，造成双主与数据丢失 |
| 配置原因 | 缺少 `replica-priority`、缺少 `min-replicas-to-write` 保护，旧主分区时仍能写 |
| 客户端原因 | 客户端没有正确订阅哨兵 pub/sub 刷新拓扑，切换后还连旧主 |

## 解决步骤

### 止血

1. 立刻手动确认唯一主，把旧主拉下来避免双写：

```bash
# 确认 .11 是新主后，把旧主 .10 强制改成 .11 的从
redis-cli -h 10.0.7.10 REPLICAOF 10.0.7.11 6379
# 它会自动同步 .11 的数据，丢弃切换期间的孤立写入
```

2. 通知客户端重连（或重启客户端服务，强制刷新拓扑）。

### 根治

1. 在主库配置"最少从库数才允许写"，主库发现从库失联时自动拒绝写：

```conf
# 主库 redis.conf
min-replicas-to-write 1          # 至少 1 个从库在线才允许写
min-replicas-max-lag 10          # 从库延迟超过 10s 也算不在线
```

这样主库被网络隔离、连不上从库时会**自己拒绝写入**，避免脑裂双写。

2. 合理设置哨兵参数：

```conf
# sentinel.conf
sentinel monitor mymaster 10.0.7.10 6379 2
sentinel down-after-milliseconds mymaster 5000     # 缩短判定时间
sentinel failover-timeout mymaster 30000
sentinel parallel-syncs mymaster 1
```

3. 从库设不同 `replica-priority`，明确谁优先被提升：

```conf
# 性能强的从库 priority 小，优先当主
replica-priority 100     # .11
replica-priority 200     # .12
```

4. 客户端必须正确监听哨兵事件刷新拓扑（Lettuce/Jedis 都支持），切换后立即断开旧主连接。

## 验证与预防

```bash
redis-cli -p 26379 SENTINEL get-master-addr-by-name mymaster
# 三个节点 INFO replication 应只有一个 role:master
```

- 演练：定期做主从切换演练，验证哨兵 + 客户端联动正常。
- 监控：监控哨兵主观/客观下线事件、主从切换次数；双主检测告警。
- 规范：哨兵节点至少 3 个且跨机部署；客户端必须走哨兵发现而非写死主地址。

## 相关

- 命令速查：[Linux 命令速查](/reference/linux-commands) ｜ [网络命令速查](/reference/network-commands)
- 同组短文：[Redis 内存打满 OOM](/cases/t-redis-memory-oom) ｜ [缓存穿透/击穿/雪崩](/cases/t-redis-cache-avalanche) ｜ [集群脑裂](/cases/t-cluster-split-brain)
