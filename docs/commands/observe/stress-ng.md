---
title: "stress-ng · 系统压测"
description: "stress-ng 压 CPU/内存/IO/上下文切换、复现高负载、验证监控告警与稳定性。比 stress 更全面，中文详解。"
---

# stress-ng · 系统压测

> 命令手册 · [排障观测](/commands/observe/) ｜ 频率：很少用
> 想复现"CPU 满载""内存吃紧"来验证监控告警、测试调度？stress-ng 按需制造各种压力。

## 一句话用途

人为制造 CPU/内存/IO 等压力，复现高负载场景、验证告警与稳定性。

## 高频场景速查

```bash
stress-ng --cpu 4 --timeout 60s          # 4核满载60秒
stress-ng --cpu 2 --cpu-load 50 --timeout 30s   # 2核各50%
stress-ng --vm 2 --vm-bytes 1G --timeout 60s    # 内存压力（2进程各1G）
stress-ng --io 4 --timeout 30s           # IO 压力
stress-ng --hdd 2 --hdd-bytes 1G --timeout 30s  # 磁盘写压力
stress-ng --switch 4 --timeout 30s       # 上下文切换压力
stress-ng --metrics-brief --cpu 2 --timeout 10s # 带指标
```

## 常用压力器

| 参数 | 压什么 |
|---|---|
| `--cpu N` | N 个 CPU 满载进程 |
| `--cpu-load P` | CPU 占用百分比 |
| `--vm N --vm-bytes` | 内存分配压力 |
| `--io N` | sync IO 压力 |
| `--hdd N` | 磁盘读写 |
| `--switch N` | 上下文切换 |
| `--timeout` | 持续时间（必设，别无限） |

## 运维实战

**验证监控告警**：压 CPU 到 90% 看 Prometheus 告警是否触发（[Prometheus](/services/observability/prometheus/04-实战)）。
**测试 OOM 行为**：--vm 超物理内存，观察 OOM killer 杀谁（[dmesg](/commands/system/dmesg)）。
**验证资源限制**：容器/cgroup 限额下压测，确认限制生效。

::: danger 生产慎用
stress-ng 会真占资源，生产上压测可能拖垮业务。在测试环境/隔离容器跑，必设 --timeout 自动停。压内存可能触发 OOM 杀其他进程。
:::

## 相关命令

[fio 磁盘压测](./fio) · [vmstat](./vmstat) · [top/htop](/commands/system/htop) · [nice/ionice](/commands/system/nice-renice)

## 官方文档

- stress-ng：<https://github.com/ColinIanKing/stress-ng>
- man：<https://man7.org/linux/man-pages/man1/stress-ng.1.html>