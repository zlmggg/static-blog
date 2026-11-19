---
title: "strace 命令详解：跟踪系统调用定位卡顿与报错"
description: "strace 直接跟踪进程的系统调用，能看到进程在等哪个文件、哪个网络连接、哪次权限检查失败。本文给出附加进程、按调用类型过滤、统计耗时、容器内跟踪和常见误区。"
---

# strace 命令详解：跟踪系统调用定位卡顿与报错

> `strace` 跟踪的是**系统调用**，不是函数调用。进程卡在 `read`、`connect`、`futex`、`wait4` 时，它能直接告诉你卡在哪一步；但 CPU 热点、锁竞争、内存分配更适合用 `perf`、`pidstat`、`gdb` 等工具。

## 安装与基本用法

```bash
# RHEL / Rocky / CentOS
dnf install -y strace

# Debian / Ubuntu
apt install -y strace

# 跟踪一个已经在运行的进程
strace -p 12345

# 跟踪进程及其子进程，带时间戳和调用耗时
strace -f -tt -T -p 12345

# 只跟踪文件、网络相关调用，并输出到文件
strace -f -tt -T -s 256 \
  -e trace=openat,stat,access,connect,read,write \
  -p 12345 -o /tmp/strace-12345.log
```

常用参数：

| 参数 | 作用 |
|---|---|
| `-p PID` | 附加到已运行的进程 |
| `-f` | 跟踪 fork 出来的子进程，排查多进程服务必加 |
| `-tt` | 每行带精确时间戳 |
| `-T` | 显示每个系统调用的耗时 |
| `-s 256` | 字符串最多显示 256 字节，默认 32 容易截断 |
| `-o FILE` | 输出到文件，避免刷屏影响终端 |
| `-e trace=...` | 只跟踪指定系统调用，降低开销 |
| `-c` | 汇总每个系统调用的次数、耗时和错误 |
| `-y` | 把文件描述符打印成实际路径，便于确认操作对象 |
| `-k` | 打印用户态调用栈（需要编译时支持 libunwind） |

## 场景一：进程卡住，不知道在等什么

```bash
strace -f -tt -T -p 12345 -o /tmp/strace-block.log
# 另开一个终端观察最后几行
tail -f /tmp/strace-block.log
```

重点看**耗时很长的调用**和**没有返回的调用**：

- `connect(...)` 长时间不返回：对端不可达、防火墙丢包、DNS 解析慢。
- `read(...)` / `recvfrom(...)` 长时间不返回：等下游响应、等锁、等数据。
- `futex(...)` 长时间阻塞：用户态锁竞争，需要结合 `perf` 或线程栈分析。
- `wait4(...)`：在等子进程结束，检查子进程是否卡住。
- `openat(...)` 返回 `ENOENT`：路径不对、相对路径基准不对、容器内挂载缺失。

`-T` 会在每行末尾显示耗时，例如 `<0.000123>`；超过几百毫秒的调用优先看。

## 场景二：文件找不到、权限不足

```bash
strace -f -e trace=openat,stat,access,newfstatat -p 12345
```

常见返回值：

| 返回值 | 含义 | 排查方向 |
|---|---|---|
| `ENOENT` | 文件或目录不存在 | 路径拼错、工作目录不对、容器内没挂载 |
| `EACCES` | 权限不足 | 文件权限、目录执行权限、SELinux/AppArmor |
| `EPERM` | 操作被拒绝 | capabilities、`ptrace_scope`、安全策略 |
| `ENOSPC` | 空间不足 | 磁盘满、inode 满、配额满 |
| `EMFILE` | 打开文件数达到上限 | `ulimit -n`、fd 泄漏 |

加 `-y` 可以直接看到 fd 对应的真实路径：

```bash
strace -f -y -e trace=openat,read,write -p 12345
```

如果进程在容器里，`strace` 必须进入同一个 PID 命名空间：

```bash
# 从宿主机进入容器命名空间再跟踪
nsenter -t <容器PID> -p -m -- strace -f -p <容器内PID>
```

## 场景三：网络连接与 DNS 问题

```bash
strace -f -e trace=network -s 256 -p 12345
```

关注：

- `socket(AF_INET, SOCK_STREAM, ...)` 是否成功。
- `connect(...)` 的目标地址、端口、返回值；`ETIMEDOUT` 通常是链路/防火墙，`ECONNREFUSED` 是对端没监听。
- `sendto(...)` / `recvfrom(...)` 的地址和长度；UDP 服务要看是否发到了错误地址。
- `getaddrinfo` 不在 `trace=network` 里时，可加 `-e trace=network,openat`，或直接看 `/etc/resolv.conf`、`dig`。

```bash
# 只看网络相关，并统计耗时
strace -f -c -e trace=network -p 12345
```

## 场景四：统计哪类系统调用最耗时

```bash
strace -f -c -p 12345
# 运行 10 秒后 Ctrl-C，输出汇总表
```

输出会按耗时排序，适合快速判断是文件 I/O、网络、锁还是信号处理占大头。注意 `-c` 是**统计模式**，不会再逐行打印调用；要和逐行日志分开跑。

## 性能与安全注意点

- `strace` 会让被跟踪进程变慢，尤其是 `-f` 跟踪大量子进程时；生产环境尽量缩小 `-e trace=` 范围，并限制跟踪时间。
- 不要对高并发核心服务长时间全量跟踪，先 `-c` 统计，再针对可疑调用抓短片段。
- `ptrace` 默认受 `kernel.yama.ptrace_scope` 限制；普通用户附加别人的进程会报 `EPERM`，需要 root 或调整策略。
- 容器内进程可能被 seccomp 拦截 `ptrace`；必要时在宿主机命名空间内跟踪，而不是改容器安全配置。
- `strace` 输出可能包含密码、Token、文件内容片段；日志要按敏感信息处理，不要直接贴到公开渠道。

## 官方文档

- [strace 官网](https://strace.io/)
- [strace(1) man page](https://man7.org/linux/man-pages/man1/strace.1.html)
