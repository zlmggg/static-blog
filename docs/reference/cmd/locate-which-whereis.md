# locate / which / whereis 命令详解：三种"找东西"的小工具

> 本文是 [Linux 命令速查](../linux-commands#文件与目录) 中 `locate`、`which`、`whereis` 的从 0 到 1 详解，本篇一次讲清这三个查找小命令。
> 目标：把它们各自的用途和常用选项讲清楚，多看几遍后，你就知道"找文件名、找命令位置、找命令相关文件"分别该用哪个。
> 环境依据：本机实跑 `which`（debianutils）、`whereis`（util-linux 2.37.2）；`locate` 本机未安装，选项依据 GNU locate 官方手册（man-pages，findutils；现代 Ubuntu/Debian 默认由 `plocate` 包提供）。

## 一、命令是干什么的

这三个都是"找东西"，但找的对象不同：

- `locate 关键词`：**按文件名**全盘找，查的是预先建好的数据库，**极快**，但可能不是最新的；
- `which 命令名`：找**某个命令的可执行文件**在哪个路径（你敲这个命令时 shell 实际跑的是哪个）；
- `whereis 命令名`：找某个命令的**二进制、源码、man 手册**都在哪。

> 类比：
> - `locate` 像查图书馆的电子检索卡片——输入书名关键词秒出结果，但卡片是上周整理的，新进的书可能查不到；
> - `which` 像问"我喊'小明'这个名字，屋里到底答应的是哪个小明"——告诉你 `python3` 实际跑的是 `/opt/python3.12/bin/python3`；
> - `whereis` 比 `which` 多查一步，连它的说明书（man 页）和源码位置一起给你。

## 二、命令语法

```bash
locate [选项]... 关键词...
which 命令名...
whereis [选项]... 命令名...
```

- `locate`：给要找的文件名关键词，它查数据库列出匹配路径；
- `which`：给命令名，输出该命令的完整路径；
- `whereis`：给命令名，输出二进制、man 页等位置。

## 三、选项全表

### 1. locate（依据官方手册）

> `locate` 不在本机，下列选项依据 GNU locate 手册（现代 plocate 基本兼容）。它的核心原理：搜索一个**预先由 `updatedb` 建好的文件名数据库**，而不是实时翻磁盘。

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-i`，`--ignore-case` | 忽略大小写匹配 | 记不准大小写时 |
| `-r 正则`，`--regex` | 用**正则表达式**匹配路径 | 复杂模式查找 |
| `-c`，`--count` | 只输出**匹配到多少个**，不列文件名 | 只想知道数量时 |
| `-l N`，`--limit=N` | 最多列 N 条结果 | 结果太多截断 |
| `-e`，`--existing` | 只列出**当前还存在**的文件 | 数据库里已删除的不显示 |
| `-b`，`--basename` | 只匹配**文件名本身**（不匹配完整路径） | 精确找文件名 |
| `-d 路径`，`--database=路径` | 指定用哪个数据库文件 | 用自定义数据库时 |
| `-S`，`--statistics` | 显示数据库的**统计信息**（条数、位置） | 看数据库多久没更新 |
| `-0`，`--null` | 结果用 NUL 分隔 | 配合 xargs 处理奇怪文件名 |

> 关键点：数据库由 `updatedb` 命令生成/更新，通常每天由 cron 自动跑一次。**刚新建的文件 locate 暂时查不到**，要手动 `sudo updatedb` 后再查；数据库超过约 8 天 locate 会提示。

### 2. which（本机实跑）

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| （不带选项） | 输出命令的完整路径 | 最常用：`which python3` |
| `-a` | 列出 PATH 中**所有**同名命令 | 系统里装了多个同名命令想看全 |

> `which` 只在 `PATH` 环境变量列出的目录里找，找到第一个就停（除非 `-a`）。

### 3. whereis（本机实跑）

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-b` | 只找**二进制**文件 | 只要可执行路径 |
| `-m` | 只找 **man 手册** | 想知道手册在哪 |
| `-s` | 只找**源码** | 想找源码位置 |
| `-u` | 找"不寻常"的（缺二进制或缺手册的） | 排查安装不完整时 |

> `whereis` 不仅找二进制，还顺带找该命令的 man 手册页路径。

## 四、由浅入深的典型示例

### 示例 1：which——看命令到底跑的是哪个

```bash
which ls
```

```text
/usr/bin/ls
```

```bash
which python3 grep sed
```

```text
/opt/python3.12/bin/python3
/usr/bin/grep
/usr/bin/sed
```

> 一次给多个命令，分别列出路径。注意 `python3` 指向 `/opt/python3.12`，不是默认的 `/usr/bin`——这正是 `which` 的价值：搞清你敲命令时真正执行的是谁。

### 示例 2：which 找不到命令

```bash
which nonexistentcmd
```

> 没有任何输出，退出码为 1。脚本里常用 `which xxx || echo "没装"` 来判断命令是否存在。

### 示例 3：whereis——连手册位置一起看

```bash
whereis ls
```

```text
ls: /usr/bin/ls
```

```bash
whereis gcc
```

```text
gcc: /usr/bin/gcc /usr/lib/gcc /usr/share/gcc
```

> `whereis gcc` 一次给出二进制 `/usr/bin/gcc`、库目录 `/usr/lib/gcc`、手册相关 `/usr/share/gcc` 多处位置。

### 示例 4：whereis 只看二进制 / 只看手册

```bash
whereis -b bash
whereis -m bash
```

> `-b` 只列可执行文件路径，`-m` 只列 man 手册位置。

### 示例 5：locate 按文件名快速找（依据官方手册，本机未装）

```bash
locate nginx.conf
```

> 示意（依据官方手册）：会瞬间列出数据库里所有路径含 `nginx.conf` 的文件，例如 `/etc/nginx/nginx.conf`。因为是查数据库，比 `find / -name nginx.conf` 快几个数量级。

### 示例 6：locate 忽略大小写 + 限制条数

```bash
locate -i -l 5 readme
```

> 忽略大小写、最多列 5 条。记不准大小写时加 `-i`。

### 示例 7：locate 用正则

```bash
locate -r '\.conf$'
```

> `-r` 后面接正则，这里列出所有以 `.conf` 结尾的文件。

### 示例 8：locate 查数量、看数据库统计

```bash
locate -c nginx
locate -S
```

> `-c` 只数匹配到多少条；`-S` 打印数据库里总共收录了多少文件、数据库在哪——发现查不到新文件时，先 `-S` 看数据库年龄，再 `sudo updatedb` 更新。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `which 命令` | 看命令实际路径 |
| `which -a 命令` | 看所有同名命令 |
| `whereis 命令` | 看命令二进制 + 手册位置 |
| `locate 关键词` | 按文件名秒查数据库 |
| `locate -i 关键词` | 忽略大小写 |
| `sudo updatedb` | 手动刷新 locate 数据库 |
| `type 命令` | 看是别名/内建/外部命令（见 Shell 篇） |

## 六、RHEL 系与 Debian 系差异

- **`which`**：Debian/Ubuntu 上来自 `debianutils`，RHEL 上是 `which` 包，用法一致；RHEL 的 `which` 有时默认带别名行为。
- **`whereis`**：两系都属 util-linux，一致。
- **`locate`**：包名不同——现代 Ubuntu/Debian 默认 `plocate`（更快），老版本和 RHEL 传统用 `mlocate`；两者都提供 `locate` 命令、都依赖 `updatedb` 建库。用法几乎一样。**本机未安装**，需 `sudo apt install plocate`（Debian）或 `sudo dnf install plocate`（RHEL）后用。

## 七、新手易错点

1. **`locate` 查不到刚建的文件**：它查的是定时更新的数据库，新文件要等 `updatedb` 跑完（或手动 `sudo updatedb`）才能查到。
2. **`locate` 可能列出已删除的文件**：数据库是旧的，加 `-e` 只显示当前还存在的。
3. **`which` 找不到 shell 内建命令**：`cd`、`alias` 这种是 shell 自带的，`which cd` 可能没结果，要用 `type cd`。
4. **`which` 只看 PATH**：不在 PATH 里的命令它找不到，要写全路径。
5. **`locate` 快但不精确、`find` 慢但精确**：日常凭印象找文件用 locate；要按大小/时间/权限精确筛，还是得 `find`。
6. **危险提示**：`locate` 结果直接接 `xargs rm` 要小心——数据库可能含已删/重复路径，先 `-c` 或 `-e` 核对。

## 八、相关命令与文档

- 速查页：[Linux 命令速查](../linux-commands#文件与目录)
- 实时、按条件精确找文件：`find`（详解见 [find](./find)）
- 把找到的文件名批量交给命令：`xargs`（详解见 [xargs](./xargs)）
- Shell 内建命令与 PATH：见 [Linux Shell 专题](../../guide/linux-shell)
