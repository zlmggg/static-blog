# ss 命令详解：查看端口、连接与进程（替代 netstat）

> 本文是 [网络命令速查](../network-commands#端口与连接) 中 `ss` 的从 0 到 1 详解，并附带与老命令 `netstat` 的对照。
> 目标：把 `ss -h` 里 `-t/-u/-l/-n/-p/-a/-s/state` 这几个最常用开关的组合讲清楚，线上排查"谁占了端口、有多少连接"时一眼定位。
> 环境依据：iproute2 **5.15.0**（本机实跑 `ss -V`、各组合输出；`netstat` 属于 net-tools，本沙箱未装，对照列为据其常用语义整理）。

## 一、命令是干什么的

`ss`（socket statistics，套接字统计）用来查看本机的**网络连接、监听端口、UNIX 套接字**，以及每个连接被哪个进程占用。它是老命令 `netstat` 的现代替代品，**更快、信息更全**。

它能回答的三个高频问题：

1. **本机哪个端口在监听？**（服务有没有起来、端口对不对）
2. **谁连着本机 / 本机连到了谁？**（连接数、对端是谁）
3. **这个端口被哪个进程占用？**（PID、进程名）

> 类比：Windows 里你可能用过 `netstat -ano` 看"哪个程序占了 8080 端口"。`ss` 干的是同一件事，只是参数更短、速度更快，还能直接按连接状态过滤。

什么时候用：
- 服务起不来，报"Address already in use"——用 `ss` 查谁占了端口；
- 线上连接数暴涨——`ss -s` 看汇总，`ss -tan` 看 TIME-WAIT 堆积；
- 排查某个进程到底对外建了哪些连接。

## 二、命令语法

```bash
ss [选项]... [过滤条件]
```

- `[选项]`：一堆单字母开关组合（如 `-tlnp`），决定看哪种套接字、显示多详细；
- `[过滤条件]`：如 `state established`、`dst 1.2.3.4`、`dport = :80`，进一步筛结果。

最简用法：

```bash
ss            # 默认显示已建立(ESTAB)的 TCP 连接
```

## 三、选项全表（对照 `ss -h`）

下面按功能分组。短长选项同格写。

### 1. 看哪种协议的套接字

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-t`，`--tcp` | 只看 **TCP** | 查 Web/数据库连接（最常用） |
| `-u`，`--udp` | 只看 **UDP** | 查 DNS/NTP/QUIC 等 |
| `-4`，`--ipv4` | 只看 IPv4 | 排除 IPv6 干扰 |
| `-6`，`--ipv6` | 只看 IPv6 | 排 IPv6 问题 |
| `-x`，`--unix` | 只看 **UNIX 域套接字** | 查本机进程间通信（如 systemd、docker） |
| `-0`，`--packet` | 看链路层 packet 套接字 | 抓包类程序用 |
| `-S` / `-M` / `-w` | SCTP / MPTCP / RAW | 少见，特殊场景 |

### 2. 看哪些状态的套接字

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-l`，`--listening` | 只看**监听中**（LISTEN）的套接字 | 查服务端口有没有开（极常用） |
| `-a`，`--all` | 显示**所有**套接字（监听 + 已连接） | 想看全貌时；不加 `-a` 默认只看 ESTAB |
| `state 状态` | 按 TCP 状态过滤 | 见下方状态表 |

可用的 TCP 状态：`established`、`syn-sent`、`syn-recv`、`fin-wait-1/2`、`time-wait`、`close-wait`、`last-ack`、`listening`、`closing`、`closed`；还有集合别名 `all`/`connected`/`synchronized`/`bucket`/`big`。

### 3. 显示多详细

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-n`，`--numeric` | **不解析**服务名/主机名，直接显示数字端口 | 快、干净，**几乎总是加上** |
| `-p`，`--processes` | 显示套接字属于哪个**进程**（PID/名字） | 查谁占端口（需 root 才看全） |
| `-o`，`--options` | 显示连接**定时器**信息（如 keepalive） | 看长连接保活 |
| `-i`，`--info` | 显示内部 TCP 详情（cwnd、rtt、重传） | 深入网络性能 |
| `-e`，`--extended` | 扩展信息（uid、inode） | 排权限归属 |
| `-m`，`--memory` | 显示套接字缓冲内存用量 | 查内存占用 |
| `-s`，`--summary` | **连接统计汇总**（各状态多少条） | 一眼看连接数规模 |
| `-r`，`--resolve` | 反解主机名 | 与 `-n` 相反，少用 |

### 4. 输出控制

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-H`，`--no-header` | 不打印表头 | 给脚本处理 |
| `-O`，`--oneline` | 每个套接字打印成一行 | 配合 grep |
| `-A QUERY` | 指定查询哪类套接字集合 | 高级 |
| `-Z`，`--context` | 显示进程 SELinux 上下文 | RHEL 开 SELinux 时 |
| `-N 命名空间` | 切换到指定网络命名空间 | 容器/K8s 排障 |

## 四、由浅入深的典型示例

以下输出为本机（iproute2 5.15.0）实跑。

### 示例 1：统计汇总——连接数规模

```bash
ss -s
```

```text
Total: 150
TCP:   131 (estab 19, closed 95, orphaned 0, timewait 95)

Transport Total     IP        IPv6
RAW      0         0         0
UDP      2         1         1
TCP      36        22        14
INET     38        23        15
FRAG     0         0         0
```

> 关键看 `estab 19`（已建立 19 条）、`timewait 95`（TIME-WAIT 高达 95，常见于短连接高频调用）。

### 示例 2：看所有 TCP 监听端口（最常用组合）

```bash
ss -tlnp
```

```text
State  Recv-Q Send-Q Local Address:Port  Peer Address:PortProcess
LISTEN 0      4096       127.0.0.1:18080      0.0.0.0:*    users:(("gost",pid=1283,fd=3))
LISTEN 0      2048       127.0.0.1:8091       0.0.0.0:*    users:(("python-server",pid=1277,fd=14))
LISTEN 0      10         127.0.0.1:9222       0.0.0.0:*    users:(("chrome",pid=1330,fd=78))
LISTEN 0      511          0.0.0.0:8080       0.0.0.0:*
LISTEN 0      4096               *:10900            *:*
```

逐列读：

- `State=LISTEN`：正在监听，等待别人来连；
- `Recv-Q/Send-Q`：接收/发送队列；
- `Local Address:Port`：本地监听地址和端口。`127.0.0.1:8091` 表示**只监听本机**；`0.0.0.0:8080` / `*:10900` 表示**监听所有网卡**（对外可达）；
- `Peer Address:Port`：对方地址，监听态都是 `*`；
- `Process`：`users:(("进程名",pid=1283,fd=3))`——谁占了这个端口。不加 `-p` 或不是 root 时这列可能空。

> 口诀：`-t` TCP、`-l` 监听、`-n` 数字、`-p` 进程。**`ss -tlnp` 是查端口的万能开头。**

### 示例 3：加 `-a` 看全部（含已连接）

```bash
ss -tna
```

```text
State     Recv-Q Send-Q         Local Address:Port          Peer Address:Port Process
LISTEN    0      4096               127.0.0.1:18080              0.0.0.0:*
LISTEN    0      511                  0.0.0.0:8080               0.0.0.0:*
TIME-WAIT 0      0               9.103.17.236:51810         9.103.17.236:8080
TIME-WAIT 0      0                  127.0.0.1:10000            127.0.0.1:34368
```

> `-a` 把 LISTEN、ESTAB、TIME-WAIT 全列出来。这里能看到一堆 `TIME-WAIT`——连接关闭后内核保留的过渡状态。

### 示例 4：看 UDP 监听

```bash
ss -ulnp
```

```text
State  Recv-Q Send-Q Local Address:Port Peer Address:PortProcess
UNCONN 0      0          127.0.0.1:323       0.0.0.0:*
UNCONN 0      0              [::1]:323          [::]:*
```

> UDP 是无连接的，所以状态是 `UNCONN` 而不是 LISTEN。`127.0.0.1:323` 通常是 chronyd（时间同步）。

### 示例 5：按状态过滤——只看已建立连接

```bash
ss -tn state established
```

```text
Recv-Q Send-Q         Local Address:Port          Peer Address:Port Process
0      0            169.254.112.206:33844        100.65.53.105:443
0      0               9.103.17.236:8080          9.103.17.236:46056
0      0                  127.0.0.1:10000            127.0.0.1:37888
```

> 直接回答"现在有哪些活跃连接、连到哪个对端"。

### 示例 6：查某个端口被谁占了（管道 grep）

```bash
ss -tlnp | grep 10000
```

```text
LISTEN 0      4096       127.0.0.1:10000      0.0.0.0:*    users:(("mcp_vm_server",pid=1298,fd=3))
```

> "Address already in use" 时这一招立刻告诉你是 PID 1298 的 `mcp_vm_server`。

### 示例 7：看 UNIX 域套接字

```bash
ss -x
```

```text
Netid State Recv-Q Send-Q Local Address:Port  Peer Address:PortProcess
u_str ESTAB 0      0 /run/systemd/journal/stdout 3670  * 0
u_str ESTAB 0      0 /run/user/1234/dbus-session-bus 6890  * 0
```

> 本机进程之间不走网络、直接用文件套接字通信（如 systemd、dbus、docker），`-x` 才能看到。

### 示例 8：按对端地址过滤

```bash
ss -tn dst 100.65.53.105
```

> 只看本机连到 `100.65.53.105` 的连接（等价过滤还有 `dst 10.0.0.0/24`、`dport = :443`）。

### 示例 9：看 TCP 内部性能指标

```bash
ss -tni
```

> 在连接详情里额外显示 `cwnd`（拥塞窗口）、`rtt`（往返时延）、`retrans`（重传）等，网络慢时定位是丢包还是窗口太小。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `ss -tlnp` | 看 TCP 监听端口 + 进程（**最常用，查端口被谁占**） |
| `ss -ulnp` | 看 UDP 监听 |
| `ss -tna` | 看所有 TCP 连接（含 TIME-WAIT） |
| `ss -s` | 连接数统计汇总 |
| `ss -tn state established` | 只看活跃连接 |
| `ss -tlnp \| grep 端口` | 定位某端口占用进程 |
| `ss -x` | 看 UNIX 域套接字 |

## 六、RHEL 系与 Debian 系差异

`ss` 来自 iproute2，两系用法一致。需要知道的历史背景：

- 老一代用 `netstat`（来自 net-tools，如 `netstat -tunlp`）。net-tools 已停止维护，**新机器默认可能不装**，命令行为与 `ss` 对应：`netstat -tulnp` ≈ `ss -tulnp`；
- 区别：`ss` 直接读内核（TCP 诊断模块），连接数很大时比 `netstat` 快得多；
- 看进程列：两系下 `-p` 都需要 root 才能看到**别的用户**进程的名字，普通用户只能看自己的。

## 七、新手易错点

1. **不加 `-n` 会慢**：ss 会反解主机名/服务名，连接多时卡很久，排障一律带 `-n`。
2. **`Process` 列为空**：要么没加 `-p`，要么不是 root 看不到别人的进程。
3. **`127.0.0.1:port` 不对外**：只监听本机回环的端口，外面机器连不上，别误以为端口开了就对外可达。
4. **TIME-WAIT 很多不等于故障**：短连接服务（如 HTTP 短连接）大量 TIME-WAIT 是正常现象，`ss -s` 看规模再判断。
5. **`-l` 和不加 `-l` 的区别**：不加 `-l` 默认只看已建立连接，看不到监听端口——查服务端口必须加 `-l`。
6. **UDP 没有 LISTEN**：UDP 是 `UNCONN`，看到它别以为出错了。

## 八、相关命令与文档

- 速查页：[网络命令速查](../network-commands#端口与连接)
- 看网卡/IP：见 [ip addr 与 ip link](./ip-addr-link)
- 测端口通不通：见 [nc 与 telnet](./nc-telnet)
- 抓连接上的包：见 [tcpdump](./tcpdump)
- 防火墙放行端口：见 [iptables](./iptables) / [firewalld 与 ufw](./firewalld-ufw)
- 网络整体原理：见 [Linux 网络专题](../../guide/linux-network)
