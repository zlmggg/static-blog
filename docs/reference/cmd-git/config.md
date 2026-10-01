# git config 命令详解：第一次用 Git 前必须配好的那些项

> 本文是 [Git 命令速查](../git-commands#初始配置) 中 `git config` 的从 0 到 1 详解。
> 目标：把 `git config -h` 里的位置和选项讲清楚，多看几遍后，你在新机器上敲 `git config --global -e` 就知道该改哪一行。
> 环境依据：Git 2.34.1（本机 `/tmp/demo` 实跑；RHEL/Rocky 自带版本用法一致，个别新键见文末差异）。

## 一、命令是干什么的

`git config` 用来**读写 Git 的配置项**：提交时署名是谁、默认主分支叫什么、用哪个编辑器、pull 默认合并还是变基、命令别名怎么起。Git 本身不带任何个人信息，所以第一次装完 Git，第一件事就是跑 `git config --global user.name` 和 `user.email`，否则提交会报错或署上一个莫名其妙的名字。

配置分三个层级，**由近到远、后者覆盖前者**：

- `system`（系统级）：`/etc/gitconfig`，全机器所有用户共享；
- `global`（用户级）：`~/.gitconfig`，当前用户的所有仓库共用（最常用）；
- `local`（仓库级）：`.git/config`，只对当前这个仓库生效（默认就是 local）。

> 类比：`system` 像公司全员默认规范，`global` 像你自己电脑上的个人偏好，`local` 像这个项目单独的特殊约定——冲突时小范围覆盖大范围。

## 二、命令语法

```bash
git config [<配置层级选项>] <动作> <键> [<值>]
git config --list [--show-origin | --show-scope]
git config --global --edit
```

- `<配置层级选项>`：`--global` / `--system` / `--local`，不写默认 `--local`（只影响当前仓库）；
- `<动作>`：`--get` 读、`--add` 增、`--unset` 删、`--list` 列出全部、`--edit` 开编辑器改；
- `<键>`：形如 `user.name`、`init.defaultBranch`、`pull.rebase`，由「段.键」组成；
- 写配置时给 `<值>`，读配置时不给值。

最常用的两条：

```bash
git config --global user.name "你的名字"
git config --global user.email "you@example.com"
```

## 三、选项全表（对照 `git config -h`）

### 1. 选择配置层级（写到哪个文件）

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `--global` | 写到用户级 `~/.gitconfig` | 配个人署名、别名、默认分支（**90% 的情况用它**） |
| `--system` | 写到系统级 `/etc/gitconfig` | 管理员给整台机器设默认值，普通用户很少用 |
| `--local` | 写到当前仓库 `.git/config`（默认） | 某个项目单独的配置，比如这个仓库 pull 用 rebase |
| `--worktree` | 按 worktree 单独配置 | 一个仓库多个工作树时 |
| `-f <文件>`，`--file <文件>` | 读写指定文件而不是默认配置 | 脚本里生成临时配置 |
| `--blob <对象>` | 从某个 git 对象里读配置 | 排查历史配置，极少用 |

### 2. 读配置

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `--get <键>` | 读某个键的值 | `git config user.name`（读不到会以非 0 退出） |
| `--get-all <键>` | 读某键的全部值（如多邮箱） | `git config --get-all user.email` |
| `--get-regexp <正则>` | 按正则批量读 | `git config --get-regexp alias` 看所有别名 |
| `-l`，`--list` | 列出所有配置 | 排查「我这台机器到底配了啥」（最常用） |
| `--show-origin` | 列出每项来自哪个文件 | 区分某条配置是 system/global/local 哪来的 |
| `--show-scope` | 列出每项属于哪个层级 | 同上，输出更紧凑 |
| `--name-only` | 只输出键名 | 脚本里遍历键 |
| `--default <值>` | 键不存在时用默认值代替 | 脚本判断 `git config --default main init.defaultBranch` |

### 3. 写 / 改 / 删配置

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `--add <键> <值>` | 新增一个值（可同键多值） | 加多个 `include.path` |
| `--replace-all <键> <值>` | 替换某键所有值 | 改全局邮箱 |
| `--unset <键>` | 删除一个值 | 删错配的别名 |
| `--unset-all <键>` | 删除某键全部值 | 清空某段配置 |
| `--rename-section <旧> <新>` | 重命名一段 | 极少用 |
| `--remove-section <段>` | 删除整段 | 删整个 `alias` 段重来 |
| `-e`，`--edit` | 用编辑器打开配置文件改 | 大规模手改（`git config --global -e`） |

### 4. 值的类型与其他

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `--bool` / `--int` / `--path` | 把值当布尔 / 整数 / 路径解析 | 脚本里校验类型 |
| `-z`，`--null` | 用 NUL 分隔输出 | 给脚本处理 |
| `--includes` | 展开 `include` 指令后再读 | 看最终生效值 |

## 四、由浅入深的典型示例

### 示例 1：第一次配置署名（必做）

```bash
git config --global user.name "张三"
git config --global user.email "zhangsan@example.com"
```

> 这两条没有任何输出（写成功就是安静的）。之后所有 `--global` 范围内的提交都会署上「张三 <zhangsan@example.com>」。

### 示例 2：读回来看配没配上

```bash
git config --global user.name
git config --global user.email
```

```text
张三
zhangsan@example.com
```

### 示例 3：列出当前仓库所有生效配置，并看来自哪个层级

```bash
git config --list --show-scope
```

```text
local	core.repositoryformatversion=0
local	core.filemode=true
local	core.bare=false
local	core.logallrefupdates=true
local	user.name=Demo User
local	user.email=demo@example.com
local	remote.origin.url=/tmp/demo.git
local	remote.origin.fetch=+refs/heads/*:refs/remotes/origin/*
local	branch.main.remote=origin
local	branch.main.merge=refs/heads/main
```

> 第一列是层级（`local`），后面是 `键=值`。这个仓库因为是演示时临时 `git config user.name` 写在 local 里的，所以只在 `local` 段出现。

### 示例 4：设置默认主分支名（避免老机器默认 master）

```bash
git config --global init.defaultBranch main
```

> 老版本 Git（<2.28）`git init` 默认建 `master`。设了这一项后，以后 `git init` 默认就是 `main`。配合 GitHub/GitLab 现在的默认分支名，能少踩一次「push 上去分支名对不上」的坑。

### 示例 5：设置默认编辑器与 pull 策略

```bash
git config --global core.editor "vim"
git config --global pull.rebase true
```

> `core.editor` 决定提交信息、rebase 交互时弹哪个编辑器；`pull.rebase true` 让 `git pull` 默认走「拉下来后变基」而不是「拉下来后做合并提交」，团队分支历史更干净。

### 示例 6：起别名（把长命令变短）

```bash
git config --global alias.st status
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.lg "log --oneline --graph --all --decorate"
```

配完之后：

```bash
git st
git lg
```

```text
On branch main
Your branch is up to date with 'origin/main'.

nothing to commit, working tree clean
```

> `git st` 等价于 `git status`，`git lg` 等价于那一长串 log。别名里带参数（如 `log --oneline`）要加引号。

### 示例 7：直接开编辑器手改全局配置

```bash
git config --global --edit
```

> 会打开 `~/.gitconfig`，长这样：
>
> ```ini
> [user]
> 	name = 张三
> 	email = zhangsan@example.com
> [init]
> 	defaultBranch = main
> [pull]
> 	rebase = true
> [alias]
> 	st = status
> 	lg = log --oneline --graph --all --decorate
> ```
>
> 直接改文本保存即可，效果和命令行一模一样。

### 示例 8：删掉一条配错的配置

```bash
git config --global --unset alias.st
```

> 删别名、删错配的键都用 `--unset`；想删整段就 `--remove-section alias`。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `git config --global user.name "名字"` | 配署名 |
| `git config --global user.email "邮箱"` | 配邮箱 |
| `git config --list` | 看本机所有配置 |
| `git config --list --show-origin` | 看每条配置来自哪个文件 |
| `git config --global --edit` | 手改全局配置 |
| `git config --global init.defaultBranch main` | 默认主分支改 main |
| `git config --global pull.rebase true` | pull 默认变基 |
| `git config --global alias.短名 原命令` | 起别名 |
| `git config --get-regexp alias` | 列出所有别名 |

## 六、RHEL 系与 Debian 系差异

`git config` 属于 git 本体，**RHEL/CentOS/Rocky 与 Ubuntu/Debian 用法完全一致**，上述层级、动作、选项通用。细微差别：

- 包名：Ubuntu 是 `git`，RHEL 系是 `git`（RHEL8+ 通过 AppStream 安装）；
- 系统级配置路径都是 `/etc/gitconfig`；
- 老版本 Git（<2.28）没有 `init.defaultBranch` 这个键，想改默认分支只能 init 时手动 `-b main` 或事后 `git branch -m`；本机 2.34.1 已支持。

## 七、新手易错点

1. **忘了配 user.name / user.email 就提交**：Git 会用系统用户名拼一个邮箱，提交记录在 GitHub 上不会算进你的贡献绿格子。新机器第一件事就是配这两项。
2. **`--global` 漏写，配到了 local**：在某个仓库里 `git config user.email a@b.com` 不配 `--global`，这条只写进了 `.git/config`，换个仓库又没了。记住：个人偏好一律加 `--global`。
3. **同名键有多个值分不清**：用 `git config --list --show-origin` 看每条来自哪个文件，别瞎猜。
4. **改了 `~/.gitconfig` 不知道在哪**：`git config --global --edit` 最稳，别自己到处找文件。
5. **别名里带空格忘了加引号**：`git config alias.lg log --graph` 只会把 `log` 当别名，后面的 `--graph` 被 shell 吞掉，必须写成 `"log --graph"`。
6. **危险：`git config --global --unset-all` 没接键**会删一堆东西**。删配置前先 `--get-regexp` 看清楚要删哪个键。

## 八、相关命令与文档

- 速查页：[Git 命令速查](../git-commands#初始配置)
- 配完怎么建仓库：`git init`（详解见 [init-clone](./init-clone)）
- 提交署名相关：`git commit`（详解见 [commit](./commit)）
- 团队里怎么管 pull 策略与分支：[团队分支工作流](./workflow)
- GitOps 视角看配置即代码：[automation-gitops](../../guide/automation-gitops)
