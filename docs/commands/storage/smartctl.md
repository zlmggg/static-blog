---
title: "smartctl 命令详解：磁盘健康检查与 SMART 预警"
description: "本文是 Linux 命令速查 中磁盘健康检查的补充；smartctl 属于 smartmontools 包，用来读 SATA/SAS/NVMe 盘的 SMART 自监控数据，提前发现坏道、扇区重映射、温度异常和寿命衰减。 目标：知道巡检时看哪几个字段，能区分“盘快坏了”和“只是报了个错”。"
---
# smartctl 命令详解：磁盘健康检查与 SMART 预警

> 本文是 [Linux 命令速查](/reference/linux-commands#磁盘空间) 中磁盘健康检查的补充；`smartctl` 属于 `smartmontools` 包，用来读 SATA/SAS/NVMe 盘的 SMART 自监控数据，提前发现坏道、扇区重映射、温度异常和寿命衰减。
> 目标：知道巡检时看哪几个字段，能区分“盘快坏了”和“只是报了个错”。

## 一、它解决什么问题

`df` 只能看“空间用了多少”，`dmesg` 只在内核已经报错时才有输出；磁盘真正要坏之前，SMART 往往已经给出预警：

- **Reallocated_Sector_Ct** 持续增长：盘片出现坏扇区，固件在用备用扇区顶替；
- **Current_Pending_Sector** 大于 0：有扇区读取失败，等着重映射；
- **Offline_Uncorrectable** 增长：离线自检都修不了的错误，通常比 pending 更严重；
- **UDMA_CRC_Error_Count** 增长：多半是 SATA 线、背板或接口接触问题，不一定是盘坏；
- **Temperature** 偏高：散热或风道问题，长期高温会加速老化；
- **Power_On_Hours / Wear_Leveling**：机械盘看通电时长，SSD 看磨损和剩余寿命。

巡检结论不能只看一个数：**趋势比单次值更重要**。同一块盘本周 `Reallocated_Sector_Ct` 从 0 涨到 8，比它一直稳定在 8 更值得处理。

## 二、安装与识别设备

```bash
# RHEL / Rocky / CentOS
sudo dnf install -y smartmontools

# Debian / Ubuntu
sudo apt update && sudo apt install -y smartmontools
```

先确认盘名和类型：

```bash
lsblk -d -o NAME,SIZE,MODEL,ROTA,TRAN
sudo smartctl --scan
```

`--scan` 会输出类似：

```text
/dev/sda -d scsi # /dev/sda, SCSI device
/dev/nvme0 -d nvme # /dev/nvme0, NVMe device
```

`ROTA=1` 通常是机械盘，`ROTA=0` 是 SSD/NVMe。云主机上的虚拟盘经常没有 SMART 数据，`smartctl -a` 会提示不支持，这是正常现象，不要当成故障。

## 三、最常用的五条命令

```bash
# 1. 一次看全：型号、容量、健康结论、温度、关键属性
sudo smartctl -a /dev/sda

# 2. 只看健康结论：PASSED / FAILED
sudo smartctl -H /dev/sda

# 3. 只看设备信息
sudo smartctl -i /dev/sda

# 4. 只看 SMART 属性表（脚本巡检常用）
sudo smartctl -A /dev/sda

# 5. 扩展信息：错误日志、自检日志、温度等
sudo smartctl -x /dev/sda
```

NVMe 盘把 `/dev/sda` 换成 `/dev/nvme0` 即可：

```bash
sudo smartctl -a /dev/nvme0
sudo smartctl -H /dev/nvme0
```

## 四、关键字段怎么读

`smartctl -A` 输出里的 `RAW_VALUE` 才是原始计数，`VALUE` 是归一化后的 0–100 分值（不同厂商算法不同，不能跨型号直接比）。

| 字段 | 含义 | 看到什么要警惕 |
|---|---|---|
| `Reallocated_Sector_Ct` | 已重映射的坏扇区数 | 非 0 且持续增长 |
| `Current_Pending_Sector` | 等待重映射的扇区数 | 大于 0，尤其是持续增加 |
| `Offline_Uncorrectable` | 离线自检无法修复的扇区 | 大于 0，通常比 pending 更严重 |
| `UDMA_CRC_Error_Count` | SATA 链路 CRC 错误 | 增长先查线缆、背板、接口 |
| `Reported_Uncorrect` | 上报给系统的不可纠正错误 | 增长说明读写出过错 |
| `Temperature_Celsius` | 盘温 | 机械盘长期超过 50–55℃ 要查散热 |
| `Power_On_Hours` | 通电小时数 | 结合年限判断是否到更换周期 |
| `Wear_Leveling_Count` | SSD 磨损均衡计数 | 接近厂商阈值说明寿命将尽 |
| `Media_Wearout_Indicator` | SSD 介质磨损指示 | 越低越接近寿命终点 |

机械盘重点看前四项 + 温度；SSD 重点看 `Current_Pending_Sector`、`Offline_Uncorrectable`、`Wear_Leveling_Count`、`Percentage_Used`（NVMe）。

`smartctl -H` 只给一个总体结论：

```text
SMART overall-health self-assessment test result: PASSED
```

`PASSED` 不等于“盘绝对没问题”，它只表示固件当前没把盘标记为故障；坏道趋势、文件系统错误、RAID 卡缓存问题仍要单独看。

## 五、跑自检

SMART 自检分短检和长检：

```bash
# 短检：几十秒到几分钟，查电子和机械基础项
sudo smartctl -t short /dev/sda

# 长检：几十分钟到几小时，全盘扫描，生产低峰期做
sudo smartctl -t long /dev/sda

# 查看自检进度和结果
sudo smartctl -l selftest /dev/sda
```

长检期间盘还能用，但 IO 会变慢；数据库盘、RAID 重建期间不要安排长检。自检日志里 `Self-test execution status` 显示 `completed without error` 才算通过。

## 六、NVMe、RAID 和 USB 盘的写法

```bash
# NVMe
sudo smartctl -a /dev/nvme0

# MegaRAID / PERC 等 RAID 卡后面的盘：N 是逻辑盘号
sudo smartctl -a -d megaraid,0 /dev/sda
sudo smartctl -a -d megaraid,1 /dev/sda

# USB 硬盘盒经常识别成 SCSI，需要指定 sat 协议
sudo smartctl -a -d sat /dev/sdb

# 不让 smartctl 唤醒处于 standby 的盘
sudo smartctl -n standby -a /dev/sda
```

RAID 卡后面的盘，`smartctl --scan` 不一定能自动发现，需要按卡型用 `-d megaraid,N`、`-d cciss,N` 或 `-d areca,N` 逐个读。具体编号以阵列卡管理工具（如 `storcli`、`perccli`）列出的物理盘为准。

## 七、批量巡检脚本

```bash
#!/usr/bin/env bash
set -u
for dev in $(sudo smartctl --scan | awk '{print $1}'); do
  echo "===== $dev ====="
  sudo smartctl -H "$dev" | grep -E 'result|FAILED|PASSED'
  sudo smartctl -A "$dev" | awk '
    /Reallocated_Sector_Ct|Current_Pending_Sector|Offline_Uncorrectable|UDMA_CRC_Error_Count|Temperature_Celsius|Wear_Leveling_Count/ {
      printf "%-28s %s\n", $2, $10
    }'
done
```

需要结构化结果时用 JSON：

```bash
sudo smartctl -j -a /dev/sda | jq '.smart_status.passed, .ata_smart_attributes.table[] | select(.name=="Reallocated_Sector_Ct")'
```

脚本里不要只判断 `smartctl` 的退出码：它的退出状态是位掩码，可能同时表示“命令成功”和“盘有 prefail 属性”。优先解析 `-H` 的 `PASSED/FAILED`，或 `-j` 里的 `smart_status.passed`。

## 八、常见坑

1. **虚拟盘没有 SMART**：云主机、部分虚拟化磁盘读不到属性，报告 “SMART support is: Unavailable” 属正常；要靠宿主机或云监控。
2. **USB 硬盘盒读不到**：加 `-d sat`；仍不行说明桥接芯片不透传 SMART。
3. **RAID 卡只看得到逻辑盘**：必须用 `-d megaraid,N` 读物理盘，否则看到的是阵列卡伪造的健康状态。
4. **`PASSED` 就放心**：还要看 pending/uncorrectable 的趋势，以及 `dmesg` 里的 IO 错误。
5. **长检影响业务**：数据库、分布式存储的重建期间不要跑 long test。
6. **CRC 错误不等于盘坏**：先换 SATA 线、换槽位、检查背板，再判断盘。

## 九、和监控系统结合

生产上建议把 SMART 采集接进 Prometheus：

- `node_exporter --collector.smartctl` 需要 `smartmontools`，并让 node_exporter 有权限执行 `smartctl`；
- 采集指标后重点告警：`smart_status_passed == 0`、`Reallocated_Sector_Ct` 增长、`Current_Pending_Sector > 0`、温度超阈值；
- 没有监控条件时，至少每周跑一次上面的批量脚本，把结果落到日志或巡检表。

## 官方文档

- [smartctl man page（Debian）](https://manpages.debian.org/bookworm/smartmontools/smartctl.8.en.html)
- [smartmontools 官方文档](https://www.smartmontools.org/wiki/TocDoc)
