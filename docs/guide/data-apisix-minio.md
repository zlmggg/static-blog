---
title: APISIX 与 MinIO
description: API 网关 APISIX（etcd 架构、Docker 部署、route/upstream/consumer、限流认证流量插件）、DAS/NAS/SAN、S3 对象存储 MinIO（单机/分布式纠删码、mc、SDK 对接）
category: 数据
difficulty: 中级
---
# APISIX 与 MinIO

::: tip 本篇定位
部署云原生 API 网关 **APISIX**（etcd 动态配置、路由/上游、限流认证插件），理解存储分类，部署 S3 兼容对象存储 **MinIO**（单机/分布式、mc、应用对接）。
:::

# 第一部分：APISIX

## 一、APISIX 简介

Apache APISIX 是开源、云原生、高性能 API 网关，基于 OpenResty（Nginx + LuaJIT），配置存在 **etcd**，变更**毫秒级热生效、无需 reload**。提供路由、负载均衡、认证、限流、可观测等上百个插件。

### 1.1 架构

| 组件 | 角色 |
|---|---|
| APISIX | 数据面，处理实际流量 |
| **etcd** | 配置中心，存路由/上游/消费者（APISIX 强依赖，集群 3 节点） |
| APISIX Dashboard | 可视化管理面（可选，更新较慢） |

### 1.2 与其他网关对比

| 网关 | 特点 |
|---|---|
| **APISIX** | etcd 动态配置、热更新、插件多、社区活跃 |
| Kong | 同 OpenResty，数据库 etcd/Postgres，生态成熟 |
| Nginx | 高性能但配置静态、改配置 reload |
| Spring Cloud Gateway | Java 体系集成好，资源/性能不如 Nginx 系 |
| Envoy | xDS 动态配置，Service Mesh 常用 |

## 二、APISIX 部署

### 2.1 docker-compose

`/data/apisix/docker-compose.yml`：

```yaml
services:
  etcd:
    image: bitnami/etcd:3.5.18
    environment:
      - ALLOW_NONE_AUTHENTICATION=yes
      - ETCD_ADVERTISE_CLIENT_URLS=http://etcd:2379
    volumes:
      - /data/apisix/etcd:/bitnami/etcd

  apisix:
    image: apache/apisix:3.11.0-debian
    ports:
      - "9080:9080"      # 数据面
      - "9091:9091"      # Admin API
    volumes:
      - ./config.yaml:/usr/local/apisix/conf/config.yaml:ro
    depends_on: [etcd]

  dashboard:
    image: apache/apisix-dashboard:3.0.0-alpine
    ports:
      - "9000:9000"
    volumes:
      - ./dashboard-conf.yaml:/usr/local/apisix-dashboard/conf/conf.yaml:ro
    depends_on: [etcd]
```

`config.yaml`：

```yaml
deployment:
  role: traditional
  role_traditional:
    config_provider: etcd
  etcd:
    host:
      - "http://etcd:2379"
```

```bash
docker compose up -d
curl http://127.0.0.1:9091/apisix/admin/routes \
  -H 'X-API-KEY: edd1c9f034335f136f87ad84b625c8f1'
```

::: warning Dashboard 现状
Dashboard 停留在 3.0.0。生产推荐 **Admin API、standalone 声明式配置、APISIX Ingress Controller**；学习可用 Dashboard。
:::

## 三、核心对象

| 对象 | 说明 |
|---|---|
| **Route 路由** | 匹配条件（host/uri/method）+ plugins + upstream |
| **Upstream 上游** | 后端节点、负载均衡（roundrobin/chash/ewma）、健康检查 |
| Service | 一组路由复用的插件和上游 |
| Consumer | 消费方身份，配合认证插件 |
| SSL | 证书与 SNI |
| Plugin Config | 可复用的插件集合 |

## 四、路由与插件

### 4.1 创建路由

```bash
curl http://127.0.0.1:9091/apisix/admin/routes/1 \
  -H 'X-API-KEY: edd1c9f034335f136f87ad84b625c8f1' -X PUT -d '
{
  "uri": "/get",
  "hosts": ["api.example.com"],
  "methods": ["GET"],
  "upstream": {
    "type": "roundrobin",
    "nodes": { "httpbin.org:80": 1 }
  }
}'

curl http://127.0.0.1:9080/get -H "Host: api.example.com"
```

### 4.2 常用插件

| 类别 | 插件 |
|---|---|
| 限流 | limit-req（漏桶）、limit-count（周期计数）、limit-conn（并发） |
| 认证 | key-auth、jwt-auth、basic-auth、openid-connect、ldap-auth |
| 流量 | proxy-rewrite、redirect、traffic-split（灰度/金丝雀）、response-rewrite |
| 安全 | cors、ip-restriction、ua-restriction、csrf |
| 可观测 | prometheus、skywalking、opentelemetry、http/log/kafka-log |

在路由的 `plugins` 字段配置即可，例如同时启用 key-auth + limit-count。

---

# 第二部分：MinIO

## 五、存储基础

### 5.1 三种存储形态

| 形态 | 全称 | 特点 | 级别 |
|---|---|---|---|
| DAS | Direct Attached Storage | 存储直连主机（本地盘），简单、便宜，主机故障不可访问 | 块设备 |
| NAS | Network Attached Storage | 接入网络、用 NFS/CIFS/FTP 共享，"文件级"共享、即插即用，性能一般 | 文件级 |
| SAN | Storage Area Network | 高速专用网络（FC/iSCSI），高速、集中、可扩展，成本高 | 块级共享 |

### 5.2 对象存储

对象存储用于海量非结构化数据（图片、视频、备份、日志），把数据作为**对象（Object）**放在**桶（Bucket）**中：

- 每个对象 = **数据 + 元数据 + 唯一标识（ID/Key）**；
- **扁平结构**、无多级目录树，通过 **RESTful API**（S3）访问；
- 水平扩展、多副本/纠删码、高持久，适合读多写少、大文件、云环境。

公有云：阿里云 OSS、腾讯云 COS、AWS S3；**私有云：MinIO、Ceph RGW**。

## 六、MinIO 简介

MinIO 是 Go 开发、**兼容 Amazon S3 API** 的开源对象存储，轻量、高性能、支持分布式和纠删码，适合自建图片/视频/备份存储、私有云、S3 网关。单对象最大可达 5TB。

## 七、MinIO 部署

### 7.1 单机二进制

```bash
wget https://dl.min.io/server/minio/release/linux-amd64/minio -O /usr/local/bin/minio
chmod +x /usr/local/bin/minio
mkdir -p /data/minio

MINIO_ROOT_USER=admin MINIO_ROOT_PASSWORD=Admin@12345 \
minio server /data/minio --console-address ":9001"
# S3 API 9000，控制台 9001
```

### 7.2 Docker（版本锁定）

```bash
docker run -d --name minio \
  -p 9000:9000 -p 9001:9001 \
  -e MINIO_ROOT_USER=admin \
  -e MINIO_ROOT_PASSWORD=Admin@12345 \
  -v /data/minio:/data \
  minio/minio:RELEASE.2025-04-22T22-12-26Z server /data --console-address ":9001"
```

> MinIO tag 即发布日期（非 latest）。上面为格式示例，部署前到 https://min.io/download 复制当前稳定 RELEASE tag。

### 7.3 分布式（生产，纠删码）

```bash
# 4 节点、每节点 2 盘（每台执行）
minio server http://node{1...4}.example.com/data{1...2} \
  --console-address ":9001"
```

- **纠删码 Erasure Coding**：数据分片 + 校验分片，可容忍部分盘/节点故障不丢数据；
- 生产至少 4 节点，启用 TLS、版本控制、生命周期。

## 八、mc 客户端

```bash
wget https://dl.min.io/client/mc/release/linux-amd64/mc -O /usr/local/bin/mc
chmod +x /usr/local/bin/mc

mc alias set local http://10.0.0.13:9000 admin 'Admin@12345'
mc ls local
mc mb local/mybucket                    # 建桶
mc cp image.png local/mybucket/         # 上传
mc ls local/mybucket
mc cp local/mybucket/image.png ./       # 下载
mc anonymous set download local/mybucket   # 公开读
mc share download --expire 1h local/mybucket/image.png  # 临时链接
```

## 九、应用对接

- 用各语言 **S3 SDK**：endpoint 指向 MinIO、配 access/secret key、region；
- 私有文件用 **预签名 URL（presigned URL）**临时授权上传/下载；
- 架构：应用/网页 → MinIO，图片访问可经 **Nginx 反代或 CDN**；
- 图片处理/媒体转码可在上传后对接处理服务。

---

## 面试自测

1. APISIX 为什么能热更新？etcd 在其中起什么作用？
2. Route、Upstream、Consumer 分别是什么？
3. DAS、NAS、SAN 的区别？块级和文件级存储有什么不同？
4. 对象存储和文件存储有什么区别？为什么对象存储适合海量图片？
5. MinIO 的纠删码解决什么问题？分布式部署最少几个节点？
6. 什么是预签名 URL，解决什么问题？

## 相关速查

- [kubectl 命令速查](/reference/kubectl-commands)
- [Linux 命令速查](/reference/linux-commands)
- APISIX 文档：https://apisix.apache.org/docs/
- MinIO 文档：https://min.io/docs/minio/linux/index.html
