# kill、killall、pkill 命令详解：给进程发信号（重点 1/9/15）

> 本文是 [Linux 命令速查](../linux-commands#进程查看) 中 `kill`、`killall`、`pkill` 的从 0 到 1 详解，本篇一次讲清「怎么停掉一个不听话的进程」。
> 目标：把信号（重点 SIGHUP=1、SIGKILL=9、SIGTERM=15）讲清楚，看完你知道什么时候该用 15、什么时候才用 9。
> 环境依据：`kill` 是 bash 内建命令（也有 `/usr/bin/kill` 在 procps-ng）；`killall` 属 psmisc；`pkill` 属 procps-ng 3.3.17。

## 一、命令是干什么的

`kill` 不只是「杀进程」——它是**给进程发信号**。信号是操作系统通知进程的一种方式：「请你退出」「请你重新读配置」「立刻停下来」。

- `kill PID`：给指定 PID 发信号（默认发 15=SIGTERM，请它自己退出）；
- `kill -9 PID`：发 9=SIGKILL，强制立刻干掉（不给它清理机会）；
- `killall 程序名`：给所有叫这个名字的进程发信号；
- `pkill 名字`：按模式匹配进程名发信号（和 pgrep 配对）。

> 类比：`kill -15` 像敲门说「您好，请下班吧」，程序可以收拾东西再走；`kill -9` 像直接断电拔网线，不管你在干嘛立刻停，可能丢数据。

## 二、命令语法

```bash
kill [信号] PID...
killall [选项] [信号] 程序名...
pkill [选项] [信号] 模式
```

- `信号`：可以是数字（`-9`）或名字（`-KILL`）；不写默认是 `-15`（SIGTERM）；
- `kill` 跟 **PID**；`killall` 跟**程序名**；`pkill` 跟**名字模式**。

## 三、选项全表

### 1. 信号列表（`kill -l` 本机实跑）

```text
 1) SIGHUP	 2) SIGINT	 3) SIGQUIT	 9) SIGKILL	15) SIGTERM
18) SIGCONT	19) SIGSTOP	20) SIGTSTP
```

最该记住的几个信号：

| 信号 | 数字 | 含义 | 什么时候用 |
|---|---|---|---|
| `SIGHUP` | `1` | 挂断。守护进程常用它**重新加载配置** | `kill -1 nginx` 让 nginx 重读配置（不重启） |
| `SIGINT` | `2` | 中断，等同你按 `Ctrl+C` | 前台程序中断 |
| `SIGKILL` | `9` | **强制杀**，进程无法拦截/忽略 | 只有 -15 叫不走时才用（最后手段） |
| `SIGTERM` | `15` | **请求退出**（kill 默认发的就是它） | 优雅停止，让程序清理现场 |
| `SIGSTOP` | `19` | 暂停进程（不可拦截） | 配合 SIGCONT 继续 |
| `SIGCONT` | `18` | 继续运行被暂停的进程 | 配合 19 |

> 关键：**9 和 19 是不可被程序捕获/忽略的**，内核直接干掉；1、15 程序可以选择不理或自己处理。

### 2. kill（bash 内建）

| 用法 | 作用 |
|---|---|
| `kill -l` | 列出所有信号名和编号 |
| `kill PID` | 发 SIGTERM（15） |
| `kill -15 PID` | 显式发 SIGTERM |
| `kill -9 PID` | 发 SIGKILL |
| `kill -0 PID` | 不真发信号，只检查进程是否存在 |

### 3. killall（按程序名）

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-信号`，`-s 信号` | 发指定信号（默认 15） | `killall -9 nginx` |
| `-i`，`--interactive` | 杀之前**逐个询问** | 怕误杀时 |
| `-e`，`--exact` | 长名字要求精确匹配 | 避免误杀 |
| `-I`，`--ignore-case` | 忽略大小写 |  |
| `-u 用户` | 只杀某用户的进程 | `killall -u user sleep` |
| `-r`，`--regexp` | 名字当正则 | 模糊匹配 |
| `-w`，`--wait` | 等进程真死了才返回 | 脚本里 |
| `-v`，`--verbose` | 打印杀了谁 | `killall -v sleep` |
| `-l`，`--list` | 列所有信号名 |  |

### 4. pkill（按模式）

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-信号` | 发指定信号 | `pkill -9 nginx` |
| `-f`，`--full` | 匹配**完整命令行**（不只进程名） | `pkill -f "python server.py"` |
| `-u 用户` | 只杀某用户的进程 |  |
| `-P PID` | 只杀某父进程的子进程 |  |
| `-n`/`-o` | 只杀最新/最早的 |  |
| `-x`，`--exact` | 精确匹配 | 避免子串误杀 |
| `-e`，`--echo` | 打印杀了谁 | 安全 |

## 四、由浅入深的典型示例

### 示例 1：温柔停止一个进程（默认 15）

```bash
sleep 600 &
MYPID=$!
kill -0 $MYPID && echo "存活"
kill -15 $MYPID
```

```text
存活
/bin/bash: kill: (8006) - No such process
```

> `kill -15` 发 SIGTERM，sleep 收到后立刻退出。`kill -0` 不发信号只探测进程在不在——退出后再 `kill -0` 报「No such process」说明它走了。

### 示例 2：强制杀（-9，最后手段）

```bash
kill -9 1234
```

> 先用 15 叫它退出，等几秒还不退，再用 9。**别上来就 9**——程序可能正在写文件，强杀会损坏数据/留下临时锁。

### 示例 3：让守护进程重读配置（-1）

```bash
sudo kill -1 $(cat /run/nginx.pid)
```

> nginx 收到 SIGHUP 会重新加载配置而不中断服务。很多守护进程（nginx、apache、sshd）都这么做，等价于 `systemctl reload nginx`。

### 示例 4：按程序名杀所有同名进程

```bash
killall -v sleep
```

```text
Killed sleep(1297) with signal 15
Killed sleep(5944) with signal 15
Killed sleep(8019) with signal 15
```

> `killall sleep` 把**所有**叫 sleep 的进程都发 15。`-v` 打印杀了谁。注意：它杀的是全系统所有同名进程，不只是你的！

### 示例 5：按模式杀（pkill）

```bash
sleep 603 &
pkill -f "sleep 603"
```

> `pkill -f "sleep 603"` 按完整命令行匹配，精准杀掉那个带参数 603 的 sleep，不影响别的 sleep。`-f` 很关键，不加就只匹配进程名。

### 示例 6：先 pgrep 确认再 pkill

```bash
pgrep -af "sleep"
pkill -f "sleep 603"
```

> 好习惯：先用 `pgrep -af` 列出会被匹配的进程，看清楚了再 `pkill`。pkill 和 pgrep 用同样的匹配规则，先查后杀。

### 示例 7：只杀某用户的进程

```bash
sudo pkill -u user chrome
```

> `-u user` 只杀 user 这个用户名下的 chrome，不影响别人。

### 示例 8：列出所有信号

```bash
kill -l
```

```text
 1) SIGHUP	 2) SIGINT	 3) SIGQUIT	 4) SIGILL	 5) SIGTRAP
 9) SIGKILL	15) SIGTERM	18) SIGCONT	19) SIGSTOP	20) SIGTSTP
```

> 忘了信号编号就 `kill -l` 查。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `kill PID` | 温柔停止（默认 15） |
| `kill -15 PID` | 显式温柔停止 |
| `kill -9 PID` | 强制杀（**最后手段**） |
| `kill -1 PID` | 让守护进程重载配置 |
| `kill -0 PID` | 探测进程是否存在 |
| `killall 程序名` | 杀所有同名进程 |
| `pkill -f 关键字` | 按命令行关键字杀 |
| `pgrep -af 关键字` | 杀之前先确认 |

## 六、RHEL 系与 Debian 系差异

- `kill` 是 bash 内建，两系一致；`killall` 在 psmisc、`pkill` 在 procps-ng，两系同名同选项；
- 现代服务器更推荐用 `systemctl stop 服务名` 停服务，而不是直接 kill；直接 kill 只在进程失控、systemctl 也拉不回来时用。

## 七、新手易错点

1. **别上来就 `kill -9`**：先 `kill -15` 等几秒，不行再 `kill -9`。-9 不给程序清理机会，可能丢数据、留临时文件锁。
2. **`killall` 杀的是全系统同名进程**：不是只杀你那个。公共机器上 `killall python` 会杀掉所有人的 python，慎用。
3. **`pkill` 不加 `-f` 只匹配进程名**：要按命令行参数找，记得加 `-f`。
4. **`pkill -f` 可能误杀**：`pkill -f nginx` 会把命令行里带 nginx 字样的都杀了（包括你正在敲的 `vim nginx.conf`）。杀之前先 `pgrep -af` 确认。
5. **`kill -9` 杀不掉僵尸进程**：僵尸进程已经死了，只是父进程没收尸，要找它爹（`ps -ef` 看 PPID）处理。
6. **`kill` 跟的是 PID 不是名字**：`kill nginx` 是错的（会把 nginx 当 PID）。按名字杀用 `killall`/`pkill`。
7. **危险：`kill -9 -1`** 或 `kill -9 $(pgrep xxx)` 误杀范围极大。永远先确认匹配到的进程列表。

## 八、相关命令与文档

- 速查页：[Linux 命令速查](../linux-commands#进程查看)
- 找进程 PID：见 [process-find](./process-find)
- 后台/作业控制（暂停、继续、nohup）：见 [job-control](./job-control)
- 实时看进程：见 [top](./top)
- 进程专题：[Linux 进程管理](../../guide/linux-process)
