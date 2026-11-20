---
title: "命令手册 · 磁盘与存储"
description: "不止查看检测：分区、格式化、挂载、LVM 扩缩容、修复、RAID 全套操作。"
---

# 磁盘与存储

### 容量与占用

::: cmd

| 命令 | 用途 |
|---|---|
| [df](./df) | 看磁盘分区还剩多少空间 |
| [du](./du) | 找是哪个目录把磁盘塞满了 |
| [ncdu](./ncdu) | 交互式磁盘占用 |
| [logrotate](./logrotate) | 日志轮转、压缩与清理 |

:::

### 块设备与健康

::: cmd

| 命令 | 用途 |
|---|---|
| [lsblk / blkid / findmnt](./lsblk-blkid-findmnt) | 块设备与挂载 |
| [nvme / xfs_info / hdparm](./nvme-xfs_info-hdparm) | 磁盘信息与调优 |
| [smartctl](./smartctl) | 磁盘健康检查与 SMART 预警 |

:::

### 分区与格式化

::: cmd

| 命令 | 用途 |
|---|---|
| [fdisk / parted / gdisk](./fdisk-parted-gdisk) | 分区 |
| [mkfs / mkswap](./mkfs) | 格式化 |
| [wipefs / partprobe](./wipefs-partprobe) | 清签名与刷新分区 |

:::

### 挂载与共享

::: cmd

| 命令 | 用途 |
|---|---|
| [mount / umount](./mount-umount) | 挂载卸载 |
| [/etc/fstab](./fstab) | 持久化挂载 |
| [NFS](./nfs) | 网络文件共享 |
| [mount.cifs](./cifs) | 挂载 Windows/SMB 共享 |

:::

### LVM

::: cmd

| 命令 | 用途 |
|---|---|
| [pvs / vgs / lvs](./lvm-view) | LVM 查看 |
| [pvcreate / vgcreate / lvcreate](./lvm-create) | LVM 创建 |
| [lvextend / vgextend / resize2fs / xfs_growfs](./lvm-extend) | LVM 扩容 |
| [lvreduce / lvremove / pvremove](./lvm-reduce) | LVM 缩容与移除 |

:::

### RAID、加密与多路径

::: cmd

| 命令 | 用途 |
|---|---|
| [mdadm](./mdadm) | 软 RAID |
| [cryptsetup](./cryptsetup) | LUKS 磁盘加密 |
| [iscsiadm / multipath](./iscsi-multipath) | iSCSI 与多路径 |

:::

### 修复、调优与交换

::: cmd

| 命令 | 用途 |
|---|---|
| [fsck / xfs_repair](./fsck-xfs_repair) | 文件系统修复 |
| [tune2fs / dumpe2fs](./tune2fs-dumpe2fs) | ext4 调优与查看 |
| [swapon / swapoff / mkswap](./swapon) | 交换空间 |

:::

### 底层复制

::: cmd

| 命令 | 用途 |
|---|---|
| [dd](./dd) | 底层复制与镜像 |

:::
