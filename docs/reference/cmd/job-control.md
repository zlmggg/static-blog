# jobs、fg、bg、nohup、nice、renice 命令详解：后台作业与进程优先级

> 本文是 [Linux 命令速查](../linux-commands#进程查看) 中 `jobs`/`fg`/`bg`/`nohup`/`nice`/`renice` 的从 0 到 1 详解，本篇一次讲清「把命令放后台跑、断开 SSH 后不让它死、调整优先级」。
> 目标：把 bash 内建命令（jobs/fg/bg，用 `help` 取语法）和 coreutils 的 nohup/nice/renice 讲清楚，看完你知道怎么让一个长跑任务不霸占终端、断了 SSH 还活着。
> 环境依据：`jobs`/`fg`/`bg` 是 bash 内建命令（随 bash 提供，用 `help 命令名` 取语法）；`nohup`/`nice` 属 GNU coreutils 8.32；`renice` 属 util-linux（Ubuntu 包名 bsdutils）。

## 一、命令是干什么的

在终端里跑一个要跑 10 分钟的任务，终端就被它占死了，干不了别的。这组命令解决「后台运行」和「优先级」：

- `命令 &`：把命令扔到**后台**，立刻拿回提示符；
- `jobs`：看当前终端有哪些后台任务；
- `fg 任务号`：把后台任务**拉回前台**；
- `bg 任务号`：把暂停的任务放到**后台继续跑**；
- `nohup 命令 &`：让命令**忽略挂断信号**，SSH 断开后还能继续跑；
- `nice -n N 命令`：以指定**优先级**启动命令；
- `renice N PID`：改一个**已经在跑**的进程的优先级。

> 类比：前台任务像「你自己在前台手搓」，后台任务像「派了个伙计在后面干」；`jobs` 是看派了几个伙计；`nohup` 是「就算你下班（断 SSH），伙计也得把活干完」；`nice` 是给伙计排「这个活急不急」。

## 二、命令语法

```bash
命令 &                # 后台启动
jobs [-lnprs] [任务号]
fg [任务号]
bg [任务号]
nohup 命令 [参数]...
nice [-n N] [命令 [参数]...]
renice [-n] 优先级 [-p PID] [-g 进程组] [-u 用户]
```

- 任务号：`jobs` 列出的 `[1]`/`[2]`，用 `%1`/`%2` 引用；
- `nice` 不给命令就打印当前 nice 值；
- `renice` 默认对 PID 操作。

## 三、选项全表

### 1. jobs（bash 内建，`help jobs`）

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-l` | 额外显示 **PID** | 要拿后台任务 PID |
| `-p` | 只列 PID | 脚本取 PID |
| `-r` | 只列**正在运行**的任务 |  |
| `-s` | 只列**已停止**的任务 |  |
| `-n` | 只列自上次通知后状态变化的 |  |
| `-x 命令` | 把任务号替换成 PID 后执行命令 | 较少用 |

### 2. fg / bg（bash 内建）

| 命令 | 作用 |
|---|---|
| `fg` | 把当前任务拉回前台 |
| `fg %1` | 把 1 号任务拉回前台 |
| `bg` | 把当前暂停的任务放到后台继续 |
| `bg %1` | 把 1 号任务放到后台 |

### 3. nohup（coreutils）

| 用法 | 作用 |
|---|---|
| `nohup 命令 &` | 忽略 SIGHUP，让命令在 SSH 断开后继续跑 |
| `nohup 命令 > 文件 2>&1 &` | 输出重定向到文件（默认写 nohup.out） |

> nohup 本身没有选项（只有 `--help`/`--version`），它就是「让命令忽略挂断信号」。

### 4. nice / renice（调优先级）

| 命令 | 作用 |
|---|---|
| `nice` | 打印当前 nice 值（默认 0） |
| `nice -n N 命令` | 以 nice 值 N 启动命令（N 越大越谦让，默认 10） |
| `renice -n N -p PID` | 改已运行进程的 nice 值 |
| `renice -n N -u 用户` | 改某用户所有进程的 nice |

> nice 范围：`-20`（最高优先级，最抢 CPU）到 `19`（最低，最谦让）。普通用户只能把自己的进程**调得更谦让**（数值调大），想调高优先级（数值调小）要 root。

## 四、由浅入深的典型示例

### 示例 1：把命令扔到后台

```bash
sleep 300 &
```

```text
[1] 8179
```

> `&` 结尾 = 后台跑。立刻返回 `[1] 8179`：`[1]` 是任务号，`8179` 是 PID。终端立刻还给你。

### 示例 2：看有哪些后台任务

```bash
jobs
jobs -l
```

```text
[1]+  Running                 sleep 300 &
[1]+  8179 Running                 sleep 300 &
```

> `jobs` 列当前终端的后台任务。`-l` 多列 PID。`+` 号表示这是「当前任务」。

### 示例 3：把后台任务拉回前台

```bash
fg %1
```

> 把 1 号任务拉到前台。如果它在跑长任务，终端又被占住了。想暂停它按 `Ctrl+Z`。

### 示例 4：Ctrl+Z 暂停后用 bg 继续

```bash
# 假设前台跑着一个任务，按 Ctrl+Z 暂停它
# 输出类似：
# [1]+  Stopped   sleep 300
bg %1      # 让它在后台继续跑
jobs
```

> `Ctrl+Z` 是暂停（不是结束），任务变成 Stopped；`bg %1` 让它在后台继续跑。这是「前台跑一半想放后台」的标准流程。

### 示例 5：nohup 让任务断 SSH 也活着

```bash
nohup ./long-task.sh > task.log 2>&1 &
```

> 关键三件套：`nohup`（忽略挂断）+ `> task.log`（输出别打到终端）+ `&`（后台）。这样你退出 SSH，任务还在跑，输出写在 task.log。不加 `> 文件` 的话，nohup 会把输出写到当前目录的 `nohup.out`。

### 示例 6：看当前 nice 值

```bash
nice
```

```text
0
```

> 裸 `nice` 打印当前 shell 的 nice 值，默认 0。

### 示例 7：以低优先级启动任务

```bash
nice -n 19 sleep 500 &
ps -o pid,ni,comm -p $!
```

```text
  PID  NI COMMAND
 8181  19 sleep
```

> `nice -n 19` 以最谦让的优先级跑这个任务——它不会抢前台任务的 CPU。跑批量编译、数据处理这种不急的活时用，别影响线上请求。

### 示例 8：改已运行进程的优先级

```bash
nice -n 10 sleep 500 &
renice -n 15 -p $!
```

```text
(进程) old priority 10, new priority 15
```

> `renice` 改已经在跑的进程。注意：普通用户只能往**更大的 nice 值**调（更谦让），往小了调（更抢 CPU）会报 `Permission denied`——那需要 root。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `命令 &` | 后台跑 |
| `jobs` | 看后台任务 |
| `fg %1` | 拉回前台 |
| `bg %1` | 暂停后放后台继续 |
| `Ctrl+Z` | 暂停前台任务 |
| `nohup 命令 > log 2>&1 &` | 断 SSH 也不死（**最常用**） |
| `nice -n 19 命令 &` | 低优先级跑后台任务 |
| `renice -n 15 -p PID` | 改已运行进程优先级 |

## 六、RHEL 系与 Debian 系差异

- `jobs`/`fg`/`bg` 是 bash 内建，两系一致；
- `nohup`/`nice` 属 coreutils、`renice` 属 util-linux，两系用法一致；
- 现代更推荐用 `systemd`/`supervisor` 托管长跑服务（如 `systemd-run`），nohup 适合临时一次性任务。

## 七、新手易错点

1. **`&` 只是后台，断 SSH 还是会死**：要断了 SSH 还活着，必须 `nohup ... &`。普通 `&` 任务在 SSH 断开时会收到 SIGHUP 死掉。
2. **`nohup` 不加输出重定向会写 nohup.out**：几百 MB 的日志写到当前目录会撑爆磁盘，记得 `> task.log 2>&1`。
3. **`Ctrl+Z` 是暂停不是结束**：任务停在那还占着，要 `bg` 继续或 `kill` 掉。
4. **`jobs` 只看当前终端的任务**：换个终端/重连 SSH 后，jobs 是空的（但 nohup 的进程还在跑）。
5. **nice 数值越大越谦让**：`-20` 最抢 CPU、`19` 最礼貌。别记反。
6. **普通用户不能调高进程优先级**：`renice -n -5`（往小调）会报 Permission denied，要 root。
7. **危险：nohup 忘了 kill**：断 SSH 前 nohup 的任务一直跑，下次回来用 `ps`/`pgrep` 找到再 kill，别让僵尸后台任务吃资源。

## 八、相关命令与文档

- 速查页：[Linux 命令速查](../linux-commands#进程查看)
- 找后台任务 PID：见 [process-find](./process-find)
- 杀后台任务：见 [process-signal](./process-signal)
- 实时看进程优先级（NI 列）：见 [top](./top)
- 进程专题：[Linux 进程管理](../../guide/linux-process)
