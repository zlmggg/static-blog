---
title: "nc / socat / telnet · 端口与连接测试"
description: "nc 测端口连通/监听/传数据、socat 双向转发、telnet 测端口。ping 不通时验证 TCP 端口，中文详解。"
---

# nc / socat / telnet · 端口与连接测试

> 命令手册 · [网络](/commands/network/) ｜ 频率：每天用
> ping 被禁、要测具体端口通不通——nc（netcat）是网络瑞士军刀，测端口、临时监听、传数据都行。

## 一句话用途

测试 TCP/UDP 端口连通性，临时起监听，双向传数据。

## 高频场景速查

```bash
nc -zv 10.0.0.11 80              # 测 TCP 80 通不通（-z 扫描 -v 显示）
nc -zv 10.0.0.11 20-100          # 扫端口范围
nc -zuv 10.0.0.11 53             # 测 UDP 53
nc -l 8080                       # 监听 8080（临时服务端）
echo hi | nc 10.0.0.11 8080      # 发数据
nc -w 3 10.0.0.11 3306           # 3秒超时
telnet 10.0.0.11 6379            # 测端口（连上可交互）
socat TCP-LISTEN:8080,fork TCP:10.0.0.11:80   # 端口转发
```

## 参数详解

### nc

| 参数 | 含义 |
|---|---|
| `-z` | 只测连通不发数据 |
| `-v` | 显示结果 |
| `-l` | 监听模式 |
| `-u` | UDP（默认 TCP） |
| `-w 秒` | 超时 |
| `-k` | 监听保持（多连接） |
| `-p 端口` | 指定源端口 |

## 运维实战

**测远程端口**：`nc -zv 数据库IP 3306`  succeeded=通，refused=没监听，timeout=被防火墙挡。
**临时收文件**：接收端 `nc -l 9999 > file`，发送端 `nc 接收IP 9999 < file`。
**验证防火墙规则**：改完规则用 nc 测端口确认放行/拦截生效。
**socat 转发**：把本地 8080 转发到后端 80，临时调试用。

::: tip nc 版本差异
有 traditional/netcat-openbsd 两个版本，参数略有差异（-z 在某些版本无）。`nc -h` 看支持。测端口最稳是 `nc -zv` 或 bash 内建 `</dev/tcp/IP/端口`。
:::

## 相关命令

[ss](./ss) · [ping](./ping) · [curl](./curl) · [tcpdump](./tcpdump) · [nmap](./nmap)

## 官方文档

- nc：<https://man7.org/linux/man-pages/man1/nc.1.html>
- socat：<https://man7.org/linux/man-pages/man1/socat.1.html>