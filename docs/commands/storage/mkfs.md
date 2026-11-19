---
title: "mkfs / mkswap · 格式化"
description: "mkfs.ext4/mkfs.xfs 建文件系统、-L 标签/-N inode、mkswap 建交换。xfs 与 ext4 选型，操作变更类，中文详解。"
---

# mkfs / mkswap · 格式化

> 命令手册 · [磁盘与存储](/commands/storage/) ｜ 频率：偶尔用
> 分区后建文件系统才能存数据。RHEL 默认 xfs，Debian 常用 ext4。格式化会清空分区数据。

## 一句话用途

在分区/逻辑卷上创建文件系统（格式化），或创建 swap。

## 高频场景速查

```bash
sudo mkfs.xfs /dev/sdb1              # 格式化为 xfs
sudo mkfs.ext4 /dev/sdb1             # 格式化为 ext4
sudo mkfs.xfs -L data /dev/sdb1      # 带标签
sudo mkfs.ext4 -L data -m 1 /dev/sdb1   # 标签+保留块1%（默认5%）
sudo mkswap /dev/sdb2                # 建 swap
sudo swapon /dev/sdb2                # 启用（见 swapon）
```

## xfs vs ext4

| | xfs | ext4 |
|---|---|---|
| 默认 | RHEL/Rocky | Debian/Ubuntu |
| 扩容 | 在线扩（xfs_growfs） | 在线扩（resize2fs） |
| **缩容** | **不支持** | 支持（需卸载） |
| 大文件/并发 | 强 | 良好 |
| 修复 | xfs_repair | fsck |

::: warning xfs 不能缩
xfs 只能扩不能缩。要缩容选 ext4，或备份→重建→恢复。规划时想清楚，别选了 xfs 又要缩。
:::

## 参数详解

### mkfs.ext4

| 参数 | 含义 |
|---|---|
| `-L 标签` | 卷标 |
| `-m N` | 保留块百分比（数据盘可调1） |
| `-N 数` | inode 数量（海量小文件需调大） |
| `-T largefile` | 大文件优化 |

### mkfs.xfs

| 参数 | 含义 |
|---|---|
| `-L 标签` | 卷标 |
| `-f` | 强制（覆盖已有文件系统） |
| `-d agcount=N` | 分配组数 |

## 运维实战

**数据盘格式化**：`mkfs.xfs -L data /dev/sdb1`，标签便于识别。
**海量小文件**：ext4 调大 inode（`-N` 或 `-i 4096`），否则 inode 耗尽"磁盘满"但空间还有（[df -i](./df)）。
**数据库盘**：xfs 并发性能好，常用。

## 相关命令

[fdisk/parted](./fdisk-parted-gdisk) · [mount](./mount-umount) · [fstab](./fstab) · [swapon](./swapon) · [fsck/xfs_repair](./fsck-xfs_repair)

## 官方文档

- mkfs.xfs：<https://man7.org/linux/man-pages/man8/mkfs.xfs.8.html>
- mkfs.ext4：<https://man7.org/linux/man-pages/man8/mke2fs.8.html>