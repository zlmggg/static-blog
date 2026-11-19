---
title: "ELK · 集中式日志平台"
description: "Elastic Stack 四组件分工与数据流、Elasticsearch 集群/索引/分片/副本与倒排索引、系统准备与安装、Filebeat 直连 vs Logstash 解析、Kibana 检索、Nginx 日志全流程与常见坑。单页四段。"
---

# ELK · 集中式日志平台

> 单页四段：理论 → 部署 → 功能 → 实战。返回 [服务详解 · 监控与可观测](/services/observability/)。指标监控见 [Prometheus](/services/observability/prometheus/01-理论)。

## 01 · 服务理论

服务跑在一台机器时 `tail -f` 看日志没问题，但线上分散在多台机器，逐个登录翻日志效率极低。**集中式日志平台**把所有机器日志统一采集、集中存储、全文检索、图形分析。这是可观测性三信号里的"日志"支（指标是 [Prometheus](/services/observability/prometheus/01-理论)）。

### Elastic Stack 四组件

| 组件 | 角色 | 特点 |
|---|---|---|
| Elasticsearch | 存储与检索引擎 | 基于 Lucene，JSON 文档，倒排索引全文检索 |
| Logstash | 数据处理管道 | 采集+过滤解析+输出，功能强但重（JVM） |
| Kibana | 可视化界面 | 对接 ES 做检索/图表/仪表盘 |
| Beats（Filebeat） | 轻量采集器 | Go 编写，部署在各主机，占用极小 |

```mermaid
flowchart LR
    F["Filebeat<br/>(各主机采集)"] -->|简单采集直连| ES["Elasticsearch"]
    F -->|需复杂解析| L["Logstash<br/>(grok 解析富化)"] --> ES
    ES --> K["Kibana 检索展示"]
```

::: tip Filebeat 直连还是经 Logstash
日志已结构化或只需简单采集，**Filebeat 直连 ES** 最省资源；需要 grok 拆非结构化文本、字段转换、多源汇聚时才加 Logstash。Logstash 集中部署少量几台，不必每台业务机都装。
:::

### Elasticsearch 核心概念

- **Cluster/Node**：集群由节点组成，靠集群名加入。
- **Index**：一类文档集合，类似库/表，名称全小写。
- **Document**：一条 JSON 记录。
- **Shard/Replica**：索引拆成主分片分布到节点实现水平扩展；副本是主分片拷贝，提供高可用和读吞吐，**主分片和自身副本不在同一节点**。

**主分片数创建后不能改**（副本数可随时调），要提前规划。小日志索引 1 个主分片即可，分片不是越多越好（每个有管理开销）。ES 靠**倒排索引**（记录每个词出现在哪些文档）实现快速全文检索，写入后约 1 秒可搜（近实时）。

## 02 · 部署方案

### 系统准备（ES 硬性要求）

```bash
echo 'vm.max_map_count=262144' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
# limits.conf 设 nofile 65536 / nproc 4096
```

`vm.max_map_count` 不够 ES 启动直接报错，这是新手最常踩的坑。

### 安装 Elasticsearch（9.x）

```bash
# RHEL 系
wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-9.5.4-x86_64.rpm
sudo yum localinstall elasticsearch-9.5.4-x86_64.rpm -y
```

单节点配置 `/etc/elasticsearch/elasticsearch.yml`：

```yaml
cluster.name: my-elk
node.name: node-1
network.host: 0.0.0.0
discovery.type: single-node
```

```bash
sudo systemctl enable --now elasticsearch
curl -k -u elastic:密码 https://127.0.0.1:9200
```

9.x 默认启用认证 + TLS，安装时生成 `elastic` 初始密码**务必保存**，忘了用 `elasticsearch-reset-password -u elastic` 重置。

::: warning 生产别关安全
纯内网实验可设 `xpack.security.enabled: false` 免认证，但只适用隔离学习环境，生产保留认证和 TLS。
:::

Kibana、Filebeat 同版本安装，Kibana 配 `elasticsearch.hosts` 指向 ES，Filebeat 配 output 指向 ES（或 Logstash）。

## 03 · 功能详解

### 文档增删改查

```bash
# 建索引指定分片副本
curl -k -u elastic:密码 -XPUT https://127.0.0.1:9200/logs-nginx?pretty \
  -H 'Content-Type: application/json' -d '{"settings":{"number_of_shards":1,"number_of_replicas":1}}'
# 写文档
curl -k -u elastic:密码 -XPOST https://127.0.0.1:9200/logs-nginx/_doc?pretty \
  -H 'Content-Type: application/json' -d '{"status":200,"uri":"/api"}'
# 检索
curl -k -u elastic:密码 'https://127.0.0.1:9200/logs-nginx/_search?q=status:500&pretty'
```

### Query DSL

复杂查询用 JSON DSL，`bool` 组合 must（必须匹配）/filter（过滤不算分）/should（或）：

```json
{ "query": { "bool": {
  "must": [ { "match": { "uri": "/api" } } ],
  "filter": [ { "range": { "status": { "gte": 500 } } } ]
} } }
```

### Filebeat 采集 Nginx 日志

```yaml
filebeat.inputs:
  - type: filestream
    paths: ['/var/log/nginx/access.log']
output.elasticsearch:
  hosts: ['https://10.0.0.10:9200']
  username: elastic
  password: '请替换为强密码'
```

Filebeat 有内置 Nginx module，能自动解析访问日志字段；复杂自定义解析才上 Logstash grok。

## 04 · 实战参考

**Nginx 日志全流程**：Filebeat 采 access.log → （可选 Logstash grok 拆字段）→ ES 建索引存储 → Kibana 建 index pattern 检索分析（状态码分布、慢请求、Top URI）。配合 [Nginx 日志](/services/web/nginx/04-实战) 的 log_format 定义字段。

**常见坑**：

| 现象 | 原因 | 解法 |
|---|---|---|
| ES 启动报 max_map_count | 内核参数没调 | vm.max_map_count=262144 |
| 集群 yellow | 副本没节点放（单节点） | 单节点设副本数 0 |
| 磁盘水位告警 | ES 默认 85% 停分配 | 清旧索引/扩容/调 ILM |
| 日志查不到 | index pattern 没建/时间范围 | Kibana 建 pattern 调时间 |

**索引生命周期**：日志索引按天滚动（logs-nginx-2026.11.19），用 ILM 自动热温冷归档删除，别让日志无限堆满磁盘。

## 官方文档

- Elastic Stack：<https://www.elastic.co/guide/index.html>
- Elasticsearch：<https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html>
- Filebeat：<https://www.elastic.co/guide/en/beats/filebeat/current/index.html>
- Query DSL：<https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl.html>

---

返回 [服务详解 · 监控与可观测](/services/observability/)。