---
title: "set -euo pipefail / trap · 脚本健壮性"
description: "set -e/-u/-o pipefail 让脚本出错即停、未定义变量报错、管道失败可见；trap 捕获信号做清理与回滚。运维脚本保命写法中文详解。"
---

# set -euo pipefail / trap · 脚本健壮性

> 命令手册 · [Shell 与脚本](/commands/shell/) ｜ 主题页
> 运维脚本最怕"错了还继续跑"——删错目录、部署半成品。这一页是让脚本"出错即停、可清理"的保命写法。

## 一句话用途

让脚本遇到错误立刻停下、用到未定义变量就报错、管道里任何一环失败都算失败，并在退出时做好清理。

## set 三件套

```bash
#!/usr/bin/env bash
set -euo pipefail
```

| 选项 | 作用 | 防什么 |
|---|---|---|
| `-e` (errexit) | 命令失败（非0）立即退出 | 错了还往下跑 |
| `-u` (nounset) | 用未定义变量即报错 | 拼错变量名变成空串 |
| `-o pipefail` | 管道任一环节失败整条算失败 | `cmd1 \| cmd2` 掩盖 cmd1 失败 |

::: danger 为什么必须加
没有 `-e`：`cd /not/exist; rm -rf *` 会在**当前目录**删光（cd 失败没停）。
没有 `-u`：`rm -rf "$dir/"` 当 dir 未定义变成 `rm -rf /`。
没有 pipefail：`cat missing | grep x` 返回 grep 的码，cat 失败被忽略。
:::

## -e 的例外与应对

`-e` 在这些情况不触发：条件判断里的命令（if/while/&&/||）、`!` 取反。需要"允许失败"的命令显式处理：

```bash
grep pattern file || true          # 允许 grep 无匹配
if ! cmd; then echo "失败但继续"; fi
count=$(grep -c x file || true)    # 命令替换里也要兜底
```

## trap 清理与回滚

```bash
tmp=$(mktemp -d)
cleanup() { rm -rf "$tmp"; }
trap cleanup EXIT                  # 无论正常/异常退出都清理

trap 'echo "被中断"; exit 130' INT TERM   # 捕获 Ctrl+C / kill

# 部署失败回滚
trap 'rollback' ERR
```

| 信号 | 触发 |
|---|---|
| `EXIT` | 脚本退出（任何原因） |
| `ERR` | 命令失败（配合 -e） |
| `INT` | Ctrl+C |
| `TERM` | kill 默认信号 |

## 运维实战

**安全删除脚本**：

```bash
#!/usr/bin/env bash
set -euo pipefail
dir="${1:?用法: $0 目录}"        # 未传参直接报错退出
[ -d "$dir" ] || { echo "目录不存在"; exit 1; }
rm -rf "${dir:?}/"               # :? 双保险，空值即停
```

**临时文件必清理**：mktemp 建临时目录 + `trap cleanup EXIT`，脚本崩溃也不留垃圾。

## 相关主题

[变量](./variables) · [重定向/pipefail](./redirect-pipe) · [shellcheck](./shellcheck) · [函数](./functions)

## 官方文档

- set：<https://www.gnu.org/software/bash/manual/html_node/The-Set-Builtin.html>
- trap：<https://www.gnu.org/software/bash/manual/html_node/Bourne-Shell-Builtins.html>
- 健壮性最佳实践：<https://google.github.io/styleguide/shellguide.html>