# nftables 命令详解：iptables 的现代继任者（list ruleset / add / table / chain）

> 本文是 [网络命令速查](../network-commands#防火墙-速查) 中 `nft`（nftables）的从 0 到 1 详解。
> 目标：看懂 nftables 的 table/chain 模型，会 list ruleset、加表加链加规则，知道它和 iptables 的关系。
> 环境依据：本沙箱 **nft 未安装**，语法与示例依据 nftables 官方 wiki（wiki.nftables.org，nftables 1.0.x 系列，2026 现状）。示例为官方文档标准写法，需 root。

## 一、命令是干什么的

`nft` 是 **nftables** 的命令行工具，是 iptables 的**现代替代品**（由同一批 Netfilter 内核开发者维护）。它解决了 iptables 的老毛病：表分散、规则重复、语法啰嗦。

与 iptables 的核心区别：

- **统一语法**：IPv4/IPv6/arp/bridge 不再分开写，用 `inet` 族一张表同时管 IPv4+IPv6；
- **没有预置链**：你自己建表、建链，并把链挂到内核钩子（hook）上；
- **规则集是一棵树**：`nft list ruleset` 一条命令看全部，配置可以写成声明式文件整体加载；
- **多数发行版已默认切到 nftables**：iptables 命令现在往往只是个指向 nft 的兼容壳。

> 类比：iptables 像分散在四本本子上的规定（filter/nat/mangle 各一本），nftables 把它们合并成一本结构清晰的规则集，还能整份导出/导入。

什么时候用：
- 新装的现代发行版（Debian 11+、RHEL 9+）默认防火墙就是 nftables；
- 想写一份干净、可版本管理的防火墙配置。

## 二、命令语法

```bash
nft [选项] 'nft命令'
```

- 整个 nft 语句用**单引号**包起来（里面有分号等 shell 元字符）；
- 常用子命令：`list ruleset`（看全部）、`add table`/`add chain`/`add rule`（加）、`delete`（删）、`flush`（清空）。

## 三、选项全表（据 nftables 官方 wiki）

### 1. 查看

| 命令 | 含义 |
|---|---|
| `nft list ruleset` | 打印**全部规则集**（最常用，等价 iptables -L 但更全） |
| `nft list tables` | 列出所有表 |
| `nft list table inet filter` | 看某张表 |

### 2. 增删改

| 命令 | 含义 |
|---|---|
| `nft add table inet filter` | 建表（`inet` 族同时管 IPv4/IPv6） |
| `nft add chain inet filter input { type filter hook input priority 0 ; policy accept ; }` | 建基础链并挂到 input 钩子 |
| `nft add rule inet filter input tcp dport 22 accept` | 往链里加规则 |
| `nft delete table inet filter` | 删整张表 |
| `nft flush ruleset` | 清空全部（危险） |
| `nft -f 配置文件` | 从文件加载整份规则集 |

### 3. 关键概念

| 概念 | 说明 |
|---|---|
| 族（family） | `ip`(IPv4)、`ip6`、`inet`(两者)、`netdev` |
| 钩子（hook） | `input`/`output`/`forward`/`prerouting`/`postrouting`，链挂哪就看哪类包 |
| 类型（type） | `filter`（过滤）、`nat`（地址转换）、`route` |
| 默认策略 | `policy accept` 或 `policy drop`，链尾没匹配上时的动作 |

## 四、由浅入深的典型示例

以下为官方 wiki 标准写法（示意），需 root。

### 示例 1：看现有规则集

```bash
sudo nft list ruleset
```

```text
table inet filter {
    chain input {
        type filter hook input priority filter; policy accept;
        tcp dport 22 accept
    }
}
```

> 整份规则集用缩进块打印出来，结构一目了然。

### 示例 2：从零建一张过滤表

```bash
sudo nft 'add table inet filter'
sudo nft 'add chain inet filter input { type filter hook input priority 0 ; policy drop ; }'
sudo nft 'add chain inet filter output { type filter hook output priority 0 ; policy accept ; }'
```

> 建表 → 建 input 链（挂到 input 钩子，默认 DROP）→ 建 output 链（默认 ACCEPT）。这是一台独立服务器的骨架。

### 示例 3：加放行规则

```bash
sudo nft 'add rule inet filter input ct state established,related accept'
sudo nft 'add rule inet filter input iif lo accept'
sudo nft 'add rule inet filter input tcp dport {22, 80, 443} accept'
```

> 注意 nft 的简洁：`tcp dport {22,80,443}` 一条规则开多个端口；`ct state established` 放行回程连接跟踪状态。

### 示例 4：声明式整体加载（推荐生产做法）

把配置写进 `/etc/nftables.conf`：

```text
#!/usr/sbin/nft -f
table inet filter {
    chain input {
        type filter hook input priority filter; policy drop;
        ct state established,related accept
        iif lo accept
        tcp dport { 22, 80, 443 } accept
    }
    chain output {
        type filter hook output priority filter; policy accept;
    }
}
```

然后：

```bash
sudo nft -f /etc/nftables.conf
```

> 这就是 nftables 的威力：一份文件描述整份防火墙，可进 Git 版本管理，`nft -f` 一次性原子加载。

### 示例 5：删表

```bash
sudo nft 'delete table inet filter'
```

> 整张表连同所有规则一起删掉。

### 示例 6：清空全部规则（危险）

```bash
sudo nft flush ruleset
```

> ⚠️ 清空所有规则集。远程操作前确认 SSH 不会因此断开。

### 示例 7：看表清单

```bash
sudo nft list tables
```

```text
table inet filter
```

### 示例 8：nftables 与 iptables 的关系

```bash
sudo iptables -L        # 在新发行版上，这其实走的是 nft 后端
```

> 现代发行版（如 Debian 11+、Ubuntu 22.04+、RHEL 9）提供 `iptables-nft` 兼容层：你敲老的 `iptables` 命令，底层翻译给 nftables。但**新配置建议直接写 nft 语法**，别长期依赖兼容层。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `sudo nft list ruleset` | 看全部规则（**最常用**） |
| `sudo nft list tables` | 看有哪些表 |
| `sudo nft 'add table inet filter'` | 建表 |
| `sudo nft 'add chain ... hook input ...'` | 建链 |
| `sudo nft 'add rule inet filter input tcp dport 22 accept'` | 加规则 |
| `sudo nft -f 配置文件` | 整体加载配置 |

## 六、RHEL 系与 Debian 系差异

- Debian 11+ / Ubuntu 22.04+ 默认 nftables；RHEL 8 提供 nftables，RHEL 9 默认改用 nftables 后端；
- RHEL 系上层仍多由 firewalld 封装（firewalld 后端就是 nftables）；Debian 常用 ufw 或直接手写 nft；
- 包名：Debian `nftables`，RHEL `nftables`。

## 七、新手易错点

1. **语句要包单引号**：nft 语法里有 `;`、`{}`，不包引号会被 shell 拆开报错。
2. **不加 hook 的链看不到包**：普通链（regular chain）必须被基础链跳转才生效，别建了链没挂 hook。
3. **远程先放行 SSH 再设 policy drop**：和 iptables 一样的经典锁门外事故。
4. **`inet` 族同时管 IPv4/IPv6**：别再像 iptables 那样写两遍。
5. **`flush ruleset` 是大招**：清空前留好后门。
6. **别混用两套**：同一台机器上 iptables-nft 和原生 nft 规则可能互相影响，选一套。

## 八、相关命令与文档

- 速查页：[网络命令速查](../network-commands#防火墙-速查)
- 老一代防火墙：见 [iptables](./iptables)
- 发行版封装：见 [firewalld 与 ufw](./firewalld-ufw)
- 完整防火墙原理：见 [iptables 防火墙指南](../../guide/linux-security-iptables)
- 网络整体原理：见 [Linux 网络专题](../../guide/linux-network)
