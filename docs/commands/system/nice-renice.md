---
title: "nice / renice / taskset · 优先级与绑核"
description: "nice/renice 调进程 CPU 优先级（-20~19）、taskset 绑核、ionice IO 优先级。让关键服务优先、压测不抢资源，中文详解。"
---

# nice / renice / taskset · 优先级与绑核

> 命令手册 · [进程与系统](/commands/system/) ｜ 频率：很少用
> 让重要服务多抢 CPU、让备份/压测少抢；把进程绑到指定核减少缓存抖动。

## 一句话用途

调整进程 CPU 调度优先级、绑定 CPU 核、调 IO 优先级。

## 高频场景速查

```bash
nice -n 10 ./backup.sh           # 以低优先级启动（nice 值越大越谦让）
sudo renice -n -5 -p 1234        # 提高已运行进程优先级
sudo renice -n 10 -u backupuser  # 调某用户所有进程
taskset -c 0,1 ./app             # 绑到 0、1 号核
taskset -cp 1234                 # 看进程绑了哪些核
sudo taskset -cp 0-3 1234        # 改进程绑核
```

## nice 值

范围 **-20（最高优先级）到 19（最低）**，默认 0。普通用户只能调高 nice 值（降低优先级），调低（提权）需 root。

| 命令 | 作用 |
|---|---|
| `nice -n N cmd` | 以 nice N 启动 |
| `renice -n N -p PID` | 改运行中进程 |
| `renice -n N -u 用户` | 改某用户全部 |

## taskset 绑核

```bash
taskset -c 0-3 cmd       # 绑 0~3 核
taskset -c 0,2,4 cmd     # 绑指定核
```

绑核减少跨核迁移与缓存失效，低延迟场景（DPDK/实时）有用；普通服务一般不用。

## ionice（IO 优先级）

```bash
ionice -c 3 ./backup.sh        # idle 类：只在磁盘空闲时 IO
ionice -c 2 -n 7 ./scan.sh     # best-effort 最低
```

## 运维实战

**备份不抢业务资源**：`nice -n 19 ionice -c 3 ./backup.sh`，CPU 和 IO 都让着业务。
**关键服务提优先级**：`renice -n -5 -p $(pgrep nginx)`（谨慎，可能饿死其他）。

::: tip 易错点
nice 只影响 CPU 调度权重，不是硬限制；要硬限 CPU 用 cgroup（systemd CPUQuota）。绑核不当反而限制吞吐，普通服务别乱绑。
:::

## 相关命令

[kill](./kill) · [top/htop](./htop) · [systemctl 资源控制](./systemctl-journalctl) · [stress-ng](/commands/observe/)

## 官方文档

- nice：<https://man7.org/linux/man-pages/man1/nice.1.html>
- taskset：<https://man7.org/linux/man-pages/man1/taskset.1.html>