# mkdir 命令详解：新建目录

> 本文是 [Linux 命令速查](../linux-commands#文件与目录) 中 `mkdir` 的从 0 到 1 详解。
> 目标：把 `mkdir --help` 里的每个选项讲清楚，多看几遍后，你在服务器上敲 `mkdir --help` 就知道该用哪个选项。
> 环境依据：GNU coreutils 8.32（Ubuntu 22.04 自带；RHEL/Rocky 自带版本用法一致）。

## 一、命令是干什么的

`mkdir` 是 **make directory（创建目录）** 的缩写，用来新建文件夹。

- 不给选项：在当前目录新建一个空目录；
- 一次给多个名字：同时建多个目录；
- 加 `-p`：连父目录一起递归建（最常用）。

> 类比：`mkdir` 就像 Windows 资源管理器里"右键 → 新建文件夹"，只不过它一次能建好几个、还能一口气建一整条目录链。

它属于 GNU coreutils，系统自带。

## 二、命令语法

```bash
mkdir [选项]... 目录名...
```

- `[选项]`：可选，控制建目录的方式（如 `-p` 递归、`-m` 设权限、`-v` 打印动作）；
- `目录名`：要建的目录，可以一次给多个。

最简单的用法：

```bash
mkdir docs
```

## 三、选项全表（对照 `mkdir --help`）

### 1. 控制"怎么建目录"

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-p`，`--parents` | 递归建：父目录不存在就一起建；目录已存在也不报错 | **最常用**，一口气建 `a/b/c` 这种多级路径 |
| `-v`，`--verbose` | 每建一个目录就打印一行 | 想看它到底建了哪些目录时 |

### 2. 控制"建出来的目录权限"

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-m MODE`，`--mode=MODE` | 直接指定目录权限（如 `700`），不受 umask 影响 | 建"只有自己能进"的私密目录时 |

### 3. 安全上下文（SELinux 相关）

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-Z` | 把新目录的 SELinux 安全上下文设为默认类型 | RHEL 开了 SELinux 时 |
| `--context[=CTX]` | 同 `-Z`，或指定具体的安全上下文 CTX | 精细控制 SELinux/SMACK 上下文 |

> `-Z`、`--context` 只在开了 SELinux 的系统上有意义，普通 Ubuntu 桌面用不到。

## 四、由浅入深的典型示例

### 示例 1：建单个目录

```bash
mkdir docs
ls -d docs
```

```text
docs
```

### 示例 2：一次建多个目录

```bash
mkdir src bin lib
ls
```

```text
bin
docs
lib
src
```

### 示例 3：-p 递归建多级目录（最高频）

```bash
mkdir -p projects/web/src/components
ls projects/web/src
```

```text
components
```

> 没有 `-p` 的话，`mkdir projects/web/src/components` 会因为 `projects/web/src` 不存在而报错；加了 `-p` 会把中间缺的目录全部补出来。

### 示例 4：-p 遇到已存在的目录不报错

```bash
mkdir -p docs
```

> 目录 `docs` 已经存在，**普通 `mkdir docs` 会报错 `File exists`**，加 `-p` 则静默跳过。这在写脚本时特别重要：重复执行不会崩。

### 示例 5：-v 打印它建了什么

```bash
mkdir -p -v a/b/c
```

```text
mkdir: created directory 'a'
mkdir: created directory 'a/b'
mkdir: created directory 'a/b/c'
```

### 示例 6：-m 建一个私密目录

```bash
mkdir -m 700 secret
ls -ld secret
```

```text
drwx------ 2 user user 4096 Sep 30 23:29 secret
```

> `700` 表示只有属主能读/写/进入，其他人完全没权限。默认不加 `-m` 时权限受 umask 影响（通常是 `755`）。

### 示例 7：不带 -p 建多级会怎样

```bash
mkdir x/y/z
```

```text
mkdir: cannot create directory ‘x/y/z’: No such file or directory
```

> 因为 `x` 都不存在，mkdir 不会自动帮你建——这正是 `-p` 要解决的问题。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `mkdir 目录` | 建一个目录 |
| `mkdir -p a/b/c` | 递归建多级（**最常用**） |
| `mkdir -p -v a/b/c` | 递归建并打印过程 |
| `mkdir -m 700 目录` | 建只有自己能进的目录 |
| `mkdir d1 d2 d3` | 一次建多个 |

## 六、RHEL 系与 Debian 系差异

`mkdir` 属于 GNU coreutils，**两系用法完全一致**。细微差别：

- RHEL 开了 SELinux 时，新建目录的默认安全上下文由系统策略决定；`-Z` 才用得上；
- 默认权限都是 `rwxr-xr-x`（即 755，受 umask 调整），两系相同；
- 老版本 coreutils 不影响上述常用选项。

## 七、新手易错点

1. **建多级目录忘记 `-p`**：报 `No such file or directory`，几乎是每个新手都会踩一次的坑。
2. **`mkdir` 不创建文件**：它只能建目录；建空文件要用 `touch`（见 [touch](./touch)）。
3. **目录已存在会报错**：脚本里重复执行要加 `-p`，否则 `File exists` 会中断脚本。
4. **权限位别写错**：`-m 700` 是三位八进制；写成 `777` 等于所有人可写，服务器上慎用。
5. **`mkdir` 不会动已有内容**：它只负责建目录，安全；但配合 `sudo` 在 `/` 下建目录要想清楚路径。

## 八、相关命令与文档

- 速查页：[Linux 命令速查](../linux-commands)
- 建空文件：`touch`（详解见 [touch](./touch)）
- 看目录里有什么：`ls`（详解见 [ls](./ls)）
- 删目录：`rm`（详解见 [rm](./rm)）
- 复制目录：`cp -r`（详解见 [cp](./cp)）
- 目录权限：见 [chmod](./chmod)
- 文件系统结构：见 [Linux 文件系统](../../guide/linux-filesystem)
