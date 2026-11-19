---
title: "ldd / strings · 二进制分析"
description: "ldd 查程序依赖的动态库（排缺 .so）、strings 提取二进制里的可读字符串（找版本/路径/线索）。程序起不来/排错，中文详解。"
---

# ldd / strings · 二进制分析

> 命令手册 · [排障观测](/commands/observe/) ｜ 频率：很少用
> 程序报"缺 libxxx.so"用 ldd 看依赖；想知道二进制里编进了什么路径/版本/提示，用 strings 提取可读文本。

## 一句话用途

查可执行文件依赖哪些动态库、提取二进制里的可读字符串找线索。

## 高频场景速查

```bash
ldd /usr/local/nginx/sbin/nginx      # 看依赖的 .so（not found=缺）
ldd ./app | grep 'not found'         # 只找缺的库
strings /usr/bin/nginx | grep -i version   # 找版本字符串
strings binary | grep '/etc/'        # 找编进的配置路径
strings core.dump | head             # 从 core 找线索
file binary                          # 看文件类型/架构
```

## ldd

输出每个依赖库的解析路径，`not found` 就是缺库。配合 [ldconfig](/commands/package/ldconfig) 修。

::: warning ldd 的安全风险
ldd 对不可信程序可能触发其加载逻辑（等价部分执行）。只对可信/自己编译的程序用，陌生二进制用 `objdump -p` 或 `readelf -d` 看依赖更安全。
:::

## strings

提取二进制中连续可打印字符（默认≥4）。能找到：版本信息、编译路径、错误提示、URL、甚至硬编码密码（安全审计）。

| 参数 | 含义 |
|---|---|
| `-n N` | 最短字符串长度 |
| `-a` | 扫整个文件 |
| `-t x` | 显示十六进制偏移 |

## 运维实战

**程序起不来缺库**：`ldd ./app` 看 not found，装对应包或 [ldconfig](/commands/package/ldconfig) 加路径。
**确认二进制版本**：没有 --version 时 `strings binary | grep -iE 'v[0-9]|version'`。
**安全审计**：strings 找硬编码的密码/密钥/内网地址。
**core 分析辅助**：strings core 看崩溃前的字符串线索。

## 相关命令

[ldconfig](/commands/package/ldconfig) · [gdb/pstack](./gdb-pstack) · [file/stat](/commands/basic/) · [readelf/objdump](./gdb-pstack)

## 官方文档

- ldd：<https://man7.org/linux/man-pages/man1/ldd.1.html>
- strings：<https://man7.org/linux/man-pages/man1/strings.1.html>