# lsblk 与 blkid 命令详解：看清磁盘、分区、文件系统和 UUID

> 本文是 [Linux 命令速查](../linux-commands#文件系统与磁盘) 中 `lsblk`、`blkid` 的从 0 到 1 详解。
> 目标：把 `lsblk` 的树形输出、`-f`/`-o` 选项，以及 `blkid` 查 UUID 的用法讲清楚，多看几遍后，你在服务器上敲 `lsblk -f` 就知道哪块盘对应哪个分区。
> 环境依据：均属 util-linux 2.37.2（Ubuntu 22.04 自带；RHEL/Rocky 自带同属 util-linux，用法一致）。

## 一、命令是干什么的

- **`lsblk`**（list block devices）：以**树形**列出所有块设备（磁盘、分区、LVM、挂载点），一眼看清"哪块盘、分了几个区、每个区挂在哪"。
- **`blkid`**（block id）：查看每个分区的**文件系统类型、LABEL、UUID**。`/etc/fstab` 里挂盘常用 UUID，`blkid` 就是查 UUID 的工具。

> 类比：`lsblk` 像"磁盘和分区的家谱树"——大盘下面挂着哪些分区、分区挂到哪个目录；`blkid` 像给每个分区发的"身份证"——读出它的文件系统类型和唯一编号 UUID。

## 二、命令语法

```bash
# lsblk
lsblk [选项]... [设备]...

# blkid
blkid [选项]... [设备]...
```

- `lsblk` 不带参数：列出所有块设备的树；
- `blkid` 不带参数：列出所有能识别的分区的 UUID/类型（通常要 root）；
- 给设备路径：只看指定设备。

## 三、选项全表（对照 `--help`）

### 1. lsblk 常用选项

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-f`，`--fs` | 输出**文件系统**信息（FSTYPE、LABEL、UUID、挂载点） | 查 UUID/文件系统类型（最常用） |
| `-o 列`，`--output=列` | 只显示指定列 | 只要 NAME/SIZE/MOUNTPOINT 时 |
| `-a`，`--all` | 显示所有设备（含空设备） | 想看全部 |
| `-b`，`--bytes` | 大小用字节而非人类可读 | 脚本精确取值 |
| `-d`，`--nodeps` | 不显示从属关系（只看盘，不看分区） | 只想列磁盘 |
| `-i`，`--ascii` | 用 ASCII 字符画树（不用框线） | 终端不支持 Unicode 时 |
| `-l`，`--list` | 用列表而非树形 | 输出给脚本 |
| `-m`，`--perms` | 显示属主/权限 | 看设备权限 |
| `-n`，`--noheadings` | 不显示表头 | 脚本取值 |
| `-p`，`--paths` | 显示完整设备路径（/dev/...） | 想要完整路径 |
| `-r`，`--raw` | 原始输出（制表符分隔） | 喂给脚本/awk |
| `-t`，`--topology` | 输出设备拓扑（对齐、 rotational 等） | 判断 HDD/SSD |
| `-J`，`--json` | JSON 格式输出 | 程序解析 |

### 2. lsblk 常用输出列

| 列 | 含义 |
|---|---|
| `NAME` | 设备名（vda、vda1） |
| `SIZE` | 大小 |
| `TYPE` | disk / part / lvm 等 |
| `MOUNTPOINT` | 挂载点 |
| `FSTYPE` | 文件系统类型（ext4/xfs...） |
| `LABEL` | 文件系统卷标 |
| `UUID` | 唯一标识（/etc/fstab 用） |

### 3. blkid 常用选项

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-o 格式`，`--output=格式` | 输出格式：`value`/`device`/`export`/`full` | 想要纯值时用 `-o value` |
| `-s TAG`，`--match-tag=TAG` | 只显示指定标签，如 `-s UUID` | 只查 UUID |
| `-t NAME=VALUE`，`--match-token=` | 按标签查找设备，如 `-t UUID=xxx` | 已知 UUID 找设备 |
| `-L LABEL`，`--label=` | 按 LABEL 反查设备名 | 用卷标找盘 |
| `-U UUID`，`--uuid=` | 按 UUID 反查设备名 | 用 UUID 找盘 |
| `-g`，`--garbage-collect` | 清理 blkid 缓存 | 缓存过期时 |
| `-i`，`--info` | 收集 I/O 限制信息 | 较少用 |
| `-p`，`--probe` | 低层探测，绕过缓存 | 新分区没被识别时 |

## 四、由浅入深的典型示例

### 示例 1：默认树形输出

```bash
lsblk
```

```text
NAME      MAJ:MIN RM  SIZE RO TYPE MOUNTPOINTS
vda       254:0    0   10G  0 disk 
vdb       254:16   0   10G  0 disk /tmp/user
pmem0     259:0    0  766M  0 disk 
└─pmem0p1 259:1    0  765M  0 part 
```

- 树形缩进表示从属：`pmem0p1` 是 `pmem0` 下的一个分区；
- `TYPE` 列：`disk` 是整盘、`part` 是分区；
- `MOUNTPOINTS` 为空说明该设备/分区还没挂载。

### 示例 2：看文件系统和 UUID（最高频）

```bash
lsblk -f
```

```text
NAME      FSTYPE FSVER LABEL UUID FSAVAIL FSUSE% MOUNTPOINTS
vda                                                       
vdb                                   9.7G     0% /tmp/user
pmem0                                                     
└─pmem0p1                                                 
```

> 加 `-f` 后多出 `FSTYPE`、`LABEL`、`UUID` 等列。在你自己的机器上，已格式化的分区这里会显示出 UUID，把它抄进 `/etc/fstab` 即可开机自动挂载。

### 示例 3：只想要几列

```bash
lsblk -o NAME,SIZE,TYPE,MOUNTPOINT
```

```text
NAME       SIZE TYPE MOUNTPOINT
vda         10G disk 
vdb         10G disk /tmp/user
pmem0      766M disk 
└─pmem0p1  765M part 
```

> 用 `-o` 自定义列，输出干净，适合截图和脚本。

### 示例 4：只列磁盘（不要分区）

```bash
lsblk -d -o NAME,SIZE,TYPE
```

> `-d` 只显示设备本身、不展开分区，适合"先看有几块盘"。

### 示例 5：判断是不是 SSD/机械盘

```bash
lsblk -d -o NAME,ROTA,TYPE
```

> `ROTA`（rotational）为 1 表示机械盘（会转），为 0 表示 SSD。这是快速判断介质类型的办法。

### 示例 6：blkid 查所有分区的 UUID

```bash
sudo blkid
```

示意输出（在已格式化的机器上）：

```text
/dev/vdb1: UUID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" TYPE="ext4" PARTUUID="..."
/dev/vda1: UUID="yyyyyyyy-yyyy-..." TYPE="xfs"
```

> 把输出里的 `UUID="..."` 抄到 `/etc/fstab`，比写 `/dev/vdb1` 更稳（设备名可能因为插拔顺序变化，UUID 不变）。

### 示例 7：只查某个分区的 UUID

```bash
sudo blkid -s UUID -o value /dev/vdb1
```

```text
xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

> `-s UUID` 只显示 UUID 标签、`-o value` 只显示值，方便脚本直接取到纯 UUID 字符串。

### 示例 8：按 UUID 反查设备

```bash
sudo blkid -U xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

> 反过来：给一个 UUID，告诉你它对应 `/dev/` 下哪个设备。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `lsblk` | 树形看盘和分区 |
| `lsblk -f` | 看文件系统/UUID/挂载点（**最常用**） |
| `lsblk -o NAME,SIZE,TYPE,MOUNTPOINT` | 精简列输出 |
| `lsblk -d -o NAME,ROTA` | 判断 SSD/HDD |
| `sudo blkid` | 列出所有分区 UUID |
| `sudo blkid -s UUID -o value /dev/vdb1` | 只取某分区 UUID |

## 六、RHEL 系与 Debian 系差异

两命令都属 util-linux，**用法完全一致**。细微差别：

- RHEL/CentOS/Rocky 默认根分区是 `xfs`，Debian/Ubuntu 是 `ext4`，`lsblk -f` 的 `FSTYPE` 列不同；
- 云服务器常见 `vda`/`vdb`（virtio）、`nvme0n1`（AWS NVMe）；
- `blkid` 在普通权限下可能读不到所有设备，查 UUID 时记得加 `sudo`；容器里可能输出为空（没有块设备权限），属正常。

## 七、新手易错点

1. **`lsblk` 看到的 `NAME` 带缩进树**：缩进表示从属关系，不是名字的一部分。
2. **有盘没挂载**：`MOUNTPOINTS` 为空只是没挂上去，不代表盘坏了，用 `mount` 或写进 `/etc/fstab` 挂载。
3. **`/etc/fstab` 里别写死 `/dev/vdb1`**：重启后设备名可能变，建议用 `blkid` 拿到 UUID 再写。
4. **`blkid` 不加 sudo 没输出**：权限不够读不到分区超块。
5. **格式化前先确认设备名**：`lsblk` 看清楚再 `mkfs`，把数据盘格错是灾难操作。
6. **这些都是只读命令**：`lsblk`、`blkid` 都不修改任何东西，可放心使用。

## 八、相关命令与文档

- 速查页：[Linux 命令速查](../linux-commands)
- 看分区空间用量：`df`（详解见 [df](./df)）
- 看目录占用：`du`（详解见 [du](./du)）
- 磁盘 I/O 性能：`iostat`（详解见 [iostat-iotop](./iostat-iotop)）
- 存储专题：见 [Linux 存储专题](../../guide/linux-storage)
