# tree 命令详解：树状看目录结构

> 本文是 [Linux 命令速查](../linux-commands#文件与目录) 中 `tree` 的从 0 到 1 详解。
> 目标：把 `tree --help` 里的每个选项讲清楚，多看几遍后，你在服务器上敲 `tree --help` 就知道该用哪个选项。
> 环境依据：tree v2.0.2（本沙箱已装；属 `tree` 包，未装系统用 `yum install tree` 或 `apt install tree` 安装）。

## 一、命令是干什么的

`tree` 把一个目录的内容用**树状图**画出来，让你一眼看清"谁是谁的子目录、里面有哪些文件"。

- 不带参数：以当前目录为根画一棵树；
- 给目录名：画那个目录；
- 加 `-L 2`：只看两层，避免整棵树刷屏。

`ls` 是平铺列表，`tree` 是立体结构——看项目骨架时 `tree` 舒服得多。

> 类比：`ls` 像把文件夹里的东西排成一行平铺出来；`tree` 像把文件夹一层层展开成一棵倒挂的树，父子关系一目了然。

它**不随系统默认安装**：Ubuntu/Debian 用 `sudo apt install tree`，RHEL/CentOS/Rocky 用 `sudo yum install tree`。

## 二、命令语法

```bash
tree [选项]... [目录]
```

- `[选项]`：控制显示几层、含不含隐藏文件、要不要大小/权限/颜色等；
- `[目录]`：要看谁；不写就看当前目录。

最简单的用法：

```bash
tree
```

## 三、选项全表（对照 `tree --help`）

### 1. 控制"显示哪些内容、多深"

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-a` | 显示**所有文件**，包括隐藏文件 | 想看 `.git`、`.env` 等 |
| `-d` | **只列目录**，不列文件 | 只看骨架结构时 |
| `-L 层数` | 只往下看**指定层数** | **最常用**，`tree -L 2` 防刷屏 |
| `-l` | 把软链接当目录继续跟随 | 想顺着链接看真实目录时 |
| `-f` | 每个名字前打印**完整路径** | 需要路径方便复制时 |
| `-x` | 只在当前文件系统内，不进挂载点 | 避免连带列出其他盘 |
| `-R` | 到达最大层数后在每个目录里再跑一次 | 配合 `-L` 用 |
| `--noreport` | 结尾不打印"N directories, M files"统计 | 输出要干净时 |

### 2. 控制"按名字筛"

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-P 模式` | **只显示**匹配通配符的文件 | 如 `-P '*.py'` 只看 Python 文件 |
| `-I 模式` | **排除**匹配的文件 | 如 `-I '*.py'` 不看 py 文件 |
| `--matchdirs` | 让 `-P` 连目录名一起匹配 | 想按目录名过滤时 |
| `--ignore-case` | 匹配时忽略大小写 | 文件名大小写不一时 |
| `--filelimit #` | 文件数超过 # 的目录不进入 | 跳过 node_modules 这种大目录 |
| `--gitignore` | 按 `.gitignore` 规则过滤 | 看 git 项目时忽略被忽略的文件 |

### 3. 控制"显示哪些元信息"

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-p` | 显示**权限** | 看每个文件什么权限 |
| `-u` | 显示**属主** | 看谁建的 |
| `-g` | 显示**属组** | 看属组 |
| `-s` | 显示**字节大小** | 精确大小 |
| `-h` | 大小用**人类可读**（K/M） | 配合 `-s`，看大小舒服 |
| `--si` | 同 `-h`，但按 1000 换算 | 厂商口径 |
| `-D` | 显示**修改日期** | 看新旧 |
| `--timefmt 格式` | 自定义时间格式 | 想要特定日期样式 |
| `-F` | 给名字加类型标记（`/`目录、`*`可执行等） | 一眼区分类型 |
| `--inodes` | 显示每个文件的 inode 号 | 排查硬链接 |
| `--device` | 显示每个文件所在设备号 | 跨文件系统排查 |
| `-Q` | 文件名加双引号 | 文件名带空格时 |

### 4. 控制"排序和图形"

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-v` | 按版本号自然排序 | 文件名带数字时 |
| `-t` | 按**修改时间**排序 | 找最近改动 |
| `-c` | 按**状态改变时间**排序 | 看属性改动 |
| `-r` | 逆序 | 倒过来 |
| `-U` | **不排序**（最快，按磁盘顺序） | 追求速度 |
| `--dirsfirst` | **目录排在文件前** | 看结构更清晰 |
| `--sort=X` | 显式指定排序（`name/version/size/mtime/ctime`） | 用长选项 |
| `-i` | 不画缩进连线 | 输出给程序处理 |
| `-A` | 用 ANSI 字符画缩进线 | 终端不支持 Unicode 时 |
| `-n` / `-C` | 关闭/开启颜色 | 终端颜色异常时手动控 |

### 5. 导出成 XML / HTML / JSON

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-o 文件名` | 输出到文件而不是屏幕 | 存一份目录树文档 |
| `-X` | 输出 **XML** | 给程序解析 |
| `-J` | 输出 **JSON** | 给程序解析 |
| `-H 网址` | 输出 **HTML** 网页版 | 做可点的目录树 |
| `-T 标题` | 配合 `-H` 改网页标题 | 自定义 HTML 标题 |

## 四、由浅入深的典型示例

### 示例 1：基本树状

```bash
tree project
```

```text
project
├── assets
│   └── logo.png
├── docs
│   └── readme.md
└── src
    ├── components
    │   └── Button.py
    ├── main.py
    └── utils
        └── helper.py

5 directories, 5 files
```

> 结尾统计：5 个目录、5 个文件。

### 示例 2：-L 限制层数（最常用）

```bash
tree -L 2 project
```

```text
project
├── assets
│   └── logo.png
├── docs
│   └── readme.md
└── src
    ├── components
    ├── main.py
    └── utils

5 directories, 3 files
```

> 只看两层，再深的 `components/Button.py` 就不展开了。项目大时必加 `-L`。

### 示例 3：-a 看隐藏文件

```bash
tree -a project
```

```text
project
├── assets
│   └── logo.png
├── docs
│   └── readme.md
├── .hidden
└── src
    ├── components
    │   └── Button.py
    ├── main.py
    └── utils
        └── helper.py

5 directories, 6 files
```

> 多了 `.hidden` 这个默认不显示的隐藏文件。

### 示例 4：-d 只看目录骨架

```bash
tree -d project
```

```text
project
├── assets
├── docs
└── src
    ├── components
    └── utils

5 directories
```

> 不显示任何文件，只看目录层级。

### 示例 5：-f 带完整路径

```bash
tree -L 1 -f project
```

```text
project
├── project/assets
├── project/docs
└── project/src

3 directories, 0 files
```

### 示例 6：-h 可读大小 + -p 权限

```bash
tree -L 2 -h -p project
```

```text
[drwxr-xr-x 4.0K]  project
├── [drwxr-xr-x 4.0K]  assets
│   └── [-rw-r--r--    2]  logo.png
├── [drwxr-xr-x 4.0K]  docs
│   └── [-rw-r--r--    2]  readme.md
└── [drwxr-xr-x 4.0K]  src
    ├── [drwxr-xr-x 4.0K]  components
    ├── [-rw-r--r--    2]  main.py
    └── [drwxr-xr-x 4.0K]  utils

5 directories, 3 files
```

### 示例 7：-P 只看某类文件

```bash
tree -P '*.py' project
```

```text
project
├── assets
├── docs
└── src
    ├── components
    │   └── Button.py
    ├── main.py
    └── utils
        └── helper.py

5 directories, 3 files
```

> 只保留 `.py` 文件（目录仍显示，否则树就断了）。

### 示例 8：-I 排除某类文件

```bash
tree -I '*.py' project
```

```text
project
├── assets
│   └── logo.png
├── docs
│   └── readme.md
└── src
    ├── components
    └── utils

5 directories, 2 files
```

> `.py` 文件全部不显示。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `tree` | 看当前目录树 |
| `tree -L 2` | 只看两层（**最常用**） |
| `tree -L 3 -a` | 三层 + 含隐藏文件 |
| `tree -d` | 只看目录骨架 |
| `tree -h` | 带可读大小 |
| `tree -I 'node_modules'` | 排除某些目录 |
| `tree -P '*.conf'` | 只看某类文件 |

## 六、RHEL 系与 Debian 系差异

- `tree` **两系都不默认安装**：Debian/Ubuntu 用 `sudo apt install tree`，RHEL/CentOS/Rocky 用 `sudo yum install tree`（CentOS 8+ 用 `dnf install tree`）；
- 装完后选项行为基本一致；不同发行版自带的 tree 大版本可能略有差异，以本机 `tree --help` 为准。

## 七、新手易错点

1. **没装会报 `command not found`**：先 `apt install tree` / `yum install tree`。
2. **大树不限制层数会刷屏**：`tree 某超大目录` 能吐几屏，养成 `-L 2` 的习惯。
3. **`-P`/`-I` 要加引号**：通配符用单引号包起来，别让 shell 先把它展开了。
4. **它只读不改**：`tree` 纯展示，安全；不影响任何文件。
5. **看隐藏文件要 `-a`**：否则 `.git`、`.env` 默认不出现。

## 八、相关命令与文档

- 速查页：[Linux 命令速查](../linux-commands)
- 平铺列出目录：`ls`（详解见 [ls](./ls)）
- 按条件查找文件：`find`（详解见 [find](./find)）
- 看磁盘占用：`du`（详解见 [du](./du)）
- 文件系统结构：见 [Linux 文件系统](../../guide/linux-filesystem)
