# free 命令详解：看内存还剩多少

> 本文是 [Linux 命令速查](../linux-commands#性能与监控) 中 `free` 的从 0 到 1 详解。
> 目标：把 `free --help` 里的每个选项讲清楚，多看几遍后，你在服务器上敲 `free --help` 就知道该用哪个选项。
> 环境依据：procps-ng 3.3.17（Ubuntu 22.04 自带；RHEL/Rocky 自带同属 procps-ng，用法一致）。

## 一、命令是干什么的

`free` 用来查看系统**内存（RAM）和交换分区（swap）的使用情况**：总共有多少、已用多少、还剩多少。它是 SRE 判断"内存够不够"的第一把尺子。

- 不带参数：打印一次内存和 swap 概况后退出；
- 加 `-h`：用 K/M/G 这种人类可读的单位（最常用）；
- 加 `-s N`：每隔 N 秒自动刷新一次，像一个极简的实时监控。

> 类比：`free` 就像 Windows 任务管理器里"性能 → 内存"那一块的数字概览，只不过它在终端里用一行表格呈现。

关键概念：输出里的 **`buff/cache`（缓冲区/缓存）并不是"被用掉的内存"**，它们是 Linux 拿空闲内存临时缓存磁盘数据，需要时可以立刻回收。所以判断内存是否真的紧张，要看 **`available`（可用）** 这一列，而不是 `free`（空闲）那一列。

## 二、命令语法

```bash
free [选项]
```

- `[选项]`：可选，控制单位、是否持续刷新、是否显示合计等；
- `free` 没有"文件参数"，它只读内核提供的 `/proc/meminfo`，不操作任何文件。

最简单的用法：

```bash
free
```

## 三、选项全表（对照 `free --help`）

### 1. 控制显示单位

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-h`，`--human` | 人类可读单位（自动用 K/M/G） | **最常用**，一眼看懂大小 |
| `-b`，`--bytes` | 以字节为单位 | 需要精确到字节时 |
| `-k`，`--kibi` | 以 KiB（1024）为单位（默认） | 脚本里固定单位 |
| `-m`，`--mebi` | 以 MiB 为单位 | 快速看大致兆数 |
| `-g`，`--gibi` | 以 GiB 为单位 | 大内存机器看 GB |
| `--kilo`/`--mega`/`--giga`/`--tera`/`--peta` | 按 1000 进制的 KB/MB/GB… | 想看厂商口径大小 |
| `--tebi`/`--pebi` | 按 1024 进制的 TiB/PiB | 超大内存机器 |
| `--si` | 用 1000 而不是 1024 换算 | 配合 `-h` 改换算进制 |

### 2. 控制显示内容与刷新

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-t`，`--total` | 在最后增加一行，显示 RAM+swap 的合计 | 想看总内存盘子 |
| `-l`，`--lohi` | 显示低内存/高内存的详细统计 | 排查内存分片（较少用） |
| `-s N`，`--seconds N` | 每隔 N 秒重复打印 | 持续观察内存变化（配合 `Ctrl+C` 停） |
| `-c N`，`--count N` | 只打印 N 次就退出 | 配合 `-s` 做有限次采样 |
| `-w`，`--wide` | 宽列输出（把 buffer 和 cache 分成两列） | 想分清 buffer/cache 各占多少 |

## 四、由浅入深的典型示例

### 示例 1：默认输出（单位是 KB）

```bash
free
```

```text
               total        used        free      shared  buff/cache   available
Mem:         8324672      571376     3311160       19104     4442136     7620072
Swap:              0           0           0
```

逐列解释：

- `total`：物理内存总量（约 8 GB）；
- `used`：真正被进程用掉的内存；
- `free`：完全空闲、一点没碰的内存；
- `shared`：多个进程共享的内存（如 tmpfs）；
- `buff/cache`：内核做的磁盘缓冲/缓存，需要时可回收；
- `available`：**估算出的"应用程序还能用多少内存"**，判断内存够不够看这一列。

> 这台机器 `free` 有 3.2 GB、`buff/cache` 有 4.2 GB，`available` 高达 7.3 GB——说明内存非常充裕，绝不是"只剩 3.2 GB"。

### 示例 2：人类可读（最高频）

```bash
free -h
```

```text
               total        used        free      shared  buff/cache   available
Mem:           7.9Gi       557Mi       3.2Gi        18Mi       4.2Gi       7.3Gi
Swap:             0B          0B          0B
```

> 单位自动换成 GiB/MiB，不用心算除以 1024。

### 示例 3：显示 RAM+swap 合计行

```bash
free -h -t
```

```text
               total        used        free      shared  buff/cache   available
Mem:           7.9Gi       557Mi       3.2Gi        18Mi       4.2Gi       7.3Gi
Swap:             0B          0B          0B
Total:         7.9Gi       557Mi       3.2Gi        18Mi       4.2Gi       7.3Gi
```

> 最后多一行 `Total`，把内存和 swap 加总。

### 示例 4：每 2 秒刷新一次

```bash
free -s 2
```

> 每 2 秒打印一屏，按 `Ctrl+C` 停止。适合盯"内存是不是在悄悄涨"。

### 示例 5：每 2 秒刷一次，只刷 3 次

```bash
free -s 2 -c 3
```

> 自动采样 3 次后退出，适合写进一次性观察脚本里，不用手动 `Ctrl+C`。

### 示例 6：宽列输出，buffer 和 cache 拆开

```bash
free -h -w
```

> 加 `-w` 后 `buff/cache` 会拆成 `buffers` 和 `cache` 两列，能看清"块设备缓冲"和"页缓存"各占多少。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `free -h` | 人类可读看内存（**最常用**） |
| `free -h -t` | 看内存+swap 合计 |
| `free -h -s 2` | 每 2 秒持续刷新 |
| `free -h -s 2 -c 5` | 持续采样 5 次自动退出 |
| `free -h -w` | 拆开 buffers 和 cache |

## 六、RHEL 系与 Debian 系差异

`free` 属于 procps-ng，**RHEL/CentOS/Rocky 与 Ubuntu/Debian 用法完全一致**，上面的选项通用。唯一要注意的是版本：

- 老版本 procps（3.3.10 以前）的输出里**没有 `available` 列**，只有 `free` 和 `buff/cache`；现在主流发行版都有 `available`，以本机 `free -h` 实际列为准；
- swap 是否存在、大小多少取决于是否划分了交换分区/文件，两系默认都可能没有 swap（如容器里 `Swap: 0`）。

## 七、新手易错点

1. **把 `free` 列当成"还能用的内存"**：这是最常见的误判。真正能用的是 `available`，`buff/cache` 是可以回收的。
2. **看到 `buff/cache` 很大就以为内存不足**：恰恰相反，Linux 鼓励用空闲内存做缓存，缓存多是好事。
3. **容器里 `free` 显示的是宿主机内存**：容器没有独立的内存视图隔离时，`free` 看到的是整个节点的内存，别当成容器配额。
4. **`-s` 会一直刷**：忘了按 `Ctrl+C` 就停不下来；脚本里请用 `-c` 限制次数。
5. **`free` 是只读命令，可放心使用**：它只读取 `/proc/meminfo`，不会改动任何东西。
6. **单位别搞混**：裸 `free` 是 KB，`-h` 才是 K/M/G；写脚本时记得显式加 `-k` 或 `-m`。

## 八、相关命令与文档

- 速查页：[Linux 命令速查](../linux-commands)
- 看更细的内存/swap/Io 趋势：`vmstat`（详解见 [vmstat](./vmstat)）
- 看哪个进程最吃内存：`top`、`ps`
- 磁盘空间别和内存搞混：`df`（详解见 [df](./df)）
- 性能排查思路：见 [Linux 性能专题](../../guide/linux-performance)
