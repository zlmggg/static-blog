---
title: "sysctl · 内核参数调优"
description: "sysctl 查看/临时改/持久化内核参数、网络调优（somaxconn/tw_reuse）、内存（swappiness）、文件句柄。/etc/sysctl.conf 与 sysctl.d，中文详解。"
---

# sysctl · 内核参数调优

> 命令手册 · [进程与系统](/commands/system/) ｜ 频率：偶尔用
> 内核运行时的可调参数：网络连接队列、内存回收倾向、文件句柄上限。高并发服务调优绕不开它。

## 一句话用途

查看和修改内核运行时参数，临时生效或持久化。

## 高频场景速查

```bash
sysctl -a                          # 看所有参数
sysctl net.core.somaxconn          # 看单个
sudo sysctl -w net.core.somaxconn=65535   # 临时改（重启失效）
sudo sysctl -p                     # 加载 /etc/sysctl.conf
sudo sysctl --system               # 加载所有 sysctl.d 配置
```

## 持久化

写 `/etc/sysctl.d/99-tuning.conf`（推荐，按文件管理）：

```text
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.ip_local_port_range = 1024 65535
vm.swappiness = 10
fs.file-max = 1000000
```

`sudo sysctl --system` 生效。

## 常用调优参数

| 参数 | 含义 | 典型值 |
|---|---|---|
| `net.core.somaxconn` | listen 队列上限 | 65535 |
| `net.ipv4.tcp_max_syn_backlog` | SYN 半连接队列 | 65535 |
| `net.ipv4.ip_local_port_range` | 本地端口范围 | 1024 65535 |
| `net.ipv4.tcp_tw_reuse` | 复用 TIME_WAIT | 1 |
| `vm.swappiness` | 用 swap 倾向（0-100） | 10（少用swap） |
| `fs.file-max` | 系统文件句柄上限 | 1000000 |
| `net.ipv4.tcp_fin_timeout` | FIN_WAIT2 超时 | 15 |

::: warning 别照抄网上"优化大全"
参数要按实际负载调，盲目改可能适得其反。tcp_tw_recycle 在 NAT 环境会丢连接（新内核已移除），别开。改前 `sysctl 参数` 记录原值，便于回滚。
:::

## 运维实战

**Nginx 高并发**：somaxconn 调大配合 nginx `listen ... backlog=65535`，否则队列瓶颈。
**减少 swap 抖动**：数据库机器 `vm.swappiness=10`，尽量用物理内存。
**排"too many open files"**：fs.file-max 调大 + [ulimit](./ulimit) 进程级调大。

## 相关命令

[ulimit](./ulimit) · [ss](/commands/network/ss) · [free/vmstat](/commands/observe/) · [Nginx 性能](/services/web/nginx/04-实战)

## 官方文档

- sysctl：<https://man7.org/linux/man-pages/man8/sysctl.8.html>
- 内核参数：<https://www.kernel.org/doc/Documentation/admin-guide/sysctl/>