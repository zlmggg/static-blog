# tcpdump 命令详解：命令行抓包（附 tshark）

> 本文是 [网络命令速查](../network-commands#抓包) 中 `tcpdump` 的从 0 到 1 详解，并附带 `tshark`（Wireshark 命令行版）对照。
> 目标：掌握 `-i/-nn/-w/-r/-A/-c` 和过滤表达式 `port`/`host`/`src`/`dst`，能抓到你想看的那几个包并存盘分析。
> 环境依据：本沙箱 **tcpdump/tshark 均未安装**，以下选项与过滤语法依据 tcpdump 官方 man（tcpdump.org 官方手册，1.x/4.x 系列，2026 现状）。示例输出为典型形态示意，非本机实跑。抓包需 root。

## 一、命令是干什么的

`tcpdump` 从网卡上**实时抓取经过的网络数据包**，并按你给的过滤条件筛选、打印或存盘。它是网络问题的"显微镜"——当 `ping`/`ss`/`curl` 都不够用时，抓包看真相。

它能回答：
- 我的请求到底发出去没有？对方回了什么？
- 三次握手走完了吗？卡在哪一步？
- 某个端口有没有数据进来？是谁发的？
- HTTP 明文里到底传了什么？

> 类比：其它命令像是"看电表度数"，tcpdump 是"在网线旁边装个摄像头，把经过的每个包裹都拍下来"。你还能设置只拍你关心的包裹（只拍某个人、某个端口）。

什么时候用：
- 应用报"连接超时"但说不清，抓包看是 SYN 没出去还是没回 ACK；
- 抓 HTTP/Redis/MySQL 等明文协议的请求内容；
- 存成 `.pcap` 拿到 Wireshark 里图形化慢慢看。

## 二、命令语法

```bash
tcpdump [选项]... [过滤表达式]
sudo tcpdump -i eth0 -nn port 80
```

- `[选项]`：选网卡、显示格式、存盘/读盘；
- `[过滤表达式]`：用布尔条件挑包（`host`、`port`、`src`、`dst`、`tcp`、`udp`，可用 `and/or/not` 组合）；
- 不按 Ctrl+C 会一直抓，加 `-c N` 抓够 N 个自动停。

## 三、选项全表（据 tcpdump 官方 man）

### 1. 选网卡与停止条件

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-i 网卡` | 指定在哪个网卡抓包（`any` 抓所有） | `sudo tcpdump -i eth0`；不写会自动选第一个 |
| `-c 数量` | 抓够 N 个包就**自动退出** | 脚本里避免一直抓 |
| `-w 文件` | 把原始包**存成 .pcap 文件** | 留着给 Wireshark 分析 |
| `-r 文件` | **读取**已存的 pcap 文件（不需网卡权限） | 事后分析 |
| `-C 大小` | 输出文件到多大就滚动切分 | 大流量长期抓包 |
| `-G 秒` | 每 N 秒滚动一个文件 | 按时间切片 |

### 2. 显示格式

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-n` | 不反解主机名 | 快、干净 |
| `-nn` | 主机名**和端口名都不反解** | 更快，**强烈建议加** |
| `-A` | 以 **ASCII** 打印包内容 | 看 HTTP 明文 |
| `-x` / `-X` | 同时打印**十六进制+ASCII** | 看二进制内容 |
| `-v` / `-vv` / `-vvv` | 越打越详细（TTL、标志、选项） | 深入分析 |
| `-tttt` | 每行带完整日期时间戳 | 排时间线 |
| `-s 长度` | 每个包抓多少字节（默认截断） | `-s 0` 抓完整包 |

### 3. 过滤表达式（pcap-filter）

| 表达式 | 含义 |
|---|---|
| `host 1.2.3.4` | 源或目的是该 IP 的包 |
| `src host X` / `dst host X` | 按源/目的 IP |
| `port 80` | 源或目的端口是 80 |
| `src port 80` / `dst port 80` | 按源/目的端口 |
| `tcp` / `udp` / `icmp` | 只抓某协议 |
| `net 10.0.0.0/8` | 某个网段 |
| `and` / `or` / `not` | 组合条件（`'tcp port 80 and host 1.2.3.4'`） |
| `tcp[tcpflags] & tcp-syn != 0` | 抓带 SYN 标志的包（高级） |

> 表达式建议用单引号包起来，避免 shell 把 `&`、`()` 当成 shell 元字符拆开解释。

## 四、由浅入深的典型示例

以下为据官方 man 的典型输出形态（示意），非本机实跑，抓包需 root。

### 示例 1：抓某网卡所有包（先看个热闹）

```bash
sudo tcpdump -i eth0 -nn
```

```text
15:30:01.123456 IP 9.103.17.236.51810 > 93.184.216.34.443: Flags [S], seq 1, win 64240
15:30:01.234567 IP 93.184.216.34.443 > 9.103.17.236.51810: Flags [S.], seq 2, ack 1, win 65535
```

> `-nn` 不反解。`Flags [S]` 是 SYN、`[S.]` 是 SYN+ACK、`[P.]` 是 PSH+ACK——这就是 TCP 三次握手的前两步。

### 示例 2：只抓 80 端口的 HTTP 流量

```bash
sudo tcpdump -i eth0 -nn port 80
```

> 过滤掉无关包，只留 80 端口。

### 示例 3：抓与某主机的所有通信

```bash
sudo tcpdump -i eth0 -nn host 93.184.216.34
```

> 只看和这台服务器之间的包。

### 示例 4：抓包并存盘（.pcap）

```bash
sudo tcpdump -i eth0 -nn -w /tmp/cap.pcap port 80
```

> `-w` 写原始包到文件，不打印。文件可拖进 Wireshark 图形化分析。

### 示例 5：事后读 pcap 文件

```bash
tcpdump -nn -r /tmp/cap.pcap
```

> `-r` 读盘，不需要 root，适合把文件拷回来慢慢看。

### 示例 6：看 HTTP 明文内容（ASCII）

```bash
sudo tcpdump -i eth0 -nn -A port 80
```

> `-A` 把包内容按 ASCII 打出来，能直接看到 HTTP 请求行、Header（明文协议才看得到；HTTPS 是加密的，只能看到握手和 IP）。

### 示例 7：抓够 100 个包自动停

```bash
sudo tcpdump -i eth0 -nn -c 100 port 443
```

> 抓 100 个 443 端口的包就退出，适合写进脚本。

### 示例 8：组合过滤——某主机的某 TCP 端口

```bash
sudo tcpdump -i eth0 -nn 'host 93.184.216.34 and tcp port 443'
```

> `and` 组合。整段用单引号包起来，避免空格/特殊字符被 shell 拆开。

### 示例 9：只抓 TCP 握手 SYN（看谁在连我）

```bash
sudo tcpdump -i eth0 -nn 'tcp[tcpflags] & tcp-syn != 0'
```

> 只打印 SYN 包，一眼看"谁在向本机发连接请求"。

### 示例 10：tshark（Wireshark 命令行版）

```bash
sudo tshark -i eth0 -f 'tcp port 80' -c 20
```

> `tshark` 是 Wireshark 的 CLI，能用 Wireshark 的解码能力把 HTTP/DNS/TLS 等协议字段完整解析出来；`-f` 是抓包过滤器，`-V` 打详情。复杂协议分析它比 tcpdump 更顺手。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `sudo tcpdump -i eth0 -nn` | 抓某网卡全部包 |
| `sudo tcpdump -i any -nn port 80` | 抓 80 端口 |
| `sudo tcpdump -i eth0 -nn host IP` | 抓与某主机通信 |
| `sudo tcpdump -i eth0 -nn -A port 80` | 看 HTTP 明文 |
| `sudo tcpdump -i eth0 -nn -w x.pcap port 80` | 存盘 |
| `tcpdump -nn -r x.pcap` | 读盘分析 |
| `sudo tcpdump -i eth0 -nn -c 100 ...` | 抓够就停 |

## 六、RHEL 系与 Debian 系差异

- 包名：tcpdump 两系都需单独装（Debian `tcpdump`、RHEL `tcpdump`）；tshark 在 Debian 属 `tshark`，RHEL 属 `wireshark-cli`；
- 选项一致；
- 容器里抓包常缺 CAP_NET_RAW，需要 `--cap-add=NET_RAW` 或在宿主机抓。

## 七、新手易错点

1. **必须 root**：普通用户跑 tcpdump 会报权限错误，前面加 `sudo`。
2. **不加 `-nn` 会被反解拖慢**：高流量时反解主机名很慢，排障一律 `-nn`。
3. **HTTPS 看不到明文**：`-A` 只对 HTTP 等明文协议有效，TLS 内容是加密的。
4. **过滤表达式放最后、用引号**：`tcpdump -i eth0 port 80 and host 1.2.3.4` 容易被 shell 拆错，养成加单引号习惯。
5. **`-w` 存盘后屏幕没输出是正常的**：它在写文件，不是卡死。
6. **高流量别裸抓全部**：不加过滤在万兆网卡上会瞬间产生海量数据并丢包，先定好 `port`/`host` 过滤。
7. **抓包本身有开销**：生产环境短时抓、加 `-c`，别长时间裸奔。

## 八、相关命令与文档

- 速查页：[网络命令速查](../network-commands#抓包)
- 看连接/端口：见 [ss](./ss)
- 测端口连通：见 [nc 与 telnet](./nc-telnet)
- 路径排障：见 [traceroute 与 mtr](./traceroute-mtr)
- 网络整体原理：见 [Linux 网络专题](../../guide/linux-network)
