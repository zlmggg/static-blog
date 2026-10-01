---
category: 数据
difficulty: 中级
date: 2020-09-22
---

# MySQL 慢查询与索引失效（2020-09-22）

## 现象

后台报表接口越来越慢，一个原本 200ms 的查询慢慢退化到 8s 以上，高峰期直接超时。DBA 反馈慢查询日志里同一类 SQL 每天累积上万条。

```text
# Query_time: 8.421312  Lock_time: 0.000187 Rows_sent: 15  Rows_examined: 2034881
SELECT id, title, created_at FROM t_article
 WHERE status = 1 AND category_id = 8
 ORDER BY created_at DESC LIMIT 15;
```

注意：`Rows_examined=203 万` 只返回 15 行——扫描了全表 200 万行才挑出 15 条。

## 环境

| 组件 | 版本 / 配置 |
|---|---|
| 操作系统 | Ubuntu 18.04.5 LTS |
| MySQL | 8.0.21 |
| 表规模 | `t_article` 约 2300 万行 |
| 索引现状 | 只有主键 `PRIMARY(id)`，`status`/`category_id`/`created_at` 无联合索引 |
| 慢日志 | `slow_query_log=ON`，`long_query_time=1` |

## 定位过程

### 1. 确认慢日志已开启并定位 SQL

```sql
SHOW VARIABLES LIKE 'slow_query_log%';
SHOW VARIABLES LIKE 'long_query_time';
```

用 `mysqldumpslow` 聚合慢日志，找出最耗时 / 最频繁的 SQL：

```bash
mysqldumpslow -s t -t 10 /var/lib/mysql/slow.log
# -s t 按总时间排序，-t 10 取前 10 条
```

### 2. EXPLAIN 看执行计划

```sql
EXPLAIN
SELECT id, title, created_at FROM t_article
 WHERE status = 1 AND category_id = 8
 ORDER BY created_at DESC LIMIT 15\G
```

输出关键字段：

```text
type:         ALL                -- 全表扫描！理想应为 ref / range
possible_keys: NULL
key:          NULL               -- 没用到任何索引
rows:         2034881
Extra:        Using where; Using filesort   -- 额外文件排序
```

- `type=ALL`：全表扫描。
- `key=NULL`：没用上索引。
- `Using filesort`：`ORDER BY` 没法走索引，要额外排序。

### 3. 验证索引为什么没生效

`status` 字段区分度极低（只有 0/1），单独建索引也没用。检查字段基数：

```sql
SELECT
  COUNT(DISTINCT status)/COUNT(*) AS status_sel,
  COUNT(DISTINCT category_id)/COUNT(*) AS cat_sel
FROM t_article;
```

```text
status_sel: 0.0002    -- status 几乎没区分度
cat_sel:    0.0813    -- category_id 有一定区分度
```

即使对 `status` 建单列索引，优化器也会因为区分度太差放弃它，继续全表扫。

### 4. 看执行计划里索引是否被"选错"

有时索引存在但没被选中，可能是统计信息过期：

```sql
ANALYZE TABLE t_article;
-- 再 EXPLAIN 一次对比
```

本次没有现成索引可选错，问题是**压根没有合适的联合索引**。

## 根因

| 层级 | 说明 |
|---|---|
| 直接原因 | 查询条件 `status + category_id` + 排序 `created_at` 没有对应联合索引，触发全表扫描 + filesort |
| 数据原因 | 随业务增长行数从几十万涨到 2300 万，全表扫描代价被放大 |
| 设计原因 | 高频查询字段缺索引，且 `status` 低基数字段被错误地期待单独走索引 |

## 解决步骤

### 止血

1. 报表接口先加缓存（Redis 缓存查询结果，TTL 1 分钟），挡住高峰读压力：

```text
key = report:cat:{category_id}:page:{n}   TTL=60s
```

2. 报表查询临时切到只读从库，不要打主库。

### 根治

1. 建**联合索引**，遵循"等值在前、排序在后"原则：

```sql
-- 把区分度高的等值列 category_id 放前面，排序列 created_at 放最后
ALTER TABLE t_article
  ADD INDEX idx_cat_status_created (category_id, status, created_at);
```

> 联合索引列顺序：先放等值查询列（`category_id=8`、`status=1`），再放范围/排序列（`ORDER BY created_at`）。这样既能定位数据，又能利用索引顺序避免 filesort。

2. 加完后重新 `EXPLAIN` 验证：

```text
type: ref
key:  idx_cat_status_created
rows: 1520          -- 从 200 万降到 1500
Extra: Using where; Using index condition
```

`Using filesort` 消失，`rows` 大幅下降。

3. 大表加索引注意：8.0 支持 Online DDL，但 2300 万行仍建议在低峰期执行，或用 `pt-online-schema-change` 避免锁表。

## 验证与预防

```sql
-- 慢查询量应明显下降
SHOW GLOBAL STATUS LIKE 'Slow_queries';
```

- 监控：监控慢查询条数增长率、`Rows_examined` 均值。
- 规范：上线新 SQL 前必须 `EXPLAIN`，禁止 `SELECT *`，禁止无 `WHERE` 的大表更新。
- 流程：DBA 定期 review 慢日志，清理无用索引、补充缺失索引。

## 相关

- 命令速查：[Linux 命令速查](/reference/linux-commands)
- 同组短文：[主从复制延迟](/cases/t-mysql-replica-lag) ｜ [InnoDB 死锁](/cases/t-mysql-deadlock) ｜ [连接数打满](/cases/t-mysql-too-many-connections)
