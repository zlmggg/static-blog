# firewalld 与 ufw 命令详解：发行版自带的防火墙管家

> 本文是 [网络命令速查](../network-commands#防火墙-速查) 中 `firewalld`（RHEL 系，`firewall-cmd`）与 `ufw`（Debian/Ubuntu 系）的从 0 到 1 详解。
> 目标：会用发行版自带的高层管家放行端口、查看状态、重载配置，不用直接写 iptables。
> 环境依据：本沙箱 **firewall-cmd / ufw 均未安装**，选项依据官方 man 锁定——firewalld（Debian bookworm `firewalld` 0.9.x，RHEL 8/9 同款）、ufw（Ubuntu 标配 `ufw` 0.36+）。示例需 root。

## 一、命令是干什么的

直接写 iptables/nftables 又繁琐又容易锁死自己。两大发行版家族各自做了一层**封装**：

- **firewalld**：RHEL/CentOS/Rocky/Fedora 默认防火墙，用 `firewall-cmd` 命令管理，核心概念是 **zone（区域）**；
- **ufw**（uncomplicated firewall）：Ubuntu/Debian 默认防火墙，主打"简单"，`ufw allow/deny/enable`。

它们底层都是 nftables/iptables，但你不用关心链和表，只要说"放行 80 端口"即可。

> 类比：iptables/nftables 是"手动挡"，每一步都要自己踩离合挂挡；firewalld/ufw 是"自动挡"，你只要说目的地（开哪个端口），它帮你把底层规则配好，还自动持久化。

什么时候用：
- RHEL 系服务器配对外开放端口；
- Ubuntu 服务器用 ufw 开防火墙。

## 二、命令语法

```bash
# RHEL 系：firewalld
sudo firewall-cmd [--permanent] [--zone=区域] --动作
# Debian/Ubuntu 系：ufw
sudo ufw 动作 [规则]
```

## 三、选项全表（据官方 man）

### 1. firewalld（firewall-cmd）

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `--state` | 看 firewalld 是否在运行 | 确认服务状态 |
| `--get-default-zone` | 看默认区域 | 知道规则默认加哪 |
| `--list-all` | 列出当前区域的所有规则 | 查配置（最常用） |
| `--add-port=端口/协议` | 临时放行端口 | 立刻生效 |
| `--permanent` | 规则**持久化**（重启不丢） | 配永久规则必加 |
| `--reload` | 重载，让 permanent 规则生效 | 加完永久规则后执行 |
| `--remove-port=端口/协议` | 删端口 | 关闭端口 |
| `--add-service=服务名` | 按服务名放行（如 http/https/ssh） | 比写端口更语义化 |
| `--add-rich-rule='...'` | 富规则（精细控制） | 只允许某 IP 访问 |

> 关键认知：**不加 `--permanent` 的规则重启就没；加了 `--permanent` 的要 `--reload` 才生效**。常用套路是 `--permanent --add-port=...` 然后 `--reload`。

### 2. ufw

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `ufw enable` | 启用防火墙 | 首次开启 |
| `ufw disable` | 关闭 | 临时关 |
| `ufw status` / `status verbose` | 看规则 | 查配置 |
| `ufw allow 端口/协议` | 放行 | `ufw allow 80/tcp` |
| `ufw deny 端口/协议` | 拒绝 | 封禁端口 |
| `ufw delete allow 端口` | 删除规则 | 撤销 |
| `ufw reload` | 重载 | 应用改动 |
| `ufw allow from IP to any port 端口` | 只允许某 IP | 精细控制 |

## 四、由浅入深的典型示例

以下命令均需 root（示意）。

### 示例 1：查看防火墙状态与已有规则

::: code-group

```bash [RHEL firewalld]
sudo firewall-cmd --state
sudo firewall-cmd --list-all
```

```bash [Debian ufw]
sudo ufw status verbose
```

:::

> `--list-all` / `status verbose` 会列出当前放行了哪些服务、端口、来源。

### 示例 2：放行 HTTP/HTTPS

::: code-group

```bash [RHEL firewalld]
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

```bash [Debian ufw]
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

:::

### 示例 3：放行一个端口

::: code-group

```bash [RHEL firewalld]
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --reload
```

```bash [Debian ufw]
sudo ufw allow 8080/tcp
```

:::

### 示例 4：先开 SSH 再启用防火墙（关键安全步骤）

::: code-group

```bash [RHEL firewalld]
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --reload
```

```bash [Debian ufw]
sudo ufw allow 22/tcp     # 先放行 SSH！
sudo ufw enable           # 再启用
```

:::

> ⚠️ 远程服务器上**一定要先放行 22 再 enable**，否则防火墙一开就连不回来了。

### 示例 5：只允许某 IP 访问某端口

::: code-group

```bash [RHEL firewalld]
sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="192.168.1.0/24" port protocol="tcp" port="3306" accept'
sudo firewall-cmd --reload
```

```bash [Debian ufw]
sudo ufw allow from 192.168.1.0/24 to any port 3306 proto tcp
```

:::

### 示例 6：删除一条规则

::: code-group

```bash [RHEL firewalld]
sudo firewall-cmd --permanent --remove-port=8080/tcp
sudo firewall-cmd --reload
```

```bash [Debian ufw]
sudo ufw delete allow 8080/tcp
```

:::

### 示例 7：重载配置

::: code-group

```bash [RHEL firewalld]
sudo firewall-cmd --reload
```

```bash [Debian ufw]
sudo ufw reload
```

:::

### 示例 8：封禁某 IP

::: code-group

```bash [RHEL firewalld]
sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="203.0.113.66" drop'
sudo firewall-cmd --reload
```

```bash [Debian ufw]
sudo ufw deny from 203.0.113.66
```

:::

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `firewall-cmd --list-all` / `ufw status` | 看规则 |
| `firewall-cmd --permanent --add-port=80/tcp && firewall-cmd --reload` | RHEL 永久放行 |
| `ufw allow 80/tcp` | Debian 放行 |
| `ufw allow 22/tcp && ufw enable` | Debian 开防火墙 |

## 六、RHEL 系与 Debian 系差异

| | RHEL/CentOS/Rocky | Ubuntu/Debian |
|---|---|---|
| 默认防火墙 | firewalld（`firewall-cmd`） | ufw |
| 配置单元 | zone（区域：public/trusted...） | 简单 allow/deny 列表 |
| 持久化 | `--permanent` + `--reload` | 写即生效，自动保存 |
| 后端 | nftables（新版） | iptables/nftables |

- 包名：RHEL `firewalld`（通常自带）；Debian `ufw`（Ubuntu 自带，Debian 需装）；
- 两者都是 nftables/iptables 的上层封装，底层规则另见 [iptables](./iptables) / [nftables](./nftables)。

## 七、新手易错点

1. **远程先放行 SSH 再 enable**：这是 ufw/firewalld 最常见的把自己锁门外事故。
2. **firewalld 的 permanent 要 reload**：只加 `--permanent` 不 reload，当前不生效；只加运行时不 permanent，重启就没。
3. **云安全组是另一层**：云上即使本地防火墙全开，云平台安全组仍可能挡端口，两层都要查。
4. **`ufw enable` 默认策略是拒绝入站**：开启后没 allow 的端口全关，记得放行你要的服务。
5. **别和裸 iptables 混用**：用了 firewalld/ufw 就别再手动 `iptables -A`，规则会互相覆盖。
6. **服务名比端口更省心**：firewalld 的 `--add-service=http` 自动知道是 80/tcp。

## 八、相关命令与文档

- 速查页：[网络命令速查](../network-commands#防火墙-速查)
- 底层规则：见 [iptables](./iptables) / [nftables](./nftables)
- 完整防火墙原理：见 [iptables 防火墙指南](../../guide/linux-security-iptables)
- 网络整体原理：见 [Linux 网络专题](../../guide/linux-network)
