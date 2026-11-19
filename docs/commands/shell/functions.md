---
title: "函数 · 组织与复用"
description: "Shell 函数定义与调用、参数 $1/$@/$#、return 与退出码、local 局部变量、函数库 source。脚本组织复用中文详解。"
---

# 函数 · 组织与复用

> 命令手册 · [Shell 与脚本](/commands/shell/) ｜ 主题页
> 把重复逻辑封装成函数，脚本更清晰可复用。函数的参数、返回值、变量作用域有讲究。

## 一句话用途

把一段逻辑命名封装，传参调用，避免重复代码。

## 定义与调用

```bash
log() {
  printf '[%s] %s\n' "$(date '+%F %T')" "$*"
}
log "开始部署"                 # 调用，参数空格分隔

deploy() {
  local host="$1"             # local 局部变量，不污染全局
  local port="${2:-22}"       # 第二参默认 22
  ssh -p "$port" rocky@"$host" 'bash -s' < deploy.sh
}
deploy 10.0.0.11
```

## 参数与返回

| 符号 | 含义 |
|---|---|
| `$1 $2 ...` | 位置参数 |
| `$@` | 所有参数（各自独立，**推荐**） |
| `$*` | 所有参数（合成一个） |
| `$#` | 参数个数 |
| `$0` | 脚本/函数名 |
| `return N` | 返回退出码（0-255，不是返回值） |
| `$?` | 上一条命令/函数退出码 |

::: danger return 是退出码不是返回值
Shell 函数 `return` 只能返回 0-255 的状态码。要"返回字符串"用 echo 输出 + 命令替换接收：`result=$(get_ip)`。
:::

## 局部变量与作用域

```bash
g=全局
f() {
  local g=局部        # local 只在函数内生效
  echo "$g"
}
f                    # 局部
echo "$g"            # 全局（未被改）
```

不用 local 的变量默认全局，函数间易互相污染——**函数内变量一律 local**。

## 函数库复用

```bash
# lib.sh
log() { ...; }
die() { echo "$*" >&2; exit 1; }

# main.sh
source ./lib.sh      # 引入函数库
log "ready"
[ -f cfg ] || die "缺配置"
```

## 运维实战

**统一日志/报错函数**：log/die 封装，全脚本复用，格式一致。
**参数校验**：函数开头 `[ $# -ge 1 ] || { echo "用法..."; return 1; }`。

## 相关主题

[变量](./variables) · [getopts/shift](./getopts-shift) · [exec/source/eval](./exec-source-eval) · [健壮性](./robust)

## 官方文档

- Bash 函数：<https://www.gnu.org/software/bash/manual/html_node/Shell-Functions.html>