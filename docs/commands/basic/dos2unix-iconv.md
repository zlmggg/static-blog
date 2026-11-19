---
title: "dos2unix / iconv · 换行与编码转换"
description: "dos2unix 去 Windows 回车（CRLF→LF）、unix2dos 反向、iconv 转字符编码（GBK→UTF-8）。跨平台文本乱码修复，中文详解。"
---

# dos2unix / iconv · 换行与编码转换

> 命令手册 · [文件与文本](/commands/basic/) ｜ 频率：偶尔用
> Windows 编辑的脚本到 Linux 报 `\r` 错、中文文件乱码——换行符和编码问题。dos2unix 修换行，iconv 修编码。

## 一句话用途

转换文本换行符（CRLF↔LF）与字符编码。

## dos2unix（换行符）

```bash
dos2unix script.sh               # CRLF→LF（去 \r）
dos2unix -k script.sh            # 保留原时间戳
unix2dos file.txt                # LF→CRLF（给 Windows）
dos2unix *.sh                    # 批量
cat -A script.sh                 # 先看：行尾 ^M$ 说明有 \r
```

## iconv（编码）

```bash
iconv -f GBK -t UTF-8 old.txt > new.txt    # GBK→UTF-8
iconv -f UTF-8 -t GBK new.txt > old.txt    # 反向
iconv -l                         # 列支持的编码
iconv -f GBK -t UTF-8//IGNORE old.txt      # 忽略无法转换字符
file -i old.txt                  # 先看原编码
```

## 常见问题

| 症状 | 原因 | 解法 |
|---|---|---|
| `bash: \r: command not found` | Windows 换行 | dos2unix |
| 中文乱码 | GBK/UTF-8 不符 | iconv 转码 |
| `bad interpreter: ...^M` | 脚本 shebang 带 \r | dos2unix |

::: tip 脚本上传后先 dos2unix
Windows 写的 shell 脚本传 Linux 常因 CRLF 报错。养成习惯：上传后 dos2unix，或编辑器设 LF 换行。cat -A 看 ^M 确认。
:::

## 运维实战

**修脚本 \r 错**：dos2unix script.sh 后正常执行。
**转日志编码**：老系统 GBK 日志 iconv 转 UTF-8 便于 grep 中文。
**批量转码**：`for f in *.txt; do iconv -f GBK -t UTF-8 "$f" -o "$f"; done`。

## 相关命令

[cat](./cat) · [file](./file) · [tr](./tr) · [sed](./sed) · [vim](./vim)

## 官方文档

- dos2unix：<https://man7.org/linux/man-pages/man1/dos2unix.1.html>
- iconv：<https://man7.org/linux/man-pages/man1/iconv.1.html>