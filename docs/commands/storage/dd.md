---
title: "dd · 底层复制与镜像"
description: "dd 块级复制/做磁盘镜像/写 ISO、bs 块大小/count/conv、测磁盘吞吐、备份 MBR。危险与正确用法，中文详解。"
---

# dd · 底层复制与镜像

> 命令手册 · [磁盘与存储](/commands/storage/) ｜ 频率：很少用
> dd 按字节复制，能做整盘镜像、写启动盘、测裸盘吞吐。也 infamous 能一键毁盘——of 写错就完了。

## 一句话用途

块级精确复制数据：磁盘镜像、写 ISO、备份引导、测吞吐。

## 高频场景速查

```bash
# 做磁盘镜像（备份）
sudo dd if=/dev/sdb of=/backup/sdb.img bs=64K status=progress conv=noerror,sync

# 恢复镜像到盘
sudo dd if=/backup/sdb.img of=/dev/sdb bs=64K status=progress

# 写 ISO 到 U 盘
sudo dd if=linux.iso of=/dev/sdc bs=4M status=progress oflag=sync

# 测顺序写吞吐
dd if=/dev/zero of=/data/test bs=1M count=1024 oflag=direct
# 测顺序读
dd if=/data/test of=/dev/null bs=1M iflag=direct

# 备份 MBR（前512字节）
sudo dd if=/dev/sda of=mbr.bin bs=512 count=1
```

## 参数详解

| 参数 | 含义 |
|---|---|
| `if=` | 输入文件/设备 |
| `of=` | 输出文件/设备 |
| `bs=` | 块大小（64K/1M/4M） |
| `count=N` | 复制 N 块 |
| `status=progress` | 显示进度 |
| `conv=noerror,sync` | 遇错继续+补齐（救坏盘） |
| `oflag=direct` | 绕过缓存（测真实吞吐） |
| `oflag=sync` | 同步写（写 ISO 确保落盘） |

::: danger of 写错毁盘
`of=/dev/sda` 会覆盖整盘。dd 不确认、不可逆。操作前 lsblk 三确认目标设备，**if/of 别写反**。生产备份优先用专业工具，dd 用于镜像/应急。
:::

## 运维实战

**坏盘抢救镜像**：`conv=noerror,sync` 遇坏道跳过继续，先镜像出来再修。
**写启动 U 盘**：of 是整盘 /dev/sdc（不是分区 sdc1），oflag=sync 确保写完。
**粗测磁盘吞吐**：oflag=direct 绕缓存，bs=1M count=1024 测顺序写（精确用 [fio](/commands/observe/fio)）。

## 相关命令

[lsblk](./lsblk-blkid-findmnt) · [fio](/commands/observe/fio) · [fsck](./fsck-xfs_repair) · [mkfs](./mkfs) · [cp](/commands/basic/cp)

## 官方文档

- dd：<https://man7.org/linux/man-pages/man1/dd.1.html>