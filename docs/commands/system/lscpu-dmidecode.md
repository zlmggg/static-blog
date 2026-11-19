---
title: "dmidecode / lscpu · 硬件信息"
description: "dmidecode 查内存条/主板/BIOS/序列号、lscpu CPU 拓扑、/proc/cpuinfo /proc/meminfo。不拆机摸清硬件配置，中文详解。"
---

# dmidecode / lscpu · 硬件信息

> 命令手册 · [进程与系统](/commands/system/) ｜ 频率：很少用
> 不拆机就知道插了几根内存、什么主板、BIOS 版本、机器序列号——dmidecode 读 SMBIOS/DMI 表。

## 一句话用途

查看物理硬件详情：内存条规格、主板、BIOS、CPU、序列号。

## 高频场景速查

```bash
sudo dmidecode -t memory           # 内存条详情（容量/频率/槽位）
sudo dmidecode -t system           # 厂商/型号/序列号
sudo dmidecode -t bios             # BIOS 版本/日期
sudo dmidecode -t processor        # CPU 信息
sudo dmidecode -s system-serial-number   # 只取序列号
lscpu                              # CPU 拓扑
cat /proc/meminfo                  # 内存详情
free -h                            # 内存概览
```

## dmidecode -t 类型

| 类型 | 内容 |
|---|---|
| `memory` | 内存设备（每根条） |
| `system` | 系统厂商/型号/序列号 |
| `bios` | BIOS 信息 |
| `processor` | 处理器 |
| `baseboard` | 主板 |
| `cache` | 缓存 |

## 运维实战

**查内存能不能扩**：`dmidecode -t memory` 看已用槽位/最大容量/频率，判断加条还是换条。
**报修要序列号**：`dmidecode -s system-serial-number` 取机器 SN。
**云主机看规格**：云厂商虚机 dmidecode 可能显示厂商信息，配合 lscpu/free 确认实际配额。

::: tip 易错点
dmidecode 需 root，读的是固件表，虚机里可能是宿主伪造信息。内存实际可用看 free / /proc/meminfo，dmidecode 看物理插槽。
:::

## 相关命令

[uptime/uname/lscpu](./uptime-uname) · [free](/commands/observe/) · [lspci/lsmod](./lspci-lsmod) · [smartctl](/commands/storage/smartctl)

## 官方文档

- dmidecode：<https://man7.org/linux/man-pages/man8/dmidecode.8.html>
- lscpu：<https://man7.org/linux/man-pages/man1/lscpu.1.html>