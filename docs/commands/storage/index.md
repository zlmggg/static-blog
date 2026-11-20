---
title: "命令手册 · 磁盘与存储"
description: "不止查看检测：分区、格式化、挂载、LVM 扩缩容、修复、RAID 全套操作。"
---

# 磁盘与存储

> 命令手册 · [返回总览](/commands/) ｜ 本组 25 个页面，按功能分类

## 功能

磁盘命令分两类动作：一类是"看"（df/du/lsblk/smartctl/iostat），一类是"改"（fdisk/parted 分区、mkfs 格式化、mount/fstab 挂载、LVM 扩缩容、fsck 修复）。运维不只看得懂容量，还要敢动手扩容、换盘、修文件系统。"磁盘满了"和"加块盘"是两种完全不同的工作，本组都覆盖。

## 类别

### 容量与占用

| 命令 | 用途 |
|---|---|
| [df](./df) | 看磁盘分区还剩多少空间 |
| [du](./du) | 找是哪个目录把磁盘塞满了 |
| [ncdu](./ncdu) | 交互式磁盘占用 |
| [logrotate](./logrotate) | 日志轮转、压缩与清理 |

### 块设备与健康

| 命令 | 用途 |
|---|---|
| [lsblk-blkid-findmnt](./lsblk-blkid-findmnt) | 块设备与挂载 |
| [nvme-xfs_info-hdparm](./nvme-xfs_info-hdparm) | 磁盘信息与调优 |
| [smartctl](./smartctl) | 磁盘健康检查与 SMART 预警 |

### 分区与格式化

| 命令 | 用途 |
|---|---|
| [fdisk-parted-gdisk](./fdisk-parted-gdisk) | 分区 |
| [mkfs](./mkfs) | 格式化 |
| [wipefs-partprobe](./wipefs-partprobe) | 清签名与刷新分区 |

### 挂载与共享

| 命令 | 用途 |
|---|---|
| [mount-umount](./mount-umount) | 挂载卸载 |
| [fstab](./fstab) | 持久化挂载 |
| [nfs](./nfs) | 网络文件共享 |
| [cifs](./cifs) | 挂载 Windows/SMB 共享 |

### LVM

| 命令 | 用途 |
|---|---|
| [lvm-view](./lvm-view) | LVM 查看 |
| [lvm-create](./lvm-create) | LVM 创建 |
| [lvm-extend](./lvm-extend) | LVM 扩容 |
| [lvm-reduce](./lvm-reduce) | LVM 缩容与移除 |

### RAID、加密与多路径

| 命令 | 用途 |
|---|---|
| [mdadm](./mdadm) | 软 RAID |
| [cryptsetup](./cryptsetup) | LUKS 磁盘加密 |
| [iscsi-multipath](./iscsi-multipath) | iSCSI 与多路径 |

### 修复、调优与交换

| 命令 | 用途 |
|---|---|
| [fsck-xfs_repair](./fsck-xfs_repair) | 文件系统修复 |
| [tune2fs-dumpe2fs](./tune2fs-dumpe2fs) | ext4 调优与查看 |
| [swapon](./swapon) | 交换空间 |

### 底层复制

| 命令 | 用途 |
|---|---|
| [dd](./dd) | 底层复制与镜像 |

::: tip 组织原则
同族命令合并成一页，一条命令只有一个主页；跨组场景用链接指向对应分组。
:::
