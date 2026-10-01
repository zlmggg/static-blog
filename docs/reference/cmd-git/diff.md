# git diff 命令详解：看工作区、暂存区、分支之间到底改了什么

> 本文是 [Git 命令速查](../git-commands#日常四件套) 中 `git diff` 的从 0 到 1 详解。
> 目标：把 `git diff -h` 里的常用选项讲清楚，搞懂「工作区 vs 暂存区」「暂存区 vs HEAD」「两个分支之间」三种 diff 分别怎么打。
> 环境依据：Git 2.34.1（本机 `/tmp/demo` 实跑；RHEL/Rocky 用法一致）。

## 一、命令是干什么的

`git diff` 用来**对比两个版本之间的差异**——逐行显示哪些行加了、哪些行删了。提交前必看：先 `git diff` 看一眼改了啥，再 add/commit，能避免把调试代码、打印语句提交上去。

它能对比三种常见组合：

- **工作区 vs 暂存区**：`git diff`（不加参数）——你改了但还没 `git add` 的内容；
- **暂存区 vs 最近一次提交**：`git diff --cached`——已经 `git add`、准备提交的内容；
- **两个分支 / 两个提交之间**：`git diff 分支A 分支B`——历史版本对比。

> 类比：`git diff` 像 Word 的「审阅 → 比较文档」，左右两版逐行对比，红删绿加。区别是它用文字符号 `-`/`+` 表示。

## 二、命令语法

```bash
git diff [<选项>]            # 工作区 vs 暂存区
git diff --cached [<选项>]   # 暂存区 vs HEAD
git diff <提交A> <提交B>     # 两个提交/分支之间
git diff <分支A>..<分支B>    # 同上
```

- 不给参数：对比工作区和暂存区；
- `--cached`（或 `--staged`，等价）：对比暂存区和 HEAD；
- 给两个引用：对比两个版本；
- 末尾加 `-- <路径>`：只看某个文件 / 目录的差异。

## 三、选项全表（对照 `git diff -h`）

### 1. 控制输出形式

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-p`，默认 | 生成 patch 格式差异 | 看具体改了哪几行（最常用） |
| `--stat` | 只输出**统计**：改了几个文件、几行增删 | 提交前快速看改动规模 |
| `--shortstat` | 只输出最后一行汇总 | 只要「N 文件改动，N 插入 N 删除」 |
| `--numstat` | 机器可读的数字统计 | 脚本里用 |
| `--name-only` | 只列出改了哪些文件名 | 不关心内容，只要名单 |
| `--name-status` | 文件名 + 状态（M/A/D） | 看哪些改了、哪些新增、哪些删了 |
| `--check` | 检查是否有冲突标记 / 空白错误 | 提交前自查格式 |
| `-w`，`--ignore-all-space` | 忽略所有空白变化 | 只改了缩进时，过滤噪音 |
| `--ignore-blank-lines` | 忽略空行变化 | 同上 |
| `-U<n>` | 显示改动行前后 n 行上下文 | 默认 3 行，想多看就 `-U10` |

### 2. 范围与对比对象

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `--cached`，`--staged` | 对比暂存区 vs HEAD | 看「准备提交的内容」（提交前必看） |
| `<commit>` | 工作区 vs 某次提交 | 看从某次提交到现在改了啥 |
| `<commit1> <commit2>` | 两次提交之间 | 分支对比、code review |
| `<分支A>...<分支B>` | 两分支**共同祖先**到 B 的差异 | 看 B 分支相对分叉点改了啥（PR 常用） |
| `HEAD` | 当前最新提交 | `git diff HEAD` = 工作区 vs 最新提交（含已暂存） |
| `-- <路径>` | 只看指定文件/目录 | `git diff -- app.py` |

### 3. 其他常用

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `--color` | 彩色 diff | 终端默认开，强制就加 `--color=always` |
| `--word-diff` | 按**单词**对比而非整行 | 改了一长行里几个字时更清楚 |
| `-R` | 反转方向 | 看「从 B 回到 A」的差异 |
| `--binary` | 包含二进制文件 diff | 要生成可补丁的包时 |

## 四、由浅入深的典型示例

### 示例 1：看工作区改了什么（没 add 的部分）

先改个文件：

```bash
printf 'main branch v3\n' >> app.py
git diff app.py
```

```text
diff --git a/app.py b/app.py
index b9e055f..6c91108 100644
--- a/app.py
+++ b/app.py
@@ -1 +1,2 @@
 main branch v2 (merged)
+main branch v3
```

逐行读：

- `diff --git a/app.py b/app.py`：对比的两个版本，`a/` 是旧、`b/` 是新；
- `--- a/app.py` / `+++ b/app.py`：红色旧版、绿色新版；
- `@@ -1 +1,2 @@`：旧版从第 1 行起、新版从第 1 行起共 2 行；
- 没有前缀的行＝上下文；`+` 开头＝新增行；`-` 开头＝删除行。

### 示例 2：`git add` 之后，用 `--cached` 看暂存了什么

```bash
git add app.py
git diff --cached app.py
```

```text
diff --git a/app.py b/app.py
index b9e055f..6c91108 100644
--- a/app.py
+++ b/app.py
@@ -1 +1,2 @@
 main branch v2 (merged)
+main branch v3
```

> add 之后 `git diff`（不带 `--cached`）就空了，因为工作区和暂存区一致了。要看暂存区里准备提交什么，用 `git diff --cached`。提交前最后一眼永远看它。

### 示例 3：`--stat` 看改动规模（不看内容）

```bash
git diff --cached --stat
```

```text
 app.py | 1 +
 1 file changed, 1 insertion(+)
```

> 只告诉你：1 个文件改了，加了 1 行。改动文件多的时候先用它扫一眼规模，再决定要不要细看。

### 示例 4：两个分支之间的差异

```bash
git diff main feature/login
```

> 对比 `main` 和 `feature/login` 两个分支最终内容的差异。想只看文件名单：

```bash
git diff main feature/login --name-status
```

```text
A	auth.py
M	app.py
```

> `A`＝新增文件，`M`＝修改文件。

### 示例 5：`...` 三点——PR 式对比（看分支自己改了啥）

```bash
git diff main...feature/login
```

> 三点表示「从两个分支的共同祖先开始，到 feature/login 结束」的差异。这正是 PR/MR 页面显示的改动范围——只看你这个分支自己干了啥，不含 main 上别人后来的提交。

### 示例 6：忽略空白变化 `-w`

```bash
git diff -w app.py
```

> 当你只是改了缩进、空行，`git diff` 会把整行标成「删了又加」，很吵。加 `-w` 忽略所有空白差异，只看真正的代码改动。

### 示例 7：对比工作区和最近一次提交（含已暂存）

```bash
git diff HEAD app.py
```

> `git diff` 只看工作区 vs 暂存区；`git diff HEAD` 看工作区 vs 最新提交，**包含已暂存的改动**。想一眼看完「这次提交到底会改什么」，用它。

### 示例 8：检查空白错误与冲突标记

```bash
git diff --check
```

> 如果输出 `app.py:1: trailing whitespace.` 之类，说明有行尾空格；如果输出 `app.py:3: leftover conflict marker`，说明还有 `<<<<<<<` 冲突标记没清掉。提交前跑一遍。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `git diff` | 看工作区未暂存的改动 |
| `git diff --cached` | 看已暂存、准备提交的改动（提交前必看） |
| `git diff HEAD` | 看工作区 vs 最新提交（含暂存） |
| `git diff --stat` | 只看改了几个文件几行 |
| `git diff --name-status` | 只看文件名 + M/A/D |
| `git diff 分支A 分支B` | 对比两个分支 |
| `git diff A...B` | 看 B 相对分叉点改了啥（PR 视角） |
| `git diff -w` | 忽略空白 |
| `git diff --check` | 查冲突标记/行尾空格 |

## 六、RHEL 系与 Debian 系差异

`git diff` 属于 git 本体，**两系用法与输出完全一致**。唯一差别：

- 彩色 diff 默认开，但有些极简服务器（`TERM=dumb` 或无 tty）不显示颜色；脚本里强制彩色用 `--color=always`，重定向到文件时用 `--color=never`。
- 外部 diff 工具（如 `meld`、`vimdiff`）通过 `git config --global diff.tool meld` 配置，与发行版无关。

## 七、新手易错点

1. **`git diff` 看完是空的，但我明明改了文件**：因为你已经 `git add` 了。改用 `git diff --cached` 或 `git diff HEAD`。
2. **把 `git diff` 和 `git status` 搞混**：`status` 看「哪些文件变了」，`diff` 看「具体哪几行变了」。
3. **三点和两点分不清**：`A B` 比两分支最终差异；`A...B` 比分叉点到 B。PR 里要看自己分支改了啥，用三点。
4. **改了缩进导致整个文件 diff 全红全绿**：加 `-w` 过滤空白噪音。
5. **二进制文件 `git diff` 显示 "Binary files differ"**：正常，文字 diff 对图片/二进制无效。
6. **危险：`git diff > patch` 后别直接 `git apply` 到别的分支**——context 对不上会失败，这不是危险操作，但别拿 diff 当备份，备份要用 commit/tag。

## 八、相关命令与文档

- 速查页：[Git 命令速查](../git-commands#日常四件套)
- 看完 diff 怎么提交：[commit](./commit)
- 暂存管理：[add](./add)
- 看历史提交的 diff：`git log -p`（详解见 [log-show](./log-show)）
