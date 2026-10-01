---
category: 数据
difficulty: 中级
date: 2022-06-14
---

# MySQL 主从复制延迟排查（2022-06-14）

## 现象

业务反馈：从库读到的数据"慢半拍"，主库刚写入的记录，在从库接口里要等十几秒甚至更久才出现。监控告警 `Seconds_Behind_Source` 持续飙高，峰值超过 300s。

```text
MySQL Replication Lag  告警：replica-lag > 120s
当前值：318s
实例：10.0.8.21:3306 (replica)
```

## 环境

| 组件 | 版本 / 配置 |
|---|---|
| 操作系统 | Ubuntu 20.04.4 LTS |
| MySQL | 8.0.28 (Community, InnoDB) |
| 复制方式 | 异步复制，GTID 模式（`gtid_mode=ON`） |
| 拓扑 | 1 主（10.0.8.20） + 2 从（.21 / .22） |
| 关键参数 | `replica_parallel_workers=4`，`replica_parallel_type=LOGICAL_CLOCK` |

## 定位过程

### 1. 看复制状态总览

在**从库**上执行（MySQL 8.0.22+ 用 `SHOW REPLICA STATUS`，老版本才是 `SHOW SLAVE STATUS`）：

```sql
SHOW REPLICA STATUS\G
```

重点关注这几列：

```text
Replica_IO_Running: Yes
Replica_SQL_Running: Yes
Seconds_Behind_Source: 318
Last_SQL_Errno: 0
Retrieved_Gtid_Set: 3e11f2a0-...:1-882134
Executed_Gtid_Set: 3e11f2a0-...:1-879001
Relay_Log_Space: 45628113
```

- `IO_Running=Yes`、`SQL_Running=Yes`：复制线程都活着，不是中断。
- `Seconds_Behind_Source=318`：确实延迟。
- `Retrieved_Gtid_Set` 比 `Executed_Gtid_Set` 多了约 3000 个事务：已经拉到 relay log 但还没重放完，瓶颈在 SQL 回放端，不是 IO 拉取端。

### 2. 确认瓶颈在 SQL 线程还是 IO 线程

```sql
-- 从库看 IO 拉取位点，主库看最新 binlog 位点
SHOW REPLICA STATUS\G;        -- 关注 Source_Read_Log_Pos
SHOW MASTER STATUS;            -- 主库当前 Position
```

如果 `Retrieved_Gtid_Set` 已基本追到主库最新位点，而 `Executed_Gtid_Set` 远远落后，说明 IO 已经拉完、SQL 跟不上——典型的**回放慢**。

### 3. 看并行复制是否生效、worker 在忙什么

```sql
-- 5.7+/8.0 性能视图：看各 worker 的回放状态
SELECT worker_id, thread_id, service_state, last_applied_trx_original_commit_timestamp
FROM performance_schema.replication_applier_status_by_worker\G
```

输出解读：

```text
worker_id: 0  service_state: ON   (协调线程)
worker_id: 1  service_state: ON
worker_id: 2  service_state: ON
worker_id: 3  service_state: ON
worker_id: 4  service_state: ON
```

worker 都在 `ON`（忙碌）说明并行复制在干活；但如果延迟仍然高，往往是**事务之间存在冲突/依赖**，导致 LOGICAL_CLOCK 并行度上不去，大量事务退化为串行。

### 4. 抓大事务

延迟往往是被个别超大事务"卡住"的：一个事务在 relay log 里要重放几分钟，后面所有 worker 都得等它。

```sql
-- 主库：列出 binlog，再用 mysqlbinlog 按事务位置排序找最大事务
SHOW BINARY LOGS;
mysqlbinlog --base64-output=DECODE-ROWS -v /var/lib/mysql/binlog.000123 \
  | awk '/^# at /{pos=$2} /^COMMIT/{print pos}' | sort -n | tail

-- 从库：看当前正在执行的大事务
SELECT ID, TIME, STATE, INFO FROM information_schema.PROCESSLIST
WHERE COMMAND != 'Sleep' ORDER BY TIME DESC LIMIT 10;
```

本次抓到一个业务侧的批量 `DELETE ... WHERE created_at < ...`，单事务删除 200 万行，主库跑了 8s，从库回放要 60s+，把并行 worker 全堵死。

## 根因

| 层级 | 说明 |
|---|---|
| 直接原因 | 业务侧周期性批量删除大表，单事务过大，从库 SQL 线程回放耗时远超主库执行耗时 |
| 放大因素 | `binlog_transaction_dependency_tracking=COMMIT_ORDER`，大事务与相邻事务无法并行，并行复制退化 |
| 流程因素 | 批量清理任务没有分批、没有在低峰期执行，直接打到线上主从 |

## 解决步骤

### 止血

1. 先把大事务拆小，立刻缓解回放压力：

```sql
-- 在主库停掉正在跑的批量清理 job（找到对应连接 KILL）
KILL <batch_delete_thread_id>;
```

2. 临时调大并行度（动态生效，无需重启）：

```sql
SET GLOBAL replica_parallel_workers = 8;
SET GLOBAL replica_preserve_commit_order = ON;
```

### 根治

1. 开启 WRITESET 依赖追踪，让无冲突事务真正并行（需要主库 `binlog_format=ROW`）：

```ini
# my.cnf
binlog_transaction_dependency_tracking = WRITESET
binlog_row_image = MINIMAL
replica_parallel_workers = 8
replica_parallel_type = LOGICAL_CLOCK
replica_preserve_commit_order = ON
```

> `WRITESET` 基于行级 hash 判断事务是否修改同一行，无关事务可并行，8.0 推荐开启。

2. 根治大事务：批量操作必须**分批 + 限速**，单事务影响行数控制在 1000~5000 行：

```sql
-- 错误：一次删 200 万行
DELETE FROM t_log WHERE created_at < '2022-01-01';
-- 正确：循环小批删，每批之间 sleep 0.1s
DELETE FROM t_log WHERE created_at < '2022-01-01' LIMIT 1000;
```

3. 大表清理改用 pt-archiver 这类在线归档工具，控制事务大小。

## 验证与预防

```sql
-- 持续观察延迟是否回落，Seconds_Behind_Source 应稳定在 0~1s
SHOW REPLICA STATUS\G
```

- 监控：对 `Seconds_Behind_Source` 配告警（>60s 预警、>300s 严重），同时监控 `Relay_Log_Space`。
- 规范：禁止单事务超过 1 万行；批量任务必须分批、错峰、可限速。
- 压测：上线大促/大批量任务前，先在从库观察回放延迟表现。

## 相关

- 命令速查：[Linux 命令速查](/reference/linux-commands)
- 同组短文：[MySQL 慢查询排查](/cases/t-mysql-slow-query) ｜ [连接数打满 Too many connections](/cases/t-mysql-too-many-connections) ｜ [实例无法启动](/cases/t-mysql-cannot-start)
