---
title: "mkdir / rmdir · 建删目录"
description: "mkdir -p 递归建多级目录、-m 设权限、rmdir 删空目录。建目录基础操作，中文详解。"
---

# mkdir / rmdir · 建删目录

> 命令手册 · [文件与文本](/commands/basic/) ｜ 频率：每天用
> 建目录用 mkdir，删空目录用 rmdir。删非空目录用 rm -r（[rm](./rm)）。

## 一句话用途

创建目录、删除空目录。

## 高频场景速查

```bash
mkdir /data/logs                 # 建单级（父目录须存在）
mkdir -p /data/app/logs/2026     # 递归建多级（父不存在自动建）
mkdir -m 750 /data/private       # 建并设权限
mkdir -p /data/{app,logs,backup} # 一次建多个
rmdir /data/empty                # 删空目录
rmdir -p a/b/c                   # 递归删空目录链
```

## 参数详解

### mkdir

| 参数 | 含义 |
|---|---|
| `-p` | 递归创建，已存在不报错（**最常用**） |
| `-m 模式` | 设权限（不受 umask 影响） |
| `-v` | 显示创建过程 |

### rmdir

| 参数 | 含义 |
|---|---|
| `rmdir 目录` | 只能删**空**目录 |
| `-p` | 删目录及其空的父目录 |

::: tip rmdir vs rm -r
rmdir 只删空目录，安全（非空报错）。rm -r 删非空（危险）。脚本里删目录确认空用 rmdir，要清内容用 rm -r 但三确认路径。
:::

## 运维实战

**部署建目录**：`mkdir -p /opt/app/{bin,conf,logs}` 一次建好结构。
**幂等脚本**：mkdir -p 已存在不报错，适合反复执行的部署脚本。
**权限目录**：`mkdir -m 700 /root/.secret` 建私密目录。

## 相关命令

[rm](./rm) · [cp](./cp) · [ls](./ls) · [chmod](/commands/identity/chmod) · [touch](./touch)

## 官方文档

- mkdir：<https://man7.org/linux/man-pages/man1/mkdir.1.html>
- rmdir：<https://man7.org/linux/man-pages/man1/rmdir.1.html>