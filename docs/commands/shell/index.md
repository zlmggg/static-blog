---
title: "命令手册 · Shell 与脚本"
description: "把命令串成自动化：变量、判断、循环、函数与健壮性（主题页）。"
---

# Shell 与脚本

> 命令手册 · [返回总览](/commands/) ｜ 本组 11 个页面，按功能分类

## 功能

单条命令解决一个点，脚本解决一类事。本组是主题页而非单命令：变量与展开、重定向管道、条件循环、函数，以及 set -euo pipefail / trap 这些让脚本"出错即停、可清理"的健壮性写法。运维自动化（备份、巡检、发布）都从这里长出来。

## 类别

### 基础语法

| 命令 | 用途 |
|---|---|
| [变量 / read / printf](./variables) | 变量、read、printf |
| [test / if / case](./test-if-case) | 条件判断 |
| [for / while / until](./loops) | 循环 |
| [函数](./functions) | 组织与复用 |

### 数据流

| 命令 | 用途 |
|---|---|
| [重定向与管道](./redirect-pipe) | 数据流向 |

### 执行与参数

| 命令 | 用途 |
|---|---|
| [exec / source / eval](./exec-source-eval) | 执行方式 |
| [getopts / shift](./getopts-shift) | 参数解析 |

### 健壮性与检查

| 命令 | 用途 |
|---|---|
| [set -euo pipefail / trap](./robust) | 脚本健壮性 |
| [shellcheck / bash -n](./shellcheck) | 静态检查 |

### 交互与历史

| 命令 | 用途 |
|---|---|
| [expect](./expect) | 自动化交互 |
| [history 与引用](./history) | 复用历史 |

::: tip 组织原则
同族命令合并成一页，一条命令只有一个主页；跨组场景用链接指向对应分组。
:::
