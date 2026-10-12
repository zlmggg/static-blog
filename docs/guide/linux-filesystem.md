---
category: Linux
difficulty: 中级
---

# 文件系统

::: tip 本篇定位
理解 Linux 的目录组织、文件类型、inode、软硬链接和挂载机制。
这些是理解"文件存在哪、为什么磁盘没满却写不进、开机如何挂载"的基础。
:::

## 一、FHS 目录结构

Linux 各发行版遵循 **FHS（Filesystem Hierarchy Standard，文件系统层次化标准）**，目录用途统一。

| 目录 | 作用 |
|---|---|
| `/` | 根目录，所有目录的起点 |
| `/etc` | **系统和服务的配置文件**（纯文本），如 `/etc/passwd`、`/etc/nginx/` |
| `/var` | **经常变化的数据**：日志 `/var/log`、缓存 `/var/cache`、队列 `/var/spool`、运行库 `/var/lib` |
| `/home` | 普通用户的家目录，如 `/home/wiki` |
| `/root` | root 用户的家目录 |
| `/usr` | 软件资源：命令 `/usr/bin`、`/usr/sbin`；**本地编译安装放 `/usr/local`**；文档 `/usr/share` |
| `/bin` `/sbin` | 基础命令（现代系统已软链接到 `/usr/bin`、`/usr/sbin`）；sbin 多为管理员命令 |
| `/boot` | 引导文件：内核 `vmlinuz`、`initramfs`、grub |
| `/dev` | 设备文件：硬盘 `/dev/sda`、`/dev/null`（黑洞）、`/dev/zero`（零） |
| `/tmp` | 临时文件，**重启会清空**；`/var/tmp` 则保留 |
| `/opt` | 可选的第三方大型软件 |
| `/run` | 运行时数据（PID、socket），内存文件系统，重启清空 |
| `/mnt` `/media` | 挂载点：`/mnt` 手动临时挂载，`/media` 光盘/U 盘自动挂载 |
| `/lib` `/lib64` | 库文件与内核模块 |
| `/proc` `/sys` | 虚拟文件系统，见第六节 |

::: tip 记忆重点
配置找 `/etc`，日志找 `/var/log`，自己的东西放 `/home`，手动装的软件放 `/usr/local`，临时挂载用 `/mnt`。
:::

## 二、文件类型

`ls -l` 输出的**第一位字符**表示文件类型：

| 字符 | 类型 | 说明 / 例子 |
|---|---|---|
| `-` | 普通文件 | 文本、二进制程序、压缩包、图片等 |
| `d` | 目录 directory | 文件夹 |
| `l` | 软链接 symbolic link | 类似快捷方式，后面显示 `-> 目标` |
| `c` | 字符设备 character | 按字符流访问，如终端 `/dev/tty`、`/dev/null` |
| `b` | 块设备 block | 按块随机访问，如硬盘 `/dev/sda` |
| `p` | 命名管道 pipe | FIFO，用于进程间通信 |
| `s` | 套接字 socket | 进程/网络通信，如 `/run/docker.sock` |

判断文件真实类型：

```bash
file /etc/passwd          # 识别文件真实格式（不看扩展名）
stat /etc/passwd          # 查看详细元数据
ls -l /dev/sda /dev/null  # 观察 b、c 设备
```

## 三、inode

### 1. inode 与 block

文件在磁盘上由两部分组成：

- **block（数据块）**：存放文件实际内容，常见块大小 4KB。
- **inode（索引节点）**：存放文件**元数据**。

inode 中记录：文件大小、权限、属主、属组、时间戳、数据块的指针（位置）。
**inode 不含文件名**——文件名存在"上级目录"的 block 中，目录本质是一张 `文件名 → inode 号` 的映射表。

```bash
ls -i file          # 查看 inode 号
stat file           # 查看 inode 全部信息（含三个时间戳）
```

| 时间戳 | 含义 |
|---|---|
| `atime` | access，最后访问时间 |
| `mtime` | modify，内容最后修改时间（最常用） |
| `ctime` | change，inode/属性最后变更时间 |

### 2. inode 也会被耗尽

```bash
df -h       # 查看磁盘空间（block）使用
df -i       # 查看 inode 使用情况
```

每个文件至少占用一个 inode。当存在**海量小文件**（缓存目录、邮件队列、崩溃转储等）时，可能磁盘空间还没满，但 **inode 已耗尽（IUse% 100%），导致无法新建文件**。

排查思路：

```bash
df -i                          # 找到 IUse% 100% 的分区
find /path -xdev -type f | wc -l     # 统计某目录文件数量，定位小文件集中地
```

::: warning 经典故障现象
"No space left on device"，但 `df -h` 明明有空间——这时就要想到用 `df -i` 查 inode。
:::

## 四、硬链接与软链接

```bash
ln 相关选项 中文说明
ln --help
Usage: ln [OPTION]... [-T] TARGET LINK_NAME
  or:  ln [OPTION]... TARGET
  or:  ln [OPTION]... TARGET... DIRECTORY
  or:  ln [OPTION]... -t DIRECTORY TARGET...

在第一种形式中，创建一个指向TARGET的链接，链接名为LINK_NAME。  
在第二种形式中，创建一个指向当前目录下TARGET的链接。  
在第三种和第四种形式中，为DIRECTORY中的每个TARGET创建链接。  
默认情况下创建硬链接，使用--symbolic参数创建符号链接。  
默认情况下，每个目标（新链接的名称）不应已存在。  
创建硬链接时，每个TARGET必须已存在。符号链接可以包含任意文本；当后续解析时，相对链接将相对于其父目录进行解释。

长选项的必需参数对短选项也是必需的。
      --backup [=CONTROL]      # 为每个现有目标文件创建备份
  -b                          # 类似于 --backup，但不接受参数
  -d, -F, --directory         # 允许超级用户尝试硬链接目录（注意：由于系统限制，即使对超级用户也可能失败）
  -f, --force                 # 删除现有目标文件
  -i, --interactive           # 交互式确认删除现有目标文件
  -L, --logical               # 解引用符号链接的 TARGETs
  -n, --no-dereference        # 如果 LINK_NAME 是指向目录的符号链接，则将其视为普通文件
  -P, --physical              # 创建硬链接，而不是符号链接 直接将硬链接指向符号链接
  -r, --relative              # 创建相对链接（与链接所在目录相关），而不是绝对链接
  -s, --symbolic              # 创建符号链接（软链接），而不是硬链接
  -S, --suffix=SUFFIX         # 重写默认备份后缀 ~
  -t, --target-directory=DIRECTORY  # 在 DIRECTORY 目录下创建链接
  -T, --no-target-directory   # 如果 LINK_NAME 是指向目录的符号链接，则将其视为普通文件
  -v, --verbose               # 打印每个链接文件名
      --help        # 显示帮助信息并退出
      --version     # 输出版本信息并退出

备份后缀为 '~'，除非使用 --suffix 或 SIMPLE_BACKUP_SUFFIX 进行设置。  
版本控制方式可通过 --backup 选项或环境变量 VERSION_CONTROL 来选择。以下为可用值：

none, off       不创建备份（即使指定了 --backup）  
numbered, t     创建带编号的备份  
existing, nil   若存在带编号的备份，则创建编号备份；否则创建简单备份  
simple, never    始终创建简单备份  

使用 -s 时，-L 和 -P 会被忽略。否则，最后一个指定的选项将控制当目标为符号链接时的行为，默认为 -P。

GNU coreutils 在线帮助：https://www.gnu.org/software/coreutils/ 
完整文档： https://www.gnu.org/software/coreutils/ln 
```

### 1. 软链接（符号链接）

```bash
ln -s 目标路径 链接名
# 例：
ln -s /usr/local/python3.11 /usr/local/python3
readlink /usr/local/python3     # 查看软链接指向
```

软链接是一个**独立的文件**，内容是目标的路径（类似 Windows 快捷方式）：

- 可以跨文件系统、可以链接目录。
- 目标被删除后，软链接失效（红名/悬空链接）。

### 2. 硬链接

```bash
ln 源文件 硬链接名
# 例：
ln /data/a.txt /data/a.bak
ls -li /data/a.txt /data/a.bak   # 二者 inode 号相同，链接数为 2
```

硬链接让多个文件名指向**同一个 inode（同一份数据）**：

- 删除其中一个，只要链接数仍 > 0，数据还在。
- **不能跨文件系统，不能对目录创建**。

### 3. 对比

| 对比项 | 硬链接 | 软链接 |
|---|---|---|
| inode | 与源相同 | 独立的新 inode |
| 跨文件系统 | 不可以 | 可以 |
| 链接目录 | 不可以 | 可以 |
| 源删除后 | 数据仍在（链接数>0） | 链接失效 |
| 典型场景 | 防误删、多入口、省空间 | 版本切换、路径兼容、快捷方式 |

## 五、文件系统与挂载

### 1. 常见文件系统类型

| 类型 | 说明 |
|---|---|
| `xfs` | **RHEL/CentOS 7+ 默认**，高性能、适合大文件，支持在线扩容（不支持缩容） |
| `ext4` | **Debian/Ubuntu 默认**，稳定通用，支持缩容 |
| `swap` | 交换分区/交换文件 |
| `tmpfs` | 内存文件系统（如 `/dev/shm`、`/run`），重启清空 |
| `iso9660` | 光盘镜像 |
| `nfs` | 网络文件系统（远程挂载） |

### 2. 挂载与卸载

挂载 = 把一个设备（分区）与一个目录关联，访问该目录即访问设备内容。

```bash
mount                    # 查看当前所有挂载
sudo mount /dev/sdb1 /mnt/data        # 把 sdb1 挂载到 /mnt/data
sudo umount /mnt/data                 # 卸载
```

卸载时提示 `target is busy`（设备正被占用）：

```bash
lsof /mnt/data           # 查看哪些进程占用
fuser -mv /mnt/data      # 或用 fuser 查看
# 退出占用进程/目录后再 umount
```

### 3. 用 UUID 标识设备

`/dev/sdb1` 这类名字可能因插拔顺序变化，**UUID 全局唯一且稳定**，推荐用它：

```bash
sudo blkid               # 查看各分区 UUID 和类型
```

### 4. 开机自动挂载 /etc/fstab

挂载信息写入 `/etc/fstab`，开机时自动挂载。一行 6 个字段：

```fstab
# 设备/UUID              挂载点     类型    挂载选项   dump  fsck顺序
UUID=xxxx-xxxx           /data      xfs     defaults   0     0
```

```bash
sudo vim /etc/fstab      # 编辑
sudo mount -a            # 【关键】不重启立即测试 fstab 是否正确
df -h /data              # 确认已挂载
```

::: danger fstab 写错会导致开机失败
编辑 `/etc/fstab` 后**务必执行 `mount -a` 验证**，确认无报错再重启。写错可能让系统开机卡在挂载阶段。
:::

## 六、虚拟文件系统

`/proc` 和 `/sys` 中的文件并不真实存在于磁盘，而是内核在内存中动态生成的，用于查看/调整内核状态。

### /proc（进程与内核信息）

```bash
cat /proc/cpuinfo        # CPU 信息（等价 lscpu）
cat /proc/meminfo        # 内存信息（等价 free -h）
cat /proc/loadavg        # 系统负载
cat /proc/mounts         # 挂载信息
cat /proc/version        # 内核版本
ls /proc/$(pgrep -n nginx)   # 某进程的目录（PID 命名）
```

`/proc/sys/` 下可临时调整内核参数（配合 `sysctl`，永久配置写 `/etc/sysctl.conf`，详见 [内核调优](./linux-kernel)）。

### /sys（硬件与驱动）

`sysfs`，以规整的目录形式暴露硬件设备、驱动、内核模块信息：

```bash
ls /sys/class/net        # 网卡设备
ls /sys/block            # 块设备
```

## 相关速查

- [Linux 命令速查](/reference/linux-commands)
- [磁盘存储（LVM/RAID/分区）](./linux-storage)
