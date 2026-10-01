# git tag 命令详解：给提交打版本号（轻量标签与附注标签）

> 本文是 [Git 命令速查](../git-commands#标签) 中 `git tag` 的从 0 到 1 详解。
> 目标：搞懂轻量标签和附注标签的区别，会用 `-a -m`、`show`、push、`--tags`、`-d`、远程删除。
> 环境依据：Git 2.34.1（本机 `/tmp/demo` 实跑；RHEL/Rocky 用法一致）。

## 一、命令是干什么的

`git tag` 给某个提交**起一个人类可读的名字**，通常叫版本号，比如 `v1.0.0`、`v2.3.1`。它像分支指针，但**标签一旦打好就不动**（不会随新提交前进），专门用来标记「这个提交就是那次发布」。

两种标签：

- **轻量标签（lightweight）**：就一个指向提交的指针，没有别的信息。`git tag v1.0.0`。
- **附注标签（annotated）**：是一个完整的对象，带打标签人、日期、说明信息，可 GPG 签名。发版推荐用它：`git tag -a v1.1.0 -m "发布说明"`。

> 类比：分支像「正在连载的漫画」，标签像「单行本第 1 卷」——固定在某一画，永远指那次发布。附注标签就是单行本上印的「作者、出版日期、后记」。

## 二、命令语法

```bash
git tag <名字>                    # 轻量标签（打在当前提交）
git tag -a <名字> -m "说明"        # 附注标签
git tag                           # 列标签
git show <名字>                   # 看标签详情
git push origin <名字>            # 推单个标签
git push origin --tags           # 推所有标签
git tag -d <名字>                 # 删本地标签
git push origin --delete <名字>   # 删远程标签
```

## 三、选项全表（对照 `git tag -h`）

### 1. 创建标签

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `<名字>` | 建轻量标签 | 临时标记 |
| `-a`，`--annotate` | 建**附注标签** | 正式发版（配 `-m`） |
| `-m "<说明>"` | 标签信息 | 附注标签用，不弹编辑器 |
| `-F <文件>` | 从文件读说明 | 说明很长时 |
| `-s`，`--sign` | GPG 签名的附注标签 | 要求签名的开源项目 |
| `-u <key>` | 指定签名 key | 多 key 时 |
| `-f`，`--force` | 覆盖已存在的标签 | 标签打错提交时 |
| `<名字> <提交>` | 给历史某个提交打标签 | 补打老版本标签 |

### 2. 列出与查看

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-l`，`--list` | 列标签（可带通配符） | `git tag -l "v1.*"` |
| `-n[<n>]` | 列标签时显示 n 行说明 | `git tag -n` 看附带信息 |
| `<名字>` 配合 `git show` | 看标签详情 + 指向的提交 | 看附注信息 |
| `--contains <提交>` | 列包含某提交的标签 | 「这个提交在哪个版本里」 |
| `--points-at <提交>` | 列指向某提交的标签 | 找哪个标签指着这提交 |
| `--sort=<键>` | 排序 | `--sort=-version:refname` 按版本号 |

### 3. 删除

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-d`，`--delete` | 删本地标签 | 打错了 |
| `git push origin --delete <名字>` | 删远程标签 | 远程标签错了 |

## 四、由浅入深的典型示例

### 示例 1：建轻量标签

```bash
git tag v1.0.0
git tag
```

```text
v1.0.0
v1.1.0
```

> 直接在当前提交打 `v1.0.0`。

### 示例 2：建附注标签（发版推荐）

```bash
git tag -a v1.1.0 -m "发布 v1.1.0：登录模块"
```

> `-a` 表示附注标签，`-m` 给说明。不弹编辑器。

### 示例 3：看标签详情

```bash
git show v1.1.0 --stat
```

```text
tag v1.1.0
Tagger: Demo User <demo@example.com>
Date:   Wed Sep 30 23:45:31 2026 +0800

发布 v1.1.0：登录模块

commit d07c6aaab59801f3177a82c15c60d3494caf22b2
Merge: c21e41a 963b990
Author: Demo User <demo@example.com>
Date:   Wed Sep 30 23:45:27 2026 +0800

    merge: 合并 feature/login，解决 app.py 冲突

 app.py  | 2 +-
 auth.py | 2 ++
```

> 先显示标签对象本身（Tagger、Date、说明），再显示它指向的提交。轻量标签 `git show` 只显示提交，没有这一段标签信息。

### 示例 4：给历史提交补打标签

```bash
git tag -a v1.0.1 0b9a085 -m "补打：初始化版本"
```

> 不一定要打在当前 HEAD，可以给任意历史提交补标签。

### 示例 5：推送标签（commit 不会自动带标签）

```bash
git push origin v1.1.0       # 推单个
git push origin --tags       # 推所有本地标签
```

> 打完 tag 必须单独 push，远程才有。

### 示例 6：删除本地与远程标签

```bash
git tag -d v1.0.1                       # 删本地
git push origin --delete v1.0.1         # 删远程
```

> 标签打错提交/版本号时，本地远程都要删。

### 示例 7：按模式列标签

```bash
git tag -l "v1.*"
```

> 只列 v1 开头的标签。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `git tag -a v1.0.0 -m "说明"` | 建附注标签 |
| `git tag` | 列标签 |
| `git show v1.0.0` | 看标签详情 |
| `git push origin v1.0.0` | 推单个标签 |
| `git push origin --tags` | 推所有标签 |
| `git tag -d v1.0.0` | 删本地标签 |
| `git push origin --delete v1.0.0` | 删远程标签 |

## 六、RHEL 系与 Debian 系差异

`tag` 属于 git 本体，**两系用法与输出完全一致**。版本号排序 `version:refname` 在两系都支持。

## 七、新手易错点

1. **打完 tag 忘了 push**：远程没有这个版本。发版后 `git push origin --tags`。
2. **轻量标签 vs 附注标签**：正式发版用 `-a -m`，带说明和打标签人；轻量标签只是个临时记号，别当发版标签用。
3. **标签打错提交**：`git tag -d` 删本地、`git push origin --delete` 删远程，再重新打。
4. **危险：已推送的标签别随便删了重打**：别人已经基于这个 tag 拉代码了。要修正就打个新版本号（v1.0.1），别原地改 v1.0.0。
5. **`git push` 不带 `--tags` 不会推标签**：分支和标签是分开推的，别指望 push 分支顺手推标签。
6. **标签名带 `v` 前缀**是社区约定（`v1.0.0`），不是必须，但统一了好排序。

## 八、相关命令与文档

- 速查页：[Git 命令速查](../git-commands#标签)
- 推送与删除：[push](./push)
- 发版流程与 changelog：[workflow](./workflow)
- CI 里基于 tag 触发发布：[devops-cicd-advanced](../../guide/devops-cicd-advanced)
