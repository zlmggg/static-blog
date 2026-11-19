---
title: "fdisk / parted / gdisk · 分区"
description: "fdisk MBR 分区、parted GPT 大分区/脚本化、gdisk GPT。新建/删除/改类型、partprobe 刷新。操作变更类，中文详解。"
---

# fdisk / parted / gdisk · 分区

> 命令手册 · [磁盘与存储](/commands/storage/) ｜ 频率：偶尔用
> 新盘要先分区才能格式化挂载。fdisk 经典交互、parted 支持 GPT 与脚本、gdisk 专管 GPT。

## 一句话用途

在磁盘上创建/删除/调整分区，选择 MBR 或 GPT 分区表。

## MBR vs GPT

| | MBR | GPT |
|---|---|---|
| 最大盘 | 2TB | 几乎无限 |
| 主分区数 | 4 | 128 |
| 工具 | fdisk | parted/gdisk |
| 现代默认 | 旧 | **推荐** |

## 高频场景速查

```bash
sudo fdisk -l                    # 看所有磁盘分区
sudo fdisk /dev/sdb              # 交互分区（n 新建/p 打印/w 写入/q 退出）
sudo parted /dev/sdb mklabel gpt           # 建 GPT 表
sudo parted /dev/sdb mkpart primary xfs 0% 100%   # 整盘一个分区
sudo parted /dev/sdb print       # 看分区
sudo gdisk /dev/sdb              # GPT 交互
sudo partprobe /dev/sdb          # 刷新内核分区表（不重启识别）
```

## fdisk 交互按键

| 键 | 作用 |
|---|---|
| `n` | 新建分区 |
| `p` | 打印分区表 |
| `d` | 删除分区 |
| `t` | 改类型（8e=LVM, 82=swap） |
| `w` | 写入并退出 |
| `q` | 不保存退出 |

## parted 脚本化（推荐大盤）

```bash
sudo parted -s /dev/sdb mklabel gpt mkpart primary xfs 0% 100%
sudo parted -s /dev/sdb set 1 lvm on        # 标记 LVM
```

`-s` 脚本模式不交互，适合自动化。用百分比避免对齐问题。

::: danger 分区是破坏性操作
对**已有数据**的盘改分区表会丢数据。操作前 `lsblk` 确认是空盘/新盘，重要数据先备份。fdisk 按 w 才真正写入，之前可 q 反悔。
:::

## 运维实战

**加盘标准流程**：lsblk 确认新盘 → parted mklabel gpt + mkpart → partprobe → [mkfs](./mkfs) → [mount](./mount-umount) → [fstab](./fstab)。
**LVM 用盘**：分区 set lvm on，或直接整盘做 PV（[lvm-create](./lvm-create)）。

## 相关命令

[lsblk](./lsblk-blkid-findmnt) · [mkfs](./mkfs) · [wipefs/partprobe](./wipefs-partprobe) · [LVM](./lvm-view)

## 官方文档

- fdisk：<https://man7.org/linux/man-pages/man8/fdisk.8.html>
- parted：<https://www.gnu.org/software/parted/manual/>
- gdisk：<https://man7.org/linux/man-pages/man8/gdisk.8.html>