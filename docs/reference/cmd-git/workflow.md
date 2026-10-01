# Git 团队工作流详解：GitFlow、Trunk-based、GitHub Flow 与 PR/分支保护

> 本文是 [Git 命令速查](../git-commands#团队协作工作流) 中团队协作方法论的从 0 到 1 详解。本篇偏方法论，但仍按八段组织，命令都可直接复制。
> 目标：搞清三种主流分支模型怎么选、Conventional Commits 怎么写、PR/MR 怎么走、分支保护配什么规则。
> 环境依据：Git 2.34.1（命令部分本机实跑；流程部分基于 GitHub/GitLab 通用实践）。

## 一、命令是干什么的

这一篇不是单条命令，而是「一群 Git 命令在团队里怎么配合」。同一个仓库，多人并行开发，必须约定：

- 分支怎么命名、从哪拉、合到哪；
- 提交信息怎么写才能自动发版；
- 代码怎么评审（PR/MR）；
- 主干怎么保护（不让人直接 push）。

> 类比：个人用 Git 像一个人记日记，怎么写都行；团队用 Git 像合著一本书，得约定章节分工、审稿流程、定稿谁拍板。工作流就是这个约定。

## 二、命令语法（工作流里高频出现的命令）

```bash
git switch -c feature/xxx          # 从 main 拉特性分支
git push -u origin feature/xxx     # 推送并开 PR
git pull --rebase origin main      # 同步主干最新
git merge --no-ff feature/xxx      # PR 合并（或平台点按钮）
git tag -a v1.0.0 -m "..."         # 发版打标签
```

## 三、三种分支模型对比

### 1. 模型对比表

| 维度 | GitFlow | Trunk-based | GitHub Flow |
|---|---|---|---|
| 常驻分支 | `main` + `develop` + `release/*` + `feature/*` + `hotfix/*` | 只有 `main`（短生命周期特性分支） | 只有 `main` + 短特性分支 |
| 分支寿命 | 长，按月/版本 | 很短（一天内合回） | 短 |
| 发版 | `release` 分支筹备，打 tag | 随时可发，main 即发布 | main 即部署 |
| 适合 | 有明确版本周期、客户端/固件 | 持续部署、互联网后端 | Web 产品、持续部署 |
| 复杂度 | 高（分支多、规则重） | 低 | 低 |
| 合并方式 | `--no-ff` 保留分支痕迹 | 小步快跑，常 squash | squash/rebase |

### 2. 怎么选

- **小团队 / 互联网后端 / 每天发版**：选 Trunk-based 或 GitHub Flow，主干直接保护，特性分支活一两天就合。
- **客户端 / 移动 / 有版本号周期**：选 GitFlow，`release` 分支冻结筹备下一个版本，`hotfix` 线上修。
- 别照搬：很多团队是「Trunk-based + 发版时打 tag + 紧急修复开 hotfix 分支」的混合体。

## 四、由浅入深的典型示例

### 示例 1：GitHub Flow 一次完整流程

```bash
git switch main
git pull --rebase origin main
git switch -c feature/login
# 改代码，多次小提交
git push -u origin feature/login
# 在 GitHub/GitLab 上开 Pull Request / Merge Request
# 同事评审、改意见、CI 跑过
# 点 Squash and merge，删除特性分支
git switch main
git pull --rebase origin main
```

### 示例 2：Conventional Commits 提交信息规范

```bash
git commit -m "feat: 支持短信登录"
git commit -m "fix: 修复登录超时"
git commit -m "docs: 更新部署文档"
```

| 前缀 | 触发发版动作 |
|---|---|
| `feat!:` / `BREAKING CHANGE` | 主版本号 +1（不兼容） |
| `feat:` | 次版本号 +1（新功能） |
| `fix:` / `perf:` 等 | 修订号 +1 |

配合工具（semantic-release、release-please）能**自动生成 changelog 和发版**，不用手写版本号。

### 示例 3：PR/MR 评审流程

1. 特性分支 push 后开 PR；
2. CI 自动跑测试、lint、构建；
3. 至少 1~2 个同事 approve；
4. 讨论修改，作者继续 push 到同分支（PR 自动更新）；
5. 合入方式三选一：
   - **Merge commit**：保留分支所有提交历史；
   - **Squash**：把 N 个提交压成 1 个合进主干（历史干净，推荐）；
   - **Rebase**：把提交原样接到主干后（线性历史）。

### 示例 4：分支保护规则（在 GitHub/GitLab 后台配）

对 `main` 分支至少配：

- **禁止直接 push**：必须通过 PR 合入；
- **要求 PR 审批**：至少 N 人 approve；
- **要求 CI 通过**：测试/构建没过不能合；
- **要求最新代码**：分支必须经过 rebase/merge 最新 main；
- **禁止 force push** 和删除分支。

```bash
# 本地想强推 main 会被保护规则拒绝，这是正常的、想要的效果
git push --force origin main   # 被服务器拒绝
```

## 五、高频组合速记

| 命令/动作 | 用途 |
|---|---|
| `git switch -c feature/xxx` | 拉特性分支 |
| `git pull --rebase origin main` | 同步主干 |
| `git push -u origin feature/xxx` | 推送开 PR |
| PR 选 Squash merge | 压成干净提交 |
| `git tag -a v1.0.0 -m "..."` | 发版打 tag |
| `git push origin --tags` | 推 tag |

## 六、RHEL 系与 Debian 系差异

命令本身两系一致。差别在平台：

- GitHub Flow 配 GitHub；GitLab 叫 MR（Merge Request）；Gitea/内网 Git 类似；
- CI 钩子两系都靠平台配置（GitHub Actions / GitLab CI），与发行版无关。

## 七、新手易错点（含危险提示）

1. **危险：直接往 `main` 推代码**：本地能 commit，但远程开了分支保护会被拒；没保护的话就是事故。永远走 PR。
2. **危险：在共享特性分支上 `force push` / rebase**：别人正在基于它开发，会被搞乱。rebase 黄金法则——只在自己的个人分支上改写历史。
3. **特性分支活太久不合并**：和主干分叉越远，合并冲突越痛。小步快跑，一两天合一次。
4. **PR 里塞几十个不相关提交**：评审没法看。一个 PR 只做一件事，提交用 squash 压干净。
5. **提交信息乱写**：`update`、`fix bug` 无法自动发版、无法回溯。按 Conventional Commits 写。
6. **合完 PR 不删特性分支**：远端堆积一堆分支。合并完随手删。
7. **发版忘了打 tag / push tag**：线上出问题想回到发版点，找不到标记点。发版即打 tag 并 push。

## 八、相关命令与文档

- 速查页：[Git 命令速查](../git-commands#团队协作工作流)
- 合并与变基的命令细节：[merge](./merge)、[rebase](./rebase)
- push 与 force-with-lease：[push](./push)
- 标签发版：[tag](./tag)
- CI/CD 怎么接 PR 与自动发版：[devops-cicd-advanced](../../guide/devops-cicd-advanced)
- GitOps 里 Git 作为部署源：[automation-gitops](../../guide/automation-gitops)
