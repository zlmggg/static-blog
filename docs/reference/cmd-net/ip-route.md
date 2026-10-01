# ip route 命令详解：看懂路由表、默认网关与源地址

> 本文是 [网络命令速查](../network-commands#网络接口与-ip) 中 `ip route` 的从 0 到 1 详解。
> 目标：把 `ip route help` 里的常用动作讲清楚，看懂"去某个网段要从哪张网卡、经过哪个网关走"。
> 环境依据：iproute2 **5.15.0**（本机实跑 `ip -V`、`ip route`；RHEL/Rocky 自带版本用法一致）。

## 一、命令是干什么的

`ip route` 用来查看和操作 **路由表**：决定一台 Linux 主机收到一个目标地址的数据包时，该从哪张网卡发出去、下一跳网关（下一站）是谁。

- 不带参数（`ip route` / `ip r`）：**查看**整个 IPv4 路由表（最常用）；
- `ip route get 目标IP`：系统真要发数据包给这个 IP 时，会走哪条路（最直观的排障手段）；
- `ip route add/del ...`：临时增删路由（需 root）。

> 类比：路由表就是一张"快递路线表"——包裹要寄到 `192.168.x.x`，看表决定交给哪个快递员（网卡）、再中转给哪个分拣中心（网关）。你手机连 WiFi 后能上网，靠的就是一条"默认路由"：凡是不知道怎么走的目的地，全部丢给路由器（网关）。

什么时候用：
- 服务器多网卡/多网段，搞不清"访问公网走哪张卡"；
- 配了 IP 却上不了网，检查默认路由（default gateway）在不在；
- 专线/多出口场景，要给特定网段指定走特定网关。

## 二、命令语法

```bash
ip route { show | list | get | add | del | change | replace } [选择条件]
```

- `show`（可省略）：列出路由；
- `get 目标地址`：查询"去这个地址走哪条路"，会算出源 IP、出口网卡、网关；
- `add` / `del`：增删路由（需 root，重启失效）；
- 选择条件：`dev 网卡`、`via 网关IP`、`to 目标网段`、`src 源IP`、`table 表名`。

最简用法：

```bash
ip route        # 看路由表
```

## 三、选项全表（对照 `ip route help`）

### 1. 查看类

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `show` / `list` | 列出路由表（默认动作，可省略） | `ip route` 看全部 |
| `show default` | 只看**默认路由**（默认网关） | 快速确认"上外网的门"在不在 |
| `get 地址` | 查系统去该地址实际选哪条路 | 排障利器，能看到 src 和 dev |
| `to PREFIX` | 只看匹配某网段的路由 | `ip route show to 10.0.0.0/8` |
| `dev IFNAME` | 只看从某网卡出发的路由 | `ip route show dev eth0` |
| `table TABLE` | 查指定路由表（`local`/`main`/`all`/表号） | 多路由表策略路由排障 |
| `-n`（配合 show） | 不做反解（iproute 通用） | 更快 |

### 2. 增删改类（需 root）

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `add ... via 网关 dev 网卡` | **加**一条路由（下一跳网关 + 出口网卡） | 给某网段指定专线网关 |
| `add default via 网关 dev 网卡` | 加**默认路由** | 配置默认网关 |
| `del ...` | **删**一条路由 | 改错了的路由 |
| `change` / `replace` | 改/替换已有路由 | 调整 metric、src |
| `src ADDRESS` | 指定该路由的**本地源 IP** | 多 IP 网卡指定用哪个源地址 |
| `metric N` | 路由优先级（越小越优先） | 配双网关做主备 |
| `proto static/kernel` | 路由来源标记 | 区分手工配的 vs 内核自动生成 |

## 四、由浅入深的典型示例

以下输出为本机实跑。

### 示例 1：查看完整路由表

```bash
ip route
```

```text
default via 169.254.112.1 dev eth1 onlink
9.0.0.0/8 via 9.102.0.1 dev eth0 onlink
9.96.0.0/12 via 9.102.0.1 dev eth0 onlink
10.0.0.0/12 via 169.254.112.1 dev eth1 onlink
100.64.0.0/10 via 169.254.112.1 dev eth1 onlink
```

逐行读：

- `default`：**默认路由**，凡是表里没专门匹配的目标，都走它；
- `via 169.254.112.1`：下一跳**网关**（下一站交给这个 IP）；
- `dev eth1`：从 **eth1** 这张网卡发出去；
- `onlink`：强制把网关当作直连在该网卡上（即便网关不在同子网也先这么发）；
- `9.0.0.0/8 via 9.102.0.1 dev eth0`：访问 `9.x.x.x` 这个大网段，走另一条路（网关 `9.102.0.1`、网卡 `eth0`）。

> 匹配原则：**最长前缀优先**。去一个地址时，系统挑掩码最长（最精确）的那条路由。

### 示例 2：只看默认路由（默认网关）

```bash
ip route show default
```

```text
default via 169.254.112.1 dev eth1 onlink
```

> 上不了网时先看这条在不在。没有 `default`，就代表"不知道出门往哪走"。

### 示例 3：查"去某个 IP 实际走哪条路"（排障最准）

```bash
ip route get 223.5.5.5
```

```text
223.5.5.5 via 169.254.112.1 dev eth1 src 169.254.112.206 uid 1234
    cache
```

> 这句最有价值：它告诉你访问 `223.5.5.5` 时——网关是 `169.254.112.1`、从 `eth1` 出、**本地源地址用 `169.254.112.206`**。如果你以为会走 eth0，结果这里是 eth1，就解释了为什么流量不对。

### 示例 4：加一条临时静态路由（需 root）

```bash
sudo ip route add 192.168.50.0/24 via 10.0.0.1 dev eth0
```

> 含义：凡要去 `192.168.50.0/24` 的包，下一跳交给 `10.0.0.1`，从 eth0 出。

### 示例 5：加默认路由（需 root）

```bash
sudo ip route add default via 192.168.1.1 dev eth0
```

> 把默认网关设成 `192.168.1.1`。一般由 DHCP 或 netplan 自动配，手动加常用于容器/直连场景。

### 示例 6：删一条路由（需 root）

```bash
sudo ip route del 192.168.50.0/24
```

> 删掉示例 4 那条。写错网关时常用它纠错。

### 示例 7：指定源地址（多 IP 网卡）

```bash
sudo ip route add 203.0.113.0/24 via 10.0.0.1 dev eth0 src 10.0.0.5
```

> 一张网卡绑了多个 IP 时，用 `src` 强制指定从哪个本地地址发包，对端回包才回得到。

### 示例 8：看策略路由的其它路由表

```bash
ip route show table all
```

> 输出很长。多出口/策略路由场景（`ip rule`）下，规则会引用不同 table，普通 `ip route` 只显示 main 表。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `ip route`（`ip r`） | 看全部路由表 |
| `ip r s` / `ip route show default` | 只看默认网关 |
| `ip route get 目标IP` | 查实际走哪条路、用哪个源 IP（**排障首选**） |
| `ip route add ... via 网关 dev 网卡` | 加静态路由（root） |
| `ip route del ...` | 删路由（root） |

## 六、RHEL 系与 Debian 系差异

`ip route` 来自 iproute2，两系用法一致。区别在**持久化**：

- Ubuntu/Debian：写在 netplan 的 `routes:` 段，或 NetworkManager 连接配置里；
- RHEL/Rocky：写在 `/etc/sysconfig/network-scripts/route-eth0` 或 NetworkManager；
- 老式命令 `route`（net-tools，如 `route -n`）已被弃用，新内容一律 `ip route`。

## 七、新手易错点

1. **没有默认路由就上不了外网**：内网互通正常但公网不通，十有八九缺 `default`。
2. **`via` 的网关必须和出口网卡在同子网**：乱写网关会 `NEXTHOP has no neighbor` 之类错误。
3. **`ip route add` 重启失效**：它是运行时配置，长期要写进 netplan/NetworkManager。
4. **多网卡时别想当然**：以为走 eth0，实际 `ip route get` 显示走了 eth1——一切以 `get` 的结果为准。
5. **加错默认路由会断网**：远程服务器上把 default 指到错误网关，会立刻失联，务必有控制台兜底。
6. **最长前缀匹配**：同目标有多条路由时走最精确那条，不是第一条。
7. **别和 `ip rule` 混为一谈**：`ip route` 管路由表内容，`ip rule` 管"什么时候用哪张表"。

## 八、相关命令与文档

- 速查页：[网络命令速查](../network-commands#网络接口与-ip)
- 看网卡和 IP：见 [ip addr 与 ip link](./ip-addr-link)
- 看邻居/ARP：见 [ip neigh 与 arp](./ip-neigh-arp)
- 端到端路径排障：见 [traceroute 与 mtr](./traceroute-mtr)
- 网络整体原理：见 [Linux 网络专题](../../guide/linux-network)
