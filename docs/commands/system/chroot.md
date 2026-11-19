---
title: "chroot · 切换根目录"
description: "chroot 切根环境（救援/构建/隔离）、挂载 proc/sys/dev、与容器 namespace 的区别。系统救援与镜像构建，中文详解。"
---

# chroot · 切换根目录

> 命令手册 · [进程与系统](/commands/system/) ｜ 频率：很少用
> 系统起不来进救援模式修、构建最小根文件系统——chroot 把某目录当成新的 /。

## 一句话用途

把进程看到的根目录切到指定目录，用于系统救援、镜像构建、简单隔离。

## 高频场景速查

```bash
# 救援：从 LiveCD 修原系统
sudo mount /dev/sda2 /mnt
sudo mount --bind /dev /mnt/dev
sudo mount --bind /proc /mnt/proc
sudo mount --bind /sys /mnt/sys
sudo chroot /mnt                 # 切进原系统
# 里面可改密码、修 grub、重装内核
exit                             # 退出 chroot
```

## 关键要点

chroot 只换根目录，**不隔离进程/网络/用户**（不是安全沙箱）。新根里要有基本设备与文件系统：

```bash
mount --bind /dev  /mnt/dev      # 设备节点
mount -t proc proc /mnt/proc     # 进程信息
mount --bind /sys  /mnt/sys      # 内核接口
```

缺这些，chroot 里很多命令（systemctl/网络）跑不了。

## chroot vs 容器

| | chroot | 容器 |
|---|---|---|
| 根目录 | 换 | 换 |
| PID/网络/用户隔离 | 无 | 有（namespace） |
| 资源限制 | 无 | 有（cgroup） |
| 安全沙箱 | 不是 | 相对是 |

::: warning chroot 不是安全隔离
root 在 chroot 里能逃逸（再 chroot 出去）。要隔离用容器/namespace。chroot 只用于救援和构建，别当安全边界。
:::

## 运维实战

**救援改密码**：LiveCD 启动 → 挂载原根 → chroot → `passwd root` → 重启。
**修 grub**：chroot 进原系统 `grub2-install /dev/sda && grub2-mkconfig -o /boot/grub2/grub.cfg`。
**构建镜像根**：debootstrap/dnf --installroot 装最小系统到目录，chroot 进去配置。

## 相关命令

[mount](/commands/storage/) · [Docker 镜像](/services/container/docker/03-功能) · [systemctl](./systemctl-journalctl)

## 官方文档

- chroot：<https://man7.org/linux/man-pages/man8/chroot.8.html>