---
title: "ethtool 命令详解：网卡速率、双工、丢包与 offload"
description: "ethtool 用来查网卡协商速率、双工、光模块、驱动统计和硬件 offload。本文覆盖 link down、丢包/错误计数、ring buffer、GRO/TSO 关闭和远程改速率的风险。"
---

# ethtool 命令详解：网卡速率、双工、丢包与 offload

> `ethtool` 看的是**网卡和链路层**，不负责 IP、路由、端口。网络慢时先用 `ip -s link`、`ethtool -S` 确认有没有物理层/驱动层丢包，再去查 TCP、应用和防火墙。

## 基本信息

```bash
# 网卡列表
ip link show

# 协商速率、双工、链路状态
ethtool eth0

# 驱动与固件版本
ethtool -i eth0

# 网卡统计（不同驱动字段不同）
ethtool -S eth0
```

`ethtool eth0` 重点看：

| 字段 | 含义 |
|---|---|
| `Speed` | 当前协商速率，如 `1000Mb/s`、`10Gbps` |
| `Duplex` | `Full` / `Half`，半双工在交换式网络里通常不正常 |
| `Auto-negotiation` | 是否开启自协商 |
| `Link detected` | `yes` 才说明物理链路通 |
| `Supported link modes` | 网卡支持的能力，不代表当前协商结果 |

## 场景一：链路 down 或速率不对

```bash
ethtool eth0
ip link show eth0
```

排查顺序：

1. `Link detected: no`：先查网线、光模块、交换机端口、VLAN。
2. 速率只有 `100Mb/s`，但网卡和交换机支持千兆：可能是网线只有 4 芯、水晶头压接不良、光模块不匹配。
3. `Duplex: Half`：强制半双工或自协商失败，常见于老交换机/劣质网线；交换式网络应为全双工。
4. `Auto-negotiation: off` 且速率固定：确认两端配置一致，不要一端自协商、一端强制。

远程机器改速率/双工可能导致 SSH 断开，务必有带外管理或本地控制台：

```bash
# 临时改为自协商（风险操作，先确认对端配置）
ethtool -s eth0 autoneg on

# 强制千兆全双工（仅在对端也固定时使用）
ethtool -s eth0 speed 1000 duplex full autoneg off
```

## 场景二：丢包、错误计数

```bash
# 内核视角的收发统计
ip -s link show eth0

# 网卡驱动视角的统计
ethtool -S eth0 | grep -Ei 'drop|err|fifo|miss|overrun|discard'
```

常见字段：

| 字段 | 含义 | 可能原因 |
|---|---|---|
| `rx_dropped` / `tx_dropped` | 收/发丢包 | 缓冲区不足、CPU 处理不过来、QoS |
| `rx_errors` / `tx_errors` | 物理层/帧错误 | 网线、光模块、双工不匹配 |
| `rx_fifo_errors` | 接收 FIFO 溢出 | 网卡 ring buffer 太小、突发流量 |
| `rx_missed_errors` | 网卡没来得及收 | 中断/CPU 瓶颈、ring buffer |
| `rx_over_errors` | 接收溢出 | 驱动/硬件限制 |
| `carrier_errors` | 载波错误 | 物理链路不稳定 |

如果 `rx_dropped` 持续增长而 `ethtool -S` 没有明显错误，检查：

```bash
# ring buffer 当前值和最大值
ethtool -g eth0

# 中断是否集中在单个 CPU
grep eth0 /proc/interrupts

# 软中断是否打满
mpstat -P ALL 1
cat /proc/softirqs | grep -E 'NET_RX|NET_TX'
```

## 场景三：offload 导致抓包/转发异常

```bash
# 查看硬件 offload 开关
ethtool -k eth0

# 临时关闭 GRO/TSO（只用于排查，重启后失效）
ethtool -K eth0 gro off
ethtool -K eth0 tso off
ethtool -K eth0 gso off
```

典型现象：

- `tcpdump` 抓到的包比实际大很多（GRO 合并）。
- 容器/网桥转发时出现校验和错误（校验和 offload 与虚拟网卡不匹配）。
- 高速网卡上单流吞吐上不去，关闭 TSO 后反而更差：先确认是不是 offload 与虚拟化层不兼容。

关闭 offload 会降低性能，只用于定位；定位后要恢复：

```bash
ethtool -K eth0 gro on
ethtool -K eth0 tso on
```

## 场景四：光模块与硬件诊断

```bash
# 光模块信息（支持 DDM/DOM 的网卡）
ethtool -m eth0

# 网卡自检（会短暂中断链路，谨慎）
ethtool -t eth0

# 让网卡指示灯闪烁，便于机房找线
ethtool -p eth0 10
```

`ethtool -m` 可看光模块的收发光功率、温度、厂商和波长；光功率异常时先清洁/更换光纤和模块，不要先怀疑 TCP。

## 场景五：多队列与 RSS

```bash
# 查看队列数
ethtool -l eth0

# 查看当前 RSS 哈希配置
ethtool -n eth0
```

高并发场景下，单队列容易打满一个 CPU。可在支持的情况下调整队列数：

```bash
ethtool -L eth0 combined 8
```

调整后确认中断分散：

```bash
grep eth0 /proc/interrupts
```

## 持久化与发行版差异

`ethtool` 命令本身不持久化，重启后失效。需要持久化时：

- NetworkManager：`nmcli connection modify eth0 ethtool.speed 1000` 等（按版本支持情况）。
- systemd-networkd：`.link` 文件里配 `[Link]` 的 `Speed`/`Duplex`。
- 传统 RHEL：`/etc/sysconfig/network-scripts/ifcfg-eth0` 里 `ETHTOOL_OPTS`。
- 云主机：部分虚拟网卡不支持改速率/双工，命令会报 `Operation not supported`，以云厂商文档为准。

## 官方文档

- [ethtool(8) man page](https://man7.org/linux/man-pages/man8/ethtool.8.html)
- [Linux 内核网络文档](https://docs.kernel.org/networking/)
