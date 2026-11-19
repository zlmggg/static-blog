---
title: "rg (ripgrep) · 极速代码搜索"
description: "ripgrep 递归搜代码、默认忽略 .gitignore、-t 按类型/-i 忽略大小写、比 grep -r 快得多。现代搜索利器，中文详解。"
---

# rg (ripgrep) · 极速代码搜索

> 命令手册 · [文件与文本](/commands/basic/) ｜ 频率：每天用
> 在项目里搜字符串/正则，rg 比 grep -r 快一个量级，自动跳过 .git/node_modules，默认彩色高亮。

## 一句话用途

递归极速搜索文件内容（grep 的现代替代）。

## 高频场景速查

```bash
rg 'error'                       # 当前目录递归搜
rg -i 'timeout'                  # 忽略大小写
rg -t py 'import'                # 只搜 Python 文件
rg -t log 'ERROR'                # 只搜日志类型
rg -l 'TODO'                     # 只列含匹配的文件名
rg -c 'error'                    # 每文件匹配次数
rg -A 3 -B 2 'panic'             # 显示上下文（后3前2行）
rg --no-ignore 'secret'          # 不忽略 .gitignore（搜被忽略文件）
rg -g '*.conf' 'listen'          # 按 glob 过滤文件
```

## 参数详解

| 参数 | 含义 |
|---|---|
| `-i` | 忽略大小写 |
| `-t 类型` | 按文件类型（py/go/log/yaml） |
| `-g glob` | 按通配符过滤文件 |
| `-l` | 只列文件名 |
| `-c` | 计数 |
| `-A/-B/-C N` | 后/前/前后上下文 |
| `-w` | 全词匹配 |
| `--no-ignore` | 不遵守 .gitignore |
| `-uu` | 搜隐藏+被忽略文件 |

::: tip rg vs grep
rg 默认递归、智能忽略、多线程、彩色，搜代码项目首选。grep 是 POSIX 标准、服务器必有、管道过滤单文件仍常用。两者互补：项目搜索 rg，脚本管道 grep。
:::

## 运维实战

**搜配置项**：`rg -g '*.conf' 'worker_processes' /etc/nginx`。
**搜日志错误**：`rg -t log -i 'error|fail' /var/log`。
**找代码引用**：`rg -t py 'def connect'` 定位函数定义。

## 相关命令

[grep](./grep) · [find](./find) · [awk](./awk) · [sed](./sed) · [less](./less)

## 官方文档

- ripgrep：<https://github.com/BurntSushi/ripgrep>