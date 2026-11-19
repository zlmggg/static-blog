---
title: "/etc/fstab · 持久化挂载"
description: "fstab 六列含义、用 UUID 挂载、nofail 防起不来、mount -a 验证、_netdev 网络盘。写错 fstab 系统起不来的救援，中文详解。"
---

# /etc/fstab · 持久化挂载

> 命令手册 · [磁盘与存储](/commands/storage/) ｜ 频率：偶尔用
> mount 是临时的，重启就没了。写 fstab 开机自动挂。**写错 fstab 系统可能起不来**，务必验证。

## 一句话用途

配置开机自动挂载的文件系统。

## 六列含义

```text
UUID=xxxx-xxxx  /data  xfs  defaults,nofail  0 0
│               │      │    │                │ │
设备            挂载点 类型  选项             dump fsck顺序
```

| 列 | 含义 |
|---|---|
| 1 设备 | **UUID=**（推荐）/ LABEL= / /dev/sdX |
| 2 挂载点 | 目录（swap 写 none/swap） |
| 3 类型 | xfs/ext4/nfs/swap |
| 4 选项 | defaults / nofail / _netdev 等 |
| 5 dump | 备份标记（一般0） |
| 6 fsck | 开机检查顺序（根1，其他2，0不查） |

## 关键选项

| 选项 | 作用 |
|---|---|
| `nofail` | 设备不存在不阻塞启动（**数据盘必加**） |
| `_netdev` | 网络盘（NFS/iSCSI），等网络就绪再挂 |
| `noexec,nosuid,nodev` | 数据盘安全 |
| `x-systemd.device-timeout=10` | 等待超时 |

## 安全流程（重点）

```bash
sudo blkid /dev/sdb1                 # 取 UUID
# 编辑 /etc/fstab 加一行（用 UUID + nofail）
sudo mount -a                        # 测试挂载所有 fstab 条目
findmnt /data                        # 确认挂上
```

::: danger 写错 fstab 起不来
fstab 错误（设备不存在且无 nofail、类型错）会让系统进 emergency mode。改完**必须 `mount -a` 验证**无报错再重启。数据盘加 nofail 兜底。救援：emergency 里改回 fstab 或注释错误行。
:::

## 运维实战

**新盘持久化**：blkid 取 UUID → fstab 加 `UUID=... /data xfs defaults,nofail 0 0` → mount -a 验证。
**NFS 自动挂**：`server:/export /mnt nfs defaults,_netdev,nofail 0 0`。
**swap 持久化**：`UUID=... none swap sw 0 0`。

## 相关命令

[lsblk/blkid](./lsblk-blkid-findmnt) · [mount](./mount-umount) · [mkfs](./mkfs) · [swapon](./swapon) · [NFS](./nfs)

## 官方文档

- fstab：<https://man7.org/linux/man-pages/man5/fstab.5.html>