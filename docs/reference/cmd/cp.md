# cp 命令详解：复制文件和目录

> 本文是 [Linux 命令速查](../linux-commands#文件与目录) 中 `cp` 的从 0 到 1 详解。
> 目标：把 `cp --help` 里的每个选项讲清楚，多看几遍后，你在服务器上敲 `cp --help` 就知道该用哪个选项。
> 环境依据：GNU coreutils 8.32（Ubuntu 22.04 自带；RHEL/Rocky 自带版本用法一致）。

## 一、命令是干什么的

`cp` 是 **copy（复制）** 的缩写，把一个或多个文件/目录复制成新的副本。

- 复制文件：`cp 源 目标`；
- 复制目录：必须加 `-r`（递归），否则报错；
- 它是"复制"，原文件还在；想"搬走"用 `mv`（见 [mv](./mv)）。

> 类比：就是 Windows 里的"复制 + 粘贴"，只不过命令行里没有剪贴板，而是直接告诉它"从哪复制、复制到哪"。复制完源文件原封不动。

属于 GNU coreutils。

## 二、命令语法

```bash
cp [选项]... [-T] 源 目标
cp [选项]... 源... 目录          # 多个源放进同一个目录
cp [选项]... -t 目录 源...       # 反过来：目录在前
```

- `源`：要复制谁；
- `目标`：复制到哪。如果目标已存在且是文件，会被覆盖（注意）；如果目标是目录，就把源文件放进该目录里；
- 复制目录必须加 `-r`/`-R`。

最简单的用法：

```bash
cp src.txt dst.txt
```

## 三、选项全表（对照 `cp --help`）

### 1. 控制"遇到已存在的目标怎么办"

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-i`，`--interactive` | 覆盖前**询问** | 怕误覆盖时（很多系统把它设成别名） |
| `-n`，`--no-clobber` | **不覆盖**已存在的文件，静默跳过 | 只想补充、不想动旧文件时 |
| `-f`，`--force` | 目标打不开就先删掉再试 | 一般不用，理解即可 |
| `-u`，`--update` | **只在源比目标新、或目标不存在时**才复制 | 增量同步、只更新改过的文件 |

> 记忆：`-i` 问你、`-n` 直接跳过、`-u` 看谁新。三者若同时给，**最后一个生效**。

### 2. 控制"要不要复制目录"

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-R`，`-r`，`--recursive` | **递归复制整个目录树** | 复制文件夹时必加（最常用） |
| `-T`，`--no-target-directory` | 把目标当成普通文件，而不是目录 | 防止目标是目录时被误"塞进"里面 |

### 3. 控制"软链接怎么处理"

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-P`，`--no-dereference` | **不跟随**软链接，复制链接本身 | 想保留"链接"这个形状时 |
| `-L`，`--dereference` | **总是跟随**软链接，复制链接指向的真实内容 | 想要链接背后的真实文件时 |
| `-d` | 等同 `--no-dereference --preserve=links` | 配合递归保留软链接 |
| `-H` | 只跟随命令行里给的软链接 | 较少用 |
| `-s`，`--symbolic-link` | 建软链接而不是真复制 | 见 [ln](./ln) |
| `-l`，`--link` | 建硬链接而不是真复制 | 省空间时 |

### 4. 控制"保留原文件的属性"

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-a`，`--archive` | **归档复制**：`-dR --preserve=all`，连权限、属主、时间、软链接全保留 | 备份/迁移目录时的首选 |
| `-p` | 保留权限、属主、时间戳（不递归） | 单个文件想保留时间戳时 |
| `--preserve[=ATTR]` | 精细指定保留哪些属性（`mode,ownership,timestamps,links,xattr,all`） | 只要保留某几项时 |
| `--no-preserve=ATTR` | 明确**不保留**某项属性 | 覆盖默认行为时 |
| `--attributes-only` | 只复制属性，不复制文件数据 | 少见 |

### 5. 目标位置与备份

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-t 目录`，`--target-directory=目录` | 把后面所有源都放进该目录 | 多个源统一复制到一处 |
| `--parents` | 在目标目录下按源的完整路径建子目录 | 保留目录层级时 |
| `--remove-destination` | 打开目标前先删掉它（比 `-f` 更干脆） | 极少用 |
| `--strip-trailing-slashes` | 去掉源末尾的 `/` | 脚本里路径带 `/` 时 |
| `--backup[=CONTROL]` | 覆盖前给旧文件做备份 | 怕覆盖坏时 |
| `-b` | 同 `--backup`，但不带参数 | 简单备份 |
| `-S 后缀`，`--suffix=SUFFIX` | 改备份文件后缀（默认 `~`） | 自定义备份名 |

### 6. 其他

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-v`，`--verbose` | 打印每一步在复制什么 | 大目录复制时看进度 |
| `-x`，`--one-file-system` | 不跨进别的文件系统 | 备份整盘时跳过其他分区 |
| `--sparse=WHEN` | 控制稀疏文件怎么处理 | 处理大的空洞文件 |
| `--reflink[=WHEN]` | 用写时复制（CoW）轻量复制 | btrfs/XFS 上省空间 |
| `-Z`，`--context[=CTX]` | 设目标的 SELinux 上下文 | RHEL 开 SELinux 时 |

## 四、由浅入深的典型示例

### 示例 1：复制单个文件

```bash
echo "hello world" > src/a.txt
cp src/a.txt b.txt
ls -l b.txt
cat b.txt
```

```text
-rw-r--r-- 1 user user 12 Sep 30 23:29 b.txt
hello world
```

### 示例 2：复制目录必须加 -r

```bash
cp src dst
```

```text
cp: -r not specified; omitting directory 'src'
```

```bash
cp -r src dst
ls -R dst
```

```text
dst:
a.txt
sub

dst/sub:
x.log
```

> 不加 `-r` 它只会警告"省略了目录"，什么都不复制。

### 示例 3：-i 覆盖前询问

```bash
echo "n" | cp -i src/a.txt b.txt
```

```text
cp: overwrite 'b.txt'? b.txt 内容仍是: hello world
```

> 它问"是否覆盖"，我们喂了 `n`（不），所以 `b.txt` 没被改。

### 示例 4：-n 不覆盖

```bash
echo "should not overwrite" > src/a.txt
cp -n src/a.txt b.txt
cat b.txt
```

```text
hello world
```

> 目标已存在就跳过，不覆盖也不询问，脚本里很安全。

### 示例 5：-v 打印动作

```bash
cp -v src/a.txt c.txt
```

```text
'src/a.txt' -> 'c.txt'
```

### 示例 6：-u 只在更新时复制

```bash
touch src/a.txt     # 让源变新
cp -v -u src/a.txt b.txt
```

```text
'src/a.txt' -> 'b.txt'
```

> 源比目标新才复制；如果目标更新，就什么都不做。适合"只同步改过的文件"。

### 示例 7：-p 保留时间戳

```bash
touch -d "2020-05-05 10:00" src/a.txt
cp src/a.txt plain.txt
cp -p src/a.txt kept.txt
stat -c '%y %n' plain.txt kept.txt
```

```text
2026-09-30 23:29:54.244921090 +0800 plain.txt
2020-05-05 10:00:00.000000000 +0800 kept.txt
```

> 普通副本时间变成了"现在"；`-p` 副本保留了源文件原来的时间。

### 示例 8：-a 归档复制目录

```bash
cp -a src arch_a
ls -l arch_a
```

```text
total 8
-rw------- 1 user user   21 May  5  2020 a.txt
drwxr-xr-x 2 user user 4096 Sep 30 23:29 sub
```

> `-a` 等于递归 + 保留权限/属主/时间/软链接，做"原汁原味"的目录备份时用它。

### 示例 9：-t 把多个源放进同一个目录

```bash
cp -v -t /tmp/cp/dst src/a.txt
```

```text
'src/a.txt' -> '/tmp/cp/dst/a.txt'
```

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `cp 源 目标` | 复制单个文件 |
| `cp -r 源目录 目标目录` | 复制目录（**最常用**） |
| `cp -i 源 目标` | 覆盖前询问 |
| `cp -n 源 目标` | 不覆盖已有文件 |
| `cp -u 源 目标` | 只更新改过的 |
| `cp -a 源目录/ 目标/` | 归档备份（保留一切属性） |
| `cp -v ...` | 看复制了哪些 |

## 六、RHEL 系与 Debian 系差异

`cp` 属于 GNU coreutils，**两系主用法一致**。细微差别：

- 很多发行版默认把 `cp` 别名成 `cp -i`（覆盖前询问）；脚本里最好显式写 `-f`/`-n` 避免交互卡住；
- `-a` 在普通用户下复制属主时，新副本属主会变成当前用户（保留属主需要 root）；
- SELinux 相关的 `-Z`/`--context` 只在 RHEL 系开 SELinux 时才体现作用。

## 七、新手易错点

1. **复制目录忘加 `-r`**：报"omitting directory"，什么都没复制——这是最常见的错。
2. **`cp` 会静默覆盖**：目标已存在时默认直接覆盖，没有回收站，**三思**；重要目录先 `cp -i` 或 `-n`。
3. **`cp` 不删源文件**：复制完源还在；想搬走用 `mv`。
4. **结尾斜杠的坑**：`cp -r src dst` 和 `cp -r src/ dst` 在目标已存在时行为可能不同；拿不准先 `ls` 看一眼。
5. **`-a` 复制软链接时复制的是链接本身**：想要链接指向的真实内容要加 `-L`。
6. **通配符 + 覆盖**：`cp *.log bak/` 会把当前所有日志塞进 `bak/`，覆盖时不提醒，留意。

## 八、相关命令与文档

- 速查页：[Linux 命令速查](../linux-commands)
- 移动/重命名：`mv`（详解见 [mv](./mv)）
- 删除：`rm`（详解见 [rm](./rm)）
- 建软链接代替复制：`ln -s`（详解见 [ln](./ln)）
- 看复制后文件详情：`ls -l`（详解见 [ls](./ls)）
- 权限保留含义：见 [chmod](./chmod)
