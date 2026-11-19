---
title: "fuser · 查谁占用文件/端口"
description: "fuser 查占用文件/目录/端口的进程、-k 杀掉占用者。排「设备忙无法卸载/端口被占」，与 lsof 互补，中文详解。"
---

# fuser · 查谁占用文件/端口

> 命令手册 · [排障观测](/commands/observe/) ｜ 频率：偶尔用
> umount 报 "target is busy"、端口被占——fuser 直接告诉你是哪个进程占着，还能一键杀掉。

## 一句话用途

找出正在使用某文件/目录/端口的进程，必要时终止它们。

## 高频场景速查

```bash
fuser -v /data               # 看谁在用 /data（verbose）
fuser -v -m /mnt             # 看占用挂载点的所有进程
sudo fuser -k /mnt           # 杀掉占用 /mnt 的进程（再 umount）
fuser -v -n tcp 8080         # 看谁占 8080 端口
sudo fuser -k -n tcp 8080    # 杀占用 8080 的进程
fuser -v /var/log/app.log    # 看谁开着这日志
```

## 参数详解

| 参数 | 含义 |
|---|---|
| `-v` | 详细（用户/PID/访问类型/命令） |
| `-m` | 指定挂载点/块设备 |
| `-n 空间` | 命名空间（tcp/udp/file） |
| `-k` | 杀占用进程（默认 TERM） |
| `-i` | 杀前交互确认 |
| `-信号` | 指定信号（如 -9） |

访问类型：`c` 当前目录、`e` 可执行、`f` 打开文件、`r` 根目录、`m` 映射。

## 运维实战

**卸载报 busy**：`fuser -vm /mnt` 看谁占着，`fuser -km /mnt` 杀掉再 `umount /mnt`。
**端口被占**：`fuser -v -n tcp 8080` 找出进程，确认无用后 `-k` 释放。
**日志删了空间没释放**：进程还开着已删文件，`fuser -v 日志` 找到重启它（见 [lsof](./lsof)）。

::: danger -k 会杀进程
fuser -k 直接终止占用者，可能中断业务。先 -v 看清是谁，确认能杀再 -k，加 -i 交互确认更稳。
:::

## 相关命令

[lsof](./lsof) · [umount](/commands/storage/) · [ss](/commands/network/ss) · [kill](/commands/system/kill)

## 官方文档

- fuser：<https://man7.org/linux/man-pages/man1/fuser.1.html>