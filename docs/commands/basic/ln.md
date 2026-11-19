---
title: "ln · 硬链接与软链接"
description: "ln 硬链接、ln -s 软链接（符号链接）、区别与使用场景、readlink 看指向。版本切换/共享文件，中文详解。"
---

# ln · 硬链接与软链接

> 命令手册 · [文件与文本](/commands/basic/) ｜ 频率：偶尔用
> 软链接像快捷方式（可跨盘、可指目录），硬链接是同文件的另一个名字。版本切换、共享配置常用软链。

## 一句话用途

创建硬链接或符号（软）链接。

## 高频场景速查

```bash
ln -s /opt/app-v2 /opt/app/current    # 软链接（最常用）
ln file.txt hardlink.txt              # 硬链接
ln -sf /opt/app-v3 /opt/app/current   # 强制覆盖已有链接
readlink /opt/app/current             # 看软链指向
readlink -f /opt/app/current          # 看最终真实路径
ls -l                                 # 软链显示 -> 指向
```

## 硬链接 vs 软链接

| | 硬链接 | 软链接 |
|---|---|---|
| 本质 | 同 inode 的别名 | 独立文件存路径 |
| 跨文件系统 | 不能 | 能 |
| 指目录 | 不能 | 能 |
| 删原文件 | 仍可用 | 失效（悬空） |
| 创建 | `ln 源 链` | `ln -s 源 链` |

::: tip 软链目标用绝对路径
`ln -s` 的目标路径是相对**链接所在目录**解析的，容易错。建议用绝对路径，或 cd 到链接目录再建。悬空软链 ls 显示红色。
:::

## 运维实战

**版本切换**：current 软链指向 app-v2，发布新版改指 app-v3，回滚改回——秒级切换（[部署方案](/deploy/)）。
**共享配置**：多服务软链同一份配置。
**Java/Node 版本**：/usr/bin/java 软链到具体 JDK，切换改链接。
**找真实路径**：readlink -f 解析多层软链到最终文件。

## 相关命令

[ls](./ls) · [cp](./cp) · [mv](./mv) · [rm](./rm) · [stat](./stat) · [file](./file)

## 官方文档

- ln：<https://man7.org/linux/man-pages/man1/ln.1.html>
- readlink：<https://man7.org/linux/man-pages/man1/readlink.1.html>