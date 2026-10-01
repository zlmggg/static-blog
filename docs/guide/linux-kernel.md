---
title: 内核调优与资源限制
description: sysctl 内核参数、网络/内存/文件句柄调优、ulimit 资源限制与内核模块管理
category: Linux
difficulty: 高级
---
# 内核调优与资源限制

::: tip 本篇定位
理解内核参数的查看与修改方式（`/proc/sys`、`sysctl`），掌握**网络、内存、文件句柄、进程数**等高频调优参数和 `ulimit` 资源限制，了解内核模块管理，并建立"先理解再调整"的调优原则。
:::

## 一、内核参数概览

### 1.1 /proc 虚拟文件系统

`/proc` 是内核在内存中生成的**虚拟文件系统**，不占磁盘，实时反映内核和进程的运行状态：

```bash
cat /proc/cpuinfo          # CPU 信息
cat /proc/meminfo          # 内存信息
cat /proc/version          # 内核版本
ls /proc/                  # 数字目录即各进程 PID
```

**可调整的内核参数集中在 `/proc/sys/` 下**，按子系统分类：

| 目录 | 子系统 |
|---|---|
| `/proc/sys/net/` | 网络（ipv4、core） |
| `/proc/sys/vm/` | 内存、虚拟内存、交换 |
| `/proc/sys/fs/` | 文件系统、文件句柄 |
| `/proc/sys/kernel/` | 内核通用、进程、调度 |

### 1.2 临时修改：直接写文件

参数以文件形式存在，写入新值立即生效，但**重启后丢失**：

```bash
cat /proc/sys/net/ipv4/ip_forward      # 查看（0 关闭）
echo 1 > /proc/sys/net/ipv4/ip_forward # 临时开启
```

### 1.3 sysctl 命令

`sysctl` 是读写内核参数的专用工具，用"点分路径"代替目录：

```bash
sysctl net.ipv4.ip_forward              # 查看单个参数
sysctl -a | grep tcp                    # 列出所有参数并过滤
sudo sysctl -w net.ipv4.ip_forward=1    # 临时修改（等同写文件）
sudo sysctl -p                          # 加载 /etc/sysctl.conf 使其生效
sudo sysctl -p /etc/sysctl.d/99-my.conf # 加载指定文件
```

### 1.4 永久生效：配置文件

把参数写进配置文件，重启或 `sysctl -p` 后持续生效：

| 文件/目录 | 说明 |
|---|---|
| `/etc/sysctl.conf` | 主配置（传统，通常软链或汇总） |
| `/etc/sysctl.d/*.conf` | 分片配置（推荐，按 `数字-名称` 排序加载） |
| `/usr/lib/sysctl.d/` | 软件包自带，勿手改 |

```bash
# /etc/sysctl.d/99-my-tuning.conf
net.ipv4.ip_forward = 1
vm.swappiness = 10
```

```bash
sudo sysctl -p /etc/sysctl.d/99-my-tuning.conf   # 立即加载
```

::: warning 配置文件语法
- 用 `=` 赋值，等号两侧空格可有可无；
- 路径用点分（`net.ipv4.tcp_fin_timeout`）；
- 文件名前缀数字决定加载顺序，自定义用 `99-` 确保最后加载、覆盖默认。
:::

---

## 二、网络相关参数

网络调优是高并发场景最常见的部分。

### 2.1 连接与转发

```bash
net.ipv4.ip_forward = 1
# 是否允许转发数据包。做路由器/NAT、Docker 跨容器通信时必须开启（Docker 会自动处理）

net.ipv4.tcp_tw_reuse = 1
# 允许将 TIME_WAIT 状态的连接重新用于新的出站连接，高并发短连接可缓解端口耗尽

net.ipv4.tcp_fin_timeout = 30
# 本端关闭连接后，FIN-WAIT-2 状态保持秒数，默认 60，调小可加快回收
```

### 2.2 连接队列

```bash
net.core.somaxconn = 4096
# 每个监听端口"已完成三次握手、等待 accept"队列的最大长度。
# 默认值较小（如 4096/4096 因版本而异），高并发新连接多时调大，否则新连接被丢弃。

net.ipv4.tcp_max_syn_backlog = 8192
# SYN 半连接队列（还没完成三次握手）长度，应对大量并发新建连接 / 轻度 SYN 攻击。

net.core.netdev_max_backlog = 10000
# 网卡接收数据包的内核队列长度，瞬时流量大、内核处理不过来时避免丢包。
```

::: warning somaxconn 还要应用配合
`socket listen()` 时应用传入的 backlog 如果比 `somaxconn` 小，实际取较小值。所以光调内核不够，Nginx（`net.core.somaxconn`）、应用框架的连接队列参数也要相应调大。
:::

### 2.3 端口范围与 TIME_WAIT 上限

```bash
net.ipv4.ip_local_port_range = 1024 65535
# 作为客户端发起出站连接时可用的本地端口范围，默认偏窄，调大缓解高并发外连端口耗尽。

net.ipv4.tcp_max_tw_buckets = 100000
# 系统同时保持 TIME_WAIT 的最大数量，超出后直接清理并告警，防止耗尽资源。
```

### 2.4 TCP Keepalive 与缓冲区

```bash
net.ipv4.tcp_keepalive_time = 600      # 连接空闲多久后开始发探测（秒）
net.ipv4.tcp_keepalive_intvl = 30      # 探测间隔
net.ipv4.tcp_keepalive_probes = 3      # 探测次数，无响应则判定连接失效

net.core.rmem_max / wmem_max           # socket 接收/发送缓冲区最大值
net.ipv4.tcp_rmem = 4096 87380 6291456 # TCP 接收缓冲：最小 默认 最大
net.ipv4.tcp_wmem = 4096 65536 4194304 # TCP 发送缓冲：最小 默认 最大
```

> 网络参数原理详见 [网络基础](/guide/linux-network)，排障详见 [故障排障](/cases/)。

---

## 三、文件句柄与进程数

### 3.1 系统级文件句柄

Linux 中"一切皆文件"，打开的普通文件、socket、管道都占用**文件描述符（file descriptor）**：

```bash
fs.file-max = 2097152
# 整个系统能同时打开的文件描述符总数（系统级上限）

fs.nr_open = 1048576
# 单个进程能打开的文件描述符上限
```

```bash
cat /proc/sys/fs/file-nr      # 已分配 / 空闲 / 上限，三个数
```

### 3.2 用户/进程级限制：ulimit

`fs.file-max` 是全局限，单个进程能开多少由 **ulimit** 控制（默认常只有 1024，高并发服务明显不够）：

```bash
ulimit -a              # 查看当前所有限制
ulimit -n              # 查看最大打开文件数（nofile）
ulimit -u              # 查看最大进程/线程数（nproc）
ulimit -n 65535        # 当前 shell 临时调大（重启失效）
```

常见项：

| 选项 | 限制内容 |
|---|---|
| `-n` | 最大打开文件描述符数（nofile） |
| `-u` | 用户最大进程/线程数（nproc） |
| `-s` | 栈大小（stack） |
| `-l` | 最大可锁定内存（memlock） |
| `-f` | 单个文件最大大小 |

### 3.3 永久配置：limits.conf

```bash
# /etc/security/limits.conf  或 /etc/security/limits.d/99-nofile.conf
*    soft  nofile  65535
*    hard  nofile  65535
*    soft  nproc   65535
*    hard  nproc   65535
```

字段含义：`域(用户/*)  类型(soft/hard)  项目  值`

- **soft**：当前生效值，用户可自行调大到 hard；
- **hard**：上限，soft 不能超过它（只有 root 能设）；
- 通常两者设成相同值。

```bash
# 进程/线程数上限也有内核参数
kernel.pid_max = 4194304        # 全系统 PID 上限
kernel.threads-max = 2097152    # 全系统线程总数上限
```

::: warning limits.conf 对 systemd 服务不一定生效
通过 `systemctl` 启动的服务，其限制由 systemd 接管，`limits.conf` 可能不生效。应在 Unit 文件里设置：

```ini
[Service]
LimitNOFILE=65535
LimitNPROC=65535
```

改完 `systemctl daemon-reload && systemctl restart 服务`。
:::

---

## 四、内存参数

### 4.1 交换倾向 swappiness

```bash
vm.swappiness = 10
# 内核使用 swap 的倾向，范围 0-100：
#   值越高越积极把内存数据换到 swap；0 尽量不用（并非完全禁用），100 积极换出。
# 物理内存充足的服务器设低值（10-20）减少磁盘 I/O；内存紧张的机器适当调高防 OOM。
```

### 4.2 内存过量分配 overcommit

```bash
vm.overcommit_memory = 0
# 控制 malloc 申请内存的策略：
#   0 启发式（默认）：内核判断是否超量，明显不合理就拒绝；
#   1 总是允许 overcommit（如 Redis 推荐，配合其持久化）；
#   2 禁止超过：可分配 = swap + 物理内存 * ratio(overcommit_ratio)，最稳妥。

vm.panic_on_oom = 0
# 发生 OOM 时的行为：0 由 OOM killer 挑进程杀掉（默认）；1 直接内核 panic（一般不开）。
```

::: details OOM killer
内存耗尽时，内核的 OOM killer 会按 `oom_score`（占用内存越多分越高）选一个进程杀掉保命。排查：`dmesg | grep -i "out of memory"` 或 `journalctl -k | grep -i oom`，可看到 "Killed process ... score ..."。
:::

### 4.3 脏页参数

"脏页"指已被修改、但还没写回磁盘的内存页：

```bash
vm.dirty_background_ratio = 5
# 脏页占内存百分比达到该值，内核在后台异步开始刷盘（不阻塞进程）。

vm.dirty_ratio = 20
# 脏页达到该百分比时，写操作被同步阻塞、强制刷盘（可能造成卡顿）。

vm.dirty_expire_centisecs = 3000
# 脏页最老存活时间（百分之一秒），到了就会被刷盘。
```

> 数据库等对写入敏感的服务，调小脏页比例可减少突发 I/O 停顿，但会增加写盘次数，需按业务权衡。

### 4.4 共享内存

```bash
kernel.shmmax = 68719476736     # 单个共享内存段最大值（字节）
kernel.shmall = 4294967296      # 系统可用共享内存总量（页）
# 部署 Oracle/PostgreSQL 等使用 SysV 共享内存的数据库时需要关注。
```

---

## 五、内核模块

### 5.1 模块概念

Linux 采用**单内核 + 可加载内核模块（LKM, Loadable Kernel Module）**：

- 核心功能常驻内核，驱动、文件系统、协议等以 `.ko` 模块形式按需加载，**无需重新编译内核、无需重启**；
- 兼顾单内核的高性能和动态扩展的灵活性。

### 5.2 查看模块

```bash
lsmod                          # 列出已加载模块（读 /proc/modules）
modinfo nf_nat                 # 查看某模块信息（文件、参数、版本）
```

### 5.3 加载与卸载

```bash
sudo modprobe nf_nat           # 加载模块（推荐：自动解决依赖、从标准路径找）
sudo insmod /path/to/xx.ko     # 加载指定 .ko（不解决依赖，需写绝对路径）

sudo modprobe -r nf_nat        # 卸载（推荐）
sudo rmmod xx                  # 卸载（被依赖/使用中时无法卸载）
```

### 5.4 开机自动加载与模块参数

```bash
# 开机加载：把模块名写入 /etc/modules-load.d/ 下文件
echo "nf_nat" | sudo tee /etc/modules-load.d/mymod.conf

# 模块参数：写入 /etc/modprobe.d/ 下文件
# /etc/modprobe.d/my.conf
options 模块名 参数=值
# 例：options bonding mode=1 miimon=100
```

::: tip 黑名单（禁用模块）
安全加固时常禁用不需要的模块（如 USB 存储、内核协议）：

```bash
# /etc/modprobe.d/blacklist-usb.conf
blacklist usb-storage
install usb-storage /bin/true
```
:::

---

## 六、调优原则

::: danger 不要盲目照搬网上的"优化模板"
网上流传的 sysctl 参数表常来自特定内核版本和特定业务，直接整段套用可能**适得其反甚至引发故障**。请遵循以下原则。
:::

1. **先理解含义**：每个参数搞清楚作用、取值范围、默认值，以及它解决什么问题，再决定是否调整；
2. **先备份**：修改前 `sysctl -a > sysctl.bak` 或记录原值，便于回滚；
3. **先临时、后永久**：先用 `sysctl -w` 临时调整，观察一段时间确认有效，再写进配置文件持久化；
4. **小步调整、逐项验证**：一次只改一类参数，配合监控观察 CPU/内存/网络/业务指标，避免多处同时改无法定位影响；
5. **有瓶颈才调**：默认参数对多数场景已经合理，没有监控数据证明存在瓶颈，就不要"为了优化而优化"；
6. **全链路考虑**：内核参数要和应用配置（连接数、队列、工作线程）、硬件能力匹配，单改一层往往无效；
7. **记录与复核**：记录每次调整的原因、时间和结果，纳入运维文档。

### 调优排查思路（以高并发连接异常为例）

```bash
# 1. 看现象：ss 统计各状态连接数
ss -s
ss -ant | awk '{print $1}' | sort | uniq -c
# 2. 看队列是否溢出
nstat -az | grep -i "listen"      # ListenOverflows / ListenDrops
# 3. 看端口/句柄是否耗尽
cat /proc/sys/fs/file-nr
dmesg | grep -i "too many open files"
# 4. 针对性调整 somaxconn / port_range / nofile，并同步应用配置
```

---

## 面试自测

1. /proc/sys 下的参数如何临时修改、如何永久生效？
2. `sysctl -p` 和 `sysctl -w` 的区别？
3. net.core.somaxconn 和 tcp_max_syn_backlog 分别是什么队列？
4. tcp_tw_reuse、ip_local_port_range 解决什么问题？
5. fs.file-max、ulimit -n、fs.nr_open 三者的区别和层级关系？
6. limits.conf 里 soft 和 hard 的区别？为什么对 systemd 服务可能不生效，怎么办？
7. vm.swappiness 的含义和典型取值？
8. vm.overcommit_memory 三个取值的含义？OOM killer 如何选进程？
9. 脏页 dirty_ratio / dirty_background_ratio 的区别？
10. modprobe 和 insmod 的区别？如何让模块开机自动加载？
11. 为什么不能直接照搬网上的内核调优模板？
12. 内核参数调优的正确流程是什么？

## 相关速查

- [Linux 命令速查](/reference/linux-commands)
- [网络基础](/guide/linux-network)
- [系统性能监控](/guide/linux-performance)
