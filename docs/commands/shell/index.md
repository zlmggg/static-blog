---
title: "命令手册 · Shell 与脚本"
description: "把命令串成自动化：变量、判断、循环、函数与健壮性（主题页）。"
---

# Shell 与脚本

> 命令手册分组 · 返回 [命令手册总览](/commands/)
> 把命令串成自动化：变量、判断、循环、函数与健壮性（主题页）。

## 这类命令解决什么

单条命令解决一个点，脚本解决一类事。本组是主题页而非单命令：变量与展开、重定向管道、条件循环、函数，以及 set -euo pipefail / trap 这些让脚本"出错即停、可清理"的健壮性写法。运维自动化（备份、巡检、发布）都从这里长出来。

## 学习顺序（入门 → 高级）

1. 变量 / 重定向 / 管道（基础语法）
2. test / if / for / while（判断与循环）
3. 函数 / getopts（组织与传参）
4. set -euo pipefail / trap（健壮性）
5. shellcheck / bash -n（静态检查）

## 本组命令

### 已就绪

- [exec-source-eval](./exec-source-eval)
- [expect](./expect)
- [functions](./functions)
- [getopts-shift](./getopts-shift)
- [history](./history)
- [loops](./loops)
- [redirect-pipe](./redirect-pipe)
- [robust](./robust)
- [shellcheck](./shellcheck)
- [test-if-case](./test-if-case)
- [variables](./variables)

### 规划中（待编写）

`变量 / read / printf`、`重定向与管道`、`exec / source / eval`、`test / [ ]`、`if / case`、`for / while / until`、`函数`、`set -euo pipefail`、`trap`、`getopts / shift`、`history 与引用`、`shellcheck / bash -n`、`expect`

::: tip 覆盖与组织原则
查看检测与操作变更并重；同族命令合并成页（如 fdisk/parted/gdisk → 分区工具）；一条命令只有一个主页，跨组互链。
:::

## 命令页模板

一句话用途 + 频率标记 → 高频场景速查（中文，复制即用）→ 参数详解（`--help` 全量中文化，按"每天用 / 偶尔用 / 很少用"分级，标易错点）→ 运维实战示例 → 相关命令 + 官方文档完整链接。
