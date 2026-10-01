---
category: 数据
difficulty: 初级
date: 2023-04-19
---

# MySQL 连接数打满 Too many connections（2023-04-19）

## 现象

线上 MySQL 突然拒绝所有新连接，业务侧大量报错：

```text
ERROR 1040 (08004): Too many connections
```

监控上连接数曲线从平时的 80 多突然冲到上限，随后雪崩——所有依赖该库的服务都拿不到连接。

## 环境

| 组件 | 版本 / 配置 |
|---|---|
| 操作系统 | Rocky Linux 8.6 |
| MySQL | 8.0.32 |
| `max_connections` | 151（默认值，从未调整） |
| 应用侧 | Spring Boot HikariCP 连接池 × 12 个服务实例 |
| 部署 | 单机 + ProxySQL 中间层 |

## 定位过程

### 1. 先确认连接数确实到顶

此时新连接进不来，但**已有的管理员连接还能进**（MySQL 保留 `super` 预留连接）。用高权限账号登录：

```sql
SHOW VARIABLES LIKE 'max_connections';
SHOW GLOBAL STATUS LIKE 'Threads_connected';
SHOW GLOBAL STATUS LIKE 'Max_used_connections';
```

输出：

```text
max_connections        = 151
Threads_connected      = 151     -- 已经打满
Max_used_connections   = 151
```

### 2. 看连接都被谁占着

```sql
-- 按来源 IP / 用户聚合当前连接数
SELECT
  SUBSTRING_INDEX(host, ':', 1) AS client_ip,
  user,
  COUNT(*) AS conn_cnt
FROM information_schema.PROCESSLIST
GROUP BY client_ip, user
ORDER BY conn_cnt DESC;
```

结果：

```text
client_ip      user      conn_cnt
10.0.9.31      app_rw    68     -- 某个应用实例占了 68 个
10.0.9.32      app_rw    62
10.0.9.35      app_rw    19
```

单个应用实例开了 68 个连接，远超其连接池配置（原本应该是每个实例 10 个）。

### 3. 看这些连接在干嘛

```sql
SELECT ID, USER, HOST, DB, COMMAND, TIME, STATE, INFO
FROM information_schema.PROCESSLIST
ORDER BY TIME DESC LIMIT 20;
```

关键发现：

```text
COMMAND  TIME   STATE                INFO
Sleep    1823   --                   NULL     -- 大量 Sleep 连接，闲置 30 分钟以上
Sleep    1790   --                   NULL
Query    120    Sending data         SELECT * FROM big_table ...
```

- 大量 `COMMAND=Sleep` 的**睡眠连接**，`TIME` 长达上千秒：连接池借出去没还。
- 个别 `Query` 跑了 120s 的慢 SQL，一直占着连接不释放。

### 4. 核对应用连接池配置

应用侧 HikariCP 期望每实例 `maximum-pool-size=10`、`max-lifetime=30min`。12 个实例 × 10 = 120，理论上不该超过 151。但 `max-lifetime=30min` 远大于 MySQL 侧的 `wait_timeout`，连接被服务端单方面断开后连接池还以为有效，复用时报错重建——叠加慢 SQL 占用，最终把池打爆。

## 根因

| 层级 | 说明 |
|---|---|
| 直接原因 | `max_connections=151`（默认值）过小，12 个应用实例的连接池 + 慢 SQL 占满了连接 |
| 诱因 1 | 连接池 `max-lifetime` 与 MySQL `wait_timeout` 不匹配，产生大量失效连接重连 |
| 诱因 2 | 慢 SQL / 大事务长时间持有连接不释放 |
| 流程因素 | 上线时从未评估连接容量，用的还是默认 151 |

## 解决步骤

### 止血

1. 立刻 Kill 掉长时间 Sleep 的闲置连接，腾出席位：

```sql
-- 批量 kill Sleep 超过 600s 的连接（生成 kill 语句）
SELECT GROUP_CONCAT(CONCAT('KILL ', ID, ';') SEPARATOR ' ')
FROM information_schema.PROCESSLIST
WHERE COMMAND = 'Sleep' AND TIME > 600;
-- 把上面输出的语句复制出来执行
```

2. 临时调大连接数（动态生效，无需重启）：

```sql
SET GLOBAL max_connections = 500;
```

### 根治

1. 把 `max_connections` 写进配置文件持久化：

```ini
# my.cnf
max_connections = 1000
# 合理设置超时，主动回收闲置连接
wait_timeout = 300
interactive_timeout = 300
```

> 估算公式：`max_connections ≈ 应用实例数 × 单实例池大小 + 预留 20%`。注意连接数过大会推高内存，每个连接约占线程栈内存，需结合 `innodb_buffer_pool` 一起算。

2. 对齐连接池与服务端超时，连接池的 `max-lifetime` 必须**小于**服务端 `wait_timeout`：

```yaml
spring:
  datasource:
    hikari:
      maximum-pool-size: 15      # 收敛每实例连接数
      max-lifetime: 240000       # 4min < wait_timeout 300s，提前回收
      keepalive-time: 120000     # 2min 探活
```

3. 治理慢 SQL（见 [慢查询排查](/cases/t-mysql-slow-query)），避免长事务占连接。

## 验证与预防

```sql
-- 观察连接数是否平稳
SHOW GLOBAL STATUS LIKE 'Threads_connected';
SHOW STATUS LIKE 'Aborted_clients';   -- 异常断连数应下降
```

- 监控：对 `Threads_connected / max_connections` 利用率配告警（>80% 预警）。
- 容量：扩容应用实例时同步核算数据库连接预算。
- 规范：禁止在事务里做 RPC/外部调用，避免长事务占连接。

## 相关

- 命令速查：[Linux 命令速查](/reference/linux-commands)
- 同组短文：[慢查询排查](/cases/t-mysql-slow-query) ｜ [主从复制延迟](/cases/t-mysql-replica-lag) ｜ [实例无法启动](/cases/t-mysql-cannot-start)
