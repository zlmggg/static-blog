---
category: 架构
difficulty: 高级
---

# 性能调优实战全流程

::: tip 本篇定位
面向中高级 SRE/后端：把"感觉慢、压不上去"变成一套可复制的闭环——定目标、压测建基线、按 USE/RED 定位 CPU/内存/IO/网络四类瓶颈、改参数、用前后对比数据证明有效。不重复 [linux-performance](./linux-performance) 的单命令科普，这里给的是**流程、判据和能落地的参数**。
本篇版本：wrk 4.2.0、Vegeta v12.13.0、k6 2.0、Nginx 1.30.5（stable）、MySQL 8.4 LTS（8.4.11）、Redis 8.x、JDK 25 LTS（JDK 21 为上一 LTS）。sysctl 参数适用内核 4.18（RHEL 8）~ 7.0（Ubuntu 26.04）。
:::

## 一、先定目标：别上来就调

### 1.1 小白类比：调优不是"把机器榨干"

调优像给一辆车做改装。你不能拿着扳手一通乱拧——先得知道是"想跑得更快（吞吐）"还是"想刹车更短（延迟）"，还是"拉更多货（并发）"。**这三个目标经常互相打架**：把缓存堆满能提吞吐，但冷启动时延迟尖刺会变大。

所以第一步不是敲命令，是回答两个问题：

1. **对齐 SLO**：业务要的是 P99 < 200ms，还是峰值 5000 QPS？两者都要时，以哪个为硬约束？（SLO 原理见 [monitor-slo](./monitor-slo)，本篇只讲怎么把它翻译成压测目标。）
2. **明确谁是约束资源**：一次只能调一个瓶颈，否则改了 A 又冒出 B，永远说不清是谁起的作用。

### 1.2 两套方法论：USE 与 RED

| 方法 | 适用对象 | 看什么 | 通俗记法 |
|---|---|---|---|
| **USE**（Utilization / Saturation / Errors） | **资源**（CPU、内存、磁盘、网卡、fd） | 利用率、饱和度（队列/等待）、错误数 | 资源角度："它累不累？排不排队？报错没？" |
| **RED**（Rate / Errors / Duration） | **服务**（每个接口） | 请求速率、错误率、响应时长 | 用户角度："多快？错多少？等多久？" |

> 经验法则：**用 RED 发现"哪个接口慢了"，用 USE 定位"是哪种资源扛不住"。** 先 RED 后 USE，顺序反了会满机器瞎找。

判据速记（不是绝对值，是"出现就该查"的信号）：

- CPU：`%user` 高 = 业务代码；`%system` 高 = 内核/系统调用；`%iowait` 高 = 磁盘堵；`%st`（虚拟化偷时间）高 = 宿主机超卖。
- 内存：`available` 而非 `free` 才是真实可用；swap in/out 持续发生 = 真不够。
- 磁盘：`await`（毫秒）远大于 `svctm`，或 `%util` 长期 90%+ = 瓶颈。
- 网卡：`ethtool -S` 里 `rx_dropped`/`rx_missed_errors` 增长 = 软中断/队列跟不上。

## 二、压测：三个工具怎么选

### 2.1 选型对比

| 工具 | 语言/形态 | 强项 | 弱项 | 典型场景 |
|---|---|---|---|---|
| **wrk 4.2.0** | C，单二进制 | 单机极高吞吐、Lua 脚本、报告简洁 | 不适合分布式压、不适合复杂业务流 | 快速摸一个 HTTP 接口的极限 QPS |
| **Vegeta v12.13.0** | Go，命令+库 | 恒定速率（`-rate`）精确、可画延迟分布图、可做长期 soak | 默认报告不如 wrk 直观 | 按目标速率匀速打、看分位数 |
| **k6 2.0** | JS 脚本 | 贴近业务场景、VU 模型、threshold 断言、可接 Grafana | 单机吞吐不如 wrk | 带登录/造数据/断言的端到端压测 |

### 2.2 可直接复制的用法

```bash
# wrk：12 线程、400 并发、持续 30s，打一个 GET 接口
wrk -t12 -c400 -d30s --latency http://127.0.0.1:8080/api/hello

# 带 header / Lua 脚本（POST、造 token）
wrk -t12 -c400 -d30s -s post.lua --latency http://127.0.0.1:8080/api/order
```

`post.lua`（wrk 官方 Lua 接口，可直接用）：

```lua
-- wrk Lua 脚本：每个请求带 JSON body
wrk.method = "POST"
wrk.headers["Content-Type"] = "application/json"
wrk.body   = '{"item_id": 1001, "qty": 1}'
```

```bash
# Vegeta：恒定 500 请求/秒、持续 60s，输出二进制报告再转 text/histogram
echo "GET http://127.0.0.1:8080/api/hello" | \
  vegeta attack -rate=500 -duration=60s -connections=100 | \
  tee results.bin | vegeta report

# 看延迟分布（P50/P95/P99/P999）
cat results.bin | vegeta report -type=histogram
```

```javascript
// k6 2.0 脚本（test.js）：100 VU 跑 2 分钟，断言 P95 < 300ms、错误率 < 1%
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 100,
  duration: '2m',
  thresholds: {
    http_req_duration: ['p(95)<300'],   // P95 必须小于 300ms
    http_req_failed: ['rate<0.01'],     // 错误率必须小于 1%
  },
};

export default function () {
  const res = http.get('http://127.0.0.1:8080/api/hello');
  check(res, { 'status is 200': (r) => r.status === 200 });
  sleep(0.1);
}
```

```bash
# k6 运行（固定版本二进制，不用 latest）
k6 run test.js
```

### 2.3 报告怎么读（以 wrk 输出为例）

```text
Running 30s test @ http://127.0.0.1:8080/api/hello
  12 threads and 400 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency     8.21ms    4.10ms  80.30ms   85.20%
    Req/Sec     4.02k   321.00     5.10k    70.10%
  Latency Distribution
     50%    7.90ms
     75%   10.10ms
     99%   18.40ms
  1442000 requests in 30.10s, 180.2MB read
Requests/sec:  47906.67          ← 吞吐 QPS
Transfer/sec:      5.99MB
```

要点：

- **Requests/sec** 是吞吐；**P99**（不是 Avg）才是用户体感。Avg 8ms 但 P99 18ms、Max 80ms，说明有长尾。
- 关注 **Stdev（标准差）**：越大越不稳定。
- 压测时**被测机和压测机分开**，压测机自己别成瓶颈（压测机先看 `sar -n DEV`、`ulimit -n`、本地端口耗尽）。

::: warning 压测红线
- **绝不在生产高峰直接打真实用户流量**。压测环境数据量、缓存命中率要尽量贴近生产；空库压出来的 QPS 没有意义。
- 压测机也要调 ulimit（`nofile`）和本地端口范围，否则"被测机没问题"其实是压测机先顶不住。
- 从低并发**阶梯加压**（如 50→100→200→400），找到拐点（吞吐不再涨、P99 开始陡增），而不是一上来就 1000 并发。
:::

## 三、建立基线与四类瓶颈定位

### 3.1 基线是什么

基线 = 在"正常配置、正常数据量"下，把 CPU/内存/IO/网络/RT/QPS 全部记一遍，存成文档。**后面每改一个参数，都和基线比**，没有基线的调优都是玄学。

```bash
# 一条命令收集压测期间的系统画像（后台跑，压测结束后看）
sar -u 1 30 > cpu.txt &          # CPU
sar -r 1 30 > mem.txt &         # 内存
sar -n DEV 1 30 > net.txt &      # 网络
iostat -xz 1 30 > io.txt &      # 磁盘 IO
pidstat -u -d -p ALL 1 30 > proc.txt &  # 按进程
```

### 3.2 CPU 瓶颈

```bash
top -H -p <pid>                 # 看进程内线程谁在吃 CPU（按 H）
mpstat -P ALL 1                 # 看是不是单核打满、其他核闲
pidstat -u 1                    # 按进程看 %CPU
# Java：看具体哪段代码
top -H -p <java_pid>            # 拿到忙线程 nid（十六进制）
printf "%x\n" <nid>             # 转十六进制
jstack <java_pid> | grep -A20 <nid_hex>   # 定位到代码行
```

判据：`%user` 持续 > 70% 且伴随 P99 升高 = 业务计算瓶颈，考虑加机器/加缓存/优化算法；`%system` 高 = 频繁系统调用/上下文切换，查是否每秒百万次小连接。

### 3.3 内存瓶颈

```bash
free -h                         # 看 available，不是 free
vmstat 1                        # si/so（swap 换入换出）非 0 = 内存紧张
# Java 堆
jstat -gcutil <pid> 1000        # 看各代占用、YGC/FGC 次数与耗时
# native 泄漏（非堆）
pmap -x <pid> | sort -k3 -n | tail    # 看哪块映射最大
```

判据：`available` 持续走低且 swap in/out 增长 = 真内存不足；JVM `FGC` 频繁、每次回收后老年代不降 = 堆泄漏，用 `jmap -dump` 后 MAT 分析。

### 3.4 IO 瓶颈

```bash
iostat -xz 1                    # 重点看 await、%util、aqu-sz
iotop -o                        # 哪个进程在写盘
dstat -tdrn                     # 综合
```

判据：`%util` 长期接近 100% 且 `await` 远高于正常 = 磁盘带宽/IOPS 打满。数据库常见：redo/undo 落盘、慢查询全表扫描产生大量随机读。

### 3.5 网络瓶颈

```bash
sar -n DEV 1                    # 看网卡带宽有没有打满（rxkB/txkB）
ss -s                           # 看当前各状态连接数汇总
nstat -az | grep -i retrans     # 看重传（TcpRetransSegs）
ethtool eth0                    # 看协商速率是不是被降到 100Mb
ethtool -S eth0 | grep -i drop  # 看网卡丢包
```

判据：带宽打满 = 压缩/CDN/垂直扩展网卡；重传率 > 0.5% = 网络质量或缓冲区问题；`rx_dropped` 增长 = 软中断/多队列没开。

## 四、具体调优参数（带"为什么"）

### 4.1 JVM（JDK 25 LTS，G1 为默认）

```bash
# 堆给到物理内存的 50%~70%（留够堆外/元空间/直接内存/操作系统）
# 不要把 -Xmx 设成和物理内存一样大
java -server \
  -Xms4g -Xmx4g \                       # Xms=Xmx 避免运行时扩缩抖动
  -XX:+UseG1GC \                        # JDK 9+ 默认 G1，这里显式写清楚
  -XX:MaxGCPauseMillis=200 \            # 目标停顿，不是承诺
  -XX:+ParallelRefProcEnabled \
  -XX:+HeapDumpOnOutOfMemoryError \     # OOM 自动 dump，事后能查
  -XX:HeapDumpPath=/var/log/app/heapdump.hprof \
  -jar app.jar
```

要点：**堆外内存（Netty DirectBuffer、线程栈、元空间）也要算进去**，容器里尤其要 `--memory` 留足，否则 JVM 堆没满但容器被 OOMKill。

### 4.2 连接池（HikariCP 经验值）

| 参数 | 建议 | 为什么 |
|---|---|---|
| `maximumPoolSize` | 不是越大越好，经验公式 `核数*2 + 有效磁盘数`，通常 10~30 | 连接多了数据库上下文切换反而慢，见 HikariCP 作者"pool sizing"论述 |
| `minimumIdle` | 与 max 相同（固定池） | 避免临时建连抖动 |
| `connectionTimeout` | 3000~5000ms | 快速失败，别让请求无限等连接 |

### 4.3 Nginx（1.30.5）

```nginx
worker_processes auto;              # 等于 CPU 核数，别写死 1
events {
    worker_connections 65535;        # 配合 ulimit nofile
    multi_accept on;
    use epoll;
}
http {
    keepalive_timeout 65;
    keepalive_requests 1000;         # 单连接复用次数，高并发下调大
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    gzip on;                         # 压缩响应降带宽
}
```

### 4.4 MySQL（8.4 LTS）

```ini
[mysqld]
innodb_buffer_pool_size = 12G        # 专用库给物理内存 50%~70%，最重要的一个参数
innodb_log_file_size    = 2G         # redo 日志大小，影响刷盘频率
max_connections         = 500        # 按连接池总和留，别盲目 1000+
innodb_flush_log_at_trx_commit = 1   # 1=最安全，性能敏感可评估 2（有丢数据风险）
slow_query_log          = ON
long_query_time         = 1          # 超过 1s 记慢查询
```

完整模板见 [config-best-practices](./config-best-practices)。

### 4.5 内核 sysctl（适用 4.18 ~ 7.0）

```ini
# /etc/sysctl.d/99-perf.conf —— 高并发短连接 Web 场景
net.core.somaxconn = 65535                 # 全连接队列，默认 128 太小
net.ipv4.tcp_max_syn_backlog = 65535        # 半连接队列
net.ipv4.tcp_tw_reuse = 1                   # TIME_WAIT 复用给新 outbound 连接
net.ipv4.ip_local_port_range = 1024 65535   # 本地出口端口范围，压测机必调
fs.file-max = 1048576                      # 系统级文件句柄上限
```

```bash
sysctl -p /etc/sysctl.d/99-perf.conf       # 生效
# 配合 ulimit（在 systemd unit 里设 LimitNOFILE，或 /etc/security/limits.conf）
```

> ⚠️ `tcp_tw_recycle` 在 NAT/多机场景会坑人，**新内核已废弃，不要开**；`tw_reuse=1` 安全可用。

## 五、调优前后对比表（必须留档）

改完任何参数，按下表记录——这是向团队证明"调优有效"的唯一证据：

| 指标 | 基线（默认配置） | 调优后 | 变化 | 说明 |
|---|---|---|---|---|
| 峰值 QPS | 18,000 | 47,900 | +166% | wrk -t12 -c400 |
| P99 延迟 | 95ms | 18ms | -81% | 压测同负载 |
| CPU %user | 92%（单核打满） | 63%（多核均衡） | -29% | worker_processes auto |
| 网卡带宽 | 110MB/s（打满） | 48MB/s | -56% | 开 gzip |
| 数据库连接等待 | 偶发超时 | 0 | — | HikariCP 池调优 |
| OOM/FGC | 每周 1 次 | 0 | — | 堆与堆外内存重配 |

::: danger 常见误区
- **一次改多个参数**：无法归因。一次只改一类，跑基线对比。
- **盲目加 `-Xmx` / 加连接池**：堆过大 GC 停顿更长，连接过多 DB 更慢。
- **用 Avg 看性能**：用户体感是 P99/P999，不是平均。
- **压测空库/冷缓存**：结果虚高，上线后崩盘。
- **只调应用不调压测机**：瓶颈在压测机的 ulimit/端口，误判成应用不行。
- **把 `tcp_tw_recycle` 当银弹**：NAT 环境丢连接，务必避开。
:::

## 相关速查

- 单命令用法与更多指标：[Linux 性能基础](./linux-performance)、[网络排障](./linux-network)
- 内核参数详解：[Linux 内核与 sysctl](./linux-kernel)
- eBPF 观测（无采样、低损耗定位）：[Linux eBPF](./linux-ebpf)
- SLO/错误预算怎么定：[SLO 与可观测](./monitor-slo)
- 容量与冗余系数：[容量规划与灾备](./sre-capacity-dr)
- 云原生排障命令：[/reference/cloudnative-commands](/reference/cloudnative-commands)
- 上线前压测 Checklist：[/reference/ops-checklists](/reference/ops-checklists)

### 官方文档

- wrk（GitHub）：https://github.com/wg/wrk
- Vegeta（GitHub Releases）：https://github.com/tsenart/vegeta/releases
- k6 文档：https://grafana.com/docs/k6/
- Nginx 开始页（版本公告）：https://nginx.org/en/
- MySQL 8.4 Reference Manual：https://dev.mysql.com/doc/refman/8.4/en/
- OpenJDK 版本：https://www.java.com/en/releases/
