---
title: Redis
description: Redis 单线程模型、源码/Docker 安装、五大类型与 bitmap/stream、RDB/AOF/混合持久化、过期淘汰、事务 Lua、主从、哨兵、Cluster 哈希槽、缓存穿透击穿雪崩与分布式锁
---

# Redis

::: tip 本篇定位
掌握 Redis **单线程模型、五大数据类型与场景、持久化、过期淘汰、事务/Lua**，会搭建 **主从、哨兵、Cluster**，并能解决**缓存穿透/击穿/雪崩、缓存一致性、分布式锁**等实战问题。
:::

## 先建立全局观：Redis 为什么快

| 原因 | 说明 |
|---|---|
| 纯内存 | 数据在内存，读写没有磁盘 IO |
| 高效模型 | IO 多路复用（epoll）+ 事件驱动 |
| 命令单线程 | 无锁、无线程切换、无竞态（6.0 起网络 IO 多线程，**命令执行仍单线程**） |
| 数据结构高效 | 针对场景专门优化 |

---

## 一、简介与安装

Redis（Remote Dictionary Server）是高性能内存型 key-value 数据库，BSD 协议，支持持久化、丰富数据类型、高可用。常用于缓存、计数器、排行榜、分布式锁、消息队列、限流。

### 1.1 单线程模型

- **6.0 之前**：核心全程单线程处理；
- **6.0 及以后**：网络 IO 读写引入**多线程**，但**命令执行仍由主线程串行完成**（保证原子性、无锁竞争）；
- 辅助操作（持久化、异步删除、集群同步）本来就由后台线程做。

### 1.2 源码安装（推荐，版本新）

```bash
sudo dnf install -y gcc make tar        # Debian: build-essential
tar -xzf redis-7.4.2.tar.gz && cd redis-7.4.2
make && sudo make PREFIX=/usr/local/redis install
sudo mkdir -p /etc/redis && sudo cp redis.conf /etc/redis/redis.conf
sudo /usr/local/redis/bin/redis-server /etc/redis/redis.conf
```

### 1.3 包管理 / Docker

```bash
sudo apt install -y redis-server        # Debian
sudo dnf install -y redis              # RHEL（EPEL）

docker run -d --name redis -p 6379:6379 \
  -v /data/redis/redis.conf:/etc/redis/redis.conf \
  redis:7.4.2 redis-server /etc/redis/redis.conf
```

### 1.4 核心配置 redis.conf

```conf
bind 0.0.0.0
port 6379
daemonize yes
requirepass Your@123
dir /data/redis
maxmemory 512mb
maxmemory-policy allkeys-lru
# io-threads 2        # 6.x 网络 IO 线程
```

### 1.5 客户端与通用命令

```bash
redis-cli -h 10.0.0.13 -a Your@123
```

```sql
PING                          -- PONG
SELECT 0                      -- 切换 db（默认 16 个）
DBSIZE
KEYS *                        -- 生产禁用（阻塞）
SCAN 0 MATCH user:* COUNT 100 -- 渐进遍历（推荐）
EXISTS k; DEL k; EXPIRE k 60; TTL k; TYPE k; RENAME k k2
CONFIG GET maxmemory
INFO
```

---

## 二、数据类型

### 2.1 String 字符串

缓存、计数器、分布式锁、session、验证码。

```sql
SET name tom;  GET name
SET code 100 EX 60                 -- 60 秒过期
SETNX lock 1                       -- 不存在才设置
INCR cnt; DECR cnt; INCRBY cnt 5
MSET a 1 b 2; MGET a b
APPEND name x; STRLEN name
```

### 2.2 Hash 哈希

存对象（用户、商品），可单字段更新、比 String 更省。

```sql
HSET user:1 name tom age 20
HGET user:1 name
HGETALL user:1
HMGET user:1 name age
HINCRBY user:1 age 1
HDEL user:1 age; HKEYS user:1; HVALS user:1
```

### 2.3 List 列表

有序可重复、双端操作：消息队列、最新列表/时间线。

```sql
LPUSH msgs a b; RPUSH msgs c
LRANGE msgs 0 -1
LPOP msgs; RPOP msgs
LLEN msgs
BLPOP msgs 10            -- 阻塞式弹出（队列常用）
```

### 2.4 Set 集合

无序、自动去重、交并差集：标签、共同好友、抽奖。

```sql
SADD tags redis linux mysql
SMEMBERS tags; SISMEMBER tags redis
SINTER s1 s2             -- 交集（共同好友）
SUNION s1 s2             -- 并集
SDIFF s1 s2              -- 差集
SRANDMEMBER tags 1       -- 随机
SPOP tags                -- 随机弹出
```

### 2.5 ZSet 有序集合

成员带 score 并排序：排行榜、热搜、带权重队列。

```sql
ZADD rank 90 tom 85 jack 100 lily
ZRANGE rank 0 -1 WITHSCORES
ZREVRANGE rank 0 2 WITHSCORES       -- 前 3 名
ZRANGEBYSCORE rank 80 95
ZRANK rank tom; ZSCORE rank tom
ZINCRBY rank 5 tom
ZREM rank tom
```

### 2.6 其他类型

| 类型 | 场景 | 命令 |
|---|---|---|
| Bitmap 位图 | 签到、在线状态、布尔统计（极省内存） | SETBIT、GETBIT、BITCOUNT、BITOP |
| HyperLogLog | 海量 UV 去重计数（约 0.81% 误差） | PFADD、PFCOUNT、PFMERGE |
| Stream（5.0） | 消息队列（消费组、持久化、ACK） | XADD、XREAD、XGROUP、XACK |
| Geo | 附近的人/门店、距离 | GEOADD、GEORADIUS、GEODIST |

---

## 三、持久化

### 3.1 RDB 快照

某时刻把内存数据快照写入 `dump.rdb`（`SAVE` 阻塞 / `BGSAVE` fork 子进程）。

- 优点：文件紧凑、恢复快、适合备份；
- 缺点：间隔期宕机会丢数据，fork 大内存有开销。

```conf
save 900 1            -- 900 秒内 1 次改动触发
save 300 10
dbfilename dump.rdb
```

### 3.2 AOF 追加日志

记录每条写命令，重启重放恢复。

```conf
appendonly yes
appendfsync everysec       -- always 最安全 / everysec 默认(最多丢1秒) / no
auto-aof-rewrite-percentage 100
```

- 优点：数据更安全；
- 缺点：文件大、恢复慢，需重写（BGREWRITEAOF）压缩。

### 3.3 混合持久化（推荐）

4.0+ AOF 重写时，前半部分用 RDB 快照、后半部分追加增量命令（`aof-use-rdb-preamble yes`），兼顾恢复速度与安全。

| 场景 | 选择 |
|---|---|
| 纯缓存、可丢 | 关闭持久化 |
| 不能丢 | AOF everysec / 混合 |
| 备份 | RDB 定期 + 异地 |

---

## 四、过期与淘汰

### 4.1 过期删除

设了 TTL 的 key 用**惰性删除**（访问时检查）+ **定期删除**（周期抽样）结合。

### 4.2 内存淘汰策略（maxmemory 满）

| 策略 | 说明 |
|---|---|
| noeviction | 不淘汰，写报错（默认） |
| allkeys-lru | 所有 key 淘汰最久未用（缓存常用） |
| volatile-lru | 设过期的 key 中 LRU |
| allkeys-lfu / volatile-lfu | 按访问频率淘汰最少用（4.0） |
| allkeys-random / volatile-random | 随机 |
| volatile-ttl | 淘汰最快过期的 |

---

## 五、事务与 Lua

### 5.1 事务

```sql
MULTI                -- 开启
SET a 1
SET b 2
EXEC                 -- 顺序执行（或 DISCARD 放弃）
WATCH key            -- 监视，被改动则事务失败（乐观锁）
```

> Redis 事务**不支持回滚**：命令入队时的语法错误会全部不执行，但运行期错误（如对字符串 incr）其他命令仍执行，需自己保证正确。

### 5.2 Lua 脚本（真正原子）

```bash
redis-cli -a pass EVAL "return redis.call('get', KEYS[1])" 1 mykey
# EVALSHA 执行缓存脚本；脚本整体原子执行，适合组合操作（如限流、释放锁）
```

---

## 六、主从复制

一主多从、读写分离、数据冗余。

```sql
-- 从库
REPLICAOF 10.0.0.13 6379        -- 旧命令 SLAVEOF
-- REPLICAOF NO ONE             -- 断开关联升主
```

- **全量同步**：首次连接，主库 BGSAVE 生成 RDB 发给从库 + 缓冲期间新命令；
- **增量同步**：之后通过**复制积压缓冲区（repl backlog）**用 PSYNC 补发；
- 主从需手动切换。

---

## 七、哨兵 Sentinel

在主从上提供自动化高可用：监控、通知、**自动故障转移**、配置提供。

### 7.1 部署（奇数，如 3 个）

```conf
# sentinel.conf
port 26379
sentinel monitor mymaster 10.0.0.13 6379 2     -- quorum=2
sentinel auth-pass mymaster Your@123
sentinel down-after-milliseconds mymaster 5000
sentinel failover-timeout mymaster 60000
```

```bash
redis-sentinel /etc/sentinel.conf
```

### 7.2 故障转移

1. 单哨兵发现主无响应 → **主观下线**；
2. 达 quorum → **客观下线**；
3. 哨兵选 leader，按优先级/复制偏移/runid 选一个从库**提升为新主**；
4. 其他从库指向新主，客户端经哨兵获取新主地址。

---

## 八、Cluster 集群

哨兵保证高可用但数据仍在单主、无法水平扩容量。Cluster **分片**把数据分散到多主。

### 8.1 哈希槽

- 共 **16384 槽**，`CRC16(key) % 16384` 定位，槽分给各主；
- 多主各管部分槽、每主配从；节点间用 Gossip 通信；
- 多 key 需同槽，用 **hash tag**：`{user}:1`、`{user}:2`。

### 8.2 搭建（3 主 3 从）

```bash
# 各节点配置 cluster-enabled yes、cluster-config-file nodes-7001.conf
redis-cli --cluster create \
  10.0.0.13:7001 10.0.0.13:7002 10.0.0.13:7003 \
  10.0.0.13:7004 10.0.0.13:7005 10.0.0.13:7006 \
  --cluster-replicas 1 -a Your@123

redis-cli -c -p 7001          -- -c 集群模式自动重定向
CLUSTER NODES; CLUSTER INFO
```

### 8.3 运维

```bash
redis-cli --cluster add-node 新:7007 10.0.0.13:7001     -- 加节点
redis-cli --cluster reshard 10.0.0.13:7001             -- 迁移槽
redis-cli --cluster check 10.0.0.13:7001
```

| 方案 | 解决 | 容量 | 切换 |
|---|---|---|---|
| 主从 | 读扩展/冗余 | 单机 | 手动 |
| 哨兵 | 高可用 | 单机 | 自动 |
| Cluster | 高可用 + 水平扩容 | 分片 | 自动 |

---

## 九、缓存实战问题

### 9.1 缓存穿透

查询**数据库里也不存在**的数据，每次都打到 DB（如恶意刷不存在 ID）。

- 方案：**缓存空值**（短 TTL）、**布隆过滤器**（先判断 ID 是否可能存在）、参数校验。

### 9.2 缓存击穿

某个**热点 key 过期**瞬间，大量并发同时打到 DB。

- 方案：**互斥锁**（只放一个线程查库重建，其他等待）、热点 key **逻辑过期/不过期**。

### 9.3 缓存雪崩

**大量 key 同时过期**或 **Redis 整体宕机**，请求全压 DB。

- 方案：过期时间**加随机值**错开、Redis **集群高可用**、多级缓存、限流降级兜底。

### 9.4 缓存与数据库一致性

常用 **Cache Aside**：读先查缓存、miss 查库回填；**写先更新数据库，再删除缓存**（删缓存比更新缓存更稳）；必要时**延迟双删**、订阅 binlog（如 Canal）刷新。

### 9.5 分布式锁

```sql
-- 加锁：NX + 过期时间 + 唯一标识
SET lock:order 客户端唯一ID NX PX 10000
-- 释放锁用 Lua：先判断是自己的锁再删，避免误删别人的锁
```

要点：加锁设过期防死锁、值唯一、Lua 原子释放；复杂场景（可重入、看门狗续期）用 **Redisson**。

---

## 面试自测

1. Redis 为什么快？6.0 的多线程指什么，为什么命令还是单线程？
2. 五种数据类型各自的典型场景？ZSet 底层了解吗？
3. RDB 和 AOF 的区别？混合持久化是什么？
4. Redis 的过期删除和内存淘汰策略有哪些？
5. 缓存穿透、击穿、雪崩分别是什么、怎么解决？
6. 如何保证缓存和数据库一致性？
7. 分布式锁怎么实现才安全？SETNX 有什么问题？
8. 哨兵的故障转移流程？Cluster 的哈希槽原理，为什么是 16384？

## 相关速查

- [Linux 命令速查](/reference/linux-commands)
- Redis 官方文档：https://redis.io/docs/latest/
- Redis 命令：https://redis.io/commands/
- Redisson：https://redisson.pro/
