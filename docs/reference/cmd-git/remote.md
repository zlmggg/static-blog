# git remote 命令详解：管理远程仓库地址（GitHub/GitLab 的那一头）

> 本文是 [Git 命令速查](../git-commands#远程协作) 中 `git remote` 的从 0 到 1 详解。
> 目标：搞懂 `remote -v`、`add`、`set-url`、`remove`、`show`，知道远程地址存在哪、怎么改。
> 环境依据：Git 2.34.1（本机 `/tmp/demo` 实跑；RHEL/Rocky 用法一致）。

## 一、命令是干什么的

`git remote` 用来**管理「远程仓库」的别名和地址**。远程仓库就是 GitHub/GitLab/公司服务器上那个中央仓库，默认叫 `origin`。`git remote` 本身不下载、不上传，它只是登记「这个项目有哪些远程地址、叫什么名字」。

回顾关系：`git clone` 时自动把远程登记为 `origin`；之后 `git fetch origin`、`git push origin main` 里的 `origin` 就是这里登记的名字。

> 类比：remote 像手机通讯录里的「联系人」。`origin` 是一个联系人，里面存着 GitHub 仓库的网址。`git remote add` 就是存新联系人，`set-url` 就是改号码，`remove` 就是删联系人。

## 二、命令语法

```bash
git remote -v                       # 列出所有远程地址
git remote add <名字> <地址>         # 新增远程
git remote set-url <名字> <新地址>   # 改地址
git remote remove <名字>            # 删除远程
git remote show <名字>              # 看详情
git remote rename <旧> <新>         # 改名
```

- 克隆来的仓库自动有一个叫 `origin` 的远程；
- 一个仓库可以挂多个远程（比如同时挂 GitHub 和公司 GitLab）。

## 三、选项全表（对照 `git remote -h`）

### 1. 查看

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-v`，`--verbose` | 列出远程名 + fetch/push 地址 | 最常用，看配了哪些远程 |
| `show <名字>` | 看某远程的详情（分支、跟踪关系） | 排查 pull/push 指向谁 |
| `get-url <名字>` | 只取地址 | 脚本里用 |

### 2. 增删改

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `add <名字> <地址>` | 新增一个远程 | 关联第二个远程 |
| `rename <旧> <新>` | 改远程名 | 不想要 origin 这名字时 |
| `remove <名字>` | 删除远程 | 仓库搬走了、不要这个远程了 |
| `set-url <名字> <新地址>` | 改 fetch 地址 | 仓库换地址/换协议 |
| `set-url --push <名字> <新地址>` | 只改 push 地址 | fetch 和 push 想指向不同地址 |
| `set-url --add <名字> <地址>` | 给同一远程追加一个 push 地址 | 一次 push 到多个服务器 |

### 3. 其他

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `prune <名字>` | 删掉远程已不存在的远程跟踪分支 | 同事删了分支后清理本地 |
| `update` | 对配置的远程做 fetch | 批量更新 |
| `set-head <名字> -a` | 自动设远程默认分支 | 少见 |

## 四、由浅入深的典型示例

### 示例 1：列出当前仓库的远程地址

```bash
git remote -v
```

```text
origin	/tmp/demo.git (fetch)
origin	/tmp/demo.git (push)
```

> 同一个 `origin` 有两行：`fetch`（下载用）和 `push`（上传用），默认地址相同。克隆来的仓库自动有这条。

### 示例 2：新增一个远程

```bash
git remote add upstream https://github.com/other/demo.git
git remote -v
```

```text
origin	/tmp/demo.git (fetch)
origin	/tmp/demo.git (push)
upstream	https://github.com/other/demo.git (fetch)
upstream	https://github.com/other/demo.git (push)
```

> 典型场景：你 fork 了别人的仓库，`origin` 指向你自己的 fork，`upstream` 指向原作者仓库，方便 `git fetch upstream` 同步上游更新。

### 示例 3：改远程地址（换协议 / 仓库搬家）

```bash
git remote set-url origin git@github.com:you/demo.git
```

> 比如原来用 `https://`，每次 push 要输密码，改成 SSH（`git@github.com:...`）后免密。改完 `git remote -v` 确认。

### 示例 4：看远程详情（跟踪关系一目了然）

```bash
git remote show origin
```

```text
* remote origin
  Fetch URL: /tmp/demo.git
  Push  URL: /tmp/demo.git
  HEAD branch: main
  Remote branches:
    feature/login new (next fetch will store in remotes/origin)
    main          tracked
  Local branch configured for 'git pull':
    main merges with remote main
  Local refs configured for 'git push':
    feature/login pushes to feature/login (up to date)
    main          pushes to main          (up to date)
```

> 它告诉你：远程默认分支是 main；本地 `main` 的 `git pull` 会合并远程 main；本地 `main` 的 `git push` 会推到远程 main。

### 示例 5：删除远程

```bash
git remote remove upstream
```

> 删了之后 `git fetch upstream` 就不能用了。只删远程登记，不动远程服务器上的仓库。

### 示例 6：清理远程已删除的分支（prune）

```bash
git remote prune origin
```

> 同事在远程删了 `feature/login`，你本地的 `remotes/origin/feature/login` 还残留。`prune` 把这些过期的远程跟踪分支清掉。也可以 `git fetch --prune`（见 [fetch-pull](./fetch-pull)）。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `git remote -v` | 看远程地址 |
| `git remote add 名字 地址` | 加远程 |
| `git remote set-url 名字 新地址` | 改地址 |
| `git remote remove 名字` | 删远程 |
| `git remote show origin` | 看跟踪详情 |
| `git remote prune origin` | 清理过期远程分支 |

## 六、RHEL 系与 Debian 系差异

`remote` 属于 git 本体，**两系用法与输出完全一致**。差别只在网络层：

- `https://` 远程：两系都靠系统 curl，走代理配 `git config --global http.proxy`；
- `git@` SSH 远程：两系都靠 `~/.ssh/config` 和 SSH key，与发行版无关。

## 七、新手易错点

1. **`git remote` 不等于 `git fetch`/`git push`**：remote 只是登记地址，不传输数据。改完地址要用 fetch/push 才生效。
2. **`git remote add origin` 报 already exists**：克隆来的仓库已经有 origin 了。想改地址用 `set-url`，不是再 add。
3. **改了地址但 push 还是老地址**：检查 `git remote -v`，确认改对了远程名；有时 push 地址单独配过，用 `set-url --push`。
4. **fork 仓库忘了配 upstream**：同步原作者更新时不知道拉哪个远程。按示例 2 加 `upstream`。
5. **危险：`git remote remove` 不影响远程服务器**，只删本地登记。远程仓库文件还在别人服务器上，别以为 remove 是删远端。
6. **地址里带密码**：`https://user:pass@github.com/...` 会把密码存在 `.git/config` 里，不安全。用 SSH 或凭据助手。

## 八、相关命令与文档

- 速查页：[Git 命令速查](../git-commands#远程协作)
- 怎么从远程拉代码：[fetch-pull](./fetch-pull)
- 怎么往远程推：[push](./push)
- 怎么建仓库/克隆：[init-clone](./init-clone)
- GitOps 里远程仓库即部署源：[automation-gitops](../../guide/automation-gitops)
