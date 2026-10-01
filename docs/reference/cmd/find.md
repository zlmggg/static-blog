# find 命令详解：按条件全盘查找文件

> 本文是 [Linux 命令速查](../linux-commands#文件与目录) 中 `find` 的从 0 到 1 详解。
> 目标：把 `find --help` 里的常用 tests / 选项 / 动作讲清楚，多看几遍后，你在服务器上敲 `find --help` 就知道该用哪个条件。
> 环境依据：GNU findutils 4.8.0（Ubuntu 22.04 自带；RHEL/Rocky 自带版本用法一致）。

## 一、命令是干什么的

`find` 是 Linux 上最强大的"按条件找文件"命令：你给它一个起点目录，它递归钻进每个子目录，把满足你给的条件的文件/目录列出来（或对它们执行某个命令）。

- 按名字找：`find . -name "*.log"`；
- 按类型找：只要文件、只要目录；
- 按大小、修改时间、属主、权限找；
- 找到后顺手对它们执行操作：`-exec rm {} \;`。

> 类比：`locate` 像查索引卡片，秒出但可能不准；`find` 像你亲自拿着手电筒，一个文件夹一个文件夹实地翻找——慢一点，但条件想多细就多细，最可靠。它属于 findutils 包。

## 二、命令语法

```bash
find [起点目录...] [表达式]
```

- `[起点目录]`：从哪个目录开始往下找；不写默认当前目录 `.`；
- `[表达式]`：由"测试条件 + 动作"组成，默认动作是 `-print`（把找到的路径打印出来）。

表达式的结构就是：**从哪找 → 什么条件 → 找到后干嘛**。

## 三、选项全表（对照 `find --help`）

`find` 的"选项"分四类：控制搜索深度的 options、判断条件的 tests、对结果做动作的 actions、以及连接条件的 operators。

### 1. 控制搜索范围（options）

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-maxdepth N` | 最多往下搜 N 层目录 | 不想钻进太深子目录时（很常用） |
| `-mindepth N` | 至少往下搜 N 层 | 跳过最外层目录时 |
| `-xdev` | 不进入其他磁盘分区 | 只在当前文件系统内找 |
| `-depth` | 先处理目录内容再处理目录本身 | 配合 -delete 删除深层目录时 |

### 2. 按名字 / 类型找（tests，最高频）

| 条件 | 中文含义 | 什么场景用 |
|---|---|---|
| `-name 模式` | 按**文件名**匹配（区分大小写） | `find . -name "*.log"`（最常用） |
| `-iname 模式` | 同上但**忽略大小写** | `*.LOG` 也能匹配到 |
| `-type f` | 只要**普通文件** | 排除目录、链接 |
| `-type d` | 只要**目录** | 只找文件夹 |
| `-type l` | 只要**软链接** | 找符号链接时 |
| `-path 模式` | 按**完整路径**匹配 | 路径里某段含特定名字时 |
| `-regex 模式` | 按正则匹配完整路径 | 复杂模式时 |

### 3. 按时间 / 大小 / 属性找（tests）

| 条件 | 中文含义 | 什么场景用 |
|---|---|---|
| `-mmin N` | N 分钟前**修改**过（`-N` 是 N 分钟内） | 找最近改动的文件 |
| `-mtime N` | N 天前**修改**过 | 找几天内改过的文件 |
| `-amin N` / `-atime N` | 按**访问时间**找 | 很久没被读的文件 |
| `-cmin N` / `-ctime N` | 按**状态改变时间**（权限/属性）找 | 属性变更排查 |
| `-size N` | 按大小找（`+100M` 大于、`-10k` 小于） | 找大文件（很常用） |
| `-empty` | 找**空文件 / 空目录** | 清理空文件 |
| `-user 名` | 属主是某用户 | 找某用户的文件 |
| `-group 名` | 属组是某组 | 按组找 |
| `-perm 模式` | 按权限位找 | 找权限过松的文件（如 `644`） |
| `-readable`/`-writable`/`-executable` | 当前用户可读/可写/可执行 | 按访问权限筛 |
| `-newer 文件` | 比某文件**更新** | 找比配置文件改动晚的文件 |

### 4. 对结果做什么（actions）

| 动作 | 中文含义 | 什么场景用 |
|---|---|---|
| `-print` | 打印路径（默认动作） | 基本不用显式写 |
| `-ls` | 用 `ls -dils` 详细格式打印 | 直接看详细信息 |
| `-print0` | 路径用 NUL 分隔（而非换行） | 配合 `xargs -0` 处理带空格文件名 |
| `-exec 命令 {} \;` | 对每个结果执行命令（每个一次） | 找到后批量操作 |
| `-exec 命令 {} +` | 把结果攒一批一次执行（更高效） | 批量删除/处理 |
| `-ok 命令 {} \;` | 同 `-exec`，但执行前**逐个询问确认** | 危险操作前先确认 |
| `-delete` | **直接删除**找到的文件 | 清理（高危！） |
| `-prune` | 排除某个目录 | 不想钻进某子目录时 |

### 5. 逻辑连接（operators）

| 符号 | 含义 |
|---|---|
| `! 条件` / `-not 条件` | 取反（不满足） |
| `-a` / `-and` | 并且（默认就是，可不写） |
| `-o` / `-or` | 或者 |
| `( 条件 )` | 分组改变优先级 |

## 四、由浅入深的典型示例

演示在 `/tmp/sre_shard_txt` 下，`proj` 是一棵测试目录树。

### 示例 1：列出目录下所有内容（递归）

```bash
find proj
```

```text
proj
proj/old.bak
proj/src
proj/src/tmp.tmp
proj/src/a.py
proj/src/b.sh
proj/logs
proj/logs/access.log
proj/logs/error.log
proj/docs
proj/docs/readme.md
proj/docs/api.md
```

> 不给条件时，默认从起点递归列出**所有**文件和目录。

### 示例 2：只要普通文件

```bash
find proj -type f
```

```text
proj/old.bak
proj/src/tmp.tmp
proj/src/a.py
proj/src/b.sh
proj/logs/access.log
proj/logs/error.log
proj/docs/readme.md
proj/docs/api.md
```

> 去掉了目录行，只剩文件。

### 示例 3：按文件名找所有 .md

```bash
find proj -name "*.md"
```

```text
proj/docs/readme.md
proj/docs/api.md
```

> `*.md` 要用引号包起来，防止 shell 先把它展开。这是最常用的找文件方式。

### 示例 4：忽略大小写找

```bash
find proj -iname "README.*"
```

```text
proj/docs/readme.md
```

> 不加 `-i` 时 `README.*` 匹配不到小写的 `readme.md`；加 `-iname` 就不分大小写了。

### 示例 5：限制搜索深度

```bash
find proj -maxdepth 2
```

> `-maxdepth 2` 只往下钻两层，不深入更里面。扫大盘时能大幅提速。

### 示例 6：找空文件

```bash
find proj -empty
```

```text
proj/old.bak
proj/src/tmp.tmp
proj/empty.tmp
```

> 列出所有空文件和空目录。清理垃圾时常配合 `-delete`。

### 示例 7：找最近 10 分钟内修改过的文件

```bash
find proj -mmin -10
```

> `-mmin -10` 表示"10 分钟之内被改过"。找"刚才谁动了文件"时很好用。按天就是 `-mmin` 换成 `-mtime`。

### 示例 8：找到后对每个文件执行命令（`-exec`）

```bash
find proj -name "*.md" -exec echo "发现文档:" {} \;
```

```text
发现文档: proj/docs/readme.md
发现文档: proj/docs/api.md
```

> `{}` 会被替换成找到的每个路径，`\;` 表示命令结束。这就是"找到后批量操作"的模板。

### 示例 9：把结果攒一批一次性执行（`-exec ... +`）

```bash
find proj -name "*.log" -exec ls -l {} +
```

```text
-rw-r--r-- 1 user user 3 Sep 30 23:29 proj/logs/access.log
-rw-r--r-- 1 user user 3 Sep 30 23:29 proj/logs/error.log
```

> 用 `{}`+`+` 而不是 `{} \;`，`ls` 会一次接收多个文件，比逐个调用高效。

### 示例 10：详细格式列出

```bash
find proj -name "a.py" -ls
```

```text
   528306      4 -rw-r--r--   1 user     user            4 Sep 30 23:29 proj/src/a.py
```

> `-ls` 直接打印详细信息（权限、大小、时间），省得再管道接 `ls -l`。

### 示例 11：取反——找不是 .log 的文件

```bash
find proj -type f ! -name "*.log"
```

```text
proj/old.bak
proj/src/tmp.tmp
proj/src/a.py
proj/src/b.sh
proj/docs/readme.md
proj/docs/api.md
```

> `!` 表示"不满足后面条件"，这里挑出所有不是日志的文件。

### 示例 12：或条件——找 .md 或 .log

```bash
find proj -type f \( -name "*.md" -o -name "*.log" \)
```

```text
proj/logs/access.log
proj/logs/error.log
proj/docs/readme.md
proj/docs/api.md
```

> `-o` 是或者。复杂条件用 `\( \)` 分组，注意转义。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `find . -name "*.log"` | 按名字找日志 |
| `find . -type f -name "*.conf"` | 找某类文件 |
| `find / -name 文件名 2>/dev/null` | 全盘找（丢弃报错） |
| `find . -size +100M` | 找大于 100M 的大文件 |
| `find . -mmin -60` | 找最近 1 小时改过的文件 |
| `find . -empty -delete` | 删空文件（高危，先别加 -delete 预览） |
| `find . -name "*.tmp" -exec rm {} +` | 找到 tmp 文件批量删 |
| `find . -name "*.md" -print0 \| xargs -0 grep 关键词` | 配合 xargs 处理带空格文件名 |

## 六、RHEL 系与 Debian 系差异

`find` 属 GNU findutils，**两系用法一致**。细微点：

- RHEL 系加了 SELinux 后，可用 `-context` 按安全上下文找；
- 全盘找时 `/proc`、`/sys` 是虚拟文件系统，两系都建议 `2>/dev/null` 丢掉权限报错。

## 七、新手易错点

1. **`-name "*.x"` 一定要加引号**：不引号会被 shell 提前展开，导致条件错误。
2. **`-delete` 高危**：它会真删文件！执行前先**去掉 `-delete` 跑一遍看会删什么**，确认无误再加。
3. **`-exec ... \;` 和 `{} +` 的区别**：`\;` 每个文件执行一次，`+` 攒批一次执行；后者快得多。
4. **从 `/` 全盘找很慢**：先用 `-maxdepth`、指定具体目录缩小范围。
5. **带空格的文件名会让 xargs 出错**：用 `-print0 | xargs -0`（见 [xargs](./xargs)）。
6. **`-type` 别写错**：`f` 文件、`d` 目录、`l` 链接，单字母。
7. **危险提示**：`find ... -delete` 或 `-exec rm` 是不可逆操作，先 `echo` 预览结果。

## 八、相关命令与文档

- 速查页：[Linux 命令速查](../linux-commands#文件与目录)
- 按索引快速找文件（更快但不实时）：`locate`（详解见 [locate / which / whereis](./locate-which-whereis)）
- 把找到的文件批量交给下一个命令：`xargs`（详解见 [xargs](./xargs)）
- 找文件内容里的关键词：`grep`（详解见 [grep](./grep)）
- 看目录占用：`du`（同目录详解）
