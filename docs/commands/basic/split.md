---
title: "split · 分割大文件"
description: "split 按行/大小切大文件、-l 行数/-b 大小/-d 数字后缀、cat 合并。超大日志/传输分片，中文详解。"
---

# split · 分割大文件

> 命令手册 · [文件与文本](/commands/basic/) ｜ 频率：很少用
> 几个 G 的日志/数据太大不好传/不好处理，split 切成小块。处理完 cat 合并回去。

## 一句话用途

把大文件按行数或大小切成多个小文件。

## 高频场景速查

```bash
split -l 100000 big.log part_        # 每 10 万行一块
split -b 100M big.tar part_          # 每 100M 一块
split -d -l 1000 big.log part_       # 数字后缀（part_00...）
split -n 10 big.log part_            # 均分成 10 块
cat part_* > restored.log            # 合并还原
```

## 参数详解

| 参数 | 含义 |
|---|---|
| `-l N` | 每块 N 行 |
| `-b 大小` | 每块字节（100M/1G） |
| `-n N` | 均分 N 块 |
| `-d` | 数字后缀（默认字母 aa/ab） |
| `-a N` | 后缀长度 |
| `--additional-suffix=.log` | 加扩展名 |

## 运维实战

**大日志分片处理**：split -l 切块 → 并行 grep/awk 各块 → 汇总。
**受限传输**：单文件传输有大小限制，split -b 分片传，对端 cat 合并。
**数据库导出分片**：大 SQL dump 切块便于并行导入。
**校验合并**：合并后 md5sum 对比原文件（[md5sum](./md5sum-sha256sum)）。

::: tip 合并顺序
split 默认后缀 aa/ab... 按字典序，`cat part_*` 通配展开顺序正确。用 -d 数字后缀注意位数对齐（part_00 vs part_100 排序），-a 设足够长度。
:::

## 相关命令

[cat](./cat) · [tar](./tar) · [md5sum/sha256sum](./md5sum-sha256sum) · [head](./head) · [wc](./wc)

## 官方文档

- split：<https://man7.org/linux/man-pages/man1/split.1.html>