# tar 命令详解：打包与解包（.tar / .tar.gz / .tar.bz2）

> 本文是 [Linux 命令速查](../linux-commands#压缩与打包) 中 `tar` 的从 0 到 1 详解。
> 目标：把 `tar -c/-x/-t/-z/-j/-f/-v/-C` 这几个灵魂选项讲清楚，多看几遍后，你在服务器上敲 `tar -czf` 就知道怎么打包、`tar -xzf` 怎么解包。
> 环境依据：GNU tar 1.34（Ubuntu 22.04 自带；RHEL/Rocky 自带版本用法一致）。

## 一、命令是干什么的

`tar`（tape archive，磁带归档）用来把**一堆文件打包成一个文件**，并能在打包时顺便用 gzip/bzip2/xz 压缩。`.tar`、`.tar.gz`（`.tgz`）、`.tar.bz2`、`.tar.xz` 这些后缀都是它。

- `-c`：**创建**打包；
- `-x`：**解开**打包；
- `-t`：**列出**包里有什么（不解压）；
- `-z`：用 **gzip** 压缩/解压（`.tar.gz`）；
- `-j`：用 **bzip2** 压缩/解压（`.tar.bz2`）；
- `-J`：用 **xz** 压缩/解压（`.tar.xz`）；
- `-f`：指定**文件名**（后面紧跟包名）；
- `-v`：显示正在处理的文件（verbose）；
- `-C`：解包到**指定目录**。

> 类比：`tar` 像一个"压缩文件夹"工具，但在 Linux 里它是命令行、且打包和压缩是分开的两个动作（`-c` 打包 + `-z` 压缩）。

记忆口诀：**"吃（c）稀饭（x）太（t）脏（z）就（j）烦（f）"**——`c/x/t` 是三大动作，`z/j` 是压缩方式，`f` 必须紧跟包名。

## 二、命令语法

```bash
tar <操作> [选项]... [-f 包名] [文件或目录]...
```

- 三大动作三选一：`-c`（建包）、`-x`（解包）、`-t`（列包内容）；
- `-f 包名`：**必须有**，且它是最后一个带参数的选项（包名紧跟 `-f`）；
- 后面跟要打包的文件/目录，或解包时用位置过滤。

最简单的用法：

```bash
tar -czf backup.tar.gz mydir/
```

## 三、选项全表（对照 `tar --help`）

### 1. 主操作（三选一）

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-c`，`--create` | 创建新包 | 打包时 |
| `-x`，`--extract` | 解包 | 解开时 |
| `-t`，`--list` | 列出包内容 | 不解压先看里面有啥 |
| `-r`，`--append` | 往包末尾追加文件 | 已存在的 .tar 加文件 |
| `-u`，`--update` | 只追加比包里新的文件 | 增量更新 |
| `-d`，`--diff` | 对比包和磁盘差异 | 校验 |
| `--delete` | 从包里删除文件 | 较少用 |

### 2. 压缩方式（与主动作搭配）

| 选项 | 中文含义 | 对应后缀 |
|---|---|---|
| `-z`，`--gzip` | gzip 压缩/解压 | `.tar.gz` / `.tgz`（最快、最常用） |
| `-j`，`--bzip2` | bzip2 压缩/解压 | `.tar.bz2`（压缩率更高、较慢） |
| `-J`，`--xz` | xz 压缩/解压 | `.tar.xz`（压缩率最高、最慢） |
| `--no-auto-compress` | 不自动按后缀选压缩 | 手动控制时 |

### 3. 通用修饰

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-f 包名`，`--file=` | 指定包文件名 | **必须**，紧跟包名 |
| `-v`，`--verbose` | 显示处理过程 | 看到底打包了哪些文件 |
| `-C 目录`，`--directory=` | 先切到某目录再执行 | 解包到指定目录（解包时） |
| `-p`，`--preserve-permissions` | 保留权限 | 解包时保留原权限 |
| `--exclude=PATTERN` | 排除匹配文件 | 打包时跳过 `.git`、日志 |
| `-X 文件`，`--exclude-from=` | 从文件读排除规则 | 批量排除 |
| `-P` | 允许绝对路径 | 较少用（有风险） |
| `-z` 配合 `-d` | 测试压缩包完整性 | `tar -tzf` 验证 |

## 四、由浅入深的典型示例

### 示例 1：打包并用 gzip 压缩（最常用）

```bash
tar -czf tardoor.tar.gz tardoor
ls -lh tardoor.tar.gz
```

```text
-rw-r--r-- 1 user user 1.4K Sep 30 23:28 tardoor.tar.gz
```

> `c` 建包、`z` gzip、`f` 指定包名。后缀写 `.tar.gz`（或 `.tgz`），方便别人识别。

### 示例 2：不解压，先看包里有什么

```bash
tar -tzf tardoor.tar.gz
```

```text
tardoor/
tardoor/sub/
tardoor/sub/f2.txt
tardoor/sub2/
tardoor/big.bin
tardoor/sub1/
tardoor/sub1/b.txt
tardoor/a.txt
tardoor/f1.txt
```

> `t` 列内容、`z` 告诉它这是 gzip 包。解压前先 `t` 一下，防止解出一堆不想要的文件。

### 示例 3：解包到当前目录

```bash
tar -xzf tardoor.tar.gz
```

> `x` 解包、`z` 解压、`f` 包名。默认解到当前目录。

### 示例 4：解包到指定目录（`-C`）

```bash
mkdir tout
tar -xzf tardoor.tar.gz -C tout
find tout
```

```text
tout
tout/tardoor
tout/tardoor/sub
tout/tardoor/sub/f2.txt
tout/tardoor/big.bin
tout/tardoor/sub1
tout/tardoor/a.txt
tout/tardoor/f1.txt
```

> `-C tout` 先切到 `tout` 目录再解包，避免污染当前目录。**强烈建议**解包前先建好目录再 `-C`。

### 示例 5：bzip2 压缩（更小但更慢）

```bash
tar -cjf tardoor.tar.bz2 tardoor
ls -lh tardoor.tar.*
```

```text
-rw-r--r-- 1 user user  295 Sep 30 23:28 tardoor.tar.bz2
-rw-r--r-- 1 user user 1.4K Sep 30 23:28 tardoor.tar.gz
```

> `-j` 是 bzip2。同样的目录，`.tar.bz2` 只有 295 字节，比 `.tar.gz` 的 1.4K 小很多——压缩率更高，代价是更慢。

### 示例 6：详细模式打包（`-v`）

```bash
tar -tvzf tardoor.tar.gz
```

```text
drwxr-xr-x user/user         0 2026-09-30 23:28 tardoor/
drwxr-xr-x user/user         0 2026-09-30 23:28 tardoor/sub/
-rw-r--r-- user/user         2 2026-09-30 23:28 tardoor/sub/f2.txt
-rw-r--r-- user/user   1048576 2026-09-30 23:28 tardoor/big.bin
-rw-r--r-- user/user         6 2026-09-30 23:28 tardoor/a.txt
```

> `-v` 配合 `-t` 显示每个文件的权限、大小、时间，像 `ls -l` 一样。

### 示例 7：打包时排除某些文件

```bash
tar -czf site.tar.gz --exclude='*.log' --exclude='.git' mysite/
```

> 跳过所有 `.log` 和 `.git` 目录，包更干净。

### 示例 8：只解包里的某几个文件

```bash
tar -xzf tardoor.tar.gz tardoor/a.txt tardoor/sub/f2.txt
```

> 在包名后面指定要解的文件路径，只解出这几个，不解全部。

### 示例 9：不压缩的纯打包（.tar）

```bash
tar -cf plain.tar tardoor
```

> 不加 `z/j/J` 就是纯打包、不压缩，`.tar` 文件。适合已经压缩过的内容（如 jpg/mp4）再压也没用。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `tar -czf 包.tar.gz 目录` | 打包 + gzip（**最常用**） |
| `tar -xzf 包.tar.gz` | 解开 .tar.gz |
| `tar -tzf 包.tar.gz` | 列出 .tar.gz 内容 |
| `tar -xzf 包.tar.gz -C 目录` | 解到指定目录 |
| `tar -cjf 包.tar.bz2 目录` | bzip2 高压缩打包 |
| `tar -xJf 包.tar.xz` | 解开 .tar.xz |
| `tar -czf 包.tar.gz --exclude='*.log' 目录` | 打包并排除 |

## 六、RHEL 系与 Debian 系差异

`tar` 都是 GNU tar，**两系用法完全一致**。细微差别：

- xz（`-J`）两系都支持，但需要装 `xz-utils`（Ubuntu 常默认带）；
- 解包时权限保留：root 解包默认保留属主，普通用户解包文件属主变成自己；
- 有些老系统 `tar` 是 BSD tar（如 macOS 默认），选项略有差异；Linux 上都是 GNU tar，放心用。

## 七、新手易错点

1. **`-f` 后面必须紧跟包名**：`tar -czf tardoor.tar.gz dir` 对；写成 `tar -czf dir tardoor.tar.gz` 会把 dir 当包名、把 tardoor.tar.gz 当要打包的文件，顺序反了。
2. **解压前先 `tar -tzf` 看内容**：防止包里是一堆绝对路径或散装文件，解压后到处都是。
3. **解压到当前目录容易污染**：养成先建目录再 `tar -xzf ... -C 目录` 的习惯。
4. **后缀和压缩选项要对应**：`.tar.gz` 用 `-z`、`.tar.bz2` 用 `-j`、`.tar.xz` 用 `-J`；用错会报"not in gzip format"。
5. **绝对路径打包有风险**：`tar -czf x.tar.gz /etc` 会带绝对路径，解包可能覆盖系统文件；习惯先 `cd /` 再打包相对路径。
6. **`--exclude` 要放在包名前**：选项位置不对会不生效。

## 八、相关命令与文档

- 速查页：[Linux 命令速查](../linux-commands#压缩与打包)
- zip 格式：`zip`/`unzip`（详解见 [zip-unzip](./zip-unzip)）
- 找大文件：`du`（详解见 [du](./du)）、`find`
- 文件系统：见 [Linux 文件系统专题](../../guide/linux-filesystem)
