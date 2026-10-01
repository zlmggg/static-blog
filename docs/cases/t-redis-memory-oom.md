---
category: 数据
difficulty: 中级
date: 2023-08-11
---

# Redis 内存打满 OOM（2023-08-11）

## 现象

Redis 突然拒绝写入，业务侧大量报错：

```text
(error) OOM command not allowed when used memory > 'maxmemory'.
```

监控上 Redis 内存曲线在 10 分钟内从 6GB 冲到 `maxmemory=8GB` 上限，随后所有写命令被拒。

## 环境

| 组件 | 版本 / 配置 |
|---|---|
| 操作系统 | Ubuntu 22.04 LTS |
| Redis | 7.0.11（单实例，无持久化策略误关） |
| `maxmemory` | 8gb |
| `maxmemory-policy` | `noeviction`（默认） |
| 业务 | 商品缓存 + 会话 + 排行榜，混合存放 |

## 定位过程

### 1. 确认内存确实打满

```bash
redis-cli INFO memory
```

关键输出：

```text
used_memory:8589934592        -- 已用 8GB
used_memory_human:8.00G
maxmemory:8589934592
maxmemory_policy:noeviction
mem_fragmentation_ratio:1.35
```

- `used_memory` 已经等于 `maxmemory`。
- `noeviction` 策略：内存满后**不淘汰任何 key**，直接拒绝写。

### 2. 看是哪类 key 占内存

```bash
# 按 dbsize 看总量
redis-cli DBSIZE

# 采样分析大 key（注意 --bigkeys 是采样，不阻塞）
redis-cli --bigkeys
```

`--bigkeys` 输出：

```text
# Sampling 100000 keys...
 Biggest string  found 'user:token:88213'  4MB
 Biggest list    found 'feed:timeline:100'  len=500000
 Biggest hash    found 'cache:product:all'  100万 field
```

发现一个 hash `cache:product:all` 塞了 100 万个 field，单个 key 就占了 1.2GB——典型的 **bigkey**。

### 3. 精确定位大 key

```bash
# 看某个 key 实际占用
redis-cli MEMORY USAGE cache:product:all
# 输出：1234567890 字节 ≈ 1.15GB

# 更精准的全量扫描（7.0 支持 MEMORY STATS）
redis-cli MEMORY STATS
```

### 4. 看是否有未设置过期时间的 key 无限堆积

```bash
# 找没有 TTL 的 key（永久驻留）
redis-cli --scan | head -1000 | while read k; do
  ttl=$(redis-cli TTL "$k"); [ "$ttl" = "-1" ] && echo "$k";
done | wc -l
```

结果：全库 90% 的 key 都没有设置过期时间（`TTL=-1`），业务方写缓存时忘了 `EXPIRE`。

## 根因

| 层级 | 说明 |
|---|---|
| 直接原因 | 一个 100 万 field 的大 hash + 大量无 TTL 的 key 无限堆积，把 8GB 内存吃满 |
| 策略原因 | `maxmemory-policy=noeviction`，满了不淘汰直接拒写 |
| 设计原因 | 业务把 Redis 当"永久数据库"用，缓存不设过期、不分 key 拆分 |

## 解决步骤

### 止血

1. 先临时改成 LRU 淘汰，让业务能继续写（动态生效）：

```bash
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

> 这会开始淘汰冷 key，业务可能读到空缓存（穿透到 DB），但比全挂强。

2. 立刻删掉那个失控的大 key：

```bash
# 大 key 不要直接 DEL（会阻塞），用 UNLINK 异步删
redis-cli UNLINK cache:product:all
```

### 根治

1. 合理设置淘汰策略（按业务选）：

```conf
# redis.conf
maxmemory 8gb
# 纯缓存场景用 allkeys-lru；有会话等不能丢的数据用 volatile-lru（只淘汰带 TTL 的）
maxmemory-policy allkeys-lru
```

| 策略 | 适用 |
|---|---|
| `noeviction` | 不允许丢数据（但会拒写） |
| `allkeys-lru` | 纯缓存，随便淘汰 |
| `volatile-lru` | 混合场景，只淘汰设了过期的 |
| `allkeys-lfu` | 热点明显的缓存 |

2. 拆分大 key：把 100 万 field 的大 hash 按 `product_id` 分片：

```text
cache:product:all  →  cache:product:{id%16}  每片几万 field
```

3. 强制所有缓存 key 必须带 TTL，业务侧封装写入时统一加过期时间，并加随机抖动防雪崩（见 [缓存穿透/击穿/雪崩](/cases/t-redis-cache-avalanche)）。

## 验证与预防

```bash
redis-cli INFO memory | grep used_memory_human   # 内存回落到水位线以下
redis-cli CONFIG GET maxmemory-policy
```

- 监控：对 `used_memory / maxmemory` 配告警（>70% 预警）；定期跑 `--bigkeys` 巡检。
- 规范：禁止单 key 超过 10KB（string）/ 5000 元素（hash/list/zset）；缓存必须设 TTL。
- 容量：根据数据增长预估内存，预留 30% 碎片与缓冲。

## 相关

- 命令速查：[Linux 命令速查](/reference/linux-commands)
- 同组短文：[缓存穿透/击穿/雪崩](/cases/t-redis-cache-avalanche) ｜ [哨兵故障切换异常](/cases/t-redis-sentinel-failover)
