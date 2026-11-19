---
title: "mount / umount · 挂载卸载"
description: "mount 挂文件系统、-o 选项（ro/noexec/nosuid）、bind 挂载、umount 卸载与 busy 处理。操作变更类，中文详解。"
---

# mount / umount · 挂载卸载

> 命令手册 · [磁盘与存储](/commands/storage/) ｜ 频率：偶尔用
> 格式化后挂到目录才能用。mount 临时挂载，持久化写 fstab。卸载报 busy 用 fuser/lsof 查占用。

## 一句话用途

把文件系统挂到目录树，或卸载。

## 高频场景速查

```bash
sudo mount /dev/sdb1 /data           # 挂载
sudo mount -o ro /dev/sdb1 /data     # 只读挂载
sudo mount -o remount,rw /data       # 重挂为读写
sudo mount --bind /src /dst          # bind 挂载（目录映射）
sudo mount -t xfs /dev/sdb1 /data    # 指定类型
mount | grep /data                   # 看挂载
sudo umount /data                    # 卸载
sudo umount -l /data                 # 懒卸载（busy 时）
sudo umount -f /data                 # 强制（NFS 卡死）
```

## 常用挂载选项

| 选项 | 含义 |
|---|---|
| `ro` / `rw` | 只读 / 读写 |
| `noexec` | 禁止执行（数据盘安全） |
| `nosuid` | 忽略 suid |
| `nodev` | 忽略设备文件 |
| `noatime` | 不更新访问时间（减 IO） |
| `defaults` | rw,suid,dev,exec,auto,nouser,async |

## umount busy 处理

```bash
sudo umount /data                    # 报 target is busy
sudo fuser -vm /data                 # 看谁占用
sudo fuser -km /data                 # 杀占用进程
sudo umount /data                    # 再卸
# 或懒卸载（立即断开，引用释放后真正卸）
sudo umount -l /data
```

::: danger 别在挂载点有数据时格式化
mount 错盘、mkfs 错分区会丢数据。操作前 lsblk/findmnt 三确认。umount -l 懒卸载后进程仍可能写旧引用，谨慎。
:::

## 运维实战

**新盘挂载**：mkfs → mkdir /data → mount → 写 [fstab](./fstab) 持久化。
**安全数据盘**：`-o noexec,nosuid,nodev` 防数据盘被放可执行木马。
**NFS 卡死**：`umount -f -l` 强制+懒卸载，避免进程 D 状态卡死。

## 相关命令

[lsblk/findmnt](./lsblk-blkid-findmnt) · [fstab](./fstab) · [fuser](/commands/observe/fuser) · [lsof](/commands/observe/lsof) · [NFS](./nfs)

## 官方文档

- mount：<https://man7.org/linux/man-pages/man8/mount.8.html>
- umount：<https://man7.org/linux/man-pages/man8/umount.8.html>