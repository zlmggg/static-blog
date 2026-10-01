# git 进阶命令详解：reflog、cherry-pick、bisect、worktree、clean、fsck

> 本文是 [Git 命令速查](../git-commands#实用技巧) 中 `git reflog`、`git cherry-pick`、`git bisect`、`git worktree`、`git clean`、`git fsck` 的从 0 到 1 详解。本篇一次讲清这六个「急救/高级」工具。
> 目标：出事了能救回来（reflog/fsck）、能挑提交（cherry-pick）、能二分找 bug（bisect）、能同时开多个工作区（worktree）、能清垃圾（clean）。
> 环境依据：Git 2.34.1（本机 `/tmp/demo` 实跑；RHEL/Rocky 用法一致）。

## 一、命令是干什么的

- `git reflog`：记录 **HEAD 每次移动**的历史，是「后悔药之王」——误删分支、reset 过头、detached HEAD 提交丢了，都靠它找回来。
- `git cherry-pick`：把**某一个提交**摘出来，接到当前分支上。别的分支修了个 bug，想单独要这个提交，不要整分支时用。
- `git bisect`：**二分查找**引入 bug 的提交。告诉它哪个提交好、哪个坏，它自动在历史里二分，快速定位是哪次改坏的。
- `git worktree`：一个仓库同时挂**多个工作目录**，不用 clone 多份就能同时 checkout 不同分支。
- `git clean`：删除**未跟踪**文件（`git reset --hard` 管不到的那类）。
- `git fsck`：检查仓库对象完整性，`--lost-found` 能找出「悬空对象」（可能是你以为丢了的提交）。

> 类比：reflog 是行车记录仪，不管怎么误操作都能倒带；cherry-pick 是从别的菜谱里单抄一道菜；bisect 是翻账本二分定位哪笔记错了；worktree 是同一个仓库开多个工作台；clean 是扫地；fsck 是仓库体检。

## 二、命令语法

```bash
git reflog [show]
git cherry-pick <提交> [<提交>...]
git bisect start && git bisect bad <坏> && git bisect good <好> && git bisect reset
git worktree add <路径> [<分支>]
git clean [-nd] / [-fd]
git fsck --lost-found
```

## 三、选项全表（对照各命令 -h）

### 1. git reflog

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `show`（默认） | 显示 HEAD 移动历史 | 找回误删（最常用） |
| `--date=<格式>` | 显示时间 | 知道大概什么时候操作的 |
| `expire` | 清理过期记录 | 维护用 |
| `delete <条目>` | 删某条记录 | 少见 |

### 2. git cherry-pick

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `<提交>` | 摘一个提交接到当前分支 | 单独要某个 bugfix |
| `-n`，`--no-commit` | 只改工作区不自动提交 | 想攒几个一起提交 |
| `--continue`/`--abort`/`--skip` | 冲突后流程控制 | cherry-pick 冲突时 |
| `-x` | 提交信息里注明来源 | 追溯来源 |
| `-m <n>` | 选合并提交的父线 | 摘合并提交时 |

### 3. git bisect

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `start` | 开始二分 | 进入 bisection 状态 |
| `bad <提交>` | 标记已知坏提交 | 当前出 bug 的点 |
| `good <提交>` | 标记已知好提交 | 之前没 bug 的点 |
| `reset` | 结束二分，回到原分支 | 找到后收尾 |
| `run <命令>` | 自动跑命令判定好坏 | 有测试脚本时全自动 |
| `skip` | 跳过无法测试的提交 | 编译不过的提交 |

### 4. git worktree

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `add <路径> [<分支>]` | 新增一个工作目录 | 同时开 hotfix 和 feature |
| `list` | 列出所有工作目录 | 看挂了几个 |
| `remove <路径>` | 移除工作目录 | 用完清理 |
| `lock`/`unlock` | 锁定防 prune | 少见 |
| `prune` | 清理失效的工作目录记录 | 维护 |

### 5. git clean

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-n`，`--dry-run` | 试运行，只列出要删的 | **先跑它** |
| `-f`，`--force` | 真正删除 | 确认后 |
| `-d` | 连未跟踪目录一起删 | 有未跟踪目录时 |
| `-x` | 连被忽略的文件也删 | 清得更狠 |
| `-i` | 交互式挑选删除 | 谨慎模式 |

### 6. git fsck

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `--lost-found` | 把悬空对象写到 `.git/lost-found` | 找回以为丢的提交 |
| `--unreachable` | 显示不可达对象 | 排查 |
| `--dangling` | 只显示悬空对象 | 看有没有孤儿 |

## 四、由浅入深的典型示例

### 示例 1：reflog 找回误删的提交

```bash
git reflog | head -12
```

```text
d07c6aa HEAD@{0}: reset: moving to HEAD
d07c6aa HEAD@{1}: commit (merge): merge: 合并 feature/login，解决 app.py 冲突
c21e41a HEAD@{2}: commit: feat: main 上同时改 app.py 到 v2
7434887 HEAD@{3}: checkout: moving from feature/login to main
963b990 HEAD@{4}: commit: feat: app.py 升级到 v2
9056736 HEAD@{5}: commit: feat: 新增登录模块 auth.py
7434887 HEAD@{6}: checkout: moving from main to feature/login
0b9a085 HEAD@{8}: commit (initial): chore: 初始化项目
```

> 每一行是一次 HEAD 移动，`HEAD@{n}` 是它的引用。误删了某个分支、reset 过头了，在这找你要的哈希，然后 `git switch -c 找回的分支 <哈希>` 或 `git reset --hard <哈希>`。

### 示例 2：cherry-pick 摘一个 bugfix 提交

```bash
git cherry-pick 9056736
```

> 把 `9056736`（登录模块那个提交）的改动接到当前分支。冲突就解完 `git cherry-pick --continue`。

### 示例 3：bisect 二分找 bug

```bash
git bisect start
git bisect bad                  # 当前 HEAD 是坏的
git bisect good 7434887         # 这个提交是好的
```

> Git 会自动 checkout 中间提交让你测，你回报 `git bisect good` 或 `git bisect bad`，它继续二分。定位到后：

```bash
git bisect reset
```

> 回到原分支，历史记录里会告诉你「第一个坏提交是 xxx」。有测试脚本就 `git bisect run ./run_test.sh` 全自动。

### 示例 4：worktree 同时开两个工作区

```bash
git worktree add /tmp/wt-hotfix -b hotfix
git worktree list
```

```text
/tmp/demo       d07c6aa [main]
/tmp/wt-hotfix  d07c6aa [hotfix]
```

> 不用 clone 第二份，`/tmp/wt-hotfix` 就是一个独立工作目录，切到 hotfix 分支。主目录继续干 main，两边互不干扰，共用同一个 `.git`。用完：

```bash
git worktree remove /tmp/wt-hotfix
```

### 示例 5：clean 清未跟踪文件（先 dry-run）

```bash
mkdir -p junkdir && echo temp > junkdir/a.txt && echo temp > loose.txt
git clean -nd
```

```text
Would remove junkdir/
Would remove loose.txt
```

> `-n` 是 dry-run，只列出不真删。确认无误再加 `-f`：

```bash
git clean -fd
```

```text
Removing junkdir/
Removing loose.txt
```

### 示例 6：fsck 找悬空对象

```bash
git fsck --lost-found
```

```text
dangling tree 09483710...
dangling commit 9436d9b3c8d378780a41e02455e73dfe49b4611f
dangling blob 6c91108...
```

> `dangling commit` 就是「没有任何分支指向、但对象还在」的提交——可能是你 stash 过又丢的、或 rebase 扔掉的。用 `git show 9436d9b3` 看它是不是你要找的，是就 `git branch 找回 9436d9b3`。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `git reflog` | 找误删/倒带 |
| `git reflog | grep 关键词` | 在记录里搜 |
| `git cherry-pick <提交>` | 摘单个提交 |
| `git bisect start/bad/good/reset` | 二分找 bug |
| `git worktree add 路径 -b 分支` | 开多工作区 |
| `git worktree list` | 列工作区 |
| `git clean -nd` | 预览删未跟踪文件 |
| `git clean -fd` | 真删 |
| `git fsck --lost-found` | 找悬空提交 |

## 六、RHEL 系与 Debian 系差异

这些命令都属于 git 本体，**两系用法与输出完全一致**。bisect 自动跑的脚本、worktree 路径都与发行版无关。

## 七、新手易错点（含危险提示）

1. **危险：`git clean -fd` 删除的未跟踪文件无法通过 git 找回**（它们从没被 git 跟踪过）。**永远先 `git clean -nd` 预览**，确认再 `-fd`。加 `-x` 连忽略文件也删，更要小心。
2. **reflog 不是永久的**：默认保留 90 天，过期后对象会被 GC。重要的东西别指望 reflog 救，及时 commit/push。
3. **bisect 忘了 `git bisect reset`**：仓库一直停在二分状态，切不出。跑完一定 reset。
4. **cherry-pick 多个提交顺序反了**：按从旧到新的顺序给哈希，否则冲突。
5. **worktree 里删了分支，主目录的分支记录还在**：用 `git worktree remove` 正规移除，别直接 `rm -rf` 目录。
6. **`git fsck --lost-found` 找到的悬空提交别随便删**：先 `git show` 看内容，可能正是你以为丢了的工作。
7. **危险：reset --hard + clean -fd 组合是「彻底回到某提交」的核弹**，未提交改动全没。敲之前确认。

## 八、相关命令与文档

- 速查页：[Git 命令速查](../git-commands#实用技巧)
- 回退与恢复：[reset-revert-restore](./reset-revert-restore)
- 变基与历史整理：[rebase](./rebase)
- 临时存改动：[stash](./stash)
- CI 里自动 bisect/测试：[devops-cicd-advanced](../../guide/devops-cicd-advanced)
