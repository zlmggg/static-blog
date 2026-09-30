---
title: iptables 防火墙
description: netfilter/iptables 四表五链、规则语法、过滤与 NAT 实战、持久化，含 RHEL/Debian 差异
---

# iptables 防火墙

::: tip 本篇定位
理解 **netfilter/iptables 的四表五链与数据包流向**，能独立编写主机过滤规则、做 NAT（共享上网/端口映射），并让规则开机不丢。
iptables 是 Linux 网络安全的核心，Docker、K8s、云主机安全组的底层思路都和它一脉相承。
:::

## 一、防火墙概述

### 1.1 什么是防火墙

防火墙是部署在**可信网络与不可信网络之间**的一套访问控制机制：它允许"同意"的流量通过，把"不同意"的流量挡在门外。本质是一种**隔离**技术。

### 1.2 IDS、IPS、防火墙的区别

这几个概念常被混在一起，要分清：

| 技术 | 全称 | 部署方式 | 干什么 |
|---|---|---|---|
| **FW** | Firewall 防火墙 | 串联（在线） | 按规则做访问控制，放行/阻断连接 |
| **IDS** | Intrusion Detection System 入侵检测 | **旁路**（镜像流量） | 只检测、报警，**不阻断** |
| **IPS** | Intrusion Prevention System 入侵防御 | **串联**（在线） | 深度检测，发现攻击**立即阻断** |

- IDS 是"监控摄像头"，流量不经过它也不影响业务；
- IPS 是"安检门"，所有流量都要过，发现问题当场拦下；
- 现代设备通常把三者功能合一（NGFW，下一代防火墙）。

> 另有 **WW（Waterwall 防水墙）**，防的是内部敏感信息泄露（DLP），关注"内部流量的隐患"，与防火墙方向相反。

### 1.3 主机防火墙 vs 网络防火墙

| 维度 | 主机防火墙 | 网络防火墙 |
|---|---|---|
| 保护对象 | 单台主机 | 整个网段/网络集群 |
| 典型位置 | 云服务器、单机 | 网络出入口、子网边界 |
| 工具 | iptables/firewalld/ufw | 硬件防火墙、云安全组 |
| 定位 | 最后一道防线 | 第一道防线 |

### 1.4 Linux 防火墙技术栈（重点理清关系）

很多人被 iptables、firewalld、ufw、nftables 搞晕，记住下面这张演进图：

```text
内核框架：netfilter（Linux 2.4 起内置，真正干活的是它）
   │
   ├─ 用户态工具（老）：iptables ── 命令行写规则
   │
   ├─ 前端封装（让配置更简单）：
   │     ├─ firewalld   （RHEL/CentOS/Rocky 默认）
   │     └─ ufw         （Debian/Ubuntu 默认）
   │
   └─ 新一代内核/工具：nftables（nft 命令），iptables 的继任者
```

::: warning 关键关系
- **iptables、firewalld、ufw 本质上都在操作内核的 netfilter**；
- 在较新的发行版上，`iptables` 命令的后端其实已经是 nftables（称为 **iptables-nft / xtables-nft-multi**），可以用下面命令确认：
  ```bash
  iptables --version
  # iptables v1.8.10 (nf_tables)   ← nf_tables 表示底层是 nftables
  # iptables v1.8.7  (legacy)      ← legacy 才是老式线性实现
  ```
- **一台主机只启用一个防火墙工具**，同时开 ufw/firewalld/手写 iptables 会互相冲突。
:::

---

## 二、四表五链（核心）

### 2.1 netfilter 的五个钩子函数

netfilter 在内核网络栈的关键位置放了 **5 个"钩子函数"（hook）**，数据包经过时就会被检查。这 5 个钩子对应 iptables 的 **5 条内置链（chain）**：

| 链名 | 触发时机 |
|---|---|
| **PREROUTING** | 数据包刚进入网卡、**路由判断之前** |
| **INPUT** | 路由判断后，数据包**目标是本机** |
| **FORWARD** | 路由判断后，数据包**要转发给其他主机** |
| **OUTPUT** | **本机进程产生**、向外发送的数据包 |
| **POSTROUTING** | 数据包离开网卡**之前**（路由之后） |

### 2.2 数据包的三种流向

理解五链的关键，是分清一个包到底走哪条路径：

| 场景 | 经过的链 |
|---|---|
| **流入本机**（别人访问我） | PREROUTING → **INPUT** → 用户空间进程 |
| **流出本机**（我访问别人） | 用户空间进程 → **OUTPUT** → POSTROUTING |
| **本机转发**（我当路由器） | PREROUTING → **FORWARD** → POSTROUTING |

::: tip 一个判断技巧
数据包进入网卡先过 PREROUTING，然后内核做**路由判断**：
- 目标 IP 是本机 → 走 INPUT（"上车"）；
- 目标 IP 是别的机器 → 走 FORWARD（"转车"）；
本机回应的包从 OUTPUT 出发，最后过 POSTROUTING（"出站安检"）。
:::

### 2.3 五张表

规则按功能被组织到不同的**表（table）**里，共 5 张：

| 表名 | 作用 | 典型场景 |
|---|---|---|
| **filter** | 过滤：放行/丢弃（**最常用，默认表**） | 放行 22/80、禁止恶意 IP |
| **nat** | 网络地址转换（地址/端口转换） | 共享上网、端口映射 |
| **mangle** | 修改数据包标记、TTL、QoS 等 | 流量整形、打标记 |
| **raw** | 关闭连接追踪，提升性能 | 高并发、排查追踪异常 |
| **security** | 强制访问控制（MAC），由 SELinux 实现 | 高安全场景，很少直接用 |

**表的优先级（数据包依次经过的顺序，从高到低）：**

```text
security → raw → mangle → nat → filter
```

### 2.4 表与链的对应关系

不是每条链都包含所有表，对应关系如下：

| 表 | 可使用的链 |
|---|---|
| raw | PREROUTING、OUTPUT |
| mangle | PREROUTING、POSTROUTING、INPUT、OUTPUT、FORWARD |
| nat | PREROUTING、POSTROUTING、INPUT、OUTPUT |
| filter | **INPUT、FORWARD、OUTPUT** |

可用 `iptables -t raw -L` 等命令确认某张表包含哪些链。

### 2.5 完整流转过程

以数据包进入网卡为例：

1. 进入网卡，先过 **PREROUTING**（依次 raw → mangle → nat，可做 DNAT）；
2. 内核做路由判断：
   - 目标是本机 → 进入 **INPUT**（mangle → filter → security），交给应用进程；
   - 目标是其他主机且允许转发 → 进入 **FORWARD**（mangle → filter），再过 **POSTROUTING**（mangle → nat，可做 SNAT）；
3. 本机应用向外发包，先过 **OUTPUT**（raw → mangle → nat → filter），最后过 **POSTROUTING** 发出。

---

## 三、规则语法

### 3.1 命令的组成

一条完整的 iptables 命令由四部分组成：

```bash
iptables  [-t 表名]  子命令  链名  [匹配条件]  -j 动作
```

| 部分 | 说明 |
|---|---|
| `-t 表名` | 指定操作哪张表，省略时默认 **filter** |
| 子命令 | 对规则做什么：增/删/改/查（-A/-I/-D/-R/-L） |
| 链名 | 操作哪条链：INPUT/OUTPUT/FORWARD/PREROUTING/POSTROUTING |
| 匹配条件 | 筛选数据包：协议、源/目 IP、端口、接口等 |
| `-j 动作` | 匹配后执行什么：ACCEPT/DROP/REJECT 等 |

### 3.2 链与规则的子命令

| 子命令 | 全称 | 作用 |
|---|---|---|
| `-A` | --append | 在链**末尾追加**一条规则 |
| `-I` | --insert | 在链**开头（指定位置）插入**，`-I INPUT 3` 插到第 3 行 |
| `-D` | --delete | 删除规则（可按内容或规则编号） |
| `-R` | --replace | 替换指定编号的规则 |
| `-L` | --list | 列出链上的规则 |
| `-F` | --flush | **清空**链上所有规则 |
| `-Z` | --zero | 清零数据包/字节计数器 |
| `-N` | --new-chain | 新建自定义链 |
| `-X` | --delete-chain | 删除空的自定义链 |
| `-P` | --policy | 设置链的**默认策略**（ACCEPT/DROP） |

### 3.3 查看规则

```bash
iptables -L                    # 查看 filter 表所有规则（会做反解，可能很慢）
iptables -L INPUT              # 只看 INPUT 链
iptables -nL                   # -n 以数字显示 IP/端口，不反解（推荐，快）
iptables -nL -v                # -v 详细信息：pkts/bytes/in/out 接口
iptables -nL --line-numbers    # 显示规则编号（删除/插入时要用）
iptables -S                     # 以命令格式打印规则（便于学习和备份）
```

::: warning -n 和 -L 的顺序
合并写时必须是 `-nL`，写成 `-Ln` 会报错。
`-v` 比 `-nL` 多出这些字段：
- `pkts`：命中的数据包数量；`bytes`：命中的字节数；
- `in`：流入接口；`out`：流出接口。
:::

### 3.4 基本匹配条件

| 选项 | 作用 | 示例 |
|---|---|---|
| `-s` | 源地址（IP/网段） | `-s 192.168.1.0/24` |
| `-d` | 目标地址 | `-d 10.0.0.5` |
| `-p` | 协议（tcp/udp/icmp，可查 /etc/protocols） | `-p tcp` |
| `-i` | 流入接口（仅 PREROUTING/INPUT/FORWARD） | `-i eth0` |
| `-o` | 流出接口（仅 OUTPUT/FORWARD/POSTROUTING） | `-o eth0` |

- 多个匹配条件写在一条规则里，默认是 **"与"**关系，必须同时满足；
- 条件前加 `!` 表示**取反**，如 `! -s 10.0.0.12` 表示"除了 10.0.0.12 之外"。

### 3.5 隐式扩展（tcp/udp/icmp）

用 `-p` 指定协议后，可直接使用该协议的扩展，叫**隐式扩展**（不用加 -m）：

```bash
# TCP：源端口/目标端口，可写范围
-p tcp --dport 22            # 目标端口 22
-p tcp --sport 1024:65535    # 源端口范围
-p tcp --syn                 # 只匹配 SYN（第一次握手），简写 --tcp-flags SYN,ACK,FIN,RST SYN

# UDP
-p udp --dport 53            # DNS
-p udp --sport 1024:65535

# ICMP：--icmp-type，8=请求(echo-request)，0=应答(echo-reply)
-p icmp --icmp-type 8        # 匹配 ping 请求
```

### 3.6 显式扩展（-m）

需要更复杂的匹配时，用 `-m 模块名` 加载，叫**显式扩展**：

| 模块 | 作用 | 典型用法 |
|---|---|---|
| **multiport** | 一次匹配多个离散端口（最多 15 个） | `-m multiport --dports 22,80,443` |
| **iprange** | 匹配连续 IP 范围（非整网段） | `-m iprange --src-range 10.0.0.13-10.0.0.99` |
| **mac** | 匹配源 MAC 地址 | `-m mac --mac-source 00:0c:29:b1:f4:54` |
| **string** | 匹配应用层内容中的字符串（性能差） | `-m string --string "baidu" --algo kmp` |
| **time** | 按时间段匹配（**默认用 UTC**） | `-m time --timestart 01:00 --timestop 04:00` |
| **connlimit** | 限制单 IP 的并发连接数（防 DoS） | `-m connlimit --connlimit-above 2` |
| **limit** | 按速率限速（令牌桶） | `-m limit --limit 20/minute --limit-burst 10` |
| **state** | 按连接追踪状态匹配 | `-m state --state ESTABLISHED,RELATED` |

**state（连接追踪）的状态：**

| 状态 | 含义 |
|---|---|
| NEW | 新连接的第一个包（如三次握手的 SYN） |
| ESTABLISHED | 连接已建立后的通信状态 |
| RELATED | 与已有连接相关的新连接（如 FTP 数据连接、ICMP 报错） |
| INVALID | 无效连接（flag 标记不正确） |
| UNTRACKED | 未做追踪（raw 表关闭追踪的包） |

::: details state 模块排障：nf_conntrack table full
连接追踪要消耗内存，能追踪的连接数有上限，超限会丢包并报错：
```bash
cat /proc/sys/net/netfilter/nf_conntrack_max     # 最大追踪连接数
cat /proc/sys/net/netfilter/nf_conntrack_count   # 当前已追踪数
dmesg | grep "nf_conntrack: table full"          # 超限时的报错
```
解决：调大上限、缩短超时时间（见 `nf_conntrack_*_timeout`），或对无需追踪的流量在 raw 表 `-j NOTRACK`。
:::

### 3.7 规则的匹配顺序（非常重要）

::: danger 规则自上而下、命中即停
- 规则按**从上到下**顺序检查，一旦某条规则命中（且是 DROP/ACCEPT 这类终止动作），**就不再往下匹配**；
- 所有规则都没命中时，才走链的**默认策略（policy）**。
:::

因此编写顺序有讲究：

1. **范围小、需要精确匹配的放前面**；
2. **范围大、负责兜底的放后面**；
3. 从效率看，**命中频率高的规则尽量靠前**（规则无交集时顺序不影响结果，但影响性能）；
4. 默认策略（-P）作为最后兜底。

---

## 四、处理动作 target

### 4.1 基础动作

| 动作 | 说明 |
|---|---|
| **ACCEPT** | 允许通过，命中后进入下一个处理环节 |
| **DROP** | **静默丢弃**，不做任何回应，发送方收不到任何回执 |
| **REJECT** | 拒绝，并向发送方**返回错误响应**（默认 ICMP port-unreachable） |
| **RETURN** | 在自定义链中返回主链，继续往下匹配 |
| **LOG** | 把命中的包记录到系统日志（**记录后继续往下匹配**） |

### 4.2 DROP 和 REJECT 怎么选

```bash
iptables -A INPUT -s 10.0.0.12 -j DROP      # 对方收不到任何回应
iptables -A INPUT -s 10.0.0.14 -j REJECT    # 对方收到"目标端口不可达"
```

- **DROP**：对方一直等超时（如 ping 一直卡住），**不暴露主机存在，安全性稍高**，是生产常用；
- **REJECT**：对方立刻知道被拒，便于排查和减少等待，但会暴露主机；
- 本机回环、信任内网有时用 REJECT 更友好。

### 4.3 LOG 记录日志

```bash
iptables -A INPUT -s 10.0.0.12 -j LOG --log-prefix "test-IN:" --log-level warn
```

- `--log-prefix`：日志前缀（最多 29 字符），用于在日志里区分；
- `--log-level`：级别（debug/info/notice/warn/error 等）；
- 日志位置：`/var/log/syslog`（Debian）或 `/var/log/messages`（RHEL）。

::: warning LOG 不会阻断
LOG 只记录、不终止匹配，包会继续往下走。所以通常 LOG 后面再跟一条 DROP/REJECT。
:::

### 4.4 NAT 动作

| 动作 | 作用 | 所在链 |
|---|---|---|
| **SNAT** | 源地址转换（固定出口 IP 共享上网） | POSTROUTING |
| **MASQUERADE** | 源地址**动态**转换（自动获取出口 IP） | POSTROUTING |
| **DNAT** | 目标地址转换（端口映射/发布内网服务） | PREROUTING |
| **REDIRECT** | 重定向到本机端口（透明代理/端口跳转） | PREROUTING/OUTPUT |

---

## 五、过滤实战

### 5.1 准备：关闭其他防火墙服务

手写 iptables 前，先关掉发行版自带的前端，避免冲突：

```bash
# Debian/Ubuntu：关闭 ufw
systemctl disable --now ufw

# RHEL/Rocky：关闭 firewalld
systemctl disable --now firewalld

# 确认（iptables 操作需要 root）
iptables -V
```

> Ubuntu **server** 默认可能没装 iptables，需 `apt install iptables`；桌面版默认已装。

### 5.2 白名单思路（推荐）

主机防火墙推荐**默认拒绝、按需放行**（白名单），比默认放行再拉黑更安全。

::: danger 务必先放行管理通道，再改默认策略
设置默认 DROP 前，**一定先放行 SSH 和回环口**，否则当前 SSH 会话会立刻断开、再也连不上（"自杀"）。
:::

### 5.3 完整主机过滤脚本

下面是一套可直接使用的规则（假设 SSH 端口为默认 22，若改过端口请替换）：

```bash
#!/bin/bash
IPT="iptables"

# 1) 先清空现有规则
$IPT -F
$IPT -X
$IPT -Z

# 2) 放行回环口（本机进程间通信）
$IPT -A INPUT -i lo -j ACCEPT
$IPT -A OUTPUT -o lo -j ACCEPT

# 3) 放行已建立/相关连接（让出站连接的回应包能回来，一条规则覆盖大量流量）
$IPT -A INPUT  -m state --state ESTABLISHED,RELATED -j ACCEPT
$IPT -A OUTPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# 4) 放行 SSH（生产建议改高端口 + 限制来源 IP）
$IPT -A INPUT -p tcp --dport 22 -m state --state NEW -j ACCEPT
# 更严格：只允许某网段连 SSH
# $IPT -A INPUT -p tcp --dport 22 -s 192.168.1.0/24 -m state --state NEW -j ACCEPT

# 5) 放行 HTTP/HTTPS（多端口一条规则）
$IPT -A INPUT -p tcp -m multiport --dports 80,443 -m state --state NEW -j ACCEPT

# 6) 放行 ping（可选；不想被 ping 就删掉这两条）
$IPT -A INPUT  -p icmp --icmp-type echo-request -j ACCEPT
$IPT -A OUTPUT -p icmp -j ACCEPT

# 7) 限制单 IP 对 80 的并发连接数（防简单 CC）
$IPT -A INPUT -p tcp --dport 80 -m connlimit --connlimit-above 20 -j REJECT

# 8) 拉黑某个恶意 IP（黑名单补充，放在默认 DROP 前）
# $IPT -A INPUT -s 1.2.3.4 -j DROP

# 9) 最后设置默认策略：未匹配的全部丢弃
$IPT -P INPUT DROP
$IPT -P FORWARD DROP
$IPT -P OUTPUT ACCEPT        # 出站一般放行，方便本机主动访问
```

### 5.4 验证

```bash
iptables -nL --line-numbers   # 检查规则顺序
# 从另一台机器测试 SSH、HTTP、ping 是否符合预期
```

::: tip Docker 会自动管理 iptables
如果机器上跑着 Docker，Docker 会自动向 nat/filter 表插入 DOCKER 相关链和规则（端口映射、容器互通都靠它）。
**不要手动清空或改 DOCKER 链**，否则容器网络会异常；容器端口的访问控制建议在应用层或 `DOCKER-USER` 链里做。
:::

---

## 六、NAT 实战

### 6.1 开启转发开关

做 NAT/路由器前，必须先打开内核的 **ip_forward**（默认关闭）：

```bash
# 临时开启（重启失效）
sysctl -w net.ipv4.ip_forward=1

# 永久开启
echo 'net.ipv4.ip_forward = 1' > /etc/sysctl.d/99-ipforward.conf
sysctl -p /etc/sysctl.d/99-ipforward.conf

# 验证
cat /proc/sys/net/ipv4/ip_forward    # 输出 1 即开启
```

::: warning ip_forward 和 FORWARD 链缺一不可
- `ip_forward=1` 是"是否允许转发"的**总开关**；
- FORWARD 链规则是"哪些转发包放行"的**过滤器**；
- 只有开关打开 **且** FORWARD 放行，数据包才能被转发。
:::

### 6.2 SNAT：内网共享固定公网 IP 上网

场景：内网 `10.0.0.0/24` 的机器，通过本机出口（公网 IP `192.168.8.13`）上网。

```bash
iptables -t nat -A POSTROUTING -s 10.0.0.0/24 ! -d 10.0.0.0/24 \
  -j SNAT --to-source 192.168.8.13
```

- 源地址是内网、目标不是内网（即出外网）的包，把源 IP 改写成出口 IP；
- `--to-source` 可写多个 IP 做地址池，也可加端口范围。

### 6.3 MASQUERADE：动态出口 IP（拨号/多 IP）

如果出口 IP 不固定（家庭宽带、4G/5G、DHCP），用 SNAT 写死 IP 会失效，改用 MASQUERADE，它会**自动读取出口网卡当前的 IP**：

```bash
iptables -t nat -A POSTROUTING -s 10.0.0.0/24 ! -d 10.0.0.0/24 -j MASQUERADE
# 或指定出口网卡
iptables -t nat -A POSTROUTING -s 10.0.0.0/24 -o eth0 -j MASQUERADE
```

> MASQUERADE 本质是特殊的动态 SNAT，会多一点查询开销，但更灵活、免维护。

### 6.4 DNAT：发布内网服务（端口映射）

场景：把访问本机 80 端口的流量，转发给内网服务器 `10.0.0.14` 的 80：

```bash
# 目标是本机、访问 80 的包，目标地址改写成内网服务器
iptables -t nat -A PREROUTING -d <本机对外IP> -p tcp --dport 80 \
  -j DNAT --to-destination 10.0.0.14:80

# 映射到不同端口也可以（外部 8080 → 内网 80）
iptables -t nat -A PREROUTING -d <本机对外IP> -p tcp --dport 8080 \
  -j DNAT --to-destination 10.0.0.14:80
```

同时要确保 FORWARD 链放行这些转发流量（上面白名单脚本里默认 DROP，需要加放行规则）：

```bash
iptables -A FORWARD -d 10.0.0.14 -p tcp --dport 80 -j ACCEPT
iptables -A FORWARD -s 10.0.0.14 -m state --state ESTABLISHED,RELATED -j ACCEPT
```

::: warning DNAT 不做负载均衡
一条 DNAT 规则只能重定向到一台后端，无法实现负载均衡；多目标需要多条规则，或用 LVS/IPVS、Nginx 等。
:::

### 6.5 REDIRECT：重定向到本机端口

把访问某端口的流量重定向到**本机另一个端口**，常用于透明代理（如 Squid）或服务迁移：

```bash
# 把本机 80 流量重定向到 8080
iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-ports 8080
# 本机自己产生的流量要在 OUTPUT 链处理
iptables -t nat -A OUTPUT -p tcp --dport 80 -j REDIRECT --to-ports 8080
```

> REDIRECT 是 DNAT 的特例，目标 IP 会被改成网关本机（127.0.0.1 或网卡 IP），只能转到本机，转其他主机要用 DNAT。

---

## 七、保存与持久化

::: warning 用 iptables 命令写的规则是临时的
规则的生命周期就是**内核运行期间**，一旦**重启系统（或重启相关服务），规则全部丢失**。必须手动持久化。
:::

### 7.1 通用：iptables-save / iptables-restore

```bash
iptables-save > /root/iptables.rules          # 导出当前规则
iptables-restore < /root/iptables.rules       # 从文件恢复
cat /root/iptables.rules                       # 查看保存格式（*filter ... COMMIT）
```

### 7.2 RHEL/Rocky：iptables-services

```bash
# 安装（在 EPEL/Base 源）
yum install -y iptables-services

# 规则文件位置
#   IPv4：/etc/sysconfig/iptables    IPv6：/etc/sysconfig/ip6tables
iptables-save > /etc/sysconfig/iptables

# 启用开机加载
systemctl enable --now iptables
systemctl restart iptables
```

### 7.3 Debian/Ubuntu：iptables-persistent

```bash
# 安装（会询问是否保存当前规则）
apt install -y iptables-persistent

# 规则文件位置
#   IPv4：/etc/iptables/rules.v4    IPv6：/etc/iptables/rules.v6
netfilter-persistent save        # 保存当前规则
netfilter-persistent reload      # 重新加载
systemctl enable netfilter-persistent
```

::: warning iptables 和 firewalld 不要同时启用
两个服务都管 netfilter 规则，同时开会互相覆盖、造成混乱。二选一。
:::

---

## 八、自定义链（了解）

当规则很多时，可以把一类规则放进**自定义链**分组管理、复用。

```bash
# 1. 创建自定义链
iptables -N WEB_CHAIN

# 2. 往自定义链里加规则
iptables -A WEB_CHAIN -p tcp -m multiport --dports 80,443 -j ACCEPT

# 3. 在主链里"跳转"到自定义链（关键：不关联就不会生效）
iptables -I INPUT 1 -j WEB_CHAIN

# 4. 清理：先删主链里的跳转，再清空自定义链，最后删除
iptables -D INPUT -j WEB_CHAIN
iptables -F WEB_CHAIN
iptables -X WEB_CHAIN          # 链必须为空、且无引用才能删
```

> 数据包在自定义链里若没匹配到终止动作，会通过 `RETURN` 返回主链继续匹配。

---

## 九、firewalld / ufw / nftables 对比

### 9.1 firewalld（RHEL 系）

firewalld 用 **zone（区域）** 管理规则，不同网卡/场景绑定不同 zone，修改可即时生效、不中断连接。

常用 zone：`public`（默认，仅放行指定服务）、`trusted`（全放行）、`drop`（全丢弃）、`block`（拒绝并回应）、`dmz`、`home/work/internal`。

```bash
firewall-cmd --state                          # 运行状态
firewall-cmd --get-default-zone               # 默认 zone
firewall-cmd --get-zones                      # 所有 zone
firewall-cmd --list-all                       # 默认 zone 详情
firewall-cmd --add-service=http               # 临时放行 http
firewall-cmd --permanent --add-service=http   # 永久放行（需 reload）
firewall-cmd --reload                         # 重新加载永久规则
firewall-cmd --add-rich-rule='rule family="ipv4" source address="1.2.3.4" drop'  # 富规则
```

### 9.2 ufw（Debian 系）

ufw 语法最简单，适合单机快速配置：

```bash
ufw status verbose
ufw default deny incoming
ufw allow 22/tcp
ufw allow 80,443/tcp
ufw enable
ufw delete allow 80/tcp
```

### 9.3 nftables（新一代）

nftables 用 `nft` 命令，相比 iptables 的优势：

1. **规则用哈希表/集合匹配**，不再线性遍历，规则多时性能高；
2. 一个命令可批量下发规则，减少内核调用；
3. 统一管理 IPv4/IPv6、arp、bridge，语法更简洁；
4. 与 iptables 兼容（iptables-nft 后端）。

```bash
nft list ruleset                       # 查看所有规则
nft add table inet myfw                # 建表（inet 同时管 v4/v6）
nft 'add chain inet myfw input { type filter hook input priority 0; policy drop; }'
nft add rule inet myfw input tcp dport 22 accept
```

### 9.4 选型建议

| 场景 | 建议 |
|---|---|
| 个人/云主机快速配置 | ufw（Debian）或 firewalld（RHEL），够用 |
| 需要精细控制、写脚本、理解底层 | iptables（规则即文档） |
| 规则量极大、追求性能、面向未来 | nftables（nft） |
| 容器环境 | 交给 Docker 管理，只在 DOCKER-USER 做补充 |

---

## 面试自测

1. 什么是 iptables？netfilter 和 iptables 是什么关系？
2. 说清四表五链，以及数据包流入、流出、转发分别经过哪些链。
3. filter/nat/raw/mangle/security 各有什么作用？表的优先级？
4. DROP 和 REJECT 的区别？生产一般用哪个？
5. 如何让内网机器通过本机共享上网？（ip_forward + SNAT/MASQUERADE）
6. 如何把内网服务发布到公网？（DNAT，FORWARD 放行）
7. 为什么 iptables 规则重启会丢？RHEL 和 Debian 分别怎么持久化？
8. state 模块 NEW/ESTABLISHED/RELATED 分别是什么？`nf_conntrack: table full` 怎么处理？
9. 设置默认 DROP 前为什么要先放行 SSH？（防"自杀"）
10. iptables 和 nftables 的区别？

## 相关速查

- [网络命令速查](/reference/network-commands)
- [Linux 命令速查](/reference/linux-commands)
