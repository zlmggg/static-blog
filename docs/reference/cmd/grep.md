# grep 命令详解：从文本里按关键词筛行

> 本文是 [Linux 命令速查](../linux-commands#文本处理) 中 `grep` 的从 0 到 1 详解。
> 目标：把 `grep --help` 里的每个常用选项讲清楚，多看几遍后，你在服务器上敲 `grep --help` 就知道该用哪个选项。
> 环境依据：GNU grep 3.7（Ubuntu 22.04 自带；RHEL/Rocky 自带版本用法一致）。

## 一、命令是干什么的

`grep` 是 Linux 里最常用的**文本搜索**工具：给它一个关键词（或正则表达式），它就从文件（或管道输入）里把**包含这个关键词的行**全部挑出来。

- 在日志里找报错：`grep ERROR app.log`；
- 只看行号、只看出现次数、只看前后几行；
- 配合 `-r` 递归搜整个目录；配合 `-v` 反向过滤。

> 类比：`grep` 就像 Ctrl+F"查找"，但它是在命令行里、对整个文件/管道做，而且能用正则表达"找所有像 IP 的东西"。它是"文本三剑客"之首（grep/sed/awk）。

它属 grep 包，几乎每台 Linux 都预装。

## 二、命令语法

```bash
grep [选项]... 关键词 [文件]...
```

- `[选项]`：可选，控制怎么搜、怎么显示结果；
- `关键词`：要找的内容，可以是普通字符串或正则；
- `[文件]`：可选，要搜谁；不写就从标准输入读（常接在管道后面）。

## 三、选项全表（对照 `grep --help`）

### 1. 用什么方式解释关键词（正则流派）

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-E`，`--extended-regexp` | 用**扩展正则**（支持 `+`、`\|`、`()`） | 写复杂正则时（很常用） |
| `-F`，`--fixed-strings` | 把关键词当**固定字符串**（不解释正则） | 关键词里有 `.*?` 等特殊符号时 |
| `-G`，`--basic-regexp` | 基本正则（默认） | 默认行为，一般不写 |
| `-P`，`--perl-regexp` | 用 **Perl 正则**（功能最强，支持 `\d`） | 需要 `\d`、零宽断言等高级语法 |
| `-e 关键词` | 指定一个关键词（可多次用） | 要给多个模式时 |
| `-f 文件` | 从文件里读关键词列表 | 关键词很多时 |

### 2. 匹配条件

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-i`，`--ignore-case` | 忽略大小写 | 找 `Error`/`ERROR`/`error` |
| `-v`，`--invert-match` | 反向：只显示**不匹配**的行 | 排除某类行（很常用） |
| `-w`，`--word-regexp` | 整词匹配（`ERROR` 不匹配 `ERRORS`） | 避免子串误中 |
| `-x`，`--line-regexp` | 整行完全匹配 | 要求整行一模一样 |

### 3. 怎么显示结果

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-n`，`--line-number` | 显示**行号** | 定位到第几行（很常用） |
| `-o`，`--only-matching` | 只打印**匹配到的那部分**，不整行 | 提取出具体内容（如所有 IP） |
| `-c`，`--count` | 只输出**匹配了几行** | 统计次数 |
| `-l`，`--files-with-matches` | 只列出**哪些文件**含匹配 | 批量找哪些文件有关键词 |
| `-L` | 列出**不含**匹配的文件 | 反向找文件 |
| `-q`，`--quiet` | 不输出任何内容（只看退出码） | 脚本里判断"有没有" |
| `-m N` | 找到 N 行就停 | 大文件里只要前几个 |
| `--color` | 高亮匹配到的关键词 | 终端里一眼看到匹配处 |

### 4. 上下文与递归

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-A N`，`--after-context=N` | 连匹配行**后面 N 行**一起显示 | 看报错之后发生了什么 |
| `-B N`，`--before-context=N` | 连匹配行**前面 N 行**一起显示 | 看报错之前发生了什么 |
| `-C N`，`--context=N` | 前后各 N 行（= `-A N -B N`） | 想看上下文全貌（常用） |
| `-r`，`--recursive` | **递归**搜目录下所有文件 | 在整个项目里找 |
| `-R` | 同 `-r`，但跟随软链接 | 链接目录也要搜 |
| `--include=GLOB` | 只搜匹配的文件 | 如 `--include="*.py"` |
| `--exclude=GLOB` | 跳过匹配的文件 | 如跳过 `*.min.js` |
| `--exclude-dir=GLOB` | 跳过某个目录 | 如 `--exclude-dir=node_modules` |
| `-a`，`--text` | 把二进制文件当文本搜 | 二进制里也想找关键词 |

## 四、由浅入深的典型示例

演示文件在 `/tmp/sre_shard_txt`，`app.log` 是一段示例日志。

### 示例 1：最基本——找含 ERROR 的行

```bash
grep ERROR app.log
```

```text
2026-09-30 10:00:04 ERROR db connection failed
2026-09-30 10:00:07 ERROR timeout
```

> 把含 `ERROR` 的两行挑了出来，其他行不显示。

### 示例 2：带行号

```bash
grep -n ERROR app.log
```

```text
4:2026-09-30 10:00:04 ERROR db connection failed
7:2026-09-30 10:00:07 ERROR timeout
```

> 行号在最前面：第 4 行、第 7 行。排查时能直接告诉别人"看第 7 行"。

### 示例 3：忽略大小写

```bash
grep -i error app.log
```

> `error` 小写也能匹配到 `ERROR` 大写。

### 示例 4：反向过滤——排除 INFO 行

```bash
grep -v INFO app.log
```

```text
2026-09-30 10:00:02 WARN  low memory
2026-09-30 10:00:04 ERROR db connection failed
2026-09-30 10:00:07 ERROR timeout
```

> `-v` 留下"不含 INFO"的行。日志太吵时，用它把一堆 INFO 噪音过滤掉。

### 示例 5：数匹配了几行

```bash
grep -c ERROR app.log
```

```text
2
```

> 不打印内容，只告诉你有 2 行含 ERROR。

### 示例 6：扩展正则——同时找 ERROR 或 WARN

```bash
grep -E 'ERROR|WARN' app.log
```

```text
2026-09-30 10:00:02 WARN  low memory
2026-09-30 10:00:04 ERROR db connection failed
2026-09-30 10:00:07 ERROR timeout
```

> `|` 表示或。不加 `-E` 时要写成 `ERROR\|WARN`，`-E` 后直接 `ERROR|WARN` 更顺眼。

### 示例 7：只提取匹配的部分（`-o`）

```bash
echo "port 8080 and 9090" | grep -oE '[0-9]+'
```

```text
8080
9090
```

> `-o` 不打印整行，只把"匹配到的片段"一个个列出来。这里把两个端口号单独抠了出来。

### 示例 8：看上下文（`-C`）

```bash
grep -C1 ERROR app.log
```

```text
2026-09-30 10:00:03 INFO  user alice login
2026-09-30 10:00:04 ERROR db connection failed
2026-09-30 10:00:05 INFO  retry ok
2026-09-30 10:00:06 INFO  user bob login
2026-09-30 10:00:07 ERROR timeout
2026-09-30 10:00:08 INFO  shut down
```

> `-C1` 给每个匹配行前后各带 1 行上下文，报错前发生了什么、之后怎么了一目了然。`-A3` 只看后面，`-B3` 只看前面。

### 示例 9：整词匹配

```bash
echo "ERRORS and ERROR" | grep -w ERROR
```

```text
ERRORS and ERROR
```

> `-w` 要求 `ERROR` 是独立单词。这行末尾的 `ERROR` 是独立词，所以整行被打印；但如果写成 `grep ERROR`（不加 -w），连 `ERRORS` 也会被当成匹配——`-w` 避免这种子串误中。

### 示例 10：递归搜目录，只列文件名

```bash
grep -rl "note" proj
```

```text
proj/docs/readme.md
proj/docs/api.md
```

> `-r` 递归进目录，`-l` 只列出"哪些文件含 note"，不打印具体行。想知道哪些文件里有某段话时用它。

### 示例 11：只搜某类文件

```bash
grep -r "note" proj --include="*.md"
```

```text
proj/docs/readme.md:note
proj/docs/api.md:note
```

> `--include="*.md"` 只在 markdown 文件里找，跳过 `.log`、`.sh`。

### 示例 12：Perl 正则提取日期 + 静默判断

```bash
echo "2026-09-30" | grep -oP '\d{4}-\d{2}-\d{2}'
```

```text
2026-09-30
```

> `-P` 支持 Perl 正则的 `\d`（数字）、`{4}` 这种简写。`grep -q` 则不输出，只靠退出码判断有没有匹配，常用于脚本：

```bash
grep -q ERROR app.log; echo "found ERROR exit=$?"   # exit=0
grep -q NOMATCH app.log; echo "no match exit=$?"     # exit=1
```

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `grep 关键词 文件` | 找出含关键词的行 |
| `grep -n 关键词 文件` | 找出行 + 行号 |
| `grep -i 关键词 文件` | 忽略大小写 |
| `grep -v 噪音 文件` | 反向排除 |
| `grep -E 'A\|B' 文件` | 同时找多个词 |
| `grep -C2 关键词 文件` | 看上下文 |
| `grep -r 关键词 目录` | 递归搜目录 |
| `grep -rl 关键词 目录` | 只列含关键词的文件名 |
| `命令 \| grep 关键词` | 从命令输出里过滤 |
| `grep -oE '正则' 文件` | 提取匹配片段 |

## 六、RHEL 系与 Debian 系差异

`grep` 属 GNU grep，**两系用法一致**。细微点：

- 两系默认都带 `--color=auto` 高亮；
- 老脚本里有时用 `egrep`（= `grep -E`）、`fgrep`（= `grep -F`），现在仍兼容，但推荐直接写 `grep -E`/`grep -F`。

## 七、新手易错点

1. **`grep` 匹配的是"行"**：它打印整行，不是只打印关键词；想只打印关键词用 `-o`。
2. **正则特殊字符要注意**：`. * ? []` 在正则里有特殊含义，想字面匹配用 `-F` 或转义。
3. **`-E` 和不加 `-E` 的转义区别**：`+`、`|`、`()` 在普通 grep 里要 `\+`、`\|`，加 `-E` 直接写。
4. **`grep 目录` 会报错**：直接给目录它不递归，要加 `-r`。
5. **管道里 grep 找不到时退出码是 1**：脚本里别把它当错误。
6. **危险提示**：`grep -r` 时用 `--exclude-dir` 排除 `node_modules`、`.git`，否则又慢又刷屏。

## 八、相关命令与文档

- 速查页：[Linux 命令速查](../linux-commands#文本处理)
- 找到后批量处理：`xargs`（详解见 [xargs](./xargs)）
- 按条件找文件（不是找内容）：`find`（详解见 [find](./find)）
- 替换 / 编辑文本：`sed`（详解见 [sed](./sed)）
- 按列处理文本：`awk`（详解见 [awk](./awk)）
- 管道原理：见 [重定向与管道](./redirect-tee)
