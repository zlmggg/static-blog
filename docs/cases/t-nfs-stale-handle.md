---
category: 服务
difficulty: 中级
date: 2019-06-28
---

# NFS Stale file handle 与挂载点卡死（2019-06-28）

## 现象

服务器上访问 NFS 挂载目录报错：

```bash
ls /data
# ls: cannot access /data: Stale file handle
```

或者：

```bash
cat /data/file.txt
# cat: /data/file.txt: Stale file handle
```

更严重的是：shell `cd /data` 后就卡住，`ls` 都敲不动，`Ctrl+C` 也退不出来。

## 环境

- 发行版：CentOS Linux release 7.6.1810 (Core)
- 内核：`3.10.0-957.el7.x86_64`
- NFS 服务器：`192.168.1.10:/export/data`，NFSv4
- 客户端挂载：`/etc/fstab` 里 `hard` 挂载

## 定位过程

### 1. 先看挂载状态

```bash
mount | grep nfs
# 192.168.1.10:/export/data on /data type nfs4 (rw,relatime,vers=4.1,hard,proto=tcp,timeo=600)
```

`hard` 挂载：NFS 服务器挂了，客户端进程会无限等待。

### 2. 看 NFS 服务器通不通

```bash
ping -c 3 192.168.1.10
showmount -e 192.168.1.10
# 如果 showmount 也卡，说明 NFS 服务没了
```

### 3. Stale file handle 的含义

NFS 客户端缓存了文件句柄（inode 引用）。如果 NFS 服务器上：
- 文件被删了
- 服务器重启后文件系统恢复到旧快照
- 服务器重装/导出路径变了

客户端再拿着旧句柄访问，服务器说"这个句柄我不认识"，就返回 `Stale file handle`。

### 4. 看进程是不是卡在 D 状态

```bash
ps -eo pid,stat,wchan,comm | awk '$2 ~ /D/'
# 1234 D nfs_wait_event ls
```

如果一堆 D 状态进程，参考 [D 状态假死](/cases/t-process-d-state-hang)。

## 解决步骤

### 1. 临时止血：先恢复 NFS 服务器

```bash
# 在 NFS 服务器上
systemctl status nfs-server
# 如果挂了，重启
systemctl restart nfs-server
```

服务器恢复后，`Stale file handle` 可能还在（因为句柄缓存），需要重新挂载。

### 2. 重新挂载

```bash
# 先尝试普通卸载
umount /data

# 如果 umount 卡住（因为有 D 状态进程占着），用 lazy umount
umount -l /data

# 重新挂载
mount /data
# 或
mount -a
```

`umount -l` 是救命命令：立刻把挂载点从名字空间摘掉，shell 立刻不卡，D 进程等 IO 返回后自动退出。

### 3. 如果 lazy umount 也不行

```bash
# 看看谁在占
lsof /data
fuser -m /data

# 杀掉占用进程（D 状态杀不掉，只能等）
# 最后手段：重启机器
```

### 4. 彻底修复：改挂载参数

`/etc/fstab`：

```
192.168.1.10:/export/data  /data  nfs  rw,soft,timeo=30,retrans=3,noresvport,_netdev  0 0
```

| 参数 | hard（默认） | soft |
|---|---|---|
| NFS 挂了 | 进程无限等（D 状态） | 超时后返回 IO 错误 |
| 适合 | 数据库等关键数据 | 非关键共享文件 |
| 风险 | 服务假死 | 可能丢未写完的数据 |

- 关键数据目录用 `hard` + 监控 NFS 连通性。
- 非关键目录用 `soft`，避免假死。

### 5. 用 autofs 自动挂载

不是所有服务器都需要 7×24 挂 NFS，用 autofs 按需挂载，NFS 挂了也不影响启动。

## 验证与预防

- `ls /data` 正常列出文件。
- `mount | grep nfs` 正常。
- 监控补：NFS 挂载点可访问性（`timeout 5 ls /data/.healthcheck`）。
- 告警阈值：NFS 不可达立刻告警。
- 记住：**Stale file handle = 重新挂载；shell 卡死 = umount -l；不要 kill -9 D 进程**。

## 相关

- 命令速查：[网络命令速查](/reference/network-commands)
- 进程方向：[D 状态不可中断假死](/cases/t-process-d-state-hang)
- 网络方向：[MTU 黑洞](/cases/t-mtu-black-hole)
- 巡检清单：[运维巡检清单](/reference/ops-checklists)
