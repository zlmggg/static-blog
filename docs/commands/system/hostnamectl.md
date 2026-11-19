---
title: "hostnamectl / localectl · 主机与本地化"
description: "hostnamectl 看/改主机名与系统信息、localectl 设语言键盘、/etc/hostname。主机标识与本地化设置，中文详解。"
---

# hostnamectl / localectl · 主机与本地化

> 命令手册 · [进程与系统](/commands/system/) ｜ 频率：很少用
> 改主机名、看系统概览、设语言。hostnamectl 一条命令搞定，不用手动改几个文件。

## 一句话用途

查看/设置主机名与系统标识，设置系统语言与键盘布局。

## 高频场景速查

```bash
hostnamectl                          # 看主机名+系统+内核+架构
sudo hostnamectl set-hostname web01  # 改主机名（静态）
hostnamectl status                   # 同 hostnamectl
localectl                            # 看语言/键盘
sudo localectl set-locale LANG=zh_CN.UTF-8   # 设语言
sudo localectl set-keymap us         # 设键盘
```

## hostnamectl

| 命令 | 作用 |
|---|---|
| `set-hostname 名` | 设静态主机名（写 /etc/hostname） |
| `set-hostname --transient 名` | 临时名（重启失效） |
| `status` | 系统概览 |

改完主机名建议同步 /etc/hosts 里的解析，避免 sudo 报 "unable to resolve host"。

## 运维实战

**批量规范主机名**：装机后 `hostnamectl set-hostname web01`，配合 /etc/hosts 与 DNS 统一标识。
**解决 sudo 解析警告**：改主机名后 `/etc/hosts` 加 `127.0.1.1 web01`。
**服务器统一英文环境**：`localectl set-locale LANG=en_US.UTF-8`，避免中文排序/报错乱码。

## 相关命令

[uname](./uptime-uname) · [date/timedatectl](./date-timedatectl) · [DNS](/services/web/dns) · [env/export](./env-export)

## 官方文档

- hostnamectl：<https://www.freedesktop.org/software/systemd/man/latest/hostnamectl.html>
- localectl：<https://www.freedesktop.org/software/systemd/man/latest/localectl.html>