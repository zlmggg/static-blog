---
title: "ulimit · 资源限制"
description: "ulimit 看/改进程资源限制（文件句柄 -n、进程数 -u、core -c）、软硬限制、/etc/security/limits.conf 持久化、systemd 服务限制。排 too many open files，中文详解。"
---

# ulimit · 资源限制

> 命令手册 · [进程与系统](/commands/system/) ｜ 频率：偶尔用
> 服务报 "too many open files"？进程能开多少文件、多少进程，由 ulimit 限。高并发服务必须调。

## 一句话用途

查看和设置当前 shell 及其子进程的资源上限（文件句柄、进程数等）。

## 高频场景速查

```bash
ulimit -a                # 看所有限制
ulimit -n                # 最大打开文件数
ulimit -n 65535          # 临时改（当前 shell）
ulimit -u                # 最大进程数
ulimit -c unlimited      # 允许生成 core dump
ulimit -Hn               # 看硬限制
ulimit -Sn               # 看软限制
```

## 软限制 vs 硬限制

- **软限制（-S）**：实际生效值，可自行调高到硬限制。
- **硬限制（-H）**：天花板，普通用户只能降不能升，root 可升。

## 持久化

### 用户级（/etc/security/limits.conf）

```text
*    soft  nofile  65535
*    hard  nofile  65535
*    soft  nproc   65535
*    hard  nproc   65535
```

重新登录生效（PAM 加载）。

### systemd 服务级

limits.conf 对 systemd 服务**不生效**！要在 service 里设：

```ini
[Service]
LimitNOFILE=65535
LimitNPROC=65535
```

`systemctl daemon-reload && systemctl restart 服务`。

::: danger 服务句柄改不动的坑
改了 limits.conf 但 systemd 起的 nginx 还是 1024——因为 systemd 不走 PAM limits。必须在 service 文件设 LimitNOFILE，或全局改 /etc/systemd/system.conf 的 DefaultLimitNOFILE。
:::

## 运维实战

**Nginx/MySQL 高并发**：service 设 LimitNOFILE=65535，配合 [sysctl](./sysctl) fs.file-max。
**排 too many open files**：`cat /proc/PID/limits` 看进程实际限制，`ls /proc/PID/fd | wc -l` 看已用。
**允许 core 排查崩溃**：`ulimit -c unlimited` + 配 core_pattern。

## 相关命令

[sysctl](./sysctl) · [systemctl](./systemctl-journalctl) · [lsof](/commands/observe/lsof) · [coredumpctl](./coredumpctl)

## 官方文档

- ulimit：<https://man7.org/linux/man-pages/man1/ulimit.1p.html>
- limits.conf：<https://man7.org/linux/man-pages/man5/limits.conf.5.html>