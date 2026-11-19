---
title: "zip / unzip · 跨平台打包压缩"
description: "zip 打包压缩多文件（跨平台）、unzip 解压/-l 看内容/-d 指定目录、-r 递归。与 Windows 交换文件首选，中文详解。"
---

# zip / unzip · 跨平台打包压缩

> 命令手册 · [文件与文本](/commands/basic/) ｜ 频率：偶尔用
> 要和 Windows/macOS 交换压缩包，zip 最通用（双击即开）。Linux 内部归档常用 tar.gz。

## 一句话用途

打包并压缩多个文件成 .zip，跨平台兼容。

## 高频场景速查

```bash
zip archive.zip file1 file2      # 打包多文件
zip -r archive.zip /data         # 递归打包目录
zip -e archive.zip file          # 加密（设密码）
unzip archive.zip                # 解压到当前目录
unzip archive.zip -d /target     # 解压到指定目录
unzip -l archive.zip             # 只看内容不解压
unzip -o archive.zip             # 覆盖已存在不询问
unzip -O CP936 archive.zip       # 中文文件名（Windows GBK）
```

## 参数详解

### zip

| 参数 | 含义 |
|---|---|
| `-r` | 递归目录 |
| `-e` | 加密 |
| `-9` | 最高压缩 |
| `-x` | 排除（`-x '*.log'`） |
| `-u` | 更新（只加新/改的） |

### unzip

| 参数 | 含义 |
|---|---|
| `-d 目录` | 解压目标 |
| `-l` | 列内容 |
| `-o` | 覆盖不询问 |
| `-n` | 不覆盖已存在 |
| `-O 编码` | 文件名编码（中文） |

::: tip 中文乱码
Windows 建的 zip 文件名常是 GBK，Linux 解压乱码。`unzip -O CP936`（或 GBK）指定编码。或改用 tar 避免编码问题。
:::

## 运维实战

**给 Windows 同事发文件**：zip -r 打包，对方双击即开。
**看压缩包内容**：unzip -l 先看不解压。
**释放到指定目录**：unzip -d /opt/app package.zip。

## 相关命令

[tar](./tar) · [gzip/bzip2/xz](./gzip-bzip2-xz) · [cp](./cp) · [scp/sftp](/commands/network/scp-sftp)

## 官方文档

- zip：<https://man7.org/linux/man-pages/man1/zip.1.html>
- unzip：<https://man7.org/linux/man-pages/man1/unzip.1.html>