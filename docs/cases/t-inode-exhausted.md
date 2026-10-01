---
category: Linux
difficulty: 初级
date: 2019-09-15
---

# inode 耗尽：df 有空间但写不进去（2019-09-15）

## 现象

服务器磁盘明明还有空间，但是创建文件时报错：

```
touch: cannot touch 'test.txt': No space left on device
```

`df -h` 看根分区还有 40% 可用：

```
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda2        50G   28G   22G  57% /
```

经典的"空间有，inode 没了"。

## 环境

- 发行版：CentOS Linux release 7.6.1810 (Core)
- 内核：`3.10.0-957.el7.x86_64`
- 文件系统：XFS，根分区默认 inode 密度

## 定位过程

### 1. 先看 inode 使用率

```bash
df -i
```

输出关键看最后一列 `IUse%`：

```
Filesystem      Inodes  IUsed  IFree IUse% Mounted on
/dev/sda2      3276800 3276800      0  100% /
```

`IFree=0`，inode 真的耗尽了。XFS/ext4 创建文件时都要分配一个 inode，inode 用完即使磁盘块还有空也写不进去。

### 2. 找出哪个目录下小文件最多

```bash
# 从根目录逐层统计文件数
for i in /*; do echo "=== $i ==="; ls "$i" 2>/dev/null | wc -l; done
```

然后进入可疑目录继续往下钻：

```bash
# 统计 /var 下一级目录各有多少文件
for d in /var/*/; do echo "$(find $d -maxdepth 1 | wc -l) $d"; done | sort -rn | head
```

本例中 `/var/spool/postfix/maildrop/` 下有 200 多万个小文件。

### 3. 确认是不是邮件队列爆了

```bash
ls /var/spool/postfix/maildrop/ | wc -l
# 2103842
```

这是 CentOS 上的经典坑：crond 执行脚本时输出了一些内容，但系统没装 local MTA 或 MTA 配置错，postfix 就把邮件堆在 maildrop 队列里，每个任务每次产生一个小文件。

## 根因

服务器上跑了大量 crontab 任务，脚本执行后有 stdout/stderr 输出，crond 默认会把这些输出邮寄给 root。但 postfix 配置错误（relay 失败），邮件发不出去也退不掉，全部堆积在 `/var/spool/postfix/maildrop/`，几百万个 4 字节小文件把 inode 吃光了。

## 解决步骤

### 1. 临时止血：清空 maildrop 队列

```bash
# 先停 postfix，防止一边删一边写
systemctl stop postfix

# 清空堆积的邮件
find /var/spool/postfix/maildrop/ -type f -delete

# 确认 inode 释放
df -i /
```

文件多的时候直接 `rm -rf` 可能会卡住，用 `find -delete` 或 `rsync --delete` 更快：

```bash
# 备选：用 rsync 清空大目录（比 rm -rf 快）
mkdir /tmp/empty_dir
rsync -a --delete /tmp/empty_dir/ /var/spool/postfix/maildrop/
```

### 2. 彻底修复：让 crontab 不再发邮件

方法 A：在 crontab 里把输出重定向掉：

```bash
# 编辑 /etc/crontab 或某个用户的 crontab
# 把命令末尾加 >/dev/null 2>&1
# 例如：
* * * * * /path/to/script.sh >/dev/null 2>&1
```

方法 B：在 crontab 顶部加 `MAILTO=""`，全局关闭邮件通知：

```crontab
MAILTO=""
*/5 * * * * /path/to/script.sh
```

方法 C：修复 postfix，让它能正常发邮件或正确退信。

### 3. 检查还有没有别的地方在产生海量小文件

```bash
# 全文件系统扫一遍，找出文件数最多的目录
find / -xdev -type f 2>/dev/null | awk -F/ '{print $2}' | sort | uniq -c | sort -rn | head
```

重点关注：
- `/var/spool/postfix/maildrop/`（邮件队列）
- `/tmp/`（程序临时文件没清理）
- 应用的 session 目录（PHP `/var/lib/php/session/`）
- 应用的缓存目录

## 验证与预防

- `df -i /` 确认 IFree 恢复到合理数量。
- 监控补：inode 使用率（`df -i`），不要只监控磁盘块使用率。
- 告警阈值：inode 使用 > 80% 预警。
- 记住：**`No space left on device` 不一定是磁盘满了，先 `df -h` 再 `df -i`**。

## 相关

- 命令速查：[Linux 命令速查](/reference/linux-commands)
- 磁盘方向：[磁盘空间写满](/cases/t-disk-space-full)
- 文件句柄方向：[Too many open files](/cases/t-too-many-open-files)
- 巡检清单：[运维巡检清单](/reference/ops-checklists)
