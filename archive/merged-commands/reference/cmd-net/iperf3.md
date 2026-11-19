---
title: "iperf3 带宽测试速查：点到点吞吐怎么量"
description: "本文是 网络命令速查 中「带宽测试」的补充。实时“谁在吃带宽”用 iftop/nethogs/nload；本篇只讲主动压测链路吞吐。 官方文档：iperf3 官方站 ｜ iperf3 手册"
---
# iperf3 带宽测试速查：点到点吞吐怎么量

> 本文是 [网络命令速查](../network-commands#流量监控) 中「带宽测试」的补充。实时“谁在吃带宽”用 [iftop/nethogs/nload](./bandwidth)；本篇只讲**主动压测链路吞吐**。
>
> 官方文档：[iperf3 官方站](https://software.es.net/iperf/) ｜ [iperf3 手册](https://iperf.fr/iperf-doc.php)

## 一、先分清两种问题

| 问题 | 工具 |
|---|---|
| 现在带宽被谁占了 | `iftop` / `nethogs` / `nload` |
| 这条链路**最大能跑多少**、是否达标 | `iperf3` |

`iperf3` 需要两端：一端 `-s` 做服务端，另一端 `-c` 做客户端。

## 二、最简测试

```bash
# 服务端（被压测的机器）
iperf3 -s

# 客户端（发起压测的机器），默认测 10 秒
iperf3 -c 10.0.0.12
```

输出重点：

| 字段 | 含义 |
|---|---|
| `Bitrate` | 吞吐速率（默认 bit/s） |
| `Retr` | TCP 重传次数（高说明链路质量差） |
| `sender` / `receiver` | 发送端/接收端统计，二者差大说明中间有丢包或限速 |

## 三、常用参数

| 参数 | 作用 |
|---|---|
| `-t 30` | 测试 30 秒 |
| `-P 4` | 4 条并发流（单流跑不满时用） |
| `-R` | 反向测试（服务端发、客户端收） |
| `-u -b 100M` | UDP 模式，指定目标带宽 |
| `-p 5201` | 指定端口 |
| `-f m` | 输出单位换成 Mbit/s |
| `-i 1` | 每秒打印一次中间结果 |
| `-w 1M` | 指定 TCP 窗口 |
| `--get-server-output` | 客户端拿服务端统计（UDP 丢包率常用） |

## 四、典型场景

**验证新链路/专线是否达标：**

```bash
# 服务端
iperf3 -s -p 5201

# 客户端：4 并发流跑 30 秒
iperf3 -c 10.0.0.12 -p 5201 -P 4 -t 30 -f m
```

**排查“上传慢还是下载慢”：**

```bash
iperf3 -c 10.0.0.12 -R -t 20    # 反向：由服务端发数据
```

**UDP 丢包/抖动：**

```bash
iperf3 -s
iperf3 -c 10.0.0.12 -u -b 100M -t 20 --get-server-output
```

## 五、结果怎么解读

1. **单流跑不满、多流能跑满**：常见于长肥管道（BDP 大）或单连接被限速，用 `-P` 验证。
2. **`Retr` 很高**：链路丢包/拥塞/网卡错误，结合 `ss -ti`、`ip -s link`、`mtr` 看。
3. **发送高、接收低**：中间设备限速、QoS、丢包。
4. **只有某一段慢**：分段压测（A→B、B→C），不要只测端到端。
5. **压测本身打满 CPU**：降并发或换更空闲的机器，避免把“机器 CPU 瓶颈”当成网络瓶颈。

## 六、新手易错点

1. **两端时间不同步不影响 iperf3 结果**，但看日志时间要对时。
2. **防火墙要放行 5201/tcp（UDP 测试还要放行 udp）**，否则一直 `Connection refused`。
3. **生产压测要限速/限时**：`-t` 别太长，优先在业务低峰，避免影响真实流量。
4. **`-R` 才是反向**：默认是客户端发、服务端收。
5. **UDP 模式不加 `-b` 会非常激进**，可能直接打爆链路。

## 七、官方文档与相关

- iperf3 官方站：https://software.es.net/iperf/
- iperf3 文档：https://iperf.fr/iperf-doc.php
- 实时带宽：[iftop/nethogs/nload](./bandwidth)
- 链路质量：[ping/traceroute/mtr](./traceroute-mtr)
- TCP 重传：[ss](./ss)
- 速查页：[网络命令速查](../network-commands#流量监控)
