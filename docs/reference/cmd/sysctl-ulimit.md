# sysctl 与 ulimit 命令详解：调内核参数和进程资源上限

> 本文是 [Linux 命令速查](../linux-commands#内核与系统) 中 `sysctl`、`ulimit` 的从 0 到 1 详解。
> 目标：把 `sysctl -a/-w/-p` 读写内核参数、`ulimit -a/-n/-u` 查改文件句柄数等上限讲清楚，多看几遍后，你在服务器上敲 `sysctl -a` 就知道怎么调内核。
> 环境依据：`sysctl` 属 procps-ng 3.3.17；`ulimit` 是 bash 内建命令（随 bash 提供）。Ubuntu 22.04 自带，RHEL/Rocky 用法一致。

## 一、命令是干什么的

两个命令都和"系统资源限制"有关，但管的对象不同：

- **`sysctl`**：查看和**动态修改内核参数**（/proc/sys 下的一堆开关）。比如开启 IP 转发、调整 `file-max`、`somaxconn`、`vm.overcommit_memory`。它管的是**整个内核的全局设置**。
- **`ulimit`**：bash 内建命令，查看/设置**当前 shell 及其子进程**的资源上限（能打开多少文件、能起多少进程、core 文件多大等）。它管的是**当前 shell 会话**。

> 类比：`sysctl` 像"整个城市的交通信号灯调度系统"（全局规则）；`ulimit` 像"给你这张门禁卡设的每次最多进几个人"（只对你和你后面开的进程生效）。

## 二、命令语法

```bash
# sysctl
sysctl [选项]... [变量[=值] ...]

# ulimit（bash 内建）
ulimit [选项] [新值]
```

- `sysctl 变量`：只看某个内核参数当前值；`sysctl 变量=值`：临时写一个新值；
- `ulimit -a`：打印当前 shell 的所有上限；`ulimit -n 65535`：把打开文件数上限改成 65535。

## 三、选项全表（对照 `--help` 与 `help ulimit`）

### 1. sysctl 常用选项

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-a`，`--all` | 显示**所有**内核参数 | 浏览/检索参数 |
| `-n`，`--values` | 只打印值，不打印变量名 | 脚本取值 |
| `-N`，`--names` | 只打印变量名 | 列参数名 |
| `-w`，`--write` | 允许写入新值（`变量=值`） | 临时改内核参数 |
| `-p 文件`，`--load[=文件]` | 从配置文件加载参数 | 开机加载 `/etc/sysctl.conf` |
| `--system` | 从所有系统目录加载 | 重载全部 sysctl.d 配置 |
| `-r 表达式`，`--pattern=` | 按正则匹配参数 | `sysctl -r '^net.ipv4.ip_forward'` |
| `-e`，`--ignore` | 忽略未知变量的报错 | 脚本容错 |
| `-q`，`--quiet` | 设置时不回显 | 安静加载 |
| `-b`，`--binary` | 输出不带换行 | 较少用 |

> 常见关键参数：`net.ipv4.ip_forward`（路由转发）、`vm.overcommit_memory`（内存分配策略）、`fs.file-max`（系统级文件句柄总数）、`net.core.somaxconn`（连接队列）、`kernel.hostname`（主机名）。

### 2. ulimit 常用选项（bash 内建）

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-a` | 显示**所有**当前上限 | 一次性看全（最常用） |
| `-n` | 最大打开**文件描述符**数 | 调"too many open files"（最常用） |
| `-u` | 最大**用户进程/线程**数 | 调 fork 上限 |
| `-c` | core 文件最大大小 | 想留 core dump 时设 |
| `-f` |  shell 能写的最大文件大小 | 限制写文件 |
| `-l` | 能锁进内存的最大大小 | 共享内存/DPDK 时 |
| `-s` | 栈大小 | 较少改 |
| `-v` | 虚拟内存大小 | 较少改 |
| `-t` | CPU 时间（秒） | 极少用 |
| `-m` | 最大驻留内存 | 多数系统已忽略 |
| `-H` | 操作**硬**限制（只有 root 能提高） | 设硬上限 |
| `-S` | 操作**软**限制（用户可在硬限内调） | 设软上限 |

> 软限制（soft）是当前生效值，硬限制（hard）是用户能调到的天花板。不带 `-H`/`-S` 时，`ulimit` 同时设软硬。

## 四、由浅入深的典型示例

### 示例 1：查看某个内核参数

```bash
sysctl kernel.hostname
```

```text
kernel.hostname = vefaas-zb315afk-8qrzm5xu33-daui2200e1o0s3tbqng0-sandbox
```

> 等价于 `cat /proc/sys/kernel/hostname`。

### 示例 2：列出所有参数并检索

```bash
sysctl -a 2>/dev/null | grep -E '^(kernel.shmmax|vm.overcommit_memory|net.ipv4.ip_forward|fs.file-max)'
```

```text
fs.file-max = 9223372036854775807
kernel.shmmax = 18446744073692774399
net.ipv4.ip_forward = 0
vm.overcommit_memory = 0
```

> `-a` 输出几百项，配合 `grep` 找你关心的那几个。

### 示例 3：临时开启 IP 转发

```bash
sudo sysctl -w net.ipv4.ip_forward=1
```

```text
net.ipv4.ip_forward = 1
```

> 立刻生效，但**重启后丢失**。要永久生效需写进 `/etc/sysctl.conf` 或 `/etc/sysctl.d/*.conf`。

### 示例 4：永久生效——写配置并重载

编辑 `/etc/sysctl.d/99-forward.conf`：

```conf
net.ipv4.ip_forward = 1
vm.overcommit_memory = 1
```

然后重载：

```bash
sudo sysctl --system
# 或只加载某个文件
sudo sysctl -p /etc/sysctl.d/99-forward.conf
```

> `--system` 会把 `/etc/sysctl.conf`、`/etc/sysctl.d/*.conf` 全部重新加载一遍。

### 示例 5：查看当前 shell 的所有资源上限

```bash
ulimit -a
```

```text
core file size              (blocks, -c) 0
data seg size               (kbytes, -d) unlimited
scheduling priority                 (-e) 0
file size                   (blocks, -f) unlimited
pending signals                     (-i) 1768
max locked memory           (kbytes, -l) 8192
max memory size             (kbytes, -m) unlimited
open files                          (-n) 2048
pipe size                (512 bytes, -p) 8
POSIX message queues         (bytes, -q) 819200
real-time priority                  (-r) 0
stack size                  (kbytes, -s) 8192
cpu time                   (seconds, -t) unlimited
max user processes                  (-u) 1768
virtual memory              (kbytes, -v) unlimited
file locks                          (-x) unlimited
```

> 重点看 `open files (-n) 2048` 和 `max user processes (-u) 1768`——很多服务（MySQL、Java、高并发网关）默认 1024/2048 不够用。

### 示例 6：把打开文件数上限调高

```bash
ulimit -n 65535
ulimit -n
```

```text
65535
```

> 只对**当前 shell 及随后启动的进程**生效。要永久生效，写 `/etc/security/limits.conf` 或 `/etc/security/limits.d/*.conf`：
>
> ```conf
> *  soft  nofile  65535
> *  hard  nofile  65535
> ```

### 示例 7：查看/设置用户进程数上限

```bash
ulimit -u
ulimit -u 4096
```

> `-u` 限制当前用户能开多少进程/线程，碰到 "fork: Resource temporarily unavailable" 时检查它。

### 示例 8：放开 core dump

```bash
ulimit -c unlimited
```

> 让程序崩溃时能生成 core 文件（用于事后分析）。默认 `-c 0` 是不生成。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `sysctl -a \| grep 关键字` | 查内核参数 |
| `sysctl 变量名` | 看某参数当前值 |
| `sysctl -w 变量=值` | 临时改内核参数 |
| `sysctl --system` | 重载所有 sysctl 配置 |
| `ulimit -a` | 看当前 shell 所有上限 |
| `ulimit -n` | 看/改打开文件数 |
| `ulimit -u` | 看/改进程数上限 |

## 六、RHEL 系与 Debian 系差异

- **配置目录**：两系都用 `/etc/sysctl.conf`（软链或文件）+ `/etc/sysctl.d/*.conf`，`sysctl --system` 行为一致；RHEL 系历史上还会读 `/etc/sysctl.conf`，Debian 系同样兼容。
- **ulimit 永久配置**：两系都用 `/etc/security/limits.conf` 和 `/etc/security/limits.d/`，由 `pam_limits.so` 生效；systemd 管理的服务则用 `LimitNOFILE=` 在 unit 文件里设置（`/etc/systemd/system.conf` 或 drop-in）。
- 容器里 `sysctl -w` 很多参数被禁用（namespaces 限制），属正常。

## 七、新手易错点

1. **`sysctl -w` 改完重启就没了**：必须写进 `/etc/sysctl.d/*.conf` 并 `sysctl --system` 才永久。
2. **`ulimit` 只对当前 shell 生效**：新开终端、或 systemd 启动的服务不继承你的修改，要配 limits.conf 或 unit 的 `LimitNOFILE`。
3. **`ulimit -n` 调太高会失败**：受系统级 `fs.file-max` 和 `nr_open` 限制，不是想设多大就多大。
4. **把 `ulimit` 当系统全局命令**：它是 bash 内建，脚本用 `/bin/sh`（dash）时语法可能不同。
5. **改 `vm.overcommit_memory` 等参数要懂含义**：盲目照抄网上的调优参数可能适得其反。
6. **`sysctl` 写操作要 sudo**：普通用户只能看不能写。

## 八、相关命令与文档

- 速查页：[Linux 命令速查](../linux-commands)
- 看内核日志/版本：`dmesg`、`uname`（详解见 [dmesg-uname](./dmesg-uname)）
- 加载内核模块：`modprobe`（详解见 [dmesg-uname](./dmesg-uname)）
- 内核调优思路：见 [Linux 内核专题](../../guide/linux-kernel)、[性能专题](../../guide/linux-performance)
