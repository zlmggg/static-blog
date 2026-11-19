---
title: "paste / comm · 合并与比较列"
description: "paste 横向合并多文件列、comm 比较两个已排序文件的共有/独有行。列拼接与集合比较，中文详解。"
---

# paste / comm · 合并与比较列

> 命令手册 · [文件与文本](/commands/basic/) ｜ 频率：很少用
> paste 把几个文件按列并排拼一起；comm 比较两个**已排序**文件，找出共有/各自独有的行。

## 一句话用途

paste 横向合并文件列；comm 比较两个有序文件的行集合。

## paste 速查

```bash
paste a.txt b.txt                # 两文件按行并排（Tab 分隔）
paste -d ',' a.txt b.txt         # 用逗号分隔
paste -s a.txt                   # 把一文件所有行拼成一行
paste a.txt b.txt | column -t    # 对齐显示
```

## comm 速查

```bash
# 必须先排序！
sort a.txt > a.sorted
sort b.txt > b.sorted
comm a.sorted b.sorted           # 三列：仅A / 仅B / 共有
comm -12 a.sorted b.sorted       # 只看共有（交集）
comm -23 a.sorted b.sorted       # 只看 A 独有（差集）
comm -13 a.sorted b.sorted       # 只看 B 独有
```

## comm 三列与抑制

| 列 | 含义 | 抑制参数 |
|---|---|---|
| 1 | 仅 A 有 | `-1` |
| 2 | 仅 B 有 | `-2` |
| 3 | 共有 | `-3` |

`-12` = 抑制1、2列 = 只留共有（交集）。

::: danger comm 要求已排序
comm 基于有序比较，输入**必须先 sort**。不排序结果错乱。求交集用 `comm -12 <(sort a) <(sort b)`（进程替换）。
:::

## 运维实战

**找配置差异行**：comm -23 旧配置 新配置 看删了哪些行。
**白名单交集**：comm -12 允许列表 实际列表 找合规项。
**拼 CSV 列**：paste -d, 把分散的列文件合成 CSV。

## 相关命令

[sort](./sort) · [uniq](./uniq) · [diff/patch](./diff-patch) · [cut](./cut) · [awk](./awk)

## 官方文档

- paste：<https://man7.org/linux/man-pages/man1/paste.1.html>
- comm：<https://man7.org/linux/man-pages/man1/comm.1.html>