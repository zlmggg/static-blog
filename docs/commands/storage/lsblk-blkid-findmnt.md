---
title: "lsblk / blkid / findmnt · 块设备与挂载"
description: "lsblk 树状看磁盘/分区/LVM、blkid 看 UUID/文件系统、findmnt 看挂载关系。加盘/扩容前必看的三件套，中文详解。"
---

# lsblk / blkid / findmnt · 块设备与挂载

> 命令手册 · [磁盘与存储](/commands/storage/) ｜ 频率：每天用
> 加盘、扩容、排挂载问题，先 lsblk 看清磁盘→分区→LVM→挂载的层级，blkid 拿 UUID，findmnt 看挂载。

## 一句话用途

查看块设备层级、文件系统 UUID、挂载关系。

## 高频场景速查

```bash
lsblk                      # 树状看磁盘/分区/LVM/挂载点
lsblk -f                   # 含文件系统类型/UUID/挂载
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT,UUID   # 自定义列
blkid                      # 所有块的 UUID/类型
blkid /dev/sdb1            # 某分区 UUID
findmnt                    # 树状挂载关系
findmnt /data              # 某挂载点详情
findmnt -t xfs             # 按文件系统类型过滤
```

## lsblk 输出解读

```text
NAME        MAJ:MIN RM  SIZE RO TYPE MOUNTPOINT
sda           8:0    0  100G  0 disk
├─sda1        8:1    0    1G  0 part /boot
└─sda2        8:2    0   99G  0 part
  ├─rl-root 253:0    0   50G  0 lvm  /
  └─rl-swap 253:1    0    4G  0 lvm  [SWAP]
sdb           8:16   0  200G  0 disk           ← 新盘没分区没挂载
```

TYPE：disk 整盘 / part 分区 / lvm 逻辑卷 / rom 光驱。

## 三件套分工

| 命令 | 看什么 |
|---|---|
| `lsblk` | 设备层级与挂载点 |
| `blkid` | UUID 与文件系统类型（写 fstab 用） |
| `findmnt` | 挂载源/目标/选项（含 bind） |

::: tip 为什么用 UUID 不用 /dev/sdX
/dev/sdb 这类名字加盘/重启可能变，UUID 唯一稳定。/etc/fstab 用 UUID 挂载才可靠（[fstab](./fstab)）。
:::

## 运维实战

**加盘前确认**：`lsblk` 看新盘（如 sdb 无分区无挂载），别对已有数据的盘动手。
**拿 UUID 写 fstab**：`blkid /dev/sdb1` 取 UUID。
**排挂载**：`findmnt /data` 看实际挂载源与选项，确认是不是预期设备。

## 相关命令

[df](./df) · [du](./du) · [fdisk/parted](./fdisk-parted-gdisk) · [mount](./mount-umount) · [fstab](./fstab)

## 官方文档

- lsblk：<https://man7.org/linux/man-pages/man8/lsblk.8.html>
- blkid：<https://man7.org/linux/man-pages/man8/blkid.8.html>
- findmnt：<https://man7.org/linux/man-pages/man8/findmnt.8.html>