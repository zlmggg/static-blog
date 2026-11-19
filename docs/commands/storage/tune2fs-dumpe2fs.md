---
title: "tune2fs / dumpe2fs · ext4 调优与查看"
description: "dumpe2fs 看 ext4 超级块/inode、tune2fs 调保留块/挂载次数/标签、-l 看参数。ext4 文件系统管理，中文详解。"
---

# tune2fs / dumpe2fs · ext4 调优与查看

> 命令手册 · [磁盘与存储](/commands/storage/) ｜ 频率：很少用
> ext4 文件系统的元信息与可调参数。保留块太多浪费空间、挂载次数触发强制 fsck——tune2fs 调。

## 一句话用途

查看与调整 ext4 文件系统参数。

## 高频场景速查

```bash
sudo dumpe2fs -h /dev/sdb1         # 看超级块摘要（inode/块/保留）
sudo tune2fs -l /dev/sdb1          # 看可调参数
sudo tune2fs -m 1 /dev/sdb1        # 保留块改为 1%（默认5%）
sudo tune2fs -L data /dev/sdb1     # 设卷标
sudo tune2fs -c 0 -i 0 /dev/sdb1   # 禁用挂载次数/时间触发的强制 fsck
sudo tune2fs -o journal_data_writeback /dev/sdb1   # 日志模式
```

## 关键参数

| 参数 | 含义 |
|---|---|
| `-m N` | 保留块百分比（root 专用） |
| `-L 标签` | 卷标 |
| `-c N` | N 次挂载后强制 fsck（0禁用） |
| `-i 间隔` | 时间触发 fsck（0禁用） |
| `-l` | 列出参数 |
| `-O 特性` | 启用特性（如 has_journal） |

## 看什么（dumpe2fs -h）

- Block count / Free blocks：总块/空闲。
- Inode count / Free inodes：inode 总量/空闲（小文件多易耗尽）。
- Reserved block count：保留块（默认5%，数据盘可调1%省空间）。
- Filesystem state：clean / not clean。

## 运维实战

**大数据盘省空间**：`tune2fs -m 1` 把保留块从5%降到1%，100G 盘省4G（保留块只 root 能用，数据盘没必要留5%）。
**禁强制 fsck**：大盤每次挂载计数 fsck 很慢，`-c 0 -i 0` 禁用（仍需定期手动维护）。
**排 inode 耗尽**：dumpe2fs 看 Free inodes=0，[df -i](./df) 确认，清理小文件或重建调大 inode。

## 相关命令

[df](./df) · [mkfs](./mkfs) · [fsck](./fsck-xfs_repair) · [lsblk](./lsblk-blkid-findmnt)

## 官方文档

- tune2fs：<https://man7.org/linux/man-pages/man8/tune2fs.8.html>
- dumpe2fs：<https://man7.org/linux/man-pages/man8/dumpe2fs.8.html>