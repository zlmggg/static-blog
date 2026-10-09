# 监控告警与日志

::: tip 本篇定位
覆盖监控三大支柱、Prometheus 架构与 Pull 模式、PromQL、Alertmanager 告警流程和 ELK 日志栈。
:::

## 高频面试题

### Q1：一套完整的可观测体系包含什么？

**我的答案：**

业界公认可观测有**三大支柱**：指标（Metrics）、日志（Logs）、链路追踪（Tracing），三者互补。

先说是什么：指标是浓缩的数值时间序列，比如 CPU 利用率、QPS、错误率，好处是轻、能存很久、适合画大盘和告警；日志是离散的事件文本，出问题时看具体报了什么错；链路追踪是一个请求穿过多个服务的完整调用链，用来定位慢在哪一跳。

一套完整链路是：**采集 → 存储 → 展示 → 告警**。采集层在机器上跑 node_exporter、在应用里暴露 `/metrics`；存储层用 Prometheus 存指标、用 Elasticsearch 存日志；展示层用 Grafana 画大盘；告警层由 Alertmanager 发通知。

监控对象也要分层：基础设施（CPU/内存/磁盘/网络）、中间件（MySQL、Redis、Nginx）、应用本身（接口延迟、错误率、JVM）。只监控服务器 CPU 不监控业务接口是不够的——机器很闲但接口全 502，用户照样打不开。

我的原则是：**指标回答"有没有问题"，日志回答"出了什么错"，链路回答"问题在哪一跳"**，三者串起来才能从告警一路定位到代码行。

---

### Q2：Prometheus 的工作原理？Pull 模式怎么理解？

**我的答案：**

Prometheus 我用的是 3.x 版本，架构从左到右几块：首先是**数据源**，业务应用直接暴露 `/metrics` 接口，或机器上跑 node_exporter、MySQL 自带 mysqld_exporter 这类采集器。

核心是 **Pull（拉）模式**：和传统 Zabbix 那种 Agent 主动 Push 上来不一样，Prometheus Server 定时（默认 15 秒）主动去拉这些 `/metrics` 地址。我平时验证一个端点就直接 `curl http://10.0.0.5:9100/metrics`，能看到一坨带 HELP/TYPE 注释的时间序列，比如 `node_cpu_seconds_total`。被抓的地址写在 `prometheus.yml` 的 `scrape_configs` 里；机器多了就用**服务发现**（Kubernetes 里直接发现 Pod，云上用云 API 发现 ECS），不用手写一堆 IP。

拉回来的数据存进本地 **TSDB 时序数据库**，按时间+标签建索引，自带多副本压缩。查询用 **PromQL**，展示喂给 Grafana，告警规则在 Prometheus 里算好后发给 **Alertmanager** 做收敛、分组、路由到企业微信/钉钉/电话。

我对 Pull 模式的理解是：好处是 Prometheus 完全掌控采集节奏、出问题不丢自己的数据；缺点是 Prometheus 自己单点，所以生产上要么用联邦集群、要么用远端存储（Thanos/Mimir）。配置写完我一定会跑 `promtool check config prometheus.yml` 先校验语法，再 reload，避免把整个监控搞挂。

---

### Q3：PromQL 常用查询怎么写？

**我的答案：**

PromQL 不用背全，日常排障就几类。

第一类是**直接查瞬时值**：`node_cpu_seconds_total` 一把抓会返回所有核、所有 mode 的序列，一般要按标签过滤，比如 `node_cpu_seconds_total{mode="idle"}`。

第二类是**算 CPU 使用率**，这是最高频的：先求各核空闲率，再 `100 - avg by(instance)(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100`。`rate()` 算的是这 5 分钟内每秒平均增长速率， Counter 类型必须套 `rate()` 或 `increase()`，不然拿到的是累计总量没意义。

第三类是**按维度聚合**：`sum by(instance)(rate(http_requests_total[5m]))` 算每台机器 QPS；`topk(5, ...)` 取前 5。

第四类是**算分位数延迟**：`histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))` 就是 P99 延迟，SRE 盯延迟必用。

我给个实战记忆：看接口是否变慢，就 `sum by(uri)(rate(http_request_duration_seconds_count[5m]))` 找流量、`histogram_quantile(0.99, ...)` 看长尾、`rate(http_requests_total{status=~"5.."}[5m])` 看 5xx 错误量。K8s 里 Pod 指标是 `container` 开头，排 Pod 问题我先 `kubectl logs <pod>` 看日志，再配 Prometheus 看这个 Pod 的 CPU/内存曲线，两个对着看。

---

### Q4：什么是四大黄金信号？

**我的答案：**

Google SRE 书里提的四大黄金信号，是衡量一个服务健康度最核心的四个维度，我背得很熟。

第一是**延迟（Latency）**：请求花了多久，要分成功和失败请求分别看——失败请求往往更快返回，混在一起会误判。重点看 P99、P95 这种长尾，不是平均值。

第二是**流量（Traffic）**：当前服务承载了多少负载，比如每秒多少请求、每秒多少字节，用 QPS 衡量。

第三是**错误（Errors）**：错误率，比如 5xx 占比、异常抛出率，要盯着它是不是突然抬升。

第四是**饱和度（Saturation）**：资源还剩多少余量，CPU、内存、磁盘、连接数这些最紧的瓶颈用了多少。

我的用法是：新接一个服务，先按这四个信号各配一条 Grafana 图和一条告警，服务健康度就心里有数了。出问题时也按这四个方向分诊——延迟高先查慢查询和下游，错误涨先看发布，流量爆先扩容，饱和了先看资源瓶颈。它其实就是把"用户体验"翻译成了四个能采集的指标。

---

### Q5：告警怎么设计才不被吐槽"狼来了"？

**我的答案：**

告警设计是 SRE 的硬功夫，我有几条原则。

第一，**告警要可执行**。一个告警发出来，值班的人看到得知道该干嘛，发"CPU 高"没用，要发"支付服务实例 i-xxx CPU 持续 10 分钟超 90%，已影响下单，请扩容"。那种只是"磁盘用了 80%"但两周内不会写满的，就别发。

第二，**用 `for` 持续时间去抖**。告警规则里写 `for: 5m`，意思是条件连续满足 5 分钟才触发，避免一次毛刺就把人叫醒。

第三，**分级 + 收敛抑制**。Alertmanager 里配 severity，P0 电话+短信，P1 企业微信群；配 `group_by` 把同实例的告警合并成一条，配 `inhibit` 抑制——比如整个机房挂了，就不要再把下面每台机器的告警全发出来，否则告警风暴能把人淹没。

第四，**告警流程我清楚**：Prometheus 按 rules 算出 firing 状态 → 推给 Alertmanager → Alertmanager 做分组、抑制、静默 → 按 route 路由到不同 receiver（企业微信/钉钉/邮件/电话）。

最后一条铁律：**永远不要发没用的告警**，发多了大家就习惯性忽略，真出大事反而没人看。告警数量要持续精简，每条都要问"这条叫醒我值不值"。

---

### Q6：日志系统怎么收集和分析？ELK 各管什么？

**我的答案：**

日志栈现在主流叫 **ELK/EFK**，我先把每个组件职责讲清楚，这是必考题。

- **Filebeat（或 Fluentd）**：跑在每台机器上的轻量采集器，负责读日志文件、按行切割、打标签（来自哪台机器、哪个服务），然后发给后面。它很轻，不占多少资源，还能做断点续传。
- **Logstash**：重一点的处理管道，负责 grok 把非结构化文本切成字段、过滤脱敏、做富化；现在很多场景用 Filebeat 直接送 ES，把 Logstash 省掉。
- **Elasticsearch（ES）**：存储和检索引擎，日志写进去建倒排索引，支持全文和条件查询。
- **Kibana**：可视化和查询界面，在上面搜日志、画柱状图、做错误率看板。

一条链路就是：**应用写日志文件 → Filebeat 采集 →（Logstash 处理）→ 存入 ES → Kibana 查询展示**。

我的设计要点：日志要**结构化**输出成 JSON，带 time/level/trace_id，这样不用 grok 硬切；级别要规范（DEBUG/INFO/WARN/ERROR）。排障时我常用 Kibana 按 trace_id 把一个请求串起来，配合链路追踪看是哪步慢。

K8s 环境里我会这么说：容器日志不落地，用 `kubectl logs <pod>` 先现场看，再由 DaemonSet 形式的采集器统一收进 ES。生产要注意 ES 本身的容量和分片数，日志要设保留周期（比如留 30 天），老的删冷，不然磁盘先被日志写满。

---

## 相关链接

- [相关文档](/guide/monitor-prometheus-01-intro)
- [ELK 日志栈](/guide/monitor-elk)
