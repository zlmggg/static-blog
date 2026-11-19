---
title: "free · 内存查看"
description: "free -h 看内存、buff/cache 与 available 的真正含义、Swap 使用判断、内存不足定位。别再被 used 吓到，中文详解。"
---

# free · 内存查看

> 命令手册 · [排障观测](/commands/observe/) ｜ 频率：每天用
> "内存快满了！"——先看 free 的 available，不是 used。Linux 会把空闲内存拿去做缓存，那是好事不是浪费。

## 一句话用途

看物理内存和 Swap 的使用情况，判断到底缺不缺内存。

## 高频场景速查

```bash
free -h                  # 人类可读（G/M）
free -m                  # 以 MB
free -h -s 2             # 每2秒刷新
free -w                  # 宽输出（buffers/cache 分开）
```

## 输出解读（重点）

```text
              total    used    free   shared  buff/cache   available
Mem:           15Gi    4Gi    1Gi    0.2Gi       10Gi        10Gi
Swap:           2Gi    0Gi    2Gi
```

| 列 | 含义 |
|---|---|
| `used` | 进程实际用的 |
| `free` | 完全空闲（没被利用） |
| `buff/cache` | 内核缓冲+页缓存（**可回收**） |
| `available` | **真正可用**（含可回收缓存） |

::: danger 看 available 不是 free
Linux 把空闲内存做 buff/cache 加速 IO，需要时自动回收。`free` 小不代表内存不足，`available` 才反映真实可用。available 充足就没事。
:::

## 判断内存压力

- **available 充足**：健康，buff/cache 大是好事。
- **available 很低 + Swap 在用**：内存紧张，进程可能被 OOM。
- **Swap 大量使用 + si/so 高**（[vmstat](./vmstat)）：在频繁换页，性能差，加内存。

## 运维实战

**排 OOM**：free 看 available 是否枯竭，配合 [dmesg](/commands/system/dmesg) 查 OOM 记录。
**找吃内存进程**：`ps aux --sort=-%mem | head` 或 [htop](/commands/system/htop) 按 MEM 排序。
**数据库机器**：关注 available 与 Swap，swappiness 调低减少换页（[sysctl](/commands/system/sysctl)）。

## 相关命令

[vmstat](./vmstat) · [top/htop](/commands/system/htop) · [pmap/smem](./pmap-smem) · [dmesg OOM](/commands/system/dmesg)

## 官方文档

- free：<https://man7.org/linux/man-pages/man1/free.1.html>