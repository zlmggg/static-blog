# traceroute、mtr 与 tracepath 命令详解：看数据包走了哪几跳

> 本文是 [网络命令速查](../network-commands#路由追踪) 中 `traceroute`、`mtr`、`tracepath` 的从 0 到 1 详解；本篇一次讲清这三个"路径追踪"工具。
> 目标：知道什么时候用哪个，看懂每一跳的 IP、延迟和丢包发生在哪一段。
> 环境依据：本沙箱**三者均未安装**，以下选项与示例依据官方 man 文档锁定——traceroute 经典版（traceroute 8，见 man7.org Linux man-pages）、mtr（Debian bookworm `mtr-tiny` 0.94 系列）、tracepath（iputils **20221126**，Debian bookworm）。示例输出为官方文档/典型形态示意，非本机实跑。

## 一、命令是干什么的

ping 只告诉你"到没到、延迟多少"，但如果中间某一段断了，它不知道**断在哪一跳**。路径追踪工具就是逐跳（hop）探测：把包的 TTL 从 1 开始逐个加 1，每经过一台路由器，TTL 减到 0 就回一个 ICMP 超时包，于是你就能一路数清楚"从本机到目标，中间经过了哪些路由器"。

- `traceroute`：经典逐跳追踪，一次跑完出结果；
- `mtr`：把 ping 和 traceroute 合体，**实时持续刷新**每一跳的丢包率和延迟，最适合看"哪一跳在丢包"；
- `tracepath`：iputils 出品的轻量版，**不需要 root**，还顺带探测路径 MTU。

> 类比：ping 像你直接问"对方在家吗"；traceroute/mtr 像你派一个快递员，每过一个路口就数一下自己是第几个路口——这样就知道整条路线依次经过哪些路口，以及哪段路堵/丢东西。

什么时候用：
- ping 通但很慢/偶尔丢包，定位是哪一跳出问题；
- 跨机房/跨运营商访问慢，看路径绕到了哪里；
- MTU 问题（大包被丢）用 tracepath 探路径 MTU。

## 二、命令语法

```bash
traceroute [选项] 目标主机
mtr [选项] 目标主机
tracepath [选项] 目标主机
```

- 目标：域名或 IP，必填；
- 三者都是探测工具，不加 `-c`/`-r` 时 `mtr` 默认进**交互界面**，按 `q` 退出。

## 三、选项全表（据官方 man）

### 1. traceroute

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-n` | 不反解主机名，纯 IP | 更快、更干净 |
| `-m 跳数` | 最大跳数（默认 30） | 限制探测深度 |
| `-w 秒` | 等待回复超时（默认 5 秒） | 慢链路调大 |
| `-q 次数` | 每跳发几个探测包（默认 3） | 想多测几次 |
| `-I` | 用 **ICMP Echo** 探测（像 ping） | 默认 UDP 被防火墙挡时换它 |
| `-T` | 用 **TCP SYN** 探测 | 绕过只放行 TCP 的防火墙 |
| `-p 端口` | 指定目标端口（TCP/UDP） | 如 `-T -p 443` |
| `-A` | 打印每跳的 **AS 号** | 看经过哪些运营商 |
| `-i 网卡` | 指定出口网卡 | 多网卡 |

### 2. mtr

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-r` / `--report` | **报告模式**，跑完输出一次就退出 | 写报告/脚本（非交互） |
| `-c 次数` | 一共发多少个包 | 配 `-r` 用 |
| `-n` / `--no-dns` | 不反解域名 | 更快 |
| `-i 秒` | 每跳发包间隔 | 默认 1 秒 |
| `--tcp` / `--udp` | 用 TCP/UDP 探测（默认 ICMP） | 绕防火墙 |
| `-P 端口` | 指定端口 | 如 `--tcp -P 443` |
| `--report-wide` | 宽列报告格式 | 列更全 |

### 3. tracepath（iputils，无需 root）

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-n` | 只打印 IP，不反解 | 快 |
| `-b` | 同时打印主机名和 IP | 折中 |
| `-m 跳数` | 最大跳数（默认 30） | 限制深度 |
| `-l 包长` | 设初始包长度 | 配合测 MTU |
| `-4` / `-6` | 强制 IPv4 / IPv6 | `tracepath -6` 追踪 IPv6 |

## 四、由浅入深的典型示例

以下为据官方文档的典型输出形态（示意），非本机实跑。

### 示例 1：基础逐跳追踪

```bash
traceroute -n example.com
```

```text
traceroute to example.com (93.184.216.34), 30 hops max, 60 byte packets
 1  192.168.1.1     1.0 ms  1.1 ms  0.9 ms
 2  100.64.0.1      5.2 ms  5.0 ms  5.3 ms
 3  203.0.113.5    12.4 ms 12.1 ms 12.6 ms
 4  *  *  *
 5  93.184.216.34  88.3 ms 87.9 ms 88.1 ms
```

逐跳读：第 1 列是第几跳；后面三个时间是该跳 3 个探测包的 RTT；`* * *` 表示这一跳没回应（很多路由器默认不回 ICMP，**不代表这一跳坏了**）。

### 示例 2：用 ICMP 探测（默认 UDP 被挡时）

```bash
traceroute -I -n 223.5.5.5
```

> 默认走不太常用的 UDP 端口，常被防火墙拦导致一路 `*`；换成 `-I`（ICMP Echo）或 `-T`（TCP）往往能穿过去。

### 示例 3：用 TCP 443 探测（绕防火墙）

```bash
traceroute -T -p 443 -n example.com
```

> 专门追踪"访问 443 端口"这条路，适合测 HTTPS 站点。

### 示例 4：mtr 交互式实时看丢包

```bash
mtr example.com
```

> 进入全屏界面，每一跳实时刷新 Loss%（丢包率）、Snt（已发包数）、Last/Avg/Best/Wrst（延迟）。哪一跳 Loss% 高，问题就大致在那一段及之后。按 `q` 退出。

### 示例 5：mtr 报告模式（一次性输出，适合贴工单）

```bash
mtr --report -c 100 -n example.com
```

```text
 Start: 2026-09-30T15:00:00+0800
HOST: server        Loss%   Snt   Last   Avg  Best  Wrst StDev
  1.|-- 192.168.1.1   0.0%   100    1.0   1.1   0.9   1.5   0.1
  2.|-- 100.64.0.1    0.0%   100    5.2   5.1   5.0   6.0   0.2
  3.|-- 203.0.113.5   2.0%   100   12.4  12.1  11.9  15.0   0.5
```

> `-c 100` 每跳发 100 个包再统计丢包，结果稳定，适合贴进故障工单。

### 示例 6：tracepath 探测路径 MTU（无需 root）

```bash
tracepath -n example.com
```

```text
 1?: [LOCALHOST]                      pmtu 1500
 1:  192.168.1.1                  1.234ms
 2:  100.64.0.1                   5.678ms pmtu 1400
 2:  example.com                 88.123ms reached
 Resume: pmtu 1400  hops 2  back 2
```

> 注意 `pmtu 1400`——沿途发现路径最大传输单元是 1400。大包不通/连接挂起时，这是定位 MTU 黑洞的关键。

### 示例 7：tracepath 追踪 IPv6

```bash
tracepath -6 -n 2606:4700::1111
```

> 用 IPv6 路线追踪，适合排 IPv6 连通性。

### 示例 8：限定最大跳数与等待

```bash
traceroute -n -m 15 -w 2 example.com
```

> 最多探 15 跳、每跳等 2 秒，避免在超长路径上干等。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `traceroute -n 目标` | 基础逐跳路径 |
| `traceroute -T -p 443 -n 目标` | 用 TCP 443 绕墙追踪 |
| `mtr 目标` | 交互式实时看每跳丢包（**排丢包首选**） |
| `mtr -r -c 100 -n 目标` | 报告模式贴工单 |
| `tracepath -n 目标` | 免 root + 探路径 MTU |

## 六、RHEL 系与 Debian 系差异

- 包名：traceroute 两系都需单独装（Debian `traceroute`、RHEL `traceroute`）；mtr 装 `mtr`（Debian 完整功能）或 `mtr-tiny`（无 GTK）；tracepath 在 Debian 属于 `iputils-tracepath`；
- 两系选项一致；
- 现代云/容器环境常默认不装，需 `apt install traceroute mtr-tiny` 或 `dnf install traceroute mtr`。

## 七、新手易错点

1. **中间跳 `* * *` 不一定是故障**：很多路由器被配置为不回 ICMP 超时包，链路其实是通的。
2. **看丢包要看"是否一路持续"**：某一跳显示高丢包但它后面跳都正常，往往只是那台路由器限速 ICMP，真问题要看最后一跳之前是否持续丢包。
3. **回程路径可能不对称**：去和回走的路不一定一样，单向丢包别武断。
4. **`-T` 比 `-I` 更容易穿防火墙**：纯 UDP/ICMP 被挡时换 TCP 443 试试。
5. **tracepath 不需要 root**：普通用户就能跑，受限环境里它是后备选择。
6. **mtr 不加 `-r` 是交互界面**：不知道按 `q` 退出会以为卡住了。

## 八、相关命令与文档

- 速查页：[网络命令速查](../network-commands#路由追踪)
- 基础连通性：见 [ping](./ping)
- 看路由表：见 [ip route](./ip-route)
- 抓路径上的包：见 [tcpdump](./tcpdump)
- 网络整体原理：见 [Linux 网络专题](../../guide/linux-network)
