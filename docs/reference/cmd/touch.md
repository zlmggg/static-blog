# touch 命令详解：建空文件 / 改时间戳

> 本文是 [Linux 命令速查](../linux-commands#文件与目录) 中 `touch` 的从 0 到 1 详解。
> 目标：把 `touch --help` 里的每个选项讲清楚，多看几遍后，你在服务器上敲 `touch --help` 就知道该用哪个选项。
> 环境依据：GNU coreutils 8.32（Ubuntu 22.04 自带；RHEL/Rocky 自带版本用法一致）。

## 一、命令是干什么的

`touch` 有两个完全不同的用途：

1. **文件不存在时，建一个空文件**（最常用，等价于 Windows 里"新建一个空文本文件"）；
2. **文件已存在时，把它的访问/修改时间刷新成当前时间**。

它名字叫 touch（"摸一下"），本意就是"碰一下文件，更新它的时间"；但大家更常用它来**快速建一个空文件占位**。

> 类比：在 Windows 里右键"新建文本文档"就是 `touch 名字.txt`；对着一个文件按 F5 刷新它的"修改日期"就是不带 `-c` 的 touch。注意：它**只建空文件**，不写内容，写内容要靠编辑器或重定向。

属于 GNU coreutils。

## 二、命令语法

```bash
touch [选项]... 文件...
```

- `[选项]`：可选，控制"改哪个时间、改成什么时间、不存在时建不建"；
- `文件`：要操作的文件，可以一次给多个。

默认行为：文件不存在就建空文件；已存在就把它的访问时间和修改时间都改成现在。

最简单的用法：

```bash
touch test.txt
```

## 三、选项全表（对照 `touch --help`）

### 1. 控制"不存在时建不建"

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-c`，`--no-create` | 文件不存在也**不创建**，只改时间 | 只想刷新已有文件时间、怕误建文件时 |
| `-f` | （被忽略，历史遗留） | 无实际作用，兼容旧脚本，可无视 |

### 2. 控制"改哪个时间"

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-a` | 只改**访问时间（atime）** | 只动"最后查看时间"时 |
| `-m` | 只改**修改时间（mtime）** | 只动"最后内容修改时间"时 |
| `--time=WORD` | 指定改哪个时间：`access`/`atime`/`use` 等同 `-a`；`modify`/`mtime` 等同 `-m` | 用长选项写清楚意图 |

### 3. 控制"改成什么时间"

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-d STRING`，`--date=STRING` | 用**可读日期字符串**指定时间，如 `"2020-01-15 08:30"` | 想把文件时间戳设成某个具体日期 |
| `-t STAMP` | 用 `[[CC]YY]MMDDhhmm[.ss]` 格式指定时间 | 脚本里精确给时间戳 |
| `-r FILE`，`--reference=FILE` | **照搬另一个文件的时间** | 想让两个文件时间戳一致时 |
| `-h`，`--no-dereference` | 改**软链接本身**的时间，而不是它指向的文件 | 极少数系统上才有效 |

## 四、由浅入深的典型示例

### 示例 1：建一个空文件

```bash
touch notes.txt
ls -l notes.txt
```

```text
-rw-r--r-- 1 user user 0 Sep 30 23:29 notes.txt
```

> 大小是 `0`，因为它是空文件。

### 示例 2：一次建多个空文件

```bash
touch a.log b.log c.log
ls
```

```text
a.log
b.log
c.log
notes.txt
```

### 示例 3：已存在的文件会被"刷新时间"

```bash
echo hello > old.txt
sleep 1
echo "touch 前:"; stat -c '%y %n' old.txt
touch old.txt
echo "touch 后:"; stat -c '%y %n' old.txt
```

```text
touch 前:
2026-09-30 23:29:27.448843728 +0800 old.txt
touch 后:
2026-09-30 23:29:28.473846687 +0800 old.txt
```

> 注意：`old.txt` 里的内容 `hello` 没变，只是修改时间被推到了"现在"。这在 `make` 判断"哪些文件需要重新编译"时很关键。

### 示例 4：-c 不存在也不创建

```bash
touch -c nope.txt
ls nope.txt
```

```text
ls: cannot access 'nope.txt': No such file or directory
```

> 没加 `-c` 的话 `nope.txt` 会被建出来；加了 `-c` 就什么都不做，适合脚本里"只刷新、不新建"。

### 示例 5：-d 指定一个过去的时间

```bash
touch -d "2020-01-15 08:30" fixed.txt
stat -c '%y %n' fixed.txt
```

```text
2020-01-15 08:30:00.000000000 +0800 fixed.txt
```

### 示例 6：-t 用紧凑格式给时间戳

```bash
touch -t 199912312359 y2k.txt
stat -c '%y %n' y2k.txt
```

```text
1999-12-31 23:59:00.000000000 +0800 y2k.txt
```

> 格式是 `年月日时分`：`1999 12 31 23 59` = 1999-12-31 23:59。

### 示例 7：-r 照搬另一个文件的时间

```bash
touch -r fixed.txt ref.txt
stat -c '%y %n' fixed.txt ref.txt
```

```text
2020-01-15 08:30:00.000000000 +0800 fixed.txt
2020-01-15 08:30:00.000000000 +0800 ref.txt
```

> `ref.txt` 的时间被设成和 `fixed.txt` 一模一样。

### 示例 8：-a 只动访问时间

```bash
touch a.txt
sleep 1
touch -a a.txt
stat -c '%x | %y' a.txt
```

```text
2026-09-30 23:29:29.531849742 +0800 | 2026-09-30 23:29:28.526846840 +0800
```

> 前面是访问时间 atime（被刷新到新值），后面是修改时间 mtime（保持旧值）。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `touch 文件` | 建空文件 / 刷新时间（**最常用**） |
| `touch a.log b.log` | 一次建多个空文件 |
| `touch -c 文件` | 只刷新时间，不存在也不建 |
| `touch -d "2020-01-15" 文件` | 把时间戳设成指定日期 |
| `touch -r 参考文件 文件` | 照搬参考文件的时间 |

## 六、RHEL 系与 Debian 系差异

`touch` 属于 GNU coreutils，**两系用法完全一致**。唯一提醒：

- `-d` 能识别的自然语言字符串（如 `"yesterday"`、`"2 hours ago"`）在两系都支持；
- `-h`（改软链接自身时间）在不支持修改 symlink 时间的旧内核/文件系统上无效，属正常现象。

## 七、新手易错点

1. **`touch` 建的是空文件**：它不会写入任何内容，文件大小为 0。想写内容请用 `vim`/重定向 `echo > file`。
2. **已存在文件不会被清空**：`touch 老文件` 只改时间，不动内容，放心用。
3. **别把 touch 当 mkdir**：`touch 某目录` 是想建文件；建目录要用 `mkdir`（见 [mkdir](./mkdir)）。
4. **时间戳是三个时间**：atime（访问）、mtime（内容修改）、ctime（属性改变），`touch` 默认动前两个；想看清楚用 `stat`（见 [stat](./stat)）。
5. **通配符小心**：`touch *.log` 会刷新当前目录所有 `.log` 的时间，不是新建一堆。

## 八、相关命令与文档

- 速查页：[Linux 命令速查](../linux-commands)
- 看文件的完整时间戳：`stat`（详解见 [stat](./stat)）
- 建目录：`mkdir`（详解见 [mkdir](./mkdir)）
- 往文件里写内容：`echo` / 重定向
- 文件类型与时间概念：见 [Linux 文件系统](../../guide/linux-filesystem)
