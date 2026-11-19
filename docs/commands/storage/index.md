---
title: "命令手册 · 磁盘与存储"
description: "不止查看检测：分区、格式化、挂载、LVM 扩缩容、修复、RAID 全套操作。"
---

# 磁盘与存储

> 命令手册分组 · 返回 [命令手册总览](/commands/)
> 不止查看检测：分区、格式化、挂载、LVM 扩缩容、修复、RAID 全套操作。

## 这类命令解决什么

磁盘命令分两类动作：一类是"看"（df/du/lsblk/smartctl/iostat），一类是"改"（fdisk/parted 分区、mkfs 格式化、mount/fstab 挂载、LVM 扩缩容、fsck 修复）。运维不只看得懂容量，还要敢动手扩容、换盘、修文件系统。"磁盘满了"和"加块盘"是两种完全不同的工作，本组都覆盖。

## 学习顺序（入门 → 高级）

1. df / du / lsblk（先看容量与块设备）
2. fdisk / parted / mkfs（分区与格式化）
3. mount / umount / fstab（挂载与持久化）
4. pvs / vgs / lvs + lvextend（LVM 扩容）
5. fsck / xfs_repair（修复）
6. smartctl / iostat（健康与 IO）

## 本组命令

### 已就绪

- [cifs](./cifs)
- [cryptsetup](./cryptsetup)
- [dd](./dd)
- [df](./df)
- [du](./du)
- [fdisk-parted-gdisk](./fdisk-parted-gdisk)
- [fsck-xfs_repair](./fsck-xfs_repair)
- [fstab](./fstab)
- [iscsi-multipath](./iscsi-multipath)
- [logrotate](./logrotate)
- [lsblk-blkid-findmnt](./lsblk-blkid-findmnt)
- [lvm-create](./lvm-create)
- [lvm-extend](./lvm-extend)
- [lvm-reduce](./lvm-reduce)
- [lvm-view](./lvm-view)
- [mdadm](./mdadm)
- [mkfs](./mkfs)
- [mount-umount](./mount-umount)
- [ncdu](./ncdu)
- [nfs](./nfs)
- [nvme-xfs_info-hdparm](./nvme-xfs_info-hdparm)
- [smartctl](./smartctl)
- [swapon](./swapon)
- [tune2fs-dumpe2fs](./tune2fs-dumpe2fs)
- [wipefs-partprobe](./wipefs-partprobe)

### 规划中（待编写）

`df`、`du`、`lsblk`、`blkid`、`findmnt`、`smartctl`、`iostat`、`ncdu`、`nvme`、`xfs_info`、`hdparm`、`lsscsi`、`fdisk`、`parted`、`gdisk`、`mkfs.ext4 / mkfs.xfs`、`mkswap`、`partprobe`、`wipefs`、`cryptsetup`、`mount`、`umount`、`/etc/fstab`、`swapon / swapoff`、`pvs / vgs / lvs`、`pvcreate / vgcreate / lvcreate`、`lvextend / vgextend`、`resize2fs / xfs_growfs`、`lvreduce / lvremove / pvremove`、`fsck`、`xfs_repair`、`tune2fs / dumpe2fs`、`dd`、`mdadm`、`mount.nfs / showmount`、`mount.cifs`、`exportfs`、`iscsiadm`、`multipath`、`logrotate`

::: tip 覆盖与组织原则
查看检测与操作变更并重；同族命令合并成页（如 fdisk/parted/gdisk → 分区工具）；一条命令只有一个主页，跨组互链。
:::

## 命令页模板

一句话用途 + 频率标记 → 高频场景速查（中文，复制即用）→ 参数详解（`--help` 全量中文化，按"每天用 / 偶尔用 / 很少用"分级，标易错点）→ 运维实战示例 → 相关命令 + 官方文档完整链接。
