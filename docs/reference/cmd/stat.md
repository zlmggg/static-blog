# stat 命令详解：看文件的元信息

> 本文是 [Linux 命令速查](../linux-commands#文件与目录) 中 `stat` 的从 0 到 1 详解。
> 目标：把 `stat --help` 里的每个选项讲清楚，多看几遍后，你在服务器上敲 `stat --help` 就知道该用哪个选项。
> 环境依据：GNU coreutils 8.32（Ubuntu 22.04 自带；RHEL/Rocky 自带版本用法一致）。

## 一、命令是干什么的

`stat` 用来查看一个文件（或文件系统）的**详细元信息**：大小、inode、权限、属主、三个时间（访问/修改/状态改变/出生）等。

`ls -l` 只给你其中一部分；`stat` 给你**全部**，包括 `ls` 看不到的 inode 号、块数、精确到纳秒的时间。

> 类比：`ls -l` 像是看一个人的身份证正面（照片+姓名），`stat` 像是调出这个人的全部档案（身高、血型、户籍、登记时间）。排查"文件到底什么时候被改的"时，`stat` 是首选。

属于 GNU coreutils。

## 二、命令语法

```bash
stat [选项]... 文件...
```

- `[选项]`：可选，控制看文件还是文件系统、要不要自定义格式；
- `文件`：要看谁，可以一次给多个。

最简单的用法：

```bash
stat a.txt
```

## 三、选项全表（对照 `stat --help`）

### 1. 看文件还是文件系统

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-L`，`--dereference` | **跟随软链接**，显示链接指向的目标信息 | 想看链接背后真正的文件时 |
| `-f`，`--file-system` | 显示**文件系统**状态（总块数、空闲、inode 等），而不是文件 | 想看这个文件所在分区用了多少空间 |

> 不加 `-L` 时，stat 看软链接显示的是"链接本身"的信息（大小就是它指向路径的长度）。

### 2. 自定义输出格式

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-c FORMAT`，`--format=FORMAT` | 只输出指定字段，每项后换行 | 脚本里只要权限/时间/inode 某一项 |
| `--printf=FORMAT` | 同 `-c`，但解释反斜杠转义、不自动换行 | 脚本里精细排版 |
| `-t`，`--terse` | 紧凑成一行 | 脚本快速取数 |
| `--cached=MODE` | 取属性时用不用缓存（`always`/`never`/`default`） | 远程文件系统上想强制读最新值 |

> 常用格式符：`%a` 权限八进制、`%A` 人类可读权限、`%s` 大小字节、`%i` inode、`%U/%G` 属主/属组名、`%F` 文件类型、`%y` 修改时间、`%x` 访问时间、`%z` 状态改变时间、`%w` 出生时间。

## 四、由浅入深的典型示例

### 示例 1：看一个文件的完整档案

```bash
echo "demo" > a.txt
stat a.txt
```

```text
  File: a.txt
  Size: 5         	Blocks: 8          IO Block: 4096   regular file
Device: 30h/48d	Inode: 528384      Links: 1
Access: (0644/-rw-r--r--)  Uid: ( 1234/    user)   Gid: ( 1234/    user)
Access: 2026-09-30 23:30:35.686040051 +0800
Modify: 2026-09-30 23:30:35.687040054 +0800
Change: 2026-09-30 23:30:35.687040054 +0800
 Birth: 2026-09-30 23:30:35.686040051 +0800
```

逐行认：

- `File`：文件名；`Size`：大小 5 字节；`regular file` 普通文件；
- `Inode`：inode 号；`Links`：硬链接数（这里是 1）；
- `Access (0644/-rw-r--r--)`：权限，八进制和人读两种写法；
- `Access/Modify/Change/Birth` 四个时间：访问时间、内容修改时间、属性改变时间、创建（出生）时间。

### 示例 2：-f 看文件系统状态

```bash
stat -f .
```

```text
  File: "."
    ID: 1aef37621aae8c7c Namelen: 255     Type: overlayfs
Block size: 4096       Fundamental block size: 4096
Blocks: Total: 2554693    Free: 2516805    Available: 2512709
Inodes: Total: 655360     Free: 651253
```

> 这是当前目录所在文件系统的容量信息；想看整体磁盘占用通常用 `df` 更直观。

### 示例 3：-c 只取某一项（脚本神器）

```bash
stat -c '%a' a.txt
stat -c '%A' a.txt
stat -c '%s' a.txt
stat -c '%i' a.txt
stat -c '%U/%G' a.txt
stat -c '%F' a.txt
```

```text
644
-rw-r--r--
5
528384
user/user
regular file
```

> 想在脚本里只拿到权限数字、只拿大小，就用 `-c` 拼格式，比 `ls -l` 截取字符串可靠得多。

### 示例 4：一次拼多个字段

```bash
stat -c '%y %n' a.txt
```

```text
2026-09-30 23:30:35.687040054 +0800 a.txt
```

> `%y` 是修改时间，`%n` 是文件名，拼在一起就是"时间 + 文件名"。

### 示例 5：-t 紧凑一行

```bash
stat -t a.txt
```

```text
a.txt 5 8 81a4 1234 1234 30 528384 1 0 0 1790782235 1790782235 1790782235 1790782235 4096
```

> 一串数字，给程序读的；人看还是用默认或 `-c`。

### 示例 6：软链接默认 vs -L

```bash
ln -s a.txt lnk
stat lnk | grep -E 'File|Size'
stat -L lnk | grep -E 'File|Size'
```

```text
  File: lnk -> a.txt
  Size: 5         	Blocks: 0          IO Block: 4096   symbolic link
  File: lnk
  Size: 5         	Blocks: 8          IO Block: 4096   regular file
```

> 默认 `stat lnk` 显示它是个 `symbolic link`（软链接本身）；加 `-L` 后跟随到 `a.txt`，显示成 `regular file`。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `stat 文件` | 看完整元信息 |
| `stat -c '%a' 文件` | 只看权限八进制 |
| `stat -c '%y' 文件` | 只看修改时间 |
| `stat -c '%i' 文件` | 只看 inode 号 |
| `stat -f 目录` | 看所在文件系统 |
| `stat -L 软链接` | 跟随软链接看真实文件 |

## 六、RHEL 系与 Debian 系差异

`stat` 属于 GNU coreutils，**两系用法一致**。提醒：

- 个别 shell 会自带一个同名 `stat`（如某些版本），参数略有差异；服务器上用的是 GNU 版，本篇以它为准；
- 出生时间（`Birth`/`%w`）需要文件系统支持（ext4、xfs 等现代 FS 都支持）；老文件系统上可能显示 `-`（未知）。

## 七、新手易错点

1. **分不清三个时间**：atime（读过没）、mtime（内容改没改）、ctime（权限/属主改没改）；改内容会动 mtime 和 ctime。
2. **`stat` 不修改任何东西**：纯查看命令，可放心跑。
3. **软链接要看真实文件记得 `-L`**：不加 `-L` 看到的是链接自己的大小（等于路径字符串长度），会困惑。
4. **权限是 `Access` 那行**：`0644/-rw-r--r--` 是同一个权限的两种写法，别以为是两个东西。
5. **脚本取字段用 `-c`**：别用 `ls -l` 去 cut 列，字段顺序可能变，`stat -c` 更稳。

## 八、相关命令与文档

- 速查页：[Linux 命令速查](../linux-commands)
- 长格式看文件：`ls -l`（详解见 [ls](./ls)）
- 刷新文件时间戳：`touch`（详解见 [touch](./touch)）
- inode 与硬链接：`ln`（详解见 [ln](./ln)）
- 时间戳与文件系统：见 [Linux 文件系统](../../guide/linux-filesystem)
