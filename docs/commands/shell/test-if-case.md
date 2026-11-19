---
title: "test / [ ] / if / case · 条件判断"
description: "test 与 [ ] [[ ]] 区别、文件/字符串/数值判断、if-elif-else、case 模式匹配、&& || 短路。脚本判断逻辑中文详解。"
---

# test / [ ] / if / case · 条件判断

> 命令手册 · [Shell 与脚本](/commands/shell/) ｜ 主题页
> 脚本的"如果…就…"。判断文件存在、字符串相等、数值大小，再分支执行。

## 一句话用途

按条件决定执行哪段：文件在不在、变量等不等、数字大不大。

## test 与括号

```bash
test -f file && echo 存在        # test 命令
[ -f file ] && echo 存在         # [ ] 等价 test（注意空格）
[[ -f file ]] && echo 存在       # [[ ]] bash 增强（推荐）
```

`[ ]` 是命令，**两边和运算符旁必须有空格**；`[[ ]]` 是 bash 关键字，支持 `&&`/`||`/正则，变量可不加引号更安全。

## 常用判断

| 判断 | 含义 |
|---|---|
| `-f file` | 是普通文件 |
| `-d dir` | 是目录 |
| `-e path` | 存在 |
| `-s file` | 非空 |
| `-r/-w/-x` | 可读/写/执行 |
| `-z "$s"` | 字符串为空 |
| `-n "$s"` | 字符串非空 |
| `"$a" = "$b"` | 字符串相等 |
| `$a -eq $b` | 数值相等（-ne -gt -lt -ge -le） |
| `[[ $s == pat* ]]` | 模式匹配 |
| `[[ $s =~ ^[0-9]+$ ]]` | 正则 |

## if 与 case

```bash
if [ -f /etc/nginx/nginx.conf ]; then
  echo "nginx 已装"
elif [ -d /usr/local/nginx ]; then
  echo "源码装的"
else
  echo "未装"
fi

case "$1" in
  start)  systemctl start nginx ;;
  stop)   systemctl stop nginx ;;
  *)      echo "用法: $0 {start|stop}" >&2; exit 1 ;;
esac
```

## && || 短路

```bash
[ -d /data ] || mkdir -p /data       # 不存在才建
cmd && echo 成功 || echo 失败         # 成功/失败分支
```

::: tip 易错点
数值比较用 `-eq/-gt`，字符串用 `=`/`==`，别混。`[ $x = a ]` 当 x 空会报错，用 `[[ ]]` 或加引号。`case` 每个分支以 `;;` 结束。
:::

## 运维实战

**服务管理脚本**：case 接 start/stop/restart 分发。
**前置检查**：`[ -f config.yml ] || { echo "缺配置"; exit 1; }` 缺文件即停。

## 相关主题

[变量](./variables) · [循环](./loops) · [函数](./functions) · [set -euo pipefail](./robust)

## 官方文档

- Bash 条件：<https://www.gnu.org/software/bash/manual/html_node/Bash-Conditional-Expressions.html>