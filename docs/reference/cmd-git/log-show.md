# git log、git show、git blame 命令详解：翻历史、看某次提交、查某行是谁写的

> 本文是 [Git 命令速查](../git-commands#查看历史) 中 `git log`、`git show`、`git blame` 的从 0 到 1 详解。本篇一次讲清「翻提交历史」「看某次提交的详情」「查某行代码最后是谁改的」。
> 目标：把 `git log` 的过滤/格式化选项讲清楚，搞懂 `--oneline`、`--graph`、`-p`、`--author`、`-S` 分别干什么。
> 环境依据：Git 2.34.1（本机 `/tmp/demo` 实跑；RHEL/Rocky 用法一致）。

## 一、命令是干什么的

- `git log`：列出提交历史——谁、什么时候、写了什么信息。它是 Git 的「时间机器入口」。
- `git show`：看**某一次具体提交**的详情——完整信息 + 这次改了哪些行。也能看标签、文件内容。
- `git blame`：逐行标注**这个文件每一行最后是谁、哪次提交改的**。线上出 bug 想「这行代码谁加的」时用它。

> 类比：`git log` 像翻账本目录，`git show` 像抽出某一页看明细，`git blame` 像给每行代码贴上「最后修改人」的标签。

## 二、命令语法

```bash
git log [<选项>] [<分支/提交范围>] [[--] <路径>]
git show [<提交/标签/文件>]
git blame [<选项>] [--] <文件>
```

- `git log` 不给参数：从当前 HEAD 往回列所有提交；
- 给 `-- <路径>`：只看改了某文件的提交；
- `git show <提交>`：默认显示该提交的信息 + diff；
- `git blame <文件>`：逐行标注作者。

## 三、选项全表（对照 `git log -h`、`git show -h`、`git blame -h`）

### 1. git log——控制输出多紧凑

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `--oneline` | 每次提交压成**一行**（短哈希 + 标题） | 日常翻历史最常用 |
| `-n <N>` | 只列最近 N 次 | `git log -n 5` |
| `--stat` | 每次提交附文件改动统计 | 看每次改了哪些文件 |
| `-p`，`--patch` | 每次提交附完整 diff | 看历史每处改动内容 |
| `--name-only` | 只列改动文件名 | 简洁 |
| `--graph` | 用 ASCII 画出**分支合并图** | 看分支拓扑（常配 `--oneline --all`） |
| `--decorate` | 显示提交上挂的分支/标签名 | 看哪个提交在哪个分支上 |
| `--all` | 列**所有分支**的提交 | 全局看历史 |
| `--no-merges` | 不显示合并提交 | 只看真实业务提交 |

### 2. git log——按条件过滤

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `--author=<人>` | 按作者过滤 | 「张三最近改了啥」 |
| `--grep=<关键词>` | 按提交信息关键词过滤 | 找「登录」相关提交 |
| `--since=<时间>` | 某时间之后的提交 | `--since="2 weeks ago"`、`--since=2026-09-01` |
| `--until=<时间>` | 某时间之前的提交 | 配合 since 圈范围 |
| `-S "<字符串>"` | 找**新增/删除了某行内容**的提交 | 「这个函数名是哪次加进来的」（pickaxe，神器） |
| `-G "<正则>"` | 类似 `-S`，但按正则匹配 diff | 更复杂的内容搜索 |
| `<分支A>..<分支B>` | 只看 B 有、A 没有的提交 | 看某分支领先多少 |
| `-- <路径>` | 只看改了某文件的提交 | `git log -- app.py` |

### 3. git show 的选项

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `<提交>` | 显示该提交信息 + diff | 看某次提交干了啥 |
| `<标签>` | 显示标签附注 + 指向的提交 | `git show v1.1.0` |
| `--stat` | 只看文件统计不看 diff | 快速了解 |
| `<提交>:<文件>` | 看某次提交时某文件的内容 | `git show HEAD~2:app.py` |
| `-s` | 只显示提交信息，不显示 diff | 看信息不看补丁 |

### 4. git blame 的选项

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `<文件>` | 逐行标注作者 | 查某行是谁写的（最常用） |
| `-L <起>,<止>` | 只标注指定行范围 | `git blame -L 10,30 app.py` |
| `-e`，`--show-email` | 显示邮箱而非名字 | 多人同名时 |
| `-w` | 忽略空白变化 | 改了缩进的行不算新作者 |
| `-C` / `-M` | 追踪跨文件复制/移动的行 | 代码搬家后还能找到原作者 |

## 四、由浅入深的典型示例

### 示例 1：最基本的 log（完整版）

```bash
git log
```

> 不翻页情况下，会列出每次提交的哈希、作者、日期、信息，很长。日常别用裸 `git log`，加 `--oneline`。

### 示例 2：`--oneline` 一行一个提交（最常用）

```bash
git log --oneline
```

```text
d07c6aa merge: 合并 feature/login，解决 app.py 冲突
c21e41a feat: main 上同时改 app.py 到 v2
7434887 feat: 加入默认配置 config.py
0b9a085 chore: 初始化项目，加入 README 与 app.py
```

> 一行一次提交，短哈希 + 标题。配合 `-n` 控制数量。

### 示例 3：`--graph --all --oneline` 画分支图

```bash
git log --oneline --graph --all
```

```text
*   d07c6aa merge: 合并 feature/login，解决 app.py 冲突
|\
| * 963b990 feat: app.py 升级到 v2
| * 9056736 feat: 新增登录模块 auth.py
* | c21e41a feat: main 上同时改 app.py 到 v2
|/
* 7434887 feat: 加入默认配置 config.py
* 0b9a085 chore: 初始化项目，加入 README 与 app.py
```

> `*` 是提交，`| \` 是分支线。一眼能看出：`feature/login` 分支有两个提交（9056736、963b990），后来和 main 合并成 d07c6aa。

### 示例 4：只看最近 2 次

```bash
git log -n 2 --oneline
```

```text
d07c6aa merge: 合并 feature/login，解决 app.py 冲突
c21e41a feat: main 上同时改 app.py 到 v2
```

### 示例 5：按作者过滤

```bash
git log --author="Demo" --oneline
```

```text
d07c6aa merge: 合并 feature/login，解决 app.py 冲突
c21e41a feat: main 上同时改 app.py 到 v2
963b990 feat: app.py 升级到 v2
9056736 feat: 新增登录模块 auth.py
7434887 feat: 加入默认配置 config.py
0b9a085 chore: 初始化项目，加入 README 与 app.py
```

### 示例 6：按提交信息关键词过滤

```bash
git log --grep="登录" --oneline
```

```text
9056736 feat: 新增登录模块 auth.py
```

> 在信息里搜「登录」两个字，命中一次提交。

### 示例 7：`-p` 看每次提交改了什么内容

```bash
git log -n 1 -p
```

> 会显示最近一次提交的完整 diff。配合 `--stat` 先看规模，再 `-p` 细看。

### 示例 8：`git show` 看某次提交详情

```bash
git show v1.1.0 --stat
```

```text
tag v1.1.0
Tagger: Demo User <demo@example.com>
Date:   Wed Sep 30 23:45:31 2026 +0800

发布 v1.1.0：登录模块

commit d07c6aaab59801f3177a82c15c60d3494caf22b2
Merge: c21e41a 963b990
Author: Demo User <demo@example.com>
Date:   Wed Sep 30 23:45:27 2026 +0800

    merge: 合并 feature/login，解决 app.py 冲突

 app.py  | 2 +-
 auth.py | 2 ++
```

> 先显示标签附注「发布 v1.1.0：登录模块」，再显示它指向的提交和改动文件。

### 示例 9：`git blame` 查某行是谁写的

```bash
git blame app.py
```

```text
d07c6aaa (Demo User 2026-09-30 23:45:27 +0800 1) main branch v2 (merged)
```

> 每行格式：`<短哈希> (<作者> <时间> <行号>) <该行内容>`。线上这行出问题，拿着短哈希去 `git show <哈希>` 就能看到当时的完整改动和作者。

### 示例 10：`-S` 找「某行内容是哪次加进来的」

```bash
git log -S "def login" --oneline
```

> 找 diff 里**新增或删除了** `def login` 这行的提交。不知道某个逻辑是哪次引入时，这是最强搜索。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `git log --oneline` | 一行翻历史 |
| `git log --oneline --graph --all` | 画分支图 |
| `git log -n 5 --oneline` | 最近 5 次 |
| `git log --author="名字"` | 按人过滤 |
| `git log --grep="关键词"` | 按信息搜 |
| `git log --since="2 weeks ago"` | 按时间 |
| `git log -p` | 带完整 diff |
| `git show <提交>` | 看某次提交详情 |
| `git show <标签> --stat` | 看标签指向的提交 |
| `git blame <文件>` | 逐行查作者 |
| `git log -S "代码片段"` | 找某行是哪次加的 |

## 六、RHEL 系与 Debian 系差异

`log` / `show` / `blame` 属于 git 本体，**两系用法与输出完全一致**。细微差别：

- 图形化工具：Ubuntu 常配 `gitg`，RHEL 系用 `gitk`（Git 自带 Tcl/Tk 浏览器，两系都有）。
- 日期格式可通过 `git config --global log.date iso` 统一，与发行版无关。

## 七、新手易错点

1. **裸 `git log` 输出太长翻不到底**：加 `--oneline` 和 `-n`。
2. **`--graph` 不加分 `--all` 看不到别的分支**：只看当前分支线。想全看就 `--all`。
3. **`git log <文件>` 和 `git log -- <文件>`**：当文件名可能跟分支名冲突时，加 `--` 明确。
4. **`git blame` 把改缩进的行算成新人写的**：加 `-w` 忽略空白。
5. **`-S` 和 `--grep` 别搞混**：`--grep` 搜提交**信息**；`-S` 搜提交里的**代码内容**。
6. **危险：`git log -p` 输出巨大时别直接管道到 `less` 之外**，它是只读的，不会改任何东西，放心看。
7. **`git show HEAD~2:文件` 才能看历史版本文件**，裸 `git show <提交>` 看的是 diff，不是文件全貌。

## 八、相关命令与文档

- 速查页：[Git 命令速查](../git-commands#查看历史)
- 看错了怎么回去：[reset-revert-restore](./reset-revert-restore)
- 找回归 bug 引入点：`git bisect`（详解见 [advanced](./advanced)）
- 找回误删的提交：`git reflog`（详解见 [advanced](./advanced)）
