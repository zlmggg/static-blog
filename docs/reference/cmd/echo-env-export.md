# echo、env 与 export 命令详解：打印输出、看环境变量、设环境变量

> 本文是 [Linux 命令速查](../linux-commands#Shell 基础) 中 `echo`、`env`、`export` 的从 0 到 1 详解。
> 目标：把 `echo -e/-n`、`env` 列环境变量、`export` 设环境变量和 PATH 讲清楚，多看几遍后，你在服务器上敲 `export PATH=...` 就知道怎么配环境变量。
> 环境依据：`echo`、`export` 是 **bash 内建**（用 `help echo`/`help export`），同时 GNU coreutils 也提供 `/usr/bin/echo`；`env` 属 GNU coreutils 8.32。Ubuntu 22.04 自带，RHEL 同。

## 一、命令是干什么的

三个命令都和"输出/环境变量"有关：

- **`echo`**：把后面的文本**打印到屏幕**。写脚本时输出进度、调试变量值最常用。
- **`env`**：列出当前**所有环境变量**（或在指定环境变量下运行某命令）。
- **`export`**：把一个 shell 变量**导出为环境变量**，让它被子进程（你启动的其他程序）看到。

> 类比：`echo` 是"喊话"（把文字打出来）；`env` 是"查看当前房间里挂着哪些牌子"；`export` 是"把你设的牌子挂到门上，让进来的人（子进程）也能看到"。

最经典的问题：为什么你在终端 `FOO=bar` 后，写的脚本读不到 `FOO`？因为没有 `export`——普通变量只在当前 shell 里，子进程看不到；`export FOO=bar` 后子进程才能继承。

## 二、命令语法

```bash
# echo（bash 内建）
echo [-neE] [文本]...

# env（coreutils）
env [选项]... [名字=值]... [命令 [参数]...]

# export（bash 内建）
export [-fn] [名字[=值]]...
export -p
```

- `echo hello`：直接打印；
- `env` 不带命令：列出所有环境变量；
- `export VAR=值`：设并导出环境变量；
- `export -p`：列出所有已导出的变量。

## 三、选项全表（对照 `help echo` / `env --help` / `help export`）

### 1. echo 常用选项

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-n` | 输出后**不换行** | 脚本里同一行打印进度 |
| `-e` | 解释反斜杠转义符（`\n` 换行、`\t` 制表符） | 想输出换行/制表符时 |
| `-E` | 不解释转义符（默认） | 显式关闭转义 |

`-e` 常用转义：`\n` 换行、`\t` 制表符、`\\` 反斜杠、`\a` 响铃、`\c` 不再继续输出。

### 2. env 常用选项

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| （无参数） | 列出所有环境变量 | 看当前环境 |
| `名字=值` | 在运行命令前设一个环境变量 | 临时给某命令设变量 |
| `-i`，`--ignore-environment` | 从**空环境**开始 | 干净环境调试 |
| `-u 名字`，`--unset=名字` | 运行前去掉某个变量 | 临时屏蔽某变量 |
| `-C 目录`，`--chdir=目录` | 先切到某目录再运行 | 在指定目录跑命令 |
| `-0`，`--null` | 每行用 NUL 而非换行结尾 | 脚本安全处理 |
| `命令` | 用指定环境运行命令 | `env FOO=bar python app.py` |

### 3. export 常用选项

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `名字=值` | 设变量并导出 | 最常用 |
| `-p` | 列出所有已导出的变量 | 看导出了啥 |
| `-n` | **取消**导出（变量还在，但不再传给子进程） | 临时取消导出 |
| `-f` | 导出的是 shell 函数 | 较少用 |

## 四、由浅入深的典型示例

### 示例 1：基本打印

```bash
echo "hello world"
```

```text
hello world
```

> 把后面的文本原样打印，自动加换行。

### 示例 2：打印变量值

```bash
NAME=SRE
echo $NAME
```

```text
SRE
```

> `$变量名` 取值。脚本里调试"这个变量到底是什么"全靠 `echo $VAR`。

### 示例 3：输出换行和制表符（`-e`）

```bash
echo -e "line1\nline2\ttab"
```

```text
line1
line2	tab
```

> 不加 `-e` 时 `\n`、`\t` 会被当成字面字符打印；加 `-e` 才解释成换行/制表。

### 示例 4：不换行（`-n`）

```bash
echo -n "loading..."; sleep 1; echo " done"
```

```text
loading... done
```

> `-n` 让两行输出拼在同一行，做进度提示很常见。

### 示例 5：列出所有环境变量

```bash
env | grep -E '^(PATH|HOME|USER|SHELL|PWD)='
```

```text
PWD=/tmp
HOME=/home/user
USER=user
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
```

> `env` 输出 `名字=值` 一行一个，配合 `grep` 找你关心的变量。

### 示例 6：设并导出环境变量

```bash
export MY_VAR="hello"
echo $MY_VAR
```

> 当前 shell 和随后启动的子进程都能看到 `MY_VAR`。想永久生效写进 `~/.bashrc`：
>
> ```bash
> export MY_VAR="hello"
> export PATH="$PATH:/opt/mybin"
> ```

### 示例 7：临时给某命令设变量（不污染当前 shell）

```bash
env DEBUG=1 python app.py
```

> 只在跑 `python app.py` 这一次时让 `DEBUG=1`，命令结束后当前 shell 并没有这个变量。这比先 `export` 再 `unset` 干净。

### 示例 8：改 PATH（把自己的脚本目录加进去）

```bash
export PATH="$PATH:/home/user/bin"
```

> 把 `/home/user/bin` 追加到 PATH 末尾，这样里面的可执行文件在任何目录都能直接敲名字运行。写进 `~/.bashrc` 永久生效。

### 示例 9：在干净环境下运行命令

```bash
env -i /usr/bin/ls
```

> `-i` 清空所有环境变量（连 PATH 都没了），所以命令得用绝对路径。用于排查"是不是某个环境变量导致的问题"。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `echo $VAR` | 打印变量值（调试） |
| `echo -e "a\nb"` | 输出换行 |
| `echo -n "x"` | 不换行 |
| `env` / `env \| grep VAR` | 看环境变量 |
| `export VAR=值` | 设并导出变量 |
| `export PATH="$PATH:/dir"` | 追加 PATH |
| `env VAR=值 命令` | 临时给命令设变量 |
| `~/.bashrc` | 永久保存 |

## 六、RHEL 系与 Debian 系差异

- `echo`/`export` 是 bash 内建，`env` 是 coreutils，**两系用法完全一致**。
- 永久配置文件：两系用户级都写 `~/.bashrc`（或 `~/.bash_profile`）；系统级在 `/etc/profile`、`/etc/profile.d/*.sh`、`/etc/environment`。
- 注意：Ubuntu 的默认登录 shell 配置文件和 RHEL 略有差异（`~/.profile` vs `~/.bash_profile`），但 `export` 语法一样。
- 非交互 shell（脚本/ssh 远程执行）不一定读 `~/.bashrc`，这就是为什么"终端里设了变量、cron 里却没有"。

## 七、新手易错点

1. **`VAR=值` 不 export，子进程读不到**：这是最经典的坑。当前 shell 能 `echo $VAR`，但启动的脚本/程序看不到；要 `export VAR=值`。
2. **改 PATH 用 `=` 直接覆盖会出事**：`export PATH=/dir` 会把原来的 PATH 清空，系统命令都找不到了；一定要 `export PATH="$PATH:/dir"` 追加。
3. **`echo $VAR` 没加引号**：变量含空格时会被拆词；稳妥写法 `echo "$VAR"`。
4. **改了 `~/.bashrc` 不生效**：当前 shell 要 `source ~/.bashrc` 或开新终端。
5. **`env -i` 后命令找不到**：因为 PATH 被清空了，得用绝对路径。
6. **`echo` 是内建也有外部命令**：`/bin/echo` 的转义行为和 bash 内建略有差异，脚本里一般用内建的（直接写 `echo`）。

## 八、相关命令与文档

- 速查页：[Linux 命令速查](../linux-commands#Shell 基础)
- 命令历史与别名：`history`/`alias`（详解见 [history-alias](./history-alias)）
- 脚本与环境变量：见 [Linux Shell 专题](../../guide/linux-shell)
