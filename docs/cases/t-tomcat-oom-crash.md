---
category: 服务
difficulty: 高级
date: 2020-08-07
---

# Tomcat 内存溢出 / 崩溃（2020-08-07）

## 现象

Tomcat 跑着跑着突然挂掉，日志里：

```
java.lang.OutOfMemoryError: Java heap space
Exception in thread "http-nio-8080-exec-10" java.lang.OutOfMemoryError: Java heap space
#
# There is insufficient memory for the Java Runtime Environment to continue.
# Native memory allocation (malloc) failed to allocate ...
```

或者：

```
java.lang.OutOfMemoryError: Metaspace
```

Tomcat 进程直接退出，`systemctl status tomcat` 显示 failed。

## 环境

- 发行版：CentOS Linux release 7.8.2003 (Core)
- 内核：`3.10.0-1127.el7.x86_64`
- Tomcat 9.0.30
- JDK 1.8.0_262
- 启动参数：`JAVA_OPTS="-Xms1g -Xmx1g"`（没配其他）

## 定位过程

### 1. 看是哪种 OOM

| 报错 | 含义 | 去哪查 |
|---|---|---|
| `Java heap space` | 堆满了 | jmap dump 堆，看谁占内存 |
| `Metaspace` | 类元数据满 | 动态生成类/CGLib泄漏 |
| `unable to create new native thread` | 线程数超限 | 线程池没关 |
| `Direct buffer memory` | 堆外内存泄漏 | NIO/Netty |
| `GC overhead limit exceeded` | GC 花 98% 时间只回收 <2% | 快堆满了 |

### 2. 先看 JVM 堆配置

```bash
ps -ef | grep tomcat
# 看到 -Xms -Xmx
# JAVA_OPTS=-Xms1g -Xmx1g
```

1G 堆对一个跑了一堆缓存的应用偏小。

### 3. 确认有没有自动 dump

```bash
ls -lh /var/log/
# 看有没有 java_pid<hprof>.hprof
```

如果没有，下次 OOM 时先加参数：

```
-XX:+HeapDumpOnOutOfMemoryError
-XX:HeapDumpPath=/var/log/heapdump.hprof
```

### 4. 事后手动 dump（如果进程还在）

```bash
jmap -dump:format=b,file=/var/log/heap.hprof <pid>
# 用 MAT (Eclipse Memory Analyzer) 打开
# 看 Dominator Tree，找最大的对象
```

### 5. 看 GC 情况

```bash
jstat -gcutil <pid> 1s 10
#  E  O  M  YGC YGCT FGC FGCT
# 100 100 95  100 5.0  20 10.0
# Old 100%，Full GC 20 次还回收不掉 = 内存泄漏
```

### 6. 看线程数

```bash
jstack <pid> | grep "java.lang.Thread.State" | wc -l
# 线程数超过几千，且大量 RUNNABLE，可能线程泄漏
```

## 根因

一个导出 Excel 的功能，把整张表 100 万行全查出来放进 `List<Row>` 再写 Excel，堆 1G 根本装不下，直接 OOM。每次有人点导出就挂。

## 解决步骤

### 1. 临时止血

```bash
# 先重启
systemctl restart tomcat
```

### 2. 加 dump 参数，下次能留现场

`/etc/tomcat/tomcat.conf` 或 `bin/setenv.sh`：

```bash
JAVA_OPTS="-Xms2g -Xmx2g
-XX:MetaspaceSize=256m
-XX:MaxMetaspaceSize=512m
-XX:+HeapDumpOnOutOfMemoryError
-XX:HeapDumpPath=/var/log/heapdump.hprof
-XX:+PrintGCDetails
-Xloggc:/var/log/tomcat-gc.log"
```

### 3. 修代码：导出不要全加载

- 用流式查询（ResultSet 逐行读）。
- 用 SXSSFWorkbook 流式写 Excel，不要 XSSFWorkbook 全放内存。
- 大数据量导出丢异步任务，不要同步 HTTP 等。

### 4. 如果是 Metaspace OOM

- 加 `-XX:MaxMetaspaceSize=512m`。
- 查是不是热部署反复加载类没卸载。

### 5. 如果是线程泄漏

- 查线程池是不是 `Executors.newCachedThreadPool()` 无界队列。
- 用有界线程池 + 拒绝策略。

## 验证与预防

- 修复后 `jstat -gcutil` 看 Old 区在 Full GC 后回落到 50% 以下。
- 压测导出功能不再 OOM。
- 监控补：JVM 堆使用率、Old 区使用率、Full GC 次数、Metaspace 使用率。
- 告警阈值：Old 区 > 80%、Full GC > 1 次/分钟。
- 记住：**Tomcat OOM 先加 dump 参数留现场，再修代码，不要只加 -Xmx**。

## 相关

- 命令速查：[Linux 命令速查](/reference/linux-commands)
- 内存方向：[内存泄漏与 OOM Killer](/cases/t-memory-leak-oom)
- 服务方向：[Nginx 502 Bad Gateway](/cases/t-nginx-502)
- 服务方向：[LB 后端被健康检查摘除](/cases/t-lb-backend-ejected)
