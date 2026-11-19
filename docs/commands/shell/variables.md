---
title: "变量 / read / printf · Shell 基础"
description: "Shell 变量赋值与展开、环境变量 export、read 读输入、printf 格式化、引号与变量边界。脚本基础语法中文详解。"
---

# 变量 / read / printf · Shell 基础

> 命令手册 · [Shell 与脚本](/commands/shell/) ｜ 主题页
> 脚本的地基：变量怎么存、怎么取、怎么读输入、怎么格式化输出。引号用错是脚本 bug 的头号来源。

## 一句话用途

存数据（变量）、读输入（read）、格式化输出（printf），并搞懂引号与展开规则。

## 变量赋值与展开

```bash
name="web01"                  # 赋值（= 两边不能有空格）
echo "$name"                  # 取值，双引号内仍展开
echo '${name}'                # 单引号原样输出 ${name}
echo "${name}_backup"         # 花括号界定变量边界
readonly PI=3.14              # 只读变量
unset name                    # 删除变量
export PATH="$PATH:/opt/bin"  # 导出为环境变量（子进程可见）
```

### 引号规则（重点）

| 写法 | 行为 |
|---|---|
| `"$var"` | 展开变量，保留空格为一个整体（**默认用这个**） |
| `'$var'` | 原样输出，不展开 |
| `$var` 无引号 | 展开后按空格拆词+通配（易出 bug） |

::: danger 永远给变量加双引号
`rm $file` 当 file 含空格会删错文件；`rm "$file"` 才安全。`[ $x = a ]` 当 x 为空会语法错，`[ "$x" = a ]` 才对。
:::

## 常用展开

```bash
${var:-默认}        # var 空则用默认
${var:=默认}        # var 空则赋值并用默认
${#var}             # 字符串长度
${var%.txt}         # 去最短后缀
${var#prefix}       # 去最短前缀
${var/old/new}      # 替换第一个
${var//old/new}     # 替换全部
$(command)          # 命令替换（取命令输出）
$((1+2))            # 算术展开
```

## read 与 printf

```bash
read -r -p "输入主机名: " host          # -r 不转义反斜杠，-p 提示
read -r -s -p "密码: " pass             # -s 不回显
printf "%-10s %5d\n" "$name" "$count"   # 格式化（比 echo 可控）
printf -v ts '%(%Y%m%d)T' -1            # 格式化到变量
```

`printf` 不像 echo 自动加换行，格式串里写 `\n`；`%s` 字符串、`%d` 整数、`%-10s` 左对齐宽10。

## 运维实战

**安全遍历文件**：`while IFS= read -r line; do ... done < list.txt`（IFS= 保留前后空格，-r 不转义）。
**带默认值的配置**：`PORT="${PORT:-8080}"` 环境没设就用 8080。

## 相关主题

[重定向与管道](./redirect-pipe) · [test/if/case](./test-if-case) · [set -euo pipefail](./robust)

## 官方文档

- Bash 变量：<https://www.gnu.org/software/bash/manual/html_node/Shell-Variables.html>
- Bash 展开：<https://www.gnu.org/software/bash/manual/html_node/Shell-Expansions.html>