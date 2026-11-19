---
title: "base64 / xxd / od · 编码与二进制查看"
description: "base64 编解码（K8s Secret/传输）、xxd/od 看二进制与十六进制、排查乱码与不可见字符。参数中文分级。"
---

# base64 / xxd / od · 编码与二进制查看

> 命令手册 · [开发与效率](/commands/devtools/) ｜ 频率：偶尔用
> base64 把二进制变文本（K8s Secret、邮件、URL 传输）；xxd/od 看文件的真实字节，排乱码与隐藏字符。

## 一句话用途

编解码 base64、查看文件底层字节（十六进制/八进制），定位不可见字符问题。

## 高频场景速查

```bash
echo -n 'hello' | base64                 # 编码（-n 去掉换行）
echo 'aGVsbG8=' | base64 -d              # 解码
kubectl get secret db -o jsonpath='{.data.password}' | base64 -d   # 解 K8s Secret
xxd file.bin | head                      # 十六进制查看
xxd -r hex.txt out.bin                   # 十六进制还原二进制
od -c file | head                        # 看不可见字符（\r \n \t）
cat -A script.sh                         # 显示行尾（$=LF, ^M$=CRLF）
```

## 参数详解

### base64

| 参数 | 含义 |
|---|---|
| `-d` | 解码 |
| `-w 0` | 编码不换行（默认76列折行） |
| `-i` | 解码忽略非法字符 |

### xxd / od

| 命令 | 含义 |
|---|---|
| `xxd` | 十六进制+ASCII 对照 |
| `xxd -r` | 反向还原 |
| `od -c` | 按字符显示（含转义） |
| `od -x` | 十六进制 |

::: tip 易错点
base64 编码前 `echo` 要加 `-n`，否则末尾多个换行导致编码结果不同。Windows 编辑的脚本带 CRLF（^M），Linux 跑报 `bad interpreter`，用 `cat -A` 看、`dos2unix` 转。
:::

## 运维实战

**K8s Secret 解码**：Secret 的 data 是 base64，`kubectl get secret x -o jsonpath='{.data.key}' | base64 -d` 看明文。
**脚本 shebang 报错**：`#!/bin/bash^M` 是 CRLF 作怪，`od -c` 看到 `\r`，`dos2unix` 修复。

## 相关命令

[dos2unix/iconv](/commands/basic/) · [jq](./jq) · [kubectl](/services/container/kubernetes/03-功能)

## 官方文档

- base64：<https://man7.org/linux/man-pages/man1/base64.1.html>
- xxd：<https://man7.org/linux/man-pages/man1/xxd.1.html>