# df 命令详解：看磁盘分区还剩多少空间

> 本文是 [Linux 命令速查](../linux-commands#文件系统与磁盘) 中 `df` 的从 0 到 1 详解。
> 目标：把 `df --help` 里的每个选项讲清楚，多看几遍后，你在服务器上敲 `df --help` 就知道该用哪个选项。
> 环境依据：GNU coreutils 8.32（Ubuntu 22.04 自带；RHEL/Rocky 自带版本用法一致）。

## 一、命令是干什么的

`df`（disk free）用来查看**每个文件系统（磁盘分区）的总容量、已用、可用空间和占用百分比**。"磁盘满了"是最常见的线上故障之一，`df -h` 是第一反应命令。

- 不带参数：列出所有挂载的文件系统用量；
- 加 `-h`：用 K/M/G 人类可读单位（最常用）；
- 给文件/目录路径：只显示该路径所在的那个文件系统。

> 类比：`df` 就像 Windows"此电脑"里每个盘的"已用空间/可用空间"条形图，只不过它一次把所有挂载点都列出来。

注意区分：`df` 看的是**整个分区**的用量；而 `du` 看的是**某个目录**占了多少。排查"哪个目录塞满了盘"要先用 `df` 确认哪个分区满了，再用 `du` 去找大目录。

## 二、命令语法

```bash
df [选项]... [文件或目录]...
```

- `[选项]`：可选，控制单位、是否显示 inode、文件系统类型等；
- `[文件或目录]`：可选，给一个路径，`df` 就只显示这个路径落在哪个文件系统上、该系统用量如何；不写就列出全部。

最简单的用法：

```bash
df -h
```

## 三、选项全表（对照 `df --help`）

### 1. 控制大小单位与可读性

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-h`，`--human-readable` | 1024 进制的人类可读（K/M/G） | **最常用** |
| `-H`，`--si` | 1000 进制的人类可读 | 想看厂商口径 |
| `-k` | 以 1K 块为单位 | 脚本里固定单位 |
| `-B SIZE`，`--block-size=SIZE` | 按指定块大小缩放，如 `-BM` | 想统一用某单位 |
| `--total` | 在末尾输出一个所有盘的合计 | 想看总盘子 |

### 2. 控制显示哪些文件系统

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-a`，`--all` | 包含伪文件系统（tmpfs、devtmpfs 等） | 默认已含大部分，想看全部时 |
| `-l`，`--local` | 只显示本地文件系统，排除 NFS/网络盘 | 不想被网络盘干扰时 |
| `-t TYPE`，`--type=TYPE` | 只显示指定类型，如 `-t ext4` | 只看 ext4/xfs |
| `-x TYPE`，`--exclude-type=TYPE` | 排除指定类型，如 `-x tmpfs` | 过滤掉 tmpfs |

### 3. 控制显示哪些列

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-T`，`--print-type` | 多显示一列**文件系统类型**（ext4/xfs/tmpfs...） | 想知道是什么文件系统 |
| `-i`，`--inodes` | 显示 **inode** 使用情况（而非块用量） | 排查"文件没满但新建不了文件" |
| `--output[=字段]` | 自定义输出列 | 只想要 source、size、avail 等 |
| `-P`，`--portability` | POSIX 标准格式（一行不折行） | 脚本解析时 |

## 四、由浅入深的典型示例

### 示例 1：人类可读（最高频）

```bash
df -h
```

```text
Filesystem      Size  Used Avail Use% Mounted on
shm             225M     0  225M   0% /dev/shm
overlay         9.8G  145M  9.6G   2% /
tmpfs            64M     0   64M   0% /dev
tmpfs            64M   44K   64M   1% /run
/dev/vdb        9.8G   24K  9.8G   1% /tmp/user
```

逐列解释：

- `Filesystem`：哪个设备/文件系统；
- `Size`：总容量；
- `Used`：已用；
- `Avail`：**还能用多少**（普通用户视角，已扣除 5% 保留给 root）；
- `Use%`：使用率；
- `Mounted on`：挂载在哪个目录。

> `Use%` 冲到 90%+ 就要警惕；到 100% 时普通用户就写不进去了。

### 示例 2：只看某个路径所在的分区

```bash
df -h /var/log
```

> 哪怕 `/var/log` 在某个大分区上，这条命令只返回那一行，告诉你"这个目录所在的盘还剩多少"。

### 示例 3：显示文件系统类型

```bash
df -T
```

```text
Filesystem          Type       1K-blocks      Used Available Use% Mounted on
shm                 tmpfs         230176         0    230176   0% /dev/shm
overlay             overlay      10218772    147964  10054424   2% /
/dev/vdb            ext4         10218772        24  10202364   1% /tmp/user
```

> 多了一列 `Type`，能看出是 `ext4`、`xfs`、`tmpfs` 还是别的。

### 示例 4：看 inode 用量（容易被忽略的坑）

```bash
df -i
```

```text
Filesystem                     Inodes   IUsed  IFree IUse% Mounted on
overlay                        655360    3967 651393    1% /
/dev/vdb                        655360      11 655349    1% /tmp/user
```

- `Inodes`：该分区最多能建多少个文件（每个文件占一个 inode）；
- `IUsed`：已用 inode 数；
- `IUse%`：inode 使用率。

> 经典坑：磁盘空间 `Use%` 才 50%，但新建文件报"No space left on device"——这是 **inode 用完了**（比如几十万小文件），用 `df -i` 一看 `IUse%` 100% 就明白了。

### 示例 5：只看本地盘，排除网络盘

```bash
df -h -l
```

> 去掉 NFS、CIFS 等网络挂载，只看本地磁盘，输出更干净。

### 示例 6：只看 ext4 类型

```bash
df -h -t ext4
```

> 只列出 ext4 文件系统，方便在混合文件系统里定位。

### 示例 7：自定义列输出

```bash
df -h --output=source,size,used,avail,target
```

> 只输出你想要的列，适合脚本里解析，不会被多余列干扰。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `df -h` | 人类可读看各盘用量（**最常用**） |
| `df -hT` | 用量 + 文件系统类型 |
| `df -h /path` | 只看某路径所在盘 |
| `df -i` | 看 inode 是否用完 |
| `df -hl` | 只看本地盘 |
| `df -h --total` | 末尾加合计行 |

## 六、RHEL 系与 Debian 系差异

`df` 属于 GNU coreutils，**两系用法完全一致**。细微差别：

- RHEL/CentOS/Rocky 7+ 默认根分区是 `xfs`，Debian/Ubuntu 默认是 `ext4`，`df -T` 看到的 Type 不同；
- 都可能挂载 NFS/网络盘，`-l` 排除效果一致；
- inode 数量在格式化时决定（`mke2fs -i`），两系默认值不同。

## 七、新手易错点

1. **空间没满却写不进文件**：先 `df -i` 看是不是 inode 用完了，别盲目删大文件。
2. **`Avail` 比 `Size - Used` 小一点**：文件系统默认给 root 留了约 5% 保留块，属正常，不是算错。
3. **容器里 `df` 看到很多 overlay/tmpfs**：正常，容器的根就是 overlay，别误判。
4. **删掉大文件空间没释放**：可能是进程还占着这个已删文件句柄（`lsof | grep deleted`），重启进程才释放。
5. **`df` 是只读命令，可放心使用**：它只读挂载表和文件系统统计。
6. **`df` 看分区，`du` 看目录**：别用 `du` 去回答"盘还剩多少"，也别用 `df` 去找"哪个目录大"。

## 八、相关命令与文档

- 速查页：[Linux 命令速查](../linux-commands)
- 找哪个目录占空间：`du`（详解见 [du](./du)）
- 看磁盘设备和分区：`lsblk`（详解见 [lsblk-blkid](./lsblk-blkid)）
- 找被删未释放的文件：`lsof`
- 存储排查思路：见 [Linux 存储专题](../../guide/linux-storage)
