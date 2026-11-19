---
title: "touch · 建空文件与改时间戳"
description: "touch 建空文件、改 atime/mtime、-t 指定时间、-d 日期字符串。占位/触发构建/改时间，中文详解。"
---

# touch · 建空文件与改时间戳

> 命令手册 · [文件与文本](/commands/basic/) ｜ 频率：每天用
> 文件不存在就建空文件，存在就更新时间戳。常用来占位、触发 make、标记时间。

## 一句话用途

创建空文件或修改文件的时间戳。

## 高频场景速查

```bash
touch file.txt                   # 建空文件（已存在则更新 mtime）
touch a.txt b.txt c.txt          # 一次建多个
touch -t 202601010000 file       # 设时间戳（YYYYMMDDhhmm）
touch -d '2026-01-01 12:00' file # 用日期字符串
touch -r ref.txt target.txt      # 用 ref 的时间戳
touch -a file                    # 只改访问时间
touch -m file                    # 只改修改时间
```

## 参数详解

| 参数 | 含义 |
|---|---|
| `-t 时间` | 指定时间戳 [[CC]YY]MMDDhhmm[.ss] |
| `-d 字符串` | 日期字符串（更灵活） |
| `-r 参考文件` | 复制参考文件时间 |
| `-a` | 只改 atime |
| `-m` | 只改 mtime |
| `-c` | 不存在不创建 |

## 运维实战

**占位文件**：部署前 touch 标记文件/锁文件。
**触发增量构建**：touch 源文件让 make 认为它更新了。
**清理按时间**：配合 find -mtime（[find](./find)）按修改时间筛文件，touch 可造测试时间。
**保留时间戳复制**：cp -p 保留时间（[cp](./cp)），touch -r 对齐时间。

::: tip 时间戳三种
atime 访问、mtime 内容修改、ctime 元数据变更。ls -l 看 mtime，stat 看全（[stat](./stat)）。touch 默认改 atime+mtime。
:::

## 相关命令

[stat](./stat) · [find](./find) · [cp](./cp) · [ls](./ls) · [mkdir](./mkdir-rmdir)

## 官方文档

- touch：<https://man7.org/linux/man-pages/man1/touch.1.html>