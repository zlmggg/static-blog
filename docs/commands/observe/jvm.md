---
title: "jstack / jmap / jstat · JVM 观测"
description: "jstack 看线程栈定位死锁/高 CPU 线程、jmap 看堆与导出 dump、jstat 看 GC、jinfo 看参数。Java 业务排障必备，中文详解。"
---

# jstack / jmap / jstat · JVM 观测

> 命令手册 · [排障观测](/commands/observe/) ｜ 频率：偶尔用
> Java 服务 CPU 飙高/内存泄漏/卡死——OS 工具看到 java 进程忙，但具体哪行代码、哪个线程，要靠 JDK 自带的 jstack/jmap/jstat。

## 一句话用途

观测 JVM 内部：线程栈、堆内存、GC 状况，定位 Java 应用级问题。

## 高频场景速查

```bash
jps -l                     # 列 Java 进程与主类
jstack 1234                # 导出线程栈（看死锁/卡在哪）
jstack 1234 > thread.txt   # 存文件分析
jstat -gcutil 1234 1000    # 每秒看 GC 使用率
jmap -heap 1234            # 堆概览
jmap -dump:live,format=b,file=heap.hprof 1234   # 导出堆 dump
jinfo -flags 1234          # 看 JVM 参数
```

## 各工具职责

| 工具 | 看什么 |
|---|---|
| `jps` | Java 进程列表 |
| `jstack` | 线程栈（死锁/阻塞/高 CPU 线程） |
| `jmap` | 堆内存/对象分布/dump |
| `jstat` | GC 频率/耗时/各区使用率 |
| `jinfo` | JVM 启动参数 |

## 定位高 CPU 线程（经典套路）

```bash
top -Hp 1234               # 找 java 里 CPU 高的线程 PID（如 5678）
printf '%x\n' 5678         # 转十六进制 = 162e
jstack 1234 | grep -A 20 'nid=0x162e'   # 在栈里找该线程，看跑哪段代码
```

## jstat GC 解读

`jstat -gcutil PID 1000` 输出 S0/S1/E/O/M/YGC/YGCT/FGC/FGCT：
- **O（老年代）持续接近 100 + FGC 频繁**：内存泄漏或堆太小。
- **FGC 次数暴涨**：Full GC 频繁，应用卡顿，查泄漏。

## 运维实战

**服务卡死**：jstack 看是否死锁（输出末尾 "Found one Java-level deadlock"）或全卡在某个锁/IO。
**内存泄漏**：jmap dump 导出，用 MAT/JProfiler 分析谁占着对象不释放。
**GC 调优依据**：jstat 看 GC 频率与停顿，决定是否调堆/换收集器。

::: tip 易错点
jmap -dump 会 STW（暂停应用）且文件巨大，生产慎用、避开高峰。jstack 相对轻量。容器里要用同版本 JDK 工具，或进容器执行。
:::

## 相关命令

[top/htop](/commands/system/htop) · [pidstat -t](./pidstat-mpstat) · [perf](./perf) · [free](./free)

## 官方文档

- jstack：<https://docs.oracle.com/en/java/javase/17/docs/specs/man/jstack.html>
- jmap：<https://docs.oracle.com/en/java/javase/17/docs/specs/man/jmap.html>
- jstat：<https://docs.oracle.com/en/java/javase/17/docs/specs/man/jstat.html>