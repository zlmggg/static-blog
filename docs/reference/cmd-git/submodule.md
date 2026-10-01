# git submodule 命令详解：在一个仓库里嵌套引用另一个仓库

> 本文是 [Git 命令速查](../git-commands#子模块（submodule）) 中 `git submodule` 的从 0 到 1 详解。
> 目标：搞懂子模块是什么、怎么加、克隆后怎么初始化、`update --init --recursive`、`--remote`、`deinit`。
> 环境依据：Git 2.34.1（本机 `/tmp/mainrepo` 实跑；RHEL/Rocky 用法一致）。

## 一、命令是干什么的

`git submodule`（子模块）让你在一个 Git 仓库里**固定引用另一个独立 Git 仓库的某个提交**。主仓库不存子模块的代码，只存「子模块的地址 + 应该停在哪个提交」。

典型场景：主项目依赖一个独立维护的 SDK / 公共库。你不想把库的代码复制进来（会丢失它自己的历史和版本管理），就用 submodule 把它「钉」在某个确定提交上。

> 类比：主仓库像一本书，submodule 像书里夹的一张「引用卡」，写着「第三章那本参考书是某某出版社、第 2024 版第 3 次印刷」。书本身不含参考书全文，只记录「该用哪一版」。

## 二、命令语法

```bash
git submodule add <仓库地址> <路径>        # 加子模块
git clone --recurse-submodules <主仓库>    # 克隆时连子模块一起拉
git submodule update --init --recursive     # 已克隆后补拉子模块
git submodule update --remote             # 更新到子模块远程最新
git submodule deinit <路径>               # 取消初始化
```

## 三、选项全表（对照 `git submodule -h`）

### 1. 添加

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `add <地址> <路径>` | 添加子模块 | 引入外部库 |
| `-b <分支>` | 跟踪子模块某个分支 | 想固定跟某分支 |
| `--name <名>` | 给子模块起名 | 路径名不规范时 |

### 2. 初始化与更新

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `init` | 把 `.gitmodules` 里的地址写入 `.git/config` | 克隆后第一步 |
| `update` | 按主仓库记录的提交检出子模块 | 让子模块回到主仓库钉的版本 |
| `--init` | update 时自动 init | 常用组合 |
| `--recursive` | 递归处理嵌套子模块 | 子模块里还有子模块 |
| `--remote` | 更新到子模块远程跟踪分支最新 | 想跟最新版时 |
| `--merge` / `--rebase` | 更新时用 merge/rebase | 子模块本地有改动时 |

### 3. 查看与卸载

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `status` | 显示子模块状态（钉在哪个提交） | 看当前版本 |
| `summary` | 显示子模块相对上次的提交摘要 | 升级时看变了啥 |
| `deinit <路径>` | 取消初始化（把子模块目录清空） | 暂时不用了 |
| `set-url <路径> <新地址>` | 改子模块地址 | 库换仓库了 |
| `foreach <命令>` | 在每个子模块里跑命令 | 批量操作 |
| `sync` | 把 `.gitmodules` 地址同步到 config | 地址改了后 |

## 四、由浅入深的典型示例

### 示例 1：添加一个子模块

```bash
git submodule add /tmp/librepo third_party/lib
```

```text
Cloning into '/tmp/mainrepo/third_party/lib'...
done.
```

会做三件事：把 `librepo` 克隆到 `third_party/lib`；生成 `.gitmodules` 文件；在主仓库暂存区登记。看状态：

```bash
git status -s
cat .gitmodules
```

```text
A  .gitmodules
A  third_party/lib
[submodule "third_party/lib"]
	path = third_party/lib
	url = /tmp/librepo
```

> 注意：主仓库里 `third_party/lib` 显示为一个**特殊条目**（gitlink），不是一堆文件——它只记录该子模块停在哪个提交。提交这个改动后，别人克隆主仓库才知道有这个子模块。

### 示例 2：克隆主仓库后，子模块目录是空的

```bash
git clone /tmp/mainrepo mainrepo2
ls -A mainrepo2/third_party/lib
```

```text
（空）
```

> **这是新手最大的坑**：普通 `git clone` 不会拉子模块，目录是空的。

### 示例 3：补拉子模块（标准三步合一）

```bash
cd mainrepo2
git submodule update --init --recursive
```

```text
Cloning into '/tmp/mainrepo2/third_party/lib'...
done.
Submodule path 'third_party/lib': checked out 'e24a9eee6a477ea50aa46a57116456c028e1364b'
```

> 之后 `third_party/lib` 里就有代码了，并且停在主仓库记录的那个提交。

### 示例 4：克隆时一步到位

```bash
git clone --recurse-submodules /tmp/mainrepo mainrepo3
```

> 省掉示例 3 那一步。也可以用旧别名 `--recursive`。

### 示例 5：更新子模块到它远程的最新提交

```bash
git submodule update --remote third_party/lib
```

> 进入子模块目录拉最新。注意：这会让子模块停在一个新提交，**主仓库需要重新提交一次**（记录这个新的钉版），否则别人克隆还是老版本。

### 示例 6：在子模块里升级并提交（标准流程）

```bash
cd third_party/lib
git switch main
git pull                       # 在子模块里更新代码
cd ../..
git add third_party/lib
git commit -m "chore: 升级 lib 子模块到最新"
```

> 子模块本身是独立仓库，要先在它里面提交/拉取，再回到主仓库提交「钉版变了」。

### 示例 7：卸载子模块

```bash
git submodule deinit third_party/lib
git rm third_party/lib
```

> `deinit` 清空本地子模块目录，`git rm` 从主仓库彻底移除登记。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `git submodule add 地址 路径` | 加子模块 |
| `git clone --recurse-submodules 地址` | 克隆连子模块 |
| `git submodule update --init --recursive` | 补拉子模块 |
| `git submodule update --remote` | 更新到子模块最新 |
| `git submodule status` | 看钉在哪个提交 |
| `git submodule deinit 路径` | 卸载 |

## 六、RHEL 系与 Debian 系差异

`submodule` 属于 git 本体，**两系用法与输出完全一致**。注意新版 Git 默认禁止 `file://` 本地协议克隆子模块（本机演示中需要 `git config --global protocol.file.allow always`），这是 Git 2.38+ 的安全行为，与发行版无关。

## 七、新手易错点

1. **克隆主仓库后子模块目录是空的**：忘了 `--recurse-submodules` 或 `git submodule update --init --recursive`。这是最常见的坑。
2. **改了子模块代码但主仓库没提交钉版**：别人拉主仓库后，子模块还是老提交。每次子模块升级，主仓库都要 `git add 子模块路径 && git commit`。
3. **子模块处于「detached HEAD」**：update 后子模块停在固定提交、不在任何分支上。想在子模块里开发，先 `cd` 进去 `git switch 分支`。
4. **危险：`git submodule deinit` 会清空子模块本地目录**，里面未提交的改动会丢。先在子模块里 commit/stash。
5. **把子模块当普通目录 `rm -rf` 删了**：没走 `git submodule deinit` + `git rm`，残留配置会乱。按示例 7 流程删。
6. **`.gitmodules` 没提交进主仓库**：别人克隆后不知道子模块地址。add 后记得连同 `.gitmodules` 一起 commit。
7. **子模块地址是本地路径**：换个人就克隆失败。子模块 URL 要用远程可访问地址。

## 八、相关命令与文档

- 速查页：[Git 命令速查](../git-commands#子模块（submodule）)
- 克隆与远程：[init-clone](./init-clone)、[remote](./remote)
- 替代方案对比：大型项目常改用包管理器（submodule 维护成本高）
- GitOps 里的依赖钉版：[automation-gitops](../../guide/automation-gitops)
