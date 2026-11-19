---
title: "htop · 交互式进程监控"
description: "htop 彩色交互看进程、排序/过滤/树视图、按键操作、对比 top。比 top 直观的实时进程监控，中文详解。"
---

# htop · 交互式进程监控

> 命令手册 · [进程与系统](/commands/system/) ｜ 频率：每天用
> top 的增强版：彩色、可鼠标、可滚动、按键操作直观。看"谁在吃 CPU/内存"比 top 顺手。

## 一句话用途

交互式实时看进程资源占用，排序、过滤、杀进程一站式。

## 高频场景速查

```bash
htop                     # 启动（需安装 dnf/apt install htop）
htop -u rocky            # 只看某用户进程
htop -p 1234,5678        # 只看指定 PID
htop -t                  # 树视图（看父子关系）
```

## 界面按键

| 键 | 作用 |
|---|---|
| `F6` / `>` | 选排序字段（CPU%/MEM%） |
| `F4` / `\` | 过滤进程名 |
| `F5` / `t` | 树视图切换 |
| `F9` / `k` | 发信号杀进程 |
| `F3` / `/` | 搜索 |
| `Space` | 标记多个 |
| `F10` / `q` | 退出 |
| `H` | 隐藏用户线程 |
| `K` | 隐藏内核线程 |

## 看什么

- 顶部条：每核 CPU 使用率、内存、Swap、负载、运行时间。
- 进程列：PID、USER、CPU%、MEM%、RES（常驻内存）、命令。
- **RES 才是真实占用内存**，VIRT 含映射/共享别被吓到。

::: tip htop vs top
top 默认就有、无需装；htop 要装但交互友好。脚本里取快照用 `top -bn1`，交互排障用 htop。两者数据源都是 /proc。
:::

## 运维实战

**找吃 CPU 的进程**：htop 按 F6 选 PERCENT_CPU 排序，一眼看到头部。
**找吃内存的进程**：按 PERCENT_MEM 排序，看 RES 列。
**杀卡死进程**：光标选中按 F9 选 TERM/KILL。

## 相关命令

[top](./top) · [ps](./ps) · [kill](./kill) · [free/vmstat](/commands/observe/)

## 官方文档

- htop：<https://htop.dev/>
- man htop：<https://man7.org/linux/man-pages/man1/htop.1.html>