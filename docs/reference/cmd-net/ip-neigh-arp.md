# ip neigh 与 arp 命令详解：看懂邻居表和 MAC 对应关系

> 本文是 [网络命令速查](../network-commands#arp-与邻居) 中 `ip neigh` 与 `arp` 的从 0 到 1 详解；本篇一次讲清 **现代邻居表**（`ip neigh`）和 **老 ARP 命令**（`arp`）。
> 目标：看懂"这个 IP 对应的 MAC 地址是什么"，以及为什么会出现 `FAILED`/`STALE` 状态。
> 环境依据：`ip neigh` 来自 iproute2 **5.15.0**（本机实跑）；`arp` 来自 net-tools **2.10-alpha**（本机实跑 `arp --version`，注意：多数新发行版默认不再装 net-tools）。

## 一、命令是干什么的

在同一个以太网（二层）里，机器之间最终是靠 **MAC 地址**通信的。可你只知道对方的 IP，怎么拿到它的 MAC？靠 **ARP 协议**（IPv4）/ NDP（IPv6），问一句"谁是 192.168.1.1，请把你的 MAC 告诉我"。问来的结果就存在一张表里——这就是**邻居表（neighbor table）**。

- `ip neigh`（neigh = neighbor，邻居）：查看/管理这张邻居/MAC 表，iproute2 现代写法；
- `arp`：老的 net-tools 版本，看同一张表的 IPv4 部分。

> 类比：这就像公司内部的"通讯录"——你记得同事的工位号（IP），但当面递东西要叫出真名（MAC）。第一次找人你会问一圈（ARP 请求），问来之后记在小本本上（邻居表），下次直接按小本本走，过一段时间没人用就标记成"可能过期"（STALE）。

什么时候用：
- 同网段两台机器 ping 不通，查邻居表里网关/MAC 对不对；
- 排查 ARP 欺骗、IP 冲突；
- 容器/云网络里看网关 MAC 是不是 `PERMANENT`。

## 二、命令语法

```bash
ip neigh { show | add | del | flush } [ to 目标IP ] [ dev 网卡 ]
arp [-n] [-i 网卡] [ -s IP MAC | -d IP ]
```

- `ip neigh show`：看邻居表（`show` 可省略，直接 `ip neigh`）；
- `to IP` / `dev 网卡`：过滤条件；
- `arp -n`：数字方式显示（不反解主机名）。

最简用法：

```bash
ip neigh        # 看邻居表
```

## 三、选项全表（对照 `ip neigh help` / `arp` 用法）

### 1. `ip neigh`

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `show` | 显示邻居表（可省略） | `ip neigh` 看全部 |
| `to PREFIX` | 只看属于某网段的邻居 | 过滤指定网关 |
| `dev IFNAME` | 只看某网卡上的邻居 | `ip neigh show dev eth0` |
| `nud STATE` | 按状态过滤（见下） | 找 `failed` 的坏邻居 |
| `add ... lladdr MAC dev ...` | 静态加一条邻居（需 root） | 固定网关 MAC |
| `del ...` | 删一条邻居（需 root） | 强制刷新坏表项 |
| `flush` | 清空邻居表（需 root） | 排障时一次性重来 |

`nud`（neighbor unreachability detection，邻居可达性检测）状态含义：

| 状态 | 含义 |
|---|---|
| `PERMANENT` | 永久条目，手工配的或内核固定（如网关），不过期 |
| `REACHABLE` | 近期确认可达，正常 |
| `STALE` | 放了一段时间没人用，"可能过期"，下次发包会再探测 |
| `PROBE` | 正在探测是否还可达 |
| `FAILED` | 探测失败，邻居不可达 |
| `INCOMPLETE` | 正在 ARP 解析中，还没拿到 MAC |

### 2. `arp`（net-tools，老命令）

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-a` | BSD 风格显示所有条目 | 习惯老式输出 |
| `-n` | 不反解主机名，纯数字 | **推荐**，更快更干净 |
| `-i IF` | 指定网卡 | `arp -i eth0 -n` |
| `-s IP MAC` | 静态绑定 ARP（需 root） | 防网关 ARP 欺骗 |
| `-d IP` | 删除条目（需 root） | 刷新错误 ARP |
| `-v` | 详细输出 | 排障 |

## 四、由浅入深的典型示例

以下输出为本机实跑。

### 示例 1：看邻居表（现代写法）

```bash
ip neigh
```

```text
169.254.112.1 dev eth1 lladdr ee:ff:ff:ff:ff:ff PERMANENT
9.102.0.1 dev eth0 lladdr ee:ff:ff:ff:ff:ff PERMANENT
```

逐列读：

- `169.254.112.1`：邻居 IP（这是默认网关）；
- `dev eth1`：这个邻居在 eth1 网卡的网段上；
- `lladdr ee:ff:ff:ff:ff:ff`：它的 **MAC 地址**；
- `PERMANENT`：永久条目，不会过期。

### 示例 2：只看某张网卡的邻居

```bash
ip neigh show dev eth0
```

```text
9.102.0.1 dev eth0 lladdr ee:ff:ff:ff:ff:ff PERMANENT
```

> 多网卡环境下定位"哪个网关走哪张卡"很有用。

### 示例 3：老命令 arp 看同一张表

```bash
arp -n
```

```text
Address                  HWtype  HWaddress           Flags Mask            Iface
169.254.112.1            ether   ee:ff:ff:ff:ff:ff   CM                    eth1
9.102.0.1                ether   ee:ff:ff:ff:ff:ff   CM                    eth0
```

> 对比可见，`arp -n` 显示的是同一份数据，只是列名老派：`Address`=IP，`HWaddress`=MAC，`Iface`=网卡。`CM` 大致对应 `PERMANENT`/completed。

### 示例 4：发现坏邻居（FAILED / INCOMPLETE）

```bash
ip neigh show nud failed
```

> 实际环境里若某网关 MAC 解析失败，这里会出现 `FAILED` 或 `INCOMPLETE`，对应现象就是"同网段也连不通"。

### 示例 5：静态绑定网关 MAC（防 ARP 欺骗，需 root）

```bash
sudo ip neigh replace 169.254.112.1 lladdr ee:ff:ff:ff:ff:ff dev eth1 nud permanent
```

> 把网关 IP→MAC 写死，避免内网 ARP 投毒把流量引到假网关上。

### 示例 6：强制刷新一条错误邻居（需 root）

```bash
sudo ip neigh del 192.168.1.50 dev eth0
```

> 对方换了网卡/重启后 MAC 变了，但本机还记着旧 MAC，删掉让它重新 ARP 一次。

### 示例 7：清空整张邻居表（需 root，谨慎）

```bash
sudo ip neigh flush all
```

> ⚠️ 会让本机下次通信重新做一遍 ARP，瞬时可能有几个包延迟。线上大动作前想清楚。

### 示例 8：老命令静态绑定（等价做法）

```bash
sudo arp -s 192.168.1.1 aa:bb:cc:dd:ee:ff
```

> 与示例 5 效果类似，但 `arp` 已不推荐，新脚本一律用 `ip neigh`。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `ip neigh`（`ip n`） | 看邻居/MAC 表（**推荐**） |
| `ip n s dev eth0` | 只看某网卡邻居 |
| `ip n show nud failed` | 找出失败的坏邻居 |
| `arp -n` | 老命令数字式看表 |
| `sudo ip neigh del IP dev eth0` | 刷新一条邻居 |

## 六、RHEL 系与 Debian 系差异

- `ip neigh`（iproute2）两系一致，**推荐学它**；
- `arp`（net-tools）：较新的发行版（如 Debian 12+、RHEL 9）**默认不装** net-tools，要用得 `sudo apt install net-tools` 或 `sudo dnf install net-tools`。本环境恰好装了，所以能实跑；
- 新脚本、新文档一律使用 `ip neigh`，`arp` 仅用于看懂老机器上的命令。

## 七、新手易错点

1. **邻居表里没有 ≠ 不通**：没流量时表是空的，发个包就会自动 ARP 填进来。
2. **`FAILED`/`INCOMPLETE` 才是真问题**：前者网关/目标不可达，后者还在解析。
3. **MAC 变了要刷新**：对方重装系统/换网卡后旧 MAC 缓存会导致间歇不通，`ip neigh del` 清掉即可。
4. **别在云/K8s 网络里乱绑静态 MAC**：云虚拟网关 MAC 可能漂移，绑死反而出问题。
5. **`ip neigh flush all` 是大招**：会重建所有邻居，别在高峰期随手敲。
6. **IPv6 邻居也在这张表**：`ip neigh` 同时管 IPv6 的 NDP，不只是 IPv4 ARP。

## 八、相关命令与文档

- 速查页：[网络命令速查](../network-commands#arp-与邻居)
- 看网卡/IP：见 [ip addr 与 ip link](./ip-addr-link)
- 看路由：见 [ip route](./ip-route)
- 抓 ARP 包看请求过程：见 [tcpdump](./tcpdump)
- 网络整体原理：见 [Linux 网络专题](../../guide/linux-network)
