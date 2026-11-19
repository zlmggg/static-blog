---
title: "tr · 字符转换与删除"
description: "tr 大小写转换、-d 删字符/-s 压缩重复、换行转空格、删 Windows 回车。字符级处理，中文详解。"
---

# tr · 字符转换与删除

> 命令手册 · [文件与文本](/commands/basic/) ｜ 频率：偶尔用
> 按字符（不是字符串）替换/删除/压缩。大小写转换、删回车、压空格——tr 一把好手。

## 一句话用途

转换、删除、压缩输入中的字符。

## 高频场景速查

```bash
echo 'Hello' | tr 'a-z' 'A-Z'        # 转大写
echo 'Hello' | tr 'A-Z' 'a-z'        # 转小写
echo 'a  b   c' | tr -s ' '          # 压缩连续空格为一个
cat file | tr -d '\r'                # 删 Windows 回车
echo 'a:b:c' | tr ':' '\n'           # 冒号转换行
cat file | tr -d '\n'                # 删所有换行（连成一行）
tr -cd '0-9' < file                  # 只保留数字
```

## 参数详解

| 参数 | 含义 |
|---|---|
| `tr SET1 SET2` | SET1 字符映射到 SET2 |
| `-d` | 删除 SET1 字符 |
| `-s` | 压缩连续重复字符 |
| `-c` | 取补集（不在 SET1 的） |
| `-cd` | 删除不在 SET1 的（只保留） |

## 字符类

`[:upper:]` `[:lower:]` `[:digit:]` `[:space:]` `[:alpha:]`，如 `tr '[:lower:]' '[:upper:]'`。

::: tip tr 只处理字符
tr 按单字符映射，不能替换字符串（多字符替换用 [sed](./sed)）。tr 从 stdin 读，不接文件参数（用 < 或管道）。
:::

## 运维实战

**删 Windows 回车**：`tr -d '\r' < win.txt > unix.txt`（或 [dos2unix](./dos2unix-iconv)）。
**生成随机串**：`tr -dc 'A-Za-z0-9' < /dev/urandom | head -c 16`。
**规范化分隔**：`tr -s ' ' < file` 压多余空格便于 cut/awk。
**提取数字**：`tr -cd '0-9\n' < mixed.txt`。

## 相关命令

[sed](./sed) · [awk](./awk) · [cut](./cut) · [dos2unix/iconv](./dos2unix-iconv) · [sort](./sort)

## 官方文档

- tr：<https://man7.org/linux/man-pages/man1/tr.1.html>