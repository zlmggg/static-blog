# nc 与 telnet 命令详解：测端口、传数据、当简易服务器

> 本文是 [网络命令速查](../network-commands#连通性测试) 中 `nc`（netcat）与 `telnet` 的从 0 到 1 详解；本篇一次讲清 **端口探测/数据传输神器 nc** 和 **老式端口测试 telnet**。
> 目标：掌握 `nc -l/-z/-v/-u/-k`，以及用它们测端口通不通、临时起个监听服务传文件。
> 环境依据：`nc` 为 **OpenBSD netcat 1.218**（本机实跑，`/usr/bin/nc.openbsd`）；`telnet` 为 BSD telnet（本机实跑）。注意还有一种叫 `ncat`（nmap 套件）的 nc，参数略有差异。

## 一、命令是干什么的

- `nc`（netcat，"网络瑞士军刀"）：万能网络小工具，能**连端口、监听端口、扫端口、传文件、发 UDP**。SRE 排查端口连通性几乎必用。
- `telnet`：最早的远程登录协议客户端，现在主要剩一个用途——**手敲一个 TCP 端口测它通不通**（因为它就是个裸 TCP 连接）。

> 类比：`nc` 像一个可编程的"对讲机"——你让它拨到对方哪个端口它就拨过去，说的话直接变网络字节；它也能守在某个端口等人来连。`telnet` 是个更老、功能更单一的对讲机，现在大家只用它"拨号试一下占线没"。

什么时候用：
- 服务起好了但客户端连不上？`nc -zv 主机 端口` 秒判端口通不通；
- 没有现成客户端？用 `nc -l` 起个临时服务，或两台机器之间传文件；
- ping 不通但想测应用端口（ICMP 常被禁），就用 `nc`/`telnet`。

## 二、命令语法

```bash
# 作为客户端：连到对方
nc [选项] 目标主机 端口
# 作为服务端：监听本机端口
nc [选项] -l 本机端口
telnet 目标主机 [端口]
```

- 客户端模式：给 `主机 端口`，它就发起 TCP 连接；
- 服务端模式：加 `-l`（listen），守在本机端口等别人连。

最简用法：

```bash
nc -zv 127.0.0.1 10000     # 测端口通不通
```

## 三、选项全表（对照 `nc -h`，OpenBSD netcat）

### 1. 连接与探测

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-z` | 零 I/O，只**探测端口开没开**，不发数据 | 扫端口（与 `-v` 搭配） |
| `-v` | 详细输出（打印成功/失败） | 看连接结果（极常用） |
| `-w 秒` | 连接/读取**超时** | 避免卡死 |
| `-n` | 不做 DNS/端口名反解 | 更快 |
| `-4` / `-6` | 强制 IPv4 / IPv6 | 指定协议族 |

### 2. 服务端与数据传输

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-l` | **监听模式**，当服务端等连接 | 临时起个端口 |
| `-k` | 监听后**保持**，接受多个连续连接 | 不 `-k` 则接一次就退 |
| `-p 端口` | 指定本地源端口 | 固定本机出口端口 |
| `-s 地址` | 指定本地源地址 | 多 IP 网卡选源 |
| `-N` | stdin 到 EOF 后关闭 socket | 传完文件自动结束 |
| `-q 秒` | stdin 到 EOF 后再等几秒退出 | 配合传文件 |

### 3. UDP / 其它

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-u` | 使用 **UDP**（默认是 TCP） | 测 DNS/QUIC 等 UDP 端口 |
| `-U` | 使用 UNIX 域套接字 | 测本地 socket |
| `-x 地址:端口` | 通过代理连接 | 走 socks/http 代理 |

> 注意：OpenBSD 版 `nc` **没有** `-e`（连接后执行外部程序）这个选项；把 shell 暴露到网络的反向 shell 功能只存在于 nmap 的 `ncat`（`--exec`/`-e`）和老式 GNU netcat，本环境的 OpenBSD nc 不具备。

## 四、由浅入深的典型示例

以下输出为本机实跑。

### 示例 1：测某个 TCP 端口通不通（最常用）

```bash
nc -zv 223.5.5.5 53
```

```text
Connection to 223.5.5.5 53 port [tcp/domain] succeeded!
```

> `-z` 只探测、`-v` 打印结果。看到 `succeeded!` 就说明 TCP 三次握手成功，端口是开的。

### 示例 2：测本机监听端口

```bash
nc -zv 127.0.0.1 10000
```

```text
Connection to 127.0.0.1 10000 port [tcp/webmin] succeeded!
```

> 配合 `ss -tlnp` 知道有进程在 10000 监听，这里再验证一下能连上。

### 示例 3：端口没开时的报错

```bash
nc -zv 127.0.0.1 9999
```

```text
nc: connect to 127.0.0.1 port 9999 (tcp) failed: Connection refused
```

> `Connection refused` = 明确拒绝（这个端口没人监听）。和"超时没响应"不同，后者通常是被防火墙 DROP 了。

### 示例 4：扫一段端口

```bash
nc -z -v -w2 127.0.0.1 10000-10001
```

```text
Connection to 127.0.0.1 10000 port [tcp/webmin] succeeded!
nc: connect to 127.0.0.1 port 10001 (tcp) failed: Connection refused
```

> 端口可以给区间 `lo-hi`。扫自己机器上哪些端口开着。

### 示例 5：当简易服务端，接收对方消息

在 A 机器上（监听 9000）：

```bash
nc -l 9000
```

在 B 机器上连过来打字：

```bash
nc A机器IP 9000
```

> 两边就进入了一个文字聊天窗口，敲什么对方都能看到。`-k` 让它接完一个还能接下一个。

### 示例 6：用 nc 传文件

接收方（先起）：

```bash
nc -l 9000 > received.tar.gz
```

发送方：

```bash
nc 接收方IP 9000 < file.tar.gz
```

> 一条命令把文件从一台机器搬到另一台，不用起 FTP。传完按 `Ctrl+C` 结束。

### 示例 7：测 UDP 端口

```bash
nc -zvu -w2 223.5.5.5 53
```

> `-u` 切到 UDP。注意 UDP 是无连接的，探测结果不一定准（很多时候"通了"也不回包）。

### 示例 8：用 telnet 测端口（老派做法）

```bash
telnet 127.0.0.1 10000
```

```text
Trying 127.0.0.1...
Connected to 127.0.0.1.
Escape character is '^]'.
Connection closed by foreign host.
```

> 看到 `Connected to ...` 就是 TCP 连上了；连不上会停在 `Trying ...` 然后超时/拒绝。`^]` 是 telnet 退出转义符，输入后再输 `quit` 退出。现在基本用 `nc -zv` 替代它。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `nc -zv 主机 端口` | 测 TCP 端口通不通（**最常用**） |
| `nc -zvu 主机 端口` | 测 UDP 端口 |
| `nc -z -v 主机 端口1-端口N` | 扫端口区间 |
| `nc -l 端口` | 本机起临时监听服务 |
| `nc -l 端口 > 文件` | 接收文件 |
| `nc 主机 端口 < 文件` | 发送文件 |
| `telnet 主机 端口` | 老派测端口 |

## 六、RHEL 系与 Debian 系差异

- Ubuntu/Debian 的 `nc` 默认常是 **OpenBSD netcat**（本环境即此）；
- RHEL/Rocky 上 `nc` 可能来自 **nmap-ncat**（`ncat`）。ncat 多了 `--exec`、`--ssl`、`--proxy` 等增强参数，但上面 `-z/-v/-l/-u` 基本通用；
- 包名：Debian `netcat-openbsd` 或 `ncat`；RHEL `nmap-ncat`；
- `telnet` 两系都要单独装（默认不带）：Debian `apt install telnet`，RHEL `dnf install telnet`。

## 七、新手易错点

1. **`nc -zv` 没加 `-v` 就没输出**：只探测不打印结果，会以为命令卡死了。
2. **`Connection refused` 和超时是两回事**：refused = 端口没监听；超时 = 多半被防火墙拦了，定位方向不同。
3. **UDP 探测不可靠**：UDP 无连接，`nc -zvu` 经常显示"成功"但其实没真正验证。
4. **`-l` 不加 `-k` 只接一次**：接一个连接就退出，要反复测试记得 `-k`。
5. **传文件注意方向**：接收方先 `nc -l > 文件`，发送方才 `nc 接收方 < 文件`，顺序反了会等不到连接。
6. **反向 shell 是高危功能**：ncat/GNU nc 的 `--exec`/`-e` 能把 shell 暴露到网络上，绝不要在公网监听的端口上用（OpenBSD nc 无此选项）。

## 八、相关命令与文档

- 速查页：[网络命令速查](../network-commands#连通性测试)
- 看本机谁在监听：见 [ss](./ss)
- 基础连通性：见 [ping](./ping)
- 路径排障：见 [traceroute 与 mtr](./traceroute-mtr)
- HTTP 接口测试：见 [curl](./curl)
- 网络整体原理：见 [Linux 网络专题](../../guide/linux-network)
