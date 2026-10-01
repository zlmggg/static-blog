# Git 命令与协作工作流速查

> Git 常用命令与团队协作流程速查表。日常开发、排障、Code Review 时随手翻。
> 用法：右侧「本页目录」跳转，或 `Ctrl+K` 搜索；表格左列命令可直接复制。
> 提示：可设别名 `alias g=git`，全局忽略文件 `~/.gitignore_global`。

## 初始配置

| 命令 | 说明 |
|---|---|
| [`git config --global user.name "你的名字"`](./cmd-git/config) | 设置提交用户名 |
| [`git config --global user.email "you@example.com"`](./cmd-git/config) | 设置提交邮箱 |
| [`git config --global init.defaultBranch main`](./cmd-git/config) | 新建仓库默认分支为 main |
| [`git config --global core.editor vim`](./cmd-git/config) | 设置默认编辑器 |
| [`git config --global pull.rebase false`](./cmd-git/config) | pull 默认 merge（或设 true 用 rebase） |
| [`git config --global alias.st status`](./cmd-git/config) | 命令别名（示例 st = status） |
| [`git config --list`](./cmd-git/config) | 查看所有配置 |
| [`git config --global --edit`](./cmd-git/config) | 直接编辑全局配置文件 |

## 创建与克隆仓库

| 命令 | 说明 |
|---|---|
| [`git init`](./cmd-git/init-clone) | 在当前目录初始化仓库 |
| [`git init 项目目录`](./cmd-git/init-clone) | 新建并初始化指定目录 |
| [`git clone <url>`](./cmd-git/init-clone) | 克隆远程仓库 |
| [`git clone <url> 目录名`](./cmd-git/init-clone) | 克隆到指定目录 |
| [`git clone -b 分支 <url>`](./cmd-git/init-clone) | 克隆指定分支 |
| [`git clone --depth=1 <url>`](./cmd-git/init-clone) | 浅克隆（只取最新一次提交，加速） |

## 日常四件套

| 命令 | 说明 |
|---|---|
| [`git status`](./cmd-git/add) | 查看工作区/暂存区状态 |
| [`git add 文件`](./cmd-git/add) | 把改动加入暂存区 |
| [`git add .`](./cmd-git/add) | 暂存当前目录所有改动 |
| [`git add -p`](./cmd-git/add) | 交互式逐块暂存（hunk） |
| [`git commit -m "说明"`](./cmd-git/commit) | 提交暂存区改动 |
| [`git commit -am "说明"`](./cmd-git/commit) | 对已跟踪文件跳过 add 直接提交 |
| [`git diff`](./cmd-git/diff) | 查看工作区未暂存的改动 |
| [`git diff --cached`](./cmd-git/diff) | 查看已暂存、待提交的改动 |
| [`git diff 分支A 分支B`](./cmd-git/diff) | 比较两个分支差异 |

## 查看历史

| 命令 | 说明 |
|---|---|
| [`git log`](./cmd-git/log-show) | 查看提交历史 |
| [`git log --oneline`](./cmd-git/log-show) | 每行一条，精简模式 |
| [`git log --oneline --graph --all`](./cmd-git/log-show) | 图形化查看分支合并拓扑 |
| [`git log -n 10`](./cmd-git/log-show) | 只看最近 10 条 |
| [`git log -p 文件`](./cmd-git/log-show) | 查看某文件的逐次改动 |
| [`git log --author="名字"`](./cmd-git/log-show) | 按作者过滤 |
| [`git log --since="2 weeks ago"`](./cmd-git/log-show) | 按时间过滤 |
| [`git reflog`](./cmd-git/advanced) | 查看本地 HEAD 移动记录（找回误删提交的救命命令） |
| [`git show <commit>`](./cmd-git/log-show) | 查看某次提交的具体改动 |
| [`git blame 文件`](./cmd-git/log-show) | 逐行查看每行最后由谁、哪次提交修改 |

## 分支管理

| 命令 | 说明 |
|---|---|
| [`git branch`](./cmd-git/branch) | 列出本地分支 |
| [`git branch -a`](./cmd-git/branch) | 列出本地+远程所有分支 |
| [`git branch 名`](./cmd-git/branch) | 新建分支（不切换） |
| [`git switch -c 名`](./cmd-git/checkout-switch) | 新建并切换到该分支（推荐用法） |
| [`git switch 名`](./cmd-git/checkout-switch) | 切换分支（推荐） |
| [`git switch -`](./cmd-git/checkout-switch) | 切回上一个分支 |
| [`git checkout 名`](./cmd-git/checkout-switch) | 旧版切换写法（等价 switch） |
| [`git branch -m 旧名 新名`](./cmd-git/branch) | 重命名分支 |
| [`git branch -d 名`](./cmd-git/branch) | 删除已合并的分支 |
| [`git branch -D 名`](./cmd-git/branch) | 强制删除未合并分支 |

## 合并与变基

| 命令 | 说明 |
|---|---|
| [`git merge 分支`](./cmd-git/merge) | 把指定分支合并进当前分支 |
| [`git merge --no-ff 分支`](./cmd-git/merge) | 强制生成合并提交（保留分支痕迹） |
| [`git rebase 分支`](./cmd-git/rebase) | 把当前分支的提交变基到目标分支顶端 |
| [`git rebase -i HEAD~3`](./cmd-git/rebase) | 交互式整理最近 3 条提交（squash/reword） |
| [`git rebase --continue`](./cmd-git/rebase) | 解决冲突后继续变基 |
| [`git rebase --abort`](./cmd-git/rebase) | 放弃变基，回到操作前 |
| [`git merge --abort`](./cmd-git/merge) | 放弃合并，回到合并前 |
| 冲突处理 | 编辑冲突文件 → `git add` → `git commit`（merge）或 `git rebase --continue` |

## 远程协作

| 命令 | 说明 |
|---|---|
| [`git remote -v`](./cmd-git/remote) | 查看远程仓库地址 |
| [`git remote add origin <url>`](./cmd-git/remote) | 添加远程仓库 |
| [`git remote set-url origin <url>`](./cmd-git/remote) | 修改远程地址 |
| [`git fetch origin`](./cmd-git/fetch-pull) | 拉取远程最新，但不合并到本地 |
| [`git pull`](./cmd-git/fetch-pull) | = fetch + merge（拉取并合并当前分支） |
| [`git pull --rebase`](./cmd-git/fetch-pull) | 拉取并用变基方式整合（保持线性历史） |
| [`git push origin 名`](./cmd-git/push) | 推送当前分支到远程 |
| [`git push -u origin 名`](./cmd-git/push) | 首次推送并建立跟踪关系 |
| [`git push`](./cmd-git/push) | 已建立跟踪后直接推送 |
| [`git push origin --delete 名`](./cmd-git/push) | 删除远程分支 |
| [`git branch -vv`](./cmd-git/branch) | 查看本地分支与远程跟踪分支的领先/落后情况 |

## 撤销与回退

| 命令 | 说明 |
|---|---|
| [`git restore 文件`](./cmd-git/reset-revert-restore) | 丢弃工作区未暂存的改动 |
| [`git restore --staged 文件`](./cmd-git/reset-revert-restore) | 把文件移出暂存区（不丢弃改动） |
| [`git reset --soft HEAD~1`](./cmd-git/reset-revert-restore) | 撤销上次提交，改动保留在暂存区 |
| [`git reset --mixed HEAD~1`](./cmd-git/reset-revert-restore) | 撤销上次提交，改动保留在工作区（默认） |
| [`git reset --hard HEAD~1`](./cmd-git/reset-revert-restore) | 撤销上次提交并丢弃所有改动（危险） |
| [`git revert <commit>`](./cmd-git/reset-revert-restore) | 生成一个反向提交来抵消某次改动（安全，适合已推送历史） |
| [`git cherry-pick <commit>`](./cmd-git/advanced) | 把某次提交单独拣选到当前分支 |
| [`git commit --amend`](./cmd-git/commit) | 修补最后一次提交（改信息或补文件，未推送时用） |

## 暂存（stash）

| 命令 | 说明 |
|---|---|
| [`git stash`](./cmd-git/stash) | 把当前未提交改动藏起来，工作区变干净 |
| [`git stash push -m "说明"`](./cmd-git/stash) | 带说明地暂存 |
| [`git stash list`](./cmd-git/stash) | 查看所有储藏 |
| [`git stash pop`](./cmd-git/stash) | 恢复最近一次储藏并删除该条 |
| [`git stash apply`](./cmd-git/stash) | 恢复但保留储藏记录 |
| [`git stash drop`](./cmd-git/stash) | 删除最近一条储藏 |
| [`git stash show -p stash@{0}`](./cmd-git/stash) | 查看某条储藏的具体改动 |

## 标签

| 命令 | 说明 |
|---|---|
| [`git tag`](./cmd-git/tag) | 列出所有标签 |
| [`git tag v1.0.0`](./cmd-git/tag) | 轻量标签 |
| [`git tag -a v1.0.0 -m "发布说明"`](./cmd-git/tag) | 附注标签（推荐） |
| [`git show v1.0.0`](./cmd-git/log-show) | 查看标签信息 |
| [`git push origin v1.0.0`](./cmd-git/tag) | 推送单个标签 |
| [`git push origin --tags`](./cmd-git/tag) | 推送所有标签 |
| [`git tag -d v1.0.0`](./cmd-git/tag) | 删除本地标签 |
| [`git push origin --delete v1.0.0`](./cmd-git/tag) | 删除远程标签 |

## 子模块（submodule）

| 命令 | 说明 |
|---|---|
| [`git submodule add <url> 目录`](./cmd-git/submodule) | 添加子模块 |
| [`git clone --recurse-submodules <url>`](./cmd-git/submodule) | 克隆时自动拉取子模块 |
| [`git submodule update --init --recursive`](./cmd-git/submodule) | 已克隆仓库后初始化子模块 |
| [`git submodule update --remote`](./cmd-git/submodule) | 更新子模块到其远程最新 |
| [`git submodule deinit -f 目录`](./cmd-git/submodule) | 移除子模块 |

## 实用技巧

| 命令 | 说明 |
|---|---|
| [`git bisect start`](./cmd-git/advanced) | 二分法定位引入 bug 的提交 |
| [`git bisect bad` / `git bisect good <commit>`](./cmd-git/advanced) | 标记坏/好版本，Git 自动二分跳转 |
| [`git bisect reset`](./cmd-git/advanced) | 退出二分，回到原分支 |
| [`git clean -nd`](./cmd-git/advanced) | 预览会被删除的未跟踪文件（先 dry-run） |
| [`git clean -fd`](./cmd-git/advanced) | 删除未跟踪的文件和目录（危险） |
| `git shortlog -sn` | 按提交数统计贡献者（详见 git log 文档） |
| [`git fsck --lost-found`](./cmd-git/advanced) | 修复损坏仓库、找回悬空提交 |

## 团队协作工作流

**三种主流分支模型：**

| 模型 | 做法 | 适用场景 |
|---|---|---|
| GitFlow | `main` + `develop` + `feature/release/hotfix` 长期分支 | 有版本发布周期的传统项目 |
| Trunk-based | 所有人频繁合并到 `main`，靠特性开关控制发布 | 持续交付、微服务团队（推荐学习） |
| GitHub Flow | `main` + 短生命周期 feature 分支 + PR | 云原生、Web 项目最常见 |

**提交信息规范（Conventional Commits）：**

```text
<类型>(<可选范围>): <简短描述>

[可选正文：说明为什么这样改，而不是怎么改]

[可选脚注：BREAKING CHANGE / Closes #123]
```

常用类型：`feat`(新功能)、`fix`(修 bug)、`docs`(文档)、`style`(格式)、`refactor`(重构)、`test`(测试)、`chore`(构建/工具)、`perf`(性能)。

**PR / MR 流程（GitHub / GitLab 通用）：**

1. 从 `main` 切出 feature 分支，小步提交。
2. 推送分支，发起 Pull Request（GitHub）/ Merge Request（GitLab）。
3. CI 自动跑测试、Lint、构建；至少一人 Review 通过。
4. 合并前 `git pull --rebase origin main` 解决冲突，保持历史干净。
5. 合并方式：优先 Squash merge（一个 PR 一个提交）或 Rebase merge，避免无关 merge commit。
6. 合并后删除 feature 分支，标签发布版本。

> 团队分支工作流从 0 到 1 详解（三种分支模型选型 + 完整 PR/MR 流程）：[团队分支工作流](./cmd-git/workflow)

::: warning 生产红线
- `git reset --hard`、`git clean -fd` 会丢未提交改动，执行前先 [`git status`](./cmd-git/add) 确认。
- 已推送到远程并被他人基于开发的提交，不要用 `reset` 改写历史，改用 `git revert`。
- 不要把密钥、`.env`、大二进制文件提交进仓库；用 `.gitignore` 过滤。
:::

### 官方文档

- Git 官网（下载与文档）：https://git-scm.com/
- Pro Git 中文版：https://git-scm.com/book/zh/v2
- Git 命令官方参考：https://git-scm.com/docs
- GitHub Docs：https://docs.github.com/
- GitLab Docs：https://docs.gitlab.com/
- Conventional Commits 规范：https://www.conventionalcommits.org/zh-hans/
