---
title: MySQL 进阶与高可用
description: 事务隔离级别与 MVCC、行锁/间隙锁/死锁、索引原理、EXPLAIN 实战、慢查询优化、binlog/redo/undo 日志、mysqldump/xtrabackup 备份、主从复制 GTID、MHA/MGR 高可用、读写分离
category: 数据
difficulty: 高级
---
# MySQL 进阶与高可用

::: tip 本篇定位
在 [MySQL 基础](./data-mysql) 之上，深入 **事务与隔离级别、MVCC、锁机制、索引原理、EXPLAIN 实战、慢查询优化**，掌握 **各类日志、备份恢复、主从复制（含 GTID）、高可用、读写分离中间件** 和运维排查。
:::

## 先建立全局观：一致性靠什么实现

MySQL 最核心的能力是**在并发下保证数据正确**。几个机制各有分工：

| 目标 | 靠什么 |
|---|---|
| 原子性（要么全做要么不做） | **undo log**（回滚） |
| 持久性（提交后不丢） | **redo log**（崩溃重放） |
| 隔离性（并发互不干扰） | **锁 + MVCC** |
| 最终目的：一致性 | 上面三者共同保证 |

---

## 一、事务与隔离级别

### 1.1 什么是事务

事务是一组 SQL 语句组成的逻辑单元，要么全部成功、要么全部失败回滚，遵循 **ACID**：

| 特性 | 含义 | 实现 |
|---|---|---|
| 原子性 Atomicity | 不可分割，失败全部回滚 | undo log |
| 一致性 Consistency | 事务前后数据完整、符合约束 | 其他三者共同保证 |
| 隔离性 Isolation | 并发事务相互隔离 | 锁、MVCC |
| 持久性 Durability | 提交后永久生效 | redo log |

### 1.2 并发带来的三个问题

| 问题 | 含义 |
|---|---|
| **脏读** | 一个事务读到了另一个事务**还没提交**的修改（对方可能回滚） |
| **不可重复读** | 同一事务内两次读同一行，结果不同（被其他事务 **UPDATE** 并提交） |
| **幻读** | 同一事务内两次条件查询，**行数不同**（被其他事务 INSERT/DELETE） |

### 1.3 四种隔离级别

| 隔离级别 | 脏读 | 不可重复读 | 幻读 |
|---|---|---|---|
| 读未提交 RU | 可能 | 可能 | 可能 |
| 读已提交 RC（Oracle 默认） | 避免 | 可能 | 可能 |
| **可重复读 RR（MySQL/InnoDB 默认）** | 避免 | 避免 | InnoDB 用 **Next-Key Lock** 很大程度避免 |
| 串行化 Serializable | 避免 | 避免 | 避免（读也加锁，并发最低） |

```sql
SELECT @@transaction_isolation;              -- 查看当前隔离级别
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
```

### 1.4 MVCC 多版本并发控制

**MVCC** 让普通 SELECT 在 RC/RR 下**不加锁、读快照**，从而读写不阻塞，是 InnoDB 高并发的关键。

它由三部分组成：

1. **隐藏列**：每行有 `DB_TRX_ID`（最后修改它的事务 ID）、`DB_ROLL_PTR`（指向 undo log 中的旧版本）、`DB_ROW_ID`；
2. **undo log 版本链**：每次修改把旧值写入 undo log，通过 roll_ptr 串成版本链；
3. **ReadView（读视图）**：生成时记录当前**活跃（未提交）事务 ID 列表 m_ids**、最小/最大事务 ID。

**可见性判断**：沿版本链，找第一个"对本 ReadView 可见"的版本——即该版本的 trx_id 已提交（不在 m_ids 中）。

::: tip RC 与 RR 的本质区别
- **RC（读已提交）**：**每次** SELECT 都生成新的 ReadView，所以能看到别人刚提交的（不可重复读）；
- **RR（可重复读）**：事务**第一次** SELECT 生成 ReadView 后**全程复用**，所以整个事务看到的数据一致。
:::

### 1.5 事务常用命令

```sql
START TRANSACTION;        -- 或 BEGIN
UPDATE accounts SET bal = bal - 100 WHERE id = 1;
UPDATE accounts SET bal = bal + 100 WHERE id = 2;
COMMIT;                   -- 提交
ROLLBACK;                 -- 回滚

SAVEPOINT sp1;            -- 保存点
ROLLBACK TO sp1;          -- 回滚到保存点
```

> DDL（CREATE/ALTER/DROP/TRUNCATE）会**隐式提交**且无法回滚；`autocommit` 默认开启，单条语句自动成事务。

---

## 二、锁机制

### 2.1 锁的分类

| 维度 | 类型 |
|---|---|
| 粒度 | 全局锁、表级锁、行级锁 |
| 模式 | 共享锁 S（读锁，可共存）、排他锁 X（写锁，互斥） |
| 态度 | 乐观锁（版本号/CAS，应用层）、悲观锁（数据库加锁） |

### 2.2 表级锁

- **表锁**：`LOCK TABLES t READ/WRITE`，开销小、并发低；
- **元数据锁 MDL**：访问表时自动加，防止查询中途表结构被改（常见"DDL 被长事务阻塞"）；
- **意向锁（IS/IX）**：表级，行加 S/X 锁前先在表上加意向锁，用于**快速判断表里是否有行被锁**，无需逐行检查；
- **AUTO-INC 锁**：自增插入时使用（`innodb_autoinc_lock_mode`）。

### 2.3 行级锁（InnoDB）

| 锁 | 锁定范围 |
|---|---|
| **记录锁 Record Lock** | 精确锁住某一条索引记录 |
| **间隙锁 Gap Lock** | 锁住索引记录之间的**间隙**（不含记录本身），防止插入，用于防幻读 |
| **临键锁 Next-Key Lock** | **记录锁 + 前面的间隙锁**（RR 默认行锁形式），左开右闭 |
| 插入意向锁 | INSERT 前在间隙加，与 Gap Lock 冲突 |

> 行锁是**加在索引上**的：若 UPDATE/DELETE 的条件**没走索引**，会锁全表所有行（等效表锁）。

### 2.4 锁定读

```sql
SELECT * FROM users WHERE id = 1 FOR UPDATE;          -- 加 X 排他锁
SELECT * FROM users WHERE id = 1 LOCK IN SHARE MODE;   -- 加 S 共享锁
-- 普通 SELECT 是非锁定读（MVCC 快照），不加锁
```

### 2.5 死锁

两个事务互相持有对方需要的锁、互相等待，即死锁。InnoDB 有**死锁检测（wait-for graph）**，发现后自动回滚**代价较小**的事务，另一个继续。

```sql
SHOW ENGINE INNODB STATUS\G     -- LATEST DETECTED DEADLOCK 段看死锁
```

**避免死锁：** 统一多表/多行的加锁顺序、缩短事务、保证走索引、降低隔离级别、应用侧重试。

---

## 三、索引原理

### 3.1 为什么用索引

索引类似书的目录，让数据库通过树快速定位，避免**全表扫描**，是空间换时间。索引大幅减少扫描行数和 IO。

### 3.2 B+ 树

InnoDB 索引用 **B+ 树**：

- 多路平衡、树**矮胖**（千万级数据通常 3-4 层），IO 次数少；
- 数据只在**叶子节点**，叶子之间用**双向链表**连接，天然支持**范围查询和排序**。

### 3.3 聚簇索引与二级索引

| 索引 | 叶子存 | 说明 |
|---|---|---|
| **聚簇索引** | 完整行数据 | 即主键，一张表一个 |
| **二级索引** | 主键值 | 取非索引列需**回表** |
| **覆盖索引** | — | 查询列都在索引中，免回表（Extra: Using index） |

### 3.4 索引类型与创建

主键、唯一、普通、联合、前缀、全文、函数索引。

```sql
CREATE INDEX idx_name ON users(name);
CREATE UNIQUE INDEX uk_email ON users(email);
CREATE INDEX idx_dept_age ON users(dept_id, age);   -- 联合索引
ALTER TABLE users ADD INDEX idx_phone(phone);
SHOW INDEX FROM users;
DROP INDEX idx_name ON users;
```

**联合索引最左前缀**：`(a,b,c)` 可用于 a、a,b、a,b,c；范围查询右侧列失效。

### 3.5 索引下推 ICP

5.6 引入**索引条件下推（ICP）**：把部分 WHERE 条件在存储引擎层用索引判断，减少回表次数（Extra: Using index condition）。

### 3.6 索引失效

- 索引列用函数/运算/隐式类型转换（字符串列传数字）；
- `LIKE '%xx'`（前导通配符）；
- 联合索引不满足最左前缀；
- OR 连接的列无索引；
- 字符集隐式不一致。

**设计原则：** 高频 WHERE/JOIN/排序列、区分度高、联合索引等值/高频列在前、控制索引数量。

---

## 四、EXPLAIN 执行计划

### 4.1 基本用法

```sql
EXPLAIN SELECT * FROM users WHERE dept_id = 1;
EXPLAIN FORMAT=JSON SELECT ...;     -- 更详细
```

### 4.2 关键字段

| 字段 | 关注点 |
|---|---|
| id | 越大越先执行，相同从上到下 |
| select_type | SIMPLE/PRIMARY/SUBQUERY/DERIVED |
| table / partitions | 表 / 分区 |
| **type** | 访问类型（见下） |
| possible_keys / key | 可能用 / 实际用的索引（key=NULL 没用索引） |
| key_len | 索引使用长度（判断联合索引用了几列） |
| ref | 索引比较来源 |
| **rows** | 预估扫描行数（越大越差） |
| filtered | 过滤后剩余百分比 |
| **Extra** | 附加信息（见下） |

### 4.3 type 从好到差

```
system > const > eq_ref > ref > fulltext > ref_or_null
> index_merge > unique_subquery > range > index > ALL
```

- `const`：主键/唯一等值，最多一行；
- `eq_ref`：联表用主键/唯一索引，最多匹配一行；
- `ref`：普通索引等值；
- `range`：索引范围（between/in/>）；
- `index`：扫描整棵索引树；
- **`ALL`：全表扫描，必须优化**。

### 4.4 Extra 重点

| 值 | 含义 |
|---|---|
| Using index | 覆盖索引，好 |
| Using where | 服务层再过滤 |
| Using index condition | 索引下推 ICP |
| **Using filesort** | 额外排序（需优化） |
| **Using temporary** | 用临时表（常见 group by/distinct，需优化） |
| Using join buffer | 联表没用上索引、用缓冲 |

### 4.5 SHOW PROFILE

```sql
SET profiling = 1;
SELECT ...;
SHOW PROFILES;
SHOW PROFILE FOR QUERY 1;     -- 看每一步耗时（8.0 推荐用 performance_schema）
```

---

## 五、慢查询与优化

### 5.1 开启慢查询日志

```sql
SET GLOBAL slow_query_log = ON;
SET GLOBAL long_query_time = 1;                     -- 超 1 秒记录
SET GLOBAL log_queries_not_using_indexes = ON;
SHOW VARIABLES LIKE 'slow_query_log_file';
```

永久写 my.cnf：`slow_query_log=1`、`long_query_time=1`。

### 5.2 分析

```bash
mysqldumpslow -s t -t 10 *-slow.log     # -s: t 时间 / r 行数 / c 次数，-t Top
```

### 5.3 优化思路

EXPLAIN 定位 → 加/调索引、覆盖索引 → 避免 `SELECT *` → 优化联表（小表驱动大表、加索引）→ 深分页优化（`WHERE id > x LIMIT n` 或延迟关联）→ 必要时缓存、读写分离。

---

## 六、MySQL 日志

### 6.1 日志总览

| 日志 | 作用 |
|---|---|
| 错误日志 log_error | 启动/运行/关闭的错误（排查启动问题首选） |
| 通用查询日志 general_log | 所有到达的语句（量大，默认关） |
| 慢查询日志 | 超时语句 |
| **binlog** | Server 层，记录所有更改，用于复制和 PITR |
| **redo log** | InnoDB 引擎层，崩溃恢复（物理日志，循环写） |
| **undo log** | 回滚、MVCC |
| relay log | 从库中转主库 binlog |

### 6.2 binlog

```sql
SHOW VARIABLES LIKE 'log_bin';
SHOW BINARY LOGS;
SHOW MASTER STATUS;
```

- 三种格式：`STATEMENT`（记 SQL）、`ROW`（记行变更，**默认/推荐**）、`MIXED`；
- 只在事务**提交时**写一次；
- 过期清理：`binlog_expire_logs_seconds`。

### 6.3 redo 与 binlog 的区别

| 对比 | redo log | binlog |
|---|---|---|
| 层 | InnoDB 引擎层 | Server 层（所有引擎） |
| 内容 | 物理日志（某页某偏移改成什么） | 逻辑日志（语句/行变更） |
| 方式 | **循环写**（固定大小、覆盖） | **追加写**（多个文件） |
| 用途 | 崩溃恢复 | 复制、归档、PITR |

二者通过 **两阶段提交**（先 prepare 写 redo，再写 binlog，最后 commit）保证一致。

---

## 七、备份与恢复

### 7.1 备份分类

逻辑（SQL 语句）/ 物理（拷贝文件）；热备/温备/冷备；全量/增量/差异。

### 7.2 mysqldump（逻辑，中小库）

```bash
# 备份
mysqldump -u root -p appdb > appdb.sql
mysqldump -u root -p -B appdb > appdb.sql       # -B 含建库
mysqldump -u root -p -A > all.sql               # 全库
# InnoDB 一致性热备 + 记录 binlog 位点 + 含存储过程/事件
mysqldump -u root -p --single-transaction --source-data=2 \
  --routines --triggers --events -A > all.sql

# 恢复
mysql -u root -p appdb < appdb.sql
```

### 7.3 XtraBackup（物理热备，大库）

```bash
xtrabackup --backup --user=root --password=x --target-dir=/backup/full   # 备份
xtrabackup --prepare --target-dir=/backup/full                          # 准备
# 停库、清空数据目录后：
xtrabackup --copy-back --target-dir=/backup/full
chown -R mysql:mysql /var/lib/mysql
# 增量：--incremental-dir / --incremental-basedir
```

> XtraBackup 不支持 MariaDB 的部分版本特性，MariaDB 物理备份可用其官方 mariabackup。

### 7.4 binlog 时间点恢复（PITR）

全量恢复后，重放全量位点之后的 binlog：

```bash
mysqlbinlog --start-position=156 --stop-datetime="2026-09-27 10:00:00" \
  binlog.000002 | mysql -u root -p
```

### 7.5 备份策略

**定期全量（每日/每周）+ 持续保留 binlog**，配合 crontab 自动执行、备份异地存放、定期做恢复演练（能恢复才算有效备份）。

---

## 八、主从复制

### 8.1 原理（三个线程）

```
主库：写 binlog；binlog dump 线程把变更推给从库
从库 IO 线程：拉取 binlog 写入 relay log
从库 SQL 线程：读取 relay log 重放
```

### 8.2 传统位点搭建

**主库 my.cnf：**

```ini
[mysqld]
server-id=1
log-bin=mysql-bin
binlog_format=row
```

```sql
CREATE USER 'repl'@'10.0.0.%' IDENTIFIED BY 'Repl@123';
GRANT REPLICATION SLAVE ON *.* TO 'repl'@'10.0.0.%';
SHOW MASTER STATUS;
```

**从库：**

```sql
CHANGE MASTER TO
  MASTER_HOST='10.0.0.13', MASTER_PORT=3306,
  MASTER_USER='repl', MASTER_PASSWORD='Repl@123',
  MASTER_LOG_FILE='mysql-bin.000001', MASTER_LOG_POS=156;
START SLAVE;
SHOW SLAVE STATUS\G
-- IO_Running=Yes、SQL_Running=Yes、Seconds_Behind_Master
```

### 8.3 GTID 方式（推荐）

```ini
gtid_mode=ON
enforce_gtid_consistency=ON
log_slave_updates=ON
```

```sql
CHANGE MASTER TO MASTER_HOST='10.0.0.13', MASTER_USER='repl',
  MASTER_PASSWORD='Repl@123', MASTER_AUTO_POSITION=1;
START SLAVE;
```

GTID 为每个事务分配全局唯一 ID，无需手工对位、切换更简单可靠。

### 8.4 半同步复制

默认异步（主不等从，宕机可能丢）。半同步：主库至少等一个从库确认收到 binlog 才返回（插件 `rpl_semi_sync_master/slave`），提升安全，超时自动退化为异步。

### 8.5 复制过滤与并行复制

- 过滤：`replicate-do-db`、`replicate-ignore-table`（主库 binlog-do-db）；
- 并行复制：`slave_parallel_workers`、基于 WRITESET/LOGICAL_CLOCK，降低主从延迟。

### 8.6 常见问题

| 现象 | 处理 |
|---|---|
| IO/SQL 线程 No | Last_IO/Last_Error；网络、账号、位点 |
| 1062 主键冲突 / 1236 找不到日志 | 核对位点/GTID，手动跳过或重建 |
| 主从延迟 | 大事务拆分、从库性能、并行复制 |
| 数据不一致 | pt-table-checksum 校验、pt-table-sync 修复 |

---

## 九、高可用方案

| 方案 | 说明 |
|---|---|
| MMM | 早期主主+VIP 管理，已淘汰 |
| **MHA** | Manager+Node：主故障选数据最新的从、补全 binlog、提升为新主、重定向其他从 |
| **MGR** | 官方组复制，基于 Paxos（XCom），单主/多主，成员自动协调、故障自动切换 |
| InnoDB Cluster | MGR + MySQL Router + Shell 官方完整方案 |
| Galera / PXC | 同步多主写、强一致（PXC=Percona XtraDB Cluster） |
| Orchestrator | 拓扑管理、自动故障切换 |

**故障切换流程：** 检测主故障 → 选数据最新从库（位点/GTID 最高）→ 提升新主 → 其他从库改指新主 → VIP/路由（ProxySQL/Router）切换 → 应用恢复。

::: tip 选型建议
- 个人/小项目：一主一从 + 备份 + 脚本切换即可；
- 自动高可用：MGR（官方）或 Orchestrator + ProxySQL；
- 云上：直接用 RDS，自带高可用，成本换省心。
:::

---

## 十、读写分离与分库分表

### 10.1 为什么需要中间件

单机容量/连接数到顶后，需要读写分离（写主读从）和分库分表（水平扩展）。

### 10.2 垂直与水平切分

| 切分 | 说明 |
|---|---|
| 垂直分库 | 按业务拆库（用户库、订单库） |
| 垂直分表 | 把不常用/大字段拆到扩展表 |
| 水平分库/分表 | 按分片键（用户 ID 取模/范围）把同一张表的数据分散 |

水平切分带来的问题：跨库 JOIN、分布式事务、全局唯一 ID（雪花/号段）、跨库排序分页、数据迁移扩容。

### 10.3 常用中间件

| 中间件 | 特点 |
|---|---|
| MyCat | server.xml（用户）、schema.xml（逻辑表/节点）、rule.xml（分片规则）；社区已不活跃 |
| **ProxySQL** | 高性能代理，读写分离、查询路由、连接池、查询缓存、故障感知 |
| **ShardingSphere** | JDBC（嵌入）/ Proxy（独立部署），分库分表 + 读写分离，活跃 |

---

## 十一、运维与排查

### 11.1 连接

```sql
SHOW VARIABLES LIKE 'max_connections';
SHOW STATUS LIKE 'Threads_connected';
SHOW STATUS LIKE 'Threads_running';
SHOW FULL PROCESSLIST;
```

`Too many connections`：调大 max_connections、排查连接泄漏、应用用连接池、缩短 wait_timeout。

### 11.2 锁与事务排查

```sql
SELECT * FROM information_schema.innodb_trx;
SELECT * FROM performance_schema.data_locks;
SELECT * FROM sys.innodb_lock_waits;
SHOW ENGINE INNODB STATUS\G
```

### 11.3 常用 SHOW

```sql
SHOW STATUS LIKE 'Slow_queries';
SHOW VARIABLES LIKE 'innodb_buffer_pool_size';
SHOW GLOBAL STATUS LIKE 'Innodb_row_lock%';
```

### 11.4 常见故障速查

| 现象 | 方向 |
|---|---|
| 启动失败 | error log；my.cnf 语法、数据目录权限 |
| 突然变慢 | 慢查询、锁等待、连接打满、IO/CPU、索引失效 |
| 锁等待/业务卡住 | 长事务未提交、更新无索引锁全表 |
| 主从延迟/中断 | 见 8.6 |

---

## 面试自测

1. ACID 中原子性、持久性、隔离性分别靠什么实现？
2. 脏读、不可重复读、幻读的区别？MySQL 默认隔离级别是什么，如何解决幻读？
3. 讲讲 MVCC 的原理，RC 和 RR 下 ReadView 生成有何不同？
4. 什么是 Next-Key Lock？为什么 UPDATE 没走索引会锁全表？
5. B+ 树为什么适合做索引？聚簇索引和二级索引、回表、覆盖索引是什么？
6. EXPLAIN 中 type 和 Extra 哪些值需要警惕？
7. redo log、undo log、binlog 各有什么作用？redo 和 binlog 有什么区别？
8. mysqldump --single-transaction 为什么能保证 InnoDB 一致性？
9. 主从复制的三个线程和流程？GTID 相比传统位点有什么优势？
10. 水平分库分表会带来哪些问题，怎么解决？

## 相关速查

- [MySQL 基础](./data-mysql)
- [Linux 命令速查](/reference/linux-commands)
- MySQL 8.0 文档：https://dev.mysql.com/doc/refman/8.0/en/
- XtraBackup：https://docs.percona.com/percona-xtrabackup/
- ProxySQL：https://proxysql.com/documentation/
- ShardingSphere：https://shardingsphere.apache.org/document/current/cn/overview/
