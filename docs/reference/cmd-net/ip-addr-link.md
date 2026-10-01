# ip addr 与 ip link 命令详解：看清网卡、IP 与 MAC

> 本文是 [网络命令速查](../network-commands#网络接口与-ip) 中 `ip addr`、`ip link` 的从 0 到 1 详解；本篇一次讲清 **看地址**（`ip addr`）和 **看链路状态**（`ip link`）这一对孪生命令。
> 目标：把 `ip addr help`、`ip link help` 里的常用选项讲清楚，多看几遍后，你在服务器上敲 `ip addr help` 就知道该用哪个。
> 环境依据：iproute2 **5.15.0**（本机实跑 `ip -V`，Ubuntu 22.04 自带；RHEL/Rocky 8/9 自带 4.x~5.x，子命令用法一致）。

## 一、命令是干什么的

`ip` 是 Linux 新一代网络配置工具集 **iproute2** 的总入口，`ip addr` 和 `ip link` 是其中最常用的两个子命令：

- `ip addr`（`addr` = address，地址）：**看/配网卡上的 IP 地址**，包括 IPv4、IPv6、广播地址、label；
- `ip link`（`link` = 链路层）：**看/配网卡本身**，包括 MAC 地址、MTU、网卡是 `up`（开）还是 `down`（关）、队列长度。

> 类比：在 Windows「网络连接」里，你能看到网卡名（以太网）、它的状态（已启用/已禁用）、MAC 地址，以及它拿到的 IPv4/IPv6 地址。`ip link` 对应"网卡本身和它的开关"，`ip addr` 对应"这张网卡上挂了哪些 IP"。它们是老命令 `ifconfig` 的现代替代品。

什么时候用：
- 服务器上不去网，第一件事往往就是 `ip addr` 看本机有没有拿到 IP；
- 网卡没起来，用 `ip link` 看状态、必要时 `ip link set eth0 up` 拉起；
- 排查 IPv6 是否生效、MAC 是否对得上交换机/云平台的记录。

## 二、命令语法

```bash
ip addr [show] [dev 网卡名]                # 看地址（show 可省略）
ip link [show] [dev 网卡名]                # 看链路（show 可省略）
ip link set 网卡名 { up | down }            # 改网卡状态
```

- `addr` / `link`：子命令，决定你操作的是"IP 地址层"还是"链路层"；
- `[show]`：查看动作，可省略，所以 `ip addr` 等价于 `ip addr show`；
- `dev 网卡名`：指定操作哪张网卡，如 `eth0`；不写就列出全部；
- 管理类动作（`add` / `del` / `set`）通常需要 root，且**重启后失效**，长期配置要走 netplan/NetworkManager。

最简用法：

```bash
ip addr        # 列出所有网卡的 IP（最常用）
```

## 三、选项全表（对照 `ip addr help` / `ip link help`）

下面只列日常高频项；完整语法见本机 `ip addr help`。短长选项同格写。

### 1. `ip addr` 查看与过滤

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `show` | 显示地址（默认动作，可省略） | `ip addr show eth0` 只看一张卡 |
| `dev IFNAME` | 只看指定网卡 | `ip addr show dev eth0`，避免满屏 |
| `-brief`（`-br`） | 精简格式，一行一张卡 | 快速扫视"哪张卡什么状态、什么 IP" |
| `scope SCOPE` | 按作用域过滤（`host`/`link`/`global`） | 只看全局地址 `scope global` |
| `to PREFIX` | 只看属于某网段的地址 | 如 `to 10.0.0.0/8` |
| `label LABEL` | 按地址别名标签过滤 | 找 `eth0:1` 这类老别名 |
| `up` | 只看处于启用状态的网卡 | 过滤掉 down 掉的卡 |
| `add IFADDR dev` | 给网卡**加**一个 IP（需 root） | 临时多挂一个 IP |
| `del IFADDR dev` | **删**一个 IP（需 root） | 临时摘掉某 IP |
| `flush` | 清空某类地址（需 root） | 清空某网卡所有临时地址 |

### 2. `ip link` 查看与网卡开关

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `show` | 显示链路层信息（可省略） | `ip link` 或 `ip link show eth0` |
| `set dev IFNAME up/down` | 把网卡**启用/禁用**（需 root） | 网卡没起来时拉起它 |
| `set ... mtu MTU` | 设置 MTU（需 root） | 隧道/云环境 MTU 要调小（如 1420） |
| `set ... address LLADDR` | 修改 MAC 地址（需 root） | MAC 变更/伪装 |
| `-s` / `-stats` | 额外显示收发包统计（RX/TX 计数） | 看网卡有没有丢包、错误包 |
| `-details` | 更详细的驱动/队列信息 | 深入排查时 |
| `arp on/off` | 打开/关闭该卡的 ARP | 特殊路由场景 |
| `master DEVICE` / `nomaster` | 把网卡绑到 bridge/bond / 解绑 | 做网桥、绑定网卡 |

## 四、由浅入深的典型示例

以下输出均为本机（iproute2 5.15.0）实跑。

### 示例 1：列出所有网卡和 IP（最高频）

```bash
ip addr
```

```text
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host noprefixroute
       valid_lft forever preferred_lft forever
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 00:16:3e:0c:4f:f2 brd ff:ff:ff:ff:ff:ff
    inet 9.103.17.236/32 brd 9.103.17.236 scope global eth0
       valid_lft forever preferred_lft forever
    inet6 fe80::216:3eff:fe0c:4ff2/64 scope link dadfailed tentative
       valid_lft forever preferred_lft forever
```

逐行读：

- 第一行 `2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> ... state UP`：网卡编号、标志位（`UP` = 已启用）、MTU、队列调度算法 `qdisc`、状态；
- `link/ether 00:16:3e:0c:4f:f2`：这就是 **MAC 地址**（以太网硬件地址），`brd ff:ff:ff:ff:ff:ff` 是广播 MAC；
- `inet 9.103.17.236/32`：**IPv4 地址**，`inet` = IPv4，`/32` 是前缀掩码，`scope global` 表示全局可用；
- `inet6 fe80::.../64`：**IPv6 链路本地地址**，`fe80::/10` 开头的都是只在本网段有效的"临时"IPv6；
- `lo` 是回环网卡，固定 `127.0.0.1` / `::1`，别去动它。

### 示例 2：精简模式，一行一张卡

```bash
ip -brief addr
```

```text
lo               UNKNOWN        127.0.0.1/8 ::1/128
eth0             UP             9.103.17.236/32 fe80::216:3eff:fe0c:4ff2/64
eth1             UP             169.254.112.206/32 fe80::7485:7cff:fefb:711d/64
```

> 三列：网卡名、状态（`UP`/`DOWN`/`UNKNOWN`）、拿到的地址。几十张卡时一眼扫完。

### 示例 3：只看某一张网卡

```bash
ip addr show dev eth0
```

> 等价简写 `ip a s eth0`（`a`=`addr`，`s`=`show`）。线上排障时最常用，避免被其它网卡刷屏。

### 示例 4：只看网卡链路层（MAC、MTU、开关）

```bash
ip link
```

```text
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN mode DEFAULT group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP mode DEFAULT group default qlen 1000
    link/ether 00:16:3e:0c:4f:f2 brd ff:ff:ff:ff:ff:ff
```

> 对比 `ip addr`：这里**不显示 IP**，只显示二层信息。`<...>` 里的 `UP` 就是网卡开关状态。

### 示例 5：看网卡收发包计数（有没有错包/丢包）

```bash
ip -s link
```

```text
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP mode DEFAULT group default qlen 1000
    link/ether 00:16:3e:0c:4f:f2 brd ff:ff:ff:ff:ff:ff
    RX:  bytes packets errors dropped  missed   mcast
      2871674  9564      0       0       0       0
    TX:  bytes packets errors dropped carrier collsns
       983176  3852      0       0       0       0
```

> `RX` = 接收，`TX` = 发送。重点盯 `errors`、`dropped`：长期增长说明网线/驱动/丢包有问题。

### 示例 6：把网卡拉起/关掉（需 root，危险）

```bash
sudo ip link set eth1 down      # 先关掉
sudo ip link set eth1 up        # 再拉起
```

> ⚠️ 对**正在被 SSH 使用的网卡**执行 `down` 会立刻断连！改之前确认你还有控制台/其它网卡可用。

### 示例 7：临时给网卡加/删一个 IP（需 root）

```bash
sudo ip addr add 10.10.10.5/24 dev eth0
sudo ip addr del 10.10.10.5/24 dev eth0
```

> 临时调试用，**重启就没**。要永久生效请改 netplan / NetworkManager 配置，不要指望这条命令长期管用。

### 示例 8：调 MTU（隧道/VPN 环境常见）

```bash
sudo ip link set eth1 mtu 1420
```

> 本例环境里 `eth1` 的 MTU 就是 1420（隧道封装后需要变小，否则大包被分片或丢弃）。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `ip addr`（`ip a`） | 看所有网卡 IP（**最常用**） |
| `ip a s eth0` | 只看 eth0 的地址 |
| `ip -br a` | 精简一行一张卡 |
| `ip link`（`ip l`） | 看 MAC / MTU / 网卡开关 |
| `ip -s link` | 看收发包计数、错包丢包 |
| `ip link set eth0 up` | 拉起网卡（需 root） |

## 六、RHEL 系与 Debian 系差异

`ip` 来自 iproute2，**RHEL/CentOS/Rocky 与 Ubuntu/Debian 用法完全一致**，上述命令照搬即可。细微差别：

- 老系统里很多人仍习惯 `ifconfig`（来自 net-tools），但 net-tools 已逐步被弃用，**新内容一律学 `ip`**；
- 永久配置方式不同：Ubuntu 用 netplan（`/etc/netplan/*.yaml`），RHEL/Rocky 用 NetworkManager 或 `/etc/sysconfig/network-scripts/`；
- 云主机的默认网卡名可能是 `ens3`、`eth0`、`enp0s3` 等，以 `ip link` 实际看到的为准。

## 七、新手易错点

1. **`UP` 是网卡开了，不代表有网**：网卡 up 了但没拿到 IP（DHCP 失败）照样上不了网，要 `ip addr` 一起看。
2. **`fe80::` 开头的 IPv6 不是公网地址**：它是链路本地地址，只在本网段有效，别拿去当对外 IPv6。
3. **`/32`、`/24` 是掩码不是编号**：`9.103.17.236/32` 表示单个地址；`/24` 才是常见的子网掩码 255.255.255.0。
4. **`ip link set down` 自己把自己踢下线**：SSH 登录到某张网卡上，再 `down` 它，连接立刻断开。
5. **临时 IP 重启失效**：`ip addr add` 是内存里的运行时配置，重启/重启网络服务后消失，长期配置走 netplan。
6. **别去动 `lo` 回环网卡**：它挂了会导致本机很多服务互相通信异常。
7. **`ip a` 里看不到 IP 不代表网卡坏了**：可能只是 DHCP 没租约成功，去查 DHCP/网络配置。

## 八、相关命令与文档

- 速查页：[网络命令速查](../network-commands#网络接口与-ip)
- 看路由表/默认网关：见 [ip route](./ip-route)
- 看 ARP/MAC 邻居表：见 [ip neigh 与 arp](./ip-neigh-arp)
- 看端口与连接：见 [ss](./ss)
- 网络整体原理：见 [Linux 网络专题](../../guide/linux-network)
