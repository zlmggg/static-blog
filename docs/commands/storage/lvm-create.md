---
title: "pvcreate / vgcreate / lvcreate · LVM 创建"
description: "LVM 从零搭建：pvcreate 初始化物理卷、vgcreate 建卷组、lvcreate 切逻辑卷（-L 大小/-l 百分比/-n 名）。操作变更类，中文详解。"
---

# pvcreate / vgcreate / lvcreate · LVM 创建

> 命令手册 · [磁盘与存储](/commands/storage/) ｜ 频率：偶尔用
> 新盘做 LVM：初始化 PV → 建 VG → 切 LV → 格式化挂载。一步步来。

## 一句话用途

把磁盘初始化成 LVM 物理卷，组建卷组，切出逻辑卷。

## 高频场景速查（完整流程）

```bash
# 1. 初始化物理卷（整盘或分区）
sudo pvcreate /dev/sdb /dev/sdc

# 2. 建卷组（把 PV 汇成池）
sudo vgcreate datavg /dev/sdb /dev/sdc

# 3. 切逻辑卷
sudo lvcreate -L 100G -n datalv datavg          # 指定大小
sudo lvcreate -l 100%FREE -n datalv datavg      # 用尽 VG 剩余

# 4. 格式化 + 挂载
sudo mkfs.xfs /dev/datavg/datalv
sudo mkdir /data && sudo mount /dev/datavg/datalv /data
# 5. 写 fstab 持久化
```

## 参数详解

### pvcreate

| 参数 | 含义 |
|---|---|
| `pvcreate /dev/sdX` | 初始化（会清盘上数据） |
| `-f` | 强制 |

### vgcreate

| 参数 | 含义 |
|---|---|
| `vgcreate 名 PV...` | 建卷组 |
| `-s 大小` | PE 大小（默认4M） |

### lvcreate

| 参数 | 含义 |
|---|---|
| `-L 大小` | 指定容量（100G） |
| `-l N%FREE` | 按 VG 剩余百分比 |
| `-l N%VG` | 按 VG 总量百分比 |
| `-n 名` | LV 名 |
| `-i N` | 条带数（跨 PV 并行） |
| `-s` | 快照 |

## 运维实战

**两盘合一池**：pvcreate 两盘 → vgcreate 合并 → lvcreate 切大卷，容量灵活分配。
**用尽剩余**：`-l 100%FREE` 把 VG 剩余全给一个 LV。
**条带提升性能**：`-i 2 -I 64` 跨两 PV 条带，类似 RAID0 提速（无冗余）。

::: danger pvcreate 会清数据
对已有文件系统/数据的盘 pvcreate 会破坏。确认是空盘。LV 设备路径 /dev/VG名/LV名 或 /dev/mapper/VG-LV。
:::

## 相关命令

[lvm-view](./lvm-view) · [lvm-extend](./lvm-extend) · [mkfs](./mkfs) · [fstab](./fstab) · [fdisk](./fdisk-parted-gdisk)

## 官方文档

- pvcreate：<https://man7.org/linux/man-pages/man8/pvcreate.8.html>
- vgcreate：<https://man7.org/linux/man-pages/man8/vgcreate.8.html>
- lvcreate：<https://man7.org/linux/man-pages/man8/lvcreate.8.html>