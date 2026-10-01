# git stash 命令详解：把手里没干完的活临时收起来

> 本文是 [Git 命令速查](../git-commands#暂存（stash）) 中 `git stash` 的从 0 到 1 详解。
> 目标：搞懂 `stash push`、`list`、`pop`、`apply`、`drop`、`show -p`、`branch`，以及 `-u` 连未跟踪文件一起收。
> 环境依据：Git 2.34.1（本机 `/tmp/demo` 实跑；RHEL/Rocky 用法一致）。

## 一、命令是干什么的

`git stash` 把你**当前没提交的改动临时「收起来」**，让工作区变干净，方便你切分支、拉代码、救火。等忙完了再把改动「取回来」继续干。

典型场景：你在 feature 分支改到一半，突然 master 上有线上 bug 要紧急修。你不想把半成品 commit，也不想丢掉——`git stash` 一下，切去修 bug，回来 `git stash pop` 接着写。

> 类比：stash 像「把桌上摊开的半成品图纸塞进一个标注了日期的抽屉」。桌面清空了（工作区干净），等需要时拉开抽屉照原样摆回去。

## 二、命令语法

```bash
git stash push [-m "说明"] [-u]     # 收起改动
git stash list                      # 看抽屉里有哪些
git stash pop [stash@{n}]          # 取出并删除这条
git stash apply [stash@{n}]        # 取出但保留这条
git stash drop [stash@{n}]         # 删除这条
git stash show -p stash@{n}        # 看这条存了什么改动
git stash branch <分支名>           # 基于这条 stash 开新分支
```

- 不带任何参数的 `git stash` 等价于 `git stash push`；
- `stash@{0}` 是最近一次，`stash@{1}` 是上上次。

## 三、选项全表（对照 `git stash -h`）

### 1. 收起（push）

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `push` | 收起工作区/暂存区改动 | 最常用 |
| `-m "<说明>"`，`--message` | 给这条 stash 写备注 | 多了好区分（强烈建议） |
| `-u`，`--include-untracked` | 连**未跟踪**的新文件一起收 | 新文件也想藏起来 |
| `-a`，`--all` | 连被 `.gitignore` 忽略的文件也收 | 少见 |
| `-p`，`--patch` | 交互式挑改动收哪些 | 只收部分改动 |
| `-k`，`--keep-index` | 收起来但保留暂存区 | 少见 |
| `save` | 旧版收起命令（已被 push 取代） | 老教程里会见到 |

### 2. 查看与取用

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `list` | 列出所有 stash | 看抽屉里有啥 |
| `show [-p] [stash@{n}]` | 看某条存了什么改动 | `-p` 看具体 diff |
| `pop [stash@{n}]` | 取出**并删除**该条 | 最常用，干完活收尾 |
| `apply [stash@{n}]` | 取出但**保留**该条 | 想在多个分支重复用同一份改动 |
| `branch <名> [stash@{n}]` | 基于这条 stash 开新分支 | stash 改动和当前分支冲突时的救命招 |
| `drop [stash@{n}]` | 删除某条 | 确认不要了 |
| `clear` | 清空所有 stash | 慎用 |

## 四、由浅入深的典型示例

### 示例 1：最基本的收起与取回

改了一半：

```bash
printf 'wip: 正在改 auth\n' >> auth.py
printf 'untracked file\n' > todo.txt
git stash push -u -m "WIP: 登录页改动"
```

```text
Saved working directory and index state On main: WIP: 登录页改动
```

工作区立刻干净。现在可以安心切分支修 bug。

### 示例 2：列出 stash

```bash
git stash list
```

```text
stash@{0}: On main: WIP: 登录页改动
```

> `stash@{0}` 是最新一条。多了之后按时间倒序排列。

### 示例 3：看某条 stash 存了什么

```bash
git stash show -p stash@{0}
```

```text
diff --git a/auth.py b/auth.py
index bb1271b..6d00b89 100644
--- a/auth.py
+++ b/auth.py
@@ -1,2 +1,3 @@
 def login():
     return "ok"
+wip: 正在改 auth
```

> `-p` 显示这条 stash 相对当时多了哪些改动。`-u` 收进来的未跟踪文件不会在 diff 里显示，但 pop 时会还原。

### 示例 4：pop——取出并删除

```bash
git stash pop
```

```text
On branch main
Your branch is up to date with 'origin/main'.

Changes not staged for commit:
	modified:   auth.py

Untracked files:
	todo.txt

Dropped refs/stash@{0} (9436d9b...)
```

> 改动回来了，`todo.txt`（-u 收进来的未跟踪文件）也回来了，最后一行 `Dropped` 表示这条 stash 已删除。

### 示例 5：apply——取出但保留

```bash
git stash apply
```

> 改动回到工作区，但 stash list 里那条还在。适合「同一份改动想在 feature 和 hotfix 两个分支都应用一遍」。用完手动 `git stash drop`。

### 示例 6：stash pop 冲突怎么办——用 stash branch

如果你在另一分支 pop 时和现有代码冲突，最干净的做法：

```bash
git stash branch feature/recover-login
```

> 它会基于 stash 当时的提交开一个新分支，把改动应用上去。这样不会和当前分支的新代码打架，是 stash 冲突时的标准解法。

### 示例 7：删除某条 stash

```bash
git stash drop stash@{0}
```

> 确认不要了才删。`git stash clear` 会清空所有，慎用。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `git stash push -m "说明"` | 收起改动 |
| `git stash -u -m "说明"` | 连新文件一起收 |
| `git stash list` | 查看 |
| `git stash pop` | 取出并删除 |
| `git stash apply` | 取出保留 |
| `git stash show -p stash@{0}` | 看存了啥 |
| `git stash branch 分支名` | 基于 stash 开分支 |
| `git stash drop stash@{0}` | 删除某条 |

## 六、RHEL 系与 Debian 系差异

`stash` 属于 git 本体，**两系用法与输出完全一致**。`git stash push` 是较新写法，老版本用 `git stash save`，两者都认识。

## 七、新手易错点

1. **`git stash` 默认不收未跟踪的新文件**：你新建的 `todo.txt` 默认不在 stash 里，pop 后还在原地。想一起收加 `-u`。
2. **stash 太多分不清**：每条都 `-m "说明"`，别用默认信息。`git stash list` 看备注。
3. **pop 时冲突**：改动和当前分支新代码撞了。解完冲突手动 `git stash drop`；搞不定就 `git stash branch` 开新分支。
4. **危险：`git stash clear` 清空所有 stash**，里面未提交的改动会丢。删之前 `git stash list` 确认。
5. **stash 不是备份**：它存在 `.git/refs/stash`，仓库删了就没了。重要改动还是要 commit 或 push。
6. **频繁 stash 却不 pop**：抽屉塞满了，自己都忘了里面是啥。收起来就尽快处理掉。
7. **pull 前忘 stash 导致工作区脏报错**：`git pull --autostash`（见 [fetch-pull](./fetch-pull)）能自动收放。

## 八、相关命令与文档

- 速查页：[Git 命令速查](../git-commands#暂存（stash）)
- 工作区脏想切分支：[checkout-switch](./checkout-switch)
- 丢弃而非暂存改动：[reset-revert-restore](./reset-revert-restore)
- 找回误删的 stash/reflog：[advanced](./advanced)
