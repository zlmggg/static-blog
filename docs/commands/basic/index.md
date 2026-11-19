---
title: "命令手册 · 文件与文本"
description: "定位、查看、过滤、编辑、压缩、校验——运维每天敲得最多的一类。"
---

# 文件与文本

> 命令手册分组 · 返回 [命令手册总览](/commands/)
> 定位、查看、过滤、编辑、压缩、校验——运维每天敲得最多的一类。

## 这类命令解决什么

文件与文本命令是运维的"手"：找文件、看内容、过滤日志、改配置、打包传输都靠它。文本三剑客 grep/sed/awk 是日志分析与配置批量修改的核心，值得反复练。

## 学习顺序（入门 → 高级）

1. ls / cd / pwd / cp / mv / rm（先会操作文件）
2. cat / less / head / tail（看内容）
3. find / grep（定位与过滤）
4. sed / awk（编辑与统计）
5. tar / gzip（打包压缩）
6. xargs / tee / sort / uniq（组合管道）

## 本组命令

### 已就绪

- [awk](./awk)
- [cat](./cat)
- [cd-pwd](./cd-pwd)
- [cp](./cp)
- [cut](./cut)
- [diff-patch](./diff-patch)
- [dos2unix-iconv](./dos2unix-iconv)
- [file](./file)
- [find](./find)
- [grep](./grep)
- [gzip-bzip2-xz](./gzip-bzip2-xz)
- [head](./head)
- [less](./less)
- [ln](./ln)
- [ls](./ls)
- [md5sum-sha256sum](./md5sum-sha256sum)
- [mkdir-rmdir](./mkdir-rmdir)
- [mv](./mv)
- [paste-comm](./paste-comm)
- [rename](./rename)
- [rg](./rg)
- [rm](./rm)
- [sed](./sed)
- [shred](./shred)
- [sort](./sort)
- [split](./split)
- [stat](./stat)
- [tail](./tail)
- [tar](./tar)
- [tee](./tee)
- [touch](./touch)
- [tr](./tr)
- [tree](./tree)
- [uniq](./uniq)
- [vim](./vim)
- [wc](./wc)
- [xargs](./xargs)
- [zip-unzip](./zip-unzip)

### 规划中（待编写）

`ls`、`cd / pwd`、`cp`、`mv`、`rm`、`mkdir / rmdir`、`touch`、`cat`、`less`、`head`、`tail`、`find`、`grep`、`rg (ripgrep)`、`sed`、`awk`、`cut`、`sort`、`uniq`、`wc`、`tr`、`diff / patch`、`tar`、`gzip / bzip2 / xz`、`zip / unzip`、`ln`、`file`、`stat`、`tree`、`tee`、`xargs`、`split`、`paste / comm`、`md5sum / sha256sum`、`dos2unix / iconv`、`rename`、`vim`、`shred`

::: tip 覆盖与组织原则
查看检测与操作变更并重；同族命令合并成页（如 fdisk/parted/gdisk → 分区工具）；一条命令只有一个主页，跨组互链。
:::

## 命令页模板

一句话用途 + 频率标记 → 高频场景速查（中文，复制即用）→ 参数详解（`--help` 全量中文化，按"每天用 / 偶尔用 / 很少用"分级，标易错点）→ 运维实战示例 → 相关命令 + 官方文档完整链接。
