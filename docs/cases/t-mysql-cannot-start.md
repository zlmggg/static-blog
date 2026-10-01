---
category: 数据
difficulty: 高级
date: 2022-12-05
---

# MySQL 实例无法启动（2022-12-05）

## 现象

服务器例行重启后，MySQL 起不来，`systemctl start mysqld` 一直失败：

```text
Job for mysqld.service failed because the control process exited with error code.
"systemctl status mysqld.service" and "journalctl -xe" for details.
```

尝试手动前台启动看报错：

```bash
mysqld --user=mysql
```

```text
2022-12-05T03:12:44Z [ERROR] InnoDB: Database page corruption on disk or a failed
  file read of page [page id: space=83, page number=5]. You may have to recover
  from a backup.
2022-12-05T03:12:44Z [ERROR] InnoDB: Plugin initialization aborted with error
  Generic error
2022-12-05T03:12:44Z [ERROR] Plugin 'InnoDB' init function returned error.
2022-12-05T03:12:44Z [ERROR] Plugin 'InnoDB' registration as a STORAGE ENGINE failed.
2022-12-05T03:12:44Z [ERROR] Failed to initialize builtin plugins.
2022-12-05T03:12:44Z [ERROR] Aborting
```

## 环境

| 组件 | 版本 / 配置 |
|---|---|
| 操作系统 | CentOS 7.9 |
| MySQL | 8.0.31 |
| 数据目录 | `/var/lib/mysql`（单独挂载盘） |
| 触发事件 | 凌晨服务器异常掉电后重启 |
| 存储引擎 | InnoDB，单实例 |

## 定位过程

### 1. 先分清是哪一类"起不来"

按这个顺序逐个排除：

| 可能原因 | 检查命令 |
|---|---|
| pid/socket 文件残留 | `ls -l /var/lib/mysql/*.pid /tmp/mysql.sock` |
| 数据目录权限 | `ls -ld /var/lib/mysql`，`chown mysql:mysql` |
| 配置文件语法 | `mysqld --verbose --help >/dev/null` 或看 error log |
| InnoDB 崩溃恢复失败 | 看 error log 里 `[ERROR] InnoDB` |
| 端口被占 | `ss -tlnp | grep 3306` |

本次 error log 明确指向 **InnoDB 页损坏**，属于掉电后的崩溃恢复失败。

### 2. 确认 pid / socket / 端口这些低级问题

```bash
# 残留 pid 会导致 mysqld 以为已在运行
cat /var/lib/mysql/*.pid
ss -tlnp | grep 3306
# socket 文件是否存在、属主对不对
ls -l /tmp/mysql.sock
```

本次这些都正常，排除低级问题。

### 3. 读 error log 全文

```bash
# 找到错误日志位置
grep -r "log-error" /etc/my.cnf /etc/my.cnf.d/
tail -200 /var/log/mysqld.log
```

关键行（见现象）：InnoDB 在做崩溃恢复时读到坏页 `space=83, page=5`，恢复直接 abort。

### 4. 用 innodb_force_recovery 强制拉起

InnoDB 提供 1~6 级强制恢复等级，数字越大越"暴力"。先从低等级试：

```ini
# /etc/my.cnf
[mysqld]
innodb_force_recovery = 1
```

```bash
systemctl start mysqld
```

逐档往上加（1→2→3→4→5→6），哪一档能起来就停在哪档：

| 等级 | 行为 | 风险 |
|---|---|---|
| 1~2 | 忽略坏页、暂停 insert buffer 合并 | 低 |
| 3 | 崩溃恢复后不做回滚 | 中 |
| 4 | 不做插入缓冲合并、不统计行数 | 高，可能永久损坏数据 |
| 5~6 | 不看 undo / 跳过 redo，强行认为已一致 | 最高，数据可能不一致 |

> 原则：**能用 1 起来就别用 6**。force_recovery ≥ 4 后基本等于放弃部分数据一致性。本次在 `=4` 时成功拉起。

## 根因

| 层级 | 说明 |
|---|---|
| 直接原因 | 服务器异常掉电，redo log / 数据页未刷盘一致，正常崩溃恢复遇到坏页失败 |
| 诱因 | 数据盘 IO 在掉电时没有写缓存保护（无 UPS / 电池） |
| 管理因素 | 没有可用的物理备份，只能靠强制恢复硬拉 |

## 解决步骤

### 止血（强制拉起 + 导出数据）

1. 设 `innodb_force_recovery=4` 拉起实例后，**第一件事是导出数据**，不要继续跑业务：

```bash
# 逻辑备份全部库（force_recovery 状态下实例只读，赶紧 dump）
mysqldump --single-transaction --routines --triggers --events \
  --all-databases > /backup/full_$(date +%F).sql
```

2. 导出成功后，**去掉 force_recovery**，重建干净实例：

```ini
# my.cnf 里删掉/注释掉 innodb_force_recovery
# innodb_force_recovery = 4
```

```bash
# 停库，清空数据目录（确认备份已就绪！）
systemctl stop mysqld
mv /var/lib/mysql /var/lib/mysql.bad
mkdir /var/lib/mysql
chown mysql:mysql /var/lib/mysql
# 初始化后重启，再导入备份
mysqld --initialize --user=mysql
systemctl start mysqld
mysql < /backup/full_2022-12-05.sql
```

### 根治

1. 核对磁盘可靠性：确认是否有 RAID 卡电池 / UPS，避免再次掉电丢数据。
2. 建立**定期物理备份**（xtrabackup）+ binlog 增量备份，验证可恢复性。

## 验证与预防

```sql
-- 实例正常起来后，确认 InnoDB 状态健康
SHOW ENGINE INNODB STATUS\G   -- 无 corrupt 报错
CHECK TABLE 关键业务表;
```

- 监控：配置 MySQL 存活 + 主从延迟告警；备份成功率告警。
- 规范：生产库必须有至少一份异地可恢复备份，并定期做恢复演练。
- 运维：内核参数 `vm.dirty_ratio` 合理设置，配合 RAID 掉电保护。

## 相关

- 命令速查：[Linux 命令速查](/reference/linux-commands)
- 同组短文：[主从复制延迟](/cases/t-mysql-replica-lag) ｜ [连接数打满](/cases/t-mysql-too-many-connections) ｜ [慢查询排查](/cases/t-mysql-slow-query)
