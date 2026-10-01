# dmesg、uname 与 lsmod/modprobe 详解：看内核日志、系统信息和内核模块

> 本文是 [Linux 命令速查](../linux-commands#内核与系统) 中 `dmesg`、`uname`、`lsmod`、`modprobe` 的从 0 到 1 详解。
> 目标：把 `dmesg -T/-w/-l`、`uname -a/-r`、`lsmod`/`modprobe -r` 的用法讲清楚，多看几遍后，你在服务器上敲 `dmesg -T | tail` 就知道怎么看内核启动日志。
> 环境依据：`dmesg`/`lsblk` 属 util-linux 2.37.2；`uname` 属 GNU coreutils 8.32（Ubuntu 22.04 自带）；`lsmod`/`modprobe` 属 kmod 包（本机沙箱未安装，选项依据 kmod 官方 man modprobe(8) / lsmod(8)）。

## 一、命令是干什么的

四个命令都和"内核"打交道：

- **`dmesg`**（display message）：查看**内核环形缓冲区**里的日志——硬件检测、驱动加载、磁盘识别、OOM、内核报错都在这里。开机时的"黑底白字滚动信息"就是它。
- **`uname`**（unix name）：打印系统基本信息——内核版本、硬件架构、主机名。
- **`lsmod`**（list modules）：列出**当前已加载的内核模块**（驱动）。
- **`modprobe`**：加载或卸载内核模块，自动处理依赖。

> 类比：`dmesg` 是内核的"体检报告滚动日志"；`uname` 是"系统名片"；`lsmod` 是"当前插着哪些驱动"；`modprobe` 是"拔插驱动的开关"。

## 二、命令语法

```bash
dmesg [选项]
uname [选项]
lsmod
modprobe [选项] 模块名 [参数...]
```

- `dmesg` 不带参数：打印内核环形缓冲区全部日志（很多，配合 `less`/`tail`）；
- `uname` 不带参数：只打印内核名（`Linux`）；
- `lsmod` 不带参数：列出已加载模块；
- `modprobe 模块名`：加载模块；`modprobe -r 模块名`：卸载。

## 三、选项全表（对照 `--help` 与官方文档）

### 1. dmesg 常用选项

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-T`，`--ctime` | 用**人类可读时间**打印时间戳 | 看日志发生在几点（注意：挂起后可能不准） |
| `-w`，`--follow` | 持续等待并打印新日志 | 实时盯内核日志（类似 `tail -f`） |
| `-W`，`--follow-new` | 只打印之后新产生的日志 | 不看历史、只盯新增 |
| `-l 级别`，`--level=` | 只显示指定级别（err/warn/info...） | 只看错误/警告（最常用） |
| `-f 设施`，`--facility=` | 只显示指定设施（kern/daemon...） | 按来源过滤 |
| `-x`，`--decode` | 把 facility/level 解码成可读字符串 | 输出更易读 |
| `-H`，`--human` | 人类可读 + 自动分页 | 浏览全部日志 |
| `-d`，`--show-delta` | 显示日志间的时间差 | 看事件间隔 |
| `-e`，`--reltime` | 显示相对时间 | 看距开机多久 |
| `-t`，`--notime` | 不显示时间戳 | 只要消息正文 |
| `-C`，`--clear` | **清空**内核环形缓冲区 | 排障后清空（谨慎） |
| `-c`，`--read-clear` | 读完后清空 | 取完日志清掉 |
| `--since 时间`/`--until 时间` | 只显示某时间段 | 精准捞日志 |

> 日志级别（由重到轻）：`emerg` > `alert` > `crit` > `err` > `warn` > `notice` > `info` > `debug`。

### 2. uname 常用选项

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-a`，`--all` | 一次性打印全部信息 | 最快概览（最常用） |
| `-r`，`--kernel-release` | 只打印**内核版本号** | 找内核模块目录（最常用） |
| `-s`，`--kernel-name` | 内核名（Linux） | 默认行为 |
| `-n`，`--nodename` | 主机名 | 等价 `hostname` |
| `-m`，`--machine` | 硬件架构（x86_64） | 看是 64 位还是 arm |
| `-v`，`--kernel-version` | 内核编译版本 | 较少用 |
| `-p`，`--processor` | CPU 类型 | 可能 unknown |
| `-i`，`--hardware-platform` | 硬件平台 | 可能 unknown |
| `-o`，`--operating-system` | 操作系统名（GNU/Linux） | 较少用 |

### 3. lsmod 与 modprobe 常用选项

| 命令/选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `lsmod` | 列出已加载模块（读 `/proc/modules`） | 看加载了哪些驱动 |
| `modprobe 模块名` | 加载模块（自动加依赖） | 加载驱动 |
| `modprobe -r`，`--remove` | 卸载模块（连同没用的依赖） | 卸载驱动 |
| `modprobe -v`，`--verbose` | 打印正在做什么 | 调试加载失败 |
| `modprobe -n`，`--dry-run` | 只演练不真的加载/卸载 | 先预览（安全） |
| `modprobe -q`，`--quiet` | 找不到模块时不报错 | 脚本里静默 |
| `modprobe -f`，`--force` | 强制加载（跳过版本校验） | 危险，慎用 |
| `modprobe -a`，`--all` | 一次加载多个模块 | 批量加载 |

## 四、由浅入深的典型示例

### 示例 1：看系统全部信息

```bash
uname -a
```

```text
Linux vefaas-...-sandbox 6.6.95.bck.2-rc1-amd64 #rc1 SMP Debian 6.6.95... x86_64 x86_64 x86_64 GNU/Linux
```

逐段拆：

- `Linux`：内核名；
- `vefaas-...`：主机名（`-n`）；
- `6.6.95.bck.2-rc1-amd64`：**内核版本号**（`-r`，模块目录就对应这个版本）；
- `x86_64`：硬件架构（64 位）；
- `GNU/Linux`：操作系统。

### 示例 2：只看内核版本号

```bash
uname -r
```

```text
6.6.95.bck.2-rc1-amd64
```

> 内核模块都装在 `/lib/modules/$(uname -r)/` 下，写脚本时常用这个命令动态取版本。

### 示例 3：看最近的内核日志

```bash
dmesg -T | tail -20
```

```text
[Wed Sep 30 22:27:13 2026] Linux version 6.6.95.bck.2-rc1-amd64 (STE-Kernel@ByteDance) ...
[Wed Sep 30 22:27:13 2026] Command line: reboot=k ... root=/dev/pmem0p1 ...
[Wed Sep 30 22:27:13 2026] x86/split lock detection: #DB: warning on user-space bus_locks
```

> `-T` 把开机相对时间换成可读的日期时间；`tail` 看最近的几十条。

### 示例 4：只看错误级日志

```bash
dmesg -T -l err
```

```text
[    0.001284] ACPI BIOS Error (bug): A valid RSDP was not found (20230628/tbxfroot-222)
```

> 排障时先看 `err`/`warn`，能快速定位硬件或驱动报错。

### 示例 5：实时盯内核新日志

```bash
sudo dmesg -w
```

> 像 `tail -f /var/log/messages` 一样持续滚动新日志；插盘、OOM、驱动报错会实时冒出来，按 `Ctrl+C` 停止。

### 示例 6：检索关键词

```bash
dmesg -T | grep -i -E 'error|fail|oom|ext4|xfs'
```

> 内核日志动辄上千行，`grep` 关键词是必须的。

### 示例 7：列出已加载模块

```bash
lsmod
```

示意输出（依据 kmod 常见输出，非本机实跑）：

```text
Module                  Size  Used by
vsock                 45056  0
vmw_vsock_virtio_transport_common    16384  0
virtio_net            45056  0
xfs               12300288  1
```

- 第 1 列：模块名；
- 第 2 列：大小；
- 第 3 列：被多少模块/进程使用；
- 最后一列：被哪些模块依赖。

### 示例 8：加载与卸载模块（先演练）

```bash
# 先演练，不真的加载
sudo modprobe -n -v dummy
# 真的加载
sudo modprobe dummy
# 用完卸载
sudo modprobe -r dummy
```

> `-n -v` 是安全习惯：先看它要干什么，再真的执行。`modprobe` 会自动把依赖模块一起加载。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `uname -a` | 看全部系统信息 |
| `uname -r` | 只看内核版本 |
| `dmesg -T \| tail -20` | 看最近内核日志（**最常用**） |
| `dmesg -T -l err` | 只看错误 |
| `dmesg -w` | 实时盯新日志 |
| `dmesg -T \| grep -i oom` | 找 OOM 记录 |
| `lsmod` | 看已加载模块 |
| `modprobe 模块名` / `modprobe -r 模块名` | 加载/卸载驱动 |

## 六、RHEL 系与 Debian 系差异

- `uname`、`dmesg` 属 coreutils/util-linux，**两系用法一致**。
- `lsmod`/`modprobe` 属 kmod，两系命令相同；模块配置目录都是 `/etc/modprobe.d/*.conf`。
- RHEL/CentOS 常见根文件系统是 `xfs`，Debian/Ubuntu 是 `ext4`，`dmesg` 里看到的文件系统名不同。
- 内核模块加载策略：开机自动加载的模块列表在 `/etc/modules`（Debian）或 `/etc/modules-load.d/*.conf`（两系通用）。
- 容器里 `dmesg` 可能受限或为空，`modprobe` 一般不可用（内核模块通常不能在容器里加载）。

## 七、新手易错点

1. **`dmesg` 不加 `-T` 时间是开机秒数**：`[    0.000000]` 是开机后的秒数，不是时钟时间，加 `-T` 才是日期。
2. **`dmesg -T` 在挂起/休眠后可能不准**：内核提示过 may be inaccurate，重要时间点要结合 `journalctl`。
3. **`dmesg -C` 会清空日志**：排障完想清空可以，但别在别人查问题时随手清。
4. **`lsmod` 第三列非 0 时不能卸载**：模块还被用着，`modprobe -r` 会失败。
5. **`modprobe -f` 强载模块有风险**：版本不匹配的模块可能导致内核崩溃，非必要不用。
6. **这些命令大多需要 root**：普通用户可能读不到 dmesg（受 `kernel.dmesg_restrict` 限制）。

## 八、相关命令与文档

- 速查页：[Linux 命令速查](../linux-commands)
- 调内核参数：`sysctl`（详解见 [sysctl-ulimit](./sysctl-ulimit)）
- 看系统日志：`journalctl`、`/var/log/messages`
- 内核调优：见 [Linux 内核专题](../../guide/linux-kernel)
