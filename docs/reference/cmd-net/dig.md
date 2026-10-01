# dig 命令详解：查 DNS 记录（附 nslookup、host）

> 本文是 [网络命令速查](../network-commands#dns-查询) 中 `dig` 的从 0 到 1 详解，并附带 `nslookup`、`host` 对照。
> 目标：会用 `+short`/`+trace`/`-x`/`@server` 查 A/MX/NS/TXT 等各类记录，定位"域名解析到哪了、权威是谁"。
> 环境依据：本沙箱**dig/nslookup/host 均未安装**，以下选项依据 ISC BIND 9 自带的 dig 官方 man（Arch Linux man-pages 收录的 dig(1)，BIND 9.18/9.20 LTS 系列，2026 现状）。示例输出为典型形态示意，非本机实跑。

## 一、命令是干什么的

`dig`（domain information groper）是 BIND 套件里最强大的 **DNS 查询工具**。它直接向 DNS 服务器发查询，把域名对应的各种记录完整显示出来。

它能查的记录类型：

- **A**：域名 → IPv4；
- **AAAA**：域名 → IPv6；
- **MX**：邮件服务器；
- **NS**：这个域名的权威 DNS 是谁；
- **TXT**：文本记录（SPF、域名验证等）；
- **CNAME**：别名指向；
- **SOA**：区域起始记录（主 DNS、管理员邮箱、序列号）；
- **PTR**：反向解析（IP → 域名）。

> 类比：浏览器输入域名后，背后要先问 DNS"这个域名对应哪个 IP"。`dig` 就是让你亲自去问这个问题，而且能问得非常细——指定问哪个 DNS、看完整往返、从根域名开始一路追。

什么时候用：
- 配了 DNS 不生效？`dig @8.8.8.8 域名` 直接问公共 DNS，对比本机解析；
- 邮件发不出，查 MX 记录配对不对；
- 网站证书/域名验证，查 TXT；
- `+trace` 看域名到底是怎么一步步解析出来的。

## 二、命令语法

```bash
dig [@DNS服务器] 域名 [记录类型] [+查询选项]
dig -x 目标IP                  # 反向解析
nslookup 域名 [DNS服务器]
host 域名
```

- `@服务器`：指定向哪个 DNS 问（如 `@8.8.8.8`），不写就用 `/etc/resolv.conf` 里的；
- `域名`：要查的名字；
- `记录类型`：A/AAAA/MX/NS/TXT/SOA/CNAME，不写默认 A；
- `+选项`：以加号开头控制输出详略（如 `+short`）。

最简用法：

```bash
dig example.com
```

## 三、选项全表（据 BIND dig 官方 man）

### 1. 常用查询位置参数

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `@服务器` | 指定查询的 DNS 服务器 | 对比公共 DNS：`dig @8.8.8.8` |
| `-t 类型` | 指定记录类型（可省略，直接写类型） | `dig -t MX example.com` |
| `-x 地址` | **反向解析**（IP → 域名，PTR） | `dig -x 8.8.8.8` |
| `-p 端口` | 查询非标准 DNS 端口 | 测改过 53 端口的自建 DNS |
| `-4` / `-6` | 强制只用 IPv4 / IPv6 传输 | 排协议族 |

### 2. `+` 开头的输出选项

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `+short` | **只给简洁答案**（一行 IP） | 脚本/快速看结果（极常用） |
| `+trace` | 从**根域名**开始逐级追踪解析 | 看解析全过程、定位 delegation 问题 |
| `+noall +answer` | 只打印 answer 段 | 干净取结果 |
| `+nocmd` / `+nocomments` / `+nostats` | 去掉版本/注释/统计行 | 精简输出 |
| `+tcp`（`+vc`） | 用 **TCP** 查询（默认 UDP） | 区域传输/大响应时 |
| `+tries=N` | 重试次数（默认 3） | 超时环境调整 |
| `+time=N` | 每次查询超时秒数 | 网络慢时调大 |

### 3. nslookup / host 对照

| 工具 | 特点 | 用法 |
|---|---|---|
| `nslookup` | 老式交互/非交互 DNS 查询，几乎所有系统都带 | `nslookup example.com 8.8.8.8` |
| `host` | 最简洁的单行输出 | `host -t MX example.com` |
| `dig` | 信息最全、最适合排障（**推荐**） | 本文主角 |

## 四、由浅入深的典型示例

以下为据官方 man / 典型输出形态（示意），非本机实跑。

### 示例 1：查 A 记录（默认）

```bash
dig example.com
```

```text
; <<>> dig 9.18 <<>> example.com
;; flags: qr rd ra; ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 0
;; QUESTION SECTION:
;example.com.       IN  A
;; ANSWER SECTION:
example.com.    86400  IN  A  93.184.216.34
;; Query time: 23 msec
;; SERVER: 8.8.8.8#53(8.8.8.8)
```

重点看 `ANSWER SECTION`：`example.com. 86400 IN A 93.184.216.34`——A 记录是 `93.184.216.34`，TTL 86400 秒。

### 示例 2：只要简洁结果（最常用）

```bash
dig +short example.com
```

```text
93.184.216.34
```

> 只要 IP，不给一堆废话。写脚本/记结果首选。

### 示例 3：指定 DNS 服务器查询

```bash
dig @8.8.8.8 example.com +short
```

> 不问本机默认 DNS，直接问 Google 公共 DNS。"我这解析不对，是本机 DNS 问题还是权威记录问题"——用它对比。

### 示例 4：查 MX 邮件记录

```bash
dig example.com MX +short
```

```text
10 mail.example.com.
```

> 数字 `10` 是优先级，越小越优先。邮件服务器出问题先查这个。

### 示例 5：反向解析

```bash
dig -x 8.8.8.8 +short
```

```text
dns.google.
```

> `-x` 自动把 IP 倒过来查 PTR，得到 `8.8.8.8` 的名字是 `dns.google`。

### 示例 6：查 NS / TXT / SOA

```bash
dig example.com NS +short
dig example.com TXT +short
dig example.com SOA +short
```

> NS 告诉你这个域名由哪台 DNS 管；TXT 常用于 SPF、域名所有权验证（如加云、CDN 校验）；SOA 里有主 DNS、管理员邮箱、序列号。

### 示例 7：从根开始追踪完整解析

```bash
dig +trace example.com
```

> 不再代你转发，而是自己从根 `.` → 顶级域 `.com` → 权威 DNS 逐级问下去，每一级都打印出来。解析"中途在哪一跳出问题"时用它。

### 示例 8：用 nslookup / host 快速查

```bash
nslookup example.com 8.8.8.8
host -t AAAA example.com
```

> `nslookup` 在最精简的环境（容器、急救盘）里也常带；`host` 输出单行极简。功能上都被 `dig` 覆盖。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `dig 域名 +short` | 只拿 A 记录 IP（**最常用**） |
| `dig @8.8.8.8 域名 +short` | 指定公共 DNS 对比解析 |
| `dig 域名 MX/NS/TXT +short` | 查指定记录类型 |
| `dig -x IP +short` | 反向解析 |
| `dig +trace 域名` | 从根逐级追踪 |
| `nslookup 域名` | 老派快速查 |

## 六、RHEL 系与 Debian 系差异

- 包名：`dig` 在 Debian 属 `dnsutils`，在 RHEL/CentOS/Rocky 属 `bind-utils`；`nslookup`/`host` 同包；
- 两系选项完全一致（都是 ISC BIND 出品）；
- 默认不装，需 `apt install dnsutils` 或 `dnf install bind-utils`；
- 自建 DNS 服务器（BIND）的完整配置另见 [DNS 服务专题](../../guide/services-dns)。

## 七、新手易错点

1. **改了 DNS 不生效先分清是谁的问题**：`dig @权威DNS` 直接问权威，和 `dig @本机resolv.conf` 对比——本机有缓存就会看到旧值。
2. **TTL 没到就别急着改**：记录有缓存时间，刚改完全世界不会立刻看到，看 TTL 倒计时。
3. **`+short` 最省心**：裸 `dig` 输出很长，日常加 `+short`。
4. **A 和 AAAA 分开查**：IPv4 用 A、IPv6 用 AAAA，别混。
5. **反向解析 `-x` 别手动倒 IP**：直接 `-x 8.8.8.8`，它自动拼成 `8.8.8.8.in-addr.arpa`。
6. **公共 DNS 结果 ≠ 你用户的结果**：各地 DNS 缓存、智能解析可能不同，要用对端所在区域的 DNS 查。

## 八、相关命令与文档

- 速查页：[网络命令速查](../network-commands#dns-查询)
- 自建 DNS / BIND：见 [DNS 服务专题](../../guide/services-dns)
- 基础连通性：见 [ping](./ping)
- 路径排障：见 [traceroute 与 mtr](./traceroute-mtr)
- 网络整体原理：见 [Linux 网络专题](../../guide/linux-network)
