---
title: "less · 翻页查看大文件"
description: "less 翻页/搜索/跳转大文件、/搜索 n/N、G/g 跳尾首、-N 行号、+F 跟踪。看大日志首选，中文详解。"
---

# less · 翻页查看大文件

> 命令手册 · [文件与文本](/commands/basic/) ｜ 频率：每天用
> 大日志/大配置用 less 翻页看，不刷屏、能搜索、能跳转。比 cat 安全比 more 强。

## 一句话用途

交互式翻页浏览大文件，支持搜索与跳转。

## 高频场景速查

```bash
less app.log                     # 打开
less -N app.log                  # 带行号
less +F app.log                  # 跟踪模式（类似 tail -f，Ctrl+C 停跟踪）
less +/error app.log             # 打开即搜 error
```

## 界面按键

| 键 | 作用 |
|---|---|
| `空格/f` | 下翻一页 |
| `b` | 上翻一页 |
| `↓/↑` | 逐行 |
| `/关键词` | 向下搜索 |
| `?关键词` | 向上搜索 |
| `n` / `N` | 下一个/上一个匹配 |
| `G` | 跳到末尾 |
| `g` | 跳到开头 |
| `行号G` | 跳到指定行 |
| `&模式` | 只显示匹配行 |
| `q` | 退出 |

::: tip less +F 跟踪日志
`less +F` 像 tail -f 实时跟踪，但 Ctrl+C 后可自由翻页搜索，再按 F 恢复跟踪。比 tail -f 灵活。
:::

## 运维实战

**查大日志**：less 打开 → /ERROR 搜索 → n 逐个看 → G 跳最新。
**只看错误行**：`&ERROR` 过滤只显示含 ERROR 的行（再 & 回车取消）。
**定位行号**：报错说第 1234 行，`1234G` 直接跳。

## 相关命令

[cat](./cat) · [head](./head) · [tail](./tail) · [grep](./grep) · [rg](./rg)

## 官方文档

- less：<https://man7.org/linux/man-pages/man1/less.1.html>