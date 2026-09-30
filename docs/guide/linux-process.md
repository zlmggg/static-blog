---
title: 进程与服务管理
description: 进程概念、ps/top 查看、kill 信号与作业控制，systemd/systemctl 与 Unit 文件，含僵尸/孤儿进程
---

# 进程与服务管理

::: tip 本篇定位
理解**进程与程序、父子关系和进程状态**，能用 ps/top 查看、用 kill/作业控制管理进程；并掌握用 **systemd/systemctl 管理服务**、手写 Unit 文件，最后搞清僵尸进程和孤儿进程。
:::

## 一、进程概念

### 1.1 程序与进程

| | 程序（Program） | 进程（Process） |
|---|---|---|
| 本质 | 存放在磁盘上的可执行文件（指令集合） | 程序的一次运行实例 |
| 状态 | 静态的、"死"的 | 动态的、"活"的 |
| 关系 | 一个程序可同时对应多个进程 | 每个进程由某个程序启动 |

同一份 Nginx 程序，启动后会有一个 master 加多个 worker，对应多个进程；程序是文件，进程是它跑起来的样子。

### 1.2 PID 与父子进程

- **PID（Process ID）**：内核给每个进程分配的唯一编号，用于区分不同进程；
- **PPID（Parent PID）**：父进程的 PID。

进程由父进程通过 **fork()** 创建，形成一棵进程树：

1. 父进程调用 `fork()` 复制出一个几乎相同的子进程（采用**写时复制 Copy-On-Write**，初始共享内存，真正修改时才复制，效率高）；
2. 子进程再通过 `execve()` 加载新程序，替换自己的内存空间，成为全新进程；
3. 子进程结束后，父进程通过 `wait()`/`waitpid()` 回收它的资源。

**系统的 1 号进程是 systemd**（CentOS 7 之前是 init），它是所有进程的"老祖宗"，由内核启动，负责拉起和管理整个用户空间：

```bash
pstree -p | head -3
# systemd(1)─┬─ModemManager(1024)─┬─{ModemManager}(1038)
#            ├─NetworkManager(1161)─...
```

### 1.3 进程与线程

- **线程（Thread）**是进程内部的执行流，是 CPU 调度的最小单位；
- 一个进程可含多个线程，**线程共享进程的内存空间和全局变量**，但各自有独立的栈和寄存器；
- 进程是资源分配的单位，线程是调度执行的单位。

> 类比：进程像一个"家"，有独立的房子（内存空间）；线程像家庭成员，共享家里的资源，但各自做不同的事。

### 1.4 进程状态

进程在生命周期中处于不同状态，`ps` 的 **STAT 列**就是状态：

| 状态 | 名称 | 含义 |
|---|---|---|
| **R** | Running | 运行中或就绪（在 CPU 上跑，或在队列等 CPU） |
| **S** | Sleeping | **可中断**的睡眠（等待某事件，如 I/O，能被信号唤醒）——最常见 |
| **D** | Disk sleep | **不可中断**的睡眠（通常在等磁盘 I/O，连信号都不理） |
| **T** | Stopped | 停止/暂停（被 Ctrl+z 或调试器挂起） |
| **Z** | Zombie | 僵尸（已退出，但父进程还没回收） |

STAT 还会带附加字符：

| 附加符 | 含义 |
|---|---|
| `+` | 前台进程（在终端前台） |
| `l`（小写 L） | 多线程进程 |
| `s`（小写） | 会话首进程（session leader） |
| `<` | 高优先级 |
| `N` | 低优先级 |
| `I`（大写 i） | 内核空闲线程 |

### 1.5 用户空间与内核空间

进程运行在两个隔离的"空间"：

- **用户空间**：应用程序运行的区域，权限受限，不能直接操作硬件；
- **内核空间**：内核运行的区域，拥有最高权限，管理硬件、内存、进程；
- 应用需要内核服务（读写文件、发网络包）时，通过**系统调用（system call）**进入内核。

---

## 二、查看进程

### 2.1 ps：快照查看

`ps`（process status）显示某一时刻进程的快照。三种风格选项（UNIX 用 `-`、GNU 用 `--`、BSD 不带 `-`）：

```bash
# 最常用组合
ps aux          # BSD 风格：列出所有进程及属主、资源占用
ps -ef          # UNIX 风格：全格式列出所有进程（含 PPID）
ps -eFH         # 树形/完整格式
ps -ef --forest # 以树形显示父子关系
```

**`ps aux` 字段解读：**

| 字段 | 含义 |
|---|---|
| USER | 进程属主 |
| PID / PPID | 进程 ID / 父进程 ID |
| %CPU / %MEM | CPU / 内存占用率 |
| VSZ | 虚拟内存大小（KB） |
| RSS | 实际占用的物理内存（KB） |
| TTY | 终端（`?` 表示与终端无关，如守护进程） |
| STAT | 进程状态 |
| START / TIME | 启动时间 / 累计占用 CPU 时长 |
| COMMAND | 程序及参数 |

**自定义输出列（写脚本常用）：**

```bash
ps -eo pid,ppid,user,ni,pri,pcpu,pmem,stat,comm   # -e 所有进程，-o 指定列
ps axo pid,cmd,%cpu,%mem --sort=-%cpu | head        # 按 CPU 倒序
ps -u nginx                                        # 只看某用户的进程
ps -p 1234 -o pid,ppid,cmd                         # 只看某个 PID
```

### 2.2 top：动态监控

`top` 实时刷新，顶部是系统整体负载，下方是进程排名：

```bash
top              # 默认每 3 秒刷新
top -d 1         # 每 1 秒刷新
top -p 992 -H    # 只看某进程，-H 显示其线程
top -b -n 1      # 批处理模式，只输出一次（适合脚本/采集）
```

**top 内常用交互键：**

| 按键 | 作用 |
|---|---|
| `q` | 退出 |
| `P` / `M` / `N` / `T` | 按 CPU / 内存 / PID / 运行时间排序 |
| `1` | 展开每个 CPU 核心的使用率（多核排障常用） |
| `k` / `r` | 给进程发信号 / 调整 nice 值 |
| `f` | 自定义显示字段 |
| `z` | 切换彩色显示 |

**头部关键指标：**

- `load average: 1分钟, 5分钟, 15分钟` 平均负载（正在运行 + 等待 I/O 的进程数，持续超过 CPU 核数说明压力大）；
- `%Cpu(s)`：`us` 用户态、`sy` 内核态、`id` 空闲、`wa` 等 I/O、`st` 被虚拟化偷走的时间。

> 增强版 **htop** 支持鼠标、滚动、彩色，操作更直观：`htop`（RHEL 需先启用 EPEL，Ubuntu 直接安装）。

### 2.3 pstree：进程树

```bash
pstree -p              # 树状显示并带 PID
pstree -p | grep nginx # 查看某程序的进程树
pstree zlmggg          # 只看某用户的进程树
```

### 2.4 pgrep / pidof：按名查找

```bash
pgrep nginx            # 显示名为 nginx 的所有 PID
pgrep -a sshd          # 同时显示完整命令
pgrep -u zlmggg        # 按用户查找
pgrep -f "sshd.*debug" # 匹配完整命令行（正则）

pidof nginx            # 按程序名返回 PID
pidof -s nginx         # 只返回一个
```

### 2.5 其他相关工具

内存、I/O、系统整体性能的查看（`free`、`vmstat`、`iostat`、`lsof`、`pmap`）属于性能监控范畴，详见 [系统性能监控](/guide/linux-performance)。

- `lsof -i :80`：查看谁占用了 80 端口；
- `lsof -p PID`：查看某进程打开的文件；
- `pmap -x PID`：查看进程的内存映射。

---

## 三、进程控制

### 3.1 kill 与信号

`kill` 通过给进程发送**信号（signal）**来控制它，最常用于终止进程：

```bash
kill PID            # 默认发 15 (SIGTERM)，请求进程优雅退出
kill -9 PID         # 发 9 (SIGKILL)，强制杀死，进程无法拒绝
kill -l             # 列出所有信号
```

**常用信号：**

| 编号 | 名称 | 含义 |
|---|---|---|
| 1 | SIGHUP | 挂起；常用于让守护进程**重读配置**（如 nginx reload） |
| 2 | SIGINT | 中断，相当于终端按 `Ctrl+c` |
| 3 | SIGQUIT | 退出，相当于 `Ctrl+\` |
| **9** | SIGKILL | **强制杀死**，不能被捕获/忽略，可能丢数据，慎用 |
| **15** | SIGTERM | 正常终止（默认），进程可捕获并做清理 |
| 18 | SIGCONT | 让暂停的进程继续运行 |
| 19 | SIGSTOP | 暂停进程（不能被忽略） |
| 20 | SIGTSTP | 终端暂停，相当于 `Ctrl+z`（可被捕获） |

::: warning 9 和 15 的区别
- `kill -15`（默认）是"请你退出"，进程可以先保存数据、关闭连接再走，**生产优先用**；
- `kill -9` 是"立刻消失"，进程没机会清理，可能留下脏数据、端口未释放等问题；
- 正确姿势：先 15，等几秒还不退，再上 9。
:::

### 3.2 killall / pkill：按名批量操作

```bash
killall nginx        # 杀掉所有名为 nginx 的进程（默认 15）
killall -9 nginx     # 强杀
pkill -u zlmggg      # 杀掉某用户的所有进程
pkill -f "ping.*baidu" # 按完整命令行匹配
```

> 端口被占用想快速找到并处理：`lsof -i :80` 拿 PID，或直接 `fuser -k 80/tcp`。

### 3.3 前台与后台

```bash
command &            # 直接放到后台运行（输出仍打到终端）
# 运行中按 Ctrl+z    # 把当前前台进程暂停并放到后台（状态 T）
jobs                 # 查看当前终端的作业列表
fg %1                # 把 1 号后台作业调回前台
bg %1                # 让暂停的 1 号作业在后台继续运行
```

::: warning 后台作业仍绑定终端
用 `&` 放到后台的进程，依然是当前终端的子进程；**一旦退出/关闭终端，它会收到 SIGHUP 而被杀掉**。要让它脱离终端存活，用下面的方法。
:::

### 3.4 nohup / setsid / disown

```bash
# nohup：忽略 SIGHUP，关闭终端也不死；输出默认写入 nohup.out
nohup ./run.sh > app.log 2>&1 &

# setsid：直接开启新会话，彻底脱离当前终端
setsid ./run.sh &

# disown：把已经在后台跑的作业从 shell 作业表移除，不再受终端影响
./run.sh &
disown
```

> 长时间运行、需要随时重新接入的任务，更推荐 **screen** 或 **tmux**（可断开后再 attach 回来）。

### 3.5 优先级：nice / renice

进程的"谦让度"用 **nice 值**表示，范围 **-20 到 19**：

- 值越小，优先级越高（-20 最高，19 最愿意让出 CPU）；
- 普通用户只能把自己的 nice 往高调（降低优先级），**设置负值需要 root**。

```bash
nice -n 11 ./job.sh          # 启动时指定 nice=11
renice -n -10 -p 3887        # 调整已运行进程（PID 3887）的 nice
ps axo pid,cmd,nice | grep job
top                          # top 里 NI 列就是 nice 值
```

> 现代普通进程由 **CFS（完全公平调度器）**调度，nice 值通过"权重"影响分得 CPU 的比例，而不是简单的固定时间片。

### 3.6 CPU 亲和：taskset

把进程绑定到指定 CPU 核心：

```bash
taskset -pc PID                       # 查看进程当前能在哪些核上跑
taskset -cp 0,1 PID                   # 绑定到 0、1 号核
taskset -c 1 ./job.sh                 # 启动时绑定到 1 号核
```

---

## 四、systemd 与 systemctl

### 4.1 为什么是 systemd

CentOS 7 以前用 **SysV init**（`/etc/init.d/` 脚本），串行启动、启动慢、管理能力弱。**systemd** 取代了它，成为当前所有主流发行版（RHEL 7+、Rocky、Ubuntu 15.04+、Debian 8+）的初始化系统：

- 并行启动服务，开机快；
- 用 **Unit（单元）** 统一管理服务、挂载、设备、套接字、定时任务等；
- 自带日志（journald）、依赖管理、按需启动、崩溃自动拉起。

### 4.2 Unit 的类型

systemd 把一切资源抽象为 Unit，常见类型（以后缀区分）：

| 后缀 | 类型 | 示例 |
|---|---|---|
| `.service` | 服务（最常用） | nginx.service |
| `.socket` | 套接字（按需唤醒服务） | docker.socket |
| `.target` | 目标单元（一组单元的集合，相当于运行级别） | multi-user.target |
| `.mount` / `.automount` | 挂载点 / 自动挂载 | data.mount |
| `.timer` | 定时任务（取代 cron 的一部分） | logrotate.timer |
| `.device` | 设备 | 网卡、磁盘 |

### 4.3 systemctl 管理服务

```bash
systemctl start nginx        # 启动
systemctl stop nginx         # 停止
systemctl restart nginx      # 重启
systemctl reload nginx       # 重读配置（不中断服务，需服务支持）
systemctl status nginx       # 查看状态（是否运行、最近日志）
systemctl is-active nginx    # 只输出是否在运行（脚本用）
systemctl cat nginx          # 查看该服务的 Unit 文件内容
```

**开机自启：**

```bash
systemctl enable nginx       # 设置开机自启
systemctl disable nginx      # 取消开机自启
systemctl is-enabled nginx   # 查看是否开机自启
systemctl enable --now nginx # 同时设置自启并立即启动
```

::: tip start 和 enable 是两回事
- `start/stop` 管**当前**这次运行与否；
- `enable/disable` 管**下次开机**是否自动启动；
- 二者互不影响，常常需要配合使用（如 `systemctl enable --now nginx`）。
:::

### 4.4 其他常用 systemctl

```bash
systemctl list-units --type=service          # 列出已加载的服务
systemctl list-unit-files --type=service     # 列出所有服务及自启状态
systemctl list-units --type=service --state=failed   # 查看启动失败的服务
systemctl daemon-reload                      # 改了 Unit 文件后重新加载
systemctl reboot / poweroff                  # 重启 / 关机
hostnamectl                                  # 查看主机/系统信息
journalctl -u nginx -f                       # 跟踪某服务日志（journald）
```

> 官方手册：[systemctl](https://www.freedesktop.org/software/systemd/man/latest/systemctl.html)、[systemd](https://www.freedesktop.org/wiki/Software/systemd/)

---

## 五、Unit 文件结构

### 5.1 三个主要段

一个 `.service` 文件由若干段（section）组成，最核心三段：

```ini
[Unit]            # 通用描述与依赖
[Service]         # 服务专属配置
[Install]         # enable/disable 时的安装信息
```

**[Unit] 常用指令：**

| 指令 | 含义 |
|---|---|
| `Description` | 服务的简短描述（status 时显示） |
| `After=` / `Before=` | 启动顺序（在某单元之后/之前启动） |
| `Wants=` | 弱依赖（依赖失败不影响自己） |
| `Requires=` | 强依赖（依赖失败自己也不起） |

**[Service] 常用指令：**

| 指令 | 含义 |
|---|---|
| `Type=` | 启动类型（见下） |
| `ExecStart=` | 启动服务执行的命令（**必须用绝对路径**） |
| `ExecReload=` | reload 时执行的命令 |
| `ExecStop=` | stop 时执行（不写则默认发 SIGTERM） |
| `Restart=` | 异常退出后是否自动重启（`always`/`on-failure`） |
| `User=` / `Group=` | 以哪个用户/组身份运行（安全，别用 root） |
| `WorkingDirectory=` | 工作目录 |
| `Environment=` | 设置环境变量 |

**Type 启动类型：**

| Type | 含义 |
|---|---|
| `simple` | 默认，ExecStart 启动的进程就是主进程，一直前台运行 |
| `forking` | 命令会 fork 出子进程并自己退出（传统守护进程），需配 `PIDFile=` |
| `oneshot` | 一次性任务，跑完就退出（如初始化脚本） |
| `notify` | 服务启动完成后会发通知给 systemd（如 nginx） |
| `dbus` | 取得 D-Bus 名称后才算就绪 |

**[Install] 常用指令：**

| 指令 | 含义 |
|---|---|
| `WantedBy=multi-user.target` | enable 时挂到哪个 target 下（最常见） |

### 5.2 Unit 文件的位置（优先级）

| 路径 | 用途 |
|---|---|
| `/usr/lib/systemd/system/` | **软件包安装**自带的 Unit（不要手改，升级会被覆盖） |
| `/etc/systemd/system/` | **系统管理员自定义/覆盖**，优先级最高 |
| `/run/systemd/system/` | 运行时生成，重启即丢 |

自定义服务放在 `/etc/systemd/system/`；想改包自带的，用 drop-in 更优雅：

```bash
systemctl edit nginx        # 创建 /etc/systemd/system/nginx.service.d/override.conf 覆盖部分配置
systemctl edit --full nginx # 完整复制一份再改
```

### 5.3 手写一个服务（完整示例）

假设写了一个应用 `/opt/myapp/run.sh`，希望以用户 `zlmggg` 身份运行、开机自启、崩溃自动拉起：

```bash
sudo vim /etc/systemd/system/myapp.service
```

```ini
[Unit]
Description=My Application Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=zlmggg
Group=zlmggg
WorkingDirectory=/opt/myapp
ExecStart=/opt/myapp/run.sh
ExecReload=/bin/kill -HUP $MAINPID
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

然后：

```bash
sudo systemctl daemon-reload          # 关键：新建/修改 Unit 后必须 reload
sudo systemctl enable --now myapp     # 开机自启并立即启动
systemctl status myapp                # 验证
```

::: warning 改了 Unit 文件必须 daemon-reload
systemd 启动时会把 Unit 加载到内存。之后你修改了文件，**必须先 `systemctl daemon-reload` 让它重新读取**，否则改动不生效（改 ExecStart 这类配置时尤其明显）。
:::

> 完整字段手册：[systemd.unit](https://www.freedesktop.org/software/systemd/man/latest/systemd.unit.html)、[systemd.service](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html)

---

## 六、target 与运行级别

### 6.1 target 是什么

`.target` 是一组相关 Unit 的集合，用来表示系统的某种状态，**取代了 SysV 的"运行级别（runlevel）"**。

**常用 target：**

| target | 含义 | 对应旧运行级别 |
|---|---|---|
| `multi-user.target` | 多用户命令行模式（服务器默认，无图形界面） | runlevel 3 |
| `graphical.target` | 图形界面模式（在 multi-user 基础上加桌面） | runlevel 5 |
| `rescue.target` | 救援模式（单用户、最小环境，相当于 1） | runlevel 1 |
| `emergency.target` | 紧急模式（连服务都不挂，只读根，最彻底） | — |
| `reboot.target` | 重启 | 6 / 0 |

### 6.2 切换与设置默认 target

```bash
systemctl get-default                    # 查看当前默认启动目标
sudo systemctl set-default multi-user.target   # 设置默认命令行（服务器省资源）
sudo systemctl isolate graphical.target  # 本次立即切换到某 target（不改变默认）
```

::: tip 云服务器建议用 multi-user.target
服务器跑图形界面会白白占用内存和 CPU，2核2G 的小机器尤其应该保持 **multi-user.target**（纯命令行），需要图形工具时通过 SSH 隧道转发即可。
:::

---

## 七、僵尸进程与孤儿进程

### 7.1 孤儿进程（Orphan）

**父进程先退出，子进程还在运行**，这个子进程就成了孤儿。

- 孤儿进程会被 **PID=1 的 systemd 自动"收养"**，PPID 变成 1；
- 孤儿进程**继续正常运行**，不受影响，systemd 会在它结束后负责回收；
- 所以孤儿进程**基本无害**，不用专门处理。

```bash
# 演示：父进程退出后，子进程 PPID 变为 1
(sleep 100 &)        # 在子 shell 里启动，父 shell 立刻退出
ps -o pid,ppid,cmd -C sleep
```

### 7.2 僵尸进程（Zombie）

**子进程已经退出，但父进程没有调用 wait() 回收**，子进程的进程描述符（PCB）仍残留在内核里，状态为 `Z`，命令名后显示 `<defunct>`。

**为什么有害：**

- 僵尸进程已经不占内存、不干活，但**仍占用一个 PID 和内核进程表项**；
- 少量无所谓，但**大量僵尸会耗尽 PID**，导致系统无法创建新进程。

**怎么处理：**

1. 僵尸进程**杀不掉**（它已经"死"了，`kill -9` 对它无效）；
2. 正确做法是处理它的**父进程**：
   - 先 `ps -o ppid= -p 僵尸PID` 找到父进程；
   - 通知父进程回收（给它发信号，或重启/修复父进程，很多时候父进程有 bug 没写 wait）；
   - 实在不行 `kill` 掉父进程，僵尸会被 systemd（1 号进程）接管并回收。
3. 根本解决是修复父进程代码，正确处理子进程退出（SIGCHLD + wait）。

```bash
# 排查僵尸
ps aux | grep -w Z          # STAT 为 Z
ps -eo pid,ppid,stat,cmd | awk '$3 ~ /Z/'
```

::: warning 典型场景
自己写的多进程程序（或某些有 bug 的服务）没正确回收子进程，重启该服务僵尸即消失；系统正常情况下几乎不会积累僵尸。
:::

---

## 面试自测

1. 程序和进程的区别？进程和线程的区别？
2. PID/PPID 是什么？系统的 1 号进程是谁、负责什么？
3. 说清进程的 R/S/D/T/Z 状态，D 和 S 有什么区别？
4. `kill -9` 和 `kill -15` 的区别？为什么优先用 15？
5. 如何让一个进程在关闭终端后继续运行？（nohup/setsid/disown/screen/tmux）
6. `&`、Ctrl+z、jobs、fg、bg 分别干什么？
7. systemd 相比 SysV init 有什么优势？
8. `systemctl start` 和 `enable` 的区别？
9. 手写一个 systemd service 的完整流程（为什么要 daemon-reload）？
10. 僵尸进程和孤儿进程的成因？僵尸进程为什么杀不掉、怎么处理？
11. multi-user.target 和 graphical.target 的区别？服务器用哪个？
12. nice 值范围和含义？普通用户能设负值吗？

## 相关速查

- [Linux 命令速查](/reference/linux-commands)
- [系统性能监控](/guide/linux-performance)
