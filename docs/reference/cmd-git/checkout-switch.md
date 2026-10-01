# git switch 与 git checkout 命令详解：切换分支、新建分支、回到某次提交

> 本文是 [Git 命令速查](../git-commands#分支管理) 中 `git switch` 与 `git checkout` 的从 0 到 1 详解。本篇一次讲清新版 `git switch` 和老版 `git checkout` 的对照用法。
> 目标：搞懂 `switch -c`、`switch -`、`switch --detach`，以及 `checkout -- 文件` 这种「丢弃工作区改动」的老写法。
> 环境依据：Git 2.34.1（本机 `/tmp/demo` 实跑；RHEL/Rocky 用法一致）。

## 一、命令是干什么的

这两个命令都用来**切换工作区到另一条分支 / 另一次提交**。

- `git switch`：Git 2.23 新增的**专用切换分支**命令，职责单一，新手友好；
- `git checkout`：老命令，一身兼数职（切分支、恢复文件、detach HEAD），历史悠久、到处都是它。

> 类比：两者都像「换个工作台」。`switch` 是新设计的专用按钮，只负责换分支；`checkout` 是老的多功能瑞士军刀，换分支、恢复文件都用它。新项目优先学 `switch`，但看老教程会遇到 `checkout`，必须认识。

## 二、命令语法

```bash
git switch <分支名>            # 切到某分支
git switch -c <新分支>         # 新建并切换
git switch -                   # 切回上一个分支
git switch --detach <提交>     # 脱离分支看某次提交

git checkout <分支名>          # 老写法：切分支
git checkout -b <新分支>        # 老写法：新建并切
git checkout -- <文件>         # 老写法：丢弃该文件工作区改动
```

- 给分支名：切过去；
- `-c`/`-b`：新建并切；
- `--detach`：进入「分离 HEAD」状态，不属任何分支。

## 三、选项全表（对照 `git switch -h`、`git checkout -h`）

### 1. git switch 选项

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `<分支>` | 切到某分支 | 日常切换 |
| `-c <名字>`，`--create <名字>` | **新建并切到**新分支 | 开新功能（最常用） |
| `-C <名字>`，`--force-create` | 新建/重置并切 | 分支已存在也强制切过去 |
| `-` | 切回**上一个**分支 | 在两个分支间来回跳（极好用） |
| `-d`，`--detach` | 分离 HEAD 看某次提交 | 临时看历史版本 |
| `-t`，`--track` | 新分支跟踪远程分支 | 从远程分支建本地分支 |
| `-m`，`--merge` | 带着未提交改动做三方合并切换 | 工作区有改动又想切分支 |
| `-f`，`--force` | 强制切换，丢弃本地改动 | 不要未提交改动时 |
| `--discard-changes` | 丢弃本地改动再切 | 同上 |
| `--orphan <名字>` | 建一个没有父提交的孤儿分支 | 建 gh-pages 之类 |
| `--guess` | 猜你想建同名本地分支 | 敲错分支名时自动补救 |

### 2. git checkout 选项（常用部分）

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `<分支>` | 切分支 | 老教程里到处是它 |
| `-b <名字>` | 新建并切 | 等价 `switch -c` |
| `-B <名字>` | 强制新建/重置并切 | 等价 `switch -C` |
| `-d`，`--detach` | 分离 HEAD | 同 `switch --detach` |
| `-- <文件>` | 用暂存区版本**覆盖工作区文件** | 丢弃改动（老写法，见易错点） |
| `<提交> -- <文件>` | 用某次提交的版本覆盖工作区文件 | 把单文件恢复到历史版本 |
| `-f`，`--force` | 强制切换 | 丢弃未提交改动 |
| `-m`，`--merge` | 带改动三方合并切换 | 工作区脏也想切分支 |
| `-2`，`--ours` / `-3`，`--theirs` | 冲突时取本方/对方版本 | 解冲突 |
| `-p`，`--patch` | 交互式挑 hunk 恢复 | 精细恢复 |

## 四、由浅入深的典型示例

### 示例 1：切到已有分支

```bash
git switch feature/login
```

```text
Switched to branch 'feature/login'
```

### 示例 2：新建并切换（最常用）

```bash
git switch -c feature/payment
```

```text
Switched to a new branch 'feature/payment'
```

> 等价老写法 `git checkout -b feature/payment`。

### 示例 3：`-` 切回上一个分支（高频）

```bash
git switch -
```

```text
Switched to branch 'main'
Your branch is up to date with 'origin/main'.
```

> 在 main 和 feature 之间反复横跳时，`git switch -` 就是「Alt-Tab」，不用记分支名。

### 示例 4：分离 HEAD 看某次历史提交

```bash
git switch --detach v1.0.0
```

```text
Note: switching to 'v1.0.0'.

You are in 'detached HEAD' state...
```

> 你现在站在标签 v1.0.0 上，不属于任何分支。可以看老代码、跑老版本，但**直接在这里提交会有风险**——因为没有分支指着这些新提交，切走后容易丢。想基于它开新分支，就 `git switch -c fix/from-v1`。

### 示例 5：工作区有改动想切分支

```bash
printf 'wip\n' >> app.py
git switch main
```

> 如果改动和目标分支不冲突，Git 会让你带着改动切过去；如果冲突会报错。想硬切丢弃改动用 `git switch -f`；想先存起来用 `git stash`（见 [stash](./stash)）。

### 示例 6：老写法 `checkout -- 文件` 丢弃工作区改动

```bash
git checkout -- app.py
```

> 这是老命令里**最危险也最常用**的一条：它用暂存区（或 HEAD）的版本**覆盖** `app.py`，你刚才在工作区对它的未提交修改**全部丢失**。新写法等价于：

```bash
git restore app.py
```

（见 [reset-revert-restore](./reset-revert-restore)。）

### 示例 7：把单个文件恢复到历史某个版本

```bash
git checkout v1.0.0 -- app.py
```

> 把 v1.0.0 时的 `app.py` 内容取到当前工作区并暂存。注意这不是切分支，只是「把这个文件抽回历史版本」，改完要 commit。

### 示例 8：对照速查——新旧写法一表清

| 目的 | 新写法（推荐） | 老写法 |
|---|---|---|
| 切分支 | `git switch main` | `git checkout main` |
| 新建并切 | `git switch -c dev` | `git checkout -b dev` |
| 切回上个分支 | `git switch -` | `git checkout -` |
| 分离 HEAD | `git switch --detach <提交>` | `git checkout <提交>` |
| 丢弃文件改动 | `git restore <文件>` | `git checkout -- <文件>` |

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `git switch <分支>` | 切分支 |
| `git switch -c <名字>` | 新建并切 |
| `git switch -` | 切回上个分支 |
| `git switch --detach <提交>` | 看历史版本 |
| `git restore <文件>` | 丢弃文件改动（替代 checkout --） |
| `git checkout -b <名字>` | 老版新建并切 |

## 六、RHEL 系与 Debian 系差异

`switch` 是 Git 2.23（2019 年）才加的，`checkout` 一直都有。两系差异：

- 老服务器若 Git < 2.23（如 Ubuntu 18.04 自带 2.17），**没有 `git switch`**，只能用 `git checkout`。本机 2.34.1 已支持。
- 用法与输出两系完全一致，与发行版无关。

## 七、新手易错点

1. **`git switch` 在老 Git 上报未知命令**：版本太老（<2.23），改用 `git checkout`。
2. **危险：`git checkout -- <文件>` / `git restore <文件>` 会永久丢弃未提交改动**，没有回收站。敲之前确认这改动真的不要了。
3. **detached HEAD 里直接提交**：提交会挂在「无主」的 HEAD 上，一旦 `git switch` 切走，这些提交很容易丢。要么别在 detached 状态提交，要么立刻 `git switch -c 分支名` 把它变成分支。
4. **工作区脏（有未提交改动）切分支报冲突**：别 `-f` 硬切，先 `git stash` 存起来。
5. **把 `git switch` 和 `git branch` 搞混**：`git branch <名字>` 只建不切；`git switch -c <名字>` 建并切。日常用后者。
6. **`git checkout` 后面跟文件还是跟分支，含义天差地别**：跟分支名＝切分支；跟 `-- 文件`＝丢弃文件改动。这就是为什么 Git 要拆出 `switch`。

## 八、相关命令与文档

- 速查页：[Git 命令速查](../git-commands#分支管理)
- 分支的增删改：[branch](./branch)
- 切完怎么合并：[merge](./merge)
- 丢弃/恢复改动的安全写法：[reset-revert-restore](./reset-revert-restore)
- 临时存改动：[stash](./stash)
