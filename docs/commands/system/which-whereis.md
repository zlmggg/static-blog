---
title: "which / whereis / type · 定位命令"
description: "which 查命令路径、whereis 查二进制/源码/man、type 区分别名/函数/内建/外部。排「用的是哪个版本/为什么是这个行为」，中文详解。"
---

# which / whereis / type · 定位命令

> 命令手册 · [进程与系统](/commands/system/) ｜ 频率：偶尔用
> 同名命令装了多个版本，到底跑的哪个？which/type 告诉你真实路径与类型。

## 一句话用途

查命令的可执行文件路径、区分它是别名/函数/内建还是外部程序。

## 高频场景速查

```bash
which python3                # 查路径（PATH 中第一个）
which -a python3             # 查所有匹配（看装了几个）
whereis nginx                # 二进制+源码+man 位置
type ll                      # 看 ll 是别名
type cd                      # cd 是 shell 内建
type -a python3              # 所有定义（别名/函数/路径）
command -v nginx             # POSIX 方式查路径（脚本推荐）
```

## 三者区别

| 命令 | 查什么 |
|---|---|
| `which` | PATH 里的可执行文件路径 |
| `whereis` | 二进制 + 源码 + man 手册位置 |
| `type` | 命令类型（别名/函数/内建/文件） |
| `command -v` | 脚本里可靠地查路径/存在性 |

::: tip 为什么 type 比 which 准
which 只看 PATH 文件，不知道别名和函数。`which ll` 可能找不到，但 `type ll` 告诉你是 `ls -l` 的别名。脚本里判断命令存在用 `command -v cmd >/dev/null`。
:::

## 运维实战

**确认 python 版本**：`which -a python3` 看有几个，`type -a python3` 看优先级，避免跑错版本。
**排"行为不对"**：`type cmd` 发现是别名/函数在作怪，不是你以为的那个程序。
**脚本判存在**：`command -v docker >/dev/null || { echo "需装 docker"; exit 1; }`。

## 相关命令

[env/export PATH](./env-export) · [update-alternatives](/commands/package/update-alternatives) · [变量](/commands/shell/variables)

## 官方文档

- which：<https://man7.org/linux/man-pages/man1/which.1.html>
- type：<https://www.gnu.org/software/bash/manual/html_node/Bash-Builtins.html>