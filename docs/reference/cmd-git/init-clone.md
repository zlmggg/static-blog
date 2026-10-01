# git init 与 git clone 命令详解：从无到有建仓库、把远程仓库拉到本地

> 本文是 [Git 命令速查](../git-commands#创建与克隆仓库) 中 `git init` 与 `git clone` 的从 0 到 1 详解。本篇一次讲清「在本地新建仓库」和「把已有远程仓库拉下来」这两件事。
> 目标：把 `git init -h`、`git clone -h` 里的选项讲清楚，多看几遍后，新机器上要拉代码、要起新项目就知道敲哪条。
> 环境依据：Git 2.34.1（本机 `/tmp` 实跑；RHEL/Rocky 自带版本用法一致）。

## 一、命令是干什么的

- `git init`：在一个**空目录**（或已有目录）里「种」出一个 Git 仓库——本质就是建一个 `.git` 隐藏目录，之后这个目录里的文件就能被 Git 跟踪。新项目从零开始时用它。
- `git clone`：把一个**已经存在的远程仓库**（GitHub/GitLab/同事电脑上的路径）完整复制到本地，连历史、分支、标签一起拉下来。接手别人项目时用它。

> 类比：`git init` 像在白纸上盖个章「这本本子开始记账了」；`git clone` 像把别人已经写了一半的账本复印一本给你，你在复印件上接着写，最后还能对回去。

## 二、命令语法

```bash
git init [-b <初始分支名>] [--bare] [<目录>]
git clone [-b <分支>] [--depth <深度>] [--recurse-submodules] <仓库地址> [<本地目录名>]
```

- `git init`：`<目录>` 不写就初始化**当前目录**；`-b` 指定初始分支名（不写用 `init.defaultBranch` 或默认 `master`）。
- `git clone`：`<仓库地址>` 可以是本地路径、`file://`、`https://`、`git@...`；`<本地目录名>` 不写就用远程仓库名做目录名。

## 三、选项全表（对照 `git init -h` 与 `git clone -h`）

### 1. git init 的选项

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-b <名字>`，`--initial-branch <名字>` | 指定初始分支名 | `git init -b main`，避免老机器默认建 `master`（最常用） |
| `--bare` | 建**裸仓库**（没有工作区，只有 `.git` 里的内容） | 做团队中央远程仓库时（见 remote 篇） |
| `--template=<目录>` | 用指定目录做模板 | 定制 hooks、忽略规则，极少用 |
| `--shared[=<权限>]` | 设为多用户共享仓库 | 老的 N 盘共享仓库，现在基本不用 |
| `-q`，`--quiet` | 安静模式 | 脚本里用 |
| `--separate-git-dir=<gitdir>` | 把 `.git` 单独放别处 | 特殊部署场景 |

### 2. git clone 的选项——选分支与浅克隆

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-b <分支>`，`--branch <分支>` | 只切到指定分支 | 远程默认分支不是你要的那个时 |
| `--depth <n>` | **浅克隆**，只拉最近 n 次提交 | 仓库巨大、只要最新代码时（下载快、省空间） |
| `--single-branch` | 只克隆一个分支 | 配合 `--depth` 进一步省流量 |
| `--no-tags` | 不克隆标签 | 只要代码不要历史标签时 |
| `--shallow-since <时间>` | 浅克隆只拉某时间之后 | 大仓库按时间裁剪历史 |

### 3. git clone 的选项——子模块与远程名

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `--recurse-submodules` | 克隆后自动初始化并拉取子模块 | 项目里用了 submodule 时（见 [submodule](./submodule)） |
| `--recursive` | 同上（旧别名） | 同上 |
| `-j <n>` | 并行拉子模块个数 | 子模块很多时加速 |
| `-o <名字>`，`--origin <名字>` | 把远程默认名从 `origin` 改成别的 | 一个仓库要挂多个远程时 |
| `--bare` | 克隆成裸仓库 | 做镜像 |
| `--mirror` | 镜像克隆（含所有引用、标签） | 做仓库镜像迁移 |
| `-n`，`--no-checkout` | 克隆后不检出工作区 | 只要 `.git` 对象库时 |
| `-q` / `-v` | 安静 / 详细输出 | 脚本或排查时 |

## 四、由浅入深的典型示例

### 示例 1：在当前目录初始化一个新仓库（最常用）

```bash
cd /tmp && mkdir myproj && cd myproj && git init -b main
```

```text
Initialized empty Git repository in /tmp/myproj/.git/
```

> 跑完后目录里多了一个隐藏的 `.git/`。之后 `git add`、`git commit` 才有效。`-b main` 指定初始分支直接叫 `main`。

### 示例 2：初始化时顺便指定目录

```bash
git init -b main /tmp/myproj2
```

```text
Initialized empty Git repository in /tmp/myproj2/.git/
```

> 不用先 cd 进去，直接给目录名，Git 会帮你建好目录再初始化。

### 示例 3：克隆一个远程仓库（最常用）

```bash
git clone /tmp/demo.git worker
```

```text
Cloning into 'worker'...
done.
```

> 这是把本地裸仓库 `/tmp/demo.git` 克隆到 `worker/` 目录。换成 `https://github.com/xxx/xxx.git` 或 `git@github.com:xxx/xxx.git` 写法完全一样。克隆完自动 `cd` 进去切到默认分支，并把远程命名为 `origin`。

### 示例 4：克隆时指定放到自定义目录名

```bash
git clone /tmp/demo.git my-worker
```

> 不写第三个参数时，目录名默认取远程仓库名（`demo`）；写了就用你给的名字。

### 示例 5：浅克隆——只拉最近 1 次提交（大仓库救星）

```bash
git clone --depth 1 /tmp/demo.git shallow-demo
```

```text
Cloning into 'shallow-demo'...
done.
```

> `--depth 1` 只拉最新一次提交，不拉完整历史。下载小、速度快。代价是 `git log` 看不到以前的提交，以后想补全历史用 `git fetch --unshallow`。

### 示例 6：克隆指定分支

```bash
git clone -b feature/login /tmp/demo.git login-work
```

> 默认克隆会切到远程 HEAD 所在分支（通常是 `main`）。加 `-b feature/login` 直接切到你要的分支。

### 示例 7：克隆并初始化子模块

```bash
git clone --recurse-submodules /tmp/demo.git with-sub
```

> 如果项目里用了 `git submodule`，不加这个选项克隆下来后子模块目录是空的，要手动 `git submodule update --init --recursive`。加了 `--recurse-submodules` 一步到位。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `git init -b main` | 当前目录建仓库，初始分支 main |
| `git clone <url>` | 标准克隆 |
| `git clone <url> <目录名>` | 克隆到自定义目录 |
| `git clone --depth 1 <url>` | 浅克隆，只要最新代码 |
| `git clone -b <分支> <url>` | 只克隆指定分支 |
| `git clone --recurse-submodules <url>` | 连子模块一起克隆 |
| `git clone --bare <url>` | 克隆成裸仓库（做镜像） |

## 六、RHEL 系与 Debian 系差异

`init` / `clone` 属于 git 本体，**两系用法一致**。细微差别：

- 老版本 Git（<2.28）`git init` 不支持 `-b`，默认建 `master`；本机 2.34.1 已支持。老机器要么先 `git init` 再 `git branch -m main`，要么配 `git config --global init.defaultBranch main`。
- 克隆 `https://` 仓库时，两系都用系统自带的 curl；走代理时统一配 `git config --global http.proxy`，与发行版无关。

## 七、新手易错点

1. **在已经有 `.git` 的目录里又 `git init`**：不会报错，只是把现有仓库重新初始化一遍，不会丢数据，但也没意义。
2. **`git init` 忘了 `-b main`，老机器建出 `master`**：push 到 GitHub 时远程默认是 `main`，会出现「本地 master、远程 main」对不上。提前配 `init.defaultBranch`。
3. **`git clone` 一个大仓库不拉浅克隆，等半小时**：公司内部历史几十年的 monorepo，先用 `--depth 1` 拉下来再说。
4. **克隆下来发现子模块目录是空的**：忘了 `--recurse-submodules`，补 `git submodule update --init --recursive`。
5. **危险：`git clone` 会把远程整个历史拉到本地**，里面如果有 `.env`、密钥，就一起拉下来了。克隆前不要把敏感文件提交进仓库。
6. **`--bare` 仓库不能直接改代码**：它没有工作区，只是个「中央存档点」，别进去手动改文件。

## 八、相关命令与文档

- 速查页：[Git 命令速查](../git-commands#创建与克隆仓库)
- 建完仓库怎么提交：`git add` / `git commit`（详解见 [add](./add)、[commit](./commit)）
- 配远程地址：`git remote`（详解见 [remote](./remote)）
- 子模块细节：[submodule](./submodule)
- CI/CD 里怎么 clone：[devops-cicd-advanced](../../guide/devops-cicd-advanced)
