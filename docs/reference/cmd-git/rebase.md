# git rebase 命令详解：把提交搬到新基点，交互式整理提交历史

> 本文是 [Git 命令速查](../git-commands#合并与变基) 中 `git rebase` 的从 0 到 1 详解。
> 目标：搞懂变基和合并的区别，会用 `-i HEAD~n` 交互式 pick/squash/reword/drop，记住「黄金法则：不要对已推送的公共历史 rebase」。
> 环境依据：Git 2.34.1（本机 `/tmp/demo` 实跑；RHEL/Rocky 用法一致）。

## 一、命令是干什么的

`git rebase`（变基）的作用是：**把你当前分支上的提交，「摘下来」接到另一个基点后面**，让历史变成一条直线。

和 `git merge` 对比：

- `git merge feature`：保留分叉，产生一个合并提交，历史是 `* 合并提交`；
- `git rebase main`：把你分支上的提交**重新播放**到 main 最新提交后面，历史是直线，没有合并节点。

> 类比：merge 像「把两支队伍后期剪到一起」，保留分叉痕迹；rebase 像「让你的队伍从头站到 main 最新位置，再接着往前走」——历史上看不出曾经分叉过。

**黄金法则：永远不要对已经推送到远程、被别人基于开发的公共分支做 rebase。** 因为 rebase 会**重写提交哈希**，别人本地的历史和你就对不上了。本地还没 push 的提交随便整理。

## 二、命令语法

```bash
git rebase <目标分支>              # 把当前分支变基到目标分支
git rebase -i HEAD~<n>            # 交互式整理最近 n 个提交
git rebase --continue             # 解完冲突继续
git rebase --abort                # 中止，回到变基前
git rebase --onto <新基点> <旧基点> [<分支>]
```

- 先在你的 feature 分支上执行 `git rebase main`，把你的提交搬到 main 最新位置。

## 三、选项全表（对照 `git rebase -h`）

### 1. 基本变基

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `<upstream>` | 把当前分支变基到 upstream | 同步主分支最新代码 |
| `<upstream> <分支>` | 切到某分支再变基 | 不先 switch 的简写 |
| `--onto <新基点>` | 变基到指定提交而非 upstream | 更精细地挑选新基点 |
| `--fork-point` | 用 fork-point 精确定位分叉点 | 跟踪远程分支时自动用 |

### 2. 交互式整理（`-i`）

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-i`，`--interactive` | 打开 todo 列表编辑提交 | 整理提交（最核心） |
| `--autosquash` | 自动把 `fixup!`/`squash!` 提交排好 | 配合 `git commit --fixup` |
| `-x <命令>`，`--exec <命令>` | 每个提交后跑一条命令 | 边 rebase 边跑测试 |
| `--root` | 把从根开始的所有提交都列出来 | 整理整个历史 |

### 3. 冲突与流程控制

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `--continue` | 解决冲突后继续 | 冲突后 git add 再 continue |
| `--skip` | 跳过当前这个提交 | 这个提交没东西可应用了 |
| `--abort` | 中止，回到变基前 | 搞不定想撤 |
| `--quit` | 中止但保留 HEAD 位置 | 少见 |
| `--edit-todo` | 中途再编辑 todo 列表 | 交互中改主意 |
| `--show-current-patch` | 看正在应用的补丁 | 冲突时对照 |
| `--autostash` | 变基前自动 stash、后 pop | 工作区脏时 |

### 4. 其他

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `--keep-empty` | 保留空提交 | 一般用 `--empty=drop/keep` |
| `-r`，`--rebase-merges` | 变基时保留合并提交 | 默认会跳过合并提交 |
| `--committer-date-is-author-date` | 提交日期保持 | 保留原时间 |
| `-f`，`--force-rebase` | 即使 upstream 没变也重放 | 少见 |

## 四、由浅入深的典型示例

### 示例 1：把 feature 分支变基到最新 main（同步主干）

```bash
git switch feature/login
git rebase main
```

> 假设 main 在你分支分叉后又有了新提交。这条命令把你在 feature/login 上的提交**逐个重新应用**到 main 最新提交后面。完成后 `git log --oneline` 是一条直线。如果中途冲突，会停下来让你解决。

### 示例 2：变基时冲突怎么办

```text
Auto-merging app.py
CONFLICT (content): Merge conflict in app.py
error: could not apply 9056736... feat: 新增登录模块 auth.py
Resolve all conflicts manually, mark them as resolved with
"git add <paths>", then run "git rebase --continue".
You can instead skip this commit: run "git rebase --skip".
To abort and get back to the state before "git rebase", run "git rebase --abort".
```

流程：编辑文件删冲突标记 → `git add` → `git rebase --continue`。每个冲突提交都重复一遍。想放弃就 `git rebase --abort`。

### 示例 3：交互式整理最近 3 个提交（核心）

```bash
git rebase -i HEAD~3
```

会打开编辑器，内容大致：

```text
pick 9056736 feat: 新增登录模块 auth.py
pick 963b990 feat: app.py 升级到 v2
pick c21e41a feat: main 上同时改 app.py 到 v2

# Rebase 7434887..c21e41a onto 7434887 (3 commands)
#
# Commands:
# p, pick <commit> = use commit
# r, reword <commit> = use commit, but edit the commit message
# s, squash <commit> = use commit, but meld into previous commit
# f, fixup <commit> = like "squash", but discard this commit's log message
# d, drop <commit> = remove commit
```

把行首的命令改掉、上下调整顺序，保存退出。常用动作：

| 命令 | 作用 |
|---|---|
| `pick`（p） | 原样保留这个提交 |
| `reword`（r） | 保留改动，但改提交信息 |
| `squash`（s） | 把这个提交**合并进上一个**，并让你编辑合并后的信息 |
| `fixup`（f） | 同 squash，但丢弃这个提交自己的信息 |
| `drop`（d） | 删掉这个提交 |
| 上下移动行 | 调整提交顺序 |

比如想把后两个 WIP 提交合成一个、并改第一条信息：

```text
reword 9056736 feat: 新增登录模块 auth.py
squash 963b990 feat: app.py 升级到 v2
squash c21e41a feat: main 上同时改 app.py 到 v2
```

保存后 Git 会依次让你确认/编辑信息，最终这 3 个提交变成 1 个干净提交。

### 示例 4：`--abort` 放弃变基

```bash
git rebase --abort
```

> 回到 `git rebase` 之前的状态，一个提交都没动。

### 示例 5：`--onto` 精确搬到另一个基点

```bash
git rebase --onto v1.0.0 7434887 feature/login
```

> 意思是：把 `feature/login` 上「从 7434887 之后」的提交，搬到 `v1.0.0` 后面。适合「我这条分支其实是从标签 v1.0.0 拉的，但基点记错了」。

### 示例 6：`git pull --rebase` 等价于拉取后变基

```bash
git pull --rebase origin main
```

> 团队约定「拉代码用变基不用合并」时，配 `git config --global pull.rebase true`，以后 `git pull` 自动变基（见 [fetch-pull](./fetch-pull)）。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `git rebase main` | 把当前分支搬到 main 最新 |
| `git rebase -i HEAD~3` | 交互式整理最近 3 个提交 |
| `git rebase --continue` | 解完冲突继续 |
| `git rebase --skip` | 跳过当前提交 |
| `git rebase --abort` | 中止变基 |
| `git pull --rebase` | 拉取后变基 |

## 六、RHEL 系与 Debian 系差异

`rebase` 属于 git 本体，**两系用法与输出完全一致**。交互编辑器默认 `vi`，想换 `nano` 配 `core.editor`，与发行版无关。

## 七、新手易错点（含危险提示）

1. **危险：对已 push 到公共分支的提交做 rebase**。你的提交哈希全变了，再 push 要 `--force`，会把别人基于该分支的工作搞乱。**本地未 push 的提交随便 rebase；已 push 的公共分支别 rebase**。要回退公共提交用 `git revert`（见 [reset-revert-restore](./reset-revert-restore)）。
2. **交互 rebase 中途关掉终端/编辑器**：仓库会卡在「rebase in progress」状态。`git status` 会提示，要么 `--continue` 要么 `--abort`。
3. **`squash` 和 `fixup` 区别**：`squash` 会让你编辑合并后的信息；`fixup` 直接丢弃当前提交信息，只留改动。
4. **变基后 push 报被拒绝**：因为历史重写了。本地 rebase 过、远程是老历史，需要 `git push --force-with-lease`（见 [push](./push)）——前提是这分支确实是你个人的。
5. **别在主分支上 `git rebase -i` 整理公共历史**：除非你明确知道后果并和团队沟通过。
6. **冲突解决后忘了 `git rebase --continue`**：以为卡死了，其实在等你。`git status` 看提示。
7. **`--skip` 乱用会丢提交**：只在当前提交的改动已经被前面应用过时用。

## 八、相关命令与文档

- 速查页：[Git 命令速查](../git-commands#合并与变基)
- 不重写历史的合并：[merge](./merge)
- 安全回退公共提交：[reset-revert-restore](./reset-revert-restore)
- push 时的 force-with-lease：[push](./push)
- 团队该用 merge 还是 rebase：[workflow](./workflow)
