---
title: "rename · 批量重命名"
description: "rename 用正则批量改名（Perl 版）、util-linux 版简单替换、改扩展名/加前缀。批量改名利器，中文详解。"
---

# rename · 批量重命名

> 命令手册 · [文件与文本](/commands/basic/) ｜ 频率：很少用
> 把一堆 .txt 改 .md、给文件名加前缀——rename 用正则批量改。注意有两个版本语法不同。

## 一句话用途

按规则批量重命名文件。

## 两个版本（重要）

| 版本 | 来源 | 语法 |
|---|---|---|
| Perl rename | Debian/Ubuntu 默认 | `rename 's/旧/新/' 文件` |
| util-linux rename | RHEL 默认 | `rename 旧 新 文件` |

## Perl 版（正则）

```bash
rename 's/\.txt$/.md/' *.txt     # 扩展名 txt→md
rename 's/^/prefix_/' *.log      # 加前缀
rename 'y/A-Z/a-z/' *            # 文件名转小写
rename -n 's/\.txt$/.md/' *.txt  # 预演（不真改）
```

## util-linux 版（简单替换）

```bash
rename .txt .md *.txt            # 把 .txt 替换为 .md
rename img photo img*.png        # img→photo
```

::: danger 先 -n 预演
Perl 版 rename -n 先看会改成什么，确认无误再去掉 -n 真改。批量改名不可逆，正则写错可能改乱。两个版本语法不通用，先确认装的哪个（rename --version）。
:::

## 运维实战

**统一扩展名**：日志 .log.1/.log.2 规范化。
**加日期前缀**：备份文件加日期便于排序。
**转小写**：Windows 来的大写文件名转小写统一。
**替代方案**：复杂改名用 for + mv（[mv](./mv)）更可控。

## 相关命令

[mv](./mv) · [find](./find) · [xargs](./xargs) · [ls](./ls) · [sed](./sed)

## 官方文档

- rename（Perl）：<https://man7.org/linux/man-pages/man1/file-rename.1p.html>
- rename（util-linux）：<https://man7.org/linux/man-pages/man1/rename.1.html>