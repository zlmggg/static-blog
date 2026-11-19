---
title: "systemd-analyze · 启动分析"
description: "systemd-analyze time/blame/critical-chain 分析开机耗时、定位慢服务、verify 校验 unit。排「开机慢」，中文详解。"
---

# systemd-analyze · 启动分析

> 命令手册 · [进程与系统](/commands/system/) ｜ 频率：很少用
> 开机慢？systemd-analyze 告诉你时间花在哪、哪个服务拖后腿，不用瞎猜。

## 一句话用途

分析系统启动耗时，定位拖慢开机的服务，校验 unit 文件。

## 高频场景速查

```bash
systemd-analyze                    # 总启动耗时（内核+用户空间）
systemd-analyze blame              # 各服务耗时排序（找最慢）
systemd-analyze critical-chain     # 关键路径（串行依赖链）
systemd-analyze critical-chain nginx.service   # 某服务的依赖链
systemd-analyze verify nginx.service           # 校验 unit 语法
systemd-analyze plot > boot.svg    # 启动时序图
```

## 子命令职责

| 子命令 | 作用 |
|---|---|
| `time` | 总耗时（默认） |
| `blame` | 按耗时排序列服务 |
| `critical-chain` | 关键依赖链（真正决定总时长的） |
| `verify` | 检查 unit 文件错误 |
| `plot` | SVG 时序图 |
| `dot` | 依赖图（graphviz） |

::: tip blame vs critical-chain
blame 列每个服务自身耗时，但并行启动的服务耗时长不一定拖慢总时长。critical-chain 才显示**串行关键路径**——真正卡住启动的那条链。两者结合看。
:::

## 运维实战

**开机慢定位**：`systemd-analyze blame | head` 看头部，常见是 NetworkManager-wait-online、某个挂载超时。
**禁用拖慢的服务**：确认不需要后 `systemctl disable xxx`。
**改 unit 后校验**：`systemd-analyze verify` 提前发现语法错，避免重启起不来。

## 相关命令

[systemctl/journalctl](./systemctl-journalctl) · [dmesg](./dmesg) · [uptime](./uptime-uname)

## 官方文档

- systemd-analyze：<https://www.freedesktop.org/software/systemd/man/latest/systemd-analyze.html>