# iostat 与 iotop 命令详解：谁在让磁盘忙、哪个进程在读写

> 本文是 [Linux 命令速查](../linux-commands#性能与监控) 中 `iostat`、`iotop` 的从 0 到 1 详解。
> 目标：把 `iostat -x` 的磁盘扩展列、`iotop` 的交互界面讲清楚，多看几遍后，你在服务器上敲 `iostat -xz 1` 就知道磁盘瓶颈在哪。
> 环境依据：`iostat`/`mpstat`/`sar` 属 sysstat 包（RHEL/CentOS/Rocky 默认安装；Ubuntu/Debian 需 `apt install sysstat`，2026 年主流为 sysstat 12.x）；`iotop` 属 iotop 包（需 root 或 `CAP_NET_ADMIN`）。本机沙箱未安装，以下选项与输出依据 sysstat 官方 man（man7.org iostat(1)）与 iotop 官方 man，示例为示意输出。

## 一、命令是干什么的

磁盘慢是 Linux 常见瓶颈，但 `vmstat` 只能告诉你"磁盘很忙"，看不出是哪块盘、慢在哪。两个命令分工：

- **`iostat`**：按**磁盘/分区**汇报利用率、吞吐、平均响应时间（await）、队列长度。它是"看设备"的视角。
- **`iotop`**：像 `top` 一样按**进程/线程**列出谁在读盘、谁在写盘，以及等待 I/O 的时间百分比。它是"看谁在干"的视角。

> 类比：`iostat` 像"停车场报表"——每块盘每秒吞吐多少、排队多长；`iotop` 像"调监控抓违停"——直接点名哪个进程在疯狂读写磁盘。

## 二、命令语法

```bash
# iostat
iostat [选项]... [interval [count]]

# iotop
iotop [选项]
```

- `iostat` 的 `interval`/`count`：每隔几秒采样、采几次；第一行仍是开机以来平均；
- `iotop`：默认进入全屏交互界面，按 `q` 退出；加 `-b`（批量模式）可一次性输出，适合脚本和日志。

## 三、选项全表（对照官方文档）

### 1. iostat 常用选项

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-c` | 只显示 CPU 利用率报告 | 不想看磁盘时 |
| `-d` | 只显示设备利用率报告（磁盘） | 看磁盘（常用） |
| `-x` | **扩展统计**（await、%util 等关键列） | 诊断磁盘瓶颈（最常用） |
| `-z` | 跳过采样期间没有活动的设备 | 过滤掉空闲盘，输出更干净 |
| `-k` / `-m` | 以 KB/s 或 MB/s 显示吞吐 | 单位更直观 |
| `-t` | 每次报告前打印时间戳 | 持续采样时标记时间 |
| `-y` | 省略第一行"开机以来平均" | 只想看实时增量 |
| `-p [设备\|ALL]` | 同时显示磁盘及其分区 | 想看 sda1/sda2 细分 |
| `-N` | 显示 LVM/device mapper 名字 | 用了 LVM 时 |
| `-h` | 人类可读大小 | 配合 `-x` 使用 |

### 2. iostat 扩展列（`-x`）怎么读

| 列 | 含义 | 怎么看 |
|---|---|---|
| `r/s`、`w/s` | 每秒读/写请求数 | 请求量 |
| `rkB/s`、`wkB/s` | 每秒读/写字节数 | 吞吐 |
| `await` | 每个 I/O 从发出到完成的平均耗时（毫秒） | **机械盘 >20ms、SSD >1~2ms 就要警惕** |
| `aqu-sz` | 平均 I/O 队列长度 | 持续 >1 说明盘在排队 |
| `%util` | 设备有 I/O 在处理的时间占比 | **接近 100% 说明盘打满**（SSD/RAID 除外） |

> 关键判据：`%util` 接近 100% 且 `await` 升高，就是磁盘饱和；SSD 上 `%util` 100% 不一定是瓶颈（可并行处理）。

### 3. iotop 常用选项

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-o`，`--only` | 只显示正在做 I/O 的进程 | 不看闲着的（交互里按 `o` 切换） |
| `-P`，`--processes` | 只显示进程，不显示线程 | 想看进程维度 |
| `-n NUM`，`--iter=NUM` | 批量模式下采样 NUM 次 | 配合 `-b` |
| `-d SEC`，`--delay=SEC` | 刷新间隔（默认 1 秒） | 控制采样频率 |
| `-b`，`--batch` | 非交互批量模式 | 写脚本、抓日志 |
| `-t`，`--time` | 每行加时间戳 | 批量模式下记录时间 |
| `-u USER`，`--user=USER` | 只看某个用户的进程 | 定位某用户 |
| `-p PID`，`--pid=PID` | 只盯某个进程 | 怀疑某进程时 |
| `-k`，`--kilobytes` | 用 KB 而不是自动单位 | 脚本里稳定输出 |
| `-a`，`--accumulated` | 显示累计 I/O 而非实时带宽 | 看进程总共读写了多少 |

## 四、由浅入深的典型示例

### 示例 1：iostat 基本磁盘报告

```bash
iostat -d 1 3
```

示意输出（依据官方文档，非本机实跑）：

```text
Linux 5.15.0-xx-generic (host) 	09/30/26 	_x86_64_	(4 CPU)

Device             tps    kB_read/s    kB_wrtn/s    kB_read    kB_wrtn
vda               0.50         8.00        20.00       8000      20000
```

- `tps`：每秒传输（I/O 请求）次数；
- `kB_read/s`、`kB_wrtn/s`：每秒读/写速度；
- 最后两列是开机以来累计的读/写总量。

### 示例 2：扩展统计 + 跳过空闲盘（诊断黄金组合）

```bash
iostat -xz 1 3
```

示意输出：

```text
Device            r/s     w/s     rkB/s    wkB/s   aqu-sz  await  %util
vda              1.00   20.00     16.00   400.00    0.50   10.00   12.00
```

- `await` 10ms、`%util` 12%——这块盘很闲；
- 如果 `%util` 冲到 99%、`await` 飙到 100ms+，就是磁盘瓶颈。

### 示例 3：只看 CPU 报告

```bash
iostat -c 1 3
```

> 输出和 `vmstat` 的 cpu 块类似（%user/%system/%iowait/%idle），其中 `%iowait` 高就是磁盘拖累了 CPU。

### 示例 4：带时间戳持续盯盘

```bash
iostat -xz -t 2 10
```

> 每 2 秒一次、共 10 次，每行带时间，方便事后对应"几点开始盘变忙"。

### 示例 5：iotop 交互模式（直接点名进程）

```bash
sudo iotop -oP
```

示意界面：

```text
Total DISK READ :       0.00 B/s | Total DISK WRITE :       1.20 M/s
Current DISK READ:       0.00 B/s | Current DISK WRITE:     800.00 K/s
  TID  PRIO  USER     DISK READ  DISK WRITE  SWAPIN      IO    COMMAND
  1234 be/4 mysql       0.00 B/s    1.20 M/s  0.00 %  5.00 %  mysqld
  5678 be/4 www-data    0.00 B/s    0.00 B/s  0.00 %  0.00 %  apache2
```

- `DISK READ/WRITE`：该进程实时读写带宽；
- `SWAPIN`：换入占用；
- `IO`：该进程等待 I/O 的时间百分比（最关键）；
- 交互里按 `o` 切换"只显示有 I/O 的进程"，按 `q` 退出。

### 示例 6：iotop 批量模式抓一次快照

```bash
sudo iotop -bnoP -d 1 -n 3
```

示意输出：

```text
TID  PRIO  USER     DISK READ  DISK WRITE  SWAPIN     IO    COMMAND
1234 be/4 mysql       0.00 B/s    1.20 M/s  0.00 %  5.00 %  mysqld
```

> `-b` 批量、`-n 3` 采 3 次、`-o` 只看有 I/O 的、`-P` 只看进程。适合写进监控脚本或一次性排查，不会卡在交互界面。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `iostat -xz 1 5` | 磁盘扩展统计，诊断瓶颈（**最常用**） |
| `iostat -xz -t 2` | 带时间戳持续盯盘 |
| `iostat -c 1 5` | 只看 CPU/%iowait |
| `sudo iotop -oP` | 交互模式点名谁在读写盘 |
| `sudo iotop -bnoP -n 3` | 批量抓一次 I/O 快照 |

## 六、RHEL 系与 Debian 系差异

- **包名不同**：RHEL/CentOS/Rocky 默认就装了 sysstat（提供 `iostat`/`mpstat`/`sar`）；Ubuntu/Debian 默认**没装**，需 `sudo apt install sysstat`，而且默认 `/etc/default/sysstat` 里历史采集是关闭的，要改成 `ENABLED="true"` 才会写 `/var/log/sa`。
- **iotop**：两系都要单独安装（RHEL 系 `yum install iotop`，Debian 系 `apt install iotop`），且必须 root 或给二进制加 `cap_net_admin`。
- sysstat 12.x 的列名（如 `aqu-sz`、`areq-sz`）在老版本叫 `avgqu-sz`、`avgrq-sz`，以本机 `iostat -V` 版本为准。

## 七、新手易错点

1. **`iostat` 第一行是开机以来平均**：判断当前瓶颈要看后面实时行，或加 `-y` 跳过第一行。
2. **把 `%util` 当磁盘 100% 占用率**：它是"有 I/O 的时间占比"，对可并行的 SSD/RAID 队列，100% 不等于饱和，要结合 `await` 和 `aqu-sz` 一起看。
3. **iotop 不加 sudo 跑不起来**：它需要读内核任务统计，普通用户会报错；要么 sudo，要么 `setcap cap_net_admin+ep`。
4. **Ubuntu 上 `sar`/`iostat` 有数据但没历史**：是因为没启用 sysstat 采集，不是命令坏了。
5. **`iotop` 界面别用 `Ctrl+C` 之外的方式强关**：正常按 `q` 退出即可。
6. **这些都是只读监控命令**：不会改动系统（`iotop` 交互里按 `i` 能改 I/O 优先级，那是另一个操作，别乱按）。

## 八、相关命令与文档

- 速查页：[Linux 命令速查](../linux-commands)
- 轻量版总览：`vmstat`（详解见 [vmstat](./vmstat)）
- 每个 CPU 核与历史数据：`mpstat`/`sar`（详解见 [mpstat-sar](./mpstat-sar)）
- 磁盘空间：`df`（详解见 [df](./df)）、`du`（详解见 [du](./du)）
- 磁盘设备清单：`lsblk`（详解见 [lsblk-blkid](./lsblk-blkid)）
- 存储排查思路：见 [Linux 存储专题](../../guide/linux-storage)、[性能专题](../../guide/linux-performance)
