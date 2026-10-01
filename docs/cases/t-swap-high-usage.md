---
category: Linux
difficulty: 中级
date: 2023-12-05
---

# swap 占用高、swappiness 调优与内存压力（2023-12-05）

## 现象

监控告警：一台应用服务器 swap 使用率持续 90%，且 `si`/`so`（swap in/out）持续有数据：

```bash
free -h
#               total        used        free      shared  buff/cache   available
# Mem:            15G        12G        500M        200M        2.5G        1.5G
# Swap:          4.0G        3.6G        400M
```

```bash
vmstat 1 3
# procs -----------memory---------- ---swap-- -----io----
#  r  b   swpd   free  buff  cache   si   so    bi    bo
#  2  1 3600000 500000  10000 2500000  100  200   500   800
```

`si 100` `so 200` 表示每秒有 100KB 从 swap 换入、200KB 换出，系统在频繁抖动。

## 环境

- 发行版：Ubuntu 22.04.3 LTS
- 内核：`6.2.0-35-generic`
- 内存：16GB
- swap：4GB（`/swapfile`）
- 业务：Java 服务堆 4G，其他几个小服务

## 定位过程

### 1. 先判断 swap 高是"真缺内存"还是"内核闲的把冷页换出去"

很多人一看到 swap 高就慌，其实不一定。关键看 `si`/`so` 有没有持续数据：

```bash
vmstat 1 5
# 如果 si/so 长期是 0，只是历史上内存压力大换出去过，现在不活动，不用管
# 如果 si/so 持续有几百 KB~MB，说明系统在频繁换入换出，真的内存不足
```

本例 `si 100 so 200`，持续抖动，是真问题。

### 2. 看 swappiness 当前值

```bash
cat /proc/sys/vm/swappiness
# 60
```

`swappiness` 默认 60，范围 0~100。值越高，内核越积极地把匿名页换出到 swap。
对服务器（特别是数据库/Java）来说 60 太高，一般建议 10 甚至 1。

### 3. 看内存都被谁占了

```bash
free -h
ps aux --sort=-rss | head -10
smem -k --sort=-pss | head
```

本例 Java 进程 RSS 占了 5G，远超 `-Xmx 4g`，堆外内存泄漏。

### 4. 看是不是某进程疯狂 malloc 又 free 导致的抖动

```bash
# 看每个进程的 swap 占用
for f in /proc/*/status; do awk '/VmSwap/{print $2, $f}' $f; done | sort -rn | head
# 1024000 /proc/1234/status   <- java 进程换出了 1G
```

## 根因

Java 进程堆外内存泄漏，RSS 慢慢涨到 5G，加上其他服务，16G 物理内存不够用。内核按照 swappiness=60 的默认策略，把不活跃的匿名页换到 swap，导致 swap 占用高、si/so 持续抖动，应用延迟变大。

## 解决步骤

### 1. 临时止血：调低 swappiness，让内核少用 swap

```bash
# 立刻生效
sysctl vm.swappiness=10

# 永久生效，写进 /etc/sysctl.conf
echo 'vm.swappiness=10' >> /etc/sysctl.conf
sysctl -p
```

对数据库（MySQL/PostgreSQL）和 Java 服务，建议 1~10。
对桌面/笔记本可以保持 60。

注意：调 swappiness 不会立刻把 swap 里的数据换回来，只是减少以后换出的倾向。

### 2. 如果 swap 里有大量数据想清回来

**不要直接 `swapoff -a && swapon -a`**，物理内存不够时会直接 OOM。
正确做法：先确认 available 足够大，再操作：

```bash
free -h   # 看 available 能不能容下 swap 里的数据
# 如果 available > swap used，安全：
swapoff -a && swapon -a
```

### 3. 彻底修复：找到吃内存的进程

这才是根本。swap 高往往是内存不足的症状，不是病因。

- Java 进程：加 `-XX:MaxDirectMemorySize`、检查堆外缓存。
- 数据库：调 `innodb_buffer_pool_size`，不要让 OS cache 和 buffer pool 打架。
- 应用：修内存泄漏（参考 [内存泄漏与 OOM](/cases/t-memory-leak-oom)）。

### 4. 加物理内存或加 swap

如果业务确实需要这么多内存：
- 优先加物理内存。
- 实在加不了，加 swap 当兜底（但 swap 慢，不能当内存用）。

## 验证与预防

- 调优后 `vmstat 1` 观察 `si/so` 回落到 0。
- 监控补：swap 使用率、si/so 速率、`MemAvailable`。
- 告警阈值：swap 使用 > 50% 预警，si/so 持续 > 100KB/s 告警。
- 服务器上 swappiness 统一配 10，不要用默认 60。
- 记住：**swap 高不一定是病，持续 si/so 才是病**。

## 相关

- 命令速查：[Linux 命令速查](/reference/linux-commands)
- 内存方向：[内存泄漏与 OOM Killer](/cases/t-memory-leak-oom)
- 容器方向：[Docker swap 限制不生效](/cases/t-docker-swap)
- 巡检清单：[运维巡检清单](/reference/ops-checklists)
