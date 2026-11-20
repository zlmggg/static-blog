---
title: "命令手册 · 软件包管理"
description: "装软件、查依赖、配仓库、源码编译、动态库。"
---

# 软件包管理

> 命令手册 · [返回总览](/commands/) ｜ 本组 9 个页面，按功能分类

## 功能

装软件是运维的起点。RHEL 系用 dnf/yum/rpm，Debian 系用 apt/dpkg；配仓库、查依赖、锁版本是日常；源码编译（make/gcc）和动态库（ldconfig）在缺包或排"找不到 .so"时用到。

## 类别

### 发行版包管理

| 命令 | 用途 |
|---|---|
| [apt](./apt) | Debian/Ubuntu 包管理 |
| [dnf / yum](./dnf-yum) | RHEL 系包管理 |
| [rpm / dpkg](./rpm-dpkg) | 底层包查询 |

### 仓库与依赖查询

| 命令 | 用途 |
|---|---|
| [仓库配置](./repo-config) | 换源与内网源 |
| [repoquery / apt-file](./repoquery-apt-file) | 查依赖与文件归属 |

### 编译、库与多版本

| 命令 | 用途 |
|---|---|
| [make / gcc](./make-gcc) | 源码编译 |
| [ldconfig](./ldconfig) | 动态库缓存 |
| [update-alternatives](./update-alternatives) | 多版本切换 |

### 语言级包管理

| 命令 | 用途 |
|---|---|
| [pip / npm](./pip-npm) | 语言级包管理 |

::: tip 组织原则
同族命令合并成一页，一条命令只有一个主页；跨组场景用链接指向对应分组。
:::
