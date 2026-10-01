---
category: Linux
difficulty: 高级
date: 2021-08-25
---

# 内存泄漏与 OOM Killer 分析（2021-08-25）

## 现象

一台跑 Java 服务的服务器，半夜突然挂掉，业务全部不可用。
SSH 上去后 `free -h` 看到内存几乎被吃光：

```
              total        used        free      shared  buff/cache   available
Mem:            15G         14G        200M        100M        800M        300M
Swap:            2G         1.8G       200M
```

`dmesg` 里刷出大量 OOM Killer 日志：

```
java invoked oom-killer: gfp_mask=0x280da, order=0, oom_score_adj=0
Tasks state (memory values in pages):
[ pid ]   uid  tgid total_vm      rss
 1234  1000  1234  820000  380000
Memory cgroup out of memory: Killed process 1234 (java) total-vm:3280000kB, anon-rss:1520000kB
```

## 环境

- 发行版：CentOS Linux release 7.9.2009 (Core)
- 内核：`3.10.0-1160.el7.x86_64`
- 业务：Tomcat 9.0.52，JDK 11.0.11
- 容器化：未使用 Docker，直接裸机跑

## 定位过程

### 1. 先确认是真的内存不足，还是被 cache 骗了

```bash
free -h
# 看 available 而不是 free！buff/cache 是可以被回收的，不算真占用
cat /proc/meminfo | grep -E 'MemAvailable|MemFree|Buffers|Cached'
```

`available` 才是内核估算的"还能给应用用多少内存"。本例 available 只有 300M，确实是真紧张。

### 2. 找出谁在吃内存

```bash
# 按 RSS 排序看前 10
ps aux --sort=-rss | head -11

# 更精确：用 smem 按 PSS 排序（把共享库分摊掉）
smem -k --sort=-pss | head
```

输出里 `java` 进程 RSS 占到了 13G，远超 `-Xmx` 配置的 4G。

### 3. 看 OOM Killer 到底杀了谁、为什么是它

```bash
dmesg -T | grep -i -A5 "oom-killer\|Out of memory"
# 或
grep -i "killed process" /var/log/messages
```

OOM Killer 会挑 `oom_score` 最高的进程杀掉。`oom_score` 跟进程占用内存正相关，所以一般杀的就是最大那个。

### 4. Java 进程为什么 RSS 比 Xmx 大很多

这是 Java 常见坑：

```bash
# 看 JVM 实际内存分布
jstat -gcutil <pid> 1s 5
# 看堆外内存（Metaspace、线程栈、直接内存、JNI）
pmap -x <pid> | tail -1
```

如果 `jstat` 显示堆（Eden/Survivor/Old）没满，但 RSS 一直涨，那就是堆外泄漏（Direct ByteBuffer、Metaspace、线程没回收）。

### 5. 抓堆 dump 分析（事后）

```bash
# 触发 OOM 时自动 dump（下次复现）
# 在启动参数加：
# -XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=/var/log/heapdump.hprof

# 事后手动 dump（会暂停应用几秒，谨慎）
jmap -dump:format=b,file=/var/log/heapdump.hprof <pid>
# 用 MAT / jvisualvm 打开看 Dominator Tree
```

## 根因

一次发版引入了一个本地缓存（Guava Cache）没设 `maximumSize`，无限往里面塞对象，Old 区持续上涨。Full GC 又回收不掉（都是强引用），最终堆内存顶到 `-Xmx`，JVM 抛 OOM，但此时 JVM 已经无法申请新的本地内存，直接被系统的 OOM Killer 杀掉。

## 解决步骤

### 1. 临时止血

```bash
# 先重启服务恢复业务
systemctl restart tomcat

# 如果机器上还有别的重要进程被牵连，先手动把大内存但不重要的进程 kill 掉
kill -TERM <pid>
```

### 2. 彻底修复

- 给 Guava Cache 加上 `maximumSize(10000)` 和 `expireAfterWrite(10min)`。
- JVM 启动参数加上自动 dump：

```
-Xms4g -Xmx4g
-XX:+HeapDumpOnOutOfMemoryError
-XX:HeapDumpPath=/var/log/heapdump.hprof
-XX:MaxMetaspaceSize=512m
```

### 3. 加 swap 兜底（不是解决方案，只是缓冲）

```bash
# 确认 swap 存在
swapon --show
# 没有的话临时加一个
fallocate -l 4G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap defaults 0 0' >> /etc/fstab
```

注意：swap 只是兜底，不能替代修泄漏。

## 验证与预防

- 修复后观察 24 小时，`jstat` 看 Old 区在 Full GC 后能回落到正常水位。
- 监控补：`used memory / available memory`、JVM 堆使用率、Full GC 次数和耗时。
- 告警阈值：内存可用率 < 10% 持续 3 分钟告警；OOM Killer 事件（dmesg 关键字）实时告警。
- 不要用 `free` 当监控指标，要用 `MemAvailable`。

## 相关

- 命令速查：[Linux 命令速查](/reference/linux-commands)
- CPU 方向：[CPU 飙高定位](/cases/t-cpu-high-load)
- Swap 方向：[swap 占用高与 swappiness 调优](/cases/t-swap-high-usage)
- Java 方向：[Tomcat 内存溢出崩溃](/cases/t-tomcat-oom-crash)
