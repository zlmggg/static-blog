# cat 命令详解：把文件内容打到屏幕上

> 本文是 [Linux 命令速查](../linux-commands#文件与目录) 中 `cat` 的从 0 到 1 详解。
> 目标：把 `cat --help` 里的每个选项讲清楚，多看几遍后，你在服务器上敲 `cat --help` 就知道该用哪个选项。
> 环境依据：GNU coreutils 8.32（Ubuntu 22.04 自带；RHEL/Rocky 自带版本用法一致）。

## 一、命令是干什么的

`cat` 是 **concatenate（连接）** 的缩写，最常用的用途是：**把一个或多个文件的内容原样打印到屏幕上**，一次性全部输出、不分页。

- 不带参数：从键盘读内容（配合 Ctrl+D 结束）；
- 给一个文件名：打印这个文件的全部内容；
- 给多个文件名：按顺序把它们拼在一起打印（这就是"concatenate"名字的由来）；
- 加选项：可以给行编号、显示行尾和制表符、压缩空行。

> 类比：`cat` 就像 Windows 里用记事本"打开一个文件后 Ctrl+A 全选、再把全文复制粘贴到聊天框"，只不过它直接把全文吐在终端里。文件太大时它会"一口气刷完"，屏幕滚得飞快——那是该换 `less` 的时候。

它属于 GNU coreutils 基础包，几乎所有 Linux 发行版都预装。

## 二、命令语法

```bash
cat [选项]... [文件]...
```

- `[选项]`：可选，控制行号、行尾标记等输出格式；
- `[文件]`：可选，指定要查看谁；可以一次给多个，会按顺序拼接打印；一个都不给时，就从标准输入（键盘）读。

最简单的用法：

```bash
cat /etc/hostname
```

## 三、选项全表（对照 `cat --help`）

`cat` 选项不多，主要分两类：一类给内容加"标记"（行号、行尾、制表符），一类做辅助显示。

### 1. 给输出加行号

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-n`，`--number` | 给**所有**输出行编号（含空行） | 想知道文件一共几行、按行号定位时 |
| `-b`，`--number-nonblank` | 只给**非空行**编号，且优先级覆盖 `-n` | 空行多的文件想清爽编号时 |

### 2. 把看不见的字符显示出来

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-E`，`--show-ends` | 在每行末尾显示 `$` | 排查行尾多出的空格、Windows 换行符时（很实用） |
| `-T`，`--show-tabs` | 把 TAB 字符显示成 `^I` | 分不清是空格还是制表符时 |
| `-v`，`--show-nonprinting` | 用 `^` 和 `M-` 记号显示不可打印字符 | 文件里有奇怪控制字符想揪出来时 |
| `-e` | 等价于 `-vE`（显示不可打印字符 + 行尾 `$`） | 想同时看行尾和特殊字符时 |
| `-t` | 等价于 `-vT`（显示不可打印字符 + 制表符） | 想同时看制表符和特殊字符时 |
| `-A`，`--show-all` | 等价于 `-vET`（上面三项全开） | 排查"看不见的字符"问题时的一把梭选项 |

### 3. 压缩空行与其他

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-s`，`--squeeze-blank` | 把**连续多个空行**压缩成一个空行 | 文件里空行太多影响阅读时 |
| `-u` | 忽略（历史遗留，什么都不做） | 基本用不到，了解即可 |

## 四、由浅入深的典型示例

演示文件都在 `/tmp/sre_shard_txt` 下。

### 示例 1：查看一个文件的全部内容

```bash
cat demo.txt
```

```text
apple
banana
apple
cherry
banana
apple
date
```

> 这就是 `cat` 最日常的用法：打开小文件看一眼。

### 示例 2：给所有行加行号

```bash
cat -n demo.txt
```

```text
     1	apple
     2	banana
     3	apple
     4	cherry
     5	banana
     6	apple
     7	date
```

> 每行前面多了序号，空行也会编号。

### 示例 3：只给非空行编号

```bash
cat -b special.txt
```

```text
     1	line one

     2	line three with	tab
     3	last line
```

> 中间那个空行没有编号——`-b` 只数有内容的行，这是它和 `-n` 的关键区别。

### 示例 4：显示行尾 `$`（排查多余空格）

```bash
cat -E special.txt
```

```text
line one$
$
line three with	tab$
last line$
```

> 每行末尾都有 `$`。如果某行末尾多出空格，会显示成 `last line   $`，一眼就能看到"行尾有脏数据"。

### 示例 5：把制表符显示成 `^I`

```bash
cat -T special.txt
```

```text
line one

line three with^Itab
last line
```

> 原来的那个 TAB 现在变成了 `^I`，说明这里是一个制表符而不是空格。

### 示例 6：一把梭看所有隐藏字符（`-A`）

```bash
cat -A special.txt
```

```text
line one$
$
line three with^Itab$
last line$
```

> `-A` = `-vET`，行尾的 `$` 和制表符的 `^I` 一起显示出来。遇到"复制出来的文本怎么格式乱了"，先 `-A` 一眼。

### 示例 7：压缩连续空行

文件 `blanks.txt` 里有一串连续空行，先用 `-A` 看原始样子：

```bash
cat -A blanks.txt
```

```text
a$
$
$
$
b$
$
$
c$
```

加 `-s` 后，连续多个空行被压成一个：

```bash
cat -s blanks.txt
```

```text
a

b

c
```

> 注意：`-s` 只压"连续"的空行，孤立的空行不动。

### 示例 8：一次拼接多个文件

```bash
cat nums.txt demo.txt
```

```text
10
2
33
100
7
apple
banana
apple
cherry
banana
apple
date
```

> 先打印 `nums.txt`，紧接着打印 `demo.txt`，首尾相接——这正是"concatenate 拼接"的本意。配合 `>` 就能把多个文件合并成一个：`cat a.txt b.txt > all.txt`。

### 示例 9：文件不存在时的报错

```bash
cat nope.txt
```

```text
cat: nope.txt: No such file or directory
```

> 报错信息打到**标准错误**，退出码非 0。脚本里用 `cat` 前最好确认文件存在。

## 五、高频组合速记

实际工作中基本就这几个组合：

| 命令 | 用途 |
|---|---|
| `cat 文件` | 看小文件全文（最常用） |
| `cat -n 文件` | 看全文并带行号 |
| `cat -A 文件` | 排查行尾空格 / 制表符 / 乱码 |
| `cat a b > c` | 把多个文件拼接合并成一个 |
| `cat > 文件 <<EOF` | 用键盘内容直接写文件（here 文档，见重定向篇） |
| `cat 文件 | grep 关键词` | 配合管道做过滤 |
| `cat /etc/os-release` | 看系统版本 |

## 六、RHEL 系与 Debian 系差异

`cat` 属于 GNU coreutils，**RHEL/CentOS/Rocky 与 Ubuntu/Debian 的用法完全一致**，上述选项通用，没有实质差异。仅提醒：

- 不同发行版 coreutils 大版本不同（如老版本是 8.22），选项集合基本相同，以本机 `cat --help` 为准；
- `cat` 不读交互、不依赖 SELinux，两系行为一致。

## 七、新手易错点

1. **大文件别直接 `cat`**：几百 MB 的日志直接 `cat` 会瞬间刷爆终端、找不回头，改用 `less` 或 `head`/`tail`。
2. **`cat` 不能编辑文件**：它只显示/拼接，想改内容要用 `vim`/`nano`，或配合 `>` 重定向写入。
3. **用 `cat` 配合 `>` 会覆盖原文件**：`cat a > b` 会把 `b` 清空后再写入；想追加用 `>>`，详见[重定向与管道](./redirect-tee)篇。
4. **`-n` 和 `-b` 会在空行上表现不同**：数行数要 `-n`；空行多想清爽要 `-b`。
5. **看不到行尾空格很正常**：普通 `cat` 看不出行尾空格，要 `-A` 或 `-E`。
6. **`cat 多文件` 是拼接不是对比**：想 diff 两个文件要用 `diff`，不是 `cat a b`。

## 八、相关命令与文档

- 速查页：[Linux 命令速查](../linux-commands)
- 大文件分页慢慢翻：`less`（详解见 [less 与 more](./less-more)）
- 只看开头几行：`head`（详解见 [head](./head)）
- 只看结尾几行 / 实时跟踪：`tail`（详解见 [tail](./tail)）
- 数行数字数：`wc`（详解见 [wc](./wc)）
- 重定向、管道怎么配合 `cat`：见 [重定向与管道](./redirect-tee)
- Shell 输入输出基础：见 [Linux Shell 专题](../../guide/linux-shell)
