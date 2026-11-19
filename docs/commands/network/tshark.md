---
title: "tshark · 命令行抓包分析"
description: "tshark 命令行 Wireshark、协议解码/字段提取/统计、-Y 显示过滤、-T fields 取字段。比 tcpdump 更强的协议分析，中文详解。"
---

# tshark · 命令行抓包分析

> 命令手册 · [网络](/commands/network/) ｜ 频率：很少用
> tcpdump 抓包看原始，tshark（Wireshark 命令行）能深度解码协议、提取字段、做统计。分析 HTTP/DNS/TLS 细节用它。

## 一句话用途

命令行深度解析网络协议，提取字段、统计、过滤。

## 高频场景速查

```bash
sudo tshark -i eth0                          # 实时抓包解码
sudo tshark -i eth0 -f 'tcp port 80'         # 捕获过滤
sudo tshark -i eth0 -Y 'http.request'        # 显示过滤（只看 HTTP 请求）
sudo tshark -r cap.pcap                      # 读 pcap 文件
sudo tshark -r cap.pcap -Y 'dns' -T fields -e dns.qry.name   # 提取 DNS 查询名
sudo tshark -i eth0 -q -z io,stat,1          # 每秒流量统计
sudo tshark -i eth0 -q -z conv,tcp           # TCP 会话统计
```

## 参数详解

| 参数 | 含义 |
|---|---|
| `-i 接口` | 抓包接口 |
| `-f` | 捕获过滤（BPF，同 tcpdump） |
| `-Y` | 显示过滤（Wireshark 语法） |
| `-r 文件` | 读 pcap |
| `-w 文件` | 写 pcap |
| `-T fields -e 字段` | 提取指定字段 |
| `-q -z 统计` | 统计模式 |
| `-c N` | 抓 N 包 |

## 捕获过滤 vs 显示过滤

- `-f`（BPF）：抓的时候就过滤，省资源（`tcp port 80`）。
- `-Y`（Wireshark）：抓后显示过滤，语法丰富（`http.request.method=="GET"`）。

## 运维实战

**分析 HTTP 请求**：`tshark -i eth0 -Y http.request -T fields -e http.host -e http.request.uri` 看访问了哪些 URL。
**DNS 排查**：提取 dns.qry.name 与 dns.a 看解析请求与响应。
**TLS 握手**：`-Y tls.handshake` 看 SNI/证书交换，排 HTTPS 问题。
**流量统计**：`-z io,stat,1` 看每秒吞吐定位突发。

::: tip tshark vs tcpdump
tcpdump 轻量、服务器默认有，适合快速抓包存 pcap；tshark 解码强但重，适合深度分析。常配合：tcpdump 抓 → tshark/Wireshark 分析。
:::

## 相关命令

[tcpdump](./tcpdump) · [ss](./ss) · [curl](./curl) · [openssl](/commands/devtools/openssl)

## 官方文档

- tshark：<https://www.wireshark.org/docs/man-pages/tshark.html>
- 显示过滤：<https://www.wireshark.org/docs/dfref/>