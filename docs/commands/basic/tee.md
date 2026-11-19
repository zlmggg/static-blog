---
title: "tee · 分流输出"
description: "tee 同时输出到屏幕和文件、-a 追加、管道中间存盘、sudo tee 写受保护文件。管道分流，中文详解。"
---

# tee · 分流输出

> 命令手册 · [文件与文本](/commands/basic/) ｜ 频率：偶尔用
> 管道里既想看到输出又想存文件——tee 像三通管，一边流到屏幕一边写文件。

## 一句话用途

把输入同时写到标准输出和文件（管道分流）。

## 高频场景速查

```bash
ls -l | tee listing.txt          # 屏幕显示+存文件
command | tee -a log.txt         # 追加（不覆盖）
command | tee out.txt | grep err # 分流后继续管道
echo 'config' | sudo tee /etc/protected.conf   # sudo 写受保护文件
command | tee f1.txt f2.txt      # 写多个文件
```

## 参数详解

| 参数 | 含义 |
|---|---|
| `-a` | 追加（默认覆盖） |
| `-i` | 忽略中断信号 |
| 多文件 | 同时写多个 |

::: tip sudo 重定向的坑
`sudo echo x > /etc/file` 不行——重定向由当前 shell（非 root）执行。正确：`echo x | sudo tee /etc/file`，tee 以 root 写。这是 tee 最经典用途。
:::

## 运维实战

**留执行记录**：`./deploy.sh | tee -a deploy.log` 边看边存。
**写 root 配置**：`echo 'net.ipv4.ip_forward=1' | sudo tee -a /etc/sysctl.conf`。
**管道中间存盘**：处理链中 tee 存中间结果便于排查。
**多份输出**：tee 同时写日志和摘要文件。

## 相关命令

[cat](./cat) · [grep](./grep) · [xargs](./xargs) · [重定向与管道](/commands/shell/redirect-pipe) · [sudo](/commands/identity/su-sudo)

## 官方文档

- tee：<https://man7.org/linux/man-pages/man1/tee.1.html>