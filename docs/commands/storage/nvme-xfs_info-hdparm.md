---
title: "nvme / xfs_info / hdparm · 磁盘信息与调优"
description: "nvme 看 NVMe 健康/温度/寿命、xfs_info 看 xfs 几何参数、hdparm 看 SATA 参数/测速。SSD 运维，中文详解。"
---

# nvme / xfs_info / hdparm · 磁盘信息与调优

> 命令手册 · [磁盘与存储](/commands/storage/) ｜ 频率：很少用
> NVMe SSD 用 nvme 工具看健康寿命；xfs_info 看 xfs 布局；hdparm 看 SATA 盘参数。

## 一句话用途

查看 NVMe/xfs/SATA 磁盘的详细信息与健康。

## 高频场景速查

```bash
# NVMe
sudo nvme list                     # 列 NVMe 设备
sudo nvme smart-log /dev/nvme0     # 健康/温度/寿命/读写量
sudo nvme id-ctrl /dev/nvme0       # 控制器信息
sudo nvme format /dev/nvme0n1      # 低级格式化（慎用）

# xfs
xfs_info /data                     # xfs 几何（块大小/日志/agcount）

# SATA
sudo hdparm -I /dev/sda            # 盘详细信息
sudo hdparm -tT /dev/sda           # 测读速（缓存+裸盘）
sudo hdparm -W /dev/sda            # 看写缓存开关
```

## nvme smart-log 关键项

| 字段 | 含义 |
|---|---|
| `temperature` | 温度（过高降速/损寿命） |
| `percentage_used` | 寿命已用%（接近100该换） |
| `available_spare` | 可用备用块（低于阈值告警） |
| `data_units_read/written` | 累计读写量 |
| `media_errors` | 介质错误数 |
| `critical_warning` | 严重告警位 |

## 运维实战

**SSD 寿命巡检**：`nvme smart-log` 看 percentage_used 与 available_spare，提前换盘。
**SSD 温度高**：机房散热/盘位风道，NVMe 过热会降速。
**xfs 调优参考**：xfs_info 看 agcount/块大小，大文件并发可建盘时调。
**SATA 测速**：hdparm -tT 粗测，精确用 [fio](/commands/observe/fio)。

## 相关命令

[smartctl](./smartctl) · [lsblk](./lsblk-blkid-findmnt) · [fio](/commands/observe/fio) · [xfs_growfs](./lvm-extend)

## 官方文档

- nvme-cli：<https://github.com/linux-nvme/nvme-cli>
- xfs_info：<https://man7.org/linux/man-pages/man8/xfs_info.8.html>
- hdparm：<https://man7.org/linux/man-pages/man8/hdparm.8.html>