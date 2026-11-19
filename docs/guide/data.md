---
title: "数据与中间件"
description: "本页聚合 数据库与常用中间件的部署、优化、备份和高可用：MySQL、Redis、Kafka、Spring Cloud 全家桶、APISIX / MinIO。"
---
# 数据与中间件

> 本页聚合 **数据库与常用中间件**的部署、优化、备份和高可用：MySQL、Redis、Kafka、Spring Cloud 全家桶、APISIX / MinIO。

## 文章索引

### 关系型数据库

::: idx

| 文章 | 解决什么问题 | 状态 |
|---|---|---|
| [MySQL 基础](/services/database/mysql/01-理论) | 安装、SQL 基础、用户权限、存储引擎、数据类型 | ✅️ 已完成 |
| [MySQL 进阶与高可用](/services/database/mysql/01-理论) | 索引/EXPLAIN、慢查询、备份恢复、主从复制、MHA/MGR、MyCat、运维排查 | ✅️ 已完成 |

:::

### 缓存与消息队列

::: idx

| 文章 | 解决什么问题 | 状态 |
|---|---|---|
| [Redis](/services/database/redis/01-理论) | 数据类型、持久化、主从 / 哨兵 / Cluster | ✅️ 已完成 |
| [Kafka](#合并资料) | 架构、部署、主题 / 分区 / 消费者组 | ✅️ 已完成 |

:::

### 微服务与网关

::: idx

| 文章 | 解决什么问题 | 状态 |
|---|---|---|
| [Spring Cloud 全家桶](#合并资料) | Nacos（含集群）、Sentinel、Seata、Gateway | ✅️ 已完成 |
| [APISIX 与 MinIO](#合并资料) | APISIX 路由/插件、MinIO 对象存储 | ✅️ 已完成 |

:::

## 高可用 / 主从复制要点

> 详细方案见对应文章，这里做速查提示：

- **MySQL**：主从复制 / 半同步、MHA、MGR、MyCat 读写分离
- **Redis**：主从、哨兵、Cluster
- **Nacos**：集群（Raft 协议）
- **通用**：脑裂的预防（仲裁节点、双心跳线）

## 命令速查

- 数据库/服务运维命令：[Linux 命令速查](/reference/linux-commands)

<!-- merged-qa-faq:start -->
## 常见问题 FAQ

> 数据库与中间件问题的高频问题已并入本页。默认只显示问题，点开查看完整答案。

### 一、部署前：存储与数据模型

<details>
<summary>Q1：为什么用 B+树做索引？</summary>

**答：**

结论：MySQL InnoDB 索引用 B+树，是因为它**矮胖、磁盘 IO 少、范围查询快、叶子节点有序**。

第一，先对比一下为什么不用二叉树或红黑树。数据存在磁盘上，每次读一个节点就是一次 IO。二叉树太高，几千万行数据树高十几二十层，查一条数据要读十几次磁盘，扛不住。B+树是多叉平衡树，一个节点就是一个 16KB 的页，能放下上百个键，所以树非常矮——千万级数据树高也就 3~4 层，查一次主键最多 3~4 次 IO，这是核心。

第二，对比 B 树。B 树非叶子节点也存数据，导致每个节点能放的键变少，树变高；而且范围查询要中序遍历、可能再回到根。B+树把所有数据都放在叶子节点，非叶子只存键，节点塞得下更多键、树更矮；叶子节点之间用双向链表串起来，做 `between`、`>`、`<`、`order by` 这种范围扫描特别方便，找到起点顺着链表往后扫就行。

第三，对比哈希索引。哈希等值查询 O(1) 很快，但不支持范围、不支持排序、不支持最左前缀，哈希冲突还有代价。InnoDB 的自适应哈希是内部自动加的，用户建不了。

补充两个概念：聚簇索引就是主键索引，叶子节点直接存整行数据；二级索引叶子节点存的是主键值，所以查二级索引如果要拿整行，要回表——先查二级索引拿到主键，再去聚簇索引查一次。覆盖索引就是查询的列都在索引里，不用回表。

</details>

<details>
<summary>Q2：事务隔离级别及问题？MVCC 原理？</summary>

**答：**

结论：SQL 标准四个隔离级别，从低到高是**读未提交 RU、读已提交 RC、可重复读 RR、串行化 Serializable**。MySQL InnoDB 默认是 **RR**。

并发问题三个：脏读是读到别的事务**还没提交**的修改；不可重复读是同一事务内两次读同一行，被别的事务提交更新了，值不一样（侧重单行修改）；幻读是同一事务内两次范围查询，第二次多了几行（侧重插入）。

各级别解决情况：RU 啥都不解决；RC 解决脏读；RR 解决脏读和不可重复读，InnoDB 靠 Next-Key Lock 也基本解决了幻读；Serializable 全加串行锁，啥都解决但性能最差。

MVCC（多版本并发控制）是 InnoDB 在 RC/RR 下实现"读不加锁、读写不阻塞"的核心。原理：每行隐藏两个列 `trx_id`（最近修改它的事务 ID）和 `roll_pointer`（指向 undo log 里的老版本）。读的时候，根据当前事务的 Read View 判断这行哪个版本对自己可见。Read View 里记录了"生成视图时活跃的事务列表"，规则是：如果行的 trx_id 比最小活跃事务还小，说明已经提交了，可见；比最大还大，是后面开的事务，不可见；在活跃列表里，也不可见。不可见就顺着 roll_pointer 往 undo log 找老版本，直到找到一个可见的。

RC 和 RR 的区别就一句话：RC 是**每条 SELECT 都生成新 Read View**，所以能看到别人刚提交的；RR 是**事务第一次 SELECT 时生成 Read View，整个事务复用**，所以整个事务内看到的快照一致。

</details>

<details>
<summary>Q3：Redis 数据类型及场景？</summary>

**答：**

结论：Redis 常用五种基本类型，再加三个高级结构，业务场景要对着数据形状选。

第一，**String**，最基础，字符串/数字都行。场景：计数器（`INCR article:read:123`）、分布式 session、缓存对象序列化后的 JSON、限速。最大 512MB，一般别塞这么大。

第二，**Hash**，field-value 的 map。场景：存对象，比如用户信息 `user:1001 -> {name, age, email}`，比 String 存 JSON 好在能单独改某个字段，不用整个反序列化再写回。

第三，**List**，双向链表。场景：消息队列、最新列表、关注时间线。`lpush`/`rpop` 就是简单队列；注意它不是专业 MQ，没有 ack、没有持久化强保障。

第四，**Set**，无序去重集合。场景：标签、共同好友（`sinter`）、抽奖去重、UV。

第五，**ZSet（Sorted Set）**，每个 member 带一个 score，按 score 排序。场景：排行榜（直播间热度、游戏排行）、延时队列（score 存时间戳）、带权重的任务队列。

高级结构三个：**Bitmap**，位操作，存签到、在线状态，一年签到才占 45 字节；**HyperLogLog**，基数估算，12KB 内存就能算上亿 UV，误差 0.81%，能容忍误差的统计场景非常香；**Stream**（Redis 5.0+），专业消息队列，支持消费组、ACK、 pending 列表，比 List 更像 MQ。

选型一句话：KV 计数用 String，对象用 Hash，队列用 List/Stream，去重交并用 Set，排行用 ZSet，海量统计用 HyperLogLog。

</details>

### 二、部署与高可用：复制、持久化与接入

<details>
<summary>Q4：MySQL 主从复制原理？</summary>

**答：**

结论：MySQL 主从复制分三步——**主库写 binlog、从库 IO 线程拉到 relay log、从库 SQL 线程重放**，默认异步复制。

具体流程：第一，主库任何增删改事务提交时，会把事务顺序写入 **binlog**（二进制日志，statement/row/mixed 三种格式，生产推荐 row）。第二，从库启动一个 **IO 线程**，连上主库，主库为它启动一个 **dump 线程**，把 binlog 事件推给从库。第三，从库 IO 线程收到事件后写进本地的 **relay log（中继日志）**。第四，从库另一个 **SQL 线程**（MySQL 5.7 后基于并行复制，多个 worker）实时读 relay log，重放这些事件，保持数据和主库一致。复制位点用 `binlog 文件名 + position` 记录，从库记住自己读到哪了，下次从断点继续。

复制方式有三种：**异步复制**（默认，主库提交完就返回，不等从库，性能好但主库宕机可能丢数据）；**半同步复制**（主库至少等一个从库收到 binlog 并写进 relay log 才返回客户端，损失一点性能换一致性，MySQL 5.5+ 支持）；**组复制/MGR**（基于 Paxos，多主强一致，成本高）。

主从延迟是老大难问题。原因：从库单线程重放追不上主库并发写入；大事务、DDL、慢查询都会卡住 SQL 线程。监控用 `Seconds_Behind_Master`，但这个值不太准，生产更可靠的是对比主从位点或自己记心跳表。解决办法：开启并行复制（`slave_parallel_workers`）、拆分大事务、避免长 DDL、必要时升级到半同步或 MGR。

主从复制的用途：读写分离（写走主、读走从）、做备份、做异地灾备。

</details>

<details>
<summary>Q5：RDB 和 AOF 区别？</summary>

**答：**

结论：RDB 是**时间点快照**，AOF 是**追加写命令日志**，生产一般两个都开，4.0 后还支持混合持久化。

RDB：在某个时刻把整个内存数据快照成一个 `dump.rdb` 二进制文件，靠 `save`（阻塞）或 `bgsave`（fork 子进程）触发。优点：文件小、恢复快、适合做备份和主从全量同步；缺点：两次快照之间宕机就会丢那一段时间的数据，fork 大实例时会短暂阻塞。

AOF：每写一条命令就追加到 `appendonly.aof` 文件（类似 MySQL binlog）。刷盘策略三种：`always` 每条都 fsync，最安全最慢；`everysec` 每秒 fsync，默认，最多丢 1 秒；`no` 交给 OS，最快最不安全。优点：数据安全，最多丢 1 秒；缺点：文件大、恢复慢。AOF 会重写（`bgrewriteaof`），把过期、覆盖的命令压缩成最小命令集，不然文件会无限膨胀。

Redis 4.0 开始支持**混合持久化**：AOF 重写时，把这一刻的数据用 RDB 格式写在 AOF 文件开头，之后的增量命令再用 AOF 文本格式追加。这样重启时先加载 RDB 部分（快），再 replay 后面的增量命令（丢得少），鱼和熊掌兼得，生产推荐开 `aof-use-rdb-preamble yes`。

实际选择：纯缓存、丢了能重建就关持久化；当数据库用就 RDB+AOF 都开，再定期把 RDB 拷到对象存储做异地备份。

</details>

<details>
<summary>Q6：负载均衡算法？</summary>

**答：**

结论：Nginx 原生 `upstream` 支持四种负载算法，第三方模块还能加两种，线上最常用的是轮询加权和 ip_hash。

第一，**轮询（round-robin）**，默认方式，按顺序一个一个分，谁也不多谁也不少。后端性能差不多时用它。

第二，**加权轮询（weight）**，`server 10.0.0.1:80 weight=3;`，weight 越大分到的请求越多。机器配置不一样就用权重，性能好的多分。

第三，**ip_hash**，对客户端 IP 做哈希固定分到某台后端。好处是同一会话一定打到同一台机器，解决 session 共享问题；缺点是某台挂了会有一批用户被重映射，而且 hash 不均时可能某台压力大。现在一般不用它做会话粘滞，而是用 Redis 集中存 session。

第四，**least_conn**，把请求发给当前活跃连接数最少的后端。长连接、请求处理时间差异大的场景比轮询合理。

第三方模块两种：`fair`（按后端响应时间分配，响应快的多分）、`url_hash`（按 URL 哈希，让相同 URL 打到同一台，提高缓存命中率），需要额外编译。

配合健康检查：`max_fails=3 fail_timeout=30s`，30 秒内失败 3 次就把这台后端摘 30 秒；`down` 标记下线；`backup` 标记备用机，其他都挂了才上。Nginx 原生只做被动健康检查（转发时才发现挂），主动健康检查要商业版或用 `nginx_upstream_check_module`。

</details>

<details>
<summary>Q7：反向代理和正向代理区别？</summary>

**答：**

结论：一句话——**正向代理代理的是客户端，反向代理代理的是服务端**。

正向代理：客户端不知道真正的服务器是谁，代理服务器帮客户端去请求。典型例子：翻墙/VPN、公司出口代理、APT 软件源代理。客户端要主动配置代理地址，服务端看到的是代理的 IP，不知道真实用户是谁。作用是翻墙、突破访问限制、缓存加速、隐藏客户端身份。

反向代理：服务端那一侧的代理，客户端根本不知道背后真正处理请求的是哪台机器，以为直接在跟代理说话。Nginx 就是最典型的反向代理。用户访问 `www.example.com`，DNS 解析到 Nginx，Nginx 再根据规则转给后面的 Tomcat/Node/PHP-FPM 集群。作用有四个：**负载均衡**（把请求分发到多台后端）、**SSL  termination**（证书只在 Nginx 配，后端走 HTTP）、**缓存静态资源**、**统一入口和安全防护**（隐藏后端拓扑、防恶意直接打后端）。

对比一下：正向代理服务客户端，帮客户端翻墙；反向代理服务服务端，帮后端扛流量。我们日常说 Nginx 做"反向代理+负载均衡"就是后者。配置上核心就一行 `proxy_pass http://backend;`，再配合 `proxy_set_header Host $host;`、`X-Real-IP`、`X-Forwarded-For` 把真实客户端信息透传给后端，不然后端日志里全是 Nginx 的 IP。

</details>

<details>
<summary>Q8：location 匹配规则与优先级？</summary>

**答：**

结论：Nginx location 匹配优先级从高到低是：**`=` > `^~` > 正则 `~`/`~*`（按配置顺序）> 普通前缀（最长匹配）**。

逐个解释：

- `location = /health`：精确匹配，只能是 `/health`，优先级最高，命中就立刻返回，不再往下找。常用于健康检查、首页。
- `location ^~ /static/`：前缀匹配，命中后**不再继续匹配正则**。长静态资源前缀常用，避免后面 `~ \.js$` 之类正则抢匹配。
- `location ~ \.php$`：正则匹配，区分大小写；`~*` 不区分大小写。多个正则按配置文件里的**从上到下**顺序，第一个命中就用。
- `location /api/`：普通前缀匹配，最长优先，但优先级低于上面三种。

举个例子，请求 `/static/app.js`：先看有没有 `=`，没有；再看 `^~ /static/` 命中了，直接用它，后面就算写了 `~ \.js$` 也不看了。如果没有 `^~`，就会继续往下匹配正则，命中 `~ \.js$` 用正则那条。

两个高频坑：第一，`proxy_pass` 末尾带不带斜杠差别巨大。带斜杠 `proxy_pass http://backend/;` 会把 location 匹配掉的部分替换掉；不带斜杠 `proxy_pass http://backend;` 会把完整 URI 拼上去。比如 `location /api/ { proxy_pass http://backend:8080/; }`，请求 `/api/user` 会变成 `http://backend:8080/user`；不带末尾斜杠就会变成 `http://backend:8080/api/user`。

第二，`try_files $uri $uri/ /index.html;` 是 SPA 前端神器，按顺序找文件，找不到最后回退到 index.html，交给前端路由处理。

</details>

### 三、运行与排障：慢查询、缓存与代理

<details>
<summary>Q9：索引失效的常见情况？</summary>

**答：**

结论：索引失效本质是"优化器觉得走索引比全表扫还慢，干脆不走"。常见情况按生产中常见的几类列。

第一，**不满足最左前缀**。联合索引 `(a,b,c)` 是按 a→b→c 排序的，如果你 `where b=?`、`where c=?`、或者跳过 a 直接查 b，索引用不上；`where a=? and c=?` 只能用到 a 这一列。

第二，**索引列上用函数或做运算**。`where date(create_time)='2026-09-01'`、`where age+1=10`、`where left(name,3)='abc'`，列被处理过，索引树没法直接定位。改写：改成范围 `create_time >= '2026-09-01' and create_time < '2026-09-02'`，或者建函数索引。

第三，**隐式类型转换**。字段是 varchar，你写 `where phone=13800000000`（数字），MySQL 会把每行 phone 转成数字再比，等价于在列上加函数，索引失效。字符串就老老实实地加引号。

第四，`like '%xxx'` 前导通配符，B+树是按前缀排序的，前 % 没法定位；`like 'xxx%'` 是能用的。

第五，`or` 两边有一边没索引，整个索引失效。

第六，`is null`、`!=`、`not in`、`not exists` 在数据量占比大时优化器会放弃索引，因为扫大半张表比回表还慢。

怎么确认？`explain select ...`，重点看几列：`type` 列，`const/eq_ref/ref/range` 是好的，`ALL` 就是全表扫；`key` 列实际用到的索引，NULL 就是没用上；`rows` 预估扫描行数；`Extra` 里出现 `Using filesort`、`Using temporary` 要警惕，出现 `Using index` 说明覆盖索引挺好。

</details>

<details>
<summary>Q10：慢 SQL 如何优化？explain 怎么看？</summary>

**答：**

结论：慢 SQL 优化是个固定流程——**先定位、再分析、后优化、最后验证**。

第一步，定位。先开慢查询日志：`slow_query_log=ON`、`long_query_time=1`（秒）、`slow_query_log_filename=/data/mysql/slow.log`，然后用 `mysqldumpslow -s t -t 10 /data/mysql/slow.log` 或 `pt-query-digest` 聚合，找出频次高、平均耗时长的 Top SQL。

第二步，`explain` 看执行计划。重点列：

- `id`：select 序号，越大越先执行；
- `select_type`：SIMPLE/PRIMARY/SUBQUERY 等；
- `table`：查哪张表；
- **`type`**：访问类型，从好到差 `system > const > eq_ref > ref > range > index > ALL`。看到 `ALL` 全表扫、`index` 全索引扫，就要优化；
- **`key`**：实际用的索引，NULL 说明没用上；
- `key_len`：用了索引的多长，判断联合索引用了几列；
- `ref`：索引跟什么比；
- **`rows`**：预估要扫多少行，越大越糟；
- **`Extra`**：重点。`Using index` 覆盖索引好；`Using where` 服务器层过滤；`Using filesort` 额外排序要优化；`Using temporary` 用临时表（group by/order by 常见）要优化。

第三步，优化手段：加合适的联合索引满足最左前缀；改写 SQL 避免 `select *`、只查需要的列；小表驱动大表；`join` 字段要有索引；深分页 `limit 1000000,10` 改成"记住上一页最大 id，where id > ? limit 10"；还不行就考虑分表、加缓存、读写分离。

第四步，改完再 `explain` 一遍，确认 type 升到 ref/range、rows 降下来，再 `show profiles` 或实测耗时对比。

</details>

<details>
<summary>Q11：缓存穿透/击穿/雪崩及解决？</summary>

**答：**

结论：这三个都是缓存没挡住请求、压力直接打到 DB，但成因不同，方案也不同。

**缓存穿透**：查一个数据库里**根本不存在**的数据，每次都绕过缓存打到 DB。比如有人恶意刷 `user?id=-1`。方案：第一，对查不到的 key 也缓存一个空值（短 TTL，比如 60 秒）；第二，前置**布隆过滤器**，把所有存在的 key 放 Bitmap 里，不存在的直接拒绝。注意空值缓存别放太久，不然真数据来了有短暂不一致。

**缓存击穿**：某个**热点 key 突然过期**，瞬间成千上万并发请求同时穿透到 DB。方案：第一，**互斥锁**，拿不到锁的线程 sleep 一下重试，只放一个线程去回源重建缓存（`SETNX lock:key` 抢锁，拿到的查 DB 写缓存，释放锁）；第二，**逻辑过期**，value 里存一个逻辑过期时间，发现过期后异步开线程重建，当前请求先返回老数据，不等；第三，热点 key 提前预热、永不过期。

**缓存雪崩**：**大量 key 同时过期**，或者 Redis 整个节点挂了，请求全压到 DB。方案：第一，给 TTL 加随机抖动，比如基础 300 秒加 `random(0~60)` 秒，别让一堆 key 同一秒到期；第二，热点数据永不过期或后台刷新；第三，缓存层高可用（主从+哨兵/Cluster），DB 这边加限流、降级、熔断兜底，别让 DB 被打挂。

一句话区分：穿透是"查不存在的"，击穿是"一个热点 key 过期"，雪崩是"一大片 key 同时过期或缓存挂了"。

</details>

<details>
<summary>Q12：如何实现分布式锁？</summary>

**答：**

结论：Redis 分布式锁最基本的命令是 `SET key value NX PX 过期时间`，要解决"互斥、防误删、可续期、原子释放"四个问题。

第一，加锁。`SET lock:order:1001 <uuid> NX PX 30000`。`NX` 意思是 key 不存在才设置成功，保证互斥；`PX 30000` 30 秒自动过期，防止持锁进程挂了死锁；value 必须是**全局唯一标识**（UUID+线程 id），不能随便写个固定值。

第二，释放锁。不能直接 `DEL`，否则可能把别人的锁删了——比如我 A 拿锁、执行超时、锁自动过期了、B 又拿到锁、A 醒过来执行完直接 DEL，把 B 的锁删了。正确做法：先判断 value 是不是自己的，再删，这两步要原子，用 Lua 脚本：

```lua
if redis.call("get", KEYS[1]) == ARGV[1] then
  return redis.call("del", KEYS[1])
else
  return 0
end
```

第三，业务执行时间可能超过 30 秒怎么办？要**看门狗（watchdog）自动续期**：开一个后台线程，每隔过期时间的 1/3（比如 10 秒）检查自己还持不持锁，持就把过期时间重置回 30 秒。Redisson 客户端已经封装好了，直接用它的 `RLock`，别自己手写。

第四，集群问题。主从异步复制，主节点拿到锁还没同步给从就挂了，从升主后另一个客户端又能拿到同一把锁。严格场景用 **Redlock**（向 N 个独立主节点申请，多数成功才算拿到），但 Redlock 有争议（Martin Kleppmann 那篇文章），一般业务用 Redisson 单节点锁 + 主从就够，金融级强一致用 ZooKeeper/etcd 更稳。

</details>

<details>
<summary>Q13：502/504 如何排查？</summary>

**答：**

结论：502 是 Nginx 连不上后端，504 是连上了但后端超时，两者都要先在 Nginx 上看错误日志，再上后端那台查。

先看 Nginx 错误日志，最快：`tail -f /var/log/nginx/error.log`。502 一般会看到 `connect() failed (111: Connection refused) while connecting to upstream` 或 `upstream prematurely closed connection`；504 一般是 `upstream timed out (110: Connection timed out) while reading response header from upstream`。

**502 排查路径：**

1. 后端服务到底起没起？上后端机器 `ss -tlnp | grep 8080`，确认端口在监听；`systemctl status tomcat` / `docker ps` 看进程。
2. Nginx 能不能连到后端？在 Nginx 机器上 `curl -v http://10.0.0.5:8080/` 或 `telnet 10.0.0.5 8080`。连不上就查后端防火墙/安全组、Nginx 配置里 upstream 地址端口写对没。
3. 后端是不是崩了/重启中？看后端日志 `journalctl -u tomcat -f`、应用日志，有没有 OOM、OOM Killer 把进程杀了（`dmesg | tail`）。
4. 后端是不是把连接关了？后端处理完请求关连接比 Nginx 快，Keepalive 配置不一致也会 502，Nginx 侧加 `proxy_http_version 1.1; proxy_set_header Connection "";`。
5. 资源问题：后端 CPU/内存打满、连接数被打满（`ulimit -n`）。

**504 排查路径：**

1. 后端确实慢。看后端慢查询、慢接口日志、APM 链路追踪，找到那个耗时长的接口。
2. Nginx 超时配置太短。`proxy_connect_timeout` 默认 60s、`proxy_read_timeout` 60s，长接口要适当调大，但不能乱调大，不然慢请求占着 worker 不放。
3. 后端等 DB/外部服务卡住。上后端机器 `tcpdump -i any port 3306`、`ss -tnp` 看连接状态，`jstack`/`py-spy` 抓栈看卡在哪。
4. 网络问题：Nginx 到后端之间丢包、跨机房专线抖动，用 `mtr`、`tcptrace` 看。

一句话：502 先问"后端活着吗、Nginx 连得通吗"，504 先问"后端为什么这么慢"。

</details>

<!-- merged-qa-faq:end -->

<!-- merged-guide-material:start -->
## 合并资料

> 原先单独成页的同主题内容已收进本页；默认折叠，点开看原页全文。

<details>
<summary><strong>APISIX 与 MinIO — API 网关 APISIX（etcd 架构、Docker 部署、route/upstream/consumer、限流认证流量插件）、DAS/NAS/SAN、S3 对象存储 MinIO（单机/分布式纠删码、mc、SDK 对接）</strong></summary>

::: tip 本篇定位
部署云原生 API 网关 **APISIX**（etcd 动态配置、路由/上游、限流认证插件），理解存储分类，部署 S3 兼容对象存储 **MinIO**（单机/分布式、mc、应用对接）。
:::

# 第一部分：APISIX

#### 一、APISIX 简介

Apache APISIX 是开源、云原生、高性能 API 网关，基于 OpenResty（Nginx + LuaJIT），配置存在 **etcd**，变更**毫秒级热生效、无需 reload**。提供路由、负载均衡、认证、限流、可观测等上百个插件。

##### 1.1 架构

| 组件 | 角色 |
|---|---|
| APISIX | 数据面，处理实际流量 |
| **etcd** | 配置中心，存路由/上游/消费者（APISIX 强依赖，集群 3 节点） |
| APISIX Dashboard | 可视化管理面（可选，更新较慢） |

##### 1.2 与其他网关对比

| 网关 | 特点 |
|---|---|
| **APISIX** | etcd 动态配置、热更新、插件多、社区活跃 |
| Kong | 同 OpenResty，数据库 etcd/Postgres，生态成熟 |
| Nginx | 高性能但配置静态、改配置 reload |
| Spring Cloud Gateway | Java 体系集成好，资源/性能不如 Nginx 系 |
| Envoy | xDS 动态配置，Service Mesh 常用 |

#### 二、APISIX 部署

##### 2.1 docker-compose

`/data/apisix/docker-compose.yml`：

```yaml
services:
  etcd:
    image: bitnami/etcd:3.5.18
    environment:
      - ALLOW_NONE_AUTHENTICATION=yes
      - ETCD_ADVERTISE_CLIENT_URLS=http://etcd:2379
    volumes:
      - /data/apisix/etcd:/bitnami/etcd

  apisix:
    image: apache/apisix:3.11.0-debian
    ports:
      - "9080:9080"      # 数据面
      - "9091:9091"      # Admin API
    volumes:
      - ./config.yaml:/usr/local/apisix/conf/config.yaml:ro
    depends_on: [etcd]

  dashboard:
    image: apache/apisix-dashboard:3.0.0-alpine
    ports:
      - "9000:9000"
    volumes:
      - ./dashboard-conf.yaml:/usr/local/apisix-dashboard/conf/conf.yaml:ro
    depends_on: [etcd]
```

`config.yaml`：

```yaml
deployment:
  role: traditional
  role_traditional:
    config_provider: etcd
  etcd:
    host:
      - "http://etcd:2379"
```

```bash
docker compose up -d
curl http://127.0.0.1:9091/apisix/admin/routes \
  -H 'X-API-KEY: edd1c9f034335f136f87ad84b625c8f1'
```

::: warning Dashboard 现状
Dashboard 停留在 3.0.0。生产推荐 **Admin API、standalone 声明式配置、APISIX Ingress Controller**；学习可用 Dashboard。
:::

#### 三、核心对象

| 对象 | 说明 |
|---|---|
| **Route 路由** | 匹配条件（host/uri/method）+ plugins + upstream |
| **Upstream 上游** | 后端节点、负载均衡（roundrobin/chash/ewma）、健康检查 |
| Service | 一组路由复用的插件和上游 |
| Consumer | 消费方身份，配合认证插件 |
| SSL | 证书与 SNI |
| Plugin Config | 可复用的插件集合 |

#### 四、路由与插件

##### 4.1 创建路由

```bash
curl http://127.0.0.1:9091/apisix/admin/routes/1 \
  -H 'X-API-KEY: edd1c9f034335f136f87ad84b625c8f1' -X PUT -d '
{
  "uri": "/get",
  "hosts": ["api.example.com"],
  "methods": ["GET"],
  "upstream": {
    "type": "roundrobin",
    "nodes": { "httpbin.org:80": 1 }
  }
}'

curl http://127.0.0.1:9080/get -H "Host: api.example.com"
```

##### 4.2 常用插件

| 类别 | 插件 |
|---|---|
| 限流 | limit-req（漏桶）、limit-count（周期计数）、limit-conn（并发） |
| 认证 | key-auth、jwt-auth、basic-auth、openid-connect、ldap-auth |
| 流量 | proxy-rewrite、redirect、traffic-split（灰度/金丝雀）、response-rewrite |
| 安全 | cors、ip-restriction、ua-restriction、csrf |
| 可观测 | prometheus、skywalking、opentelemetry、http/log/kafka-log |

在路由的 `plugins` 字段配置即可，例如同时启用 key-auth + limit-count。

---

# 第二部分：MinIO

#### 五、存储基础

##### 5.1 三种存储形态

| 形态 | 全称 | 特点 | 级别 |
|---|---|---|---|
| DAS | Direct Attached Storage | 存储直连主机（本地盘），简单、便宜，主机故障不可访问 | 块设备 |
| NAS | Network Attached Storage | 接入网络、用 NFS/CIFS/FTP 共享，"文件级"共享、即插即用，性能一般 | 文件级 |
| SAN | Storage Area Network | 高速专用网络（FC/iSCSI），高速、集中、可扩展，成本高 | 块级共享 |

##### 5.2 对象存储

对象存储用于海量非结构化数据（图片、视频、备份、日志），把数据作为**对象（Object）**放在**桶（Bucket）**中：

- 每个对象 = **数据 + 元数据 + 唯一标识（ID/Key）**；
- **扁平结构**、无多级目录树，通过 **RESTful API**（S3）访问；
- 水平扩展、多副本/纠删码、高持久，适合读多写少、大文件、云环境。

公有云：阿里云 OSS、腾讯云 COS、AWS S3；**私有云：MinIO、Ceph RGW**。

#### 六、MinIO 简介

MinIO 是 Go 开发、**兼容 Amazon S3 API** 的开源对象存储，轻量、高性能、支持分布式和纠删码，适合自建图片/视频/备份存储、私有云、S3 网关。单对象最大可达 5TB。

#### 七、MinIO 部署

##### 7.1 单机二进制

```bash
wget https://dl.min.io/server/minio/release/linux-amd64/minio -O /usr/local/bin/minio
chmod +x /usr/local/bin/minio
mkdir -p /data/minio

MINIO_ROOT_USER=admin MINIO_ROOT_PASSWORD=Admin@12345 \
minio server /data/minio --console-address ":9001"
# S3 API 9000，控制台 9001
```

##### 7.2 Docker（版本锁定）

```bash
docker run -d --name minio \
  -p 9000:9000 -p 9001:9001 \
  -e MINIO_ROOT_USER=admin \
  -e MINIO_ROOT_PASSWORD=Admin@12345 \
  -v /data/minio:/data \
  minio/minio:RELEASE.2025-04-22T22-12-26Z server /data --console-address ":9001"
```

> MinIO tag 即发布日期（非 latest）。上面为格式示例，部署前到 https://min.io/download 复制当前稳定 RELEASE tag。

##### 7.3 分布式（生产，纠删码）

```bash
# 4 节点、每节点 2 盘（每台执行）
minio server http://node{1...4}.example.com/data{1...2} \
  --console-address ":9001"
```

- **纠删码 Erasure Coding**：数据分片 + 校验分片，可容忍部分盘/节点故障不丢数据；
- 生产至少 4 节点，启用 TLS、版本控制、生命周期。

#### 八、mc 客户端

```bash
wget https://dl.min.io/client/mc/release/linux-amd64/mc -O /usr/local/bin/mc
chmod +x /usr/local/bin/mc

mc alias set local http://10.0.0.13:9000 admin 'Admin@12345'
mc ls local
mc mb local/mybucket                    # 建桶
mc cp image.png local/mybucket/         # 上传
mc ls local/mybucket
mc cp local/mybucket/image.png ./       # 下载
mc anonymous set download local/mybucket   # 公开读
mc share download --expire 1h local/mybucket/image.png  # 临时链接
```

#### 九、应用对接

- 用各语言 **S3 SDK**：endpoint 指向 MinIO、配 access/secret key、region；
- 私有文件用 **预签名 URL（presigned URL）**临时授权上传/下载；
- 架构：应用/网页 → MinIO，图片访问可经 **Nginx 反代或 CDN**；
- 图片处理/媒体转码可在上传后对接处理服务。

---

#### 本章自测

1. APISIX 为什么能热更新？etcd 在其中起什么作用？
2. Route、Upstream、Consumer 分别是什么？
3. DAS、NAS、SAN 的区别？块级和文件级存储有什么不同？
4. 对象存储和文件存储有什么区别？为什么对象存储适合海量图片？
5. MinIO 的纠删码解决什么问题？分布式部署最少几个节点？
6. 什么是预签名 URL，解决什么问题？

#### 相关速查

- [kubectl 命令速查](/reference/kubectl-commands)
- [Linux 命令速查](/reference/linux-commands)
- APISIX 文档：https://apisix.apache.org/docs/
- MinIO 文档：https://min.io/docs/minio/linux/index.html

</details>

<details>
<summary><strong>Kafka — Kafka 高吞吐原理、topic/partition/副本/ISR/消费组/offset、KRaft 部署、topic 管理、生产消费、消费堆积与 lag、消息不丢不重顺序、rebalance 与监控</strong></summary>

::: tip 本篇定位
理解消息队列**解耦/异步/削峰**和 Kafka **高吞吐原理**，掌握**分区、副本、ISR、消费组、offset**，用 **KRaft** 部署集群，完成 topic 管理、生产消费、消费组运维，并解决**消息丢失/重复/顺序、堆积、rebalance**。
:::

#### 先建立全局观：Kafka 为什么吞吐高

| 机制 | 说明 |
|---|---|
| 磁盘顺序写 | 消息追加写（append），顺序写磁盘接近内存速度 |
| 页缓存 Page Cache | 读写依赖 OS 缓存，数据先落缓存 |
| 零拷贝 sendfile | 数据直接从页缓存到网卡，不经过用户态拷贝 |
| 分区并行 | topic 拆分区，多节点多分区并行读写 |
| 批量 + 压缩 | 消息批量发送、按批压缩（snappy/lz4/zstd） |

---

#### 一、简介

##### 1.1 消息队列的作用

| 作用 | 说明 |
|---|---|
| 解耦 | 生产与消费不直接依赖，独立演进 |
| 异步 | 耗时操作异步处理，快速响应 |
| 削峰填谷 | 突发流量先入队，按消费能力处理，保护下游 |

##### 1.2 Kafka 特点与选型

Kafka 是分布式高吞吐、可持久化、可回放的消息与流平台，常用于日志收集、数据管道、大数据、事件驱动、流处理（Kafka Streams）。

| MQ | 特点 | 适合 |
|---|---|---|
| **Kafka** | 吞吐极高、分区并行、可回放、生态 | 日志、大数据、高吞吐管道 |
| RabbitMQ | 路由灵活、确认完善、协议丰富、延迟低 | 业务消息、复杂路由 |
| RocketMQ | 事务/顺序消息、阿里开源 | 电商金融 |
| Pulsar | 存算分离、多租户 | 云原生消息 |

---

#### 二、核心概念

| 概念 | 说明 |
|---|---|
| Producer | 生产者，发布消息 |
| Consumer | 消费者，拉取消息 |
| Broker | 一个 Kafka 节点，多节点组成集群 |
| Topic | 消息的逻辑分类 |
| **Partition 分区** | topic 拆成多个分区分布在 broker，是**并行和扩展单位**；消息只在**分区内有序** |
| **Replica 副本** | 每分区一个 **Leader**（读写）、多个 **Follower**（同步、备份） |
| **Consumer Group** | 消费组：一条消息只被组内一个消费者消费；不同组各自消费全量 |
| **Offset** | 消息在分区中的唯一编号；消费位置提交到内部 topic |
| **ISR** | 与 Leader 保持同步的副本集合；故障从 ISR 选新 Leader |
| AR / OSR | 所有副本 / 同步落后的副本；AR = ISR + OSR |
| LEO / HW | 日志末端偏移 / 高水位（HW 之前的消息才对消费者可见） |

> 一个分区在一个消费组内最多被一个消费者消费，消费者数超过分区数会有空闲——**分区数决定消费并行度**。

---

#### 三、部署（KRaft 模式）

Kafka 3.3 起 KRaft 生产可用、3.5 弃用 ZooKeeper。KRaft 把元数据 quorum 内置在 Kafka，组件更少。

##### 3.1 二进制部署

```bash
# https://kafka.apache.org/downloads 下载 3.9.x（scala 2.13）
tar -xzf kafka_2.13-3.9.0.tgz && cd kafka_2.13-3.9.0

KAFKA_CLUSTER_ID="$(bin/kafka-storage.sh random-uuid)"
bin/kafka-storage.sh format -t "$KAFKA_CLUSTER_ID" -c config/kraft/server.properties
bin/kafka-server-start.sh -daemon config/kraft/server.properties
```

关键配置 `config/kraft/server.properties`：

```properties
process.roles=broker,controller
node.id=1
controller.quorum.voters=1@10.0.0.13:9093,2@10.0.0.14:9093,3@10.0.0.15:9093
listeners=PLAINTEXT://10.0.0.13:9092,CONTROLLER://10.0.0.13:9093
advertised.listeners=PLAINTEXT://10.0.0.13:9092
log.dirs=/data/kafka-logs
num.partitions=3
default.replication.factor=3
min.insync.replicas=2
offsets.topic.replication.factor=3
unclean.leader.election.enable=false
auto.create.topics.enable=false
```

##### 3.2 Docker（KRaft）

```bash
docker run -d --name kafka -p 9092:9092 \
  -e KAFKA_NODE_ID=1 \
  -e KAFKA_PROCESS_ROLES=broker,controller \
  -e KAFKA_CONTROLLER_QUORUM_VOTERS=1@localhost:9093 \
  -e KAFKA_LISTENERS=PLAINTEXT://:9092,CONTROLLER://:9093 \
  -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://203.0.113.10:9092 \
  -e KAFKA_CONTROLLER_LISTENER_NAMES=CONTROLLER \
  -e KAFKA_LISTENER_SECURITY_PROTOCOL_MAP=CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT \
  -v /data/kafka:/tmp/kraft-combined-logs \
  apache/kafka:3.9.0
```

> 生产集群至少 3 broker、副本因子 3、controller quorum 配 3 节点。

---

#### 四、Topic 管理

```bash
# 创建（分区数、副本因子）
bin/kafka-topics.sh --create --topic test \
  --partitions 3 --replication-factor 3 \
  --bootstrap-server localhost:9092

bin/kafka-topics.sh --list --bootstrap-server localhost:9092

# 详情：Leader、Replicas、ISR
bin/kafka-topics.sh --describe --topic test --bootstrap-server localhost:9092
# PartitionCount、ReplicationFactor、Isr

# 修改（分区只能增加）、删除
bin/kafka-topics.sh --alter --topic test --partitions 6 --bootstrap-server localhost:9092
bin/kafka-topics.sh --delete --topic test --bootstrap-server localhost:9092

# 配置
bin/kafka-configs.sh --entity-type topics --entity-name test \
  --add-config retention.ms=86400000 --bootstrap-server localhost:9092
```

---

#### 五、生产与消费

##### 5.1 命令行

```bash
# 生产者（开启 key，默认 key/tab/value）
bin/kafka-console-producer.sh --topic test --bootstrap-server localhost:9092 \
  --property parse.key=true --property key.separator=:

# 消费者
bin/kafka-console-consumer.sh --topic test --bootstrap-server localhost:9092 \
  --from-beginning --group g1 \
  --property print.key=true --property key.separator=:
```

##### 5.2 客户端关键参数（了解）

- Producer：`acks`（0/1/all）、`retries`、`enable.idempotence`、`compression.type`、`linger.ms`、`batch.size`；
- Consumer：`group.id`、`enable.auto.commit`、`auto.offset.reset`（earliest/latest）、`max.poll.records`；
- key 决定消息进入哪个分区（相同 key 同分区）。

---

#### 六、运维

##### 6.1 分区与副本

```bash
# 扩分区
bin/kafka-topics.sh --alter --topic test --partitions 6 --bootstrap-server localhost:9092

# 副本重分配：--generate 生成计划 → --execute 执行 → --verify 验证
bin/kafka-reassign-partitions.sh --bootstrap-server localhost:9092 \
  --topics-to-move-json-file topics.json --broker-list "1,2,3" --generate

# 优先副本 Leader 选举（均衡 leader）
bin/kafka-leader-election.sh --bootstrap-server localhost:9092 \
  --election-type preferred --all-topic-partitions
```

##### 6.2 消费组与 Lag

```bash
bin/kafka-consumer-groups.sh --list --bootstrap-server localhost:9092
bin/kafka-consumer-groups.sh --describe --group g1 --bootstrap-server localhost:9092
# TOPIC PARTITION CURRENT-OFFSET LOG-END-OFFSET LAG CONSUMER-ID
```

`LAG = LOG-END-OFFSET - CURRENT-OFFSET`，即未消费的积压条数。

```bash
# 重置 offset（组无活跃消费者）
bin/kafka-consumer-groups.sh --group g1 --topic test \
  --reset-offsets --to-earliest --execute --bootstrap-server localhost:9092
# --to-latest / --to-offset n / --to-datetime
```

##### 6.3 监控指标

| 指标 | 含义 |
|---|---|
| Consumer Lag | 消费积压（核心告警） |
| UnderReplicatedPartitions | 副本未同步分区（>0 告警） |
| ISR 收缩/扩缩 | 同步异常 |
| ActiveController | 控制器是否唯一 |
| 吞吐 bytes in/out、请求队列、磁盘/CPU | 容量性能 |

---

#### 七、可靠性与常见问题

##### 7.1 消息不丢失

| 环节 | 措施 |
|---|---|
| 生产端 | `acks=all`、`retries>0`、`enable.idempotence=true` |
| Broker | 副本因子 ≥3、`min.insync.replicas≥2`、`unclean.leader.election.enable=false` |
| 消费端 | 处理完成后**再手动提交** offset |

##### 7.2 消息不重复（幂等/精确一次）

- 生产端开启**幂等**（`enable.idempotence=true`，PID+序列号去重）；
- 跨分区/会话用 **Kafka 事务**；
- 消费端做**业务幂等**（唯一键、去重表、状态判断）——offset 提交与处理非原子，重复难完全避免。

##### 7.3 消息顺序

- 全局有序用单分区（牺牲并行）；
- 业务有序让相关消息用**相同 key** 路由同分区；
- 单分区单消费者、失败不打乱顺序。

##### 7.4 消费堆积

排查消费为何慢（下游 DB/接口、处理逻辑）→ 增加分区 + 消费者（不超分区数）→ 临时扩消费者/批量处理 → 限流保护下游。

##### 7.5 频繁 Rebalance

消费者处理过久、心跳超时会被踢出组触发 rebalance。措施：调大 `session.timeout.ms`、`max.poll.interval.ms`，减少单次 poll 处理量，用**静态成员**（group.instance.id）避免重启触发。

---

#### 本章自测

1. Kafka 为什么吞吐高？顺序写、页缓存、零拷贝分别解决什么？
2. Partition、Replica、ISR、HW 分别是什么？
3. 为什么消费者数超过分区数会有空闲？
4. KRaft 相比 ZooKeeper 模式有什么优势？
5. 如何保证消息不丢失？min.insync.replicas 和 acks=all 怎么配合？
6. 如何保证消息不重复 / 精确一次？
7. 如何保证消息顺序？
8. 消费堆积怎么排查和处理？什么是 rebalance，如何减少？

#### 相关速查

- [Linux 命令速查](/reference/linux-commands)
- Kafka 官方文档：https://kafka.apache.org/documentation/
- KRaft：https://kafka.apache.org/documentation/#kraft

</details>

<details>
<summary><strong>Spring Cloud 微服务 — 架构演进与微服务特点、Spring Cloud Alibaba 版本配套、Nacos 注册配置、Sentinel 限流熔断、Seata 分布式事务 AT、Gateway 路由限流、OpenFeign 与链路追踪</strong></summary>

::: tip 本篇定位
理解架构演进与微服务本质，掌握 **Spring Cloud Alibaba** 全家桶：**Nacos**（注册 + 配置）、**Sentinel**（限流熔断）、**Seata**（分布式事务）、**Gateway**（网关），并了解 OpenFeign 与链路追踪。
:::

#### 先建立全局观：为什么需要这么多组件

单体应用里，方法调用、配置、事务都在一个进程内完成。拆成微服务后，这些原本"天然成立"的事都变成了跨网络问题，需要专门组件解决：

| 单体里天然有的 | 微服务里由谁解决 |
|---|---|
| 我知道调用谁 | 注册中心（Nacos） |
| 配置统一管理 | 配置中心（Nacos） |
| 一个方法直接调用 | OpenFeign / Dubbo |
| 本地事务 | Seata 分布式事务 |
| 一个入口 | Gateway |
| 扛不住流量 | Sentinel 限流熔断 |
| 出问题能排查 | 链路追踪（SkyWalking） |

---

#### 一、微服务概述

##### 1.1 架构演进

| 阶段 | 特点 | 问题 |
|---|---|---|
| 单体架构 | 所有模块打成一个包部署 | 耦合重、技术栈统一、扩展要整体扩、迭代慢 |
| SOA | 服务化，通过 **ESB（企业服务总线）** 集成 | ESB 笨重、易成单点瓶颈、成本高 |
| **微服务** | 拆成一组小服务，独立进程、独立部署 | 分布式复杂度高 |

##### 1.2 微服务特点

- **单一职责**：一个服务只做好一块业务；
- **独立**：独立进程、独立开发部署、独立数据库/技术栈；
- **轻量通信**：REST（HTTP）或 RPC（Dubbo/gRPC）；
- **去中心化治理**：数据、治理各自独立，自动化部署。

##### 1.3 优缺点

优点：粒度小易理解、可独立技术栈/扩展、故障隔离、小团队自治。
缺点：服务拆分增加开发/测试/运维复杂度、分布式事务/数据一致性、链路追踪难、服务治理复杂。**小系统盲目拆分反而增加成本。**

##### 1.4 Spring Cloud 与版本配套

Spring Cloud 是基于 Spring Boot 的微服务规范与全家桶，国内主流 **Spring Cloud Alibaba**：

| 能力 | 组件 |
|---|---|
| 注册/配置 | Nacos |
| 限流熔断 | Sentinel |
| 分布式事务 | Seata |
| 网关 | Spring Cloud Gateway |
| 服务调用 | OpenFeign / Dubbo |
| 负载均衡 | Spring Cloud LoadBalancer |
| 链路追踪 | Micrometer Tracing + SkyWalking/Zipkin |

::: warning 版本必须配套（重点，最易踩坑）
以当前主流一套为例：

| Spring Boot | Spring Cloud | Spring Cloud Alibaba | JDK |
|---|---|---|---|
| 3.2.x | 2023.0.x (Leyton) | 2023.0.1.x | 17 |

三者版本号没有数字对应关系，必须查官方版本说明对齐；随意混用会出现启动报错、类找不到。
:::

---

#### 二、Nacos

Nacos = **注册中心 + 配置中心**。

##### 2.1 注册中心

- 服务启动时注册自己的 IP/端口，消费者从 Nacos 拉取实例列表做调用和负载均衡；
- 健康检查：**临时实例**（客户端心跳，AP，Distro 协议）、**非临时实例**（服务端主动探测，CP，Raft）；
- 实例不健康会被摘除。

##### 2.2 配置中心

- 统一管理各环境配置，修改后**动态推送、无需重启**；
- 三级隔离：**Namespace（环境，如 dev/test/prod）→ Group（分组）→ Data ID（具体配置文件）**。

##### 2.3 部署

```bash
# 单机
docker run -d --name nacos -p 8848:8848 -p 9848:9848 \
  -e MODE=standalone nacos/nacos-server:v2.4.3
# 控制台 http://IP:8848/nacos  默认 nacos/nacos
```

生产集群：至少 **3 节点**、共享 **MySQL** 持久化配置、内部 Raft/Distro 保证一致，前置负载均衡。

##### 2.4 应用接入

```yaml
spring:
  application:
    name: user-service
  cloud:
    nacos:
      discovery:
        server-addr: 10.0.0.13:8848
      config:
        server-addr: 10.0.0.13:8848
        file-extension: yaml
        namespace: dev
```

依赖 `spring-cloud-starter-alibaba-nacos-discovery`、`-config`。

---

#### 三、Sentinel

Sentinel 做**流量控制、熔断降级、系统负载保护**，替代已停更的 Hystrix。

##### 3.1 核心概念：资源与规则

- **资源**：被保护的方法/接口（`@SentinelResource`）；
- **规则**：围绕资源设置的流控/熔断规则。

##### 3.2 限流

- 阈值类型：**QPS** 或 **并发线程数**；
- 流控模式：直接、关联（关联资源达阈值限流自己）、链路；
- 流控效果：快速失败、Warm Up（冷启动）、排队等待。

##### 3.3 熔断降级

| 策略 | 触发条件 |
|---|---|
| 慢调用比例 | 平均 RT 超过阈值的比例达限 |
| 异常比例 | 异常占比超阈值 |
| 异常数 | 异常条数超阈值 |

熔断后进入 OPEN（拒绝请求）→ 经过时长进入 HALF-OPEN（试探）→ 恢复或继续熔断。

##### 3.4 Dashboard 与持久化

```bash
java -Dserver.port=8080 -jar sentinel-dashboard-1.8.8.jar
# 默认 sentinel/sentinel
```

规则默认存内存、重启丢失，生产可持久化到 **Nacos**（数据源 datasource）。

---

#### 四、Seata

Seata 解决跨服务/跨库的**分布式事务**。

##### 4.1 三个角色

| 角色 | 说明 |
|---|---|
| **TC** | 事务协调器（Seata Server），维护全局事务、驱动提交/回滚 |
| **TM** | 事务管理器，发起/提交/回滚全局事务 |
| **RM** | 资源管理器，管理分支事务与本地资源 |

##### 4.2 AT 模式（最常用，自动）

- 每个业务库建 **undo_log** 表；
- 一阶段：执行业务 SQL，同时记录**前镜像/后镜像**到 undo_log，提交本地事务、释放锁；
- 二阶段：全局提交 → 异步删 undo_log；全局回滚 → 按 undo_log **自动反向补偿**。

##### 4.3 其他模式

TCC（手动 Try/Confirm/Cancel，无锁、性能高但侵入）、SAGA（长事务）、XA（强一致、资源锁定久）。

##### 4.4 部署与接入

```bash
docker run -d --name seata-server -p 8091:8091 -p 7091:7091 \
  apache/seata-server:2.0.0
```

业务加 `spring-cloud-starter-alibaba-seata`，入口方法标注：

```java
@GlobalTransactional
public void createOrder(...) { ... }
```

---

#### 五、Gateway

Spring Cloud Gateway 基于 WebFlux/Netty，**非阻塞、高吞吐**，替代 Zuul，作为统一入口。

##### 5.1 核心概念

| 概念 | 说明 |
|---|---|
| Route | id + 目标 uri + Predicates + Filters |
| Predicate 断言 | Path、Method、Header、Host、时间、参数 |
| Filter 过滤器 | 加头、改路径、鉴权、限流 |

##### 5.2 配置

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: user-service
          uri: lb://user-service        # lb 从 Nacos 按服务名负载均衡
          predicates:
            - Path=/api/user/**
          filters:
            - StripPrefix=2
            - AddRequestHeader=X-From, gateway
```

##### 5.3 限流与跨域

- `RequestRateLimiter` 基于 **Redis + 令牌桶**，按用户/IP/接口限流；
- 统一处理跨域 CORS、鉴权、日志、灰度。

---

#### 六、服务调用与链路追踪

##### 6.1 OpenFeign

声明式 HTTP 调用：定义接口 + `@FeignClient("服务名")`，像调本地方法一样调远程服务，内置负载均衡。

##### 6.2 链路追踪

微服务一次请求经过多个服务，需要链路追踪串起调用链（Trace ID / Span ID）。常用 **SkyWalking**（国产、功能全、字节码无侵入）、Micrometer Tracing + Zipkin/Tempo，配合日志定位跨服务问题。

---

#### 本章自测

1. 单体、SOA、微服务的区别？微服务有什么优缺点，适合所有项目吗？
2. Spring Boot、Spring Cloud、Spring Cloud Alibaba 版本为什么必须配套？
3. Nacos 注册中心临时实例和非临时实例有什么区别？配置如何做环境隔离？
4. Sentinel 限流的 QPS 和线程数模式、熔断的三种策略分别是什么？
5. Seata 的 TC/TM/RM 角色？AT 模式两阶段怎么做的？
6. Gateway 的 Route/Predicate/Filter 是什么？如何限流？
7. 分布式链路追踪解决什么问题？

#### 相关速查

- [Linux 命令速查](/reference/linux-commands)
- Spring Cloud Alibaba：https://sca.aliyun.com/docs/
- Nacos：https://nacos.io/zh-cn/docs/what-is-nacos.html
- Sentinel：https://sentinelguard.io/zh-cn/docs/introduction.html
- Seata：https://seata.apache.org/zh-cn/docs/overview/what-is-seata/
- Gateway：https://docs.spring.io/spring-cloud-gateway/reference/

</details>

<!-- merged-guide-material:end -->
