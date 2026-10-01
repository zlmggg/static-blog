---
category: 架构
difficulty: 高级
---

# 疑难杂症专题：从现象到根因的定位手册

::: tip 本篇定位
面向中高级 SRE：把生产上最折腾人的七类疑难杂症，按统一结构「现象 → 定位命令 → 根因 → 处置 → 预防」写死。命令可直接复制，判据给数值。不重复 [linux-performance](./linux-performance) 的命令科普，这里是**组合拳和判据**。
本篇版本：JDK 21/25 LTS（jmap/jstack/jstat）、内核 4.18~7.0（dmesg/ss/slabtop）、MySQL 8.4 LTS、Redis 8.x。
:::

> 统一心法：**先看现象再猜，别上来就重启。** 重启会把现场（崩溃前的堆栈、连接、内存映射）蒸发掉。能保留现场就先 dump。

## 一、内存泄漏（Java 堆 / native）

### 现象
- 进程 RSS 只涨不降，重启后缓解、几周后复现；JVM 老年代 FGC 后回收不下来；系统 `available` 持续走低直到 OOM。

### 定位命令
```bash
# 1) 先确认是 Java 堆泄漏还是 native/堆外泄漏
jstat -gcutil <pid> 1000     # O（老年代）FGC 后是否回落
# 若 FGC 后老年代仍 >90% 不降 → 堆内泄漏
# 若老年代正常但 RSS 一直涨 → native/堆外泄漏（DirectBuffer、metaspace、堆外库）

# 2) 堆内：dump 后用 MAT / JProfiler 分析大对象
jmap -dump:live,format=b,file=/tmp/heap.hprof <pid>   # live 会触发一次 FGC
# 注意：dump 会 STW，大堆线上慎在高峰做

# 3) native：看进程内存映射分布
pmap -x <pid> | sort -k3 -n | tail -20     # 哪块 RSS 最大
# 关注 [anon] 持续增长、libxxx.so 映射、堆外 mmap

# 4) 内核 slab 缓存泄漏（非进程）
slabtop -o -s:c               # 看 dentry/inode/sock 等 slab 是否异常巨大
```

### 根因与处置
- **堆内**：MAT 看 Dominator Tree，找"被静态集合/缓存持有不释放"的对象。临时处置：扩容/重启；根治：修代码、给缓存加过期上限。
- **堆外**：Netty DirectByteBuffer 没释放、JNI 库泄漏。加 `-XX:MaxDirectMemorySize` 限住堆外，配 `-Dio.netty.leakDetectionLevel=ADVANCED`。
- **slab 泄漏**：`dentry`/`inode` 暴涨常是大量小文件/频繁创建删除，或内核已知 bug；升级内核或 `echo 2 > /proc/sys/vm/drop_caches` 临时回收（不治本）。

### 预防
加 `-XX:+HeapDumpOnOutOfMemoryError`；容器设 `--memory` 并监控 RSS 增长率；缓存一律设容量上限与 TTL。

## 二、fd / 连接耗尽

### 现象
- 业务报 `Too many open files` / `Cannot assign requested address` / 新建连接失败；`ss` 看到大量 TIME_WAIT 或 CLOSE_WAIT。

### 定位命令
```bash
ulimit -n                          # 当前进程 fd 软限制（默认常 1024）
cat /proc/<pid>/limits | grep "open files"   # 进程实际限制
ls /proc/<pid>/fd | wc -l          # 进程已用 fd 数
lsof -p <pid> | awk '{print $5}' | sort | uniq -c | sort -rn   # fd 都分给谁了
ss -s                              # 汇总：TIME_WAIT/CLOSE_WAIT 各多少
ss -tan state time-wait | wc -l    # TIME_WAIT 数量
ss -tan state close-wait | wc -l    # CLOSE_WAIT 数量
```

### 根因与处置
- **fd 数撞到 `ulimit -n`**：提高限制。systemd 里设 `LimitNOFILE=65535`（别只改 limits.conf，systemd 服务不读 PAM）。
- **CLOSE_WAIT 堆积**：对端关了连接，**自己应用没调用 close()**——是代码 bug（没正确关闭 socket/连接池），不是内核参数问题。
- **TIME_WAIT 过多**：高并发短连接，压测/出口调 `net.ipv4.tcp_tw_reuse=1` 与 `ip_local_port_range`（见 [config-best-practices](./config-best-practices)）。

### 预防
所有对外连接池化；监控 fd 使用率 >70% 告警；部署时在 unit 文件固化 LimitNOFILE。

## 三、OOM（系统 OOM Killer / JVM 堆溢出）

### 现象
- 进程突然消失、日志没了；`dmesg` 里有 `Out of memory: Killed process`；或 Java 报 `java.lang.OutOfMemoryError: Java heap space`。

### 定位命令
```bash
dmesg -T | grep -i -A5 -B5 "out of memory"   # 看 OOM Killer 杀了谁、当时内存
# 关键行：Killed process <pid> (<comm>)、以及进程内存占比
free -h
# JVM 侧
jmap -heap <pid> 2>/dev/null | head -20       # 堆配置与使用
# 容器场景：看是不是 cgroup OOMKilled
kubectl describe pod <pod> | grep -i oomkilled
```

### 根因与处置
- **系统 OOM Killer**：物理内存耗尽，内核挑"坏孩子"（oom_score 最高）杀。处置：加内存/限 `-Xmx`/加交换；找到吃内存的元凶（dmesg 里 oom_score 高的进程）。
- **JVM 堆溢出**：堆内泄漏（见专题一）或 `-Xmx` 给小了。处置：调大堆或修泄漏。
- **容器 OOMKilled**：JVM `-Xmx` 没算堆外，`--memory` 限得比 JVM 总占用小。处置：让 `Xmx + 堆外 + 元空间 < 容器 limit`，或用 `-XX:MaxRAMPercentage`。

### 预防
监控 `memory.usage` 与 RSS 增长曲线；JVM 开 HeapDumpOnOutOfMemoryError；容器内用 MaxRAMPercentage 而非写死 Xmx。

## 四、系统卡顿（load 高、D 状态、iowait）

### 现象
- SSH 上去输入命令半天没反应，`top` 里 load average 很高，但 CPU `%us` 不高。

### 定位命令
```bash
uptime                          # load average：1/5/15 分钟
# load > CPU 核数就是排队；但要看是"CPU 排队"还是"D 状态（IO 等待）排队"
top                             # 按 w 看进程状态列
ps -eo stat,pid,comm | grep '^D'    # 所有 D 状态（不可中断睡眠，多在等 IO）
vmstat 1                        # 看 r（运行队列）、b（阻塞）、wa（iowait）
iostat -xz 1                    # %util、await
```

### 根因与判据
- **load 高但 `%us` 低、`wa` 高、大量 D 状态** → 磁盘 IO 瓶颈，不是 CPU。查慢查询、大量随机写、swap。
- **load 高、`r` 队列长、`%us` 高** → CPU 真不够。
- **load 高但空闲** → 可能是大量 D 状态进程等 NFS/网络存储超时，存储挂了。

### 处置
- IO：定位是哪个进程（`iotop -o`），优化查询/批量写、换 SSD、加缓存。
- D 状态等 NFS：恢复存储或卸载卡死的 NFS 挂载。
- 临时别 kill D 状态进程（杀不动），先解决它等的资源。

## 五、丢包与重传

### 现象
- 偶发超时、RT 抖动、业务说"有时慢"，但 CPU/内存正常。

### 定位命令
```bash
ss -ti dst <目标IP>             # 看 TCP 连接细节：重传 rto、cwnd、ssthresh
nstat -az | grep -iE "retrans|drop|listen"
# 关注：TcpRetransSegs（重传段数）、TcpExtListenOverflows（全连接队列溢出）
netstat -s | grep -i retrans    # 累计重传
ethtool -S eth0 | grep -iE "drop|miss|error"   # 网卡丢包
ethtool eth0                     # 协商速率是否被降速
sar -n ETCP,ETCP6 1              # 重传率趋势
```

### 判据与处置
- **重传率 = 重传段 / 发送段 > 0.5%** → 网络问题：查链路、路由器、网卡半双工/降速、缓冲区。
- **`ListenOverflows` / `ListenDrops` 增长** → 全连接队列（somaxconn）小于应用 backlog，调高 `net.core.somaxconn` 和应用 backlog。
- **`rx_dropped`/`rx_missed_errors` 增长** → 网卡软中断处理不过来：开多队列（RPS/RSS）、调高网卡 ring buffer（`ethtool -G`）。
- **本机到本机重传** → 排查 conntrack 表满（`nf_conntrack: table full`）。

### 预防
监控重传率、队列溢出、网卡丢包；高并发前调 somaxconn；网卡多队列与 ring buffer 按机器调。

## 六、时钟跳变

### 现象
- 日志时间戳前后跳变、定时任务（cron/延迟队列）时间错乱、证书校验失败、分布式 token（JWT exp）判断异常。

### 定位命令
```bash
timedatectl                     # 看 System clock synchronized、NTP service
chronyc tracking                # chrony：最后同步、system time 漂移
chronyc sources
dmesg -T | grep -i clock        # 内核时钟调整日志
date; sleep 1; date             # 肉眼看是否跳
```

### 根因与处置
- 机器没跑 NTP/NTP 服务挂了，硬件时钟漂移；或虚拟化环境时钟不稳。处置：启用 chrony/systemd-timesyncd，保证所有节点时钟同步。
- 大跨度跳变（step）会让基于时间的逻辑出错；`slew`（慢慢校准）比 `step`（大步跳）友好。

### 预防
所有节点强制配 NTP/chrony；监控 `chronyc tracking` 的偏移量；K8s 节点时钟必须同步否则证书/etcd 出问题。

## 七、脏数据与脑裂（仲裁与 fencing）

### 现象
- 双主/主从切换后数据两边都在写、互相冲突；同一数据出现两个值；HA 集群两台都认为自己是主（脑裂）。

### 定位命令
```bash
# MySQL 主从
mysql> SHOW REPLICA STATUS\G     # 看 Seconds_Behind_Source、Seconds_Behind_Master、是否 SQL 线程报错
# 看当前谁是可写主
mysql> SHOW VARIABLES LIKE 'read_only';
# 哨兵/集群
redis-cli -p 26379 sentinel masters       # Redis Sentinel 视角谁是主
# Keepalived
ip a | grep virtual_ip                     # VIP 飘在哪台
```

### 根因与处置
- **脑裂**：两台都认为自己是主，因为脑裂期间仲裁通道也断了。处置：
  1. **先停一个主**（fencing，隔离），避免双写继续污染。
  2. 选数据新的一侧做主，另一侧重建从库。
  3. 人工核对冲突数据（按业务主键合并）。
- **脏数据**：切换瞬间未同步完的写入丢失或重复。

### 预防（关键机制）
- **法定仲裁（quorum）**：奇数节点（3/5），少数派自动降级为只读，避免"两个都活"。
- **fencing（隔离）**：主挂了切换前，先把旧主隔离（STOMITH：断电/拒写），保证旧主不可能再写。
- **VIP + 健康检查**：Keepalived/云 LB 配真实健康检查，别只 ping。
- 切换流程演练：平时就切，别等真故障第一次切。

## 排错速查表

| 现象 | 第一反应命令 | 大概率根因 |
|---|---|---|
| RSS 只涨不降 | `jstat -gcutil` / `pmap -x` | 堆/堆外泄漏 |
| Too many open files | `ls /proc/<pid>/fd \| wc -l` | ulimit 太低/连接泄漏 |
| 进程消失无日志 | `dmesg -T \| grep -i "killed"` | OOM Killer |
| load 高但 CPU 闲 | `ps -eo stat,pid,comm \| grep '^D'` | IO/存储等待 |
| 偶发超时抖动 | `ss -ti` / `nstat \| grep retrans` | 网络重传/队列溢出 |
| 日志时间跳 | `timedatectl` / `chronyc tracking` | 时钟未同步 |
| 双主都在写 | `SHOW REPLICA STATUS` / `sentinel masters` | 脑裂 |

::: warning 生产红线
- `jmap -dump:live`、`kill -9`、重启都会丢现场——**先取证再处置**，能 dump 就 dump。
- 别在高峰期对大堆 JVM 做 full GC 的 dump；选低峰或先摘流量。
- 脑裂处置第一步永远是**先隔离旧主**，不要两边同时写着谈"谁对谁错"。
- D 状态进程 kill 不动，要解决它等待的 IO/存储，而不是反复 kill。
:::

## 相关速查

- 单命令详解：[Linux 性能基础](./linux-performance)、[网络排障](./linux-network)
- 内核参数与 slab：[Linux 内核与 sysctl](./linux-kernel)
- 低损耗定位（perf/ftrace 替代）：[Linux eBPF](./linux-ebpf)
- 入侵导致的异常进程/外连：[安全应急响应](./expert-security-incident)
- MySQL 主从：[MySQL 数据](./data-mysql)、Redis 高可用：[Redis](./data-redis)
- 运维 Checklist：[/reference/ops-checklists](/reference/ops-checklists)

### 官方文档

- Java 工具（jmap/jstack/jstat）：https://docs.oracle.com/en/java/javase/25/docs/specs/man/
- ss/nstat 手册：https://man7.org/linux/man-pages/man8/ss.8.html
- MySQL Replication：https://dev.mysql.com/doc/refman/8.4/en/replication.html
- Redis Sentinel：https://redis.io/docs/latest/operate/oss_and_stack/management/sentinel/
- chrony：https://chrony-project.org/documentation.html
