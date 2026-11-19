---
title: "gzip / bzip2 / xz · 单文件压缩"
description: "gzip/bzip2/xz 压缩单文件、-k 保留原文件/-d 解压、压缩率与速度权衡、配合 tar。压缩三选一，中文详解。"
---

# gzip / bzip2 / xz · 单文件压缩

> 命令手册 · [文件与文本](/commands/basic/) ｜ 频率：每天用
> 压缩单个文件（不是打包）。gzip 快、xz 压缩率高、bzip2 居中。多文件打包用 tar（[tar](./tar)）。

## 一句话用途

压缩/解压单个文件。

## 三者权衡

| 工具 | 速度 | 压缩率 | 扩展名 | 适用 |
|---|---|---|---|---|
| gzip | 快 | 中 | .gz | 日常/日志 |
| bzip2 | 中 | 较高 | .bz2 | 较少用 |
| xz | 慢 | 高 | .xz | 归档/分发 |

## 高频场景速查

```bash
gzip file.txt                    # 压缩成 file.txt.gz（删原文件）
gzip -k file.txt                 # 保留原文件
gzip -d file.txt.gz              # 解压（= gunzip）
gzip -9 file.txt                 # 最高压缩率
xz file.txt                      # 压缩成 .xz
xz -d file.txt.xz                # 解压
xz -k -T0 file.txt               # 保留+多线程
bzip2 file.txt                   # 压缩成 .bz2
```

## 参数详解

| 参数 | 含义 |
|---|---|
| `-k` | 保留原文件（默认删！） |
| `-d` | 解压 |
| `-1`~`-9` | 压缩级别（1快9小） |
| `-T0` | 多线程（xz） |
| `-c` | 输出到 stdout（不删原文件） |
| `-l` | 看压缩信息 |

::: danger 默认删原文件
gzip/xz 压缩后**默认删除原文件**！要保留加 -k。解压同理删压缩包。脚本里注意，别压完发现原文件没了。
:::

## 运维实战

**压缩日志**：`gzip -k app.log` 保留原文件归档。
**高压缩归档**：`xz -T0 backup.tar` 多线程压 tar（[tar](./tar)）。
**管道压缩**：`tar cf - /data | gzip > data.tar.gz`。
**看压缩内容不解压**：`zcat file.gz`、`xzcat file.xz`。

## 相关命令

[tar](./tar) · [zip/unzip](./zip-unzip) · [cp](./cp) · [logrotate](/commands/storage/logrotate)

## 官方文档

- gzip：<https://man7.org/linux/man-pages/man1/gzip.1.html>
- xz：<https://man7.org/linux/man-pages/man1/xz.1.html>