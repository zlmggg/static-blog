---
title: "update-alternatives · 多版本切换"
description: "Debian 系 update-alternatives 与 RHEL 系 alternatives 管理同一命令的多版本（java/python/gcc），列出/设置/自动切换。参数中文分级。"
---

# update-alternatives · 多版本切换

> 命令手册 · [软件包管理](/commands/package/) ｜ 频率：很少用
> 系统装了多个 java/python/gcc 版本时，用 alternatives 决定 `java` 命令默认指向哪个。

## 一句话用途

管理"同一个命令的多个版本"，一条命令切换默认版本，不用手动改软链。

## 高频场景速查

```bash
# Debian/Ubuntu
sudo update-alternatives --config java        # 交互选默认 java
sudo update-alternatives --list java          # 看候选
sudo update-alternatives --install /usr/bin/java java /opt/jdk17/bin/java 1700
sudo update-alternatives --install /usr/bin/java java /opt/jdk21/bin/java 2100

# RHEL/Rocky（命令名 alternatives）
sudo alternatives --config java
sudo alternatives --install /usr/bin/java java /opt/jdk17/bin/java 1700
```

## 参数详解

| 参数 | 含义 |
|---|---|
| `--config 名` | 交互选默认版本 |
| `--list 名` | 列候选 |
| `--install 链接 名 真实路径 优先级` | 注册一个候选 |
| `--remove 名 路径` | 移除候选 |
| `--auto 名` / `--manual 名` | 自动（按优先级）/手动模式 |

`--install` 四个参数：通用链接（/usr/bin/java）、组名（java）、实际路径、优先级（数字越大自动模式越优先）。

## 运维实战

**装了 JDK17 和 21，切默认**：分别 `--install` 注册（优先级 1700/2100），`--config java` 选 21。自动模式下优先级高的胜出。

**python2/3 共存**：同理注册 python 候选，避免直接改 /usr/bin/python 软链导致系统工具（依赖特定版本）出错。

::: tip 易错点
别手动 `ln -sf` 改 /usr/bin/java——会绕过 alternatives 管理，包升级时冲突。统一用 alternatives 注册切换。
:::

## 相关命令

[dnf/yum](./dnf-yum) · [apt](./apt) · [which/whereis](/commands/system/) 查命令路径

## 官方文档

- update-alternatives：<https://manpages.debian.org/bookworm/dpkg/update-alternatives.1.en.html>
- alternatives（RHEL）：<https://man7.org/linux/man-pages/man8/alternatives.8.html>