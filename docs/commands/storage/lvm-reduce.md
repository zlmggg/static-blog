---
title: "lvreduce / lvremove / pvremove · LVM 缩容与移除"
description: "LVM 缩容（ext4 可缩 xfs 不可）、先缩文件系统再缩 LV 的顺序、lvremove/vgremove/pvremove 移除。高危操作，中文详解。"
---

# LVM 缩容与移除 · lvreduce / lvremove / pvremove

> 命令手册 · [磁盘与存储](/commands/storage/) ｜ 频率：很少用
> 扩容常见，缩容危险。xfs 不能缩，ext4 能缩但顺序错了丢数据。移除卷也要按序。

## 一句话用途

缩小逻辑卷、移除 LV/VG/PV。

## ext4 缩容流程（顺序关键）

```bash
sudo umount /data                      # 1. 卸载（ext4 缩容需离线）
sudo e2fsck -f /dev/datavg/datalv      # 2. 强制检查
sudo resize2fs /dev/datavg/datalv 50G  # 3. 先缩文件系统到 50G
sudo lvreduce -L 50G /dev/datavg/datalv   # 4. 再缩 LV 到 50G
sudo mount /dev/datavg/datalv /data    # 5. 重挂
```

::: danger 顺序：先文件系统后 LV
缩容必须**先 resize2fs 缩文件系统，再 lvreduce 缩 LV**。反过来（先缩 LV）会截断文件系统尾部数据，直接损坏。扩容则相反（先 LV 后文件系统）。**xfs 不支持缩容**，只能备份→重建小卷→恢复。
:::

## 移除流程（从上层往下）

```bash
sudo umount /data
sudo lvremove /dev/datavg/datalv       # 删 LV
sudo vgremove datavg                   # 删 VG（需先删/移走所有 LV）
sudo pvremove /dev/sdb                 # 清 PV 标记
```

## 参数详解

| 命令 | 含义 |
|---|---|
| `lvreduce -L 大小` | 缩 LV（-L -10G 减10G） |
| `lvremove LV` | 删 LV |
| `vgremove VG` | 删 VG |
| `pvremove PV` | 清 PV 标签 |
| `vgreduce VG PV` | 从 VG 移除某 PV（需先 pvmove 迁数据） |

## 运维实战

**换盘迁数据**：`pvmove /dev/sdb` 把数据迁到其他 PV → `vgreduce datavg /dev/sdb` → `pvremove /dev/sdb`，安全拔盘。
**清理测试卷**：lvremove→vgremove→pvremove 逐层清。
**缩容评估**：xfs 直接放弃缩容念头，备份重建。

## 相关命令

[lvm-view](./lvm-view) · [lvm-extend](./lvm-extend) · [fsck](./fsck-xfs_repair) · [mkfs](./mkfs) · [wipefs](./wipefs-partprobe)

## 官方文档

- lvreduce：<https://man7.org/linux/man-pages/man8/lvreduce.8.html>
- pvmove：<https://man7.org/linux/man-pages/man8/pvmove.8.html>