---
category: 监控
difficulty: 中级
---

# ELK 日志平台实战

::: tip 本篇定位
从零搭建一套集中式日志平台：Filebeat/Logstash 采集与解析日志、Elasticsearch 存储与检索、Kibana 可视化分析，并以 Nginx 日志为例走通全流程。本篇各组件统一使用 9.5.4 版本。
:::

## 一、简介与架构

### 1.1 为什么需要集中式日志

当服务只跑在一台机器上时，直接 `tail -f` 看日志没问题。但线上服务往往分散在多台机器，逐个登录翻日志效率极低，还面临日志散落、难以检索、保留时间短、无法统计分析的问题。集中式日志平台把所有机器的日志统一采集、集中存储，并提供全文检索和图形化分析。

### 1.2 Elastic Stack 各组件

Elastic Stack（原名 ELK Stack，5.0 加入 Beats 套件后改名）由几个分工明确的组件组成：

| 组件 | 角色 | 说明 |
|---|---|---|
| Elasticsearch（ES） | 存储与检索引擎 | 分布式、近实时的搜索分析引擎，基于 Lucene，数据以 JSON 文档存储 |
| Logstash | 数据处理管道 | 从多来源采集数据，用过滤器转换解析，再输出到 ES；功能强但较重（依赖 JVM） |
| Kibana | 可视化界面 | 对接 ES，提供检索、图表、仪表盘 |
| Beats | 轻量采集器 | Go 编写的一系列单功能代理，部署在各主机，占用资源极小 |

Beats 家族里最常用的是 **Filebeat**（采集日志文件），此外还有 Metricbeat（指标）、Packetbeat（网络包）等。

### 1.3 数据流

典型日志流向：主机上的 Filebeat 采集日志文件，可直接送到 ES，或先送到 Logstash 做解析富化后再入 ES；Kibana 从 ES 读取数据做展示。

![Elastic Stack 数据流：Filebeat 采集各主机日志，可经 Logstash 解析后写入 Elasticsearch，Kibana 从 ES 读取并可视化](/diagrams/elk-01.svg)

::: tip Filebeat 直连还是经过 Logstash
日志已经是结构化、或只需要简单采集，用 **Filebeat 直接输出到 ES**，最省资源；需要复杂解析（如用 grok 拆分非结构化文本）、字段转换、多源汇聚时，才在中间加 **Logstash**。Logstash 通常集中部署少量几台，不必每台业务机都装。
:::

EFK（Elasticsearch + Fluentd + Kibana）是另一套同类方案，Fluentd 常作为容器/K8s 环境的采集器，思路与 ELK 一致，本篇以 Elastic Stack 为准。

## 二、Elasticsearch

### 2.1 核心概念

- **Cluster（集群）**：一个或多个节点的集合，共同保存全部数据，由唯一的集群名标识（默认 `elasticsearch`），节点靠集群名加入。
- **Node（节点）**：集群中的一台服务器，存储数据并参与索引和检索。
- **Index（索引）**：一类文档的集合，类似关系库中的"库/表"，名称必须全小写。
- **Document（文档）**：可被索引的基本信息单位，是一条 JSON 记录。
- **Shard（分片）**：一个索引可被拆成多个分片，分布到不同节点，实现水平扩展和并行。分片有**主分片（primary）**和**副本分片（replica）**。
- **Replica（副本）**：主分片的拷贝，提供高可用（主分片所在节点故障时副本可顶上）和额外的读吞吐。主分片和它的副本不会放在同一节点。

![分片与副本分布：主分片 P0/P1 与对应副本 R0/R1 交叉放置在两个节点上，主分片与自身副本不在同一节点](/diagrams/elk-02.svg)

::: tip 分片数在创建时确定
主分片数在索引创建后**不能修改**（副本数可以随时调整），所以要提前规划。小日志索引通常 1 个主分片即可；分片不是越多越好，每个分片都有管理开销。ES 通过倒排索引实现快速全文检索：它记录每个词出现在哪些文档中。
:::

ES 是**近实时**的：文档写入后约 1 秒可被搜索到（中间有一次刷新 refresh）。

### 2.2 系统准备

ES 对系统参数有要求，先调整（否则启动可能报错或性能差）：

```bash
# 允许进程拥有的最大内存映射区域数
echo 'vm.max_map_count=262144' >> /etc/sysctl.conf
sysctl -p

# 文件句柄和线程数（deb/rpm 安装通常已自带 limits，可确认）
cat >> /etc/security/limits.conf <<'EOF'
*  soft  nofile  65536
*  hard  nofile  65536
*  soft  nproc   4096
*  hard  nproc   4096
EOF
```

### 2.3 安装 Elasticsearch 9.5.4

**Ubuntu / Debian（deb）：**

```bash
wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-9.5.4-amd64.deb
apt install ./elasticsearch-9.5.4-amd64.deb -y
```

**RHEL / Rocky（rpm）：**

```bash
wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-9.5.4-x86_64.rpm
yum localinstall elasticsearch-9.5.4-x86_64.rpm -y
```

::: tip 下载慢
官方源 artifacts.elastic.co 直连慢时，可从清华镜像下载对应版本，路径形如 `https://mirrors.tuna.tsinghua.edu.cn/elasticstack/9.x/apt/`（deb）或 `.../9.x/yum/`（rpm）；也可在本机下载后上传。
:::

安装完成后，安装器会自动生成安全配置：启用认证、为传输层和 HTTP 层配置 TLS，并给出内置超级用户 `elastic` 的初始密码，请**务必保存**这串密码。若忘记可重置：

```bash
/usr/share/elasticsearch/bin/elasticsearch-reset-password -u elastic
```

### 2.4 单机配置与启动

配置文件为 `/etc/elasticsearch/elasticsearch.yml`。单节点学习可设置：

```yaml
cluster.name: my-elk
node.name: node-1
network.host: 0.0.0.0
http.port: 9200
discovery.type: single-node
```

启动并设开机自启：

```bash
systemctl daemon-reload
systemctl enable --now elasticsearch
ss -tnlp | grep 9200
```

默认开启 HTTPS，访问时需要带 `-k`（跳过自签证书校验）和认证：

```bash
curl -k -u elastic:你的密码 https://127.0.0.1:9200
```

```json
{
  "name" : "node-1",
  "cluster_name" : "my-elk",
  "version" : {
    "number" : "9.5.4",
    "build_type" : "deb",
    "lucene_version" : "10.x"
  },
  "tagline" : "You Know, for Search"
}
```

::: warning 生产不要简单关闭安全
纯内网做实验、想免认证访问，可在 `elasticsearch.yml` 设 `xpack.security.enabled: false`，重启后用 `http://` 直接访问。但这只适用于隔离的学习环境；生产环境应保留认证和 TLS。
:::

### 2.5 文档的增删改查

8.x 起移除了 type 概念，文档路径统一为 `/{index}/_doc/{id}`。

**创建索引并指定分片/副本：**

```bash
curl -k -u elastic:密码 -XPUT https://127.0.0.1:9200/index2?pretty \
  -H 'Content-Type: application/json' -d'
{
  "settings": {
    "number_of_shards": 3,
    "number_of_replicas": 1
  }
}'
```

**写入文档（不指定 id 则自动生成，用 POST）：**

```bash
curl -k -u elastic:密码 -XPOST https://127.0.0.1:9200/index1/_doc/1?pretty \
  -H 'Content-Type: application/json' -d'
{
  "name": "linux",
  "age": 18,
  "tags": ["sre", "ops"]
}'
```

**按 id 查询：**

```bash
curl -k -u elastic:密码 -XGET https://127.0.0.1:9200/index1/_doc/1?pretty
```

**全文检索（query string 简单写法）：**

```bash
curl -k -u elastic:密码 'https://127.0.0.1:9200/index1/_search?q=name:linux&pretty'
```

**按 id 删除：**

```bash
curl -k -u elastic:密码 -XDELETE https://127.0.0.1:9200/index1/_doc/1?pretty
```

**修改副本数（主分片数不可改，副本可随时改）：**

```bash
curl -k -u elastic:密码 -XPUT https://127.0.0.1:9200/index2/_settings?pretty \
  -H 'Content-Type: application/json' -d'
{
  "index": { "number_of_replicas": 2 }
}'
```

### 2.6 查询 DSL 与聚合

更复杂的查询用 JSON 风格的 Query DSL。例如按条件组合查询：

```bash
curl -k -u elastic:密码 -XGET https://127.0.0.1:9200/index1/_search?pretty \
  -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "must":   [ { "match": { "name": "linux" } } ],
      "filter": [ { "range": { "age": { "gte": 18 } } } ]
    }
  }
}'
```

::: tip query 与 filter 的区别
`match` 这类 query 会算相关性得分、用于全文匹配；`filter` 只判断"是否满足"、不算分，结果可缓存，做精确条件和范围过滤时更快。日志类查询大量使用 filter。
:::

聚合（aggregation）用于统计，类似 SQL 的 GROUP BY。例如按标签统计文档数：

```json
"aggs": {
  "by_tag": { "terms": { "field": "tags.keyword" } }
}
```

### 2.7 JVM 内存与调优

ES 是 Java 应用，堆内存通过 `/etc/elasticsearch/jvm.options`（或 jvm.options.d 目录）配置：

```text
# 在 /etc/elasticsearch/jvm.options.d/heap.options 中设置
-Xms1g
-Xmx1g
```

- `-Xms` 和 `-Xmx` 设为相同值，避免运行时动态调整；
- 堆大小建议为**物理内存的 50% 左右**、且不超过约 31 GB（超过会失去指针压缩优势），另一半内存留给文件系统缓存（Lucene 高度依赖它）；
- 小内存机器（如 2 GB）跑单节点学习，可给 512m～1g，量力而行。

## 三、Kibana

### 3.1 安装 Kibana 9.5.4

Kibana 版本必须与 Elasticsearch **完全一致**。出于性能考虑，建议装在独立节点上。

**Ubuntu / Debian：**

```bash
wget https://artifacts.elastic.co/downloads/kibana/kibana-9.5.4-amd64.deb
apt install ./kibana-9.5.4-amd64.deb -y
```

**RHEL / Rocky：**

```bash
wget https://artifacts.elastic.co/downloads/kibana/kibana-9.5.4-x86_64.rpm
yum localinstall kibana-9.5.4-x86_64.rpm -y
```

### 3.2 修改配置

配置文件 `/etc/kibana/kibana.yml`：

```yaml
server.port: 5601
server.host: "0.0.0.0"
elasticsearch.hosts: ["https://10.0.0.101:9200"]
elasticsearch.username: "kibana_system"
elasticsearch.password: "kibana_system 用户的密码"
i18n.locale: "zh-CN"
```

::: tip 用 kibana_system 账号而不是 elastic
Kibana 连接 ES 应使用内置的 `kibana_system` 服务账号，而不是超级用户 elastic。该账号初始密码可在 ES 上设置：
`/usr/share/elasticsearch/bin/elasticsearch-reset-password -u kibana_system`。若 ES 关闭了安全，则 hosts 用 `http://`、无需账号密码。
:::

启动并设置开机自启：

```bash
systemctl enable --now kibana
ss -tnlp | grep 5601
```

浏览器访问 `http://服务器IP:5601`。

### 3.3 创建数据视图（索引模式）

Kibana 不直接指定索引，而是先创建一个**数据视图（Data View，旧版叫 Index Pattern 索引模式）**来匹配 ES 中一批索引：

- 进入 **Stack Management → Data Views → Create data view**；
- 名称可填通配符，如 `filebeat-*` 或 `myapp-access-*`，匹配按天生成的索引；
- 时间字段选择 `@timestamp`（日志时间），保存。

### 3.4 Discover 检索与可视化

- **Discover（发现）**：选定数据视图和时间范围，即可逐条浏览日志、按关键词搜索（KQL 语法，如 `status: 500 and clientip: 1.2.3.4`）、展开字段、保存查询；
- **Dashboard（仪表盘）**：在 **Visualize Library** 里基于字段做折线图（如各时段 QPS）、饼图（状态码占比）、数据表（Top IP）等，再添加到仪表盘组合展示。

Filebeat 各模块自带做好的仪表盘，执行 `filebeat setup` 后可直接在 Dashboard 里打开，无需手画。

## 四、日志采集

### 4.1 Filebeat 安装

在产生日志的业务主机上安装 Filebeat **9.5.4**：

```bash
# Ubuntu/Debian
wget https://artifacts.elastic.co/downloads/beats/filebeat/filebeat-9.5.4-amd64.deb
apt install ./filebeat-9.5.4-amd64.deb -y

# RHEL/Rocky
wget https://artifacts.elastic.co/downloads/beats/filebeat/filebeat-9.5.4-x86_64.rpm
yum localinstall filebeat-9.5.4-x86_64.rpm -y
```

### 4.2 Filebeat 配置

配置文件 `/etc/filebeat/filebeat.yml`。新版输入类型推荐 `filestream`。

**方式一：直接输出到 Elasticsearch（最省资源）：**

```yaml
filebeat.inputs:
  - type: filestream
    id: nginx-access
    paths:
      - /var/log/nginx/access.log

output.elasticsearch:
  hosts: ["https://10.0.0.101:9200"]
  username: "elastic"
  password: "你的密码"
```

**方式二：输出到 Logstash 做解析：**

```yaml
filebeat.inputs:
  - type: filestream
    id: nginx-access
    paths:
      - /var/log/nginx/access.log

output.logstash:
  hosts: ["10.0.0.101:5044"]
```

启动：

```bash
systemctl enable --now filebeat
```

### 4.3 使用 Filebeat 模块

Filebeat 为 Nginx、MySQL、系统日志等预置了模块（含采集路径、ES 解析规则和 Kibana 仪表盘）：

```bash
filebeat modules enable nginx
# 按实际路径编辑 /etc/filebeat/modules.d/nginx.yml
filebeat setup -e        # 建立索引模板、数据视图、仪表盘
systemctl restart filebeat
```

### 4.4 Logstash 管道

Logstash 安装（集中部署，版本 9.5.4）：

```bash
# Ubuntu/Debian
wget https://artifacts.elastic.co/downloads/logstash/logstash-9.5.4-amd64.deb
apt install ./logstash-9.5.4-amd64.deb -y

# RHEL/Rocky
wget https://artifacts.elastic.co/downloads/logstash/logstash-9.5.4-x86_64.rpm
yum localinstall logstash-9.5.4-x86_64.rpm -y
```

管道配置放在 `/etc/logstash/conf.d/`，由 `input`、`filter`、`output` 三段组成。下面是接收 Filebeat、用 grok 解析 Nginx 文本日志并写入 ES 的示例：

```ruby
input {
  beats {
    port => 5044
  }
}

filter {
  grok {
    match => { "message" => "%{COMBINEDAPACHELOG}" }
  }
  geoip {
    source => "clientip"
  }
  date {
    match => [ "timestamp", "dd/MMM/yyyy:HH:mm:ss Z" ]
    target => "@timestamp"
  }
}

output {
  elasticsearch {
    hosts => ["https://10.0.0.101:9200"]
    user => "elastic"
    password => "你的密码"
    index => "myapp-access-%{+YYYY.MM.dd}"
  }
}
```

常用过滤器：

| 过滤器 | 作用 |
|---|---|
| grok | 把非结构化文本按模式拆成命名字段（`%{内置模式:字段名}`），Nginx 文本日志可直接用 `%{COMBINEDAPACHELOG}` |
| geoip | 根据 IP 解析地理位置，用于地图和地域分析 |
| date | 用日志自带时间作为事件时间 `@timestamp`，否则默认是采集时间 |
| mutate | 字段重命名、删除、类型转换等整理 |
| useragent | 从 UA 串解析浏览器、操作系统、设备类型 |

改完先做**配置语法检查**再启动（Logstash 配置错误时直接启动会反复失败）：

```bash
/usr/share/logstash/bin/logstash -f /etc/logstash/conf.d/nginx.conf -t
systemctl enable --now logstash
```

::: tip 调试 grok
grok 模式写错是最常见的问题。可以在 **Kibana → Dev Tools（开发工具）→ Grok Debugger** 里贴一条真实日志、边改模式边验证；也可用 `-e` 在命令行快速跑一个最小管道测试。
:::

## 五、实战：Nginx 日志全流程

目标：把 Nginx 访问日志采集进 ES，并在 Kibana 分析状态码、QPS、来源 IP。

![Nginx 日志采集全流程：Nginx 输出 JSON 或文本日志，JSON 可由 Filebeat 直连 ES，文本经 Logstash grok 解析后入 ES，Kibana 建数据视图与仪表盘](/diagrams/elk-03.svg)

**做法 A（推荐）：让 Nginx 直接输出 JSON 日志。** 在 Nginx 配置里定义 JSON 格式并使用，字段天然结构化，Filebeat 可直连 ES、无需 grok：

```nginx
log_format json_log escape=json
  '{"time":"$time_iso8601",'
  '"remote_addr":"$remote_addr",'
  '"request_uri":"$request_uri",'
  '"status":$status,'
  '"body_bytes_sent":$body_bytes_sent,'
  '"request_time":$request_time,'
  '"http_user_agent":"$http_user_agent"}';

access_log /var/log/nginx/access.log json_log;
```

reload Nginx 后，Filebeat 用 filestream 采集并直接输出 ES。

**做法 B：保留默认文本日志，用 Logstash grok 解析。** 即第 4.4 节的管道，`%{COMBINEDAPACHELOG}` 会拆出客户端 IP、请求、状态码、字节数、UA 等字段。

数据进入 ES 后，在 Kibana 创建匹配的 data view（如 `myapp-access-*`），即可在 Discover 检索，并做这些典型分析：按 `status` 统计 4xx/5xx 占比、按时间画 QPS 曲线、按 `remote_addr` 找访问量最高的 IP、用 `request_time` 找慢请求。

::: warning 索引命名限制
从 8.10 起，ES 禁止用 `nginx`、`elasticsearch`、`kibana` 等保留名作为索引、数据流或别名的开头。自定义索引名请用其他前缀（如 `myapp-access-*`、`web-access-*`），否则会被拒绝。Filebeat 模块默认使用 `filebeat-*`，不受影响。
:::

## 六、运维与资源规划

### 6.1 集群状态与常用 _cat API

```bash
# 集群健康状态：green(全部分片正常) / yellow(主分片正常、副本未分配) / red(有主分片缺失)
curl -k -u elastic:密码 'https://127.0.0.1:9200/_cluster/health?pretty'

curl -k -u elastic:密码 'https://127.0.0.1:9200/_cat/nodes?v'    # 节点
curl -k -u elastic:密码 'https://127.0.0.1:9200/_cat/indices?v'  # 索引及大小
curl -k -u elastic:密码 'https://127.0.0.1:9200/_cat/shards?v'   # 分片分布
curl -k -u elastic:密码 'https://127.0.0.1:9200/_cat/health?v'   # 健康概览
```

单节点时集群常显示 **yellow**，原因是单节点无法分配副本（主、副本不能同机），属正常现象；把副本数设为 0 可变 green。

### 6.2 磁盘水位线

ES 按磁盘使用率设置了几道水位线，达到后会限制行为：

- **low（默认 85%）**：不再往该节点分配新分片；
- **high（默认 90%）**：尝试把分片迁移到其他节点；
- **flood_stage（默认 95%）**：节点上的索引被置为**只读**，写入报错。

::: warning 只读了怎么办
磁盘超过 95% 触发只读时，先清理空间，再对受影响索引执行解除只读：
`curl ... -XPUT '<索引>/_block/null' -d '{"index.blocks.read_only_allow_delete": null}'`。根本办法是扩容或用 ILM 定期删旧日志，不要长期卡在高水位。
:::

### 6.3 索引生命周期管理（ILM）

日志通常按天生成索引，配合 **ILM（Index Lifecycle Management）** 自动管理：热阶段（正常读写）→ 温阶段（可缩减、迁移到便宜盘）→ 删除阶段（如保留 30/90 天后自动删除），避免日志无限增长撑爆磁盘。Filebeat 默认就带有 ILM 策略，也可在 Kibana 里自定义。

### 6.4 资源规划与常见问题

- **资源**：ES 吃内存，生产建议至少给 JVM 堆 2 GB 以上、节点留足文件系统缓存；小规格机器（2 GB 内存）只适合单机学习、把堆调小，不建议在同一小机器上同时堆 ES + Logstash + Kibana + 其他重服务。
- **集群部署**：多节点使用相同 `cluster.name`，配置 `discovery.seed_hosts` 列出各节点、`cluster.initial_master_nodes` 指定初始可成为主节点的节点；生产通常 3 个节点起步以实现高可用。
- **ES 起不来**：优先查 `journalctl -u elasticsearch` 和 `/var/log/elasticsearch/`，常见原因是内存不足、`vm.max_map_count` 未改、数据目录权限不对。
- **时间不对**：检索结果时间错位，多半是没配 date 过滤器（用了采集时间而非日志时间）或时区问题。

## 面试自测

1. 为什么需要集中式日志平台？直接在各机器上看日志有什么问题？
2. 说清 Elastic Stack 各组件（ES/Logstash/Kibana/Beats）的职责。
3. Filebeat 和 Logstash 都能采集，区别是什么？什么情况下 Filebeat 直连 ES、什么情况下加 Logstash？
4. 描述一条日志从产生到在 Kibana 展示的完整数据流。
5. ES 中的集群、节点、索引、文档、分片、副本分别是什么？
6. 主分片和副本分片的作用？为什么主分片和它的副本不能在同一节点？
7. 为什么主分片数创建后不能改、副本数可以改？分片是不是越多越好？
8. ES 为什么检索快？什么是倒排索引？为什么说 ES 是"近实时"的？
9. ES 对操作系统有哪些要求（max_map_count、句柄）？为什么？
10. 写出文档的增、查、删的 REST API（注意 8.x 的路径变化）。
11. Query DSL 中 query 和 filter 有什么区别？日志查询为什么多用 filter？
12. ES 的聚合能做什么？举例说明。
13. ES 的 JVM 堆内存怎么设置？为什么建议只占物理内存约 50%？
14. Kibana 连接 ES 为什么用 kibana_system 而不是 elastic？
15. 什么是数据视图（索引模式）？为什么常用通配符如 `filebeat-*`？
16. Logstash 管道由哪三段组成？grok、geoip、date、mutate 各做什么？
17. 为什么要用 date 过滤器把日志时间设为 @timestamp？
18. Nginx 日志采集，让 Nginx 输出 JSON 和用 grok 解析文本，各自优缺点？
19. 集群状态 green/yellow/red 的含义？单节点为什么常是 yellow？
20. ES 的磁盘水位线 low/high/flood_stage 分别会发生什么？触发只读后怎么恢复？
21. 什么是 ILM？它如何解决日志无限增长的问题？
22. 8.10 之后索引命名有什么限制？
23. EFK 和 ELK 的区别？Fluentd 常用于什么场景？

## 相关速查

- 命令速查：[Linux 命令速查](/reference/linux-commands)、[网络命令速查](/reference/network-commands)、[Docker 命令速查](/reference/docker-commands)
- 官方资源：
  - Elastic Stack 下载（含历史版本）：https://www.elastic.co/cn/downloads/
  - Elasticsearch 文档：https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html
  - 索引设置（分片/副本）：https://www.elastic.co/guide/en/elasticsearch/reference/current/index-modules.html
  - Query DSL：https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl.html
  - Filebeat 文档：https://www.elastic.co/guide/en/beats/filebeat/current/filebeat-overview.html
  - Filebeat Nginx 模块：https://www.elastic.co/guide/en/beats/filebeat/current/filebeat-module-nginx.html
  - Logstash 文档：https://www.elastic.co/guide/en/logstash/current/index.html
  - grok 过滤器：https://www.elastic.co/guide/en/logstash/current/plugins-filters-grok.html
  - grok 内置模式：https://github.com/logstash-plugins/logstash-patterns-core/tree/main/patterns
  - Kibana 文档：https://www.elastic.co/guide/en/kibana/current/index.html
  - 索引生命周期 ILM：https://www.elastic.co/guide/en/elasticsearch/reference/current/index-lifecycle-management.html
  - 清华 Elastic Stack 镜像：https://mirrors.tuna.tsinghua.edu.cn/elasticstack/

