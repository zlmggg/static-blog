---
category: 数据
difficulty: 高级
date: 2021-11-08
---

# InnoDB 死锁排查（2021-11-08）

## 现象

业务接口偶发报错，错误日志里反复出现：

```text
ERROR 1213 (40001): Deadlock found when trying to get lock; try restarting transaction
```

高峰期（约 10:00~11:00）每小时出现几十次，集中在"订单扣减库存 + 更新状态"这条事务链路上。

## 环境

| 组件 | 版本 / 配置 |
|---|---|
| 操作系统 | CentOS 7.9 |
| MySQL | 8.0.26 (InnoDB) |
| 隔离级别 | `REPEATABLE-READ`（默认） |
| 存储引擎 | InnoDB，`innodb_autoinc_lock_mode=2` |
| 业务表 | `stock`（商品库存）、`order`（订单） |

## 定位过程

### 1. 打开 InnoDB 锁监控开关（动态）

```sql
-- 把最近一次死锁信息保留下来（默认只在发生时打印到 error log）
SET GLOBAL innodb_print_all_deadlocks = ON;

-- 确认锁监控开启（8.0 默认可用）
SHOW STATUS LIKE 'InnoDB_row_lock%';
```

### 2. 抓最近一次死锁现场

```sql
SHOW ENGINE INNODB STATUS\G
```

输出里找 `LATEST DETECTED DEADLOCK` 段：

```text
------------------------
LATEST DETECTED DEADLOCK
------------------------
*** (1) TRANSACTION:
TRANSACTION 54210321, ACTIVE 0 sec starting index read
mysql tables in use 1, locked 1
LOCK WAIT 3 lock struct(s)
MySQL thread id 8821, OS thread handle 0x7f2, query id 99123 updating
UPDATE stock SET count = count - 1 WHERE sku_id = 1001

*** (2) TRANSACTION:
TRANSACTION 54210325, ACTIVE 0 sec starting index read
mysql tables in use 1, locked 1
3 lock struct(s)
MySQL thread id 8822, query id 99127 updating
UPDATE order SET status = 1 WHERE order_id = 5567

*** WE ROLL BACK TRANSACTION (2)
```

解读要点：

- 两个事务各持一把锁、又在等对方的锁，形成循环等待。
- InnoDB 主动回滚了**回滚代价小**的那个事务（这里是事务 2）。

### 3. 看具体锁等待与间隙锁

```sql
-- 8.0 性能视图：看当前锁等待与持有的锁
SELECT * FROM performance_schema.data_lock_waits\G
SELECT * FROM performance_schema.data_locks\G
```

`data_locks` 里 `LOCK_MODE` 列是关键：

| LOCK_MODE | 含义 |
|---|---|
| `X` | 排他记录锁 |
| `X,GAP` | 间隙锁（锁住索引区间，防止插入） |
| `X,Next-Rec` | 临键锁（记录锁 + 间隙锁，RR 级别默认） |

本次两个事务都用了 `Next-Rec` 临键锁：事务 A 按 `sku_id` 范围更新锁住了 `(1000,1001]`，事务 B 按另一个范围更新锁住了 `(1001,1002]`，两个区间在 1001 这个点上互相等待。

### 4. 复盘业务 SQL 的加锁顺序

把报错时段业务日志里的两条事务 SQL 摘出来：

| 事务 A（线程 8821） | 事务 B（线程 8822） |
|---|---|
| `UPDATE stock SET count=count-1 WHERE sku_id=1001` | `UPDATE stock SET count=count-2 WHERE sku_id BETWEEN 1000 AND 1002` |
| `UPDATE order SET status=1 WHERE order_id=5567` | `UPDATE order SET status=2 WHERE order_id=5567` |

两边**加锁顺序不一致**：A 先锁 stock 再锁 order；B 先范围锁 stock（更大区间）再锁 order。交叉之下形成死锁。

## 根因

| 层级 | 说明 |
|---|---|
| 直接原因 | 两个并发事务以不同顺序、不同范围（等值 vs 范围）更新同一批行，RR 隔离级别的临键锁/间隙锁放大了锁区间 |
| 代码原因 | 业务代码没有统一的"加锁顺序"，且范围更新 `BETWEEN` 触发了间隙锁 |
| 索引原因 | `sku_id` 上索引区分度不足，范围扫描锁住了本不该锁的行 |

## 解决步骤

### 止血

1. 死锁本身是 InnoDB 主动牺牲小事务，业务侧必须**重试**被回滚的事务（报错 1213 是可重试错误）：

```java
// 伪代码：捕获 1213 后指数退避重试
while (retry < 3) {
  try { doBusinessTx(); break; }
  catch (DeadlockLoserDataAccessException e) { sleep(50 << retry); retry++; }
}
```

2. 高峰期临时把热点商品库存更新改成单行等值更新，去掉范围更新。

### 根治

1. **统一加锁顺序**：所有事务都按相同顺序访问资源（例如永远先锁 stock 再锁 order，且按主键/sku_id 升序加锁），破坏循环等待条件。

2. 缩小锁范围：把范围更新改成等值更新，避免临键锁：

```sql
-- 避免：范围更新会加间隙锁
UPDATE stock SET count = count - 2 WHERE sku_id BETWEEN 1000 AND 1002;

-- 改为：逐行等值更新，或在应用层拆成多条
UPDATE stock SET count = count - 1 WHERE sku_id = 1001;
UPDATE stock SET count = count - 1 WHERE sku_id = 1002;
```

3. 必要时降低隔离级别到 `READ-COMMITTED`（RC 级别不用间隙锁，能显著减少死锁）：

```ini
transaction_isolation = READ-COMMITTED
# RC 下必须确保 binlog_format=ROW（statement 格式在 RC 下不安全）
binlog_format = ROW
```

4. 给 `sku_id`、`order_id` 确保有合适索引，避免索引失效导致锁全表。

## 验证与预防

```sql
-- 观察死锁是否消失
SHOW ENGINE INNODB STATUS\G   -- LATEST DETECTED DEADLOCK 不再刷新
SHOW STATUS LIKE 'Innodb_deadlocks';  -- 计数器不再增长
```

- 监控：对 `Innodb_deadlocks` 计数器做增量告警。
- 规范：code review 时检查事务内多表写操作的加锁顺序；范围更新必须评估间隙锁影响。
- 压测：对高并发扣减链路做并发压测，提前暴露死锁。

## 相关

- 命令速查：[Linux 命令速查](/reference/linux-commands)
- 同组短文：[主从复制延迟](/cases/t-mysql-replica-lag) ｜ [慢查询排查](/cases/t-mysql-slow-query) ｜ [连接数打满](/cases/t-mysql-too-many-connections)
