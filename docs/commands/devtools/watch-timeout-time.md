---
title: "watch / timeout / time · 执行控制"
description: "watch 周期重复执行盯变化、timeout 给命令设超时防卡死、time 测命令耗时。脚本与排障常用，参数中文分级。"
---

# watch / timeout / time · 执行控制

> 命令手册 · [开发与效率](/commands/devtools/) ｜ 频率：偶尔用
> 三个控制命令执行方式的小工具：watch 盯着看变化、timeout 防卡死、time 测耗时。

## 一句话用途

周期重复跑命令看变化、给可能卡死的命令设超时、测一条命令跑多久。

## 高频场景速查

```bash
watch -n 2 'ss -ltnp'                  # 每2秒看端口（盯变化）
watch -d -n 1 'df -h'                  # -d 高亮变化部分
timeout 30 curl -s http://slow-api     # 30秒不返回就杀掉
timeout -k 5 30 long-task              # 30秒TERM，再5秒还没退就KILL
time ./backup.sh                       # 测耗时（real/user/sys）
```

## 参数详解

### watch

| 参数 | 含义 |
|---|---|
| `-n N` | 间隔 N 秒（默认2） |
| `-d` | 高亮前后差异 |
| `-t` | 不显示顶部标题 |
| `-g` | 输出变化时退出 |

### timeout

| 参数 | 含义 |
|---|---|
| `时长 命令` | 超时发 TERM |
| `-k 时长` | TERM 后再等这么久发 KILL |
| `-s 信号` | 指定发送的信号 |
| 退出码 124 | 表示超时被杀 |

### time

输出 `real`（墙钟总耗时）、`user`（用户态 CPU）、`sys`（内核态 CPU）。real 远大于 user+sys 说明在等 IO/网络。

## 运维实战

**盯磁盘增长**：`watch -d -n 5 'df -h /data'` 看哪个挂载点涨得快。
**脚本防卡死**：巡检脚本里每个远程命令包 `timeout 10 ssh ...`，避免一台卡死拖垮整个巡检。
**定位慢在哪**：`time` 看 real vs user+sys，IO 等待还是 CPU 计算一目了然。

::: tip 易错点
`timeout` 默认发 TERM，进程可能忽略；加 `-k` 兜底 KILL。退出码 124 是超时标志，脚本里据此判断。
:::

## 相关命令

[time 性能观测](/commands/observe/) · [curl](/commands/network/curl) · [parallel](./fzf-parallel-pv)

## 官方文档

- watch：<https://man7.org/linux/man-pages/man1/watch.1.html>
- timeout：<https://man7.org/linux/man-pages/man1/timeout.1.html>