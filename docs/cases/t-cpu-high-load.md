---
category: Linux
difficulty: 高级
date: 2022-06-18
---

# CPU 飙高、load average 高的定位（2022-06-18）

## 现象

监控告警：一台 Web 服务器 CPU 使用率持续 95% 以上，`load average` 三个值都飙到 20+（机器 16 核）。
业务接口响应变慢，502 增多。登录上去 `top` 看到：

```
top - 14:22:31 up 30 days,  2:11,  1 user,  load average: 22.34, 18.12, 12.05
%Cpu(s): 82.3 us, 12.1 sy,  0.0 ni,  0.0 id,  1.5 wa,  0.0 hi,  4.1 si,  0.0 st
```

需要判断到底是用户态程序吃 CPU、内核态开销大、还是 IO 等待，再决定怎么处理。

## 环境

- 发行版：Rocky Linux release 8.5 (Green Obsidian)
- 内核：`4.18.0-348.2.1.el8.x86_64`
- CPU：Intel Xeon Silver 4214，16 核
- 业务：Nginx 1.20.1 + PHP-FPM 7.4.28

## 定位过程

### 1. 先看 us / sy / wa / si 各占多少

```bash
top - 1   # 按 1 展开每颗核心
mpstat -P ALL 1 3
```

关键判断：

| 指标 | 高代表什么 | 下一步看哪 |
|---|---|---|
| `us` 高 | 用户态程序计算密集 | `pidstat -u 1` 找进程 |
| `sy` 高 | 内核态调用多（系统调用/上下文切换） | `pidstat -w`、`strace -c` |
| `wa` 高 | CPU 在等 IO | 去看磁盘，别去杀进程 |
| `si` 高 | 软中断多（网络收包） | `nstat`、网卡 RSS |
| `hi` 高 | 硬中断多（网卡/磁盘中断） | `/proc/interrupts` |

本例中 `us 82%`，说明是用户态程序在烧 CPU，不是 IO。

### 2. 找到吃 CPU 的进程

```bash
pidstat -u 1 5          # 每秒采样，看哪个 PID %CPU 最高
top -b -n1 -o %CPU | head -20
```

本例中 `php-fpm` PID 12345 占了 400%（即 4 核满）。

### 3. 找到进程里哪个线程/函数在烧 CPU

```bash
# 看线程级 CPU
pidstat -t -p 12345 1 3

# 如果是 Java 进程，用 top -H 找到高 CPU 线程，再 dump
top -H -p <pid>
printf "%x\n" <tid>     # 十进制转十六进制
jstack <pid> | grep <十六进制tid> -A 20

# 如果是 PHP/C 程序，用 perf 抓调用栈
perf top -p 12345
perf record -g -p 12345 -- sleep 10
perf report
```

### 4. 区分 load average 高 vs CPU 高

很多人会把这两个混为一谈。用 `vmstat 1` 看：

```bash
vmstat 1 5
# procs -----------memory---------- ---swap-- -----io---- --system-- -----cpu-----
#  r  b   swpd   free  buff  cache   si   so    bi    bo   in   cs us sy id wa st
# 18  0      0  20000  100  80000   0    0     5    10 1200 800 85 13  1  1  0
```

- `r`（运行队列）长期大于 CPU 核数 → 真的是 CPU 不够用。
- `b`（D 状态阻塞进程）多 → load 高但 CPU 可能很闲，是 IO 等待，去看 [D 状态进程假死](/cases/t-process-d-state-hang)。

## 根因

一个 PHP 脚本里的死循环（分页接口没加 `LIMIT`，循环里反复 `mysql_query` 查全表），被突发流量放大，几十个 php-fpm worker 同时进入这段慢代码，把 16 核打满。

## 解决步骤

### 1. 临时止血

```bash
# 先把这个 PID 的 CPU 压下来（SIGTERM，让 php-fpm 平滑退出）
kill -TERM 12345

# 如果一台机器上全是 php-fpm 在烧，重启 php-fpm 池
systemctl reload php-fpm
```

注意：不要直接 `kill -9` php-fpm，会断掉正在执行的请求；先 `reload`。

### 2. 彻底修复

- 给问题接口加 `LIMIT` 分页，修复死循环。
- 给慢查询加索引：`slow_query_log = 1`，`long_query_time = 1`。
- 给 php-fpm 配 `request_terminate_timeout = 30s`，防止单个请求跑飞把 worker 占死。

### 3. 限流兜底

Nginx 层加 `limit_req`，对这个接口做令牌桶限速，避免下次再被打穿。

## 验证与预防

- 修复后 `mpstat 1` 观察 `%us` 回落到 30% 以下，`load average` 降到核数以下。
- 监控补：CPU 使用率、`load average`、`vmstat` 的 `r` 队列、`%iowait`、上下文切换速率 `cs`。
- 告警阈值建议：CPU 持续 5 分钟 > 80%、load average 持续 5 分钟 > 核数 × 1.5。

## 相关

- 命令速查：[Linux 命令速查](/reference/linux-commands)
- 内存方向：[内存泄漏与 OOM Killer](/cases/t-memory-leak-oom)
- IO 方向：[进程 D 状态不可中断假死](/cases/t-process-d-state-hang)
- Web 方向：[Nginx 502 Bad Gateway](/cases/t-nginx-502)
