---
title: "xargs · 把输入变参数"
description: "xargs 把 stdin 转成命令参数、-I 占位/-n 分组/-P 并行、-0 配 find -print0 处理空格文件名。管道批量执行核心，中文详解。"
---

# xargs · 把输入变参数

> 命令手册 · [文件与文本](/commands/basic/) ｜ 频率：每天用
> find/grep 输出一堆文件名，怎么批量传给 rm/grep？xargs 把标准输入转成命令参数。批量操作的核心枢纽。

## 一句话用途

把标准输入的内容作为参数传给其他命令。

## 高频场景速查

```bash
find . -name '*.tmp' | xargs rm           # 批量删
find . -name '*.log' | xargs grep ERROR   # 批量搜
ls *.jpg | xargs -I {} cp {} /backup/     # 占位符逐个处理
cat urls.txt | xargs -n 1 curl -O         # 每行一个参数
cat files | xargs -P 4 -I {} gzip {}      # 4 路并行
find . -name '*.txt' -print0 | xargs -0 rm   # 处理含空格文件名
```

## 参数详解

| 参数 | 含义 |
|---|---|
| `-I {}` | 占位符，每行替换 {}（逐个执行） |
| `-n N` | 每次传 N 个参数 |
| `-P N` | 并行 N 进程 |
| `-0` | 以 \0 分隔（配 find -print0） |
| `-t` | 打印将执行的命令 |
| `-p` | 执行前确认 |
| `-r` | 输入为空不执行 |

::: danger 空格文件名要 -0
文件名含空格/换行时，普通 xargs 会拆错。`find -print0 | xargs -0` 用 \0 分隔才安全。批量删尤其要注意，别误删。
:::

## 运维实战

**批量清理**：`find /tmp -name '*.tmp' -mtime +7 -print0 | xargs -0 rm`。
**并行压缩**：`ls *.log | xargs -P 4 -I {} gzip {}` 提速。
**批量改权限**：`find . -type f -print0 | xargs -0 chmod 644`。
**参数太长**：命令参数超限（Argument list too long）用 xargs 分批。

## 相关命令

[find](./find) · [grep](./grep) · [tee](./tee) · [rm](./rm) · [parallel](/commands/devtools/fzf-parallel-pv)

## 官方文档

- xargs：<https://man7.org/linux/man-pages/man1/xargs.1.html>