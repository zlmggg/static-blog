---
title: "getopts / shift · 参数解析"
description: "getopts 解析短选项（-h -v -f arg）、shift 移动位置参数、OPTARG/OPTIND、手写长选项。脚本命令行参数中文详解。"
---

# getopts / shift · 参数解析

> 命令手册 · [Shell 与脚本](/commands/shell/) ｜ 主题页
> 让脚本像正规命令一样接 `-f file -v` 选项。getopts 解析短选项，shift 处理剩余位置参数。

## 一句话用途

解析脚本的命令行选项与参数，支持 `-h` 帮助、`-f 值` 带参选项。

## getopts

```bash
#!/usr/bin/env bash
set -euo pipefail
verbose=0; file=""
while getopts "vf:h" opt; do
  case "$opt" in
    v) verbose=1 ;;
    f) file="$OPTARG" ;;        # 带参选项的值在 OPTARG
    h) echo "用法: $0 [-v] [-f file]"; exit 0 ;;
    *) echo "未知选项" >&2; exit 1 ;;
  esac
done
shift $((OPTIND - 1))           # 移走已解析选项，剩位置参数
echo "file=$file verbose=$verbose 剩余=$*"
```

选项串 `"vf:h"`：`v` 无参，`f:` 带参（冒号），`h` 无参。开头加 `:` 进入静默模式自己处理错误。

| 变量 | 含义 |
|---|---|
| `OPTARG` | 当前带参选项的值 |
| `OPTIND` | 下一个要处理的参数索引 |

## shift

```bash
shift        # 位置参数左移一位（$2→$1）
shift 2      # 左移两位
# 遍历所有参数
while [ $# -gt 0 ]; do
  echo "$1"
  shift
done
```

## 长选项（手写）

getopts 只支持短选项。长选项 `--file` 用 case 手写：

```bash
while [ $# -gt 0 ]; do
  case "$1" in
    --file) file="$2"; shift 2 ;;
    --verbose) verbose=1; shift ;;
    --) shift; break ;;
    *) echo "未知: $1" >&2; exit 1 ;;
  esac
done
```

## 运维实战

**部署脚本接环境参数**：`./deploy.sh -e prod -f app.yml -v`，getopts 解析后分发。
**必选参数校验**：解析后 `[ -n "$file" ] || { echo "缺 -f"; exit 1; }`。

## 相关主题

[函数](./functions) · [test/if/case](./test-if-case) · [变量](./variables)

## 官方文档

- getopts：<https://www.gnu.org/software/bash/manual/html_node/Bourne-Shell-Builtins.html>