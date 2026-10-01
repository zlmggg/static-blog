---
category: Linux
difficulty: 高级
date: 2023-02-19
---

# 进程 D 状态不可中断、服务假死（2023-02-19）

## 现象

一台数据库服务器，业务卡住，SSH 登录上去后 `top` 里 CPU 很闲（idle 90%+），但 `load average` 高达 30+。

```
top - 15:30:00 up 10 days,  3:22,  1 user,  load average: 31.45, 28.12, 25.05
%Cpu(s):  3.5 us,  1.2 sy,  0.0 ni, 91.8 id,  3.5 wa,  0.0 hi,  0.0 si,  0.0 st
```

`ps aux` 看到一堆进程状态是 `D`（不可中断睡眠）：

```
ps aux | awk '$8 ~ /D/ {print}'
# mysql     1234  0.0  0.5 ... D  15:20   0:05 /usr/sbin/mysqld
# nginx     5678  0.0  0.1 ... D  15:22   0:00 nginx: worker
```

`kill -9` 这些 D 状态进程**杀不掉**：

```
kill -9 1234
# 没反应，进程还在
```

## 环境

- 发行版：Rocky Linux release 9.1 (Blue Onyx)
- 内核：`5.14.0-162.6.el9.x86_64`
- 业务：MySQL 8.0.32，数据目录在 NFS 挂载的 `/data` 上
- 存储：NFSv4 挂载到一台外部存储服务器

## 定位过程

### 1. 先确认 load 高是因为 D 状态而不是 CPU

```bash
vmstat 1 5
# procs -----------memory---------- ---swap-- -----io---- --system-- -----cpu-----
#  r  b   swpd   free  buff  cache   si   so    bi    bo   in   cs us sy id wa st
#  1 28      0  20000      0 800000   0    0 12000     5  200  10  1  1 90  8  0
```

`b` 列（阻塞在 D 状态的进程）28 个，`wa` 8%。load 高是因为这 28 个 D 进程在排队等 IO，不是 CPU 不够。

### 2. 找出 D 状态进程在等什么

```bash
ps -eo pid,stat,wchan:30,comm | awk '$2 ~ /D/'
# 1234 D nfs_wait_event            mysqld
# 5678 D nfs_wait_event            nginx
```

`wchan`（wait channel）显示 `nfs_wait_event`，说明这些进程卡在 NFS 上。

### 3. 看这些进程在等哪个文件/FD

```bash
# 找 D 状态进程打开的文件
ls -l /proc/1234/fd/ | grep -i nfs
# lrwx------ 1 mysql mysql 64 Feb 19 15:20 3 -> /data/mysql/ibdata1 (deleted)

# 看它的 IO 状态
cat /proc/1234/io
# read_bytes: ...
# write_bytes: ...
```

### 4. 确认 NFS 挂载状态

```bash
mount | grep nfs
# 192.168.1.10:/export/data on /data type nfs4 (rw,relatime,vers=4.1,...)

# 看 NFS 挂载是不是 hung
cat /proc/mounts | grep nfs
nfsstat -m
# Flags: rw,vers=4.1,rsize=1048576,wsize=1048576,namlen=255,hard,proto=tcp,timeo=600,retrans=2,...
```

注意 `hard` 挂载：NFS 服务器挂了之后，客户端所有访问这个挂载点的进程都会进入 D 状态，直到 NFS 恢复。这是 NFS 硬挂载的设计行为。

### 5. 确认 NFS 服务器是不是真挂了

```bash
ping -c 3 192.168.1.10
# PING 192.168.1.10: 56 data bytes
# --- 192.168.1.10 ping statistics ---
# 3 packets transmitted, 0 packets received, 100.0% packet loss
```

NFS 服务器网络不通了。

## 根因

NFS 存储服务器机房网络抖动，客户端用 `hard` 模式挂载 `/data`，所有读写 NFS 的系统调用都进入不可中断睡眠（D 状态），等 NFS 服务器恢复。这些 D 进程无法被 kill，导致 load average 飙高，业务假死。

## 解决步骤

### 1. 临时止血：恢复 NFS 连通

先把 NFS 服务器网络恢复：

```bash
# 在客户端上测试
showmount -e 192.168.1.10
ping 192.168.1.10
```

网络恢复后，D 状态进程会自动醒来，不需要 kill。

### 2. 如果 NFS 服务器一时半会恢复不了

**不要试图 kill -9 D 进程**，没用。两条路：

路 A：把挂载点 umount 掉（可能也会卡，因为文件系统 hung）：

```bash
# 软尝试卸载，不行就强制
umount /data
umount -f /data    # 强制，可能留下脏状态
umount -l /data    # lazy，立刻把挂载点从名字空间摘掉，IO 完成后再清理
```

`umount -l` 是救命招，能立刻让 shell 不卡，D 进程等 IO 返回后自动退出。

路 B：直接重启机器（最后手段）。

### 3. 彻底修复：改 NFS 挂载参数

把 `hard` 改成 `soft`，或者加 `intr`（虽然新内核 intr 已废弃，但 soft 模式有超时）：

`/etc/fstab`：

```
192.168.1.10:/export/data  /data  nfs  rw,soft,timeo=30,retrans=3,noresvport  0 0
```

`soft` 模式：NFS 请求超时后返回 IO 错误给应用，而不是无限等。代价是可能丢数据，但服务不会假死。

重要数据库目录不建议用 soft（可能导致数据文件损坏），建议：
- 业务数据目录用 hard + 监控 NFS 连通性
- 非关键目录用 soft

### 4. 监控 NFS 挂载健康

```bash
# 写个简单探针：每 10s 试一下读挂载点
timeout 5 ls /data/.healthcheck && echo OK || echo "NFS STALE"
```

## 验证与预防

- NFS 恢复后 `ps -eo stat | grep -c D` 回到 0。
- 监控补：D 状态进程数、NFS 挂载点可访问性、`mountstats`。
- 告警阈值：D 状态进程 > 0 持续 1 分钟就告警。
- 记住：**D 状态 = 进程在内核态等 IO，kill -9 杀不掉**，要么等 IO 完成，要么 `umount -l`，要么重启。

## 相关

- 命令速查：[Linux 命令速查](/reference/linux-commands)
- 存储方向：[NFS Stale file handle](/cases/t-nfs-stale-handle)
- CPU 方向：[CPU 飙高与 load average](/cases/t-cpu-high-load)
- 磁盘方向：[磁盘空间写满](/cases/t-disk-space-full)
