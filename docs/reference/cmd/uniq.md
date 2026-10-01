# uniq 命令详解：去掉相邻的重复行

> 本文是 [Linux 命令速查](../linux-commands#文本处理) 中 `uniq` 的从 0 到 1 详解。
> 目标：把 `uniq --help` 里的每个选项讲清楚，多看几遍后，你在服务器上敲 `uniq --help` 就知道该用哪个选项。
> 环境依据：GNU coreutils 8.32（Ubuntu 22.04 自带；RHEL/Rocky 自带版本用法一致）。

## 一、命令是干什么的

`uniq` 是 **unique（去重）** 的缩写，用来**把相邻的重复行合并成一行**。它最经典的搭档是 `sort`：因为 `uniq` 只认"相邻"的重复，所以通常先 `sort` 把相同行排到一起，再 `uniq` 去重。

- 不加选项：相邻重复行只留一条；
- `-c`：顺便数每行出现了几次（统计词频神器）；
- `-d`：只显示出现过重复的行；
- `-u`：只显示从没重复过的行。

> 类比：`uniq` 就像把一份名单里"挨在一起的重名"划掉。但它很死板——如果两个同名的人中间夹了别人，它就认不出来。所以要先 `sort` 把同名的排到一块儿。

它属于 GNU coreutils，常和 `sort` 连用。

## 二、命令语法

```bash
uniq [选项]... [输入文件 [输出文件]]
```

- `[选项]`：可选，控制去重行为和计数；
- `[输入文件]`：可选，不写就从标准输入读（常用管道喂进来）；
- `[输出文件]`：可选，不写就打到屏幕。

> 黄金套路：`sort 文件 | uniq`——先排序，再去重。

## 三、选项全表（对照 `uniq --help`）

### 1. 控制去重 / 计数行为

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-c`，`--count` | 每行前面**加出现次数** | 统计词频（最常用） |
| `-d`，`--repeated` | 只**打印出现过重复**的行（每组一条） | 只想看哪些值重复了 |
| `-u`，`--unique` | 只**打印从未重复**的行 | 只想看只出现一次的 |
| `-D` | 打印**所有**重复行（一条不漏） | 想保留重复行的完整内容 |
| `--all-repeated[=METHOD]` | 同 `-D`，但可在各组之间空一行 | 分组看得更清 |
| `-i`，`--ignore-case` | 比较时**忽略大小写** | `Apple` 和 `apple` 算重复 |

### 2. 比较时跳过部分内容

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-f N`，`--skip-fields=N` | 比较时跳过**前 N 个字段** | 想忽略第一列（如时间戳）再比 |
| `-s N`，`--skip-chars=N` | 比较时跳过**前 N 个字符** | 想忽略行首固定前缀再比 |
| `-w N`，`--check-chars=N` | 只比较每行**前 N 个字符** | 只按前缀是否相同去重 |

### 3. 其他

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-z`，`--zero-terminated` | 行分隔符是 NUL | 处理特殊文件名时配合管道 |
| `--group[=METHOD]` | 显示所有行，并用空行把各组分开 | 看分组效果更直观 |

## 四、由浅入深的典型示例

演示文件在 `/tmp/sre_shard_txt`。`demo.txt` 内容（注意相同行不相邻）：

```text
apple
banana
apple
cherry
banana
apple
date
```

### 示例 1：直接 uniq（不会去干净！）

```bash
uniq demo.txt
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

> 看，几乎没变！因为 `apple` 之间夹了 `banana`，`uniq` 只合并**相邻**重复，不相邻的它不管。这是新手最大的坑。

### 示例 2：先 sort 再 uniq（正确姿势）

```bash
sort demo.txt | uniq
```

```text
apple
banana
cherry
date
```

> 先 `sort` 把相同行排到相邻，再 `uniq`，去重才干净。这就是为什么说 uniq 必须配 sort。

### 示例 3：统计每行出现次数（`-c`）

```bash
sort demo.txt | uniq -c
```

```text
      3 apple
      2 banana
      1 cherry
      1 date
```

> 每行前面是次数：apple 出现 3 次、banana 2 次。这是统计"词频 / IP 出现次数 / 状态码分布"的核心命令。

### 示例 4：只看重复过的值

```bash
sort demo.txt | uniq -d
```

```text
apple
banana
```

> 只列出出现不止一次的（apple、banana），只出现一次的 cherry、date 被丢掉。

### 示例 5：只看唯一的（从没重复过的）

```bash
sort demo.txt | uniq -u
```

```text
cherry
date
```

> 和 `-d` 相反，只列出现一次的行。

### 示例 6：忽略大小写去重

`cases.txt` 内容是 `Apple / apple / APPLE / banana`：

```bash
uniq -i cases.txt
```

```text
Apple
banana
```

> 不加 `-i` 时这三个算不同行；加 `-i` 后大小写视为相同，合并成一条。

### 示例 7：组合拳——按出现次数倒序排行

```bash
sort demo.txt | uniq -c | sort -nr
```

```text
      3 apple
      2 banana
      1 date
      1 cherry
```

> `uniq -c` 数完次数，再 `sort -nr` 按次数从大到小排——这就是"找出出现最多的 Top N"的万能套路。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `sort 文件 \| uniq` | 排序后去重 |
| `sort 文件 \| uniq -c` | 统计每行出现次数 |
| `sort 文件 \| uniq -c \| sort -nr` | 按出现次数倒序（Top N） |
| `sort 文件 \| uniq -d` | 只看重复过的值 |
| `sort 文件 \| uniq -u` | 只看唯一的值 |
| `uniq -i 文件` | 忽略大小写去重 |
| `awk '{print $1}' 日志 \| sort \| uniq -c \| sort -nr` | 统计第一列的频次（如 Top IP） |

## 六、RHEL 系与 Debian 系差异

`uniq` 属于 GNU coreutils，**两系用法完全一致**，无实质差异。记住它和 `sort` 的搭档关系跨发行版通用即可。

## 七、新手易错点

1. **`uniq` 不排序，只去相邻重复**：这是头号坑。不先 `sort`，去重等于没去。
2. **`uniq` 和 `sort -u` 的区别**：`sort -u` 自带排序去重，一步到位；`uniq` 必须先 sort。
3. **`-c` 的计数在最左列**：注意前面那一列是次数，不是内容。
4. **`-d` 只给每组一条**：想看到所有重复行用 `-D`。
5. **`-f`/`-s`/`-w` 是"比较时跳过/截取"**：不是删除列，只是比较时忽略，原文照输出。
6. **`uniq` 只读不写原文件**：想保存结果要重定向。

## 八、相关命令与文档

- 速查页：[Linux 命令速查](../linux-commands#文本处理)
- 排序（uniq 的前置搭档）：`sort`（详解见 [sort](./sort)）
- 统计行数：`wc`（详解见 [wc](./wc)）
- 按列提取再统计：`awk`（详解见 [awk](./awk)）
- 管道原理：见 [重定向与管道](./redirect-tee)
