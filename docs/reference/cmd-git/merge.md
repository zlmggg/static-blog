# git merge 命令详解：把分支合并回主线，处理合并冲突

> 本文是 [Git 命令速查](../git-commands#合并与变基) 中 `git merge` 的从 0 到 1 详解。
> 目标：搞懂「快进合并」和「三方合并」的区别，会用 `--no-ff`、`--squash`、`--abort`，并能独立处理冲突。
> 环境依据：Git 2.34.1（本机 `/tmp/demo` 实跑；RHEL/Rocky 用法一致）。

## 一、命令是干什么的

`git merge` 把**另一条分支的合并进当前分支**。你在 `feature/login` 上干完活，切回 `main`，`git merge feature/login`，那条分支的提交就进主线了。

两种合并方式：

- **快进合并（fast-forward）**：如果 main 从分叉后没有新提交，Git 只是把 main 指针**直接前移**到 feature 的末尾，不产生新提交。历史是一条直线。
- **三方合并（3-way merge）**：两边都有新提交时，Git 找一个共同祖先，把两边改动合成一个**新的合并提交**。历史上会留下一个分叉再汇合的节点。

合并冲突：如果两边改了**同一文件的同一行**，Git 无法自动决定留谁，会停下来让你手动解决。

> 类比：两个人同时改同一份文档的同一句话，Git 不知道听谁的，就把两种版本都摆出来（`<<<<<<<`），让你拍板留哪个。

## 二、命令语法

```bash
git merge <分支名>               # 把某分支合进当前分支
git merge --no-ff <分支名>       # 强制产生合并提交
git merge --squash <分支名>      # 把分支改动压成一个暂存改动
git merge --abort               # 中止进行中的合并
```

- 先 `git switch main`（切到要合入的目标分支），再 `git merge <来源分支>`；
- 冲突时编辑文件 → `git add` → `git commit` 完成合并。

## 三、选项全表（对照 `git merge -h`）

### 1. 合并方式控制

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `--ff`（默认） | 能快进就快进，不能就三方 | 默认行为 |
| `--no-ff` | **强制产生合并提交** | 保留「这条分支存在过」的痕迹（GitFlow 常用） |
| `--ff-only` | 只能快进，否则直接失败 | 不想产生合并提交时，失败了手动处理 |
| `--squash` | 把来源分支多个提交**压成一个暂存改动**，不自动提交 | 想把分支 N 个提交合成 1 个干净提交 |
| `-m "<信息>"` | 指定合并提交信息 | 非快进合并时 |

### 2. 冲突与中止

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `--abort` | 中止进行中的合并，回到合并前 | 冲突搞不定想撤 |
| `--quit` | 中止但保留 index/工作区 | 少见 |
| `--continue` | 冲突解决后继续 | 解决完手动提交时 |
| `-X ours` | 冲突时**取当前分支**版本 | 明确想以自己为准 |
| `-X theirs` | 冲突时**取来源分支**版本 | 明确想以对方为准 |
| `--no-commit` | 合并成功但不自动提交 | 想先检查再提交 |
| `--allow-unrelated-histories` | 允许合并不相关的历史 | 两个独立仓库合并时 |

### 3. 其他

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `--stat` | 合并结束显示改动统计 | 看规模 |
| `-e`，`--edit` | 编辑合并提交信息 | 想改默认信息 |
| `--no-verify` | 跳过 pre-merge 钩子 | 慎用 |
| `--autostash` | 合并前自动 stash、后自动 pop | 工作区脏时 |

## 四、由浅入深的典型示例

### 示例 1：快进合并（main 没动过）

```bash
git switch main
git merge feature/login
```

> 如果 main 从分叉后没有新提交，输出类似 `Updating 7434887..963b990 Fast-forward`，历史是直线，没有合并节点。

### 示例 2：三方合并 + 冲突（真实演示）

我们在 main 和 feature/login 上**同时改了 app.py 同一行**：

```bash
git switch main
git merge feature/login
```

```text
Auto-merging app.py
CONFLICT (content): Merge conflict in app.py
Automatic merge failed; fix conflicts and then commit the result.
```

看状态：

```bash
git status
```

```text
On branch main
You have unmerged paths.
  (fix conflicts and run "git commit")
  (use "git merge --abort" to abort the merge)

Changes to be committed:
	new file:   auth.py

Unmerged paths:
  (use "git add <file>..." to mark resolution)
	both modified:   app.py
```

打开 `app.py`，冲突长这样：

```text
<<<<<<< HEAD
main branch v2 (from main)
=======
main branch v2
>>>>>>> feature/login
```

- `<<<<<<< HEAD` 到 `=======` 之间是**当前分支（main）**的版本；
- `=======` 到 `>>>>>>> feature/login` 之间是**来源分支**的版本。

手动改成想要的最终内容（比如合并成 `main branch v2 (merged)`），删掉那三行标记，然后：

```bash
git add app.py
git commit
```

```text
[main d07c6aa] merge: 合并 feature/login，解决 app.py 冲突
```

合并完成。看历史：

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
```

> 那个 `|\` 分叉再汇合的节点 `d07c6aa` 就是合并提交。

### 示例 3：`--no-ff` 强制保留分支痕迹

```bash
git merge --no-ff feature/login -m "merge: 合并登录分支"
```

> 即使能快进，也产生一个合并提交。好处是 `git log --graph` 能清楚看到「这条 feature 分支从哪来到哪去」。GitFlow 风格推荐。

### 示例 4：`--squash` 把多个提交压成一个

```bash
git switch main
git merge --squash feature/login
git commit -m "feat: 登录模块（含 auth.py）"
```

> `--squash` 不真的合并，而是把 feature 分支上所有改动**堆到暂存区**，你再自己 `git commit` 成一个干净提交。适合「分支上一堆 WIP 提交不想进主线历史」。

### 示例 5：冲突搞不定，中止合并

```bash
git merge --abort
```

> 回到合并前的状态，工作区和暂存区都还原。想清楚了再重新 merge。

### 示例 6：明确以某一方为准解冲突

```bash
git merge -X ours feature/login    # 冲突全留 main 的版本
git merge -X theirs feature/login  # 冲突全留 feature 的版本
```

> 注意 `-X ours`/`-X theirs` 只解决**冲突部分**，不冲突的改动照常合并。

### 示例 7：合并后删除已合并分支

```bash
git branch -d feature/login
```

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `git merge <分支>` | 合并分支 |
| `git merge --no-ff <分支>` | 强制产生合并提交 |
| `git merge --squash <分支>` | 压成一个改动 |
| `git merge --abort` | 中止合并 |
| `git merge --continue` | 解完冲突继续 |
| `git add <文件> && git commit` | 手动完成冲突合并 |

## 六、RHEL 系与 Debian 系差异

`merge` 属于 git 本体，**两系用法与输出完全一致**。图形化解冲突工具（`git mergetool` 配 `meld`/`kdiff3`）两系都支持，与发行版无关。

## 七、新手易错点

1. **冲突标记 `<<<<<<<` 没删干净就 commit**：文件里残留冲突标记，代码直接坏了。提交前 `git diff --check` 查一下。
2. **合并到一半不知道进行中**：`git status` 会显示 `You have unmerged paths`。要么解决完 commit，要么 `--abort`。
3. **危险：合并冲突时随手 `git merge -X ours` 可能丢掉对方有用代码**。只在你确定「冲突部分都以自己为准」时用。
4. **`--squash` 后不 commit 就切走分支**：改动还堆在暂存区，容易丢。squash 后立刻 commit。
5. **合并完忘记删分支**：长期不删会堆积一堆已合并分支。定期 `git branch --merged` 清理。
6. **在 detached HEAD 或脏工作区里 merge**：先切到正确分支、`git status` 确认干净再合。
7. **危险：对已推送的公共分支用 `--reset` 式撤回合并**见 [rebase](./rebase) 黄金法则——公共历史别改写，要回退用 `git revert`（见 [reset-revert-restore](./reset-revert-restore)）。

## 八、相关命令与文档

- 速查页：[Git 命令速查](../git-commands#合并与变基)
- 另一种整理历史的方式：[rebase](./rebase)
- 安全回退已合并的提交：[reset-revert-restore](./reset-revert-restore)
- 团队合并流程与 PR：[workflow](./workflow)
