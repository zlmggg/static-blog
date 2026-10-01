# top 与 htop 命令详解：实时看谁在吃 CPU 和内存

> 本文是 [Linux 命令速查](../linux-commands#进程查看) 中 `top` 与 `htop` 的从 0 到 1 详解，本篇一次讲清「实时资源监控」。
> 目标：把 `top`/`htop` 的命令行选项和启动后的交互键位讲清楚（交互键是本机启动后按 `h` 抓到的真实帮助），看完你在服务器上就能熟练操作。
> 环境依据：`top` 属 procps-ng 3.3.17（Ubuntu 22.04 自带）；`htop` 3.0.5（`htop` 包，需单独装）。RHEL/Rocky 自带 top 同为 procps-ng。

## 一、命令是干什么的

`ps` 是拍快照，`top` 是**实时刷新**的动态任务管理器：每隔几秒刷新一次，持续显示谁占 CPU、谁占内存、负载多高。

- `top`：系统自带、纯文本、开箱即用；
- `htop`：`top` 的增强版，有颜色、鼠标、树形显示，更好用，但要单独装。

> 类比：就是 Linux 版「任务管理器」的性能标签页。服务器卡顿时第一个敲的命令就是 `top`。

## 二、命令语法

```bash
top [选项]
htop [选项]
```

两者都主要是**交互程序**——启动后全屏显示，在界面里按键操作，不是靠命令行参数一次性跑完。

## 三、选项全表

### 1. top 命令行选项（对照 `top -h`）

```text
top -hv | -bcEeHiOSs1 -d secs -n max -u|U user -p pid(s) -o field -w [cols]
```

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-b` | **批处理模式**（不进交互屏，输出到终端） | 脚本里抓快照 |
| `-n 次数` | 刷新几次后退出 | 配合 `-b`，如 `top -b -n 1` |
| `-d 秒` | 设刷新间隔 | `top -d 1` 每秒刷新 |
| `-u 用户` | 只看某用户的进程 | 只盯一个人 |
| `-p PID` | 只看某几个 PID | 盯指定进程 |
| `-o 字段` | 启动时就按某列排序 | `top -o %CPU` |
| `-1` | 展开每个 CPU 核心 | 看多核占用 |
| `-H` | 显示线程 | 看多线程程序 |
| `-c` | 显示完整命令行 | 看完整启动参数 |

### 2. top 交互键（启动后按 `h` 看到的真实帮助）

下面是本机启动 `top` 后按 `h` 抓到的真实帮助原文：

```text
Help for Interactive Commands - procps-ng 3.3.17
Window 1:Def: Cumulative mode Off.  System: Delay 3.0 secs; Secure mode Off.
  Z,B,E,e   Global: 'Z' colors; 'B' bold; 'E'/'e' summary/task memory scale
  l,t,m,I   Toggle: 'l' load avg; 't' task/cpu; 'm' memory; 'I' Irix mode
  0,1,2,3,4 Toggle: '0' zeros; '1/2/3' cpu/numa views; '4' cpus two abreast
  f,F,X     Fields: 'f'/'F' add/remove/order/sort; 'X' increase fixed-width
  L,&,<,> . Locate: 'L'/'&' find/again; Move sort column: '<'/'>' left/right
  R,H,J,C . Toggle: 'R' Sort; 'H' Threads; 'J' Num justify; 'C' Coordinates
  c,i,S,j . Toggle: 'c' Cmd name/line; 'i' Idle; 'S' Time; 'j' Str justify
  x,y     . Toggle highlights: 'x' sort field; 'y' running tasks
  z,b     . Toggle: 'z' color/mono; 'b' bold/reverse (only if 'x' or 'y')
  u,U,o,O . Filter by: 'u'/'U' effective/any user; 'o'/'O' other criteria
  n,#,^O  . Set: 'n'/'#' max tasks displayed; Show: Ctrl+'O' other filter(s)
  V,v     . Toggle: 'V' forest view; 'v' hide/show forest view children
  k,r       Manipulate tasks: 'k' kill; 'r' renice
  d or s    Set update interval
  W,Y,!     Write config file 'W'; Inspect other output 'Y'; Combine Cpus '!'
  q         Quit
```

最该记住的几个键：

| 键 | 作用 |
|---|---|
| `h` 或 `?` | 调出帮助（就是上面这个屏） |
| `q` | 退出 |
| `P` | 按 **CPU** 占用排序（大写 P） |
| `M` | 按 **内存** 占用排序（大写 M） |
| `N` | 按 PID 排序 |
| `T` | 按累计时间排序 |
| `1` | 展开/收起每个 CPU 核心 |
| `k` | 杀进程（先输 PID 再输信号） |
| `r` | 改进程 nice 值 |
| `u` | 只看某用户 |
| `f` | 选要显示哪些列 |
| `d`/`s` | 改刷新间隔 |
| `W` | 保存当前设置成默认 |

> 注意：`R` 是**反转排序方向**（升/降切换）；`P`/`M`/`N`/`T` 是直接切到按某列排序。

### 3. htop 命令行选项（对照 `htop --help`）

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-d 毫秒` | 刷新延迟（十分之一秒） | `htop -d 10` = 1 秒 |
| `-p PID` | 只看指定 PID | 盯进程 |
| `-u 用户` | 只看某用户 | 过滤 |
| `-t` | **树形**显示 | 看父子关系 |
| `-s 列` | 按列排序 | `htop -s PERCENT_CPU` |
| `-C` | 单色（无颜色） | 不支持颜色的终端 |
| `-h` | 帮助 |  |

> htop 启动后按 `F1` 看在线帮助；底部有快捷键提示（F5 树形、F6 排序、F9 杀进程）。

## 四、由浅入深的典型示例

### 示例 1：直接启动 top（最常用）

```bash
top
```

启动后你看到的第一屏（本机实跑）：

```text
top - 23:28:40 up  1:01,  0 users,  load average: 0.21, 0.24, 0.14
Tasks:  37 total,   1 running,  36 sleeping,   0 stopped,   0 zombie
%Cpu(s):  0.0 us,  0.0 sy,  0.0 ni,100.0 id, 0.0 wa, 0.0 hi, 0.0 si, 0.0 st
MiB Mem :   8129.6 total,   3219.5 free,   569.6 used, 4340.6 buff/cache
MiB Swap:      0.0 total,      0.0 free,      0.0 used.   7429.9 avail Mem

  PID USER      PR  NI    VIRT    RES    SHR S  %CPU  %MEM     TIME+ COMMAND
    2 root      20   0 1349248  62084  34052 S   0.0   0.7   0:08.07 runtime-a+
 1277 user      20   0  310964 104860  27392 S   0.0   1.3   0:02.69 python-se+
```

顶部几行读法：
- `load average: 0.21, 0.24, 0.14`：1/5/15 分钟平均负载；
- `Tasks: 37 total, 1 running...`：共 37 个进程；
- `%Cpu(s): ... 100.0 id`：id=空闲比例，这里 CPU 几乎全闲；
- `MiB Mem`：内存总量/空闲/已用/缓存。

下面表格列：`PID`、`USER`、`%CPU`、`%MEM`、`RES`(真实内存)、`COMMAND`。

### 示例 2：批处理模式抓一张快照（脚本用）

```bash
top -b -n 1
```

> `-b` 不进交互屏、直接把一屏输出到终端；`-n 1` 只刷新一次就退出。监控脚本里常用它抓数据。

### 示例 3：启动就按 CPU 排序

```bash
top -b -n 1 -o %CPU
```

```text
  PID USER      PR  NI    VIRT    RES    SHR S  %CPU  %MEM     TIME+ COMMAND
    2 root      20   0 1349248  63352  34052 S   0.0   0.8   0:09.87 runtime-a+
 1277 user      20   0  310964 104860  27392 S   0.0   1.3   0:03.02 python-se+
```

> `-o %CPU` 启动即按 CPU 排。交互里等价于按 `P`。

### 示例 4：只看某用户的进程

```bash
top -b -n 1 -u user
```

```text
  PID USER      PR  NI    VIRT    RES    SHR S  %CPU  %MEM     TIME+ COMMAND
 1277 user      20   0  310964 104860  27392 S   0.0   1.3   0:03.02 python-se+
 1280 user      20   0    7344   3072   2432 S   0.0   0.0   0:00.00 websocat
 1283 user      20   0 1263524  37420  19584 S   0.0   0.4   0:00.57 gost
```

> `-u user` 过滤出 user 的进程。交互里等价于按 `u` 再输用户名。

### 示例 5：交互中按 M 切到内存排序

```bash
top
# 启动后按 M
```

> 启动后按 `M`，列表立刻按 `%MEM` 从大到小排；按 `P` 切回 CPU 排序；按 `R` 反转方向。这是排查「内存飙高」的标准动作。

### 示例 6：交互中按 1 展开每个 CPU 核心

```bash
top
# 启动后按 1
```

> 单核机器只有一行 `%Cpu(s)`；多核按 `1` 后会展开成 `%Cpu0`、`%Cpu1`... 每个核心一行，看是不是某个核心打满了。

### 示例 7：交互中按 k 杀进程

```bash
top
# 启动后按 k，输入 PID，回车，再输入信号（默认 15），回车
```

> 按 `k` 后 top 会提示你输要杀的 PID，然后输信号（默认 15=SIGTERM 温柔退出，不行再 9=SIGKILL）。比另开终端敲 kill 方便。

### 示例 8：用 htop 看树形

```bash
htop -t
```

> `-t` 树形显示父子关系，配合颜色比 top 直观。底部 F5 切换树形、F6 选排序列、F9 杀进程。没有 htop 的服务器用 `top` 也完全够。

### 示例 9：改刷新间隔

```bash
top
# 启动后按 d 或 s，输入秒数（如 0.5）
```

> 默认 3 秒刷新一次，排障时太快晃眼、太慢看不清，按 `d` 改成合适间隔。

## 五、高频组合速记

| 命令/键 | 用途 |
|---|---|
| `top` | 启动实时监控（**最常用**） |
| `top -b -n 1` | 脚本里抓一次快照 |
| `top -o %CPU` | 启动即按 CPU 排 |
| `top -u 用户` | 只看某用户 |
| `htop` | 彩色增强版（有就用它） |
| `htop -t` | htop 树形 |
| 交互 `P` | 按 CPU 排序 |
| 交互 `M` | 按内存排序 |
| 交互 `1` | 展开 CPU 核心 |
| 交互 `k` | 杀进程 |
| 交互 `q` | 退出 |

## 六、RHEL 系与 Debian 系差异

- `top` 都是 procps-ng，交互键一致；
- `htop` 两系都要单独装：`apt install htop` / `yum install htop`；
- RHEL 老版本 top 的默认颜色和列可能略不同，按 `h` 看本机真实键位为准。

## 七、新手易错点

1. **`top` 是交互程序，别忘 `q` 退出**：它不会自己回到命令行，按 `q` 或 `Ctrl+C`。
2. **load average 不是 CPU 使用率**：load 是「排队等 CPU 的任务数」，几核就看几（如 4 核机器 load 4.0 才算满），别拿 load 1.0 当满载。
3. **`%wa` 高是磁盘瓶颈**：CPU 列里 wa(iowait) 高说明进程在等磁盘，不是 CPU 不够。
4. **杀进程先用 15 再用 9**：`k` 默认 15 让程序优雅退出；直接 9 可能丢数据。
5. **RES 才是真实物理内存**：VIRT 是虚拟内存，别被它吓到。
6. **`top` 需要等几秒才准**：刚启动时 %CPU 是从上一次刷新算的，停留几秒再看才准。
7. **危险：在 top 里按 `k` 杀错 PID**：杀之前先确认 COMMAND 列是你要杀的进程，别把 PID 看串行。

## 八、相关命令与文档

- 速查页：[Linux 命令速查](../linux-commands#进程查看)
- 一次性看进程快照：见 [ps](./ps)
- 找进程 PID：见 [process-find](./process-find)
- 杀进程/发信号：见 [process-signal](./process-signal)
- 文件占用：见 [lsof](./lsof)
- 性能分析专题：[Linux 性能调优](../../guide/linux-performance)、[Linux 进程管理](../../guide/linux-process)
