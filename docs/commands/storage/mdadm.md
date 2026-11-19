---
title: "mdadm · 软 RAID"
description: "mdadm 建/管软 RAID（0/1/5/10）、--create/--detail/--manage、坏盘替换与重建。无硬件 RAID 卡时的冗余方案，中文详解。"
---

# mdadm · 软 RAID

> 命令手册 · [磁盘与存储](/commands/storage/) ｜ 频率：很少用
> 没有硬件 RAID 卡，用 Linux 软 RAID 做冗余/提速。mdadm 管理 RAID 阵列。

## 一句话用途

创建和管理 Linux 软件 RAID 阵列。

## RAID 级别

| 级别 | 特点 | 最少盘 | 容错 |
|---|---|---|---|
| 0 | 条带提速 | 2 | 无（坏一盘全丢） |
| 1 | 镜像 | 2 | 坏1盘 |
| 5 | 条带+分布校验 | 3 | 坏1盘 |
| 6 | 双校验 | 4 | 坏2盘 |
| 10 | 镜像+条带 | 4 | 每组坏1盘 |

## 高频场景速查

```bash
# 建 RAID1
sudo mdadm --create /dev/md0 --level=1 --raid-devices=2 /dev/sdb /dev/sdc
cat /proc/mdstat                     # 看阵列与重建进度
sudo mdadm --detail /dev/md0         # 阵列详情
# 保存配置
sudo mdadm --detail --scan | sudo tee -a /etc/mdadm.conf
# 格式化挂载（在 md0 上）
sudo mkfs.xfs /dev/md0 && sudo mount /dev/md0 /data
```

## 坏盘替换

```bash
sudo mdadm --manage /dev/md0 --fail /dev/sdb --remove /dev/sdb   # 标记坏盘移除
# 换新盘后
sudo mdadm --manage /dev/md0 --add /dev/sdd                      # 加入重建
cat /proc/mdstat                     # 看 rebuild 进度
```

## 运维实战

**系统盘 RAID1**：两块盘镜像，坏一块不宕机。
**数据盘 RAID5/10**：容量与冗余平衡，RAID10 性能更好。
**监控重建**：/proc/mdstat 看 rebuild%，重建期间性能下降、再坏盘可能丢数据（RAID5）。

::: danger RAID 不是备份
RAID 防硬件坏盘，不防误删/勒索/逻辑错误。重要数据仍需独立备份。RAID5 重建时再坏一盘就全丢，大盤建议 RAID6/10。
:::

## 相关命令

[lsblk](./lsblk-blkid-findmnt) · [smartctl](./smartctl) · [mkfs](./mkfs) · [lvm-create](./lvm-create) · [dd](./dd)

## 官方文档

- mdadm：<https://man7.org/linux/man-pages/man8/mdadm.8.html>
- md：<https://man7.org/linux/man-pages/man4/md.4.html>