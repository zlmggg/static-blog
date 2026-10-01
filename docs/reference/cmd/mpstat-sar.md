# mpstat 与 sar 命令详解：看每个 CPU 核，并回溯历史性能

> 本文是 [Linux 命令速查](../linux-commands#性能与监控) 中 `mpstat`、`sar` 的从 0 到 1 详解。
> 目标：把 `mpstat -P ALL` 的多核输出、`sar -u/-r/-n/-q/-b` 的各类报表讲清楚，多看几遍后，你在服务器上敲 `sar -u` 就知道怎么回溯昨天的 CPU。
> 环境依据：两者都属 sysstat 包（RHEL/CentOS/Rocky 默认安装；Ubuntu/Debian 需 `apt install sysstat` 并启用采集，2026 年主流为 sysstat 12.x）。本机沙箱未安装，以下选项与输出依据 sysstat 官方 man（man7.org sar(1)），示例为示意输出。

## 一、命令是干什么的

- **`mpstat`**（multiprocessor stat）：和 `vmstat`/`iostat` 类似，但它能**按每个 CPU 核分别**汇报利用率。排查"是不是某个核被打满、其他核闲着"这种多核不均衡问题，非 `mpstat` 不可。
- **`sar`**（system activity reporter）：是 sysstat 的灵魂。它既能**实时**输出各类统计，更重要的是能读取 `/var/log/sa/` 下**历史采集好的数据**，让你回头看"昨天下午 3 点 CPU 为什么飙高"。这是 `top`/`vmstat` 这些只能看当下的命令做不到的。

> 类比：`mpstat` 像"把 CPU 拆成每个窗口单独报进出人数"；`sar` 像"商场的监控录像+客流台账"，出事了能倒带回看。

## 二、命令语法

```bash
# mpstat
mpstat [选项]... [interval [count]]

# sar
sar [选项]... [interval [count]]
# 读历史数据
sar -f /var/log/sa/saDD [-s hh:mm:ss] [-e hh:mm:ss]
```

- `interval`/`count`：每隔几秒采样、采几次；
- 不带 interval 时，`sar` 默认读**当天**或指定文件的历史数据；
- `-f`：指定历史数据文件（默认读 `/var/log/sa/saDD`，DD 是当天日期）。

## 三、选项全表（对照官方文档）

### 1. mpstat 常用选项

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-P ALL` | **每个 CPU 核都打印一行** + 一行全局平均 | 看多核均衡（最常用） |
| `-P 0,1` | 只看指定核 | 盯某几个核 |
| `-u` | 显示 CPU 利用率（默认） | 看 usr/sys/iowait 等 |
| interval/count | 采样间隔与次数 | 实时观察 |

### 2. sar 常用报表选项（按资源分类）

| 选项 | 报表内容 | 看什么 |
|---|---|---|
| `-u` | **CPU** 利用率（%user/%nice/%system/%iowait/%steal/%idle） | CPU 是不是打满（默认） |
| `-r` | **内存**利用率（kbmemfree/kbavail/buff/cache/...） | 内存历史走势 |
| `-B` | **分页**统计（pgpgin/s/pgpgout/s/fault/s/majflt/s） | 缺页、换页压力 |
| `-b` | **I/O 与传输**（tps/rtps/wtps/bread/s/bwrtn/s） | 磁盘读写速率 |
| `-d` | 每个**块设备**活动（配合 `-x` 看 await/%util） | 磁盘历史 |
| `-n KEYWORD` | **网络**统计，KEYWORD 可取 `DEV`/`EDEV`/`TCP`/`ETCP`/`SOCK` | 网卡收发、TCP 重传 |
| `-q` | **队列长度与负载**（runq-sz/ldavg-1/5/15） | 系统负载历史 |
| `-w` | 进程创建/上下文切换 | cswch/s 飙升 |
| `-m KEYWORD` | 电源/温度（CPU/FAN/TEMP） | 较少用 |
| `-A` | 几乎所有报表合起来 | 一次性全看（输出很长） |

### 3. sar 读历史数据的控制选项

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-f 文件` | 从指定数据文件读取 | 读 `/var/log/sa/sa29` 这种历史文件 |
| `-o 文件` | 实时采样时把数据存成文件 | 现场采集 |
| `-s hh:mm:ss` | 设定起始时间 | 只看某个时段 |
| `-e hh:mm:ss` | 设定结束时间 | 圈定"昨天 15:00~15:30" |
| `-i 秒` | 尽量按固定间隔取点 | 历史数据太多时降采样 |
| `-P ALL` | 每个 CPU 核一行 | 配合 `-u` 看多核历史 |
| `-1` / `-2` | 读昨天/前天的文件 | 快速回看（`-1`=昨天） |

> 数据文件位置：默认 `/var/log/sa/saDD`（二进制，DD 为日期）；文字版报告在 `/var/log/sarDD`（若配置了）。

## 四、由浅入深的典型示例

### 示例 1：mpstat 看每个 CPU 核

```bash
mpstat -P ALL 1 3
```

示意输出（依据官方文档，非本机实跑）：

```text
Linux 5.15.0-xx-generic (host) 	09/30/26 	_x86_64_	(4 CPU)

11:28:36  CPU    %usr   %nice    %sys %iowait    %irq   %soft  %steal  %guest  %idle
11:28:37  all    2.00    0.00    1.00    0.00    0.00    0.00    0.00    0.00   97.00
11:28:37    0    5.00    0.00    2.00    0.00    0.00    0.00    0.00    0.00   93.00
11:28:37    1    1.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00   98.00
11:28:37    2    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00  100.00
11:28:37    3    2.00    0.00    1.00    0.00    0.00    0.00    0.00    0.00   97.00
```

- `all` 是四个核的平均；
- 每一行是一个核。如果看到某个核 `%usr` 长期 100% 而其他核 `%idle` 很高，说明应用没有用好多核。

### 示例 2：sar 看今天的 CPU 历史

```bash
sar -u
```

示意输出：

```text
11:20:01     CPU      %usr     %nice      %sys   %iowait    %steal      %irq     %soft    %guest     %idle
11:30:01     all      3.25      0.00      1.10      0.20      0.00      0.00      0.05      0.00     95.40
11:40:01     all      5.10      0.00      1.30      0.10      0.00      0.00      0.05      0.00     93.45
Average:     all      4.18      0.00      1.20      0.15      0.00      0.00      0.05      0.00     94.42
```

> 每 10 分钟一个点，`%idle` 低、`%usr` 高的时段就是忙时。

### 示例 3：sar 看内存历史

```bash
sar -r
```

> 输出 kbmemfree、kbavail、%memused、buffers、cached、commitmem 等列，能画出"内存是不是在持续上涨"的曲线。

### 示例 4：sar 看网络接口收发

```bash
sar -n DEV 1 3
```

示意输出：

```text
IFACE   rxpck/s   txpck/s    rxkB/s    txkB/s   rxcmp/s   txcmp/s  rxmcst/s   %ifutil
eth0      12.50     10.20    200.00    150.00      0.00      0.00      0.00      0.05
lo         0.00      0.00      0.00      0.00      0.00      0.00      0.00      0.00
```

- `rxkB/s`/`txkB/s`：收/发带宽；
- `%ifutil`：网卡利用率，接近网卡带宽说明网卡跑满。

> 想看 TCP 重传：`sar -n EDEV`；看 TCP 连接数：`sar -n SOCK`。

### 示例 5：sar 看负载与运行队列历史

```bash
sar -q
```

> 输出 runq-sz（等待运行的进程数）、ldavg-1/5/15（负载）。事后定位"几点开始负载升高"。

### 示例 6：sar 看磁盘 I/O 历史

```bash
sar -b
```

> tps、rtps、wtps、bread/s、bwrtn/s——开机以来的磁盘读写速率历史。

### 示例 7：读昨天某时段的数据

```bash
sar -u -f /var/log/sa/sa29 -s 14:00:00 -e 15:00:00
```

> 读 29 号（`sa29`）的数据，只看 14:00~15:00 的 CPU 报表。这是事后复盘的核心用法。

### 示例 8：实时采样并存档

```bash
sar -o /tmp/mydata 2 10
```

> 每 2 秒采一次、共 10 次，同时把数据存到 `/tmp/mydata`，事后可用 `sar -f /tmp/mydata` 慢慢翻。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `mpstat -P ALL 1 3` | 看每个 CPU 核是否均衡 |
| `sar -u` | 今天 CPU 历史 |
| `sar -r` | 今天内存历史 |
| `sar -n DEV 1 3` | 实时看网卡收发 |
| `sar -q` | 负载/运行队列历史 |
| `sar -b` | 磁盘 I/O 历史 |
| `sar -u -f /var/log/sa/saDD -s ... -e ...` | 回看指定时段 CPU |
| `sar -u -1` | 看昨天 CPU |

## 六、RHEL 系与 Debian 系差异

- **RHEL/CentOS/Rocky**：sysstat 默认安装并开启采集，`/var/log/sa/` 下默认保留约 4 周数据，开箱即用。
- **Ubuntu/Debian**：默认不装、也不采集。需 `sudo apt install sysstat`，再把 `/etc/default/sysstat` 的 `ENABLED="false"` 改成 `ENABLED="true"`，重启 `sysstat` 服务后才会生成 `/var/log/sa/saDD`。
- 数据保留天数由 `/etc/sysstat/sysstat`（或 `/etc/sysconfig/sysstat`）里的 `HISTORY` 控制，默认约 28 天。
- 列名在 sysstat 12.x 与老版本基本一致，个别新列（如 PSI 压力）以本机 `sar -V` 为准。

## 七、新手易错点

1. **Ubuntu 上 `sar` 报"没数据"**：不是命令坏了，是没启用采集；先确认 `/var/log/sa/` 下有没有 `saDD` 文件。
2. **`sar` 不带参数默认只看 CPU**：想看内存/网络必须加 `-r`/`-n DEV`，别以为它万能。
3. **读历史要加 `-f`**：裸 `sar -u` 只看当天；看别的日期一定要 `-f /var/log/sa/saDD` 或 `-1`/`-2`。
4. **`mpstat` 不 `-P ALL` 只看平均**：平均会掩盖"单核打满"，排查多核问题务必 `-P ALL`。
5. **`%iowait` 高是磁盘问题不是 CPU 问题**：结合 `sar -b`/`iostat -x` 看磁盘。
6. **这些都是只读命令**：`sar -o` 会写文件，注意别写到没有权限的目录。

## 八、相关命令与文档

- 速查页：[Linux 命令速查](../linux-commands)
- 实时总览：`vmstat`（详解见 [vmstat](./vmstat)）
- 磁盘扩展统计：`iostat`（详解见 [iostat-iotop](./iostat-iotop)）
- 内存：`free`（详解见 [free](./free)）
- 性能排查思路：见 [Linux 性能专题](../../guide/linux-performance)
