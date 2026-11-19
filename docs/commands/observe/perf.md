---
title: "perf 命令详解：CPU 热点、调度延迟与性能采样"
description: "perf 是 Linux 内核自带的性能分析工具，能看 CPU 热点、上下文切换、调度延迟和函数调用栈。本文覆盖 perf top、perf stat、perf record/report、FlameGraph 和容器内核符号的常见坑。"
---

# perf 命令详解：CPU 热点、调度延迟与性能采样

> `perf` 是内核性能事件接口的用户态工具，适合回答“CPU 花在哪个函数”“谁在频繁上下文切换”“为什么进程被调度出去”。它不是万能 profiler：Java 应用还需要 JVM 的 JFR、async-profiler；锁竞争要结合 `perf sched` 或 `eBPF`。

## 安装与权限

```bash
# RHEL / Rocky
dnf install -y perf

# Ubuntu / Debian：版本要和当前内核匹配
uname -r
apt install -y linux-tools-common linux-tools-$(uname -r)
```

普通用户可能只能看自己的进程；系统级采样需要 root，或调整：

```bash
cat /proc/sys/kernel/perf_event_paranoid
# 2 通常只允许用户态采样；-1 最宽松，生产环境不要随意改
```

```bash
# 临时允许系统级采样（按需，不要永久放宽）
sysctl -w kernel.perf_event_paranoid=1
```

内核符号看不到时，检查 `kptr_restrict` 和 `perf` 的符号包：

```bash
cat /proc/sys/kernel/kptr_restrict
# RHEL/Rocky 安装 kernel-debuginfo 后才有完整内核符号
```

## 快速看 CPU 热点：perf top

```bash
perf top
# 只看指定进程
perf top -p 12345
# 显示调用图
perf top -g
```

`perf top` 是实时采样，适合登录机器后先看整体热点。按 `q` 退出。重点看：

- 用户态符号集中在哪个库/函数。
- 内核态是否大量消耗在 `copy_user_enhanced_fast_string`、`mutex_lock`、`schedule`、网络协议栈。
- `[unknown]` 过多说明符号缺失，先装 debuginfo 或用 `--symfs` 指定符号路径。

## 统计事件：perf stat

```bash
# 统计进程 10 秒内的 CPU、上下文切换、缺页
perf stat -p 12345 sleep 10

# 指定事件
perf stat -e cycles,instructions,cache-misses,context-switches,cpu-migrations,page-faults -p 12345 sleep 10
```

输出中的关键指标：

| 指标 | 说明 |
|---|---|
| `cycles` / `instructions` | CPU 周期与指令数，可算 IPC |
| `cache-misses` | 缓存未命中，偏高可能是内存访问模式问题 |
| `context-switches` | 上下文切换次数，过高说明锁竞争或 I/O 等待 |
| `cpu-migrations` | 跨 CPU 迁移，偏高可能影响缓存局部性 |
| `page-faults` | 缺页，频繁 major fault 可能是内存不足或 mmap 文件被换出 |

## 采样调用栈：perf record / report

```bash
# 以 99Hz 采样，记录调用栈，持续 30 秒
perf record -F 99 -g -p 12345 -- sleep 30

# 生成报告
perf report
```

`perf report` 里按 `+`/`-` 展开调用图，按 `Enter` 查看符号和调用链。常用技巧：

```bash
# 记录所有 CPU，适合短时压测
perf record -F 99 -g -a -- sleep 10

# 只记录指定事件
perf record -e cycles -g -p 12345 -- sleep 10

# 记录后导出文本，便于脚本处理
perf script > /tmp/perf.txt
```

采样频率不是越高越好：`-F 99` 是常用折中；`-F 1000` 开销明显增加，短时定位才用。

## 调度与延迟：perf sched

```bash
# 记录调度事件
perf sched record -- sleep 10

# 查看每个进程的调度延迟
perf sched latency

# 查看调度时间线
perf sched timehist
```

适合排查：

- 进程明明 CPU 不高，但请求延迟大：看是否频繁被抢占、等 CPU。
- 大量 `context-switches`：结合 `perf sched` 看谁在让出 CPU。
- 容器 CPU 限流（cgroup throttling）：`perf sched` 只能看调度侧，还要看 `cpu.stat` 的 `throttled` 计数。

## 生成火焰图

```bash
# 1. 采样
perf record -F 99 -g -p 12345 -- sleep 30

# 2. 导出折叠栈
perf script | stackcollapse-perf.pl > out.perf-folded

# 3. 生成 SVG
flamegraph.pl out.perf-folded > flamegraph.svg
```

`stackcollapse-perf.pl`、`flamegraph.pl` 来自 Brendan Gregg 的 [FlameGraph](https://github.com/brendangregg/FlameGraph)。火焰图看的是**宽度**：越宽说明采样命中越多；不是调用顺序的时间轴。

## 容器与云主机注意点

- 容器内默认可能没有 `perf`，也不一定有权限访问 `perf_event_open`；优先在宿主机上按容器 PID 采样。
- 容器使用 host PID namespace 时，宿主机 `perf -p <容器内PID>` 才能对应上；否则要先 `nsenter`。
- 云主机的内核符号可能被裁剪，`perf report` 里 `[unknown]` 多；安装对应内核的 debuginfo 或使用云厂商的符号包。
- Java、Go 有运行时符号；Go 的 goroutine 调度还要配合 `go tool pprof`，不要只看 `perf`。
- 生产环境采样要先评估开销；对核心交易服务，优先短时、低频率、指定进程。

## 官方文档

- [perf 内核文档](https://docs.kernel.org/admin-guide/perf.html)
- [perf(1) man page](https://man7.org/linux/man-pages/man1/perf.1.html)
