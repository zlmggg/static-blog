# git reset、git revert、git restore 命令详解：撤销改动的三把「后悔药」

> 本文是 [Git 命令速查](../git-commands#撤销与回退) 中 `git reset`、`git revert`、`git restore` 的从 0 到 1 详解。本篇一次讲清「本地后悔」和「公共历史安全回退」分别用哪个。
> 目标：搞懂 `reset --soft/--mixed/--hard` 的区别，知道公共历史回退必须用 `revert`，以及 `restore` 怎么替代危险的 `checkout --`。
> 环境依据：Git 2.34.1（本机 `/tmp/resetdemo` 实跑；RHEL/Rocky 用法一致）。

## 一、命令是干什么的

这三个都是「反悔」命令，但作用范围不同：

- `git reset`：移动 **HEAD 指针**，把分支回退到某个提交。`--soft` 只动 HEAD、`--mixed` 连暂存区一起动、`--hard` 连工作区一起动。**改写历史，只用于本地未推送的提交**。
- `git revert`：**新增一个反向提交**来抵消某次提交的效果，不动历史。**已推送的公共回退用它**。
- `git restore`：把工作区 / 暂存区的文件**恢复成某个版本**，不改变提交历史。是 `git checkout -- 文件` 的安全替代。

> 类比：reset 像「把账本翻回前一页，后面那几页撕掉」（本地专用）；revert 像「在账本后面补一页『上一页作废』」（历史保留，别人也能看到）；restore 像「把写错的那行擦回上次复印的样子」。

## 二、命令语法

```bash
git reset [--soft|--mixed|--hard] [<提交>]     # 移动 HEAD
git reset [--] <文件>                          # 只把某文件撤出暂存区
git revert [<提交>]                            # 新增反向提交
git restore [--staged] [--source=<提交>] <文件> # 恢复工作区/暂存区文件
```

## 三、选项全表（对照 `git reset -h`、`git revert -h`、`git restore -h`）

### 1. git reset 三种模式（核心）

| 模式 | HEAD | 暂存区(index) | 工作区 | 用途 |
|---|---|---|---|---|
| `--soft` | 回退 | 不动 | 不动 | 把最近几个提交「拆开」重新组合提交 |
| `--mixed`（默认） | 回退 | 回退 | 不动 | 把提交撤回成「未暂存的改动」 |
| `--hard` | 回退 | 回退 | 回退 | **彻底丢弃**提交和工作区改动 |

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `--soft` | 只动 HEAD | 想把最近 2 个提交合成 1 个 |
| `--mixed` | HEAD + 暂存区 | 默认；改主意不想提交了 |
| `--hard` | HEAD + 暂存区 + 工作区 | 丢弃一切，回到某提交（危险） |
| `--keep` | 回退 HEAD 但保留本地改动 | 有未提交改动想保留时 |
| `<提交> -- <文件>` | 把某文件在暂存区恢复成 HEAD 版本 | `git reset -- f.txt`（撤销 add） |
| `-p`，`--patch` | 交互式挑 hunk | 精细撤回 |

### 2. git revert 选项

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `<提交>` | 新增一个反向提交抵消该提交 | 公共历史回退（安全） |
| `-n`，`--no-commit` | 反向改动先放暂存区，不自动提交 | 想一次 revert 多个再统一提交 |
| `--continue` / `--abort` | 冲突后继续/中止 | revert 冲突时 |
| `-m <n>` | 指定合并提交的父线 | revert 合并提交时 |

### 3. git restore 选项

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `<文件>` | 用暂存区/HEAD 版本恢复工作区 | 丢弃工作区改动（替代 `checkout --`） |
| `--staged`（`-S`） | 恢复**暂存区**（把文件撤出暂存） | `git restore --staged f.txt`（撤销 add） |
| `--source=<提交>`（`-s`） | 从指定版本恢复 | 把文件恢复成历史某版本 |
| `--worktree`（`-W`，默认） | 恢复工作区 | 默认 |
| `-p`，`--patch` | 交互式挑 hunk | 精细恢复 |

## 四、由浅入深的典型示例

先建三个提交 c1/c2/c3：

```text
a2ca725 c3: 改 f.txt
ea836e2 c2: 改 f.txt
0e52f96 c1: 加 f.txt
```

### 示例 1：reset --soft——把最近提交拆回暂存区

```bash
git reset --soft HEAD~1
git log --oneline -1
git status -s
cat f.txt
```

```text
ea836e2 c2: 改 f.txt
M  f.txt
v1
v2
v3
```

> HEAD 退到 c2，但：暂存区还留着 c3 的改动（`M  f.txt`），工作区文件内容没变（还是 v1/v2/v3）。适合「我刚才那个提交拆错了，撤回暂存区重新组织」。

### 示例 2：reset --mixed（默认）——撤回成未暂存改动

```bash
git reset --mixed HEAD~1
git status -s
cat f.txt
```

```text
Unstaged changes after reset:
M	f.txt
 M f.txt
v1
v2
v3
```

> HEAD 退到 c2，暂存区也退回 c2，但工作区文件还是 v1/v2/v3（` M f.txt` 表示改了没暂存）。适合「这个提交我不想了，改动留着重新 add」。

### 示例 3：reset --hard——彻底丢弃（危险）

```bash
git reset --hard HEAD~1
git log --oneline -1
cat f.txt
```

```text
HEAD is now at ea836e2 c2: 改 f.txt
ea836e2 c2: 改 f.txt
v1
v2
```

> HEAD、暂存区、工作区全部退到 c2。c3 的提交和工作区里的 `v3` **全部丢失**。这是最危险的命令之一。

### 示例 4：reset -- 文件——撤销 add（保留工作区）

```bash
git add f.txt
git reset -- f.txt
git status -s
```

> `git reset -- f.txt` 把 `f.txt` 从暂存区撤出（变成 ` M`），但工作区改动还在。等价于新版的 `git restore --staged f.txt`。

### 示例 5：revert——安全回退公共提交

```bash
git revert --no-edit HEAD
git log --oneline -3
cat f.txt
```

```text
[main 76e7c88] Revert "c3: 改 f.txt"
 1 file changed, 1 deletion(-)

76e7c88 Revert "c3: 改 f.txt"
a2ca725 c3: 改 f.txt
ea836e2 c2: 改 f.txt
v1
v2
```

> 它**没有删 c3**，而是新增了一个提交 `Revert "c3"`，效果上把 c3 的改动抵消了。历史是连续的，push 出去别人也能看懂。**已推送的提交要回退，一律用 revert，不要用 reset**。

### 示例 6：revert -n——一次回退多个

```bash
git revert -n HEAD~2..HEAD
```

> 把最近两个提交的反向改动都放进暂存区，不自动提交。你检查后自己 `git commit`。

### 示例 7：restore——丢弃工作区改动

```bash
printf 'junk\n' >> f.txt
git status -s
git restore f.txt
git status -s
```

```text
 M f.txt
(干净了)
```

> `git restore f.txt` 用暂存区版本覆盖工作区，刚才追加的 `junk` 没了。这是 `git checkout -- f.txt` 的新写法，更安全（不会和切分支混淆）。

### 示例 8：restore --staged——撤销 add

```bash
printf 'x\n' >> f.txt
git add f.txt
git status -s
git restore --staged f.txt
git status -s
```

```text
M  f.txt
 M f.txt
```

> `M `（已暂存）变成 ` M`（改了没暂存）。文件内容不变，只是撤出暂存区。

### 示例 9：restore --source——把文件恢复成历史版本

```bash
git restore --source=HEAD~2 f.txt
```

> 把 `f.txt` 恢复成 c1 时的样子（并放进工作区）。注意这只改文件，要 commit 才生效。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `git reset --soft HEAD~1` | 撤回最近提交到暂存区 |
| `git reset --mixed HEAD~1` | 撤回提交到工作区（默认） |
| `git reset --hard HEAD~1` | 彻底丢弃（危险） |
| `git reset -- f.txt` | 撤销某文件的 add |
| `git revert <提交>` | 公共历史安全回退 |
| `git restore f.txt` | 丢弃工作区改动 |
| `git restore --staged f.txt` | 撤销 add |
| `git restore --source=HEAD~2 f.txt` | 文件恢复到历史版本 |

## 六、RHEL 系与 Debian 系差异

三个命令属于 git 本体，**两系用法与输出完全一致**。`git restore` / `git switch` 是 Git 2.23 新增，老系统（<2.23，如 Ubuntu 18.04）没有，只能用 `git reset` / `git checkout --`。本机 2.34.1 已支持。

## 七、新手易错点（含危险提示）

1. **危险：`git reset --hard` 丢失的工作区改动无法找回**（除非还在 reflog 里）。敲之前确认改动真的不要了，或者先 `git stash`。
2. **公共分支上用 reset 回退**：会改写历史，push 要强推，把同事历史搞乱。**已推送的提交要回退，用 `git revert`，不要用 reset**。
3. **`reset --soft` 和 `--mixed` 别记反**：`--soft` 暂存区不动（改动留在暂存区）；`--mixed` 暂存区也退回（改动留在工作区）。
4. **`git restore f.txt` 和 `git restore --staged f.txt` 区别**：前者恢复工作区（丢弃改动）；后者恢复暂存区（撤销 add，工作区改动保留）。
5. **revert 产生冲突**：和 merge 一样解冲突，`git add` 后 `git revert --continue`，或 `--abort`。
6. **`reset --hard` 到错的提交**：还好有 reflog（见 [advanced](./advanced)），`git reflog` 能找回来，但别依赖这个。
7. **危险：`git clean -fd` 配合 reset --hard** 会连未跟踪文件一起删，见 [advanced](./advanced)。

## 八、相关命令与文档

- 速查页：[Git 命令速查](../git-commands#撤销与回退)
- 找回误删提交：`git reflog`（详解见 [advanced](./advanced)）
- 整理本地提交历史：[rebase](./rebase)
- 丢弃工作区改动的老写法对照：[checkout-switch](./checkout-switch)
