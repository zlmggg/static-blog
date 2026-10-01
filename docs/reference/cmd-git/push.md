# git push 命令详解：把本地提交上传到远程，重点是 --force-with-lease

> 本文是 [Git 命令速查](../git-commands#远程协作) 中 `git push` 的从 0 到 1 详解。
> 目标：搞懂 `-u` 首次推送、普通 push、`--force-with-lease`、`--delete`、`--tags`，并理解为什么 `--force` 危险。
> 环境依据：Git 2.34.1（本机 `/tmp/demo` 实跑；RHEL/Rocky 用法一致）。

## 一、命令是干什么的

`git push` 把你本地的提交**上传**到远程仓库（GitHub/GitLab）。本地 commit 只存在你电脑上，不 push 别人看不到；push 之后远程才有，才能开 PR/MR。

常见场景：

- 第一次推新分支：`git push -u origin 分支名`；
- 日常推送：`git push`（配好上游后）；
- 删远程分支：`git push origin --delete 分支名`；
- 推标签：`git push origin --tags`。

> 类比：commit 是你在本地写好稿子，push 是把稿子投稿到报社（远程）。不投稿，没人能看；投错了想改，就得和编辑打招呼（force-with-lease）。

## 二、命令语法

```bash
git push [-u] origin <分支名>     # 推送分支，-u 设置上游
git push origin <分支名>           # 普通推送
git push origin --delete <分支名>  # 删除远程分支
git push origin --tags            # 推送所有标签
git push --force-with-lease       # 安全强制推送
```

- `-u`（`--set-upstream`）：首次推新分支时用，之后 `git pull`/`git push` 不用再指定远程和分支。

## 三、选项全表（对照 `git push -h`）

### 1. 基本推送

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `origin <分支>` | 推送指定分支 | 日常 |
| `-u`，`--set-upstream` | 推送并设置上游跟踪 | 首次推新分支（必用） |
| `--all` | 推送所有本地分支 | 少见 |
| `--tags` | 推送所有标签 | 发版时 |
| `--follow-tags` | 只推送当前提交关联的标签 | 更精准 |

### 2. 删除与强制

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-d`，`--delete` | 删除远程引用（分支/标签） | `git push origin --delete dev` |
| `-f`，`--force` | **强制推送**（覆盖远程历史） | 危险，别用 |
| `--force-with-lease[=<ref>]` | **安全强制**：只在远程没被别人更新时才覆盖 | rebase 后推送用它（推荐） |
| `--prune` | 删掉本地没有的远程分支 | 少见 |

### 3. 其他

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-n`，`--dry-run` | 试运行，不真推 | 先看会推啥 |
| `--no-verify` | 跳过 pre-push 钩子 | 慎用 |
| `--atomic` | 要么全成功要么全失败 | 一次推多个引用时 |
| `-o <选项>` | 传服务器端选项 | PR 平台参数 |

## 四、由浅入深的典型示例

### 示例 1：首次推送新分支（带 -u）

```bash
git push -u origin feature/login
```

```text
Enumerating objects: 4, done.
Counting objects: 100% (4/4), done.
To /tmp/demo.git
 * [new branch]      feature/login -> feature/login
Branch 'feature/login' set up to track remote branch 'feature/login' from 'origin'.
```

> `* [new branch]` 表示远程新建了这个分支；最后一句说明本地 `feature/login` 已跟踪远程同名分支。之后裸 `git push` 就行。

### 示例 2：日常推送（已配上游）

```bash
git push
```

> 直接把当前分支的新提交推上去。没配上游会报错，提示你用 `-u`。

### 示例 3：删除远程分支

```bash
git push origin --delete feature/login
```

```text
To /tmp/demo.git
 - [deleted]         feature/login
```

> PR 合并完，远程分支可以删了。删的是远程，本地分支用 `git branch -d` 另删。

### 示例 4：推送标签

```bash
git push origin v1.0.0      # 推单个标签
git push origin --tags       # 推所有本地标签
```

> commit 不会自动带标签，要单独推。发版时打完 tag 记得 push。

### 示例 5：rebase 后用 --force-with-lease 推送（核心安全操作）

你在本地 `git rebase -i` 整理了提交，哈希变了，直接 `git push` 被拒绝：

```text
 ! [rejected]        feature/login -> feature/login (non-fast-forward)
error: failed to push some refs to '/tmp/demo.git'
```

因为远程还是老历史，你重写了本地历史，Git 怕覆盖别人的提交。这时用：

```bash
git push --force-with-lease
```

> 它的含义是：「只有当远程 `feature/login` 还是我上次 fetch 看到的那个状态时，才允许我覆盖。」如果这期间别人往这个分支推了新提交，`--force-with-lease` 会**拒绝**推送，避免覆盖同事的工作。比 `--force` 安全得多。

### 示例 6：先 dry-run 看会推啥

```bash
git push --dry-run origin main
```

> 不真推，只显示会传哪些对象、更新哪些引用。

### 示例 7：推送时顺便推关联标签

```bash
git push --follow-tags origin main
```

> 比 `--tags` 精准：只推当前提交链上打过的标签，不推无关标签。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `git push -u origin 分支` | 首次推新分支 |
| `git push` | 日常推送 |
| `git push origin --delete 分支` | 删远程分支 |
| `git push origin --tags` | 推所有标签 |
| `git push --force-with-lease` | 安全强制推送 |
| `git push --dry-run` | 预览 |

## 六、RHEL 系与 Debian 系差异

`push` 属于 git 本体，**两系用法与输出完全一致**。认证方式两系通用：

- HTTPS：用凭据助手或 token；
- SSH：用 `~/.ssh/id_ed25519`，与发行版无关。

## 七、新手易错点（含危险提示）

1. **危险：`git push --force` 会直接覆盖远程历史**，不管别人有没有往里推。同事辛苦推的提交可能被你一秒抹掉。**永远优先用 `--force-with-lease`**，它在远程被别人动过时报错而不是覆盖。
2. **rebase/`commit --amend` 后普通 push 被拒**：这是正常的，因为历史重写了。用 `--force-with-lease`，而且只在你**个人分支**上这么做。
3. **首次 push 忘了 `-u`**：之后 `git pull` 报「no tracking information」。补救：`git branch -u origin/分支`。
4. **打了 tag 忘了 push**：远程没有这个版本。发版后 `git push origin --tags`。
5. **危险：对公共分支（main/develop）做 force push**：会把整个团队的历史搞乱。公共分支别强推，要改回去用 `git revert`（见 [reset-revert-restore](./reset-revert-restore)）。
6. **`git push origin --delete` 删错分支**：删远程分支是即时生效的，确认名字再敲。删了还能从 reflog 恢复，但麻烦。
7. **push 报认证失败**：HTTPS 用 token 不是密码；SSH 检查 key 是否加到平台。

## 八、相关命令与文档

- 速查页：[Git 命令速查](../git-commands#远程协作)
- 拉远程代码：[fetch-pull](./fetch-pull)
- 远程地址：[remote](./remote)
- 为什么 rebase 后要强推：[rebase](./rebase)
- 标签管理：[tag](./tag)
- PR/分支保护流程：[workflow](./workflow)
