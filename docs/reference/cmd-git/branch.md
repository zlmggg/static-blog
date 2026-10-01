# git branch 命令详解：列出、创建、重命名、删除分支

> 本文是 [Git 命令速查](../git-commands#分支管理) 中 `git branch` 的从 0 到 1 详解。
> 目标：把 `git branch -h` 里的选项讲清楚，搞懂 `-a`、`-m`、`-d`、`-D`、`-vv` 分别干什么，以及「跟踪关系」是什么。
> 环境依据：Git 2.34.1（本机 `/tmp/demo` 实跑；RHEL/Rocky 用法一致）。

## 一、命令是干什么的

`git branch` 用来**管理分支**：列出现有分支、新建分支、重命名分支、删除分支。注意它本身**不切换分支**——切换是 `git switch` / `git checkout` 的事（见 [checkout-switch](./checkout-switch)）。

分支在 Git 里就是一个**指向某次提交的可移动指针**，非常轻量。你可以并行开好几条分支各干各的，互不影响。

> 类比：`git branch` 像给电影开「平行剪辑线」——主线（main）继续拍，另开一条支线（feature/login）拍别的戏，拍完再剪回主线。`git branch` 就是管这些「剪辑线」的工具。

## 二、命令语法

```bash
git branch                        # 列出本地分支
git branch <新分支名>             # 新建分支（不切换）
git branch -m <旧名> <新名>       # 重命名
git branch -d <分支名>            # 删除（已合并的）
git branch -D <分支名>            # 强制删除
git branch -vv                    # 列出并显示跟踪关系
```

- 不给子命令：列分支；
- 给一个名字：在当前提交上**新建**一个分支指针（不切过去）；
- `-d`/`-D`：删；`-m`：改名。

## 三、选项全表（对照 `git branch -h`）

### 1. 列出分支

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| 无参数 | 列本地分支 | 看有哪些线 |
| `-a`，`--all` | 本地 + 远程跟踪分支都列 | 看远程有哪些分支（常用） |
| `-r`，`--remotes` | 只列远程跟踪分支 | 只关心远程时 |
| `-v` / `-vv` | 显示哈希、标题、**跟踪关系** | `-vv` 看本地分支跟踪哪个远程分支（常用） |
| `--list` | 列名字（可带通配符） | `git branch --list "feature/*"` |
| `--show-current` | 只显示当前分支名 | 脚本里用 |
| `--column` | 多列排列 | 分支多时紧凑 |

### 2. 创建 / 重命名 / 删除

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `<名字>` | 在当前提交新建分支 | `git branch dev`（不切换） |
| `<名字> <起点>` | 从指定提交/分支新建 | `git branch hotfix v1.0.0` |
| `-f`，`--force` | 强制重建（已存在也覆盖） | 分支指错提交时 |
| `-m`，`--move` | 重命名分支 | `git branch -m old new` |
| `-M` | 强制重命名（目标已存在也覆盖） | 同上加强版 |
| `-c`，`--copy` | 复制分支 | 少见 |
| `-d`，`--delete` | 删除**已合并**的分支 | 删完活分支（安全） |
| `-D` | 强制删除**未合并**的分支 | 确认不要了才用 |

### 3. 跟踪关系与过滤

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-t`，`--track` | 新建分支时设置上游跟踪 | 从远程分支建本地分支时 |
| `-u <上游>`，`--set-upstream-to=<上游>` | 改现有分支的上游 | `git branch -u origin/dev` |
| `--unset-upstream` | 取消跟踪关系 | 不想要自动跟踪时 |
| `--merged <提交>` | 只列已合并到某提交的分支 | 找「可以安全删」的分支 |
| `--no-merged <提交>` | 只列**还没合并**的分支 | 找还有活的分支 |
| `--contains <提交>` | 只列包含某提交的分支 | 「这个提交在哪些分支上」 |
| `--sort=<键>` | 按字段排序 | `--sort=-committerdate` 看最近动过的 |
| `--points-at <对象>` | 只列指向某提交的分支 | 找「哪个分支指着这个提交」 |

## 四、由浅入深的典型示例

### 示例 1：列出本地分支

```bash
git branch
```

```text
  feature/login
* main
```

> 前面带 `*` 的是**当前所在分支**。这里 `main` 是当前分支。

### 示例 2：`-a` 连远程跟踪分支一起列

```bash
git branch -a
```

```text
  feature/login
* main
  remotes/origin/feature/login
  remotes/origin/main
```

> `remotes/origin/...` 是**远程跟踪分支**，不是本地分支，是 Git 记住的「远程那边分支长啥样」。

### 示例 3：`-vv` 看跟踪关系（最有用）

```bash
git branch -vv
```

```text
  feature/login 963b990 feat: app.py 升级到 v2
* main          d07c6aa [origin/main] merge: 合并 feature/login，解决 app.py 冲突
```

逐列读：

- 第一列：分支名；
- 第二列：短哈希；
- 第三列：提交标题；
- `[origin/main]`：`main` 跟踪着远程 `origin/main`。`feature/login` 后面没有方括号，说明它**还没有跟踪远程分支**（从没 push 过）。

如果本地领先/落后远程，会显示 `[origin/main: ahead 2]` 或 `[origin/main: behind 1]`。

### 示例 4：新建分支（不切换）

```bash
git branch hotfix/login-crash
git branch
```

> 新建了 `hotfix/login-crash`，但当前还在 `main`。要切过去用 `git switch hotfix/login-crash`。日常更常用 `git switch -c <名字>`（一步建并切，见 [checkout-switch](./checkout-switch)）。

### 示例 5：重命名分支

```bash
git branch -m hotfix/login-crash hotfix/login-timeout
```

> 把分支名改准确。如果改名的是当前分支，直接 `git branch -m 新名` 即可。

### 示例 6：删除已合并的分支（安全）

```bash
git branch -d feature/login
```

```text
Deleted branch feature/login (was 963b990).
```

> `-d` 只在分支**已经合并进当前分支**时才让删。没合并的会报错并提示用 `-D`。

### 示例 7：强制删除未合并的分支（危险）

```bash
git branch -D experiment/wrong-idea
```

> 分支上还没合并的提交会**丢失**（虽然 reflog 短期内还能找回）。确认不要了再用。

### 示例 8：找出已合并、可以安全删的分支

```bash
git branch --merged
```

> 列出所有已经合并进当前分支的本地分支——这些就是可以放心 `-d` 的。

### 示例 9：给现有分支设置跟踪关系

```bash
git branch -u origin/main
```

> 让当前分支跟踪 `origin/main`。之后 `git pull`、`git status` 就知道跟谁比 ahead/behind。等价于首次 push 时加 `-u`（见 [push](./push)）。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `git branch` | 列本地分支 |
| `git branch -a` | 列本地 + 远程分支 |
| `git branch -vv` | 看跟踪关系与 ahead/behind |
| `git branch <名字>` | 新建分支（不切） |
| `git branch -m 旧 新` | 重命名 |
| `git branch -d <分支>` | 删已合并分支 |
| `git branch -D <分支>` | 强制删 |
| `git branch --merged` | 找可安全删的分支 |
| `git branch -u origin/分支` | 设置上游跟踪 |

## 六、RHEL 系与 Debian 系差异

`branch` 属于 git 本体，**两系用法与输出完全一致**。唯一差别：

- 老版本 Git 默认初始分支叫 `master`，新版（2.28+）可用 `init.defaultBranch` 改成 `main`。本机 2.34.1 已支持。
- 远程跟踪分支前缀都是 `remotes/origin/`，与发行版无关。

## 七、新手易错点

1. **`git branch <名字>` 建完以为切过去了**：没有！它只建不切。要 `git switch <名字>`。
2. **`git branch -d` 报「not fully merged」**：说明分支还有没合并的提交。确认不要了用 `-D`，否则先去合并。
3. **`git branch -a` 里的 `remotes/origin/xxx` 删不掉**：那是远程跟踪分支，要删的话用 `git push origin --delete xxx`（见 [push](./push)）或 `git remote prune`（见 [fetch-pull](./fetch-pull)）。
4. **`-vv` 里没看到 `[origin/xxx]`**：分支没设上游，`git pull` 会不知道拉哪个。首次 push 加 `-u`。
5. **危险：`git branch -D` 删掉未合并分支后，那些提交在 reflog 过期后（默认 90 天）真的会被 GC 回收**，找不回来。
6. **分支名别用中文/空格**：虽然 Git 支持，但跨平台、脚本处理容易出问题，统一用小写英文加连字符。

## 八、相关命令与文档

- 速查页：[Git 命令速查](../git-commands#分支管理)
- 怎么切换 / 新建并切换：[checkout-switch](./checkout-switch)
- 分支怎么合并回 main：[merge](./merge)
- 分支历史怎么整理：[rebase](./rebase)
- 团队怎么用分支：[workflow](./workflow)
