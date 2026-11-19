---
title: "fio · 磁盘 IO 压测"
description: "fio 测磁盘 IOPS/吞吐/延迟、随机/顺序读写、iodepth 队列深度、bs 块大小。验证存储性能与复现 IO 瓶颈，中文详解。"
---

# fio · 磁盘 IO 压测

> 命令手册 · [排障观测](/commands/observe/) ｜ 频率：很少用
> 新盘性能达标吗？数据库盘能扛多少 IOPS？fio 是磁盘压测的事实标准，测 IOPS/吞吐/延迟。

## 一句话用途

对磁盘/文件系统做可控 IO 压测，测 IOPS、带宽、延迟。

## 高频场景速查

```bash
# 随机读 IOPS（4k，队列32）
fio --name=randread --rw=randread --bs=4k --iodepth=32 \
    --size=1G --numjobs=4 --runtime=60 --group_reporting --filename=/data/testfile

# 顺序写吞吐
fio --name=seqwrite --rw=write --bs=1M --iodepth=16 \
    --size=2G --runtime=60 --group_reporting --filename=/data/testfile

# 随机读写混合 70/30
fio --name=randrw --rw=randrw --rwmixread=70 --bs=4k --iodepth=32 \
    --size=1G --runtime=60 --group_reporting --filename=/data/testfile
```

## 关键参数

| 参数 | 含义 |
|---|---|
| `--rw` | read/write/randread/randwrite/randrw |
| `--bs` | 块大小（IOPS 用 4k，吞吐用 1M） |
| `--iodepth` | 队列深度（并发 IO 数） |
| `--numjobs` | 并行任务数 |
| `--size` | 测试文件大小 |
| `--runtime` | 持续秒数 |
| `--direct=1` | 绕过页缓存（测真实磁盘） |
| `--group_reporting` | 汇总报告 |

## 看结果

- **IOPS**：每秒 IO 次数（随机小 IO 关键指标）。
- **BW**：带宽（顺序大 IO 关键）。
- **lat/clat**：延迟（clat 完成延迟，看 p99）。
- **slat**：提交延迟。

::: danger 别在生产数据盘上压测
fio 会写测试文件、占满 IO，影响业务。用独立测试盘/文件，测完删 testfile。--direct=1 才测到真实磁盘（否则测的是内存缓存）。
:::

## 运维实战

**验收新 SSD**：4k 随机读 IOPS 对比厂商标称，差距大查驱动/队列/对齐。
**复现数据库 IO 瓶颈**：用接近业务的 bs/iodepth/读写比压测，看 await 是否达标。
**对比云盘规格**：不同云盘 ESSD PL 级别压测对比，选性价比。

## 相关命令

[iostat/iotop](./iotop) · [smartctl](/commands/storage/smartctl) · [dd](/commands/storage/) · [stress-ng](./stress-ng)

## 官方文档

- fio：<https://fio.readthedocs.io/en/latest/>
- fio man：<https://man7.org/linux/man-pages/man1/fio.1.html>