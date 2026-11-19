---
title: "uniq · 去重与计数"
description: "uniq 去相邻重复行、-c 计数/-d 只显重复/-u 只显唯一。必须先 sort，统计频次经典组合，中文详解。"
---

# uniq · 去重与计数

> 命令手册 · [文件与文本](/commands/basic/) ｜ 频率：每天用
> 统计"每个值出现几次"——uniq -c。但它只去**相邻**重复，所以前面必须先 sort。

## 一句话用途

去除/统计相邻重复行（常与 sort 连用）。

## 高频场景速查

```bash
sort file | uniq                 # 去重
sort file | uniq -c              # 计数（每行前加次数）
sort file | uniq -d              # 只显示重复过的行
sort file | uniq -u              # 只显示没重复的行
sort file | uniq -c | sort -rn   # 按频次排行（经典）
uniq -i file                     # 忽略大小写
uniq -f 1 file                   # 跳过第1列比较
```

## 参数详解

| 参数 | 含义 |
|---|---|
| `-c` | 每行前加出现次数 |
| `-d` | 只输出重复行 |
| `-u` | 只输出唯一行 |
| `-i` | 忽略大小写 |
| `-f N` | 跳过前 N 列 |
| `-s N` | 跳过前 N 字符 |

::: danger 必须先 sort
uniq 只合并**相邻**重复。不 sort 直接 uniq，分散的重复去不掉。`sort | uniq` 是固定搭配。sort -u 可一步去重（但不计数）。
:::

## 运维实战

**统计访问 IP Top10**：`awk '{print $1}' access.log | sort | uniq -c | sort -rn | head -10`。
**统计错误类型**：`grep ERROR app.log | awk '{print $5}' | sort | uniq -c | sort -rn`。
**找重复配置**：`sort conf | uniq -d` 看哪些行重复。

## 相关命令

[sort](./sort) · [awk](./awk) · [grep](./grep) · [wc](./wc) · [cut](./cut)

## 官方文档

- uniq：<https://man7.org/linux/man-pages/man1/uniq.1.html>