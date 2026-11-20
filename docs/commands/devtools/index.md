---
title: "命令手册 · 开发与效率"
description: "Git 是工具不是服务，命令留这里；工作流详解在 CI/CD 服务页。"
---

# 开发与效率

> 命令手册 · [返回总览](/commands/) ｜ 本组 8 个页面，按功能分类

## 功能

Git 是版本协作工具（不是常驻服务），命令放本组；GitLab/Jenkins 的工作流详解在 CI/CD 服务页。其余是日常效率小工具：jq 解析 JSON、openssl 看证书、watch 周期执行、fzf 模糊查找。

## 类别

### 版本控制

| 命令 | 用途 |
|---|---|
| [git](./git) | 版本协作底座 |

### 结构化数据处理

| 命令 | 用途 |
|---|---|
| [jq](./jq) | JSON 解析利器 |
| [yq](./yq) | YAML 处理 |

### 编码与二进制

| 命令 | 用途 |
|---|---|
| [base64 / xxd / od](./base64-xxd-od) | 编码与二进制查看 |

### 证书与密钥

| 命令 | 用途 |
|---|---|
| [openssl](./openssl) | 证书与加密排查 |
| [ssh-keygen / ssh-copy-id](./ssh-keygen) | 密钥与免密 |

### 执行控制与效率

| 命令 | 用途 |
|---|---|
| [watch / timeout / time](./watch-timeout-time) | 定时刷新、超时与计时 |
| [fzf / parallel / pv](./fzf-parallel-pv) | 模糊查找、并行与进度条 |

::: tip 组织原则
同族命令合并成一页，一条命令只有一个主页；跨组场景用链接指向对应分组。
:::
