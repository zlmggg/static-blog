---
title: "命令手册 · 软件包管理"
description: "装软件、查依赖、配仓库、源码编译、动态库。"
---

# 软件包管理

> 命令手册分组 · 返回 [命令手册总览](/commands/)
> 装软件、查依赖、配仓库、源码编译、动态库。

## 这类命令解决什么

装软件是运维的起点。RHEL 系用 dnf/yum/rpm，Debian 系用 apt/dpkg；配仓库、查依赖、锁版本是日常；源码编译（make/gcc）和动态库（ldconfig）在缺包或排"找不到 .so"时用到。

## 学习顺序（入门 → 高级）

1. dnf / apt（装与卸）
2. rpm / dpkg（查包内容）
3. 仓库配置（换源/内网源）
4. dnf repoquery / apt-file（查依赖与文件归属）
5. make / gcc / ldconfig（编译与动态库）

## 本组命令

### 已就绪

- [apt](./apt)
- [dnf-yum](./dnf-yum)
- [ldconfig](./ldconfig)
- [make-gcc](./make-gcc)
- [pip-npm](./pip-npm)
- [repo-config](./repo-config)
- [repoquery-apt-file](./repoquery-apt-file)
- [rpm-dpkg](./rpm-dpkg)
- [update-alternatives](./update-alternatives)

### 规划中（待编写）

`yum / dnf`、`apt`、`rpm`、`dpkg`、`仓库配置`、`dnf repoquery / apt-file`、`make / gcc`、`update-alternatives`、`ldconfig`、`pip / npm`

::: tip 覆盖与组织原则
查看检测与操作变更并重；同族命令合并成页（如 fdisk/parted/gdisk → 分区工具）；一条命令只有一个主页，跨组互链。
:::

## 命令页模板

一句话用途 + 频率标记 → 高频场景速查（中文，复制即用）→ 参数详解（`--help` 全量中文化，按"每天用 / 偶尔用 / 很少用"分级，标易错点）→ 运维实战示例 → 相关命令 + 官方文档完整链接。
