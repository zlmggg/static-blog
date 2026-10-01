# history 与 alias 命令详解：翻历史命令和给命令起别名

> 本文是 [Linux 命令速查](../linux-commands#Shell 基础) 中 `history`、`alias` 的从 0 到 1 详解。
> 目标：把 `history -c/-d/-a/-w`、`alias`、以及 `!!`/`!n` 历史展开讲清楚，多看几遍后，你在服务器上敲 `history | grep` 就知道怎么找回之前的命令。
> 环境依据：`history`、`alias` 都是 **bash 内建命令**（随 bash 提供，没有独立 `--help`，用 `help history`/`help alias` 查看）。Ubuntu 22.04 默认 bash，RHEL 同。

## 一、命令是干什么的

- **`history`**：显示和管理**当前 shell 敲过的命令历史**。你之前敲过什么、哪条命令反复用，都能翻出来，还能直接按编号重跑。
- **`alias`**：给长命令起一个**短别名**。比如把 `ls -l --color=auto` 起名 `ll`，以后敲 `ll` 就等于敲那一长串。

> 类比：`history` 像浏览器的"浏览记录"，能翻回去重新打开；`alias` 像把常用网址存成书签，一键直达。

两者都是 bash 内建，只对当前 shell 生效；想永久生效要写进 `~/.bashrc`。

## 二、命令语法

```bash
# history（bash 内建）
history [-c] [-d 偏移] [n]
history [-anrw] [文件名]
history -ps 参数...

# alias（bash 内建）
alias [-p] [名字[=值]...]
```

- `history` 不带参数：列出全部历史（带行号）；
- `alias` 不带参数：列出当前所有别名；
- `alias 名字='值'`：定义一个别名；
- `unalias 名字`：删除别名。

## 三、选项全表（对照 `help history` / `help alias`）

### 1. history 常用选项

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| （数字 n） | 只列出最近 n 条 | `history 10` |
| `-c` | **清空**整个历史列表 | 不想要历史时（谨慎） |
| `-d 偏移` | 删除指定编号的那条历史 | 删掉输错的命令 |
| `-a` | 把本次会话新增的历史**追加**到历史文件 | 手动保存 |
| `-w` | 把当前历史**写入**历史文件（覆盖） | 强制保存 |
| `-r` | 把历史文件读进当前列表 | 加载历史 |
| `-n` | 读取历史文件里还没读过的新行 | 同步其他会话的历史 |
| `-p` | 对参数做历史展开但**不存储** | 测试展开结果 |
| `-s` | 把参数作为一条历史追加 | 伪造一条历史 |

历史展开快捷键（在命令行直接用，不是 `history` 的选项）：

| 写法 | 含义 |
|---|---|
| `!!` | 上一条命令（常配合 `sudo !!`） |
| `!n` | 历史里第 n 条命令 |
| `!字串` | 最近一条以"字串"开头的命令 |
| `!$` | 上一条命令的最后一个参数 |
| `↑`/`↓` | 上下翻历史 |
| `Ctrl+R` | **反向搜索**历史（最常用） |

### 2. alias 常用选项

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| （无参数） | 列出当前所有别名 | 看有哪些别名 |
| `-p` | 以可复用格式列出所有别名 | 脚本里 |
| `名字='值'` | 定义别名 | 如 `alias ll='ls -lh'` |
| `unalias 名字` | 删除别名 | 临时取消 |

## 四、由浅入深的典型示例

### 示例 1：列出最近的历史

```bash
history
```

> 输出每行 `编号  命令`。配合 `grep` 找命令：`history | grep ssh`。

### 示例 2：只看最近 10 条

```bash
history 10
```

> 数字作为参数，只列出最近 10 条，避免刷屏。

### 示例 3：用 `Ctrl+R` 反向搜索（最高效）

> 在命令行按 `Ctrl+R`，输入关键词（如 `ssh`），bash 会自动在历史里向后匹配，每按一次 `Ctrl+R` 跳到更早一条；找到后按回车执行，按 `→` 先编辑再执行。

### 示例 4：重复上一条命令

```bash
!!
# 最常见用法：上一条命令忘了加 sudo
sudo !!
```

> `sudo !!` = 以 root 身份重跑上一条命令，是运维高频操作。

### 示例 5：按编号重跑

```bash
!1023
```

> 假设 `history` 显示第 1023 条是 `tar -czf backup.tar.gz /data`，敲 `!1023` 就重跑它。

### 示例 6：把上一条命令的最后一个参数拿来用

```bash
# 假设上一条是 cd /etc/nginx
ls -l !$
# 等价于 ls -l /etc/nginx
```

> `!$` 取上一条命令的最后一个参数，省得重新敲长路径。

### 示例 7：删除某条历史（如含密码）

```bash
history -d 204
```

> 假设第 204 条不小心敲了 `mysql -p密码`，用 `-d 204` 删掉它，避免留在历史文件里。

### 示例 8：定义别名

```bash
alias ll='ls -lh --color=auto'
alias gs='git status'
alias ..='cd ..'
```

> 定义后当前 shell 里敲 `ll` 就等于 `ls -lh --color=auto`。想永久生效，把这些行写进 `~/.bashrc`。

### 示例 9：列出和删除别名

```bash
alias            # 列出所有
alias ll         # 看 ll 等于什么
unalias gs       # 删除 gs 这个别名
```

## 五、高频组合速记

| 命令/写法 | 用途 |
|---|---|
| `history \| grep 关键词` | 找历史命令 |
| `history 10` | 最近 10 条 |
| `Ctrl+R` | 反向搜索历史（**最常用**） |
| `sudo !!` | 上一条命令加 sudo 重跑 |
| `!n` | 按编号重跑 |
| `!$` | 上一条命令的最后参数 |
| `alias` | 看所有别名 |
| `alias 名字='命令'` | 定义别名 |
| `~/.bashrc` | 永久保存别名 |

## 六、RHEL 系与 Debian 系差异

- 两者都是 bash 内建，**两系用法一致**。
- 默认别名不同：Ubuntu 默认给 `ls`、`grep` 加 `--color=auto`；RHEL 也类似。
- 历史文件：都是 `~/.bash_history`；历史条数由 `HISTSIZE`（内存中条数）和 `HISTFILESIZE`（文件条数）控制。
- RHEL 7+ 默认 shell 仍是 bash；Fedora 新版默认可能换成 zsh，那两个命令在 zsh 里语法略不同。

## 七、新手易错点

1. **`alias` 只对当前 shell 生效**：新开终端就没了；要永久用写进 `~/.bashrc` 并 `source ~/.bashrc`。
2. **脚本里别依赖别名**：非交互式 shell（脚本）默认不加载别名，脚本里写完整命令。
3. **`history -c` 只清当前内存列表**：想彻底清掉磁盘上的 `~/.bash_history`，还要 `history -w` 或直接删文件。
4. **把密码敲进命令行**：会留在 history 里，事后用 `history -d 编号` 删，或下次用 `read -s` 输入密码。
5. **`!!`/`!n` 用错编号会执行错命令**：不确定时先 `history` 看一眼，别盲跑。
6. **别名和原命令冲突**：如果 alias 名字和系统命令同名（如 `alias ls='...'`），想绕过别名用 `\ls` 或 `command ls`。

## 八、相关命令与文档

- 速查页：[Linux 命令速查](../linux-commands#Shell 基础)
- 环境变量/export：`export`（详解见 [echo-env-export](./echo-env-export)）
- Shell 进阶：见 [Linux Shell 专题](../../guide/linux-shell)
