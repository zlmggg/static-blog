---
title: "wget · 下载工具"
description: "wget 下载文件/递归整站、-c 断点续传、-O 改名、--limit-rate 限速、后台下载。与 curl 互补，中文详解。"
---

# wget · 下载工具

> 命令手册 · [网络](/commands/network/) ｜ 频率：偶尔用
> 下载文件用 wget（专注下载、支持递归/续传），调接口用 curl。两者互补。

## 一句话用途

从 HTTP/HTTPS/FTP 下载文件，支持断点续传、递归、限速。

## 高频场景速查

```bash
wget https://example.com/file.tar.gz          # 下载
wget -O app.tar.gz https://example.com/f      # 指定保存名
wget -c https://example.com/big.iso           # 断点续传
wget --limit-rate=1m https://example.com/f    # 限速1MB/s
wget -b https://example.com/big.iso           # 后台下载（日志 wget-log）
wget -i urls.txt                              # 批量下载列表
wget --no-check-certificate https://...       # 跳过证书校验（慎用）
wget -r -np -k https://example.com/docs/      # 递归整站
```

## 参数详解

| 参数 | 含义 |
|---|---|
| `-O 名` | 保存为指定名 |
| `-c` | 断点续传 |
| `-b` | 后台 |
| `-q` | 静默 |
| `--limit-rate` | 限速 |
| `-i 文件` | 从文件读 URL 列表 |
| `-r` | 递归 |
| `-np` | 不追溯到父目录 |
| `-P 目录` | 保存目录 |
| `-t N` | 重试次数 |
| `--timeout` | 超时 |

## wget vs curl

| | wget | curl |
|---|---|---|
| 强项 | 下载/递归/续传 | 调接口/多协议/上传 |
| 递归整站 | 支持 | 不支持 |
| 默认输出 | 存文件 |  stdout |

## 运维实战

**下安装包**：`wget -c URL` 大文件断了续传。
**限速不抢带宽**：生产下载 `--limit-rate=2m` 避免占满出口。
**批量拉取**：URL 写文件 `wget -i list.txt`。
**离线镜像文档**：`wget -r -np -k -p URL` 抓整站供离线看。

::: tip 易错点
--no-check-certificate 跳过证书校验有中间人风险，仅临时调试用。脚本下载建议校验 sha256（[md5sum/sha256sum](/commands/basic/)）确认完整。
:::

## 相关命令

[curl](./curl) · [scp/sftp](./scp-sftp) · [rsync](./ssh-rsync) · [sha256sum](/commands/basic/)

## 官方文档

- wget：<https://www.gnu.org/software/wget/manual/>