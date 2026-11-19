---
title: "tree · 树状目录结构"
description: "tree 树状显示目录、-L 限深度/-d 只目录/-a 含隐藏、-I 排除。看项目结构/写文档，中文详解。"
---

# tree · 树状目录结构

> 命令手册 · [文件与文本](/commands/basic/) ｜ 频率：偶尔用
> 直观看目录层级结构，写文档/理项目布局必备。ls 是平铺，tree 是树。

## 一句话用途

以树状图显示目录层级结构。

## 高频场景速查

```bash
tree                             # 当前目录树
tree -L 2                        # 只看 2 层
tree -d                          # 只显示目录
tree -a                          # 含隐藏文件
tree -I 'node_modules|.git'      # 排除指定目录
tree -L 2 -I 'node_modules' /opt/app   # 项目结构（排除依赖）
tree -h                          # 带文件大小
tree --du -h                     # 含目录累计大小
```

## 参数详解

| 参数 | 含义 |
|---|---|
| `-L N` | 限制深度 |
| `-d` | 只目录 |
| `-a` | 含隐藏 |
| `-I 模式` | 排除（竖线分隔） |
| `-h` | 人类可读大小 |
| `-f` | 显示完整路径 |
| `-P 模式` | 只显示匹配 |
| `--dirsfirst` | 目录排前 |

::: tip 需安装
tree 多数发行版默认不装：`dnf install tree` / `apt install tree`。没装时用 `find . -maxdepth 2` 或 ls -R 替代。
:::

## 运维实战

**理项目结构**：`tree -L 2 -I 'node_modules|.git'` 看骨架。
**写部署文档**：tree 输出贴进 README 说明目录布局。
**找目录**：`tree -d -L 3 /etc` 看配置目录层级。

## 相关命令

[ls](./ls) · [find](./find) · [mkdir](./mkdir-rmdir) · [du](/commands/storage/du)

## 官方文档

- tree：<https://man7.org/linux/man-pages/man1/tree.1.html>