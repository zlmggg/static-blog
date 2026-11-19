---
title: "wc · 统计行/词/字节"
description: "wc -l 行数/-w 词数/-c 字节/-m 字符、统计日志条数/文件数。计数基础，中文详解。"
---

# wc · 统计行/词/字节

> 命令手册 · [文件与文本](/commands/basic/) ｜ 频率：每天用
> 数日志多少行、文件多少个、内容多大——wc（word count）。-l 数行最常用。

## 一句话用途

统计文件的行数、词数、字节数。

## 高频场景速查

```bash
wc -l app.log                    # 行数（日志条数）
wc -l *.log                      # 多文件各自行数+总计
wc -w file.txt                   # 词数
wc -c file                       # 字节数
wc -m file                       # 字符数（中文友好）
grep ERROR app.log | wc -l       # 错误条数
ls /etc | wc -l                  # 文件个数
find . -name '*.log' | wc -l     # 日志文件数
```

## 参数详解

| 参数 | 含义 |
|---|---|
| `-l` | 行数（最常用） |
| `-w` | 词数（空白分隔） |
| `-c` | 字节数 |
| `-m` | 字符数（多字节正确） |
| `-L` | 最长行长度 |

::: tip 中文用 -m 不用 -c
-c 数字节（中文 UTF-8 一字3字节），-m 数字符。统计中文字数用 -m。wc -l 数行不受影响。
:::

## 运维实战

**统计错误数**：`grep -c ERROR app.log`（grep -c 更直接）或 `grep ERROR | wc -l`。
**统计文件数**：`find /data -type f | wc -l`。
**看日志规模**：`wc -l /var/log/*.log` 评估日志量。
**对比行数**：处理前后 wc -l 确认没丢行。

## 相关命令

[grep](./grep) · [find](./find) · [sort](./sort) · [uniq](./uniq) · [head](./head)

## 官方文档

- wc：<https://man7.org/linux/man-pages/man1/wc.1.html>