---
title: "bpftrace / bcc · eBPF 深度观测"
description: "bpftrace 用 eBPF 动态追踪内核/用户函数、统计延迟分布、抓系统调用。无侵入深度排障，bcc 工具集，中文详解。"
---

# bpftrace / bcc · eBPF 深度观测

> 命令手册 · [排障观测](/commands/observe/) ｜ 频率：很少用
> strace 慢、perf 看热点，但要"统计每个 IO 的延迟分布""谁在调某内核函数"，eBPF 工具无侵入、低开销、极灵活。

## 一句话用途

用 eBPF 在内核/用户态动态插桩，做低开销的深度追踪与统计。

## 高频场景速查

```bash
# bpftrace 一行脚本
sudo bpftrace -e 'tracepoint:syscalls:sys_enter_openat { printf("%s %s\n", comm, str(args->filename)); }'
sudo bpftrace -e 'kprobe:vfs_read { @bytes = hist(arg2); }'   # 读大小分布
sudo bpftrace -e 'tracepoint:syscalls:sys_exit_read /comm=="nginx"/ { @ns = hist(args->ret); }'

# bcc 现成工具
sudo /usr/share/bcc/tools/execsnoop      # 抓所有新进程执行
sudo /usr/share/bcc/tools/opensnoop      # 抓文件打开
sudo /usr/share/bcc/tools/biolatency     # 块 IO 延迟分布
sudo /usr/share/bcc/tools/tcpconnect     # 抓 TCP 连接
sudo /usr/share/bcc/tools/funclatency vfs_read   # 函数延迟
```

## bpftrace 探针类型

| 探针 | 含义 |
|---|---|
| `tracepoint:子系统:事件` | 内核静态跟踪点（稳定） |
| `kprobe:函数` | 内核函数入口（动态） |
| `kretprobe:函数` | 内核函数返回 |
| `uprobe:路径:函数` | 用户态函数 |
| `profile:hz:99` | 定时采样（CPU 火焰图） |

## 常用 bcc 工具

| 工具 | 作用 |
|---|---|
| `execsnoop` | 抓进程执行（入侵排查） |
| `opensnoop` | 抓文件打开 |
| `biolatency` | IO 延迟直方图 |
| `tcpconnect`/`tcpaccept` | TCP 连接 |
| `runqlat` | CPU 调度延迟 |
| `memleak` | 内存泄漏追踪 |

## 运维实战

**IO 延迟分布**：`biolatency` 看 p99 延迟，比 iostat 平均值更能反映毛刺。
**抓异常进程**：`execsnoop` 实时看谁在执行命令，入侵时揪恶意进程。
**CPU 火焰图**：`profile:hz:99` 采样 + FlameGraph 生成，看热点函数。

::: tip 易错点
eBPF 需较新内核（4.9+，推荐 5.x）与 root/CAP_BPF。生产低开销但别在高负载长时间跑复杂脚本。bcc 工具路径各发行版不同。
:::

## 相关命令

[perf](./perf) · [strace](./strace) · [iostat](./iotop) · [proc](./proc)

## 官方文档

- bpftrace：<https://bpftrace.org/docs/>
- bcc：<https://github.com/iovisor/bcc>
- eBPF：<https://ebpf.io/>