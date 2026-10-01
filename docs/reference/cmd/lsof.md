# lsof 命令详解：查看「哪个进程打开了哪些文件/端口」

> 本文是 [Linux 命令速查](../linux-commands#进程查看) 中 `lsof` 的从 0 到 1 详解。
> 目标：把 `lsof -h` 里的每个高频选项讲清楚，尤其是 `-i`（查端口）、`-p`（查进程）、`-u`（查用户）、`-n`/`-P`（加速）、`+c`（显示全名），看完你排障时能一眼定位「谁占了这个端口/文件」。
> 环境依据：lsof 4.93.2（Ubuntu 22.04 自带 `lsof` 包；RHEL/Rocky 同为 `lsof` 包）。

## 一、命令是干什么的

`lsof` = **list open files**（列出打开的文件）。Linux 里「一切皆文件」——网络连接、管道、设备、磁盘文件都是文件。所以 lsof 能回答两个高频问题：

1. **哪个端口被谁占用了？**（启动服务报 `Address already in use` 时）
2. **哪个进程打开了某个文件？**（要删文件删不掉、想知道谁在用）

- `lsof`：列出**所有**进程打开的所有文件（输出巨长）；
- `lsof -i :端口`：查谁在占用这个端口；
- `lsof -p PID`：查某进程打开了哪些文件；
- `lsof 文件`：查谁打开了这个文件。

> 类比：像「文件被占用，无法删除」弹窗背后那个管理器——Windows 会问「哪个程序在用它」，lsof 在 Linux 上直接告诉你答案。

## 二、命令语法

```bash
lsof [选项] [文件名...]
```

- 不带任何参数：列出系统里所有打开的文件（一般要 root，输出很长）；
- 带文件名参数：查谁打开了这个文件；
- 选项用来过滤（按端口/进程/用户）。

## 三、选项全表（对照 `lsof -h`）

### 1. 查网络相关（最常用）

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-i` | 列出所有**网络文件**（TCP/UDP 连接） | 看谁在联网 |
| `-i :端口` | 查占用**某端口**的进程 | `lsof -i :80`（端口冲突排查） |
| `-iTCP` / `-iUDP` | 只看 TCP 或 UDP | 限定协议 |
| `-i@host` | 按对端主机过滤 | 较少用 |
| `-sTCP:状态` | 按 TCP 状态过滤 | `-sTCP:LISTEN` 只看监听中的 |
| `-U` | 只看 Unix socket | 查本地套接字 |

### 2. 按进程/用户/命令过滤

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-p PID` | 只列某 **PID** 打开的文件 | 看某进程在读写什么 |
| `-c 命令名` | 只列**命令名**以 xx 开头的进程 | `lsof -c nginx` |
| `-u 用户名` | 只列某**用户**打开的文件 | `lsof -u user` |
| `-a` | 多个条件 **AND**（默认是 OR） | 如 `-u user -a -i` 看该用户的网络连接 |

### 3. 输出格式与加速

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-n` | **不反解主机名**（直接显示 IP） | 加速，避免 DNS 慢 |
| `-P` | **不反解端口名**（直接显示端口号） | 加速，避免查 /etc/services |
| `+c 宽度` | COMMAND 列显示**完整命令名**（默认截到 9 字符） | 看全进程名 |
| `-t` | **精简输出**（只列 PID） | 配合 kill：`kill $(lsof -t -i :80)` |
| `-F` | 输出机器可读格式 | 脚本解析 |
| `-R` | 显示父进程 PPID | 看父子 |
| `-d FD` | 按文件描述符过滤 | 较少用 |
| `+D 目录` | 递归查目录下打开的文件 | 比 +d 慢 |

## 四、由浅入深的典型示例

### 示例 1：看谁在监听 TCP 端口

```bash
lsof -iTCP -sTCP:LISTEN
```

```text
COMMAND    PID USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
python-se 1277 user   14u  IPv4  10272      0t0  TCP localhost:8091 (LISTEN)
websocat  1280 user    6u  IPv4   8117      0t0  TCP localhost:6080 (LISTEN)
gost      1283 user    3u  IPv4   8151      0t0  TCP localhost:18080 (LISTEN)
Xvnc      1288 user    9u  IPv4  9121      0t0  TCP localhost:5900 (LISTEN)
chrome    1330 user   78u  IPv4 10538      0t0  TCP localhost:9222 (LISTEN)
```

> `-iTCP -sTCP:LISTEN` 只列正在监听的 TCP 端口。一眼看清机器上开了哪些服务端口。

### 示例 2：端口被占用了，查谁占的（最高频）

```bash
lsof -i :8091
```

```text
COMMAND    PID USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
python-se 1277 user   14u  IPv4  10272      0t0  TCP localhost:8091 (LISTEN)
```

> 启动 nginx 报 `bind: Address already in use`？就 `lsof -i :80` 看谁占着，然后 kill 那个 PID。

### 示例 3：查某进程打开了哪些文件

```bash
lsof -p $$
```

```text
COMMAND  PID USER   FD   TYPE DEVICE SIZE/OFF                NODE NAME
bash    5207 user  cwd    DIR   0,53     4096 1279866719103711331 /home/user/Doubao/...
bash    5207 user  rtd    DIR   0,47     4096                   2 /
bash    5207 user  txt    REG   0,49  1396520              752263 /usr/bin/bash
bash    5207 user  mem    REG   0,46                       912744 /usr/lib/x86_64-linux-gnu/libc.so.6
```

> `-p $$`（当前 shell 的 PID）列出它打开的所有东西：`cwd` 当前目录、`txt` 程序本身、`mem` 映射的库。排查「进程的工作目录在哪」很有用。

### 示例 4：查谁打开了某个文件

```bash
lsof /tmp/demo/a.txt
```

```text
（无输出 = 当前没有进程打开这个文件）
```

> 删文件删不掉、或想知道谁在读某个日志时，`lsof 文件名` 一查便知。有输出说明有人在用。

### 示例 5：按命令名查

```bash
lsof -c bash
```

```text
COMMAND  PID USER   FD   TYPE DEVICE SIZE/OFF                NODE NAME
bash    1514 user  cwd    DIR   0,47     4096                 828 /workspace
bash    1514 user  rtd    DIR   0,47     4096                   2 /
bash    1514 user  txt    REG   0,49  1396520              752263 /usr/bin/bash
```

> `-c bash` 列所有命令名是 bash 的进程打开的文件。

### 示例 6：按用户查

```bash
lsof -u user
```

```text
COMMAND    PID USER  FD      TYPE DEVICE  SIZE/OFF NODE NAME
python-se 1277 user  cwd       DIR  0,47      4096    32 /runtime/mcp_vm_server
python-se 1277 user  txt       REG  0,49  33399016 250807 /opt/python3.12/bin/python3.12
```

> `-u user` 列 user 这个用户打开的所有文件。想看某用户在搞什么大动作时用。

### 示例 7：让进程名显示完整（+c）

```bash
lsof -iTCP -sTCP:LISTEN +c 15
```

```text
COMMAND        PID USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
python-server 1277 user   14u  IPv4  10272      0t0  TCP localhost:8091 (LISTEN)
websocat      1280 user    6u  IPv4  8117      0t0  TCP localhost:6080 (LISTEN)
```

> 默认 COMMAND 列只显示 9 个字符，`python-server` 被截成 `python-se`。`+c 15` 加宽到 15 字符就能看全。

### 示例 8：加 -n -P 加速（不反解）

```bash
lsof -i :8091 -n -P
```

```text
COMMAND    PID USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
python-se 1277 user   14u  IPv4  10272      0t0  TCP 127.0.0.1:8091 (LISTEN)
```

> `-n` 不把 IP 反解成主机名、`-P` 不把端口号反解成服务名（如 `webmin` 变回 `10000`）。机器 DNS 慢时 lsof 卡，加上这两个立刻快。

### 示例 9：一行杀掉占用某端口的进程

```bash
kill $(lsof -t -i :8091)
```

> `-t` 精简模式只输出 PID，配合 `$(...)` 直接喂给 kill。端口冲突时一条命令解决（先确认确实是该杀的进程）。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `lsof -i :端口` | 查谁占用端口（**最常用**） |
| `lsof -iTCP -sTCP:LISTEN` | 看所有监听端口 |
| `lsof -p PID` | 查某进程打开了什么 |
| `lsof 文件名` | 查谁打开了这个文件 |
| `lsof -c 命令名` | 按命令名查 |
| `lsof -u 用户名` | 按用户查 |
| `lsof -i -n -P` | 加速版网络查看 |
| `kill $(lsof -t -i :端口)` | 杀掉占用端口的进程 |

## 六、RHEL 系与 Debian 系差异

- 包名都是 `lsof`，装法 `apt install lsof` / `yum install lsof`；
- 选项行为两系一致；
- 容器里 lsof 可能看不到宿主机的进程（PID namespace 隔离），这是容器特性不是命令差异。

## 七、新手易错点

1. **普通用户 lsof 看不全**：很多进程是 root 的，普通用户只能看到自己的。看全系统要 `sudo lsof`。
2. **`lsof` 不带参数输出巨长**：一般别直接跑裸 `lsof`，加过滤条件（`-i`/`-p`/`文件名`）。
3. **端口冲突先 lsof**：服务起不来先 `lsof -i :端口`，别急着重启。
4. **删不掉的文件 lsof 查一下**：磁盘满了但 du 看着不大？可能是被进程打开着但已删的文件，`lsof +L1` 找已删除但仍占用的。
5. **`-n -P` 必加**：不加会做 DNS/服务名反解，慢到怀疑人生。
6. **危险：`kill $(lsof -t ...)` 前先确认**：先单独跑 `lsof -i :端口` 看清是哪个进程，再杀，别误杀业务。
7. **lsof 不是 netstat**：查端口 lsof 更直接；要看连接统计表也可 `ss -tnp`（见网络篇）。

## 八、相关命令与文档

- 速查页：[Linux 命令速查](../linux-commands#进程查看)
- 找进程 PID：见 [process-find](./process-find)
- 杀进程：见 [process-signal](./process-signal)
- 看进程快照：见 [ps](./ps)、实时看 [top](./top)
- 网络排障专题：[Linux 网络](../../guide/linux-network)
