---
title: "head · 看文件开头"
description: "head 看前 N 行（默认10）、-n 行数/-c 字节、多文件、管道取前几条。快速预览，中文详解。"
---

# head · 看文件开头

> 命令手册 · [文件与文本](/commands/basic/) ｜ 频率：每天用
> 看文件前几行预览内容/表头，或管道里取前 N 条结果。与 tail（看尾部）对应。

## 一句话用途

输出文件开头若干行（默认 10 行）。

## 高频场景速查

```bash
head file.txt                    # 前 10 行
head -n 20 file.txt              # 前 20 行
head -n 5 a.txt b.txt            # 多文件各前5行（带文件名头）
head -c 100 file                 # 前 100 字节
ls -lh | head                    # 管道取前几条
du -ah | sort -rh | head -10     # 找最大的10个（配合 sort）
```

## 参数详解

| 参数 | 含义 |
|---|---|
| `-n N` | 前 N 行（`-N` 简写） |
| `-c N` | 前 N 字节 |
| `-q` | 不显示文件名头 |
| `-v` | 总是显示文件名头 |

## 运维实战

**预览 CSV 表头**：`head -n 3 data.csv` 看列名与样例。
**找最大文件**：`du -ah /data | sort -rh | head -20`（[du](/commands/storage/du)+[sort](./sort)）。
**取 Top N 进程**：`ps aux --sort=-%mem | head -11`（含表头）。
**看日志开头**：head 看启动日志，tail 看最新（[tail](./tail)）。

## 相关命令

[tail](./tail) · [less](./less) · [cat](./cat) · [sort](./sort) · [wc](./wc)

## 官方文档

- head：<https://man7.org/linux/man-pages/man1/head.1.html>