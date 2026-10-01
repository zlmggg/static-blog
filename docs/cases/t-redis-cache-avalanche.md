---
category: 数据
difficulty: 中级
date: 2024-03-20
---

# Redis 缓存穿透 / 击穿 / 雪崩（2024-03-20）

## 现象

大促期间，DB 连接数突然飙升，慢查询暴增，Redis 命中率从 95% 掉到 60%。监控显示某几个热点商品的查询在同一秒内打到数据库上千次。

```text
# 应用日志
Cache miss, query DB: product_id=9527
Cache miss, query DB: product_id=9527   -- 同一 key 被并发回源上千次
```

## 环境

| 组件 | 版本 / 配置 |
|---|---|
| 操作系统 | Rocky Linux 9.2 |
| Redis | 7.2.4（哨兵模式） |
| 业务 | 电商商品详情页，QPS 峰值 8000 |
| 缓存策略 | 查不到 DB 后回写缓存，TTL=10min |

## 定位过程

先分清是"穿透 / 击穿 / 雪崩"哪一类——三者症状相似但根因不同：

| 现象 | 根因 | 典型特征 |
|---|---|---|
| 穿透 | 查询**根本不存在**的数据，缓存永远 miss | 大量查不存在的 id，DB 被打 |
| 击穿 | **单个热点 key** 过期瞬间，并发回源 | 某个 key 同一时刻上千次回源 |
| 雪崩 | **大批 key 同时过期** | 整体命中率骤降，DB 整体被打 |

### 1. 看 Redis 命中率

```bash
redis-cli INFO stats | grep -E "keyspace_hits|keyspace_misses"
# 命中率 = hits / (hits + misses)
```

本次命中率骤降集中在几个热点 key，且发生在整点（缓存统一 TTL=10min，整点批量过期）。

### 2. 抓回源热点

```bash
# 看哪些 key 正在被高频访问
redis-cli --hotkeys        # 需要开启 LFU 策略才准确
# 应用日志里 grep 同一 product_id 的回源次数
grep "product_id=9527" app.log | wc -l
```

确认：`product_id=9527` 是爆款，缓存过期瞬间 1000+ 并发同时 miss 回源——这是**击穿**。

同时发现有恶意脚本在遍历不存在的 `product_id`（负数/随机数），缓存永远 miss——这是**穿透**。

## 根因

| 问题 | 根因 |
|---|---|
| 击穿 | 热点 key 无互斥保护，过期瞬间并发全部回源 |
| 穿透 | 对不存在的数据也每次查 DB，没有拦截 |
| 雪崩隐患 | 所有 key 用固定 TTL=10min，整点集中过期 |

## 解决步骤

### 止血

1. 先给 DB 前面加限流，挡住瞬时回源洪峰：

```text
# 网关/应用层对 product 接口限流：单接口 200 QPS，超出快速失败
```

2. 把爆款商品 key 先手动塞回缓存，恢复命中率。

### 根治

**针对击穿——互斥锁回源（只放一个请求去查 DB）：**

```text
# 伪代码：缓存 miss 时，先抢锁，抢到的才查 DB，其余短暂等待后重读缓存
func getProduct(id):
    data = GET("product:" + id)
    if data != nil: return data
    if SETNX("lock:product:"+id, "1", EX=5) == 1:   # 抢锁成功
        data = queryDB(id)
        SET("product:"+id, data, EX=600)
        DEL("lock:product:"+id)
    else:
        sleep(50ms); return getProduct(id)            # 自旋等缓存
    return data
```

**针对穿透——布隆过滤器 + 空值缓存：**

```bash
# 方案一：布隆过滤器（Redis 7 自带 Bloom 模块，或用 Redisson）
# 启动时把所有存在的 product_id 灌进布隆过滤器
# 请求先过布隆，判断"一定不存在"的直接返回，不查缓存不查 DB

# 方案二：对不存在的 key 也缓存空值（短 TTL）
SET "product:notexist:999999" "" EX=60
```

| 手段 | 适用 | 注意 |
|---|---|---|
| 布隆过滤器 | 数据量大、防恶意枚举 | 有误判率，误判只是多查一次 DB |
| 空值缓存 | 数据量小 | 注意防缓存膨胀 |

**针对雪崩——TTL 加随机抖动：**

```text
# 不要统一 TTL=600，加随机偏移，避免同一秒批量过期
ttl = 600 + random(0, 120)     # 600~720s 随机
```

3. 热点 key 可做**逻辑过期**（不设物理 TTL，value 里带过期时间，异步线程刷新），保证任何时刻缓存都有值。

## 验证与预防

```bash
redis-cli INFO stats | grep -E "hits|misses"   # 命中率恢复到 95%+
# DB 侧慢查询、连接数应回落到正常水位
```

- 监控：缓存命中率、DB 回源 QPS 配告警；命中率 <90% 预警。
- 规范：热点 key 必须加互斥锁；批量写缓存 TTL 必须带随机抖动；恶意穿透用布隆拦截。
- 预案：大促前提前预热爆款缓存。

## 相关

- 命令速查：[Linux 命令速查](/reference/linux-commands) ｜ [网络命令速查](/reference/network-commands)
- 同组短文：[Redis 内存打满 OOM](/cases/t-redis-memory-oom) ｜ [哨兵故障切换异常](/cases/t-redis-sentinel-failover)
