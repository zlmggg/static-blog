# ps 命令详解：查看系统里正在跑哪些进程

> 本文是 [Linux 命令速查](../linux-commands#进程查看) 中 `ps` 的从 0 到 1 详解。
> 目标：把 `ps --help` 里的每个选项讲清楚，尤其是 `aux`、`-ef`、`-e`、`-o`、`--sort` 这几个高频写法，多看几遍后，你在服务器上敲 `ps --help` 就知道该用哪个选项。
> 环境依据：procps-ng 3.3.17（Ubuntu 22.04 自带；RHEL/Rocky 自带的 procps-ng 版本略旧，核心选项一致）。

## 一、命令是干什么的

`ps` = **process status**（进程状态），用来列出当前系统里**正在运行的进程**快照。它是「这一瞬间」的照片，不是实时刷新的（要实时刷新用 `top`）。

- 不加参数：只列**当前终端**的进程；
- `ps aux`：列出**所有**进程（BSD 风格，最常用）；
- `ps -ef`：列出所有进程（System V 风格，也很常用）；
- `ps -o 字段`：自定义要显示哪些列。

> 类比：就像 Windows 任务管理器的「进程」标签页，只不过 ps 是命令行、输出纯文本，方便管道给 grep/awk。
>
> 排障第一反应：「那个服务起没起来？占了多少 CPU/内存？」——先 `ps`。

## 二、命令语法

```bash
ps [选项]
```

`ps` 的特殊之处：它同时兼容 **BSD 风格**（选项不加横杠，如 `aux`）和 **System V 风格**（选项加横杠，如 `-ef`）。所以你会看到 `ps aux` 和 `ps -ef` 两种写法都对。

## 三、选项全表（对照 `ps --help` 分档）

`ps` 选项分好几组，下面按真实 `ps --help simple/list/output/misc` 分组列。

### 1. 选「列哪些进程」（simple）

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-A`，`-e` | **所有**进程 | 看全部（最常用） |
| `-a` | 所有有终端的进程（除会话首进程） | 看别人在终端干啥 |
| `x` | 列出**没有控制终端**的进程 | 看后台守护进程（常和 `-a` 配成 `ax`） |
| `r` | 只列**正在运行**的 | 排除睡眠的 |
| `T` | 当前终端上的所有进程 | 只看自己终端 |
| `-d` | 所有进程（除会话首进程） | 较少用 |
| `-N`，`--deselect` | **反向**选择 | 排除匹配项 |

> `aux` 三个字母其实是三件套：`a`(所有有终端) + `x`(无终端的也列) + `u`(用户友好格式)。合起来就是「全部进程 + 详细列」。

### 2. 按条件筛选进程（list）

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-u 用户`，`-U 用户` | 只列某**用户**的进程 | `ps -u root` |
| `-p PID`，`--pid PID` | 只列指定 PID | 查某个进程详情 |
| `-C 命令名` | 按**命令名**列 | `ps -C nginx` |
| `--ppid PID` | 只列某进程的**子进程** | 找父进程下的所有进程 |
| `-g 组` | 按组/会话列 | 较少用 |
| `--tty 终端` | 按终端列 | 看某登录终端 |

### 3. 控制「显示成什么样」（output）

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-f` | **完整格式**（带命令行参数、PPID） | `-ef` 的 f |
| `-e` | 全进程（配 `-f` 就是 `-ef`） | 最常用组合 |
| `u` | **用户友好格式**（%CPU/%MEM） | `aux` 的 u |
| `-o 字段`，`--format 字段` | **自定义列** | `ps -o pid,user,comm` |
| `-F` | 额外完整 | 比 `-f` 更详细 |
| `f`，`--forest` | **ASCII 树状**显示父子关系 | 看进程树 |
| `-H` | 显示进程层级 | 配合树看 |
| `-j` | jobs 格式 | 看会话/进程组 |
| `-l` | 长格式 | 看调度信息 |
| `--no-headers` | 不打印表头 | 脚本取数据 |
| `L` | 列出所有可用字段名 | 记不住字段名时查 |

### 4. 排序与其他（misc）

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `--sort=字段`，`k 字段` | 按字段**排序**，`-` 表示降序 | `--sort=-%cpu` 找最耗 CPU 的 |
| `S`，`--cumulative` | 含已退出子进程数据 | 较少用 |
| `e` | 显示进程的环境变量 | 排查服务配置 |
| `w`，`-w` | 不截断输出宽度 | 命令行太长看不全时 |
| `H` | 把**线程**也当进程列 | 看多线程程序 |
| `-L` | 显示线程（带 LWP/NLWP 列） | 看线程数 |
| `n` | UID/wchan 用数字显示 | 较少用 |

## 四、由浅入深的典型示例

### 示例 1：最经典——看全部进程

```bash
ps aux
```

```text
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.0  0.0    876   384 ?        Ss   22:27   0:00 /usr/local/bin/dumb-init -c -- ...
root         2  0.2  0.7 1349248 63352 ?       Sl   22:27   0:09 runtime-agent /opt/bytefaas/run.sh
root        14  0.0  0.0   11520 4608 ?       S    22:47   0:00 /bin/bash ./entrypoint.sh
```

逐列读：`USER` 谁跑的、`PID` 进程号、`%CPU` 占 CPU、`%MEM` 占内存、`RSS` 实际物理内存(KB)、`STAT` 进程状态（S 睡眠、R 运行、Z 僵尸）、`COMMAND` 启动命令。

### 示例 2：另一种经典写法 -ef

```bash
ps -ef
```

```text
UID        PID  PPID  C STIME TTY          TIME CMD
root         1     0  0 22:27 ?        00:00:00 /usr/local/bin/dumb-init -c -- ...
root         2     1  0 22:27 ?        00:00:09 runtime-agent /opt/bytefaas/run.sh
root        14     2  0 22:47 ?        00:00:00 /bin/bash ./entrypoint.sh
```

> `-ef` 和 `aux` 都列全部进程，区别是 `-ef` 多了 `PPID`（父进程号）列。查「谁是它爸」用 `-ef`。

### 示例 3：管道 grep 找特定进程

```bash
ps aux | grep nginx
```

> 这是最高频的组合：先列全部，再 grep 出关心的。注意 grep 自己也会出现在结果里，可用 `grep [n]ginx` 或 `pgrep` 避免。

### 示例 4：只看某个用户的进程

```bash
ps -u root -o pid,ppid,comm --no-headers
```

```text
    1     0 dumb-init
    2     1 runtime-agent
   14     2 entrypoint.sh
  446    14 vm_runtime_hook
  456    14 gem.sh
```

> `-u root` 只列 root 的进程；`-o pid,ppid,comm` 只要这三列；`--no-headers` 去掉表头（脚本友好）。

### 示例 5：按命令名精确查

```bash
ps -C nginx -o pid,user,cmd
```

```text
  PID USER     CMD
 1279 root     nginx: master process /usr/sbin/nginx -c /opt/gem/nginx.conf -g daemon off;
 1543 nobody   nginx: worker process
```

> `-C nginx` 按命令名过滤，比 `ps aux | grep nginx` 更准（不会把 grep 自己带进来）。

### 示例 6：自定义列 + 按内存排序

```bash
ps -eo pid,user,%mem,rss,comm --sort=-%mem | head -6
```

```text
  PID USER     %MEM   RSS COMMAND
 1330 user      3.0 256404 chrome
 1277 user      1.2 104860 python-server
 1619 user      1.2 100244 chrome
 1589 user      1.1  94720 chrome
 1288 user      1.0  89856 Xvnc
```

> `-eo` 自定义列，`--sort=-%mem` 按内存**降序**（负号=从大到小），`head` 取前几名。找「谁吃内存最多」就这么干。同理 `--sort=-%cpu` 找最耗 CPU 的。

### 示例 7：看进程树（谁是谁的子进程）

```bash
ps -ef --forest
```

```text
root         1     0  ... /usr/local/bin/dumb-init -c -- ...
root         2     1  ... runtime-agent /opt/bytefaas/run.sh
root        14     2  ...  \_ /bin/bash ./entrypoint.sh
root       446    14  ...      \_ /runtime/mcp_vm_server/vm_runtime_hook --host 127.0.0.1 --port 10080
root       477     1  ... python3 /opt/gem/browser-supervisor.py
root      1279  1276 ...      \_ nginx: master process ...
nobody    1543  1279 ...          \_ nginx: worker process
```

> `--forest` 用 `\_` 画出父子关系，一眼看清「谁启动了谁」。比单独看 PPID 直观得多。

### 示例 8：查某 PID 的详情

```bash
ps -p 1279 -o pid,ppid,user,stat,%cpu,%mem,cmd
```

> `-p` 指定 PID，`-o` 要哪些列。找到一个可疑进程后，用它看它的父进程(PPID)、状态、资源占用。

### 示例 9：看线程

```bash
ps -eLf --no-headers | wc -l
```

> `-L` 把线程也列出来（带 LWP 线程号列）。数一下总线程数，排查「线程数爆了」类问题。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `ps aux` | 看全部进程（BSD 风格，**最常用**） |
| `ps -ef` | 看全部进程（System V 风格，带 PPID） |
| `ps aux \| grep 名字` | 找某进程 |
| `ps -u 用户` | 看某用户的进程 |
| `ps -C 命令名` | 按命令名精确查 |
| `ps -eo pid,user,comm --sort=-%cpu` | 找最耗 CPU 的 |
| `ps -eo pid,user,comm --sort=-%mem` | 找最耗内存的 |
| `ps -ef --forest` | 看进程树 |
| `ps -p PID -o ...` | 查指定 PID 详情 |

## 六、RHEL 系与 Debian 系差异

`ps` 属 procps-ng，**两系用法完全一致**。仅有的细微点：

- RHEL 老版本（CentOS 7）是 procps-ng 3.3.10，少数新字段名可能不同，以本机 `ps --help` 为准；
- `aux`/`-ef`/`-o`/`--sort` 这些核心写法两系通用。

## 七、新手易错点

1. **`ps` 是快照不是实时**：它只拍一张照片，要持续刷新看 `top`。
2. **`ps aux | grep xxx` 会把 grep 自己列出来**：这是正常现象，不是 bug；想避开用 `pgrep` 或 `grep [x]xx`。
3. **STAT 列要会读**：`R` 运行、`S` 可中断睡眠（最常见）、`Z` 僵尸进程、`s` 是会话首进程、`+` 是前台进程。
4. **RSS 才是真实物理内存**：VSZ 是虚拟内存（含交换库等），别拿 VSZ 当内存占用。
5. **别用 `ps -ef | kill`**：ps 只是查，杀进程用 `kill PID` 或 `pkill 名字`。
6. **`-ef` 和 `aux` 别混写成 `-aux`**：历史上 `ps aux` 和 `ps -aux` 在老系统含义不同，现在一般都行，但养成习惯写 `ps aux` 或 `ps -ef`。
7. **找进程先想 pgrep**：`ps aux | grep` 能做的，`pgrep -a 名字` 更干净（见 [process-find](./process-find)）。

## 八、相关命令与文档

- 速查页：[Linux 命令速查](../linux-commands#进程查看)
- 实时刷新看资源：见 [top 与 htop](./top)
- 找进程 PID：见 [process-find](./process-find)
- 杀进程/发信号：见 [process-signal](./process-signal)
- 后台/作业：见 [job-control](./job-control)
- 进程专题：[Linux 进程管理](../../guide/linux-process)
