---
title: "iostat / iotop · IO 性能定位"
description: "iostat 看磁盘 %util/await/r/s w/s 判断 IO 瓶颈、iotop 定位哪个进程在读写。磁盘慢/IO 等待排障，中文详解。"
---

# iostat / iotop · IO 性能定位

> 命令手册 · [排障观测](/commands/observe/) ｜ 频率：偶尔用
> vmstat 看到 wa 高、b 高，说明卡在 IO。iostat 看哪块盘忙、iotop 看哪个进程在读写。

## 一句话用途

iostat 看磁盘整体负载与延迟，iotop 定位到具体进程的 IO。

## 高频场景速查

```bash
iostat -xz 2             # 每2秒，扩展统计，只看活跃盘（需 sysstat）
iostat -dx 2             # 含设备利用率
iotop                    # 交互看进程 IO（需 root）
iotop -o                 # 只显示有 IO 的进程
iotop -P                 # 按进程而非线程
pidstat -d 2             # 进程级 IO 统计
```

## iostat 关键列（重点）

| 列 | 含义 | 异常信号 |
|---|---|---|
| `r/s` `w/s` | 每秒读/写次数（IOPS） | — |
| `rkB/s` `wkB/s` | 每秒读/写吞吐 | — |
| `await` | IO 平均等待毫秒 | 高 = 延迟大 |
| `r_await`/`w_await` | 读/写各自延迟 | — |
| `%util` | 设备繁忙度 | 接近100% = 饱和 |
| `aqu-sz` | 平均队列深度 | 高 = 排队 |

::: tip %util 与 await 结合看
%util 100% 不一定瓶颈（SSD 能并行），要结合 await：await 高（如 >20ms 机械盘/>5ms SSD）且队列深，才是真饱和。SSD 的 %util 参考意义弱于 await。
:::

## 运维实战

**数据库慢查 IO**：`iostat -xz 2` 看数据盘 await 是否飙升，`iotop -o` 看是不是备份/大查询在抢 IO。
**定位刷盘进程**：iotop 按 DISK WRITE 排序，揪出疯狂写的进程。
**确认磁盘饱和**：%util 长期 100 + await 高 + aqu-sz 深 → 换 SSD/加盘/分散 IO。

## 相关命令

[vmstat](./vmstat) · [pidstat](./pidstat-mpstat) · [df/du](/commands/storage/df) · [smartctl](/commands/storage/smartctl) · [fio 压测](./fio)

## 官方文档

- iostat：<https://man7.org/linux/man-pages/man1/iostat.1.html>
- iotop：<https://man7.org/linux/man-pages/man1/iotop.1.html>