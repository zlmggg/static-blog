---
title: "MinIO · S3 兼容对象存储"
description: "对象存储 vs 文件/块存储、MinIO 的 S3 兼容与纠删码、单机/分布式部署、mc 客户端与 bucket 操作、S3 SDK 对接、Nginx 反代与常见坑。单页四段。"
---

# MinIO · S3 兼容对象存储

> 单页四段：理论 → 部署 → 功能 → 实战。返回 [服务详解 · 存储与搜索](/services/storage-search/)。

## 01 · 服务理论

存储分三类：**块存储**（裸磁盘，给数据库）、**文件存储**（NAS 共享目录）、**对象存储**（扁平 bucket + 对象，给图片/视频/备份）。对象存储不做目录树，每个对象是一个 key + 数据 + 元数据，通过 HTTP API 存取，天然适合海量非结构化数据和水平扩展。

公有云有阿里 OSS/腾讯 COS/AWS S3；私有云自建用 **MinIO** 或 Ceph RGW。MinIO 是 Go 开发、**兼容 Amazon S3 API** 的开源对象存储，轻量高性能，支持分布式和纠删码，单对象最大 5TB。适合自建图片/视频/备份存储、S3 网关。

### 纠删码（Erasure Code）

分布式 MinIO 用纠删码而非简单副本：把数据切成数据块 + 校验块分散到多盘，坏几块还能算回原数据。比三副本省空间（副本要 3 倍，纠删码约 1.5 倍），可靠性更高。分布式最少 4 个驱动（节点×盘）。

## 02 · 部署方案

### 单机（开发/小规模）

```bash
docker run -d --name minio -p 9000:9000 -p 9001:9001 \
  -e MINIO_ROOT_USER=admin \
  -e MINIO_ROOT_PASSWORD='请替换为强密码' \
  -v /data/minio:/data \
  minio/minio:RELEASE.2025-xx-xxTxx-xx-xxZ server /data --console-address ":9001"
```

9000 是 S3 API 端口，9001 是 Web 控制台。**tag 即发布日期**（非 latest），部署前到 min.io/download 复制当前稳定 RELEASE。

### 分布式（生产）

多节点多盘，各节点跑 `minio server http://node{1...4}/data{1...4}`（展开成所有节点盘），纠删码自动生效。前面挂 [Nginx](/services/web/nginx/01-理论)/VIP 做入口。

## 03 · 功能详解

### mc 客户端

```bash
mc alias set local http://10.0.0.50:9000 admin '请替换为强密码'
mc mb local/images                     # 建 bucket
mc cp photo.jpg local/images/          # 上传
mc ls local/images                     # 列举
mc anonymous set download local/images # 设公开读
```

### S3 SDK 对接

应用用各语言 S3 SDK：endpoint 指向 MinIO、配 access/secret key、region。因为兼容 S3，代码几乎不用改就能从 AWS S3 切到自建 MinIO。

## 04 · 实战参考

**典型架构**：应用/网页 → MinIO 存图片，访问经 [Nginx 反代](/services/web/nginx/03-功能) 或 CDN。备份脚本把数据库 dump 传 MinIO 异地留存。

**常见坑**：

| 现象 | 原因 | 解法 |
|---|---|---|
| SDK 连不上 | endpoint/端口错（9000 非 9001） | API 用 9000 |
| 路径风格报错 | 默认 virtual-host 风格 | SDK 设 path-style access |
| 分布式起不来 | 节点盘数不满足纠删码 | 至少 4 驱动 |
| 公开访问 403 | bucket 策略私有 | mc anonymous set download |

## 官方文档

- MinIO：<https://min.io/docs/minio/linux/index.html>
- 纠删码：<https://min.io/docs/minio/linux/operations/concepts/erasure-coding.html>
- mc：<https://min.io/docs/minio/linux/reference/minio-mc.html>

---

返回 [服务详解 · 存储与搜索](/services/storage-search/)。