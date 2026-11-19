---
title: "gdb / pstack / strace 补充 · 进程调试"
description: "gdb 附加进程看栈/断点、pstack 快速看线程栈、readelf/objdump 看二进制结构。与 strace/perf 配合定位深层问题，中文详解。"
---

# gdb / pstack · 进程调试

> 命令手册 · [排障观测](/commands/observe/) ｜ 频率：很少用
> strace 看系统调用、perf 看热点，但要看"进程此刻卡在哪个函数调用栈"，用 gdb/pstack。

## 一句话用途

附加到运行中进程看调用栈、调试崩溃 core、分析二进制结构。

## 高频场景速查

```bash
pstack 1234                  # 快速打印所有线程栈（需装）
sudo gdb -p 1234             # 附加进程
# gdb 内：
#   bt          看当前线程回溯栈
#   thread apply all bt   所有线程栈
#   detach      脱离（让进程继续）
gdb ./app core.nginx         # 分析 core
#   bt          看崩溃栈
readelf -d ./app             # 看动态依赖（比 ldd 安全）
objdump -d ./app | head      # 反汇编
```

## gdb 常用命令

| 命令 | 作用 |
|---|---|
| `bt` / `backtrace` | 调用栈 |
| `thread apply all bt` | 所有线程栈 |
| `info threads` | 线程列表 |
| `frame N` | 切到第 N 帧 |
| `print 变量` | 看变量值 |
| `detach` | 脱离进程 |
| `quit` | 退出 |

::: danger gdb 附加会暂停进程
gdb -p 附加瞬间进程被停住（SIGSTOP），生产上会让服务短暂无响应。看完尽快 detach。pstack 也短暂暂停。高峰期慎用。
:::

## 运维实战

**进程卡死定位**：`pstack PID` 看所有线程栈，发现全卡在某个锁/系统调用，对照代码定位。
**崩溃分析**：[coredumpctl](/commands/system/coredumpctl) 导出 core，`gdb ./app core` + `bt` 看崩在哪行（需调试符号）。
**C/C++ 死锁**：gdb 看各线程持有的锁与等待关系。

## 相关命令

[strace](./strace) · [perf](./perf) · [coredumpctl](/commands/system/coredumpctl) · [jstack JVM](./jvm) · [ldd/strings](./ldd-strings)

## 官方文档

- GDB：<https://www.sourceware.org/gdb/documentation/>
- pstack：<https://man7.org/linux/man-pages/man1/pstack.1.html>