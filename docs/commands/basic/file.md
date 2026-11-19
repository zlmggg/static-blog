---
title: "file · 识别文件类型"
description: "file 按内容识别真实类型（不看扩展名）、-i  MIME、判断二进制/文本/编码。下载文件验真，中文详解。"
---

# file · 识别文件类型

> 命令手册 · [文件与文本](/commands/basic/) ｜ 频率：偶尔用
> 扩展名能骗人，file 看文件头（magic number）识别真实类型。下载的文件是不是真图片/真压缩包，file 一验便知。

## 一句话用途

按文件内容识别真实类型（不依赖扩展名）。

## 高频场景速查

```bash
file image.png                   # 看真实类型
file *                           # 当前目录所有文件
file -i file                     # 输出 MIME 类型
file -b file                     # 简洁（不显示文件名）
file archive.tar.gz              # 识别压缩格式
file /bin/ls                     # ELF 可执行
```

## 输出示例

```text
image.png: PNG image data, 1920 x 1080, 8-bit/color RGB
script.sh: Bourne-Again shell script, ASCII text executable
data.bin:  data
doc.pdf:   PDF document, version 1.7
```

## 运维实战

**验下载文件**：下载说是 .tar.gz，file 确认是不是真 gzip（防下成 HTML 错误页）。
**判断文本/二进制**：file 显示 text 才能 grep/sed，data/ELF 是二进制别乱 cat。
**查编码**：`file -i text.txt` 看 charset（utf-8/iso-8859-1），配合 [iconv](./dos2unix-iconv) 转码。
**排脚本不能执行**：file 看是不是真脚本、有没有 BOM/Windows 换行。

::: tip 扩展名不可信
Linux 不靠扩展名判断类型。file 读 magic number 才准。一个 .jpg 可能是伪装的脚本，安全核查用 file。
:::

## 相关命令

[stat](./stat) · [ls](./ls) · [cat](./cat) · [dos2unix/iconv](./dos2unix-iconv) · [md5sum/sha256sum](./md5sum-sha256sum)

## 官方文档

- file：<https://man7.org/linux/man-pages/man1/file.1.html>