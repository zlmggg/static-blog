---
title: "pmap / smem / slabtop · 内存细节"
description: "pmap 看进程内存映射、smem 看 PSS/USS 真实占用（去共享）、slabtop 看内核 slab。排「内存到底谁用了」，中文详解。"
---

# pmap / smem / slabtop · 内存细节

> 命令手册 · [排障观测](/commands/observe/) ｜ 频率：很少用
> free 看总量，但"每个进程真实占多少"要看 PSS/USS——共享库被多进程共用，RSS 会重复算。smem 给你去重后的真实值。

## 一句话用途

深入看内存：进程映射明细、去共享后的真实占用、内核 slab 缓存。

## 高频场景速查

```bash
pmap -x 1234               # 进程内存映射（含 RSS）
pmap -X 1234               # 更详细
smem -k                    # 按进程看 PSS/USS（需装 smem）
smem -k -s pss -r          # 按 PSS 排序
smem -k -P nginx           # 只看 nginx
sudo slabtop               # 内核 slab 缓存（dentry/inode）
cat /proc/meminfo          # 含 Slab/SReclaimable
```

## RSS vs PSS vs USS（重点）

| 指标 | 含义 |
|---|---|
| `VSZ/VIRT` | 虚拟内存（含未分配/映射，参考意义弱） |
| `RSS` | 常驻物理内存（**共享库重复算**） |
| `PSS` | 比例分摊共享后的占用（**最公平**） |
| `USS` | 进程独占内存（杀掉能释放的） |

::: tip 为什么 RSS 加起来超总量
10 个进程都用 libc，RSS 各算一份 libc，加起来远超实际。PSS 把共享部分按进程数分摊，所有进程 PSS 之和才接近真实用量。看真实占用用 smem 的 PSS。
:::

## slabtop

内核对象缓存（dentry/inode 等）。`SReclaimable` 大说明缓存了大量文件元数据，可回收。大量小文件操作后 dentry 缓存涨是正常的。

## 运维实战

**找真实内存大户**：`smem -k -s pss -r | head` 按 PSS 排序，比 top 的 RSS 准。
**判断杀进程能释放多少**：看 USS（独占部分）。
**内存被缓存吃了**：/proc/meminfo 的 Slab/SReclaimable 大，是内核缓存非泄漏。

## 相关命令

[free](./free) · [pmap/proc](./proc) · [top/htop](/commands/system/htop) · [jmap JVM 堆](./jvm)

## 官方文档

- pmap：<https://man7.org/linux/man-pages/man1/pmap.1.html>
- smem：<https://man7.org/linux/man-pages/man8/smem.8.html>
- slabtop：<https://man7.org/linux/man-pages/man1/slabtop.1.html>