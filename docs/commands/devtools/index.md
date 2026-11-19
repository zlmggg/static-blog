---
title: "命令手册 · 开发与效率"
description: "Git 是工具不是服务，命令留这里；工作流详解在 CI/CD 服务页。"
---

# 开发与效率

> 命令手册分组 · 返回 [命令手册总览](/commands/)
> Git 是工具不是服务，命令留这里；工作流详解在 CI/CD 服务页。

## 这类命令解决什么

Git 是版本协作工具（不是常驻服务），命令放本组；GitLab/Jenkins 的工作流详解在 CI/CD 服务页。其余是日常效率小工具：jq 解析 JSON、openssl 看证书、watch 周期执行、fzf 模糊查找。

## 学习顺序（入门 → 高级）

1. git（版本协作底座）
2. jq / yq（JSON/YAML 处理）
3. openssl / ssh-keygen（证书与密钥）
4. watch / timeout / time（执行控制）
5. fzf / parallel（效率）

## 本组命令

### 已就绪

- [base64-xxd-od](./base64-xxd-od)
- [fzf-parallel-pv](./fzf-parallel-pv)
- [git](./git)
- [jq](./jq)
- [openssl](./openssl)
- [ssh-keygen](./ssh-keygen)
- [watch-timeout-time](./watch-timeout-time)
- [yq](./yq)

### 规划中（待编写）

`git`、`jq`、`yq`、`openssl`、`ssh-keygen / ssh-copy-id`、`base64`、`xxd / od`、`watch`、`timeout`、`time`、`fzf`、`parallel`、`pv`

::: tip 覆盖与组织原则
查看检测与操作变更并重；同族命令合并成页（如 fdisk/parted/gdisk → 分区工具）；一条命令只有一个主页，跨组互链。
:::

## 命令页模板

一句话用途 + 频率标记 → 高频场景速查（中文，复制即用）→ 参数详解（`--help` 全量中文化，按"每天用 / 偶尔用 / 很少用"分级，标易错点）→ 运维实战示例 → 相关命令 + 官方文档完整链接。
