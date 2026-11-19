---
title: "cat · 查看与拼接文件"
description: "cat 输出全文、-n 行号/-A 显示隐藏字符、拼接文件、here-doc。小文件查看与组合，中文详解。"
---

# cat · 查看与拼接文件

> 命令手册 · [文件与文本](/commands/basic/) ｜ 频率：每天用
> 小文件直接 cat 看全文，大文件用 less（[less](./less)）。cat 还能拼接文件、显示隐藏字符。

## 一句话用途

输出文件内容、拼接多个文件、显示不可见字符。

## 高频场景速查

```bash
cat file.txt                     # 输出全文
cat -n file.txt                  # 带行号
cat -A file.txt                  # 显示隐藏字符（Tab=^I 行尾=$）
cat a.txt b.txt > merged.txt     # 拼接
cat > new.txt <<'EOF'            # here-doc 写文件
line1
line2
EOF
cat file | grep error            # 配合管道（小文件）
```

## 参数详解

| 参数 | 含义 |
|---|---|
| `-n` | 所有行编号 |
| `-b` | 非空行编号 |
| `-A` | 显示所有隐藏字符（排错神器） |
| `-s` | 压缩连续空行 |
| `-E` | 行尾显示 $ |
| `-T` | Tab 显示 ^I |

::: tip 大文件别 cat
cat 大日志会刷屏卡终端。大文件用 less 翻页、tail 看尾部、head 看头部。cat 适合小配置文件。
:::

## 运维实战

**排隐藏字符**：脚本/配置报错可能是 Windows 换行（^M）或多余空格，`cat -A` 一眼看出（配合 [dos2unix](./dos2unix-iconv)）。
**快速写配置**：here-doc `cat > conf <<'EOF'`（单引号 EOF 不展开变量）。
**拼接日志**：`cat app.log.1 app.log > all.log` 合并分段日志。

## 相关命令

[less](./less) · [head](./head) · [tail](./tail) · [grep](./grep) · [dos2unix/iconv](./dos2unix-iconv)

## 官方文档

- cat：<https://man7.org/linux/man-pages/man1/cat.1.html>