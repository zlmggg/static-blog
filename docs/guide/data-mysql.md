---
title: MySQL 基础
description: 关系型数据库与范式、MySQL/MariaDB 多种安装与安全初始化、SQL 增删改查/联表/聚合/函数、用户权限、数据类型、视图/存储过程/触发器、InnoDB 存储引擎
---

# MySQL 基础

::: tip 本篇定位
从零开始：理解**关系型数据库与三大范式**，用多种方式安装 MySQL/MariaDB 并完成安全初始化，扎实掌握 **SQL 增删改查、联表、聚合、常用函数**，管理用户权限，会写**视图、存储过程、触发器**，最后理解 **InnoDB 存储引擎**。
索引优化、事务隔离/MVCC、备份恢复、主从高可用见 [MySQL 进阶](./data-mysql-advanced)。
:::

## 先建立全局观：一条 SQL 的一生

MySQL 是**单进程多线程**的数据库。一条查询语句从发出到返回，大致经历：

```
客户端 → 连接器(认证/授权) → 查询缓存(8.0已移除) → 解析器(词法/语法)
       → 优化器(选索引/决定执行顺序) → 执行器(调用存储引擎接口)
       → 存储引擎(InnoDB,读写数据页) → 返回结果
```

记住这个流程，后面的索引、EXPLAIN、慢查询都是在这条链路的某个环节做文章。

---

## 一、数据库基础

### 1.1 什么是数据库

- **数据（Data）**：描述事物的符号记录；
- **数据库（DB）**：长期存储在计算机内、有组织、可共享的大量数据集合；
- **数据库管理系统（DBMS）**：位于用户和操作系统之间、专门用于管理数据库的软件（MySQL、Oracle 就是 DBMS）；
- **数据库系统（DBS）** = 数据库 + DBMS + 应用 + 管理员（DBA）。

### 1.2 关系型数据库

关系型数据库把数据组织成**二维表（Table）**：

- 一行称为一条**记录（Record / 元组）**，一列称为一个**字段（Field / 属性）**；
- 表与表之间通过**主键、外键**建立关系；
- 使用 **SQL（结构化查询语言）** 操作；
- 强调事务，遵循 **ACID**：原子性（Atomicity）、一致性（Consistency）、隔离性（Isolation）、持久性（Durability）。

### 1.3 E-R 模型（设计数据库的工具）

设计表之前先用 **实体 - 联系（E-R）模型**抽象现实：

| 概念 | 说明 | 例子 |
|---|---|---|
| 实体 Entity | 客观存在并可区分的事物 | 学生、课程 |
| 属性 Attribute | 实体的特征 | 学号、姓名 |
| 联系 Relationship | 实体间的关联 | 学生"选修"课程 |

三种联系：**一对一（1:1）**、**一对多（1:N）**、**多对多（M:N）**。多对多（如学生选课）在数据库中要拆成一张中间表（选课表），用两个一对多实现。

### 1.4 关系型数据库的三大范式

范式是设计表结构时要遵循的规范，目的是**减少数据冗余、避免插入/更新/删除异常**。

| 范式 | 核心要求 | 通俗理解 |
|---|---|---|
| **第一范式 1NF** | 每个字段都是**不可再分的原子值** | 一个格子里不能塞"电话1,电话2"，也不能有重复的组 |
| **第二范式 2NF** | 在 1NF 基础上，非主属性必须**完全依赖**主键（消除部分依赖） | 联合主键时，字段不能只依赖主键的一部分 |
| **第三范式 3NF** | 在 2NF 基础上，消除**传递依赖**（非主属性不依赖其他非主属性） | 学生表里不能同时存"学院编号 + 学院名称 + 学院电话"，学院信息应单独建表 |

> 实际工程中通常做到 **3NF** 即可；有时为了查询性能会**故意反范式**（适当冗余，如订单里存商品快照名），这是规范与性能的权衡。

### 1.5 MySQL 体系结构（逻辑分层）

| 层 | 组件 | 职责 |
|---|---|---|
| 连接层 | 连接池、线程处理 | 认证、权限校验、为每个连接分配线程 |
| 服务层 | SQL 接口、解析器、优化器 | 解析 SQL、生成执行计划（8.0 移除查询缓存） |
| 存储引擎层 | InnoDB、MyISAM 等 | **插件式**，负责数据的存储和提取 |
| 文件系统层 | 数据文件、日志 | 落盘（redo/undo/binlog、表空间） |

### 1.6 MySQL 与 MariaDB、版本

- MySQL 当前主流为 **8.0**；**8.4 为 LTS（长期支持）**；9.x 为创新版（版本号奇数）；
- **MariaDB** 是 MySQL 原作者主导的开源分支，命令、配置、SQL 基本兼容，开源更彻底；**11.4 为 LTS**；
- 本服务器实际使用 **MariaDB 11.4**，下文两者命令一致处会合并说明，差异处单独标注。

---

## 二、安装与初始化

### 2.1 方式一：RHEL/Rocky 安装官方 MySQL

```bash
# 安装官方 yum 仓库（默认启用 8.0）
sudo dnf install -y https://dev.mysql.com/get/mysql80-community-release-el9-1.noarch.rpm
sudo dnf install -y mysql-community-server
sudo systemctl enable --now mysqld

# MySQL 8.0 首次启动会在日志里生成一个随机临时密码
sudo grep 'temporary password' /var/log/mysqld.log
# [Note] A temporary password is generated for root@localhost: xj?k9!pQ...
```

### 2.2 方式二：RHEL / Ubuntu 安装 MariaDB（本服务器方案）

```bash
# RHEL/Rocky
sudo dnf install -y mariadb-server
sudo systemctl enable --now mariadb

# Debian/Ubuntu
sudo apt update && sudo apt install -y mariadb-server
sudo systemctl enable --now mariadb
```

### 2.3 方式三：Debian/Ubuntu 安装 MySQL

```bash
sudo apt update && sudo apt install -y mysql-server
sudo systemctl enable --now mysql
```

### 2.4 方式四：二进制包（版本可控，生产常用）

```bash
# 从 https://dev.mysql.com/downloads/mysql/ 下载 Linux - Generic 二进制包
tar -xJf mysql-8.0.42-linux-glibc2.17-x86_64.tar.xz -C /usr/local/
ln -s /usr/local/mysql-8.0.42-linux-glibc2.17-x86_64 /usr/local/mysql
groupadd mysql && useradd -r -g mysql -s /sbin/nologin mysql
cd /usr/local/mysql
mkdir mysql-files && chown mysql:mysql mysql-files
bin/mysqld --initialize --user=mysql        # 初始化，末尾打印 root 临时密码
cp support-files/mysql.server /etc/init.d/mysql
```

### 2.5 方式五：Docker（版本锁定）

```bash
docker run -d --name mysql \
  -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=Root@123 \
  -v /data/mysql:/var/lib/mysql \
  mysql:8.0.42

# MariaDB（本服务器锁定版本）
docker run -d --name mariadb \
  -p 3306:3306 \
  -e MARIADB_ROOT_PASSWORD=Root@123 \
  -v /data/mysql:/var/lib/mysql \
  mariadb:11.4.13
```

### 2.6 安全初始化（必做）

```bash
sudo mysql_secure_installation
```

按提示逐项完成：

1. 输入 root 当前密码（官方 MySQL 用临时密码；MariaDB 本机 root 常为空，直接回车）；
2. **切换到 unix_socket 认证 / 设置 root 密码**；
3. **删除匿名用户**（Remove anonymous users）→ 选 Y；
4. **禁止 root 远程登录**（Disallow root login remotely）→ 选 Y；
5. **删除 test 测试库**（Remove test database）→ 选 Y；
6. **刷新权限表**（Reload privilege tables）→ 选 Y。

### 2.7 登录与退出

```bash
sudo mysql -u root -p                 # 本机登录（-p 后回车再输密码）
mysql -h 10.0.0.13 -P 3306 -u app -p  # 远程登录
```

```sql
MariaDB [(none)]> SELECT VERSION(), USER(), NOW();
MariaDB [(none)]> SHOW DATABASES;
MariaDB [(none)]> exit;
```

::: warning MySQL 8.0 认证插件
8.0 默认认证插件是 `caching_sha2_password`，老版本 Navicat 等客户端可能报无法连接。可对某用户改回旧插件：
```sql
ALTER USER 'root'@'%' IDENTIFIED WITH mysql_native_password BY 'Root@123';
FLUSH PRIVILEGES;
```
:::

---

## 三、SQL 基础

### 3.1 SQL 的分类

| 分类 | 全称 | 关键字 | 作用 |
|---|---|---|---|
| DDL | 数据定义语言 | CREATE / ALTER / DROP / TRUNCATE | 定义库、表结构 |
| DML | 数据操纵语言 | INSERT / UPDATE / DELETE | 增删改数据 |
| DQL | 数据查询语言 | SELECT | 查询数据 |
| DCL | 数据控制语言 | GRANT / REVOKE | 权限控制 |

### 3.2 库操作（DDL）

```sql
CREATE DATABASE IF NOT EXISTS appdb
  DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
SHOW DATABASES;
USE appdb;
SELECT DATABASE();                 -- 查看当前所在库
DROP DATABASE IF EXISTS appdb;
```

### 3.3 表操作（DDL）

```sql
CREATE TABLE users (
    id      INT PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
    name    VARCHAR(50) NOT NULL COMMENT '姓名',
    age     TINYINT UNSIGNED DEFAULT 0,
    email   VARCHAR(100) UNIQUE,
    dept_id INT,
    created DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';
```

常用约束：`PRIMARY KEY`（主键，唯一非空）、`AUTO_INCREMENT`（自增）、`NOT NULL`（非空）、`UNIQUE`（唯一）、`DEFAULT`（默认值）、`COMMENT`（注释）。

```sql
SHOW TABLES;
DESC users;                       -- 查看表结构
SHOW CREATE TABLE users\G         -- 查看完整建表语句
ALTER TABLE users ADD COLUMN phone VARCHAR(20) AFTER name;   -- 加列
ALTER TABLE users MODIFY age INT;                            -- 改列类型
ALTER TABLE users CHANGE phone mobile VARCHAR(30);           -- 改列名和类型
ALTER TABLE users DROP COLUMN mobile;                        -- 删列
ALTER TABLE users RENAME TO t_users;                         -- 改表名
DROP TABLE t_users;
```

### 3.4 插入数据（DML）

```sql
-- 插入单条
INSERT INTO users (name, age, email, dept_id)
VALUES ('tom', 20, 'tom@x.com', 1);

-- 一次插入多条（推荐，比循环单条快）
INSERT INTO users (name, age, dept_id)
VALUES ('jack', 22, 1), ('lily', 25, 2), ('rose', 23, 2);

-- 列与 select 结果一致时，可从其他表复制
INSERT INTO users_bak SELECT * FROM users;
```

### 3.5 更新与删除（DML）

```sql
UPDATE users SET age = 21 WHERE id = 1;
UPDATE users SET age = age + 1 WHERE dept_id = 1;
DELETE FROM users WHERE id = 4;
```

::: danger UPDATE / DELETE 必须带 WHERE
不带 WHERE 会修改/删除**整张表**。生产操作前先 `SELECT` 确认范围：
```sql
SELECT * FROM users WHERE dept_id = 1;   -- 先看会影响哪些行
```
`TRUNCATE TABLE users;` 是 DDL：清空整表、不可回滚、自增归零，与逐行 DELETE 机制不同。
:::

### 3.6 基础查询（DQL）

```sql
SELECT * FROM users;
SELECT name, age FROM users;
SELECT name AS 姓名, age 年龄 FROM users;     -- AS 起别名（可省略）
```

**条件 WHERE：**

```sql
SELECT * FROM users WHERE age >= 20;
SELECT * FROM users WHERE age BETWEEN 20 AND 25;     -- 区间（含边界）
SELECT * FROM users WHERE dept_id IN (1, 2);
SELECT * FROM users WHERE name LIKE '张%';           -- % 任意多个，_ 单个
SELECT * FROM users WHERE email IS NULL;             -- 判空用 IS NULL，不能用 = NULL
SELECT * FROM users WHERE age >= 20 AND dept_id = 1;
```

**排序、分页、去重：**

```sql
SELECT * FROM users ORDER BY age DESC;        -- ASC 升序(默认)，DESC 降序
SELECT * FROM users ORDER BY age DESC, id ASC;
SELECT DISTINCT dept_id FROM users;           -- 去重
SELECT * FROM users LIMIT 10;                 -- 取前 10 条
SELECT * FROM users LIMIT 20, 10;             -- 跳过 20 条取 10（每页10条的第3页）
```

### 3.7 聚合与分组

```sql
SELECT COUNT(*) FROM users;                   -- 总行数（COUNT(*) 不忽略 NULL）
SELECT COUNT(email) FROM users;               -- 统计 email 非空的行数
SELECT AVG(age), SUM(age), MAX(age), MIN(age) FROM users;

SELECT dept_id, COUNT(*) AS cnt
FROM users GROUP BY dept_id;                  -- 按部门统计人数

SELECT dept_id, AVG(age) AS avg_age
FROM users
GROUP BY dept_id
HAVING avg_age > 22;                          -- 对分组结果再过滤
```

::: tip WHERE 与 HAVING 的区别
- `WHERE` 在**分组前**过滤行，不能用聚合函数/聚合别名；
- `HAVING` 在**分组后**过滤组，可以用聚合结果。
:::

### 3.8 联表查询

先准备部门表：

```sql
CREATE TABLE dept (
    id INT PRIMARY KEY AUTO_INCREMENT,
    dept_name VARCHAR(50)
);
INSERT INTO dept (dept_name) VALUES ('运维'), ('开发'), ('测试');
```

**内连接 INNER JOIN：** 只返回两表中**匹配成功**的行。

```sql
SELECT u.name, d.dept_name
FROM users u
INNER JOIN dept d ON u.dept_id = d.id;
```

**左连接 LEFT JOIN：** 左表（users）全部保留，右表无匹配时补 NULL。

```sql
SELECT u.name, d.dept_name
FROM users u
LEFT JOIN dept d ON u.dept_id = d.id;
```

**右连接 RIGHT JOIN：** 右表全部保留。

```sql
SELECT u.name, d.dept_name
FROM users u
RIGHT JOIN dept d ON u.dept_id = d.id;
```

| 连接 | 结果 |
|---|---|
| INNER JOIN | 两边都匹配的行（交集） |
| LEFT JOIN | 左表全部 + 右表匹配 |
| RIGHT JOIN | 右表全部 + 左表匹配 |

> 字段名相同时可用更简洁的 `USING(id)`；实际中 **LEFT JOIN 用得最多**。

### 3.9 子查询

一条查询里嵌套另一条查询：

```sql
-- IN 子查询：查"运维部"的所有用户
SELECT * FROM users
WHERE dept_id IN (SELECT id FROM dept WHERE dept_name = '运维');

-- 标量子查询：查年龄大于平均年龄的用户
SELECT * FROM users
WHERE age > (SELECT AVG(age) FROM users);
```

### 3.10 常用函数

**字符串函数：**

```sql
SELECT CONCAT('a', '-', 'b');          -- a-b
SELECT CONCAT(name, '-', age) FROM users;
SELECT SUBSTRING('hello', 1, 3);       -- hel（MySQL 下标从 1 开始）
SELECT LENGTH('abc'), CHAR_LENGTH('你好');
SELECT UPPER('abc'), LOWER('ABC');
SELECT REPLACE('a-b-c', '-', '+');
SELECT TRIM('  x  ');
```

**日期函数：**

```sql
SELECT NOW(), CURDATE(), CURTIME();
SELECT YEAR(NOW()), MONTH(NOW()), DAY(NOW());
SELECT DATE_FORMAT(NOW(), '%Y-%m-%d %H:%i:%s');
SELECT DATEDIFF('2026-12-31', NOW());    -- 相差天数
```

**数值与控制流函数：**

```sql
SELECT ABS(-5), ROUND(3.567, 2), FLOOR(3.9), CEIL(3.1);
SELECT IF(1 > 0, '真', '假');
SELECT IFNULL(email, '未填写') FROM users;
SELECT CASE WHEN age >= 30 THEN '中年'
            WHEN age >= 18 THEN '青年'
            ELSE '未成年' END AS 分类 FROM users;
```

---

## 四、数据类型

### 4.1 数值类型

| 类型 | 字节 | 范围（有符号） | 说明 |
|---|---|---|---|
| TINYINT | 1 | -128 ~ 127 | UNSIGNED 0~255，常表示布尔/状态 |
| SMALLINT | 2 | -32768 ~ 32767 | |
| MEDIUMINT | 3 | | |
| INT / INTEGER | 4 | 约 ±21 亿 | 最常用整数 |
| BIGINT | 8 | 约 ±9.2×10^18 | 雪花 ID、大计数 |
| FLOAT | 4 | | 单精度浮点（有误差） |
| DOUBLE | 8 | | 双精度浮点 |
| DECIMAL(M,D) | 变长 | | **定点数，金额必用**，如 DECIMAL(10,2) |

### 4.2 字符串类型

| 类型 | 说明 |
|---|---|
| CHAR(n) | **定长**，不足补空格，适合定长数据（手机号、状态码、MD5） |
| VARCHAR(n) | **变长**，按实际长度存储，最常用，n 按"最长可能 + 余量"设置 |
| TINYTEXT / TEXT / MEDIUMTEXT / LONGTEXT | 长文本（文章、正文），无需指定长度 |
| TINYBLOB / BLOB / LONGBLOB | 二进制大对象（文件、图片） |
| ENUM | 单选枚举，如 ENUM('男','女') |
| SET | 多选集合 |

### 4.3 日期时间类型

| 类型 | 格式 | 说明 |
|---|---|---|
| DATE | YYYY-MM-DD | 只存日期（生日） |
| TIME | HH:MM:SS | 只存时间 |
| DATETIME | YYYY-MM-DD HH:MM:SS | 范围大、**与时区无关**，8 字节 |
| TIMESTAMP | YYYY-MM-DD HH:MM:SS | 范围到 2038、**随时区转换**，4 字节 |
| YEAR | YYYY | 年份 |

### 4.4 选择原则

1. **够用就选最小的类型**（越小越省空间、越快）；
2. 整数优先，金额用 **DECIMAL**，别用 FLOAT/DOUBLE 存钱；
3. 定长用 CHAR、变长用 VARCHAR，超长文本用 TEXT；
4. 字符串统一 **utf8mb4**（utf8mb4 才支持完整 Unicode，包括 emoji）；
5. 时间根据是否需要时区转换选 DATETIME / TIMESTAMP。

---

## 五、用户与权限

### 5.1 创建用户

```sql
-- 格式：'用户名'@'允许登录的主机'
CREATE USER 'app'@'localhost' IDENTIFIED BY 'App@123';
CREATE USER 'app'@'10.0.0.%' IDENTIFIED BY 'App@123';   -- 允许 10.0.0 网段
CREATE USER 'ro'@'%' IDENTIFIED BY 'Ro@123';            -- % 表示任意主机
```

> MySQL 8.0 必须**先 CREATE USER，再 GRANT**，GRANT 语句不再自动创建用户。

### 5.2 授权 GRANT

```sql
GRANT SELECT, INSERT, UPDATE ON appdb.* TO 'app'@'10.0.0.%';
GRANT ALL PRIVILEGES ON appdb.* TO 'app'@'localhost';
GRANT SELECT ON appdb.users TO 'ro'@'%';
FLUSH PRIVILEGES;
```

权限范围：`*.*`（全局）、`appdb.*`（某库）、`appdb.users`（某表）。常用权限：SELECT / INSERT / UPDATE / DELETE / CREATE / ALTER / DROP / ALL PRIVILEGES。

### 5.3 查看、回收与删除

```sql
SHOW GRANTS FOR 'app'@'10.0.0.%';
REVOKE DELETE ON appdb.* FROM 'app'@'10.0.0.%';
ALTER USER 'app'@'localhost' IDENTIFIED BY 'New@123';
DROP USER 'app'@'localhost';
```

::: tip 最小权限原则
应用账号只授予业务必需的权限（通常 SELECT/INSERT/UPDATE，不要给 DROP/GRANT），主机范围尽量精确，不要图省事全用 `%` + ALL。
:::

---

## 六、视图、存储过程与触发器

### 6.1 视图 VIEW

视图是一条 SELECT 语句的**虚拟表**，本身不存数据，像"窗口"一样展示数据。

```sql
CREATE VIEW v_user_dept AS
SELECT u.name, u.age, d.dept_name
FROM users u LEFT JOIN dept d ON u.dept_id = d.id;

SELECT * FROM v_user_dept;          -- 像查普通表一样查视图
DROP VIEW v_user_dept;
```

用途：简化复杂查询、隐藏敏感列、按不同角色暴露不同数据。

### 6.2 存储过程 PROCEDURE

把一组 SQL 预先编译好存在服务器端，用 `CALL` 调用，支持参数（IN 传入、OUT 传出、INOUT）。

```sql
DELIMITER $$                        -- 临时把语句结束符改成 $$（避免与体内 ; 冲突）
CREATE PROCEDURE p_count_dept(IN d_id INT, OUT cnt INT)
BEGIN
    SELECT COUNT(*) INTO cnt FROM users WHERE dept_id = d_id;
END$$
DELIMITER ;                         -- 改回分号

CALL p_count_dept(1, @cnt);
SELECT @cnt;
DROP PROCEDURE p_count_dept;
```

### 6.3 存储函数 FUNCTION

函数必须有返回值（RETURNS），可直接用在 SELECT 里。

```sql
DELIMITER $$
CREATE FUNCTION f_hello(n VARCHAR(20))
RETURNS VARCHAR(50)
DETERMINISTIC
BEGIN
    RETURN CONCAT('Hello ', n);
END$$
DELIMITER ;

SELECT f_hello(name) FROM users;
```

> 存储过程更适合执行一组操作，函数适合计算并返回一个值。

### 6.4 触发器 TRIGGER

在表发生 INSERT / UPDATE / DELETE 时**自动执行**（BEFORE 之前 / AFTER 之后）。

```sql
CREATE TABLE log (id INT PRIMARY KEY AUTO_INCREMENT, msg VARCHAR(100), t DATETIME);

DELIMITER $$
CREATE TRIGGER trg_after_insert
AFTER INSERT ON users
FOR EACH ROW
BEGIN
    INSERT INTO log(msg, t) VALUES (CONCAT('新增用户:', NEW.name), NOW());
END$$
DELIMITER ;
```

- `NEW` 表示新行、`OLD` 表示旧行；
- 典型用途：操作审计、数据校验、级联维护。

### 6.5 事件 EVENT（定时任务）

按时间/周期自动执行，类似系统的 crontab，需要先开启调度器：

```sql
SET GLOBAL event_scheduler = ON;

CREATE EVENT e_clear_log
ON SCHEDULE EVERY 1 DAY STARTS '2026-09-28 02:00:00'
DO
  DELETE FROM log WHERE t < DATE_SUB(NOW(), INTERVAL 30 DAY);
```

::: warning MariaDB/MySQL 默认可能关闭事件
`event_scheduler` 需要在配置或会话中显式开启；重启后若要永久生效，在 my.cnf 的 `[mysqld]` 加 `event_scheduler=ON`。
:::

---

## 七、存储引擎

### 7.1 查看引擎

```sql
SHOW ENGINES;
SELECT @@default_storage_engine;
```

### 7.2 InnoDB 与 MyISAM 对比

| 对比项 | InnoDB（默认） | MyISAM |
|---|---|---|
| 事务 | **支持** ACID | 不支持 |
| 锁粒度 | **行锁**，并发高 | 表锁 |
| 外键 | 支持 | 不支持 |
| 索引结构 | 聚簇索引（数据与主键一起存） | 非聚簇（索引与数据分开） |
| 崩溃恢复 | 支持（redo log 重放） | 差 |
| 适用场景 | OLTP 通用（**默认选择**） | 以读为主的老应用 |

### 7.3 InnoDB 内存结构

| 区域 | 作用 |
|---|---|
| **Buffer Pool** | 最大的内存区，缓存**数据页和索引页**，读写先走这里，命中率决定性能 |
| Change Buffer | 缓存对非唯一二级索引的修改（写缓冲） |
| Log Buffer | 缓存 redo log，再刷到磁盘 |
| Adaptive Hash Index | 自适应哈希索引（自动为热点页建哈希索引） |

### 7.4 InnoDB 后台线程与文件

- 后台线程：master thread、IO thread、purge thread 等，负责**刷脏页、写 redo/undo、回收**；
- 关键文件：
  - **redo log**（重做日志，ib_logfile）：记录已提交修改，崩溃后重放，保证**持久性**；
  - **undo log**（回滚日志）：记录修改前的数据，用于回滚和 **MVCC**；
  - 表空间 `.ibd`：表的数据和索引。

::: tip 为什么 InnoDB 更可靠
修改数据时先写 redo log（WAL，Write-Ahead Logging），即使数据页还没刷盘就宕机，重启也能用 redo log 恢复；配合 undo log 支持事务回滚。这就是它支持事务和崩溃恢复的底层原因。
:::

---

## 面试自测

1. 一条 SELECT 语句在 MySQL 内部经过哪些组件？查询缓存为什么在 8.0 被移除？
2. 第一、第二、第三范式分别解决什么问题？什么情况下会反范式设计？
3. `DELETE`、`TRUNCATE`、`DROP` 有什么区别？
4. WHERE 和 HAVING 的区别？内连接和左连接的区别？
5. MySQL 8.0 默认认证插件是什么？老客户端连不上怎么处理？
6. 视图和存储过程、存储函数有什么区别？
7. 为什么金额字段要用 DECIMAL 而不是 DOUBLE？
8. InnoDB 相比 MyISAM 有哪些优势？redo log 和 undo log 各起什么作用？

## 相关速查

- [MySQL 进阶与高可用](./data-mysql-advanced)
- [Linux 命令速查](/reference/linux-commands)
- MySQL 8.0 官方文档：https://dev.mysql.com/doc/refman/8.0/en/
- MariaDB 文档：https://mariadb.com/kb/en/documentation/
