---
title: "ionice · IO 调度优先级"
description: "ionice 设进程 IO 优先级（realtime/best-effort/idle 三类）、让备份不抢业务磁盘。与 nice 配合，中文详解。"
---

# ionice · IO 调度优先级

> 命令手册 · [排障观测](/commands/observe/) ｜ 频率：很少用
> nice 管 CPU 优先级，ionice 管磁盘 IO 优先级。让备份/扫描在磁盘空闲时才读写，不抢业务。

## 一句话用途

设置进程的 IO 调度类别与优先级，控制谁先读写磁盘。

## 高频场景速查

```bash
ionice -c 3 ./backup.sh          # idle 类：磁盘空闲才 IO
ionice -c 2 -n 7 ./scan.sh       # best-effort 最低优先级（0-7）
ionice -c 1 -n 0 ./critical.sh   # realtime 最高（慎用，可能饿死其他）
ionice -p 1234                   # 看进程 IO 优先级
sudo ionice -c 3 -p 1234         # 改运行中进程为 idle
nice -n 19 ionice -c 3 ./backup.sh   # CPU+IO 都让着业务
```

## 三个调度类

| 类 | -c | 含义 |
|---|---|---|
| realtime | 1 | 最高，优先抢占磁盘（危险） |
| best-effort | 2 | 默认，按优先级 0-7 轮转 |
| idle | 3 | 只在没人用磁盘时 IO |

best-effort 的 `-n 0~7`：0 最高、7 最低。

::: warning realtime 类慎用
-c 1 会让进程几乎独占磁盘，其他进程 IO 被饿死。除非明确需要（如紧急恢复），否则用 idle/best-effort。
:::

## 运维实战

**备份不抢业务**：`nice -n 19 ionice -c 3 ./backup.sh`，CPU 和 IO 都最低，业务无感。
**全盘扫描错峰**：updatedb/杀毒扫描设 idle，避免拖慢在线服务。
**注意调度器**：ionice 对 CFQ/BFQ 调度器有效；NVMe 常用 none/mq-deadline，ionice 效果有限（看 /sys/block/*/queue/scheduler）。

## 相关命令

[nice/renice/taskset](/commands/system/nice-renice) · [iostat/iotop](./iotop) · [fio](./fio) · [systemd IO 控制](/commands/system/systemctl-journalctl)

## 官方文档

- ionice：<https://man7.org/linux/man-pages/man1/ionice.1.html>