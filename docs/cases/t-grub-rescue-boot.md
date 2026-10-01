---
category: Linux
difficulty: 中级
date: 2019-04-12
---

# GRUB 损坏 / 内核升级后启动失败，进 rescue 模式（2019-04-12）

## 现象

机房例行内核升级后，重启服务器，屏幕停在黑色界面，左上角光标闪烁，再也进不去系统。
接显示器后看到的是 `grub rescue>` 提示符，或者直接出现：

```
error: no such partition.
Entering rescue mode...
grub rescue>
```

也有的机器在升级内核后旧内核被 yum/ apt 自动清理，重启时 GRUB 菜单指向了一个已经不存在的 vmlinuz 文件，报：

```
error: file '/boot/vmlinuz-3.10.0-1062.el7.x86_64' not found
error: you need to load the kernel first.
```

业务全部不可达，SSH 连不上。

## 环境

- 发行版：CentOS Linux release 7.6.1810 (Core)
- 内核：原内核 `3.10.0-957.el7.x86_64`，被升级到 `3.10.0-1062.el7.x86_64`
- 引导方式：传统 BIOS + MBR（非 UEFI），`/boot` 是独立分区 `/dev/sda1`
- 相关软件：grub2-tools-2.02-0.65.el7.centos.2.x86_64

## 定位过程

### 1. 先判断是哪种"起不来"

在 `grub rescue>` 提示符下，先看磁盘分区还在不在：

```
grub rescue> ls
(hd0) (hd0,gpt2) (hd0,gpt1) (hd0)
```

```
grub rescue> ls (hd0,gpt1)/
```

如果能列出 `boot/ grub2/ grub.cfg`，说明 `/boot` 分区还在，只是 GRUB 找不到正确的根；
如果列任何分区都提示 `unknown filesystem`，说明磁盘/分区表本身出了问题，先别往下做，去查硬盘。

### 2. 手动指定 root 与 vmlinuz，临时引导进系统

假设 `ls (hd0,gpt1)/` 能看到 `grub2/`，则：

```
grub rescue> set root=(hd0,gpt1)
grub rescue> set prefix=(hd0,gpt1)/grub2
grub rescue> insmod normal
grub rescue> normal
```

能进 GRUB 菜单后，按 `e` 编辑引导项，把 `linux` 那一行末尾确认 `root=/dev/mapper/centos-root` 正确，按 `Ctrl+X` 启动。
成功进入系统后，再执行下面的重建动作。

### 3. 确认是 grub.cfg 指向了被删的旧内核

```bash
rpm -qa | grep kernel
# kernel-3.10.0-957.el7.x86_64   <- 旧的已被自动 remove
# kernel-3.10.0-1062.el7.x86_64 <- 新的
grep vmlinuz /boot/grub2/grub.cfg | head
```

如果 grub.cfg 里 `linux /boot/vmlinuz-3.10.0-957...` 还在，但 `/boot/vmlinuz-3.10.0-957...` 文件已经没了，就是这次升级清理旧内核时 grub.cfg 没重新生成。

## 根因

`yum update kernel` 之后旧内核被 `yum-utils` 的 `kernel` 策略自动移除，但 `grub2-mkconfig` 没有被正常触发（或脚本中途被 Ctrl+C），导致 `/boot/grub2/grub.cfg` 仍然指向一个已经被删除的 vmlinuz/initramfs，GRUB 找不到文件就掉进 rescue。

## 解决步骤

### 1. 临时止血：用上面"手动指定 root"的方法先进系统

能登录系统是一切修复的前提。如果手动引导也进不去，就用 CentOS 7 安装 U 盘救援模式：
选 Troubleshooting → Rescue a CentOS Linux system，chroot 到 `/mnt/sysimage` 后再做下面的步骤。

### 2. 重建 GRUB 配置

BIOS + MBR 机器：

```bash
# 重新生成 grub.cfg，扫描 /boot 下所有可用内核
grub2-mkconfig -o /boot/grub2/grub.cfg

# 把 boot 分区写回 MBR 的 boot sector（如果连 stage1 都坏了才需要）
grub2-install /dev/sda
```

UEFI 机器注意路径不同，配置文件在 `/boot/efi/EFI/centos/grub.cfg`，且不要 `grub2-install /dev/sda`。

### 3. 确认默认启动内核是新内核

```bash
grub2-set-default 0
grub2-editenv list
# saved_entry=CentOS Linux (3.10.0-1062.el7.x86_64) 7 (Core)
```

### 4. 验证 /boot 下文件齐全

```bash
ls -1 /boot/vmlinuz-* /boot/initramfs-*.img
```

## 验证与预防

- `reboot` 一次，确认能正常进系统、SSH 可达。
- 以后内核升级脚本里，`yum update -y kernel` 之后**必须**跟一句 `grub2-mkconfig -o /boot/grub2/grub.cfg`。
- 服务器上至少保留 2 个内核：`yum install -y yum-utils && package-cleanup --oldkernels --count=2`，避免只有一个内核时它出问题就彻底起不来。
- 把 `/boot` 分区使用率纳入监控（`df /boot`），`/boot` 满了也是导致 grub.cfg 写失败、initramfs 生成失败的常见原因。

## 相关

- 命令速查：[Linux 命令速查](/reference/linux-commands)
- 巡检清单：[运维巡检清单](/reference/ops-checklists)
- 类似磁盘/文件系统问题：[文件系统损坏与 fsck 修复](/cases/t-filesystem-fsck-corrupt)
