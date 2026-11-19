---
title: "cut · 按列截取"
description: "cut 按分隔符取列（-d -f）、按字符位置（-c）、提取 CSV/日志字段。管道列处理，中文详解。"
---

# cut · 按列截取

> 命令手册 · [文件与文本](/commands/basic/) ｜ 频率：每天用
> 从每行里取出某几列——按分隔符（CSV/冒号）或按字符位置。简单列提取比 awk 轻。

## 一句话用途

按列或字符位置截取每行的部分内容。

## 高频场景速查

```bash
cut -d ':' -f 1 /etc/passwd      # 取第1列（用户名）
cut -d ':' -f 1,3 /etc/passwd    # 取第1、3列
cut -d ',' -f 2-4 data.csv       # 取第2到4列
cut -c 1-10 file                 # 取每行第1-10字符
echo 'a:b:c' | cut -d ':' -f 2   # 管道取列
ps aux | cut -c 1-80             # 截断宽输出
```

## 参数详解

| 参数 | 含义 |
|---|---|
| `-d 分隔符` | 字段分隔符（默认 Tab） |
| `-f 列` | 取第几列（1,3 / 2-4） |
| `-c 位置` | 按字符位置（1-10） |
| `-b 位置` | 按字节位置 |
| `--output-delimiter` | 输出分隔符 |
| `-s` | 不含分隔符的行不输出 |

::: tip cut vs awk
cut 只能按固定分隔符/位置取列，简单快。awk 能按任意空白分隔、条件过滤、计算（[awk](./awk)）。多空格分隔用 awk，单字符分隔用 cut。
:::

## 运维实战

**取用户名**：`cut -d: -f1 /etc/passwd`。
**取 IP**：`ss -tn | awk '{print $5}' | cut -d: -f1`（先 awk 取列再 cut 去端口）。
**CSV 取列**：`cut -d, -f1,3 data.csv`。
**截宽输出**：ps/日志太宽，cut -c 1-120 截断便于看。

## 相关命令

[awk](./awk) · [sed](./sed) · [grep](./grep) · [sort](./sort) · [paste/comm](./paste-comm)

## 官方文档

- cut：<https://man7.org/linux/man-pages/man1/cut.1.html>