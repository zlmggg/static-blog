# pstree、pgrep、pidof 命令详解：快速找进程和它的父子关系

> 本文是 [Linux 命令速查](../linux-commands#进程查看) 中 `pstree`、`pgrep`、`pidof` 的从 0 到 1 详解，本篇一次讲清「看进程树」和「按名字找 PID」。
> 目标：把各命令 `--help`/`-h` 里的选项讲清楚，看完你想找某个进程的 PID、想看它爹是谁时，不用再 `ps aux | grep`。
> 环境依据：`pstree` 属 psmisc（Ubuntu 22.04）；`pgrep`/`pidof` 属 procps-ng 3.3.17。RHEL/Rocky 对应包名一致（psmisc / procps-ng）。

## 一、命令是干什么的

找进程 PID 有三种姿势，各有所长：

- `pstree`：把进程画成**树**，一眼看清谁是谁的爹、谁是谁的娃；
- `pgrep`：按**名字模式**找 PID，比 `ps aux | grep` 干净，不会把 grep 自己带进来；
- `pidof`：按**精确程序名**找 PID，最直接。

> 类比：`ps aux | grep` 是「在通讯录里全文搜」；`pgrep` 是「按姓名搜」；`pidof` 是「按身份证上的大名精确查」；`pstree` 是「看家谱图」。

## 二、命令语法

```bash
pstree [选项] [PID|用户]
pgrep [选项] 模式
pidof [选项] 程序名
```

- `pstree`：不给参数从 PID 1 开始画整棵树；给 PID 从那棵子树开始画；
- `pgrep 模式`：按正则/名字匹配进程名，输出 PID；
- `pidof 程序名`：给精确程序名，输出它的 PID。

## 三、选项全表

### 1. pstree：画进程树

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-p`，`--show-pids` | 显示每个进程的 **PID** | 树里要看编号时（最常用） |
| `-a`，`--arguments` | 显示**完整命令行参数** | 光看名字不知道启动参数时 |
| `-u`，`--uid-changes` | 显示 UID 切换 | 看哪些进程属主变了 |
| `-n`，`--numeric-sort` | 按 PID 排序 | 默认按名字排 |
| `-g`，`--show-pgids` | 显示进程组 ID | 较少用 |
| `-l`，`--long` | 不截断长行 | 参数太长被截时 |
| `-T`，`--hide-threads` | 隐藏线程，只显示进程 | 线程太多太乱时 |
| `-A`/`-G`/`-U` | 用 ASCII/VT100/Unicode 画线 | 终端不支持 Unicode 时用 `-A` |
| `-h PID` | 高亮某进程及其祖先 | 追踪父子链 |

### 2. pgrep：按名字找 PID

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-l`，`--list-name` | 同时显示 **PID + 进程名** | 不只输出数字时（常用） |
| `-a`，`--list-full` | 同时显示 **PID + 完整命令行** | 要看完整启动命令 |
| `-f`，`--full` | 匹配**完整命令行**而不只是进程名 | 名字一样但参数不同时 |
| `-u 用户` | 只找某用户的进程 | 过滤 |
| `-P PID` | 只找某**父进程**的子进程 | 找某服务的 worker |
| `-n`，`--newest` | 只选**最新启动**的那个 | 多个同名时取最近的 |
| `-o`，`--oldest` | 只选最早启动的 | 取 master 进程 |
| `-c`，`--count` | 只输出**匹配数量** | 数有几个实例 |
| `-x`，`--exact` | **精确匹配**整个名字 | 避免子串误匹配 |
| `-i`，`--ignore-case` | 忽略大小写 |  |
| `-v`，`--inverse` | 反向匹配 | 排除 |
| `-d 分隔符` | 指定输出分隔符 | 默认换行 |

### 3. pidof：按精确程序名找 PID

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-s` | 只返回**一个** PID | 脚本只要一个 |
| `-c` | 只返回同根目录的进程 | 容器里 |
| `-x` | 也找跑该脚本的 shell | 脚本名查找 |
| `-o PID` | 排除某个 PID | 排除自己 |
| `-q` | 安静（不输出） | 脚本判断存在性 |

## 四、由浅入深的典型示例

### 示例 1：看整棵进程树

```bash
pstree
```

```text
dumb-init-+-chrome_crashpad---{chrome_crashpad}
          |-lark_hijack_pro---5*[{lark_hijack_pro}]
          |-python3---chrome-+-chrome---chrome-+-chrome
          |                  |-chrome---9*[{chrome}]
          `-tmux: server---bash
```

> 直接看到父子关系。`{...}` 是线程，`5*[{...}]` 表示 5 个同名线程被压缩了。

### 示例 2：树里带 PID 和参数

```bash
pstree -p -a | head -8
```

```text
dumb-init,1 -c -- /bin/bash -c ulimit -n ... && exec runtime-agent /opt/bytefaas/run.sh
  |-chrome_crashpad,1351 --monitor-self ...
  |-lark_hijack_pro,888
```

> `-p` 带 PID、`-a` 带完整参数。想知道「那个进程的 PID 是多少、怎么启动的」就用它。

### 示例 3：从某个 PID 开始画子树

```bash
pstree -p 1279
```

```text
nginx(1279)---nginx(1543)
```

> 给一个 PID，只画它下面的子树。这里 nginx master(1279) 下面有一个 worker(1543)。

### 示例 4：pgrep 找进程 PID（最常用）

```bash
pgrep -a nginx
```

```text
1279 nginx: master process /usr/sbin/nginx -c /opt/gem/nginx.conf -g daemon off;
1543 nginx: worker process
```

> `-a` 显示 PID + 完整命令行。比 `ps aux | grep nginx` 干净——不会把 grep 自己列出来。

### 示例 5：按完整命令行匹配（-f）

```bash
pgrep -f 'python-server'
```

```text
1277
7863
```

> `-f` 匹配**完整命令行**而不只是进程名。进程名可能被截断，`-f` 能按命令行里的关键字找。

### 示例 6：取最新/最早的那个进程

```bash
pgrep -l -n nginx
```

```text
1543 nginx
```

> `-n` 只返回最新启动的那个（worker）。反过来 `-o` 返回最早的（master）。多实例时取特定一个很方便。

### 示例 7：pidof 精确找程序名

```bash
pidof nginx
```

```text
1543 1279
```

> `pidof` 给程序名，直接列出所有同名进程的 PID。注意它匹配的是**程序名**，不是命令行参数。

### 示例 8：数一下有几个实例

```bash
pgrep -c bash
```

```text
2
```

> `-c` 只输出数量。脚本里判断「服务起了几个实例」。

### 示例 9：找某用户的进程

```bash
pstree -u user
```

> 只画属于 user 的进程树。配合 `-p` 看 user 跑了什么。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `pstree -p` | 看进程树带 PID |
| `pstree -p PID` | 看某进程的子树 |
| `pgrep -a 名字` | 找 PID 并看完整命令（**最常用**） |
| `pgrep -f 关键字` | 按命令行关键字找 |
| `pgrep -n 名字` | 取最新启动的 |
| `pgrep -c 名字` | 数有几个 |
| `pidof 程序名` | 精确按程序名找 PID |
| `pstree -u 用户` | 只看某用户的树 |

## 六、RHEL 系与 Debian 系差异

- 包名：pstree 在 psmisc（两系同名）；pgrep/pidof 在 procps-ng（两系同名）；
- 选项行为一致；
- 容器里 PID 1 可能不是 systemd（这里是 dumb-init），但 pstree 用法不受影响。

## 七、新手易错点

1. **`pgrep` 默认只匹配进程名，不匹配参数**：要按命令行关键字找记得加 `-f`。
2. **`pidof` 和 `pgrep` 的区别**：pidof 只认程序名（comm），pgrep 加 `-f` 能匹配完整命令行。
3. **pstree 里 `{...}` 是线程不是进程**：别把线程当进程数。想看纯进程加 `-T`。
4. **pgrep 找不到时退出码非 0**：脚本里 `pgrep -x nginx || echo "没起"`，可用来判断服务是否存活。
5. **`ps aux | grep` 会带 grep 自己**：养成用 `pgrep` 的习惯，更干净。
6. **容器里看到的 PID 是容器内的**：和宿主机 PID 不同，别直接拿到宿主机用。
7. **找到 PID 后别乱杀**：先 `ps -p PID -o cmd=` 确认是哪个进程，再 kill（见 [process-signal](./process-signal)）。

## 八、相关命令与文档

- 速查页：[Linux 命令速查](../linux-commands#进程查看)
- 看进程快照：见 [ps](./ps)
- 实时看资源：见 [top](./top)
- 杀进程/发信号：见 [process-signal](./process-signal)
- 查端口占用：见 [lsof](./lsof)
- 进程专题：[Linux 进程管理](../../guide/linux-process)
