# git add 与 git status 命令详解：把改动放进暂存区、随时看现在的状态

> 本文是 [Git 命令速查](../git-commands#日常四件套) 中 `git add` 与 `git status` 的从 0 到 1 详解。本篇一次讲清「把哪些改动准备好提交」和「随时查看仓库现在干到哪一步」。
> 目标：把 `git add -h`、`git status -h` 里的选项讲清楚，看懂 `git status -s` 输出里 `M`、`??`、`A` 到底什么意思。
> 环境依据：Git 2.34.1（本机 `/tmp/demo` 实跑；RHEL/Rocky 用法一致）。

## 一、命令是干什么的

Git 提交分两步：**先 `git add` 把改动放进「暂存区」（index），再 `git commit` 把暂存区里的内容打包成一次提交**。

- `git add`：把工作区的改动「登记」到暂存区。它不是「存盘」，只是「告诉 Git：下一次提交要带上这些」。
- `git status`：看现在工作区、暂存区分别有什么改动——哪些文件改了没加、加了没提交、还有哪些是全新未跟踪的文件。

> 类比：暂存区像超市收银台前的「待结账篮筐」。你改文件＝往购物车里扔东西；`git add`＝把东西放进待结账篮；`git commit`＝扫码结账打小票。`git status` 就是低头看看：购物车里还有啥没放篮里、篮里都装了啥。

## 二、命令语法

```bash
git add [<选项>] [--] <路径>...
git status [<选项>] [--] [<路径>...]
```

- `git add <路径>`：指定要加哪些文件 / 目录；`.` 表示当前目录所有改动；
- `git status`：不给路径就看整个仓库；
- `--`：路径里若有跟选项同名的文件（比如叫 `-f` 的文件），用 `--` 分隔避免误解。

## 三、选项全表（对照 `git add -h` 与 `git status -h`）

### 1. git add 的选项

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `<路径>` | 加指定文件 | `git add app.py`（最常用） |
| `.` | 加当前目录所有改动 | `git add .`（提交前一把梭） |
| `-A`，`--all` | 加**所有**改动（新增/修改/删除，全仓库） | 跟 `.` 类似，但跨目录也生效 |
| `-u`，`--update` | 只更新**已跟踪**文件（不含新文件） | 改了一堆老文件、不想带新文件时 |
| `-p`，`--patch` | **交互式逐块**挑选改动 | 一个文件里改了好几处，只想提交其中一两块时（很好用） |
| `-i`，`--interactive` | 交互式菜单挑选 | 比 `-p` 更全的交互，新手用得少 |
| `-e`，`--edit` | 直接编辑 diff 再应用 | 手工删改 hunk，高级用法 |
| `-f`，`--force` | 强制加被 `.gitignore` 忽略的文件 | 误忽略时应急 |
| `-n`，`--dry-run` | 试运行，不真加 | 先看 `git add .` 会加哪些文件 |
| `-v`，`--verbose` | 显示加了哪些 | 排查时 |
| `-N`，`--intent-to-add` | 只标记「这个文件以后会加」 | 让新文件在 `git diff` 里可见，高级用法 |

### 2. git status 的选项

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-s`，`--short` | **短格式**（一行一个文件） | 日常最常用，干净 |
| `-b`，`--branch` | 显示当前分支与跟踪关系 | 短格式里也带分支信息 |
| `--long` | 长格式（默认） | 想看到完整提示文字时 |
| `-u<模式>`，`--untracked-files=<模式>` | 未跟踪文件显示粒度（`all`/`normal`/`no`） | `-uno` 不显示未跟踪文件，刷版更干净 |
| `--ignored` | 连被忽略的文件也列出来 | 排查「为什么我的文件没被跟踪」 |
| `-v`，`--verbose` | 额外显示暂存区 diff | 想看暂存了什么内容 |
| `--porcelain[=<版本>]` | 机器可读格式 | 脚本里用，别给人看 |
| `--column` | 未跟踪文件多列排列 | 审美需求 |

## 四、由浅入深的典型示例

### 示例 1：改了一个已跟踪文件 + 新增一个未跟踪文件，看长格式 status

先造点改动：

```bash
printf 'main branch v3\n' >> app.py
printf 'temp\n' > scratch.txt
git status
```

```text
On branch main
Your branch is up to date with 'origin/main'.

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
	modified:   app.py

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	scratch.txt

no changes added to commit (use "git add" and/or "git commit -a")
```

> 三段话对应三件事：`app.py` 改了但**还没 add**；`scratch.txt` 是全新文件 Git 还没跟踪；`no changes added to commit` 意思是暂存区是空的。

### 示例 2：短格式 status（最常用，看懂 X Y）

```bash
git status -s
```

```text
 M app.py
?? scratch.txt
```

短格式每行固定两列状态码 + 文件名：

- 第一列 = **暂存区**状态（相对 HEAD）；
- 第二列 = **工作区**状态（相对暂存区）。

读这两行：

- ` M app.py`：第一列空格、第二列 `M` → 工作区改了，但还没 `git add` 到暂存区；
- `?? scratch.txt`：`??` → 全新未跟踪文件，从没被 add 过。

常见组合速查：

```text
 M  文件改了，未暂存
M   文件改了，已暂存（第一列 M）
MM  已暂存后又改了一次（暂存区和工作区不一致）
A   新文件已暂存（git add 过）
??  未跟踪
D   文件被删了
```

### 示例 3：把改动加进暂存区，再看 status 变化

```bash
git add app.py
git status -s
```

```text
M  app.py
?? scratch.txt
```

> 现在 `app.py` 从 ` M` 变成 `M `（第一列 M、第二列空格），说明改动已经进暂存区了。`scratch.txt` 还是 `??`，因为还没 add。

### 示例 4：`git add .` 一把加当前目录所有改动

```bash
git add .
git status -s
```

```text
A  scratch.txt
M  app.py
```

> `git add .` 把当前目录下所有改动（包括新文件 `scratch.txt`）都加进去。`scratch.txt` 变成 `A `（已暂存的新文件）。

### 示例 5：`git add -A` 跨目录加所有改动（含删除）

```bash
rm scratch.txt
git add -A
git status -s
```

```text
D  scratch.txt
M  app.py
```

> `-A` 会把「删除文件」这种改动也加进去。`.` 只加当前目录，`-A` 加整个仓库（不管你在哪个子目录执行）。

### 示例 6：`git add -p` 交互式挑 hunk（一个文件只提交一半改动）

```bash
git add -p app.py
```

> 会逐段弹出类似：
>
> ```text
> diff --git a/app.py b/app.py
> @@ -1 +1,2 @@
>  main branch v2 (merged)
> +main branch v3
> Stage this hunk [y,n,q,a,d,s,e,?]?
> ```
>
> 输入 `y` 收下这块、`n` 不要、`q` 退出、`s` 把大块再拆小。适合「我这次只想提交这个文件里的第 1 处改动，第 2 处等下一次提交」。

### 示例 7：先 dry-run 看会加什么，再真加

```bash
git add -n .
```

```text
add 'app.py'
add 'scratch.txt'
```

> `-n` 不真加，只告诉你会加哪些。提交前怕 `git add .` 误带东西时，先 `-n` 一眼。

### 示例 8：`.gitignore` 生效与 `-f` 强制加

```bash
echo "*.log" > .gitignore
echo "hi" > debug.log
git status -s        # debug.log 不出现，因为被忽略
git add -f debug.log  # 强制加进来
git status -s
```

> `.gitignore` 里的文件默认 `git add .` 不会带进来。真要加（比如非要提交一个日志样本），用 `-f`。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `git status` | 长格式看状态 |
| `git status -s` | 短格式看状态（**日常**） |
| `git add <文件>` | 加指定文件 |
| `git add .` | 加当前目录所有改动 |
| `git add -A` | 加整个仓库所有改动（含删除） |
| `git add -p` | 交互式逐块挑改动 |
| `git add -n .` | 预览会加哪些文件 |

## 六、RHEL 系与 Debian 系差异

`add` / `status` 属于 git 本体，**两系用法与输出完全一致**。唯一细微差别：

- 很多发行版默认给 `git status` 配了彩色（红色＝工作区改动、绿色＝已暂存）。两系都默认开，想关就 `git config --global color.ui false`。
- 别名：`git st` 是社区最常见的别名（见 [config](./config)），但不是 Git 内置，需要自己配。

## 七、新手易错点

1. **`git add .` 不是提交**：它只把改动放进暂存区，不加 `git commit` 不会产生任何提交。新手最常问「我 add 了为什么没记录」。
2. **改完文件又改了一次，`git add` 之后的新改动不会自动进暂存区**：暂存区拍的是 add 那一刻的快照。add 后又改了，要再 `git add` 一次（`git status -s` 会显示 `MM`）。
3. **`git add .` 和 `git add -A` 的区别**：`.` 只加当前目录及子目录；`-A` 加整个仓库。在子目录里 `git add .` 容易漏掉别的目录的删除改动。
4. **`??` 文件不是「出错了」**：只是 Git 还不认识它，正常现象。不想让它出现就 `.gitignore` 或 add 它。
5. **危险：`git add -f` 会强行加被忽略的敏感文件**（`.env`、密钥），加进仓库后即使删掉，历史里还在。提交前 `git status -s` 多看一眼。
6. **不要用 `git add *`**：shell 的 `*` 不匹配以 `.` 开头的文件，且行为和 `git add .` 不同。统一用 `git add .` 或 `git add -A`。

## 八、相关命令与文档

- 速查页：[Git 命令速查](../git-commands#日常四件套)
- 暂存之后怎么提交：`git commit`（详解见 [commit](./commit)）
- 暂存了又后悔怎么撤：`git restore` / `git reset`（详解见 [reset-revert-restore](./reset-revert-restore)）
- 看具体改了什么内容：`git diff`（详解见 [diff](./diff)）
