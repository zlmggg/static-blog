# iftop、nethogs 与 nload 命令详解：看谁在吃带宽

> 本文是 [网络命令速查](../network-commands#流量监控) 中 `iftop`、`nethogs`、`nload` 的从 0 到 1 详解；本篇一次讲清这三个"看带宽"工具，并按**按连接 / 按进程 / 按网卡总量**区分。
> 目标：知道带宽飙高时该用哪个，看懂实时流量。
> 环境依据：本沙箱**三者均未安装**，选项依据官方 man 锁定——iftop（Debian bookworm `iftop` 1.0~pre4）、nethogs（bookworm `nethogs`）、nload（经典 0.7.x）。示例为典型形态示意，需 root。

## 一、命令是干什么的

带宽突然飙高，要回答三个层次的问题，正好对应三个工具：

| 工具 | 统计维度 | 回答的问题 |
|---|---|---|
| `iftop` | **按连接（哪台 ↔ 哪台）** | 流量是和哪个对端之间产生的？ |
| `nethogs` | **按进程（哪个 PID）** | 是哪个程序在狂发数据？ |
| `nload` | **按网卡总量** | 这张网卡现在进出多少带宽？ |

> 类比：nload 是"电表总闸读数"，只告诉你整栋楼用了多少电；iftop 是"每根电线的电流"，告诉你是哪条线在耗电；nethogs 是"哪个电器在耗电"，直接定位到空调还是电热水器。

什么时候用：
- 服务器出口带宽打满告警：先 `nload` 看总量，再 `iftop` 看和谁，再 `nethogs` 看哪个进程。

## 二、命令语法

```bash
sudo iftop -i 网卡 [选项]
sudo nethogs [网卡] [选项]
nload [选项] [网卡]
```

- 三者默认进**实时刷新的全屏界面**，按 `q` 退出；
- 都要 root（要抓包/读套接字统计）。

## 三、选项全表（据官方 man）

### 1. iftop（按连接）

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-i 网卡` | 指定监控网卡 | `sudo iftop -i eth0` |
| `-n` | 不反解主机名 | 更快、干净 |
| `-N` | 不把端口号转成服务名 | 直接看数字端口 |
| `-P` | **显示端口** | 看清连到哪个端口 |
| `-B` | 用字节/秒而不是 bit/秒 | 按字节看 |
| `-F 网络/掩码` | 只统计进出该网段的流量 | 网关机上圈定方向 |
| `-t` | 文本模式输出（不进全屏） | 脚本里抓一次 |

界面内按键：`p` 切端口、`s`/`d` 按源/目的聚合、`1/2/3` 按某列排序、`q` 退出。

### 2. nethogs（按进程）

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-d 秒` | 刷新间隔（默认 1 秒） | `sudo nethogs -d 2` |
| `-t` | trace 模式（文本输出） | 脚本记录 |
| `-v 模式` | 显示单位（0=KB/s，5=GB/s） | 换单位 |
| `-c 次数` | 刷新几次后退出 | 配合 trace 用 |
| `-a` | 监控所有设备（含 lo） | 连回环也统计 |

### 3. nload（按网卡总量）

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-m` | 同时显示多块网卡（不画图） | 多看几张卡 |
| `-t 毫秒` | 刷新间隔 | 默认 500ms |
| `-u 单位` | 流量单位（如 m=Mbit/s） | 固定单位 |
| `-U 单位` | 显示总量（累计）单位 | 看累计吞吐 |
| 网卡名 | 指定只看某网卡 | `nload eth0` |

## 四、由浅入深的典型示例

以下为典型输出形态（示意），需 root。

### 示例 1：看某网卡按连接的流量（iftop）

```bash
sudo iftop -i eth0 -nNP
```

```text
    192.168.1.10  =>  93.184.216.34:443   2.5Mb  2.1Mb  2.0Mb
                  <=                     12Mb   11Mb   10Mb
    192.168.1.20  =>  10.0.0.5:22        10Kb   12Kb   11Kb
```

> 每行一对主机；`=>` 是发出、`<=` 是接收；三列分别是最近 2/10/40 秒平均速率。一眼看出谁在下载大文件。

### 示例 2：iftop 文本模式（给脚本抓一次）

```bash
sudo iftop -i eth0 -t -s 10
```

> `-t` 不进全屏，把一次统计打印到 stdout。

### 示例 3：看哪个进程在吃带宽（nethogs）

```bash
sudo nethogs eth0
```

```text
 PID   USER   PROGRAM            DEV        SENT      RECEIVED
 1234  root   /usr/bin/curl      eth0       2.5MB      48MB
 1283  root   gost               eth0       1.2MB      12MB
```

> 直接按进程汇总收发流量。带宽飙高时立刻看到是 PID 1234 的 curl 在大下载。

### 示例 4：nethogs 调刷新间隔 + trace 输出

```bash
sudo nethogs -d 2 -t -c 5
```

> 每 2 秒刷新、共刷 5 次后退出，文本输出，可落盘记录。

### 示例 5：看网卡总进出带宽（nload）

```bash
nload eth0
```

```text
Device eth0  [192.168.1.10]
====================================================================
Incoming:
  Curr: 12.3 MBit/s   Avg: 11.8 MBit/s   Min: 0.9 kBit/s   Max: 95 MBit/s
Outgoing:
  Curr: 2.1 MBit/s    Avg: 2.0 MBit/s    Min: 0.5 kBit/s   Max: 8 MBit/s
```

> `Incoming`=流入（下载）、`Outgoing`=流出（上传）。只看总量、不细分，最直观。

### 示例 6：同时看多张网卡

```bash
nload -m
```

> `-m` 把所有网卡分屏显示，不画大图形。

### 示例 7：固定单位

```bash
nload -u M
```

> 统一用 MB/s 显示，避免自动换算来回跳。

### 示例 8：排障组合拳

```bash
nload eth0                 # 1) 先看是不是真打满了
sudo iftop -i eth0 -nNP    # 2) 看流量和谁之间
sudo nethogs eth0          # 3) 定位到哪个进程
```

> 这就是带宽告警的标准排查链路。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `sudo iftop -i eth0 -nNP` | 按连接看流量 |
| `sudo nethogs eth0` | 按进程看谁在吃带宽 |
| `nload eth0` | 看网卡总进出带宽 |
| `nload -m` | 同时看所有网卡 |

## 六、RHEL 系与 Debian 系差异

- 包名：iftop/nethogs/nload 两系都需单独装（Debian `apt install iftop nethogs nload`，RHEL 启用 EPEL 后 `dnf install iftop nethogs nload`）；
- 选项一致；
- 三者都是交互式全屏工具，SSH 终端里用最舒服。

## 七、新手易错点

1. **都要 root**：普通用户看不到流量，前面加 `sudo`。
2. **退出是 `q`**：交互式界面不知道按 q 会以为卡住。
3. **bit 与 Byte 别混**：运营商说的带宽是 bit/s，文件下载速度是 Byte/s，差 8 倍。iftop 默认 bit，加 `-B` 才是字节。
4. **iftop 的 `=>`/`<=` 是相对网卡方向**：别和"谁主动发"混淆。
5. **nethogs 看不到内核态流量**：它按进程归类，纯网卡转发/无 socket 的流量可能显示不全。
6. **不要长时间挂着 iftop**：它本身抓包有开销，看完即退。

## 八、相关命令与文档

- 速查页：[网络命令速查](../network-commands#流量监控)
- 抓具体包内容：见 [tcpdump](./tcpdump)
- 看连接数：见 [ss](./ss)
- 网络整体原理：见 [Linux 网络专题](../../guide/linux-network)
