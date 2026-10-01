# sudo 与 su 命令详解：临时提权和切换用户

> 本文是 [Linux 命令速查](../linux-commands#用户与权限) 中 `sudo` 与 `su` 的从 0 到 1 详解，本篇一次讲清「临时用 root 跑一条命令」和「彻底切换成另一个用户」。
> 目标：把 `sudo -h` / `su --help` 里的每个选项讲清楚，多看几遍后，你在服务器上敲 `sudo -h` 就知道该用哪个选项。
> 环境依据：Ubuntu 22.04 自带 sudo 1.9.9（`sudo` 包）；`su` 属 util-linux 2.37.2。两系命令用法一致，差异在文末。

## 一、命令是干什么的

日常登录服务器应该用**普通用户**（防止手滑删库），但装软件、改 `/etc`、看 root 进程又需要 root 权限。这两个命令就是解决「我现在是普通用户，怎么临时获得高权限」：

- `sudo`：**以别人身份（默认 root）跑一条命令**，跑完就回到自己。不用知道 root 密码，只要你在 sudoers 里被授权。
- `su`：**Switch User，切换成另一个用户**，开一个新的 shell，直到你输入 `exit` 才切回来。需要知道目标用户的密码。

> 类比：`sudo` 像「临时借管理员身份签一个字」，签完还是你；`su -` 像「直接坐进管理员的办公室」，在里面做什么都是管理员身份，直到出门（exit）。
>
> 一句话区别：**临时跑一条命令用 `sudo`；要长期在别人身份下干活用 `su -`**。

## 二、命令语法

```bash
sudo [选项] [命令]
su [选项] [-] [用户 [参数...]]
```

- `sudo`：后面跟要以高权限执行的命令；不写命令只写 `sudo -l` 是看自己有哪些权限。
- `su`：后面跟要切到的用户名；不给用户默认切 root。`-`（即 `-l`）表示「完整登录」，这是最常用写法。

## 三、选项全表（对照 `sudo -h` / `su --help`）

### 1. sudo：以别的身份跑命令

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-u 用户`，`--user=用户` | 以**指定用户**身份跑（默认 root） | 如 `sudo -u nginx nginx -t` |
| `-i`，`--login` | 开一个**登录式** root shell（读 root 的环境配置） | 想要干净的 root 登录环境 |
| `-s`，`--shell` | 开一个 root shell（不切换 HOME） | 想要 root shell 但保留当前目录 |
| `-l`，`--list` | 列出**我有哪些 sudo 权限** | 登录后确认自己能干什么 |
| `-v`，`--validate` | 提前验证/续期 sudo 时间戳 | 避免中途再输密码 |
| `-k`，`--reset-timestamp` | 让 sudo 时间戳失效，下次重新问密码 | 安全/测试 |
| `-n`，`--non-interactive` | **不交互**，不许弹密码提示 | 脚本里用（失败就直接报错，不卡住） |
| `-S`，`--stdin` | 从**标准输入**读密码 | 脚本里管道喂密码 |
| `-b`，`--background` | 放后台运行 | 跑长时间任务 |
| `-E`，`--preserve-env` | 保留当前环境变量 | 需要带上自己的 PATH 等 |
| `-H`，`--set-home` | 把 HOME 设成目标用户的家目录 | 配合 `-s` 用 |
| `-e`，`--edit` | **编辑文件**而不是跑命令（= `sudoedit`） | `sudo -e /etc/hosts` |
| `-D 目录`，`--chdir=目录` | 跑之前先切到目录 | `sudo -D /var/log tail ...` |
| `-g 组`，`--group=组` | 以指定组身份跑 | 较少用 |
| `--` | 后面全当参数，不再解析选项 | 命令本身以 `-` 开头时 |

### 2. su：切换用户

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-`，`-l`，`--login` | **登录式切换**（重新读目标用户的环境、切到他家目录） | 最常用：`su -` 或 `su - root` |
| `-c 命令`，`--command 命令` | 以目标身份跑**一条命令**后返回 | `su -c 'systemctl restart nginx'` |
| `-s shell`，`--shell shell` | 指定用哪个 shell | 默认用目标用户的登录 shell |
| `-m`，`-p`，`--preserve-environment` | **保留**当前环境变量（不重置） | 想带自己的环境 |
| `-g 组` | 指定主组 | 较少用 |
| `-G 组` | 指定附加组 | 较少用 |

> 关键差别：`su`（没横杠）只切身份、**不**切环境和目录；`su -`（有横杠）才是完整登录。生产里几乎永远用 `su -`。

## 四、由浅入深的典型示例

### 示例 1：临时用 root 跑一条命令

```bash
sudo whoami
```

```text
root
```

> 这是 sudo 最基本的用法：在原命令前加 `sudo`，这条命令就以 root 身份执行。执行完你还是普通用户。

### 示例 2：看自己的 sudo 权限

```bash
sudo -l
```

```text
User user may run the following commands on this host:
    (ALL) NOPASSWD: ALL
```

> 这台机器上 `user` 被授权可以无密码跑任何命令。线上很多机器只授权你跑某几条命令（比如只能 `sudo systemctl restart nginx`），`sudo -l` 先看清楚。

### 示例 3：以指定用户身份跑（不一定是 root）

```bash
sudo -u user whoami
```

```text
user
```

> `-u` 指定身份。比如要以 nginx 用户调试：`sudo -u nginx nginx -t`。

### 示例 4：脚本里非交互使用 sudo

```bash
sudo -n true && echo "免密可用"
```

```text
免密可用
```

> `-n` 表示「不要问我密码」。脚本里如果需要 sudo 但又不想卡在密码提示，就用 `-n`，失败会直接非零退出，方便判断。

### 示例 5：用 sudo 编辑 root 文件（推荐）

```bash
sudo -e /etc/hosts
# 等价于
sudoedit /etc/hosts
```

> `sudo -e` 先把文件复制成临时副本用你自己的编辑器打开，保存后再用 root 权限写回。比 `sudo vi /etc/hosts` 安全——编辑器里跑的还是你的普通身份，不会整个 vi 都是 root。

### 示例 6：完整切换到 root（登录式）

```bash
su -
# 或
su - root
```

> 输入 root 密码后，你就进到 root 的家目录、加载了 root 的环境，提示符变成 `#`。干完活用 `exit` 切回普通用户。注意：这需要知道 root 密码，而现代服务器一般不设 root 密码，所以更多用 `sudo -i`。

### 示例 7：su 跑一条命令就回来

```bash
su -c 'whoami' root
```

```text
Password: su: Authentication failure
```

> `-c` 后面跟一条命令，以 root 身份跑完立刻返回原身份。这里因为不知道 root 密码所以认证失败——这正说明 `su` 要 root 密码，而 `sudo` 只要你在 sudoers 里。

### 示例 8：开一个 root 交互 shell

```bash
sudo -i
# 干完活
exit
```

> `sudo -i` 会开一个登录式的 root shell（读 root 的 profile），不用知道 root 密码（只要你有 sudo 权限）。这是现代服务器上「当 root」的标准方式。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `sudo 命令` | 临时以 root 跑一条命令（**最常用**） |
| `sudo -i` | 开一个完整 root shell |
| `sudo -u nginx 命令` | 以指定用户身份跑 |
| `sudo -l` | 看自己有哪些 sudo 权限 |
| `sudo -n 命令` | 脚本里非交互跑 |
| `sudo -e 文件` / `sudoedit 文件` | 安全地编辑 root 文件 |
| `su -` | 完整切到 root（要 root 密码） |
| `su -c '命令'` | 以 root 跑一条命令就回来 |

## 六、RHEL 系与 Debian 系差异

- 命令本身完全一致。差异在**默认授权方式**：
  - Debian/Ubuntu：把用户加进 `sudo` 组就有 sudo 权限（`usermod -aG sudo 名字`）。
  - RHEL/CentOS/Rocky：加进 `wheel` 组（`usermod -aG wheel 名字`）。
- Ubuntu 默认**不设 root 密码**，所以日常提权全靠 `sudo`；RHEL 安装时若设了 root 密码，可以直接 `su -`。
- sudo 配置文件都是 `/etc/sudoers`（用 `sudo visudo` 编辑，别直接 vi）。

## 七、新手易错点

1. **`su` 和 `su -` 不一样**：没有横杠不切环境，很多变量、PATH 还是旧的，导致「切了 root 但命令找不到」。一律用 `su -`。
2. **sudo 时间戳会缓存**：刚输过密码，几分钟内 sudo 不再问。公共机器上用完可以 `sudo -k` 清掉。
3. **别用 `sudo` 跑全图形/编辑器**：能 `sudo -e` 就别 `sudo vi`，减少 root 身份暴露面。
4. **`sudo` 是借身份，`su -` 是换人**：跑一条命令用 sudo，别养成 `sudo su -` 长驻 root 的习惯。
5. **脚本里的 sudo 一定要加 `-n`**：否则卡在密码提示上，任务永远不结束。
6. **危险：root 身份下 `rm -rf` 没有回收站**：提权后删东西前先 `pwd`、先 `ls`，确认路径再回车。
7. **`sudo !!`**：上一条命令忘了加 sudo，输入 `sudo !!` 可以用 root 重跑，很顺手但也要确认上一条真的安全。

## 八、相关命令与文档

- 速查页：[Linux 命令速查](../linux-commands)
- 怎么新建用户、把人加进 sudo/wheel 组：见 [用户管理](./user-mgmt)
- 权限位：见 [chmod](./chmod)
- 用户/权限概念专题：[Linux 用户与组](../../guide/linux-users)
- 安全模型专题：[Linux 安全](../../guide/linux-security)
