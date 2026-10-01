---
category: Linux
difficulty: 初级
date: 2020-11-03
---

# 磁盘空间写满（2020-11-03）

## 现象

一台应用服务器突然报错，业务写不进去：

```
java.io.IOException: No space left on device
```

或者 Nginx 报 `No space left on device`，PHP 报 `fopen: failed to open stream: No space left on device`。

登录上去 `df -h` 一看：

```
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda2        50G   50G     0 100% /
/dev/sda1       200M  120M   80M  60% /boot
```

但 `du -sh /*` 算出来的用量加起来远不到 50G，差了十几个 G。

## 环境

- 发行版：CentOS Linux release 7.8.2003 (Core)
- 内核：`3.10.0-1127.el7.x86_64`
- 业务：Nginx 1.16.1 + PHP-FPM 7.2.24，日志写到 `/var/log/nginx/`

## 定位过程

### 1. 先确认是哪个分区满了

```bash
df -hT
# Filesystem Type  Size  Used Avail Use%
# /dev/sda2   xfs   50G   50G    0 100% /
```

### 2. 从根目录逐层 du，找大目录

```bash
du -h --max-depth=1 / 2>/dev/null | sort -hr | head
du -h --max-depth=1 /var 2>/dev/null | sort -hr | head
du -h --max-depth=1 /var/log 2>/dev/null | sort -hr | head
```

本例中 `/var/log/nginx/` 下 `access.log` 已经涨到 18G。

### 3. 关键：df 与 du 对不上，一定是"已删除但被进程占用"的文件

这是最高频的坑。日志被 `rm` 删了，但 nginx 进程还持有 fd，空间不会释放：

```bash
lsof -nP +L1 / | head
# 或
lsof | grep deleted
```

典型输出：

```
nginx    1234  www   11w  REG  253,2 18874368000  1234567 /var/log/nginx/access.log (deleted)
```

`+L1` 表示列出链接数小于 1 的文件（即已被 unlink 但还被打开的）。

### 4. 确认大文件是不是日志暴涨

```bash
# 实时看哪些文件在被疯狂写入
du -sh /var/log/nginx/*
tail -f /var/log/nginx/access.log   # 看是不是访问量暴增
```

## 根因

业务上线后没配 logrotate，Nginx 的 `access.log` 三个月没切，从 0 涨到 18G 把根分区写满。
事后有人 `rm` 了日志想腾空间，但 nginx 没 reload，fd 没释放，`df` 仍然显示 100%。

## 解决步骤

### 1. 临时止血：释放已删除文件占用的空间

**不要重启 nginx**（重启会丢现场），用下面两种方式之一：

方式 A：清空 fd 指向的文件内容（不删 fd，立刻释放空间）：

```bash
# 找到占用 deleted 文件的 PID 和 fd 号
ls -l /proc/1234/fd/ | grep deleted
# 假设是 fd 11
> /proc/1234/fd/11
```

方式 B：reload 进程，让它重新打开日志文件：

```bash
nginx -s reload
# 或
systemctl reload nginx
```

reload 后 nginx 会重新打开 access.log，旧的 fd 关闭，空间立刻释放。

### 2. 如果是真的日志暴涨，先砍日志

```bash
# 不要直接 rm，用 truncate 清空（保持 inode，进程不丢 fd）
truncate -s 0 /var/log/nginx/access.log
```

### 3. 彻底修复：配 logrotate

`/etc/logrotate.d/nginx`：

```
/var/log/nginx/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 nginx adm
    sharedscripts
    postrotate
        [ -f /var/run/nginx.pid ] && kill -USR1 `cat /var/run/nginx.pid`
    endscript
}
```

测试一下：

```bash
logrotate -d /etc/logrotate.d/nginx   # -d 干跑，不真执行
```

### 4. 给日志目录单独分区（建议）

以后 `/var/log` 单独挂一个分区，日志再涨也写满不了根分区，系统还能跑。

## 验证与预防

- 修复后 `df -h /` 看 Avail 恢复正常，`lsof +L1` 没有大文件残留。
- 监控补：磁盘使用率（`df`）、inode 使用率（`df -i`）、日志目录增长率。
- 告警阈值：磁盘使用 > 80% 预警，> 90% 紧急告警。
- 记住：**清日志用 `truncate -s 0`，不要用 `rm`**；`rm` 之后一定要 reload 进程。

## 相关

- 命令速查：[Linux 命令速查](/reference/linux-commands)
- Inode 方向：[inode 耗尽问题](/cases/t-inode-exhausted)
- 文件句柄方向：[Too many open files](/cases/t-too-many-open-files)
- 巡检清单：[运维巡检清单](/reference/ops-checklists)
