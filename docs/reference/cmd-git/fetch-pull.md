# git fetch 与 git pull 命令详解：把远程最新代码拉到本地

> 本文是 [Git 命令速查](../git-commands#远程协作) 中 `git fetch` 与 `git pull` 的从 0 到 1 详解。
> 目标：搞懂 fetch 只下载不合并、pull = fetch + merge 的区别，会用 `--rebase`、`--ff-only`、`--prune`。
> 环境依据：Git 2.34.1（本机 `/tmp/demo` 实跑；RHEL/Rocky 用法一致）。

## 一、命令是干什么的

- `git fetch`：从远程**下载**最新提交、分支、标签，但**不碰你的工作区**。它只更新「远程跟踪分支」（`origin/main`），你的本地 `main` 不动，代码不变。最安全。
- `git pull`：等于 **`git fetch` + `git merge`**。下载完立刻把远程改动合并进你当前分支。一步到位，但如果两边都有提交会产生合并提交。

> 类比：fetch 像「只看一眼快递到哪了，不拆包」；pull 像「直接把快递拆了摆进你家客厅」。想稳妥就先 fetch，看清楚再决定怎么合；想快就 pull。

## 二、命令语法

```bash
git fetch [远程名] [分支]        # 只下载，不合并
git fetch --all --prune          # 拉所有远程并清理过期分支
git pull [远程名] [分支]         # 下载并合并到当前分支
git pull --rebase               # 下载并变基（而非合并）
git pull --ff-only              # 只能快进，否则失败
```

- `git fetch origin`：下载 origin 的更新；
- `git pull origin main`：下载并把远程 main 合进当前分支。

## 三、选项全表（对照 `git fetch -h`、`git pull -h`）

### 1. git fetch 选项

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `<远程名>` | 从指定远程下载 | `git fetch origin` |
| `--all` | 拉**所有**远程 | 挂了多个远程时 |
| `-p`，`--prune` | 顺手清理远程已删除的分支 | 同事删分支后同步（常用） |
| `-t`，`--tags` | 拉所有标签 | 默认就会拉 |
| `--depth <n>` | 浅克隆加深 | 浅仓库补历史 |
| `--unshallow` | 把浅仓库变成完整仓库 | 当初 `--depth 1` 拉的想补全 |
| `-j <n>` | 并行拉子模块 | 子模块多时 |
| `-f`，`--force` | 强制覆盖本地引用 | 慎用 |

### 2. git pull 选项——合并相关

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-r`，`--rebase` | 下载后**变基**而非合并 | 团队约定「pull 用 rebase」时（推荐） |
| `--ff-only` | 只能快进，否则失败 | 不想产生合并提交 |
| `--no-rebase` | 下载后合并（默认） | 覆盖全局配置 |
| `--no-commit` | 合并了但不自动提交 | 想先检查 |
| `--squash` | 压成一个改动 | 少见 |
| `--autostash` | 拉之前自动 stash、后 pop | 工作区脏时 |

### 3. git pull 选项——fetch 相关

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `--all` | 从所有远程拉 | 多远程时 |
| `--no-tags` | 不拉标签 | 少见 |

## 四、由浅入深的典型示例

### 示例 1：fetch 只下载不动工作区

```bash
git fetch origin
```

> 安静地把 origin 的新提交下载到本地，更新 `origin/main` 等远程跟踪分支。你的代码文件一个都没变。之后用 `git log main..origin/main` 看远程比你多了啥。

### 示例 2：fetch 后看看远程领先多少

```bash
git fetch origin
git log --oneline main..origin/main
```

> `main..origin/main` 表示「origin/main 有、本地 main 没有」的提交。看清楚了再决定 merge 还是 rebase。

### 示例 3：`--prune` 清理远程已删分支

```bash
git fetch --prune origin
```

```text
 - [deleted]         (none)     -> origin/feature/login
```

> 同事在远程删了 `feature/login`，本地那条 `remotes/origin/feature/login` 残留，prune 顺手清掉。

### 示例 4：标准 pull（fetch + merge）

```bash
git pull origin main
```

```text
remote: Enumerating objects: 5, done.
Unpacking objects: 100% (3/3), done.
From /tmp/demo
 * branch            main       -> FETCH_HEAD
Updating d07c6aa..e5f6a7b
Fast-forward
 app.py | 1 +
 1 file changed, 1 insertion(+)
```

> 如果能快进就直接前移；如果两边都有提交，会产生一个合并提交（类似 `git merge`），并可能弹编辑器让你写合并信息。

### 示例 5：`pull --rebase`（团队推荐写法）

```bash
git pull --rebase origin main
```

> 把你本地未推送的提交**搬到**远程最新提交后面，历史是直线，不产生「Merge branch 'main' of ...」这种无意义合并提交。长期推荐。配全局：

```bash
git config --global pull.rebase true
```

以后裸 `git pull` 就自动变基。

### 示例 6：`pull --ff-only` 防止意外合并提交

```bash
git pull --ff-only origin main
```

> 如果远程改动不能快进（说明你本地有独立提交），它**直接失败**而不是偷偷产生合并提交。适合 CI/脚本里，强制你手动决定怎么整合。

### 示例 7：工作区有未提交改动，pull 报脏

```bash
git pull --rebase --autostash
```

> `--autostash` 会先把你本地改动临时存起来，拉完再自动恢复。避免「工作区脏不让 pull」。

### 示例 8：浅仓库补全历史

```bash
git fetch --unshallow origin
```

> 当初 `git clone --depth 1` 拉的仓库，`git log` 看不到老历史。用它把完整历史拉回来。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `git fetch origin` | 只下载不合并 |
| `git fetch --all --prune` | 拉全部远程并清理 |
| `git pull origin main` | 下载并合并 |
| `git pull --rebase origin main` | 下载并变基（推荐） |
| `git pull --ff-only` | 只能快进 |
| `git log main..origin/main` | 看远程领先多少 |

## 六、RHEL 系与 Debian 系差异

`fetch` / `pull` 属于 git 本体，**两系用法与输出完全一致**。差别在网络：

- 走代理：`git config --global http.proxy http://proxy:port`，两系通用；
- 大仓库拉取慢：两系都可用 `--depth 1` 浅克隆，与发行版无关。

## 七、新手易错点

1. **pull 和 fetch 分不清**：fetch 只下载不动代码，pull 下载+合并。想安全就先 fetch。
2. **`git pull` 弹出一堆合并提交信息编辑器**：因为两边都有提交产生了合并提交。想避免就 `git pull --rebase`。
3. **pull 时冲突**：和 merge 一样会停下来让你解冲突，`git add` 后 `git commit`（或 `git rebase --continue`）完成。
4. **危险：`git pull --rebase` 对已推送的公共分支相当于改写历史**。只在你个人分支上用；团队公共分支别乱 rebase。
5. **`git pull` 没指定远程/分支时报「no tracking information」**：说明当前分支没设上游。首次用 `git push -u`（见 [push](./push)），或手动 `git pull origin main`。
6. **远程删了分支本地还在**：那是远程跟踪分支残留，`git fetch --prune` 清，不是你本地的分支。

## 八、相关命令与文档

- 速查页：[Git 命令速查](../git-commands#远程协作)
- 远程地址管理：[remote](./remote)
- 往远程推代码：[push](./push)
- 变基原理与黄金法则：[rebase](./rebase)
- CI 里怎么拉代码：[devops-cicd-advanced](../../guide/devops-cicd-advanced)
