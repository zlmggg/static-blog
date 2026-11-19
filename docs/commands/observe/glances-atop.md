---
title: "glances / atop / dstat · 综合监控"
description: "glances 一屏看 CPU/内存/IO/网络/进程、atop 历史记录回放、dstat/nmon 多指标实时。综合性能仪表盘，中文详解。"
---

# glances / atop / dstat · 综合监控

> 命令手册 · [排障观测](/commands/observe/) ｜ 频率：偶尔用
> 不想同时开 top/iostat/iftop 几个窗口？glances 一屏全有；atop 还能像 sar 一样回放历史。

## 一句话用途

一个工具看全系统多维指标，atop 额外支持历史回放。

## 高频场景速查

```bash
glances                    # 一屏综合（CPU/内存/IO/网络/进程/告警）
glances -w                 # Web 模式（浏览器看）
glances --export prometheus  # 暴露给 Prometheus
atop                       # 综合+历史（需 atop 服务采集）
atop -r /var/log/atop/atop_20261118 -b 02:00   # 回放18号2点
dstat -cdnm                # CPU/磁盘/网络/内存实时（已停止维护）
nmon                       # IBM 出品综合监控（按 c/m/d/n 切视图）
```

## 工具对比

| 工具 | 特点 |
|---|---|
| `glances` | 一屏全、可 Web/导出、Python |
| `atop` | 综合+**历史回放**、进程级累计 |
| `dstat` | 多列实时、已停维护（用 pcstat 替代） |
| `nmon` | 交互式切换视图、可录数据 |

## atop 历史回放（亮点）

atop 服务默认每 10 分钟快照（含进程级），出事能回放：

```bash
sudo systemctl enable --now atop
atop -r                    # 读今天
# 交互里按 t 前进、T 后退、b 跳时间
```

比 sar 多了**进程级**历史——能看到当时哪个进程在吃资源。

## 运维实战

**快速体检**：glances 一屏扫 CPU/内存/IO/网络有无红字告警。
**复盘故障时刻**：atop -r 回放，看当时进程级资源占用（sar 只有系统级）。
**临时给别人看**：glances -w 起 Web，团队浏览器围观。

## 相关命令

[vmstat](./vmstat) · [sar](./sar) · [top/htop](/commands/system/htop) · [Prometheus](/services/observability/prometheus/01-理论)

## 官方文档

- glances：<https://nicolargo.github.io/glances/>
- atop：<https://www.atoptool.nl/>
- nmon：<https://nmon.sourceforge.io/>