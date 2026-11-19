---
title: "swapon / swapoff / mkswap · 交换空间"
description: "swap 分区/文件创建启用、swapon/swapoff、swappiness 调优、free 看 swap。内存不足缓冲，中文详解。"
---

# swapon / swapoff / mkswap · 交换空间

> 命令手册 · [磁盘与存储](/commands/storage/) ｜ 频率：很少用
> 内存不够时把冷页换出到磁盘，避免 OOM 直接杀进程。swap 是缓冲不是内存替代——用多了性能骤降。

## 一句话用途

创建、启用、停用交换空间（分区或文件）。

## 高频场景速查

```bash
swapon --show                  # 看当前 swap
free -h                        # 看 swap 用量
# 用文件做 swap（推荐，灵活）
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
# 用分区做 swap
sudo mkswap /dev/sdb2
sudo swapon /dev/sdb2
sudo swapoff /swapfile         # 停用
# fstab 持久化
/swapfile  none  swap  sw  0 0
```

## swappiness 调优

```bash
cat /proc/sys/vm/swappiness        # 默认60
sudo sysctl -w vm.swappiness=10    # 调低（少用 swap）
```

| 值 | 倾向 |
|---|---|
| 0 | 尽量不用 swap（内存够才换） |
| 10 | 服务器常用（少换） |
| 60 | 默认 |
| 100 | 积极换出 |

::: tip 数据库/缓存调低 swappiness
MySQL/Redis 等内存敏感服务，swap 会让延迟飙升。设 swappiness=1~10，或关 swap（K8s 节点要求关 swap）。但完全无 swap 内存峰值易 OOM，权衡。
:::

## 运维实战

**小内存 VPS 加 swap**：fallocate 建 swapfile 防 OOM。
**K8s 节点关 swap**：`swapoff -a` + 注释 fstab swap 行（kubelet 要求）。
**排 swap 用满**：free 看 swap 满 + si/so 高（[vmstat](/commands/observe/vmstat)）说明内存真不够，加内存而非加 swap。

## 相关命令

[free](/commands/observe/free) · [vmstat](/commands/observe/vmstat) · [sysctl](/commands/system/sysctl) · [fstab](./fstab) · [mkfs](./mkfs)

## 官方文档

- swapon：<https://man7.org/linux/man-pages/man8/swapon.8.html>
- mkswap：<https://man7.org/linux/man-pages/man8/mkswap.8.html>