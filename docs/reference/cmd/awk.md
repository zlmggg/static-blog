# awk 命令详解：按列处理文本的小编程语言

> 本文是 [Linux 命令速查](../linux-commands#文本处理) 中 `awk` 的从 0 到 1 详解。
> 目标：把 `awk` 的 `-F`、`模式{动作}`、`NR/NF/$n`、`BEGIN/END`、`printf`、数组讲清楚，多看几遍后，你在服务器上敲列处理时就知道该怎么写。
> 环境依据：GNU Awk 5.1.0（gawk 包，Ubuntu 22.04 自带；RHEL/Rocky 自带 gawk 用法一致）。

## 一、命令是干什么的

`awk` 不只是个命令，它是一门**专门处理按行列排版文本的小编程语言**。它把每行自动切成一列列字段（`$1`、`$2`...），你写"什么模式下做什么动作"，它就逐行帮你筛行、取列、统计、求和。

- 取 CSV 的第 1、3 列：`awk -F, '{print $1,$3}'`；
- 按条件筛行：`awk -F, '$2>28'`；
- 统计求和、计数、分组：配合 `BEGIN/END` 和数组。

> 类比：grep 是"找行"，sed 是"改行"，awk 是"把每一行当一张表格，按列做计算"。日志、CSV、`ps`/`df` 输出这种"一列列"的数据，用 awk 处理最顺手。它是文本三剑客之一。

它属 gawk（GNU awk）包。

## 二、命令语法

```bash
awk [选项] '模式 {动作}' [文件]...
```

- `-F 分隔符`：指定列分隔符（默认是空白）；
- `'模式 {动作}'`：核心——满足"模式"的行，就执行"动作"；模式可省略（对每行动作），动作也可省略（打印整行）；
- `[文件]`：要处理谁；不写就从标准输入读。

工作流程：**先跑 `BEGIN` → 逐行匹配模式并执行动作 → 最后跑 `END`**。

## 三、选项与内置变量全表

### 1. 命令行选项

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-F 分隔符`，`--field-separator=分隔符` | 指定列分隔符 | 处理 CSV 用 `-F,`（很常用） |
| `-f 脚本文件` | 从文件读 awk 脚本 | 脚本很长时 |
| `-v 变量=值` | 传入外部变量 | 把 shell 变量带进 awk |

### 2. 内置变量（最该背）

| 变量 | 含义 |
|---|---|
| `$0` | 整行内容 |
| `$1` `$2` ... | 第 1 列、第 2 列... |
| `NF` | 当前行一共有**几列**（Number of Fields） |
| `NR` | 当前是**第几行**（Number of Records） |
| `FS` | 输入列分隔符（等价 `-F`） |
| `OFS` | 输出列分隔符（默认空格） |

### 3. 结构与动作

| 写法 | 作用 |
|---|---|
| `{print $1,$3}` | 对每行做动作（这里打印 1、3 列） |
| `条件 {动作}` | 只对满足条件的行做动作 |
| `/正则/ {动作}` | 只对匹配正则的行做动作 |
| `BEGIN{...}` | 处理任何行**之前**执行一次（初始化） |
| `END{...}` | 所有行处理完**之后**执行一次（汇总） |
| `printf 格式, 值...` | 格式化打印（像 C 语言的 printf） |
| `数组[键]++` | 计数/分组（awk 数组是字典） |

## 四、由浅入深的典型示例

演示文件在 `/tmp/sre_shard_txt`，`users.csv` 内容是 `名字,年龄,城市`：

```text
alice,30,beijing
bob,25,shanghai
carol,35,beijing
dave,28,guangzhou
```

### 示例 1：默认打印整行

```bash
awk '{print}' users.csv
```

```text
alice,30,beijing
bob,25,shanghai
carol,35,beijing
dave,28,guangzhou
```

> 不写动作时 `print` 就是打印 `$0`（整行）。

### 示例 2：按逗号取第 1、3 列（高频）

```bash
awk -F, '{print $1, $3}' users.csv
```

```text
alice beijing
bob shanghai
carol beijing
dave guangzhou
```

> `-F,` 指定逗号分列，`$1` 是名字、`$3` 是城市。这是 awk 最常用的姿势。

### 示例 3：看每行有几列（`NF`）

```bash
awk -F, '{print $0, "| fields=", NF}' users.csv
```

```text
alice,30,beijing | fields= 3
bob,25,shanghai | fields= 3
carol,35,beijing | fields= 3
dave,28,guangzhou | fields= 3
```

> `NF` 告诉我们每行分了几列，这里都是 3 列。

### 示例 4：行号（`NR`）

```bash
awk -F, '{print NR": "$1}' users.csv
```

```text
1: alice
2: bob
3: carol
4: dave
```

> `NR` 是当前行号，自动从 1 递增。

### 示例 5：按条件筛行

```bash
awk -F, '$3=="beijing"' users.csv
```

```text
alice,30,beijing
carol,35,beijing
```

> 省略动作时默认打印整行。这里模式是"第 3 列等于 beijing"，只输出符合的行。

### 示例 6：数字比较

```bash
awk -F, '$2>28 {print $1, $2}' users.csv
```

```text
alice 30
carol 35
```

> 第 2 列（年龄）大于 28 的才打印，这里只挑出 alice(30) 和 carol(35)。

### 示例 7：BEGIN/END 求和平均

```bash
awk -F, 'BEGIN{sum=0} {sum+=$2} END{print "平均年龄=", sum/NR}' users.csv
```

```text
平均年龄= 29.5
```

> `BEGIN` 先把 sum 清零；逐行把第 2 列累加到 sum；`END` 时除以总行数 NR，得到平均年龄 29.5。这是 awk 做统计的经典套路。

### 示例 8：`printf` 格式化输出

```bash
awk -F, 'BEGIN{printf "%-8s %s\n","名字","年龄"} {printf "%-8s %d\n",$1,$2}' users.csv
```

```text
名字       年龄
alice    30
bob      25
carol    35
dave     28
```

> `printf` 不像 `print` 自动加空格，它按你给的格式排版：`%-8s` 是左对齐占 8 字符的字符串，`%d` 是整数。输出对齐得整整齐齐。

### 示例 9：用数组分组计数

```bash
awk -F, '{city[$3]++} END{for(c in city) print c, city[c]}' users.csv
```

```text
shanghai 1
guangzhou 1
beijing 2
```

> `city[$3]++` 把每个城市当字典键、出现一次加一；`END` 时遍历数组打印。这就是"统计每个城市有几个人"——相当于 `sort | uniq -c`，但 awk 一步到位。

### 示例 10：默认按空白分列

```bash
echo "a b c" | awk '{print $2}'
```

```text
b
```

> 不指定 `-F` 时，默认按空白（空格/Tab）分列，`$2` 就是中间的 `b`。处理 `ps`、`df` 输出时常靠这个默认行为。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `awk -F, '{print $1}' 文件` | 取 CSV 第 1 列 |
| `awk -F, '$2>28' 文件` | 按列条件筛行 |
| `awk '{print $1}' 文件` | 取默认空白分列的第 1 列 |
| `awk 'NR==1' 文件` | 只看第 1 行 |
| `awk '{sum+=$1} END{print sum}' 文件` | 对第 1 列求和 |
| `awk '{a[$1]++} END{for(k in a) print k,a[k]}'` | 统计第 1 列各值出现次数 |
| `ps \| awk '{print $1}'` | 从 ps 输出取进程名列 |

## 六、RHEL 系与 Debian 系差异

`awk` 命令在两系通常都指向 `gawk`（GNU awk），用法一致。细微点：

- Debian/Ubuntu 上 `awk` 直接就是 gawk；RHEL 上 `awk` 也多指向 gawk；
- 极少数极简系统只有 `mawk`（功能较少），写复杂脚本时用 `gawk` 调用更保险。

## 七、新手易错点

1. **CSV 一定要 `-F,`**：不指定分隔符，逗号会被当成内容的一部分，整行就是 `$1`。
2. **`$1` 的 `$` 不能丢**：写 `awk '{print 1}'` 是打印数字 1；`awk '{print $1}'` 才是打印第 1 列。
3. **比较字符串用 `==`，别用 `=`**：`=` 是赋值，`==` 才是比较。
4. **`{}` 和脚本之间不要用分号乱加**：`模式{动作}` 是连在一起的整体。
5. **`print` 和 `printf` 区别**：`print` 自动加空格换行；`printf` 要自己写 `\n`。
6. **awk 是只读处理**：它默认输出到屏幕，不改原文件，想存盘要重定向。

## 八、相关命令与文档

- 速查页：[Linux 命令速查](../linux-commands#文本处理)
- 找行：`grep`（详解见 [grep](./grep)）
- 替换整行：`sed`（详解见 [sed](./sed)）
- 排序与去重：`sort`（[sort](./sort)）、`uniq`（[uniq](./uniq)）
- 管道与 Shell 编程基础：见 [Linux Shell 专题](../../guide/linux-shell)
