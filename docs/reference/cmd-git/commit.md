# git commit 命令详解：把暂存区打包成一次提交

> 本文是 [Git 命令速查](../git-commands#日常四件套) 中 `git commit` 的从 0 到 1 详解。
> 目标：把 `git commit -h` 里的选项讲清楚，搞懂 `-m`、`-a`、`--amend`、`-v` 分别干什么，并写好提交信息。
> 环境依据：Git 2.34.1（本机 `/tmp/demo` 实跑；RHEL/Rocky 用法一致）。

## 一、命令是干什么的

`git commit` 把**暂存区**里的内容打包成一次提交（commit），永久记入仓库历史。每次提交就是历史里的一个节点，带：作者、时间、提交信息、改动快照。

回顾一下三步：改文件 → `git add`（放进暂存区）→ `git commit`（正式记一笔）。`commit` 是真正「落账」的那一步。

> 类比：`git add` 是把商品放进待结账篮，`git commit` 是扫码结账打小票。小票上写着买了啥、什么时候买的、谁买的——这就是提交信息。

## 二、命令语法

```bash
git commit -m "提交信息"
git commit -a -m "提交信息"
git commit --amend
```

- 不给 `-m`：会打开编辑器让你写提交信息（按 `core.editor` 配置）；
- `-m "..."`：直接在命令行给信息（最常用）；
- `-a`：自动把已跟踪文件的改动 `add` 进来再提交（跳过手动 add）；
- 末尾 `-- <路径>`：只提交指定文件（哪怕别的文件也改了）。

## 三、选项全表（对照 `git commit -h`）

### 1. 提交信息怎么给

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-m "<信息>"` | 直接给提交信息 | 最常用，一行搞定 |
| `-F <文件>` | 从文件读提交信息 | 信息很长时先写文件 |
| `-e`，`--edit` | 强制打开编辑器再改一遍信息 | `-m` 给了初版但想再编辑 |
| `--cleanup=<模式>` | 如何清理信息里的空行/注释 | 脚本控制格式 |
| `-t <文件>` | 用指定模板做提交信息模板 | 团队规范信息格式 |

### 2. 提交哪些内容

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-a`，`--all` | 自动暂存所有**已跟踪**文件的修改 | 改了老文件不想再 `git add`（新文件仍要手动 add） |
| `-o`，`--only` | 只提交命令行指定的文件 | `git commit app.py -m "..."` 只提交它 |
| `-i`，`--include` | 先把指定文件加入暂存再提交 | 配合路径限定 |
| `-p`，`--patch` | 交互式挑 hunk 提交 | 一个文件只提交部分改动 |
| `--dry-run` | 试运行，不真提交 | 先看会提交啥 |

### 3. 修改最近一次提交

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `--amend` | **修补最近一次提交**：把新改动并入上次提交，并可改信息 | 上次提交信息写错了、或漏了个文件（常用但要懂风险） |
| `--author=<作者>` | 覆盖提交作者 | 帮别人提交时 |
| `--date=<时间>` | 覆盖提交时间 | 极少用 |
| `--reset-author` | 配合 `--amend`/`-C`，作者改成当前用户 | 修补时把作者改成自己 |

### 4. 其他常用

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-v`，`--verbose` | 编辑器里**显示 diff** 供你写信息时参考 | 写提交信息前再看一眼改了啥 |
| `-q`，`--quiet` | 提交成功后不输出摘要 | 脚本里用 |
| `-n`，`--no-verify` | **跳过 pre-commit / commit-msg 钩子** | 钩子报错想强行提交（慎用） |
| `-s`，`--signoff` | 加 `Signed-off-by` 尾迹 | 开源项目/DCO 规范 |
| `-S`，`--gpg-sign[=<key>]` | GPG 签名提交 | 要求签名的项目 |
| `--fixup <提交>` | 生成「修补某提交」的信息 | 配合 rebase `-i --autosquash` |

## 四、由浅入深的典型示例

### 示例 1：最基本的提交

```bash
printf 'feat: 新增登录模块\n' > note.txt
git add note.txt
git commit -m "docs: 补一条发布说明"
```

```text
[main 9f3c2a1] docs: 补一条发布说明
 1 file changed, 1 insertion(+)
 create mode 100644 note.txt
```

> 输出三行：新提交的短哈希 `9f3c2a1`、改了几个文件几行、新建了哪些文件。

### 示例 2：多行提交信息（`-m` 用多次）

```bash
git commit -m "feat: 新增登录模块" -m "支持账号密码与短信验证码登录"
```

> 两个 `-m` 会变成两段：第一段是标题，第二段是正文。比打开编辑器省事。

### 示例 3：`-a` 跳过手动 add（已跟踪文件）

先改个已跟踪文件：

```bash
printf 'main branch v4\n' >> app.py
git commit -a -m "feat: app.py 追加 v4 标记"
```

```text
[main a1b2c3d] feat: app.py 追加 v4 标记
 1 file changed, 1 insertion(+)
```

> `-a` 自动把已跟踪文件的改动加进暂存再提交。**注意：新文件（从未 add 过的）`-a` 不会带进来**，还得手动 `git add`。

### 示例 4：打开编辑器写信息（不带 `-m`）

```bash
git commit
```

> 会打开编辑器，内容类似：
>
> ```text
> # Please enter the commit message for your changes. Lines starting
> # with '#' will be ignored, and an empty message aborts the commit.
> #
> # On branch main
> # Changes to be committed:
> #       modified:   app.py
> #
> ```
>
> 在 `#` 注释上面写一行信息，保存退出即可。空信息会中止提交。

### 示例 5：`-v` 边看 diff 边写信息

```bash
git commit -v
```

> 编辑器底部会附上这次改动的 diff，写信息时不用切出去看。提交信息会更准确。

### 示例 6：`--amend` 修补最近一次提交（信息写错了 / 漏文件）

```bash
git add note.txt
git commit -m "docs: 补发布说名"     # 错别字：说名 → 说明
git add forgot.txt
git commit --amend -m "docs: 补发布说明"
```

> `--amend` 不是「在后面加一笔」，而是**把上次提交整个替换掉**：把现在暂存区的新文件（`forgot.txt`）并入，并换成新信息。改完用 `git log -1` 确认。

### 示例 7：只提交指定文件，不管其他改动

```bash
git commit app.py -m "fix: 修 app.py 的启动报错"
```

> 即使 `auth.py` 也改了，这条只提交 `app.py`。适合把改动拆成多个干净的小提交。

### 示例 8：`--dry-run` 预览会提交啥

```bash
git commit --dry-run
```

> 不真提交，只告诉你暂存区里有哪些文件。提交前心里没底时跑一遍。

### 示例 9：写符合规范的提交信息（Conventional Commits）

团队里推荐用 [Conventional Commits](https://www.conventionalcommits.org/) 规范，格式 `<类型>: <简短描述>`：

```bash
git commit -m "feat: 新增短信登录"
git commit -m "fix: 修复登录超时"
```

常用类型：

| 前缀 | 含义 | 例子 |
|---|---|---|
| `feat` | 新功能 | `feat: 新增短信登录` |
| `fix` | 修 bug | `fix: 修复登录超时` |
| `docs` | 只改文档 | `docs: 更新 README` |
| `style` | 格式（不影响逻辑） | `style: 格式化 auth.py` |
| `refactor` | 重构 | `refactor: 抽出登录服务` |
| `test` | 加测试 | `test: 补登录单测` |
| `chore` | 杂项/构建 | `chore: 升级依赖` |
| `perf` | 性能优化 | `perf: 缓存用户信息` |

好处：`git log --oneline` 一眼看懂每次干了啥，还能自动生成 changelog、自动决定版本号。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `git commit -m "信息"` | 标准提交 |
| `git commit -a -m "信息"` | 已跟踪文件改动一把提交 |
| `git commit -m "标题" -m "正文"` | 多行信息 |
| `git commit --amend` | 修补上次提交 |
| `git commit -v` | 边看 diff 边写信息 |
| `git commit <文件> -m "信息"` | 只提交指定文件 |
| `git commit --dry-run` | 预览 |

## 六、RHEL 系与 Debian 系差异

`commit` 属于 git 本体，**两系用法与输出完全一致**。细微差别：

- 默认编辑器：Ubuntu 服务器新装 Git 常默认 `vi`；RHEL 系也类似。想换成 `nano`/`vim` 自己配 `git config --global core.editor`。
- 提交钩子（pre-commit 等）：两系都靠项目里 `.husky` / `.githooks` 提供，与发行版无关。

## 七、新手易错点

1. **`git commit` 打开的编辑器不会退出**：默认 vi，按 `i` 写，写完按 `Esc`，输入 `:wq` 回车。不会用就先 `git config --global core.editor nano`。
2. **`-a` 不会提交新文件**：新文件必须先 `git add`，`-a` 只管已跟踪文件。
3. **空提交信息会中止提交**：编辑器里什么都不写就保存，Git 会拒绝。
4. **危险：`--amend` 会改写提交哈希**。如果上次提交已经 `git push` 到远程公共分支，`--amend` 后再 push 会冲突——**已推送的提交别 amend**（见 [rebase](./rebase) 黄金法则）。本地还没 push 的提交随便 amend。
5. **危险：`git commit --no-verify` 跳过钩子**，会绕过 lint/格式检查，别滥用。
6. **提交信息写成 "update"、"fix"、"123"**：几周后自己都看不懂。按 Conventional Commits 写清类型和动作。
7. **一次提交塞十件事**：尽量一个提交只做一件事，方便回滚和 review。

## 八、相关命令与文档

- 速查页：[Git 命令速查](../git-commands#日常四件套)
- 提交前先看改动：[diff](./diff)、[add](./add)
- 看错了怎么改历史：[reset-revert-restore](./reset-revert-restore)
- 把多个提交整理干净：[rebase](./rebase)
- 团队里 PR 怎么写：[workflow](./workflow)
