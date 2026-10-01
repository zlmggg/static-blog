# iptables 命令详解：Linux 包过滤防火墙规则（-L/-A/-D/-I/-P/-j/-t nat）

> 本文是 [网络命令速查](../network-commands#防火墙-速查) 中 `iptables` 的从 0 到 1 详解。
> 目标：看懂四表五链，会加/删/查规则、设默认策略、做 NAT，知道和 nftables 的关系。
> 环境依据：本机实跑 **iptables v1.8.7 (legacy)**（`iptables -V`、`iptables -h`；RHEL/Rocky 8/9 自带 1.8.x，用法一致）。注意：本沙箱非 root，规则列表/增删无法实跑，下面命令为据 `-h` 与 man 的标准写法，输出为典型形态示意。完整防火墙原理另见 [iptables 防火墙指南](../../guide/linux-security-iptables)。

## 一、命令是干什么的

`iptables` 配置 Linux 内核里的**包过滤防火墙**：决定哪些数据包放行、哪些丢弃、哪些做地址转换（NAT）。它是服务器安全的第一道门。

核心概念：

- **表（table）**：按用途分，最常用 `filter`（过滤）和 `nat`（地址转换）；
- **链（chain）**：表里的规则流水线。`filter` 表默认三条链——`INPUT`（进本机的包）、`OUTPUT`（本机发出的包）、`FORWARD`（穿过本机转发的包）；
- **规则（rule）**：每条规则说"匹配某条件，就执行某动作"；
- **动作 target**：`ACCEPT`（放行）、`DROP`（丢弃）、`REJECT`（拒绝并回复）、`SNAT`/`MASQUERADE`（源地址转换）。

> 类比：iptables 像一栋大楼的门禁系统。每个进门的包裹（包）都要依次过几道检查岗（链），每道岗上贴了一堆规则（规则）："从这个 IP 来的放行、去这个端口的拦下"。最后有个总策略（policy）：没匹配上的包裹默认是放行还是拒收。

什么时候用：
- 只对外开放 80/443/22，其余端口全关；
- 做网关/路由器时配 NAT 让内网机器共享公网；
- 排查"服务起了但外面连不上"，多半是防火墙挡了。

## 二、命令语法

```bash
iptables [-t 表] 动作 [链] [匹配条件] -j 动作
```

- `[-t 表]`：默认 `filter`，NAT 要写 `-t nat`；
- `动作`：`-L` 查、`-A` 追加、`-I` 插入、`-D` 删除、`-P` 设默认策略、`-F` 清空；
- `匹配条件`：`-p 协议`、`--dport 端口`、`-s 源IP`、`-i 入网卡`、`-o 出网卡`；
- `-j 动作`：匹配后干什么（ACCEPT/DROP/...）。

所有**修改类**操作都要 root。

## 三、选项全表（对照 `iptables -h`）

### 1. 动作（对规则做什么）

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-L` | **列出**规则 | 查当前防火墙 |
| `-A 链` | 把规则**追加**到链尾 | 加一条放行规则 |
| `-I 链 [序号]` | **插入**到链首（或指定位置） | 让某规则优先匹配 |
| `-D 链 序号/规则` | **删除**规则（按序号或内容） | 删掉错规则 |
| `-R 链 序号` | 替换某条规则 | 修改 |
| `-P 链 target` | 设链的**默认策略** | `iptables -P INPUT DROP` |
| `-F [链]` | **清空**链里所有规则（危险） | 重置 |
| `-Z` | 清零计数器 | 重新统计 |
| `-N 链` / `-X 链` | 新建/删除自定义链 | 组织规则 |

### 2. 匹配条件

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-p 协议` | 匹配协议（tcp/udp/icmp） | `-p tcp` |
| `--dport 端口` | 目的端口（要配合 `-p tcp/udp`） | 开放 80 端口 |
| `--sport 端口` | 源端口 | 少见 |
| `-s 地址[/掩码]` | 源 IP | 只允许某 IP 段 |
| `-d 地址[/掩码]` | 目的 IP | 少见 |
| `-i 网卡` | 从哪块网卡进来 | `-i eth0` |
| `-o 网卡` | 从哪块网卡出去 | NAT/转发 |
| `-m state --state 状态` | 连接状态匹配 | 放行已建立连接 |

### 3. 输出与其它

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-n` | 数字显示（不反解） | 看得快 |
| `-v` | 详细（带计数器、网卡） | 看流量统计 |
| `--line-numbers` | 显示规则序号 | 删除时定位 |
| `-t 表` | 指定表（filter/nat/mangle） | 配 NAT 用 `-t nat` |
| `-j target` | 跳转到目标动作 | ACCEPT/DROP/SNAT... |
| `-w` | 等待锁（避免并发冲突） | 脚本里加 |

## 四、由浅入深的典型示例

以下命令均需 root，输出为典型形态示意（本沙箱非 root 无法实跑 `-L`）。

### 示例 1：列出 filter 表规则（数字 + 序号）

```bash
sudo iptables -L -n --line-numbers
```

```text
Chain INPUT (policy ACCEPT)
num  pkts bytes target     prot opt in     out     source               destination
1    123k  45M ACCEPT     all  --  lo     *       0.0.0.0/0            0.0.0.0/0
2     10k 800M ACCEPT     tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            tcp dpt:22
```

> 第一列 `num` 是规则序号，删除时用；`pkts/bytes` 是命中计数；`policy ACCEPT` 是该链默认策略。

### 示例 2：放行 SSH（22 端口）

```bash
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
```

> 在 INPUT 链末尾加一条：目的端口 22 的 TCP 包放行。⚠️ 远程操作前务必先放行 22，否则会把自己锁在外面。

### 示例 3：放行 HTTP/HTTPS

```bash
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
```

### 示例 4：只允许某网段访问某端口

```bash
sudo iptables -A INPUT -s 192.168.1.0/24 -p tcp --dport 3306 -j ACCEPT
```

> 只让内网段访问数据库 3306，其它来源默认被后面 DROP 掉。

### 示例 5：放行已建立/相关连接（关键）

```bash
sudo iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
```

> 本机主动出去的连接，对方回来的包靠这条放行。**几乎所有防火墙都该有它**，否则出方向会异常。

### 示例 6：设置默认策略为 DROP（危险）

```bash
sudo iptables -P INPUT DROP
```

> ⚠️ 设成 DROP 后，凡是没被前面 ACCEPT 规则匹配的进来的包全丢。**设之前务必确保 22 端口已放行且 lo 已放行**，否则立刻失联。

### 示例 7：删除一条规则

```bash
sudo iptables -L INPUT -n --line-numbers     # 先看序号
sudo iptables -D INPUT 3                     # 删掉第 3 条
```

> `-D` 可以按序号删，也可以把整条规则原样再写一遍来删。

### 示例 8：配 NAT（共享上网/端口映射）

```bash
sudo iptables -t nat -A POSTROUTING -s 10.0.0.0/24 -o eth0 -j MASQUERADE
sudo iptables -t nat -A PREROUTING -p tcp --dport 8080 -j DNAT --to-destination 10.0.0.5:80
```

> 第一条：内网 `10.0.0.0/24` 从 eth0 出去时做源地址伪装（MASQUERADE），实现共享公网；第二条：把访问本机 8080 的流量转发到内网 `10.0.0.5:80`。

### 示例 9：清空规则（危险）

```bash
sudo iptables -F
sudo iptables -P INPUT ACCEPT     # 顺便把默认策略改回 ACCEPT
```

> ⚠️ `-F` 清空所有规则。远程服务器上执行后如果策略是 DROP 会立刻断连，慎用。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `sudo iptables -L -n -v --line-numbers` | 详细列规则（**查规则首选**） |
| `sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT` | 放行 22 |
| `sudo iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT` | 放行回程 |
| `sudo iptables -D INPUT 3` | 删第 3 条 |
| `sudo iptables -P INPUT DROP` | 默认拒绝（危险） |
| `sudo iptables -t nat -L -n` | 看 NAT 规则 |

## 六、RHEL 系与 Debian 系差异

- 包名：`iptables` 两系都带；现代发行版默认转向 **nftables**（见 [nftables](./nftables)），iptables 多为兼容层；
- 持久化：iptables 规则**重启丢失**。Debian 用 `iptables-persistent`（`netfilter-persistent save`），RHEL 旧版用 `service iptables save`，新版改用 firewalld（见 [firewalld 与 ufw](./firewalld-ufw)）；
- RHEL 7+ 默认防火墙是 firewalld，不建议直接裸写 iptables，而是通过 `firewall-cmd` 管理。

## 七、新手易错点

1. **远程设默认 DROP 前先放行 SSH**：这是最经典的把自己锁在门外事故。
2. **规则按顺序匹配**：命中第一条就停，所以 `-I`（插前面）和 `-A`（加后面）效果可能完全不同。
3. **别忘了 lo 和 ESTABLISHED**：本机回环和回程包不放行，会出现各种诡异问题。
4. **规则重启就没**：手动 `iptables -A` 是内存配置，要持久化得存配置或用 firewalld/ufw。
5. **DROP 与 REJECT 区别**：DROP 静默丢包（客户端干等超时），REJECT 主动拒绝（立刻报错）。
6. **`-F` 是大招**：清空规则前确认你还有别的登录途径。
7. **云安全组在外面**：云上即使 iptables 全开，云平台安全组仍可能挡端口，两层都要查。

## 八、相关命令与文档

- 速查页：[网络命令速查](../network-commands#防火墙-速查)
- 现代防火墙替代：见 [nftables](./nftables)
- 发行版封装的防火墙：见 [firewalld 与 ufw](./firewalld-ufw)
- **完整防火墙原理与实战**：见 [iptables 防火墙指南](../../guide/linux-security-iptables)
- 网络整体原理：见 [Linux 网络专题](../../guide/linux-network)
