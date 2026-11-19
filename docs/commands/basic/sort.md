---
title: "sort · 排序"
description: "sort 按列/数值/逆序排序、-t 分隔符 -k 列、-n 数值 -h 人类可读 -u 去重、-o 输出。统计排行必备，中文详解。"
---

# sort · 排序

> 命令手册 · [文件与文本](/commands/basic/) ｜ 频率：每天用
> 排序是统计的前置：找最大文件、Top N 访问 IP、按数值排——都先 sort。常配 uniq 去重计数。

## 一句话用途

对文本行排序（字典序/数值/指定列）。

## 高频场景速查

```bash
sort file.txt                    # 字典序
sort -n nums.txt                 # 数值排序
sort -r file.txt                 # 逆序
sort -u file.txt                 # 排序+去重
sort -t ':' -k 3 -n /etc/passwd  # 按第3列数值（UID）
sort -k 2 -n data.txt            # 按第2列数值
du -ah | sort -rh | head         # 人类可读大小逆序（找最大）
sort -o sorted.txt input.txt     # 输出到文件
```

## 参数详解

| 参数 | 含义 |
|---|---|
| `-n` | 数值排序（否则字典序 10<2） |
| `-h` | 人类可读（1K<2M<3G） |
| `-r` | 逆序 |
| `-u` | 去重 |
| `-t 分隔符` | 列分隔符 |
| `-k N` | 按第 N 列（可 -k 2,2 精确） |
| `-f` | 忽略大小写 |
| `-o 文件` | 输出到文件（可同输入） |
| `-V` | 版本号排序 |

::: danger 数值要加 -n
默认字典序：10 排在 2 前面。排数字（UID/端口/大小）必须 -n，排带单位大小用 -h。漏 -n 排行就错。
:::

## 运维实战

**Top 访问 IP**：`awk '{print $1}' access.log | sort | uniq -c | sort -rn | head`（[uniq](./uniq)）。
**找最大文件**：`du -ah | sort -rh | head -20`。
**按 UID 排账号**：`sort -t: -k3 -n /etc/passwd`。
**版本排序**：`ls | sort -V` 让 v1.2 在 v1.10 前。

## 相关命令

[uniq](./uniq) · [awk](./awk) · [cut](./cut) · [head](./head) · [wc](./wc)

## 官方文档

- sort：<https://man7.org/linux/man-pages/man1/sort.1.html>