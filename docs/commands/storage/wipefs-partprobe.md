---
title: "wipefs / partprobe · 清签名与刷新分区"
description: "wipefs 擦除文件系统/RAID/LVM 签名（复用旧盘必做）、partprobe 刷新内核分区表不重启。操作变更类，中文详解。"
---

# wipefs / partprobe · 清签名与刷新分区

> 命令手册 · [磁盘与存储](/commands/storage/) ｜ 频率：很少用
> 旧盘复用前清掉残留的文件系统/LVM/RAID 签名，否则新工具误判。改了分区表用 partprobe 让内核重读。

## 一句话用途

擦除设备上的旧文件系统签名；通知内核重读分区表。

## 高频场景速查

```bash
sudo wipefs /dev/sdb               # 看有哪些签名（不擦）
sudo wipefs -a /dev/sdb            # 擦除所有签名
sudo wipefs -a /dev/sdb1           # 擦某分区签名
sudo partprobe /dev/sdb            # 刷新内核分区表
sudo partprobe                     # 刷新所有
sudo blockdev --rereadpt /dev/sdb  # 另一种重读分区表
```

## 为什么需要 wipefs

旧盘上有 ext4/xfs/LVM/RAID 签名残留，直接 pvcreate/mkfs 可能报 "existing signature" 或工具误识别。wipefs -a 清干净再操作。

::: danger wipefs -a 不可逆
擦签名后原文件系统不可挂载（数据虽在但元信息没了）。确认是要复用的盘。擦前 wipefs（不带 -a）先看有什么签名。
:::

## partprobe 何时用

fdisk/parted 改分区后，内核可能没立即识别新分区（/dev/sdb1 不出现）。partprobe 通知内核重读，不用重启。

## 运维实战

**旧盘做 LVM**：`wipefs -a /dev/sdb` → pvcreate → vgcreate。
**分区后设备没出现**：partprobe /dev/sdb，再 lsblk 确认。
**彻底清盘**：wipefs -a 清签名 + dd 清头部（[dd](./dd)），确保无残留。

## 相关命令

[fdisk/parted](./fdisk-parted-gdisk) · [lsblk](./lsblk-blkid-findmnt) · [lvm-create](./lvm-create) · [mkfs](./mkfs) · [dd](./dd)

## 官方文档

- wipefs：<https://man7.org/linux/man-pages/man8/wipefs.8.html>
- partprobe：<https://man7.org/linux/man-pages/man8/partprobe.8.html>