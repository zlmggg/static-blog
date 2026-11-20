---
title: "命令手册 · 软件包管理"
description: "装软件、查依赖、配仓库、源码编译、动态库。"
---

# 软件包管理

### 发行版包管理

::: cmd

| 命令 | 用途 |
|---|---|
| [apt](./apt) | Debian/Ubuntu 包管理 |
| [dnf / yum](./dnf-yum) | RHEL 系包管理 |
| [rpm / dpkg](./rpm-dpkg) | 底层包查询 |

:::

### 仓库与依赖查询

::: cmd

| 命令 | 用途 |
|---|---|
| [仓库配置](./repo-config) | 换源与内网源 |
| [repoquery / apt-file](./repoquery-apt-file) | 查依赖与文件归属 |

:::

### 编译、库与多版本

::: cmd

| 命令 | 用途 |
|---|---|
| [make / gcc](./make-gcc) | 源码编译 |
| [ldconfig](./ldconfig) | 动态库缓存 |
| [update-alternatives](./update-alternatives) | 多版本切换 |

:::

### 语言级包管理

::: cmd

| 命令 | 用途 |
|---|---|
| [pip / npm](./pip-npm) | 语言级包管理 |

:::
