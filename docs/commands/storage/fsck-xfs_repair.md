---
title: "fsck / xfs_repair · 文件系统修复"
description: "fsck 修 ext4、xfs_repair 修 xfs、必须卸载后修、-n 只检查不改、超级块修复。磁盘异常/断电后修复，中文详解。"
---

# fsck / xfs_repair · 文件系统修复

> 命令手册 · [磁盘与存储](/commands/storage/) ｜ 频率：很少用
> 断电/异常关机后文件系统可能损坏，挂载报错或只读。fsck（ext4）/xfs_repair（xfs）修复。

## 一句话用途

检查并修复损坏的文件系统。

## 高频场景速查

```bash
# ext4
sudo umount /data                    # 必须先卸载！
sudo fsck -n /dev/sdb1               # 只检查不修（先看）
sudo fsck -y /dev/sdb1               # 自动 yes 修复
sudo fsck.ext4 -f /dev/sdb1          # 强制检查（即使标记干净）

# xfs
sudo umount /data
sudo xfs_repair -n /dev/sdb1         # 只检查
sudo xfs_repair /dev/sdb1            # 修复
sudo xfs_repair -L /dev/sdb1         # 清日志强制修（最后手段，可能丢数据）
```

## 关键规则

::: danger 必须卸载后修复
对**已挂载**的文件系统跑 fsck/xfs_repair 会加重损坏。先 umount（根分区需救援模式/LiveCD）。xfs_repair 要求卸载，挂载着会拒绝。
:::

| 参数 | 含义 |
|---|---|
| `-n` | 只检查不修改（先评估） |
| `-y` | 自动回答 yes 修复 |
| `-f` | 强制检查 |
| `xfs_repair -L` | 清空日志强制修（丢近期数据，慎用） |

## 运维实战

**断电后挂载报只读**：dmesg 看 I/O error/文件系统错误 → 卸载 → fsck/xfs_repair → 重挂。
**根分区损坏**：进 emergency/rescue，或 LiveCD 启动后修。
**先 -n 评估**：先看损坏程度，再决定 -y 修。xfs_repair -L 是最后手段（清日志可能丢未落盘数据）。
**修前备份**：能 dd 镜像就先 dd 备份再修（[dd](./dd)）。

## 相关命令

[mount/umount](./mount-umount) · [dmesg](/commands/system/dmesg) · [smartctl](./smartctl) · [dd](./dd) · [mkfs](./mkfs)

## 官方文档

- fsck：<https://man7.org/linux/man-pages/man8/fsck.8.html>
- xfs_repair：<https://man7.org/linux/man-pages/man8/xfs_repair.8.html>