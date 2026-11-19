---
title: "lspci / lsusb / lsmod / modprobe · 设备与内核模块"
description: "lspci 看 PCI 设备（网卡/显卡/RAID）、lsusb USB 设备、lsmod 已加载模块、modprobe 加载/卸载。驱动与硬件排查，中文详解。"
---

# lspci / lsusb / lsmod / modprobe · 设备与内核模块

> 命令手册 · [进程与系统](/commands/system/) ｜ 频率：很少用
> 网卡识别没、驱动加载没、RAID 卡什么型号——lspci 看设备，lsmod/modprobe 管驱动模块。

## 一句话用途

查看硬件设备清单，查看/加载/卸载内核驱动模块。

## 高频场景速查

```bash
lspci                          # 所有 PCI 设备
lspci | grep -i eth            # 找网卡
lspci | grep -i raid           # 找 RAID 卡
lspci -nnk                     # 带厂商ID+用的驱动（排驱动没绑）
lsusb                          # USB 设备
lsmod                          # 已加载模块
lsmod | grep nvme              # 看 nvme 驱动加载没
sudo modprobe nvme             # 加载模块
sudo modprobe -r nvme          # 卸载模块
modinfo nvme                   # 模块信息
```

## 参数详解

### lspci

| 参数 | 含义 |
|---|---|
| `-nn` | 显示厂商/设备 ID |
| `-k` | 显示用的内核驱动 |
| `-v` | 详细 |
| `-s 地址` | 只看某设备 |

### modprobe

| 参数 | 含义 |
|---|---|
| `modprobe 模块` | 加载（自动处理依赖） |
| `-r 模块` | 卸载 |
| `modinfo 模块` | 模块信息/参数 |

## 运维实战

**新网卡没识别**：`lspci -nnk | grep -A3 -i eth` 看 "Kernel driver in use" 有没有，没有就是缺驱动，装对应固件/模块。
**确认 NVMe 驱动**：`lsmod | grep nvme`，没加载 `modprobe nvme`。
**模块参数持久化**：写 /etc/modprobe.d/xxx.conf，开机自动带参加载。

::: tip lsmod vs modprobe
lsmod 只读列已加载；modprobe 加载/卸载并处理依赖（比 insmod/rmmod 智能）。模块黑名单写 /etc/modprobe.d/blacklist.conf。
:::

## 相关命令

[dmidecode](./lscpu-dmidecode) · [dmesg](./dmesg) · [ethtool](/commands/network/ethtool) · [smartctl](/commands/storage/smartctl)

## 官方文档

- lspci：<https://man7.org/linux/man-pages/man8/lspci.8.html>
- modprobe：<https://man7.org/linux/man-pages/man8/modprobe.8.html>