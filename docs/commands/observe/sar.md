---
title: "sar · 历史性能回溯"
description: "sar 查历史 CPU/内存/IO/网络/负载（sysstat 采集）、-f 读某天数据、事后复盘「昨晚为什么卡」。中文详解。"
---

# sar · 历史性能回溯

> 命令手册 · [排障观测](/commands/observe/) ｜ 频率：偶尔用
> 凌晨 3 点服务卡了，现在才查——top/vmstat 只能看当下，sar 能回放历史。前提是 sysstat 在采集。

## 一句话用途

查看系统历史性能数据，事后复盘某个时间点发生了什么。

## 高频场景速查

```bash
sar -u                   # 今天 CPU 历史
sar -r                   # 内存历史
sar -b                   # IO 历史
sar -n DEV               # 网络流量历史
sar -q                   # 负载历史
sar -u -f /var/log/sa/sa18   # 读18号的数据
sar -u -s 02:00 -e 04:00     # 只看某时段
```

## 选项

| 选项 | 看什么 |
|---|---|
| `-u` | CPU |
| `-r` | 内存 |
| `-b` | IO 总量 |
| `-d` | 块设备 |
| `-n DEV` | 网卡流量 |
| `-n TCP,ETCP` | TCP 连接/重传 |
| `-q` | 队列/负载 |
| `-B` | 换页 |
| `-f 文件` | 读指定日期 |
| `-s/-e` | 起止时间 |

## 启用采集

```bash
sudo systemctl enable --now sysstat     # 启采集（默认每10分钟）
# /etc/cron.d/sysstat 调采集频率
# 数据存 /var/log/sa/saDD（DD=日期）
```

::: warning 没启 sysstat 就没历史
sar 依赖 sysstat 定时采集。没启的话只能看当下（等于 vmstat）。生产建议启用，出事才有据可查。默认保留约一个月。
:::

## 运维实战

**复盘凌晨故障**：`sar -u -f /var/log/sa/sa18 -s 02:00 -e 04:00` 看那段时间 CPU/wa，`sar -r` 看内存是否枯竭。
**网络重传排查**：`sar -n ETCP` 看 retrans/s 是否飙升。
**容量趋势**：sar 内存/磁盘历史判断增长趋势，提前扩容。

## 相关命令

[vmstat](./vmstat) · [iostat](./iotop) · [pidstat/mpstat](./pidstat-mpstat) · [Prometheus 长期监控](/services/observability/prometheus/01-理论)

## 官方文档

- sar：<https://man7.org/linux/man-pages/man1/sar.1.html>
- sysstat：<https://github.com/sysstat/sysstat>