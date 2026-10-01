---
category: 监控
difficulty: 初级
---

# Prometheus 从 0 到 1 新手实战手册

本篇是写给零基础同学的 Prometheus 上机手册：不堆概念，每一步都告诉你在哪个目录、用什么用户、敲什么命令、应该看到什么、错了怎么修，跟着敲完就能搭出一套中小企业在用的监控告警系统。

---

## 这份手册怎么用

**适合这样的你**：

- 没接触过监控，连"端口""进程"这些词都还模模糊糊；
- 会开 Linux 终端、能复制粘贴命令，但不知道命令背后的意思；
- 想学一门企业里真正在用的监控技术，并且希望学完就能写进简历、上手干活。

**不追求这些**：不考你历史年份、不让你背长篇原理。所有理论都遵循"三句话原则"——是什么、为什么需要、跟当前操作有什么关系，讲完立刻上机。

**学习方法建议**：

1. 准备一台可以随便折腾的 Linux 机器（虚拟机或云服务器都行），系统用 **Ubuntu 22.04 / 24.04 LTS**；用 RHEL/Rocky/CentOS 的同学，手册里同时给出了对应命令。
2. 手册是一环扣一环的，**请按顺序做，不要跳章**。上一条命令的输出，往往就是下一步的输入。
3. 每个大阶段末尾都有"命令速查表"和"常见坑与解决"，卡住了先翻这两块。

---

## 贯穿全书的实战项目：星辰电商监控平台

光讲零散命令学不会，本手册用一个贴近中小企业的真实项目把所有知识点串起来。

**项目背景**：星辰电商是一家几十人规模的电商公司，有 3 台核心业务服务器（Web、应用、数据库），后来又上了容器和 Kubernetes。公司要求搭一套监控系统，做到：

- 主机 CPU、内存、磁盘、网络出问题前提前预警；
- Nginx、MySQL、Redis、Java 应用等中间件运行状态可视；
- 网站打不开、接口超时能在 1 分钟内通知值班人员；
- 定时备份脚本、批处理任务的执行结果可监控；
- 监控数据长期保存，出了故障能回溯；
- 后期扩展到多机房、Kubernetes 集群。

**主机与 IP 规划（示例，请替换成你自己的）**：

| 角色 | 主机名 | 示例 IP | 部署的组件 |
| --- | --- | --- | --- |
| 监控服务器 | monitor | 10.0.0.10 | Prometheus、Alertmanager、Grafana、Pushgateway、Blackbox Exporter |
| Web 服务器 | web01 | 10.0.0.11 | Nginx、Node Exporter |
| 应用服务器 | app01 | 10.0.0.12 | Java/Go 业务应用、Node Exporter |
| 数据库服务器 | db01 | 10.0.0.13 | MySQL、Redis、Node Exporter、MySQL Exporter、Redis Exporter |
| 备用/扩展主机 | node02 | 10.0.0.14 | Node Exporter（演示扩容、联邦用） |

> 如果你只有一台机器也没关系：可以用 Docker 在一台机器上模拟所有角色；手册会在对应位置说明单机做法。

**约定：凡是命令中出现【】包裹的内容，都是需要你替换成自己环境实际值的占位符**，例如：

| 占位符 | 含义 | 示例填法 |
| --- | --- | --- |
| 【监控服务器IP】 | Prometheus 所在机器的 IP | 10.0.0.10 |
| 【Web服务器IP】 | Web 主机的 IP | 10.0.0.11 |
| 【应用服务器IP】 | 应用主机的 IP | 10.0.0.12 |
| 【数据库服务器IP】 | 数据库主机的 IP | 10.0.0.13 |
| 【你的邮箱】 | 接收告警的邮箱 | ops@example.com |
| 【邮箱授权码】 | 邮箱 SMTP 授权码（不是登录密码） | 邮箱后台生成 |

**命令格式约定**：

- 命令代码块里只有命令本身，不带 `[root@...]` 提示符，可以直接复制；
- 需要 root 权限的步骤，会明确告诉你是用 `sudo 命令`、`sudo -i` 切到 root，还是用普通用户；
- 预期输出单独用文本块给出，你实际看到的时间戳、ID 等会不一样，属正常；
- 提示框含义：`::: tip` 是小技巧，`::: warning` 是生产环境必须注意的红线。

**软件版本清单（2026 年 9 月核验的当前稳定版）**：

| 软件 | 本手册采用版本 | 默认端口 | 作用 |
| --- | --- | --- | --- |
| Prometheus | 3.15.0 | 9090 | 监控核心：采集、存储、查询、产生告警 |
| Node Exporter | 1.12.1 | 9100 | 采集主机 CPU/内存/磁盘等指标 |
| Alertmanager | 0.34.1 | 9093 | 处理告警：分组、去重、路由、发送 |
| Pushgateway | 1.11.3 | 9091 | 接收短任务/批处理主动推送的指标 |
| Blackbox Exporter | 0.28.0 | 9115 | 黑盒探测：HTTP/TCP/ICMP/DNS 探活 |
| MySQLd Exporter | 0.20.0 | 9104 | 采集 MySQL 指标 |
| Redis Exporter | 1.92.1 | 9121 | 采集 Redis 指标 |
| Nginx Prometheus Exporter | 1.5.3 | 9113 | 采集 Nginx 指标 |
| JMX Exporter | 1.6.0 | （随 Java 进程） | 采集 Java/JVM 指标 |
| cAdvisor | v0.60.6 | 8080 | 采集容器指标 |
| Grafana | 13.2.2 | 3000 | 图形化大屏展示 |
| VictoriaMetrics | v1.152.0 | 8428 / 8480-8482 | 远程长期存储 |
| Consul | 1.22.7 | 8500 | 服务注册与发现 |

::: warning
生产环境不要用 `latest` 标签，也不要追新到发布没几天的版本。本手册刻意选择已发布一段时间、经过验证的稳定版；版本号会随时间变化，安装前可以到官方下载页核对一眼，链接见文末"相关速查"。
:::

---

## 学习路线图

1. **阶段一**：搞懂监控和 Prometheus 的基本概念与架构（不动手，约 30 分钟）；
2. **阶段二**：把 Prometheus、Node Exporter、Grafana、Pushgateway 装起来，看到第一张监控图；
3. **阶段三**：学会 PromQL 查询语言，自己写 exporter；
4. **阶段四**：玩转标签；
5. **阶段五**：搭告警，邮件/钉钉/企业微信都能收到报警；
6. **阶段六**：服务发现，新机器上线不用手改配置；
7. **阶段七**：监控 MySQL、Redis、Nginx、Java 等各种中间件；
8. **阶段八**：监控 Docker 容器；
9. **阶段九**：联邦集群，支撑多机房；
10. **阶段十**：远程存储，数据长期保存与回溯；
11. **阶段十一**：在 Kubernetes 上落地 Prometheus。

---
# 阶段一：认识监控与 Prometheus

## 阶段目标

- 用大白话搞懂"监控系统"由哪几部分组成、监控些什么；
- 记住 Prometheus 全家桶每个组件是干什么的；
- 理解 Prometheus 最核心的两个特点：**拉（Pull）模式**和**标签数据模型**；
- 能对着架构图把数据流向别人讲清楚。

本阶段以理解为主，不需要上机。

---

## 1.1 监控系统由哪几部分组成

先打个比方：一套监控系统就像**小区物业的安保体系**——

| 监控系统的环节 | 小区里对应什么 | 干什么 |
| --- | --- | --- |
| 数据产生 | 电梯、水泵、电表本身会产生运行数据 | 被监控的设备和软件天然带有状态信息 |
| 数据采集 | 保安巡逻、传感器抄表 | 周期性地把状态数据收集上来 |
| 数据存储 | 物业档案室 | 把数据存起来，以后能查 |
| 数据处理 | 整理报表、算平均值 | 对原始数据做计算（比如平均 CPU 使用率） |
| 数据展示 | 监控大屏 | 用图形把数据画出来给人看 |
| 告警 | 火警铃、给值班保安打电话 | 数据异常时主动通知人处理 |

一个完整的监控系统，就是由**数据产生 → 数据采集 → 数据存储 → 数据处理 → 数据展示 → 告警**这六部分组成的闭环。少了任何一环都不完整：只采集不告警，等于装了摄像头但没人看；只告警不存数据，报警了也没法回溯原因。

### 1.1.1 可观测性的三大信号

你会反复听到"可观测性（Observability）"这个词。

- **是什么**：可观测性就是"不用登录到机器里面，光看系统对外暴露的输出，就能判断系统内部哪里出了问题"的能力。
- **为什么需要**：云原生时代一个应用可能拆成几十上百个服务、几千个容器，出了问题不可能一台台机器登上去翻。
- **和操作的关系**：Prometheus 负责其中的"指标"信号，知道三者区别后，你才不会指望用 Prometheus 去查日志、找调用链。

它包含三大信号（也叫三大支柱），用**去医院看病**来记：

| 信号 | 医院类比 | 记录的内容 | 典型工具 |
| --- | --- | --- | --- |
| 指标 Metrics | 体温计、血压计读出的数字 | 可聚合的数值（CPU 使用率、请求数） | **Prometheus** |
| 日志 Logging | 医生写的病历本 | 一条条带时间的事件记录 | ELK、Loki |
| 追踪 Tracing | 医院走廊监控回放你走过的路线 | 一个请求在多个服务间的完整调用链 | Jaeger、SkyWalking |

本手册只讲"指标"这一支，但要知道另外两支的存在。

### 1.1.2 数据从哪来、怎么采

**数据来源**主要有三类：

1. **硬件/系统本身的记录**：比如 CPU 温度、内存占用，以内核文件或内存属性的形式存在（Linux 上常见于 `/proc`、`/sys` 目录）；
2. **应用主动暴露的接口**：比如 Redis 的 `INFO` 命令、各种软件的 status 页面，主动告诉你"我现在好不好"；
3. **采集工具执行系统命令**：通过 `ps`、`df` 这类命令间接拿到状态。

这些被固定记录下来的"属性指标"，英文叫 **metric（指标）**——一个带名字的、可测量的数值，比如"CPU 使用率""当前在线人数"。

**采集方式**按协议分，先混个眼熟，后面用到再细说：

| 方式 | 一句话解释 |
| --- | --- |
| Agent | 在被监控机器上装一个专用小程序（代理），由它负责收集本机数据 |
| HTTP | 基于网页协议传输数据，在浏览器输入网址能看到数据，Prometheus 主要用这种 |
| SSH | 远程登录到机器上执行命令取数，需要登录凭证 |
| SNMP | 简单网络管理协议，主要用于交换机、路由器等网络设备 |
| IPMI | 智能平台管理接口，用于采集硬件的温度、电压、风扇、电源等物理状态（关机也能采） |

::: tip
为什么强调"周期性"采集？一个孤立的数字没有意义——"CPU 使用率现在是 80%"说明不了问题，但"过去 7 天每天下午 3 点 CPU 都冲到 100%"就能定位规律。所以监控数据必须持续、周期地采。
:::

### 1.1.3 数据为什么要存进"时序数据库"

采集来的数据有个共同点：**每个数值都带着一个时间戳**。这种"按时间顺序记录状态变化"的数据，叫**时间序列数据（Time Series Data）**；专门存它的数据库叫**时序数据库（TSDB，Time Series Database）**。

- **类比**：时序数据就像**心电图、股票 K 线图**——横轴永远是时间，纵轴是数值，一笔一笔连续画出来。
- **为什么需要专门的数据库**：监控数据量极大（一台机器几千个指标、每 15 秒采一次，一天就是上千万个点），但结构极简单（某个指标在某个时刻只有一个值），普通关系型库存它又慢又占地方。
- **和操作的关系**：Prometheus 自带一个时序数据库，装完就有，不用单独装；阶段十会讲它怎么存、怎么外接长期存储。

时序数据的特点（了解即可）：基本只追加写入、很少修改；删除一般是删一整段时间；读取按时间正序或倒序；压缩率极高，一个数据点平均只占 1～2 个字节。

---

## 1.2 监控些什么、用什么标准衡量

### 1.2.1 监控的三大类内容

1. **资源数据（基础设施）**：
   - 硬件：服务器、路由器、交换机、IO 设备；
   - 系统资源：操作系统、网络、容器、虚拟机；
   - 应用软件：Nginx、MySQL、Java 应用等。
2. **业务服务（业务指标）**：服务是否在线、QPS（每秒请求数）、DAU（日活跃用户数）、转化率、充值额度、用户投诉数，以及访问变慢、存储空间不足、主机宕机等故障。
3. **趋势分析**：用历史数据预测未来——比如"按现在的增长，磁盘再过 40 天会写满""双 11 当天流量大概是平时的 8 倍，需要提前扩容"。

### 1.2.2 衡量服务好坏：四个黄金指标

Google 总结了四个"黄金指标"，用来衡量一个在线服务的健康程度。用**一家饭店**来记：

| 黄金指标 | 含义 | 饭店类比 | 例子 |
| --- | --- | --- | --- |
| 延迟 Latency | 处理一个请求花多长时间 | 客人点完菜多久能上菜 | HTTP 请求平均响应时间；**要区分成功请求和失败请求的延迟** |
| 流量 Traffic | 每秒有多少请求进来（吞吐量） | 饭点一小时进来多少客人 | 每秒 HTTP 请求数 QPS、数据库每秒事务数 TPS |
| 错误 Errors | 失败请求的数量或比例 | 上错菜、退菜的数量 | HTTP 500 错误数、超时数、返回异常内容数 |
| 饱和度 Saturation | 资源有多"满" | 大厅上座率、厨师忙不忙得过来 | CPU/内存/磁盘/网络利用率，队列积压长度 |

::: tip
饱和度有个经验用法：很多资源在使用率到 80% 以后性能会陡增式下降，所以告警阈值常设在 80%～90%，而不是等 100% 才报警。
:::

---

## 1.3 监控的三种实现路子

在 Linux 上做监控，大致三种方式：

1. **系统命令**：用 `uptime`、`top`、`df`、`free`、`ss` 等命令临时看一眼。优点是随装随有，缺点是关了终端数据就没了，不能持续、不能告警、不能看历史。
2. **开源监控软件**：
   - **Zabbix**：传统监控的代表，诞生早、功能全，后端用关系型数据库；在微服务、容器大规模动态扩缩容的场景下逐渐吃力。
   - **Prometheus**：为云原生、容器环境设计，自带时序库和强大的查询语言，是当前容器监控的事实标准。
3. **云厂商监控平台**：阿里云云监控、AWS CloudWatch 等，开箱即用，但通常绑定云厂商、收费、定制能力有限。

本手册讲第 2 种里的 Prometheus。

---

## 1.4 正式认识 Prometheus

### 1.4.1 它是什么

- **是什么**：Prometheus（普罗米修斯）名字取自希腊神话中为人类盗火的神；它是一款**开源的时序数据库，也是一套监控告警框架**，用 Go 语言开发，灵感来自 Google 内部的 Borgmon 监控系统。
- **为什么需要它**：传统监控扛不住云原生环境里海量、动态变化的监控目标；Prometheus 用多维标签模型和拉模式解决这个问题。
- **和操作的关系**：它是本手册绝对的主角，阶段二就把它装起来。

它的主要特点：

- **多维数据模型**：时间序列由"指标名 + 一组标签（键值对）"组成，想按哪个维度筛选、聚合都行；
- **自带时序数据库**，不需要额外装数据库；
- **PromQL 查询语言**：能做非常复杂的查询、聚合，是画图和告警的基础；
- **HTTP 拉（Pull）模式**采集；
- 对短生命周期任务，可通过 **Pushgateway** 接收推送；
- 支持**静态配置和服务发现**两种方式找监控目标；
- 自带 Web 界面，也完美支持 Grafana 等第三方看板。

**它擅长**：记录任何纯数字的时间序列，无论是机器监控还是动态微服务监控；设计上强调"每个服务器独立工作、不依赖外部存储"，所以在故障发生、其他基础设施挂掉时，你依然能靠它看数据、定位问题。

**它不擅长（心里要有数）**：

- 单机版 Prometheus **自身不支持集群**（高可用要靠双机+远程存储等方案，阶段五、阶段十讲）；
- 规模过大（上万目标）时单机性能有瓶颈（可用联邦、分片解决，阶段九讲）；
- **不保证 100% 精确**：采集中可能丢点，所以**不能用来做计费、账单**这类要求分毫不差的场景，计费请用其他系统；
- 本身只是"采集+存储+查询+产生告警"，展示靠 Grafana、发告警靠 Alertmanager，需要组件配合。

### 1.4.2 最核心特点一：拉（Pull）模式

Prometheus 最典型的特性：**它主动去被监控目标上"拉"数据，而不是等对方"推"过来**。

- **类比**：Pull 像**老师上课点名**——老师（Prometheus）按花名册主动点，谁没到（拉不到）当场就知道；Push 像**学生主动交作业**——老师只能等，谁没交不一定清楚。

**Pull 模式的优点**：

1. **业务无侵入**：应用只要暴露一个标准的 `/metrics` 网页接口就行（客户端库会自动生成），不用关心 Prometheus 在哪、失败怎么重试、怎么鉴权推送；
2. **服务端集中管控**：采集间隔、超时、标签、过滤、TLS、黑名单全写在 Prometheus 配置里，运维一处管理；
3. **天然自带健康检查**：拉取时如果目标挂了、超时了，Prometheus 会自动生成一个 `up=0` 的指标，直接就能对"实例是否存活"告警；
4. **容器/K8s 友好**：新 Pod 启动自动暴露指标，不用改业务代码。

**Pull 模式的缺点（以及补救办法）**：

| 缺点 | 说明 | 补救办法 |
| --- | --- | --- |
| Prometheus 必须能网络访问到目标 | 防火墙、网段不通就拉不到 | 放通网络/端口，或用远程采集代理 |
| 短生命周期任务拉不到 | 任务可能在两次拉取之间就结束了 | 用 **Pushgateway**，任务结束前主动推 |
| 离线/内网深处服务拉不到 | Prometheus 无法直达 | 在该网络内部署采集代理再转发 |
| 对目标有轻微性能开销 | 每次拉取要消耗一点 CPU | 控制采集频率和指标数量 |

### 1.4.3 最核心特点二：指标名 + 标签的数据模型

Prometheus 里存的每一条时间序列，由**指标名（Metric Name）**和**标签（Labels，键值对）**唯一确定。

- **指标名**：表示"这是什么指标"，要有意义，比如 `http_requests_total`（HTTP 请求总数）。只能用字母、数字、下划线、冒号，且以字母或下划线开头；**冒号是留给记录规则用的**，自己起名别用。
- **标签**：表示"这个指标的哪个维度"，格式是 `标签名="标签值"`。比如：

```text
http_requests_total{method="POST", endpoint="/api/tracks"}
```

读法：`http_requests_total` 是指标名；`method="POST"` 表示只看 POST 请求；`endpoint="/api/tracks"` 表示只看 `/api/tracks` 这个接口。如果 `method` 换成 `"GET"`，那就是**另一条全新的时间序列**。

- 标签名只能用字母、数字、下划线；以 `__`（两个下划线）开头的标签名是**内部保留**的，不要自己定义。
- 标签值可以是任意字符；**标签值为空等于这个标签不存在**。
- 记住一句话：**任何标签值的改变（包括增、删标签），都会产生一条新的时间序列**。这是后面"标签爆炸撑爆内存"那个坑的根源。

### 1.4.4 Job 和 Instance

- **实例（Instance）**：一个能被抓取的目标，通常是 `IP:端口` 的形式，对应一个具体的应用进程。
- **任务（Job）**：一组同类型实例的集合，比如一个 API 服务部署了 4 个副本，这 4 个 instance 同属一个 job。

用**学校**来记：**Job 是班级，Instance 是班里的学生**。

```text
job: api-server
  instance 1: 1.2.3.4:5670
  instance 2: 1.2.3.4:5671
  instance 3: 5.6.7.8:5670
  instance 4: 5.6.7.8:5671
```

这里顺带把网络基础概念补上：

- **IP 地址像"门牌号"**：在网络中找到哪一台机器；
- **端口像"房间号"**：一台机器上同时跑很多程序，靠端口区分数据交给哪个程序。端口范围 0～65535，Prometheus 生态的常用端口见版本清单表（9090、9100 等）。

每次抓取，Prometheus 还会自动生成几个"体检指标"，先眼熟：

| 指标 | 含义 |
| --- | --- |
| `up` | 抓取是否成功：**1 正常，0 失败**，做存活告警就靠它 |
| `scrape_duration_seconds` | 这次抓取花了多少秒 |
| `scrape_samples_scraped` | 这次抓到了多少个样本 |
| `scrape_samples_post_metric_relabeling` | 标签重写后还剩多少样本 |
| `scrape_series_dded` | 这次抓取新增了多少条序列 |

### 1.4.5 指标的文本长什么样

被监控目标暴露出来的数据，本质是一段纯文本，通过网页返回给 Prometheus。格式要点：

- 每行一条，空行忽略；
- 以 `# HELP` 开头的行是这个指标的说明；
- 以 `# TYPE` 开头的行声明指标类型，共四种：**Counter（计数器）、Gauge（仪表盘）、Histogram（直方图）、Summary（摘要）**，阶段三细讲；
- 其他 `#` 开头的是普通注释，会被忽略。

真实样子（阶段二装完就能在浏览器看到）：

```text
# HELP node_cpu_seconds_total Seconds the CPUs spent in each mode.
# TYPE node_cpu_seconds_total counter
node_cpu_seconds_total{cpu="0",mode="idle"} 12345.67
node_cpu_seconds_total{cpu="0",mode="system"} 89.1
```

---

## 1.5 Prometheus 全家桶成员

| 组件 | 角色（一句话） | 大白话类比 |
| --- | --- | --- |
| **Prometheus Server** | 核心：抓取并存储时序数据、执行规则、产生告警 | 监控指挥中心 |
| **Client Library（客户端库）** | 给自研应用用的 SDK，帮应用生成并暴露指标 | 给应用发的"自测体检表" |
| **Exporters（导出器）** | 部署在被监控端，把 MySQL/Nginx/主机等的现成数据翻译成 Prometheus 格式暴露出来 | 翻译官：把各软件的"方言"翻译成 Prometheus 听得懂的话 |
| **Pushgateway** | 临时存放短任务、批处理主动推来的指标，等 Prometheus 来拉 | 临时快递柜：短寿命任务把"作业"放柜子里 |
| **Alertmanager** | 接收 Prometheus 产生的告警，做去重、分组、静默、抑制，再路由到邮件/钉钉/企微等渠道 | 接警台 + 调度员 |
| **Grafana** | 把数据画成漂亮的仪表盘、大屏 | 监控大屏 / 画图师 |
| **Service Discovery（服务发现）** | 动态发现要监控的目标，Prometheus 内置 | 自动更新的花名册 |

::: warning
Pushgateway 只用来接收**短任务、批处理**的指标，**不要用它推送主机层面的指标**（主机指标请用 Node Exporter）。原因：Pushgateway 里的数据会一直保留，主机挂了它还在显示旧数据，会造成"机器都死了监控还显示正常"的假象。
:::

---

## 1.6 架构与数据流向

下图是 Prometheus 的整体架构，本阶段的核心就是看懂它：

![Prometheus 整体架构与数据流向](/guide/diagrams/prometheus-architecture.svg)

按图把工作流程走一遍（建议自己复述一遍）：

1. **找目标**：Prometheus 通过服务发现（DNS、Kubernetes、Consul、文件等）或静态配置，得到一份要监控的目标清单；
2. **采数据**：Prometheus Server 周期性地（默认每 15～60 秒）通过 HTTP 从各类 Exporter、应用的 `/metrics` 接口**拉取（pull）**指标；短生命周期任务则先把指标**推（push）**到 Pushgateway，再由 Prometheus 拉取；
3. **存数据**：拉来的数据存入本地时序数据库（TSDB），先写内存和预写日志（WAL），再定期压缩成数据块落盘；
4. **算规则**：Prometheus 按配置的**记录规则**预先计算常用查询、生成新序列；按**告警规则**周期性计算，条件满足就产生告警；
5. **发告警**：产生的告警推送给 **Alertmanager**，由它去重、分组、静默、抑制，再按路由发送到邮件、钉钉、企业微信、PagerDuty 等接收端；
6. **看数据**：人通过 Prometheus 自带 Web UI、**Grafana** 或调用 HTTP API 的其他客户端来查询、展示数据。

---

## 本阶段概念速查表

本阶段不上机，无命令可查；记住这张概念表即可：

| 术语 | 一句话记住 |
| --- | --- |
| metric 指标 | 一个带名字、可测量的数值 |
| 时序数据 / TSDB | 带时间戳、按时间排列的数据 / 专门存它的库 |
| Pull / Push | Prometheus 主动去拉 / 目标主动来推 |
| 指标名 + 标签 | 唯一确定一条时间序列 |
| Job / Instance | 同类型实例的集合（班级）/ 单个目标（学生） |
| up | 1 健康、0 挂了 |
| Exporter | 把第三方软件数据翻译给 Prometheus |
| Pushgateway | 短任务放指标的临时快递柜 |
| Alertmanager | 告警的接警调度台 |
| Grafana | 画监控大屏的 |
| 四个黄金指标 | 延迟、流量、错误、饱和度 |
| 三大信号 | 指标、日志、追踪 |

---

## 本阶段常见坑与解决

**坑 1：以为装了 Prometheus 就万事大吉，不装 Alertmanager、Grafana**

- 新手做法：只装一个 Prometheus，以为它自带画图和发消息功能。
- 现象：打开 Prometheus 界面只有简单图表，告警也不知道去哪配。
- 根本原因：Prometheus 只负责"采集、存储、查询、**产生**告警"，**展示**靠 Grafana、**发送**告警靠 Alertmanager，职责是拆开的。
- 解决：按阶段二把 Prometheus + Grafana + Alertmanager 一起部署（Docker Compose 一条命令可全起来）。
- 预防：开工前先回看 1.5 的全家桶成员表，明确每个组件职责。

**坑 2：网络不通就急着判定"软件坏了"**

- 新手做法：浏览器打不开 Prometheus/Exporter 页面，反复重装软件。
- 报错原样（浏览器）：`无法访问此网站，10.0.0.11 拒绝了连接请求`；或 Prometheus 目标页显示 `Get "http://10.0.0.11:9100/metrics": dial tcp 10.0.0.11:9100: connect: connection refused`，目标状态为 **DOWN，up=0**。
- 根本原因：Pull 模式要求 Prometheus 能网络访问到目标；服务没启动、没监听对外地址、防火墙没放通、IP/端口写错，都会拉取失败。
- 解决步骤（阶段二会逐条实操）：
  1. 在目标机执行 `ss -lntp | grep 9100` 确认服务是否在监听；
  2. 只监听了 `127.0.0.1` 的要改成监听 `0.0.0.0`；
  3. 放通防火墙：`sudo ufw allow 9100/tcp`（Ubuntu）或 `sudo firewall-cmd --add-port=9100/tcp --permanent && sudo firewall-cmd --reload`（RHEL 系）；云服务器还要在控制台安全组放行；
  4. 在监控机执行 `curl http://【Web服务器IP】:9100/metrics` 验证。
- 预防：部署任何 exporter 后，立刻用 `ss -lntp` 和 `curl` 自检，再配 Prometheus。

**坑 3：用 Pushgateway 推送主机指标**

- 新手做法：图省事，让所有主机把 CPU、内存指标推给 Pushgateway。
- 现象：某台主机关机后，Pushgateway 里仍是它最后推的旧值，监控大屏显示一切正常，漏报宕机。
- 根本原因：Pushgateway 会一直保留推来的数据、不会因目标消失而删除；它本是为"可能在拉取前就消失的短任务"设计的。
- 解决：主机层面一律用 Node Exporter（拉不到时自动 `up=0` 并告警）；Pushgateway 只接收批处理、定时任务指标。
- 预防：记住 1.5 节的警告框。

**坑 4：随手加标签、改标签值，导致序列爆炸**

- 新手做法：把请求 ID、时间戳、用户 ID 这类每次都变的值放进标签。
- 报错/现象：Prometheus 内存、磁盘快速上涨，日志出现 `too many series`、`failed to send series: server returned HTTP 400 ... series limit exceeded` 类报错，Grafana 查询变慢。
- 根本原因：标签值一变就是一条新序列；高基数字段（每次都不同的值）会让序列数无限膨胀。
- 解决：去掉高基数标签；在 Prometheus 启动参数配置序列上限（`--storage.tsdb.max-series`）做保护。
- 预防：标签只放"可枚举、会用来分组筛选"的维度（如实例、接口、方法、状态码），绝不放每次都变的唯一值。

---
# 阶段二：部署 Prometheus 监控系统

## 阶段目标

- 完成监控服务器的初始化（国内软件源、时间同步、防火墙规划）；
- 用 5 种方式之一把 Prometheus 跑起来（重点掌握**二进制**和 **Docker/Compose**）；
- 看懂并会改 Prometheus 主配置文件；
- 完成 Node Exporter、Grafana、Pushgateway 的部署与对接，最终看到主机监控大屏、能用 Pushgateway 上报自定义指标。

本阶段是全书最重要的上机阶段，请在监控服务器 `monitor`（示例 10.0.0.10）上操作。

---

## 2.0 监控服务器初始化

### 2.0.1 把系统软件源换成国内源

官方软件源服务器在国外，装软件又慢又容易断。先换成阿里云源（也可以换成清华源，两者二选一即可）。

**操作目录与用户**：以下命令需要 root 权限。先切到 root：

```bash
sudo -i
```

`sudo -i` 会加载 root 的环境变量、直接进入 root 的家目录，提示符变成 `root@...`。后续凡是看到"用 root 操作"，都指这种状态。输入 `exit` 可退回普通用户。

**Ubuntu 22.04（源文件是 /etc/apt/sources.list）**，先备份再替换：

```bash
cp /etc/apt/sources.list /etc/apt/sources.list.bak
sed -i 's@//.*archive.ubuntu.com@//mirrors.aliyun.com@g' /etc/apt/sources.list
sed -i 's@//.*security.ubuntu.com@//mirrors.aliyun.com@g' /etc/apt/sources.list
```

参数解释：`cp 源 目标` 是复制备份；`sed -i` 表示直接修改文件；`s@旧@新@g` 表示把文件里所有旧文本替换成新文本，`@` 只是分隔符（用 `/` 也行，但网址里 `/` 多，用 `@` 看得清楚）。

**Ubuntu 24.04（源文件改成了 DEB822 格式：/etc/apt/sources.list.d/ubuntu.sources）**：

```bash
cp /etc/apt/sources.list.d/ubuntu.sources /etc/apt/sources.list.d/ubuntu.sources.bak
sed -i 's@//archive.ubuntu.com@//mirrors.aliyun.com@g' /etc/apt/sources.list.d/ubuntu.sources
sed -i 's@//security.ubuntu.com@//mirrors.aliyun.com@g' /etc/apt/sources.list.d/ubuntu.sources
```

**想用清华源**：把上面命令里的 `mirrors.aliyun.com` 换成 `mirrors.tuna.tsinghua.edu.cn` 即可。

刷新软件包索引：

```bash
apt update
```

预期输出（最后两行类似即可）：

```text
Get:7 https://mirrors.aliyun.com/ubuntu noble InRelease [267 kB]
Reading package lists... Done
Building dependency tree... Done
All packages are up to date.
```

如果看到 `Hit:`、`Get:` 都是 `mirrors.aliyun.com`，说明换源成功。

### 2.0.2 安装必备小工具

精简安装的系统常常连 `wget`、`tar` 都没有，先装上：

```bash
apt -y install wget curl tar gzip vim bash-completion lsof
```

参数解释：`-y` 表示所有询问都自动回答 yes；后面一串是要装的包名——`wget`/`curl` 下载用、`tar`/`gzip` 解压用、`vim` 编辑器、`lsof` 查端口占用。

验证：

```bash
wget --version | head -1
curl --version | head -1
```

预期输出：

```text
GNU Wget 1.21.4 built on linux-gnu.
curl 8.5.0 (x86_64-pc-linux-gnu) ...
```

### 2.0.3 设置主机名、时区、时间同步

**主机名**（监控服务器就叫 monitor）：

```bash
hostnamectl set-hostname monitor
bash
```

`bash` 是重新加载一次 shell，让提示符立刻显示新主机名。

**时区**（很多默认是 UTC，日志时间会差 8 小时）：

```bash
timedatectl set-timezone Asia/Shanghai
timedatectl
```

预期输出关键两行：

```text
               Local time: Mon 2026-09-28 11:30:00 CST
           Universal time: Mon 2026-09-28 03:30:00 UTC
                 Time zone: Asia/Shanghai (CST, +0800)
```

**时间同步**：监控数据对时间戳很敏感，机器时间不准会导致 Grafana 图错位、告警延迟。

```bash
apt -y install chrony
systemctl enable --now chrony
systemctl is-active chrony
```

预期输出：`active`。查看同步状态：

```bash
chronyc sources | head -5
```

看到以 `^` 开头、带 IP 或域名的时间服务器列表即正常。

### 2.0.4 防火墙规划

监控集群要用到一批端口，先心里有数（**先别急着一刀切关防火墙**，按表放行更安全）：

| 端口 | 组件 | 谁需要访问 |
| --- | --- | --- |
| 9090 | Prometheus | 运维浏览器、Grafana、联邦上级 |
| 9093 | Alertmanager | 运维浏览器、Prometheus |
| 3000 | Grafana | 运维浏览器 |
| 9091 | Pushgateway | 业务脚本、Prometheus |
| 9115 | Blackbox Exporter | Prometheus |
| 9100 | Node Exporter | Prometheus |

Ubuntu 默认防火墙是 `ufw`，默认不启用。如果启用了，按端口放行：

```bash
ufw allow 9090/tcp
ufw allow 9093/tcp
ufw allow 3000/tcp
ufw allow 9091/tcp
ufw allow 9115/tcp
ufw allow 9100/tcp
ufw --force enable
ufw status
```

参数解释：`allow 端口/tcp` 放行 TCP；`--force enable` 跳过确认直接启用。

RHEL/Rocky 系用 `firewalld`，对应命令（以 9090 为例，其余端口照做）：

```bash
firewall-cmd --add-port=9090/tcp --permanent
firewall-cmd --reload
```

::: warning
如果是云服务器（阿里云/腾讯云/AWS 等），除了机器内部防火墙，还要在**云控制台的"安全组"**里放行这些端口，两处都通才能访问。
:::

---

## 2.1 部署 Prometheus

### 2.1.1 五种部署方式对比

| 方式 | 适合场景 | 本手册建议 |
| --- | --- | --- |
| apt/yum 包安装 | 快速体验 | Ubuntu 仓库版本偏旧，生产不推荐 |
| 二进制安装 | 生产环境（虚拟机/物理机） | **重点掌握，生产首选** |
| Docker 启动 | 快速容器化部署 | 容器环境推荐 |
| Docker Compose | 一整套组件编排 | **组件多时最省心，重点掌握** |
| Ansible 批量部署 | 几十上百台机器批量装 | 了解，给链接 |
| Kubernetes | K8s 集群 | 阶段十一专门讲 |

### 2.1.2 方法一：Ubuntu apt 包安装（体验用）

直接安装：

```bash
apt -y install prometheus
systemctl status prometheus --no-pager
```

预期输出关键行：

```text
● prometheus.service - Monitoring system and time series database
     Loaded: loaded (/lib/systemd/system/prometheus.service; enabled)
     Active: active (running) since ...
```

安装包还会顺带装上 Node Exporter：

```bash
systemctl status prometheus-node-exporter --no-pager
ss -ntlp | grep -E '9090|9100'
```

预期输出：

```text
LISTEN 0 4096 *:9090 *:*
LISTEN 0 4096 *:9100 *:*
```

::: warning
Ubuntu 24.04 仓库里的 Prometheus 是 2.45.x，22.04 更是 2.31.x，**都不是当前稳定版 3.x**。生产环境请用下面的二进制或容器方式安装指定版本，不要直接用仓库版本。卸载体验版用：`apt -y purge prometheus prometheus-node-exporter`。
:::

**RHEL/Rocky/CentOS 的 yum 仓库**：系统默认不带 Prometheus 源，需要配置 packagecloud 仓库（服务器在国外）：

```ini
[prometheus]
name=prometheus
baseurl=https://packagecloud.io/prometheus-rpm/release/el/$releasever/$basearch
repo_gpgcheck=1
enabled=1
gpgkey=https://packagecloud.io/prometheus-rpm/release/gpgkey
gpgcheck=1
```

把上面内容保存为 `/etc/yum.repos.d/prometheus.repo`，再执行 `yum makecache && yum -y install prometheus`。由于源在国外，RHEL 系同样更推荐二进制方式。

### 2.1.3 方法二：二进制安装（生产推荐）

**第 1 步：下载二进制包**

操作目录：`/usr/local`；用户：root。

```bash
cd /usr/local
wget https://github.com/prometheus/prometheus/releases/download/v3.15.0/prometheus-3.15.0.linux-amd64.tar.gz
```

参数解释：安装包来自官方 GitHub Releases，文件名中 `3.15.0` 是版本、`linux-amd64` 表示 Linux 64 位系统。

**国内下载加速（GitHub 慢时用）**：在原链接前加 GitHub 代理前缀，例如：

```text
https://ghproxy.net/https://github.com/prometheus/prometheus/releases/download/v3.15.0/prometheus-3.15.0.linux-amd64.tar.gz
```

代理地址可能变动，一个不能用就换另一个（如 `https://gh-proxy.com/`、`https://ghfast.top/`）；也可以在能访问的机器下载后用 scp 拷到服务器。

**第 2 步：解压并建立软链接**

```bash
tar xf prometheus-3.15.0.linux-amd64.tar.gz
ln -s prometheus-3.15.0.linux-amd64 prometheus
cd prometheus
ls -l
```

参数解释：`tar xf 包名` 中 `x` 是解开（extract）、`f` 指定文件；`ln -s 真实目录 软链接名` 建立软链接——以后升级只换软链接指向，路径永远是 `/usr/local/prometheus`。

预期输出：

```text
drwxr-xr-x 2 1001 127 4096 Sep 24 00:00 console_libraries
drwxr-xr-x 2 1001 127 4096 Sep 24 00:00 consoles
-rw-r--r-- 1 1001 127 11357 Sep 24 00:00 LICENSE
-rw-r--r-- 1 1001 127  3773 Sep 24 00:00 NOTICE
-rwxr-xr-x 1 1001 127  ... prometheus
-rw-r--r-- 1 1001 127   934 Sep 24 00:00 prometheus.yml
-rwxr-xr-x 1 1001 127  ... promtool
```

两个可执行文件：`prometheus` 是服务主程序；`promtool` 是配置检查、调试工具。它们是 Go 编译的**静态链接**程序（`ldd prometheus` 会显示"不是动态可执行文件"），不依赖系统库，拷到哪都能跑。

**第 3 步：规范目录结构**

```bash
mkdir -p bin conf data
mv prometheus promtool bin/
mv prometheus.yml conf/
```

目录规划：`bin/` 放程序，`conf/` 放配置，`data/` 放时序数据。

**第 4 步：创建专用运行用户**

```bash
useradd -r -s /usr/sbin/nologin prometheus
chown -R prometheus:prometheus /usr/local/prometheus/
```

参数解释：`useradd -r` 创建系统用户（UID 较小、不可登录）；`-s /usr/sbin/nologin` 禁止该用户登录 Shell——服务程序用独立用户跑，即使被攻破也拿不到 Shell，是安全规范。`chown -R 用户:组 路径` 递归修改属主，让服务用户能读写自己的目录。

**第 5 步：配置 PATH 环境变量（可选，方便敲命令）**

```bash
cat > /etc/profile.d/prometheus.sh <<'EOF'
export PROMETHEUS_HOME=/usr/local/prometheus
export PATH=${PROMETHEUS_HOME}/bin:$PATH
EOF
source /etc/profile.d/prometheus.sh
promtool --version
```

预期输出（类似）：

```text
promtool, version 3.15.0 (branch: HEAD, revision: ...)
  build user:       ...
  build date:       ...
```

**第 6 步：检查自带配置文件**

```bash
grep -Ev '^ *#|^$' /usr/local/prometheus/conf/prometheus.yml
```

`grep -Ev '^ *#|^$'` 表示过滤掉注释行和空行，只看有效配置。预期输出：

```text
global:
  scrape_interval: 15s
  evaluation_interval: 15s
alerting:
  alertmanagers:
    - static_configs:
        - targets:
rule_files:
scrape_configs:
  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]
```

用 promtool 检查语法：

```bash
promtool check config /usr/local/prometheus/conf/prometheus.yml
```

预期输出：

```text
Checking /usr/local/prometheus/conf/prometheus.yml
  SUCCESS: 0 rule files found
```

**第 7 步：创建 systemd 服务文件**

用编辑器创建 `/etc/systemd/system/prometheus.service`（推荐用 vim；不会用 vim 也可以直接用下面的整块写入方式）：

```bash
cat > /etc/systemd/system/prometheus.service <<'EOF'
[Unit]
Description=Prometheus Server
Documentation=https://prometheus.io/docs/introduction/overview/
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=prometheus
Group=prometheus
WorkingDirectory=/usr/local/prometheus/
ExecStart=/usr/local/prometheus/bin/prometheus \
  --config.file=/usr/local/prometheus/conf/prometheus.yml \
  --storage.tsdb.path=/usr/local/prometheus/data \
  --storage.tsdb.retention.time=15d \
  --web.listen-address=0.0.0.0:9090 \
  --web.enable-lifecycle
ExecReload=/bin/kill -HUP $MAINPID
Restart=on-failure
RestartSec=5
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF
```

关键参数逐个解释：

| 参数 | 作用 |
| --- | --- |
| `After=network-online.target` | 等网络就绪后再启动 |
| `User/Group` | 用 prometheus 身份运行 |
| `--config.file` | 指定主配置文件路径 |
| `--storage.tsdb.path` | 时序数据存放目录 |
| `--storage.tsdb.retention.time=15d` | 数据保留 15 天，过期自动删；企业常用 15～30 天 |
| `--web.listen-address=0.0.0.0:9090` | 监听所有网卡的 9090（只写 127.0.0.1 外部访问不到） |
| `--web.enable-lifecycle` | 允许通过 HTTP 接口热加载/关闭，**有被远程关闭的安全风险**；不需要可删掉，改用 `systemctl reload` |
| `ExecReload` | 执行 reload 时给主进程发 HUP 信号 |
| `Restart=on-failure` | 进程异常退出自动拉起 |
| `LimitNOFILE=65535` | 提高文件描述符上限，目标多了必须调 |

::: warning
生产环境两条红线：① 数据目录建议挂独立磁盘/分区，防止监控数据把系统根分区写满；② 安全要求高时不要开 `--web.enable-lifecycle`，热加载改用 `systemctl reload prometheus`。
:::

**第 8 步：启动并设置开机自启**

```bash
systemctl daemon-reload
systemctl enable --now prometheus
ss -lntp | grep 9090
```

`systemctl daemon-reload` 让 systemd 重新读取服务文件；`enable --now` 表示同时设开机自启并立即启动。预期输出：

```text
LISTEN 0 4096 0.0.0.0:9090 0.0.0.0:* users:(("prometheus",pid=1234,fd=10))
```

**第 9 步：验证**

```bash
curl http://localhost:9090/-/healthy
curl http://localhost:9090/-/ready
```

预期输出：

```text
Prometheus Server is Healthy.
Prometheus Server is Ready.
```

浏览器访问（把 IP 换成你的监控服务器地址）：

```text
http://【监控服务器IP】:9090
```

能看到 Prometheus 自带界面即成功。

### 2.1.4 认识 Prometheus 自带界面

顶部四个一级菜单：

| 菜单 | 功能 |
| --- | --- |
| **Alerts** | 查看告警规则与当前告警状态（阶段五用） |
| **Graph** | 默认首页：写 PromQL 表达式、出表格和简单图表 |
| **Status** | 系统状态（见下表） |
| **Help** | 官方帮助链接 |

Status 下拉子菜单：

| 子菜单 | 能看到什么 |
| --- | --- |
| Runtime & Build Information | 版本、Go 版本、主机资源等运行信息 |
| Command-Line Flags | 启动时实际生效的命令行参数 |
| Configuration | 当前加载的完整配置文件内容 |
| Rules | 已加载的记录规则、告警规则 |
| **Targets** | 所有监控目标及其 UP/DOWN 状态（最常用） |
| Service Discovery | 服务发现的过程与结果（阶段六用） |

Graph 页面用法：在输入框选/填一个指标名（如 `scrape_duration_seconds`）→ 点 **Execute** → 下方 Table 标签看数值、Graph 标签看曲线。注意：自带界面的图表刷新后表达式就没了、也不能保存大屏，所以才需要 Grafana。

### 2.1.5 管理 API（自动化常用）

| 接口 | 方法 | 作用 | 是否需要 lifecycle |
| --- | --- | --- | --- |
| `/-/healthy` | GET | 健康检查，始终返回 200 | 否 |
| `/-/ready` | GET | 是否准备好响应查询 | 否 |
| `/-/reload` | POST/PUT | 热加载配置文件 | **是** |
| `/-/quit` | POST/PUT | 关闭服务 | **是** |

热加载配置（开了 lifecycle）：

```bash
curl -X POST http://localhost:9090/-/reload
```

没开 lifecycle 也能用 systemd 热加载（效果相同，更安全）：

```bash
systemctl reload prometheus
```

如果没开 lifecycle 却调用接口，会返回：

```text
Lifecycle API is not enabled.
```

远程关闭（演示，生产勿用）：

```bash
curl -X POST http://localhost:9090/-/quit
```

预期输出：`Requesting termination... Goodbye!`

### 2.1.6 方法三：Docker 方式安装

**第 1 步：安装 Docker（用国内源）**

```bash
apt -y install ca-certificates curl gnupg
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://mirrors.aliyun.com/docker-ce/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.gpg] https://mirrors.aliyun.com/docker-ce/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" > /etc/apt/sources.list.d/docker.list
apt update
apt -y install docker-ce docker-ce-cli containerd.io
systemctl enable --now docker
docker --version
```

参数解释：官方 Docker 源是 `download.docker.com`，换成 `mirrors.aliyun.com/docker-ce` 即可；`$(... VERSION_CODENAME)` 会自动取系统代号（jammy/noble）。

RHEL 系：把 repo 地址换成 `https://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo`，下载后放到 `/etc/yum.repos.d/`，再 `yum -y install docker-ce`。

**第 2 步：配置容器镜像加速**

Docker Hub 在国内拉取常超时，配置加速器：

```bash
mkdir -p /etc/docker
cat > /etc/docker/daemon.json <<'EOF'
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://docker.1panel.live",
    "https://hub.rat.dev"
  ],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "3"
  }
}
EOF
systemctl daemon-reload
systemctl restart docker
docker info | grep -A5 'Registry Mirrors'
```

参数解释：`registry-mirrors` 是 Docker Hub 的镜像加速地址，配多个会依次尝试；`log-opts` 限制容器日志单个 100MB、最多 3 个，防止日志撑爆磁盘（阶段常见坑）。

::: warning
公共加速器地址变动频繁，若某个失效，删掉即可，保留能用的；也可在 DaoCloud、1Panel 等官网查最新地址。拉取私有/国外镜像失败时，优先怀疑加速器问题。
:::

**第 3 步：启动 Prometheus 容器**

最简启动（只用默认配置，适合验证镜像）：

```bash
docker run -d --name prometheus -p 9090:9090 prom/prometheus:v3.15.0
```

参数解释：`-d` 后台运行；`--name` 容器名；`-p 宿主机端口:容器端口` 做端口映射；镜像 tag **必须写明确版本 v3.15.0，不要用 latest**。

生产推荐写法（挂载配置文件 + 数据持久化）。先在宿主机准备目录和配置：

```bash
mkdir -p /data/prometheus /etc/prometheus
docker cp prometheus:/etc/prometheus/prometheus.yml /etc/prometheus/prometheus.yml
docker rm -f prometheus
docker run -d \
  --name prometheus \
  --restart=always \
  -p 9090:9090 \
  -v /etc/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml \
  -v prometheus_data:/prometheus \
  prom/prometheus:v3.15.0 \
  --config.file=/etc/prometheus/prometheus.yml \
  --storage.tsdb.path=/prometheus \
  --storage.tsdb.retention.time=15d
```

参数解释：`--restart=always` 容器退出/开机都自动重启（生产必设）；`-v 文件:文件` 是绑定挂载，把宿主机配置挂进容器；`-v prometheus_data:/prometheus` 是命名卷，数据由 Docker 管理、持久保存；镜像名后面的内容会覆盖默认启动参数。

验证：

```bash
docker ps
curl http://localhost:9090/-/healthy
```

预期输出：容器列表里 prometheus 为 `Up`，健康检查返回 `Prometheus Server is Healthy.`。

### 2.1.7 方法四：Docker Compose 编排

**第 1 步：安装 compose 插件**

```bash
apt -y install docker-compose-plugin
docker compose version
```

预期输出：`Docker Compose version v2.xx.x`。

**第 2 步：编写只含 Prometheus 的编排文件**

创建项目目录：

```bash
mkdir -p /opt/monitoring/prometheus
cd /opt/monitoring
```

把配置文件放好：

```bash
cp /etc/prometheus/prometheus.yml /opt/monitoring/prometheus/prometheus.yml
```

创建 `/opt/monitoring/docker-compose.yml`：

```yaml
services:
  prometheus:
    image: prom/prometheus:v3.15.0
    container_name: prometheus
    restart: always
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=15d'
      - '--web.enable-lifecycle'

volumes:
  prometheus_data:
```

**第 3 步：启动**

```bash
docker compose up -d
docker compose ps
```

参数解释：`up -d` 按编排文件后台创建并启动所有服务；`ps` 查看编排内服务状态。预期输出：prometheus 行 `running`，端口 `0.0.0.0:9090->9090/tcp`。

后续本阶段每加一个组件（Node Exporter、Grafana、Pushgateway），都会往这个 compose 文件里追加，最后形成一套完整编排。

### 2.1.8 方法五：Ansible 批量部署（了解）

机器数量多时，用官方 Ansible 角色批量安装，角色仓库：

```text
https://github.com/prometheus-community/ansible
```

Prometheus 角色说明页：

```text
https://prometheus-community.github.io/ansible/branch/main/prometheus_role.html
```

用法概要：安装 ansible（`apt -y install ansible`）→ 在 playbook 中引用 `prometheus.prometheus.prometheus` 角色并设置 `prometheus_version: "3.15.0"` 等变量 → 对主机清单执行 `ansible-playbook`。初学者先掌握二进制和 Compose，工作中真有批量需求再学 Ansible。

---

## 2.2 主配置文件详解

### 2.2.1 四大核心配置段

文件路径：二进制安装为 `/usr/local/prometheus/conf/prometheus.yml`；容器为挂载的 `/etc/prometheus/prometheus.yml`。

| 配置段 | 作用 |
| --- | --- |
| `global` | 全局默认值：采集间隔、规则评估间隔、外部标签等 |
| `alerting` | Alertmanager 的地址与连接方式 |
| `rule_files` | 规则文件列表（记录规则、告警规则，阶段五用） |
| `scrape_configs` | **最核心**：定义一个个 job 以及如何抓取 |

`global` 段两个关键值：

```yaml
global:
  scrape_interval: 15s       # 全局抓取间隔，默认 1 分钟
  evaluation_interval: 15s   # 规则评估间隔，默认 1 分钟
  # scrape_timeout 默认 10s，且不能超过 scrape_interval
```

### 2.2.2 其他可选配置（眼熟即可，用到再查）

- 通用扩展：`tls_config`、`static_config`、`relabel_configs`、`metric_relabel_configs`、`alert_relabel_configs`、`alertmanager_config`、`remote_write`、`remote_read`；
- 服务发现集成：`file_sd_configs`、`dns_sd_configs`、`consul_sd_configs`、`kubernetes_sd_configs`、`ec2_sd_configs`、`openstack_sd_configs`、`azure_sd_configs`、`gce_sd_configs` 等。

### 2.2.3 scrape_configs 写法

一个 job 的标准写法：

```yaml
scrape_configs:
  - job_name: '示例任务'
    metrics_path: /metrics      # 抓取路径，默认就是 /metrics，可省略
    scheme: http                # 协议 http/https，默认 http，可省略
    static_configs:
      - targets: ['10.0.0.11:9100', '10.0.0.12:9100']
        labels:
          env: 'prod'
          idc: 'chengdu'
```

参数解释：

| 参数 | 作用 |
| --- | --- |
| `job_name` | 任务名，会成为每条序列的 `job` 标签 |
| `metrics_path` | 抓取的网页路径 |
| `scheme` | 用 http 还是 https |
| `static_configs.targets` | 静态目标列表，每个 `IP:端口` 是一个 instance |
| `static_configs.labels` | 给该组所有目标额外附加的自定义标签 |

改完任何配置，固定两步：

```bash
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus
```

::: warning
YAML 格式两条铁律：① **缩进只能用空格、不能用 Tab**，同级对齐（一般缩进 2 个空格）；② 冒号后面要有空格。缩进错了会报 `yaml: line X: did not find expected key`。改完一定先 promtool 检查再 reload。
:::

---
## 2.3 Node Exporter：采集主机指标

Node Exporter 是部署在**每一台被监控机器**上的小程序，专门采集 CPU、内存、磁盘、网络、文件系统等主机层面的指标，监听 9100 端口。

- **类比**：它像给每台机器配的"体检员"，Prometheus 这位"医生"定期来找它要体检报告。
- **为什么需要它**：Prometheus 只会说 HTTP，读不懂内核数据；Node Exporter 负责读 `/proc`、`/sys` 并翻译成 Prometheus 格式。
- **不装会怎样**：不装它，Prometheus 拿不到任何主机指标，Targets 里该目标 DOWN。

以下操作在**每台被监控主机**（web01、app01、db01……）上执行，用户为 root。

### 2.3.1 二进制安装

**第 1 步：下载解压**

```bash
cd /usr/local
wget https://github.com/prometheus/node_exporter/releases/download/v1.12.1/node_exporter-1.12.1.linux-amd64.tar.gz
tar xf node_exporter-1.12.1.linux-amd64.tar.gz
ln -s node_exporter-1.12.1.linux-amd64 node_exporter
cd node_exporter
mkdir -p bin
mv node_exporter bin/
```

备选（GitHub）：

```text
https://github.com/prometheus/node_exporter/releases/download/v1.12.1/node_exporter-1.12.1.linux-amd64.tar.gz
```

**第 2 步：建用户、授权**

```bash
id prometheus &>/dev/null || useradd -r -s /usr/sbin/nologin prometheus
chown -R prometheus:prometheus /usr/local/node_exporter/
```

`id prometheus &>/dev/null || ...` 的意思是：先查 prometheus 用户是否存在，不存在（`||` 左边失败）才执行后面的创建命令，避免重复建用户报错。

**第 3 步：认识采集器 collector**

Node Exporter 靠一个个 collector 采集不同类数据。启用用 `--collector.<名字>`，禁用用 `--no-collector.<名字>`。查看全部：

```bash
/usr/local/node_exporter/bin/node_exporter --help | grep -E 'collector\.(cpu|meminfo|diskstats|filesystem|netdev)' | head -10
```

默认已启用的主要采集器：

| collector | 采集内容 |
| --- | --- |
| cpu | CPU 使用时间 |
| meminfo | 内存 |
| diskstats | 磁盘 IO |
| filesystem | 文件系统容量 |
| netdev / netclass / netstat | 网卡流量、网络协议栈 |
| loadavg | 系统负载 |
| time / uname / stat | 时间、内核版本等 |
| pressure | PSI 资源压力（CPU/内存/IO 等待） |

**第 4 步：创建服务文件**

```bash
cat > /etc/systemd/system/node_exporter.service <<'EOF'
[Unit]
Description=Prometheus Node Exporter
After=network-online.target

[Service]
Type=simple
User=prometheus
Group=prometheus
ExecStart=/usr/local/node_exporter/bin/node_exporter \
  --web.listen-address=0.0.0.0:9100 \
  --collector.filesystem.mount-points-exclude='^/(dev|proc|run/credentials/.+|sys|var/lib/docker/.+)($|/)'
ExecReload=/bin/kill -HUP $MAINPID
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

参数解释：`--collector.filesystem.mount-points-exclude` 用正则排除虚拟/容器挂载点，避免把 `/proc`、容器内部目录等无意义的文件系统算进磁盘指标。

::: warning
不要随意加 `--no-collector.uname`：禁用 uname 采集器会导致 Grafana 主机看板无法显示该主机的内核、机器信息。
:::

**第 5 步：启动、验证**

```bash
systemctl daemon-reload
systemctl enable --now node_exporter
systemctl is-active node_exporter
ss -lntp | grep 9100
```

预期输出：

```text
active
LISTEN 0 4096 *:9100 *:* users:(("node_exporter",pid=2195,fd=3))
```

本机抓一把指标验证：

```bash
curl -s http://localhost:9100/metrics | grep -E 'node_cpu_seconds_total|node_memory_MemTotal_bytes' | head -5
```

预期输出（数值不同正常）：

```text
# HELP node_cpu_seconds_total Seconds the CPUs spent in each mode.
# TYPE node_cpu_seconds_total counter
node_cpu_seconds_total{cpu="0",mode="idle"} 12345.67
# HELP node_memory_MemTotal_bytes Memory information field MemTotal_bytes.
node_memory_MemTotal_bytes 4.14e+09
```

浏览器访问 `http://【被监控主机IP】:9100/metrics` 能看到整页指标即成功。记得放通 9100 端口（ufw/防火墙/安全组）。

### 2.3.2 容器方式安装 Node Exporter

官方推荐的容器启动（用主机网络和 PID 命名空间，才能读到宿主机真实数据）：

```bash
docker run -d \
  --name node_exporter \
  --restart=always \
  --net="host" \
  --pid="host" \
  -v "/:/host:ro,rslave" \
  prom/node-exporter:v1.12.1 \
  --path.rootfs=/host
```

参数解释：`--net="host"` 直接用宿主机网络（9100 直接在宿主机监听）；`--pid="host"` 共享宿主机进程视图；`-v "/:/host:ro,rslave"` 把宿主机根目录只读挂进容器，`rslave` 保证后续新挂载能同步看到。

Docker Compose 写法（桥接网络版）：

```yaml
services:
  node-exporter:
    image: prom/node-exporter:v1.12.1
    container_name: node-exporter
    restart: always
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--path.rootfs=/host'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
```

::: tip
YAML 里写 `$` 要写成 `$$`（Compose 会把 `$$` 转义成一个 `$`），所以正则里的 `($|/)` 在 compose 文件里写成 `($$|/)`。
:::

### 2.3.3 Kubernetes 中以 DaemonSet 安装

DaemonSet（守护进程集）能在每个节点上自动跑一个 Pod，正适合 Node Exporter。完整 K8s 概念阶段十一细讲，这里先给出可用清单。

`node-exporter-ds.yaml`：

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: prometheus-node-exporter
  namespace: monitoring
  labels:
    app: prometheus
    component: node-exporter
spec:
  selector:
    matchLabels:
      app: prometheus
      component: node-exporter
  template:
    metadata:
      labels:
        app: prometheus
        component: node-exporter
    spec:
      hostNetwork: true
      hostPID: true
      tolerations:
        - effect: NoSchedule
          key: node-role.kubernetes.io/control-plane
          operator: Exists
      volumes:
        - name: proc
          hostPath:
            path: /proc
        - name: sys
          hostPath:
            path: /sys
        - name: rootfs
          hostPath:
            path: /
      containers:
        - image: prom/node-exporter:v1.12.1
          name: prometheus-node-exporter
          args:
            - --path.procfs=/host/proc
            - --path.sysfs=/host/sys
            - --path.rootfs=/host
          ports:
            - name: metrics
              containerPort: 9100
              hostPort: 9100
          volumeMounts:
            - mountPath: /host/proc
              name: proc
            - mountPath: /host/sys
              name: sys
            - mountPath: /host
              name: rootfs
          livenessProbe:
            tcpSocket:
              port: 9100
            initialDelaySeconds: 5
          readinessProbe:
            httpGet:
              path: /metrics
              port: 9100
            initialDelaySeconds: 5
```

参数解释：`tolerations` 是"容忍"——默认 Pod 不调度到控制平面节点，这里声明容忍该污点，让 Node Exporter 也能在控制节点采集；`livenessProbe`/`readinessProbe` 是存活/就绪健康检查（生产必配）。

再配一个无头 Service 便于 Prometheus 发现：

```yaml
apiVersion: v1
kind: Service
metadata:
  name: prometheus-node-exporter
  namespace: monitoring
  labels:
    app: prometheus
    component: node-exporter
spec:
  clusterIP: None
  selector:
    app: prometheus
    component: node-exporter
  ports:
    - name: metrics
      port: 9100
      targetPort: 9100
      protocol: TCP
```

应用：

```bash
kubectl create namespace monitoring
kubectl apply -f node-exporter-ds.yaml
kubectl -n monitoring get pod -o wide
```

预期输出：每个节点一个 `prometheus-node-exporter` Pod，状态 `Running 1/1`。

### 2.3.4 Node Exporter 常用指标速览

| 指标前缀 | 含义 |
| --- | --- |
| `node_boot_time_seconds` | 系统启动时刻（1970 年以来秒数） |
| `node_cpu_seconds_total` | CPU 各模式（idle/system/user/iowait 等）累计秒数 |
| `node_disk_*` | 磁盘 IO（读写次数、字节、耗时） |
| `node_filesystem_*` | 文件系统总量、可用量 |
| `node_load1 / load5 / load15` | 1/5/15 分钟平均负载 |
| `node_memory_*` | 内存总量、可用、缓存、swap |
| `node_network_*` | 网卡收发字节、包数、错误、丢包 |
| `node_time_seconds` | 当前系统时间 |
| `go_*` / `process_*` | exporter 自身 Go 运行时、进程指标 |

---

## 2.4 Prometheus 采集 Node Exporter

回到**监控服务器 monitor**，把三台业务主机加进 Prometheus。

**第 1 步：编辑配置**

用 vim 打开 `/usr/local/prometheus/conf/prometheus.yml`，在 `scrape_configs` 段已有 job 之后追加：

```yaml
  - job_name: 'node_exporter'
    metrics_path: /metrics
    scheme: http
    static_configs:
      - targets:
          - '【Web服务器IP】:9100'
          - '【应用服务器IP】:9100'
          - '【数据库服务器IP】:9100'
        labels:
          env: 'prod'
```

完整有效配置检查：

```bash
grep -Ev '^ *#|^$' /usr/local/prometheus/conf/prometheus.yml
```

**第 2 步：检查语法、生效**

```bash
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus
```

预期输出：

```text
Checking /usr/local/prometheus/conf/prometheus.yml
  SUCCESS: /usr/local/prometheus/conf/prometheus.yml is valid prometheus config file syntax
```

**第 3 步：在界面验证**

浏览器打开：

```text
http://【监控服务器IP】:9090/targets
```

预期结果：出现 `node_exporter` 分组，下面三个 Endpoint，State 全为 **UP**。鼠标放到 Labels 上能看到 `__meta`/`__address__` 等内部标签（`__` 开头是系统保留标签）；点 Endpoint 链接可直接跳到该主机的 metrics 页面。

如果是 DOWN，点 Endpoint 前的报错提示，按本阶段末尾"常见坑"排查（90% 是端口没放通或服务没起）。

---

## 2.5 Grafana：把数据画成大屏

Grafana 是开源的可视化套件，支持 Prometheus、MySQL、ES 等几十种数据源，提供海量现成看板模板，默认监听 3000 端口。

- **类比**：Prometheus 是埋头记账的会计，Grafana 是把账本画成图表大屏的"美工"。
- **为什么需要它**：Prometheus 自带界面不能保存图表、不好看；Grafana 能做仪表盘、大屏、权限、共享。
- **不装会怎样**：只能在 Prometheus 里临时查，没有可长期使用的监控大屏。

### 2.5.1 安装 Grafana

在**监控服务器 monitor** 上执行，用户 root。

**方式一：官方包安装（推荐，地址国内可访问）**

```bash
cd /usr/local/src
wget https://dl.grafana.com/oss/release/grafana_13.2.2_amd64.deb
apt -y install ./grafana_13.2.2_amd64.deb
```

参数解释：`install ./文件名.deb` 会自动解决依赖（比 `dpkg -i` 更省心，本地文件路径前的 `./` 不能省）。这是开源版（OSS）安装包。

**备选：清华镜像站**（官方地址慢时用，包名带构建时间戳）：

```bash
wget https://mirrors.tuna.tsinghua.edu.cn/grafana/apt/pool/main/g/grafana/grafana_13.2.2_34846740809_linux_amd64.deb
apt -y install ./grafana_13.2.2_34846740809_linux_amd64.deb
```

启动并设开机自启：

```bash
systemctl daemon-reload
systemctl enable --now grafana-server
systemctl is-active grafana-server
ss -lntp | grep 3000
```

预期输出：

```text
active
LISTEN 0 4096 *:3000 *:* users:(("grafana-server",pid=35383,fd=8))
```

**RHEL 系**：下载 `.rpm` 包（`https://dl.grafana.com/oss/release/grafana-13.2.2-1.x86_64.rpm`），用 `yum -y localinstall 包名` 安装，服务名同样是 `grafana-server`。

**方式二：Docker 安装**

```bash
docker run -d \
  --name grafana \
  --restart=always \
  -p 3000:3000 \
  -v grafana_data:/var/lib/grafana \
  grafana/grafana:13.2.2
```

参数解释：Grafana 数据（数据源、看板、用户）存在容器内 `/var/lib/grafana`，用命名卷持久化。

### 2.5.2 首次登录

浏览器访问：

```text
http://【监控服务器IP】:3000
```

第 1 步：输入初始用户名 `admin`、初始密码 `admin`，点 **Log in**；
第 2 步：进入修改密码页，输入新密码并确认（学习图省事也可继续用 admin，点 Submit；**生产必须改成强密码**）；
第 3 步：进入 Grafana 首页。

### 2.5.3 添加 Prometheus 数据源

第 1 步：点首页的 **Add your first data source**（或左侧菜单 Connections / Data sources → Add data source）；
第 2 步：在数据源列表里选 **Prometheus**；
第 3 步：在 Settings 页填写：

| 配置项 | 填什么 |
| --- | --- |
| Prometheus server URL | `http://【监控服务器IP】:9090`（Grafana 和 Prometheus 同机也可填 `http://localhost:9090`，但容器版 Grafana 的 localhost 指容器自身，要用宿主机 IP） |
| 其他项 | 全部保持默认 |

第 4 步：拉到最下面点 **Save & test**；
预期结果：出现绿色提示 `Successfully queried the Prometheus API.`。如果报 `Error reading Prometheus`，检查 URL、Prometheus 是否在跑、端口是否放通。

### 2.5.4 导入主机看板模板

Grafana 社区有大量现成模板，模板用数字 ID 标识，模板市场地址：

```text
https://grafana.com/grafana/dashboards/
```

第 1 步：左侧菜单 **Dashboards → New → Import**；
第 2 步：在 "Import via grafana.com" 输入框填模板 ID，点 **Load**；
第 3 步：选择数据源为刚才添加的 Prometheus，点 **Import**。

推荐模板（都可直接导入）：

| 模板 ID | 说明 |
| --- | --- |
| **1860** | Node Exporter 经典主机看板（英文，最常用） |
| **8919** | Node Exporter 中文主机看板 |
| 11074 | Node Exporter 精简看板 |
| 13978 | Node Exporter 现代看板 |

预期结果：导入后立刻看到 CPU、内存、磁盘、网络的实时图表。

::: warning
导入看板时注意三点：① 模板 ID 要和 exporter 版本匹配，版本差太多会有面板 `No data`；② 一定要选对 Prometheus 数据源；③ Grafana 时间和服务器时间误差超过几秒也可能不显示数据，确保时间同步已配置。
:::

### 2.5.5 把 Grafana 自身纳入监控

Grafana 内置了 `/metrics` 指标接口。在 Prometheus 配置里追加一个 job：

```yaml
  - job_name: 'grafana'
    static_configs:
      - targets: ['【监控服务器IP】:3000']
```

检查生效：

```bash
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus
```

在 Grafana 添加数据源时的 **Dashboards** 标签页可导入内置的 Grafana 指标看板（Grafana metrics），即可查看 Grafana 自身的请求量、耗时、在线用户等状态。

---

## 2.6 监控 Zookeeper（内置指标）

有些软件自带 Prometheus 指标功能（称为内置仪表 Instrumentation），Zookeeper 从 3.6 起内置了 Prometheus Metrics Provider，不用额外装 exporter。

**第 1 步：开启内置 Prometheus 指标**

配置文件路径：`/usr/local/zookeeper/conf/zoo.cfg`（以实际安装路径为准），在文件末尾加入（默认配置里有这几行的注释，取消注释即可）：

```properties
metricsProvider.className=org.apache.zookeeper.metrics.prometheus.PrometheusMetricsProvider
metricsProvider.httpHost=0.0.0.0
metricsProvider.httpPort=7000
metricsProvider.exportJvmInfo=true
```

参数解释：`httpHost=0.0.0.0` 监听所有网卡；`httpPort=7000` 指标端口；`exportJvmInfo=true` 同时输出 JVM 指标。

重启：

```bash
systemctl restart zookeeper
ss -lntp | grep 7000
curl -s http://localhost:7000/metrics | head -5
```

**第 2 步：Prometheus 加 job**

```yaml
  - job_name: 'zookeeper'
    static_configs:
      - targets: ['【Zookeeper服务器IP】:7000']
```

```bash
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus
```

**第 3 步：Grafana 导入看板**

模板市场搜索 zookeeper，导入 ID **10465**（导入步骤同 2.5.4，注意选对数据源/集群名），即可看到 Zookeeper 监控图。

---
## 2.7 Pushgateway：采集短任务自定义指标

Pushgateway 是一个"指标暂存柜"：短生命周期的脚本/任务在退出前把指标**推**给它，Prometheus 再从它那里**拉**。

- **类比**：像快递柜——你（短任务）下班早，怕快递员（Prometheus）上门没人，就把包裹先放进快递柜，快递员按柜子编号统一取。
- **为什么需要它**：批处理、定时任务可能在 Prometheus 两次抓取之间就结束了，Pull 模式抓不到。
- **不学会卡在哪**：企业里"每日报表脚本跑没跑成功""数据同步任务处理了多少条"这类需求，没有它做不了。

数据流向：

![Pushgateway 数据流向](/guide/diagrams/pushgateway-flow.svg)

### 2.7.1 适用场景与缺点

**适用场景**：

1. 批处理/定时任务：每日报表、数据同步、定时清理脚本；
2. 极短生命周期任务：CI/CD 临时容器、Serverless 函数；
3. 无法暴露 HTTP 端点的隔离环境；
4. 老旧/闭源应用，用外部脚本取数后推送；
5. 作为多个任务指标的统一聚合入口。

**缺点（生产须知）**：

- Pushgateway 是单点，挂了则所有推送数据丢失（可部署多实例）；
- **失去 up 自动存活监控**：推送方机器宕机，Pushgateway 仍保留旧值，不会自动变 0；
- 指标会一直保留到被覆盖或手动删除，容易产生过期数据；
- 它不做数据校验，脚本采错了也照单全收。

::: warning
再次强调：**主机指标绝不用 Pushgateway**，只用 Node Exporter；Pushgateway 只接收短任务、批处理指标。
:::

### 2.7.2 二进制安装 Pushgateway

在**监控服务器 monitor** 上执行，用户 root。

**第 1 步：下载解压**

```bash
cd /usr/local
wget https://github.com/prometheus/pushgateway/releases/download/v1.11.3/pushgateway-1.11.3.linux-amd64.tar.gz
tar xf pushgateway-1.11.3.linux-amd64.tar.gz
ln -s pushgateway-1.11.3.linux-amd64 pushgateway
cd pushgateway
mkdir -p bin
mv pushgateway bin/
chown -R prometheus:prometheus /usr/local/pushgateway/
```

备选（GitHub）：

```text
https://github.com/prometheus/pushgateway/releases/download/v1.11.3/pushgateway-1.11.3.linux-amd64.tar.gz
```

**第 2 步：创建服务文件（含持久化）**

```bash
cat > /etc/systemd/system/pushgateway.service <<'EOF'
[Unit]
Description=Prometheus Pushgateway
After=network-online.target

[Service]
Type=simple
User=prometheus
Group=prometheus
ExecStart=/usr/local/pushgateway/bin/pushgateway \
  --web.listen-address=0.0.0.0:9091 \
  --persistence.file=/usr/local/pushgateway/data/persistence \
  --persistence.interval=5m
ExecReload=/bin/kill -HUP $MAINPID
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
mkdir -p /usr/local/pushgateway/data
chown -R prometheus:prometheus /usr/local/pushgateway/data
```

参数解释：`--persistence.file` 指定持久化文件，重启后推送的指标不丢（留空则只存内存）；`--persistence.interval=5m` 至少每 5 分钟写一次盘。

**第 3 步：启动、验证**

```bash
systemctl daemon-reload
systemctl enable --now pushgateway
systemctl is-active pushgateway
ss -lntp | grep 9091
```

预期输出：

```text
active
LISTEN 0 4096 *:9091 *:* users:(("pushgateway",pid=3001,fd=7))
```

浏览器访问 `http://【监控服务器IP】:9091` 能看到 Pushgateway 页面（此时还没有指标）。

Docker 安装（备选）：

```bash
docker run -d --name pushgateway --restart=always -p 9091:9091 prom/pushgateway:v1.11.3
```

### 2.7.3 配置 Prometheus 采集 Pushgateway

在 Prometheus 配置中追加：

```yaml
  - job_name: 'pushgateway'
    honor_labels: true
    scrape_interval: 10s
    static_configs:
      - targets: ['【监控服务器IP】:9091']
```

参数解释：**`honor_labels: true` 很关键**——推送方已经在数据里带了 `job`、`instance` 标签，设为 true 时 Prometheus 尊重并保留这些原始标签；设为 false（默认）时，Prometheus 会把原始标签改名为 `exported_job`、`exported_instance`，再用自己的 job/instance 覆盖。采集 Pushgateway 一般设 true。

检查生效：

```bash
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus
```

也支持文件服务发现写法（阶段六细讲）：

```yaml
  - job_name: pushgateway
    honor_labels: true
    file_sd_configs:
      - files:
          - targets/pushgateway/*.json
        refresh_interval: 5m
```

对应目标文件 `/usr/local/prometheus/conf/targets/pushgateway/test.json`：

```json
[
  {
    "targets": ["【监控服务器IP】:9091"]
  }
]
```

### 2.7.4 客户端推送数据

**推送 URL 格式**：

```text
http://【Pushgateway地址】:9091/metrics/job/<job名>/[<标签名>/<标签值>/]...
```

URL 路径里的 `job/<job名>` 必填；后面可以跟任意组标签（如 `instance/<实例名>`），它们会成为指标的标签。

**示例 1：推送单个指标**

在任意一台业务机器上执行（普通用户即可，能联网到 Pushgateway 就行）：

```bash
echo "some_metric 3.14" | curl --data-binary @- http://【监控服务器IP】:9091/metrics/job/some_job
```

参数解释：`echo "指标名 值"` 生成一行 Prometheus 文本；`|` 管道把它交给 curl；`--data-binary @-` 表示把标准输入（`@-`）原样作为请求体发送。没提供类型时该指标为 untyped。

**示例 2：推送带类型、标签的多条指标**

```bash
cat <<'EOF' | curl --data-binary @- http://【监控服务器IP】:9091/metrics/job/some_job/instance/some_instance
# TYPE some_metric counter
some_metric{label="val1"} 42
# TYPE another_metric gauge
# HELP another_metric Just an example.
another_metric 2398.283
EOF
```

参数解释：`cat <<'EOF' ... EOF` 是一次性生成多行文本（EOF 加引号可避免内部符号被转义）；`# TYPE` 声明类型、`# HELP` 写说明，虽可省但建议写。

**示例 3：用主机 IP 作为 instance 推送**

```bash
echo "age 18" | curl --data-binary @- http://【监控服务器IP】:9091/metrics/job/pushgateway/instance/$(hostname -I | awk '{print $1}')
```

参数解释：`$(命令)` 会先执行里面的命令并替换为结果；`hostname -I` 取本机所有 IP，`awk '{print $1}'` 取第一个。

**删除指标**：

```bash
# 删除某 job 下某 instance 的全部指标
curl -X DELETE http://【监控服务器IP】:9091/metrics/job/some_job/instance/some_instance

# 删除某 job 下全部指标（注意：不含显式指定 instance 的分组）
curl -X DELETE http://【监控服务器IP】:9091/metrics/job/some_job
```

也可以在 Pushgateway 网页上点 **Delete Group** 删除。清空所有指标需要启动时加 `--web.enable-admin-api`，再调用：

```bash
curl -X PUT http://【监控服务器IP】:9091/api/v1/admin/wipe
```

### 2.7.5 通用推送脚本与定时执行

下面脚本把"当前登录用户数"作为指标周期推送，可按需改成任意指标。

创建脚本 `/usr/local/bin/pushgateway_metric.sh`：

```bash
cat > /usr/local/bin/pushgateway_metric.sh <<'EOF'
#!/bin/bash
METRIC_NAME=login_number
METRIC_VALUE_CMD="who | wc -l"
METRIC_TYPE=gauge
METRIC_HELP="login user number"

PUSHGATEWAY_HOST=【监控服务器IP】:9091
EXPORTED_JOB=pushgateway_job
INSTANCE=$(hostname -I | awk '{print $1}')
SLEEP_TIME=10

push_metric() {
  while true; do
    VALUE=$(eval "$METRIC_VALUE_CMD")
    cat <<INNER | curl --data-binary @- http://${PUSHGATEWAY_HOST}/metrics/job/${EXPORTED_JOB}/instance/${INSTANCE}
# HELP ${METRIC_NAME} ${METRIC_HELP}
# TYPE ${METRIC_NAME} ${METRIC_TYPE}
${METRIC_NAME} ${VALUE}
INNER
    sleep $SLEEP_TIME
  done
}

push_metric
EOF
chmod +x /usr/local/bin/pushgateway_metric.sh
bash /usr/local/bin/pushgateway_metric.sh
```

参数解释：`chmod +x` 加可执行权限；脚本里 while 循环每 10 秒推一次；`eval "$METRIC_VALUE_CMD"` 执行取数命令。按 `Ctrl+C` 停止。

生产中更推荐**让任务自己在结束时推一次**，并配合计划任务。例如每日凌晨统计脚本执行完后推送结果；或用 crontab 周期推送，编辑计划任务：

```bash
crontab -e
```

加入一行（每 5 分钟推一次登录用户数）：

```cron
*/5 * * * * echo "login_number $(who | wc -l)" | curl --data-binary @- http://【监控服务器IP】:9091/metrics/job/login_check/instance/$(hostname -I | awk '{print $1}')
```

### 2.7.6 验证数据

第 1 步：浏览器打开 Pushgateway 页面 `http://【监控服务器IP】:9091`，能看到推送的指标分组和值；
第 2 步：Prometheus 侧 `http://【监控服务器IP】:9090/targets` 中 pushgateway 为 UP；
第 3 步：在 Prometheus Graph 或 Grafana 里查询 `some_metric`、`login_number` 能看到值，即整条链路打通。

---

## 本阶段命令速查表

```bash
# === 系统初始化（root）===
apt update && apt -y install wget curl tar vim lsof chrony
timedatectl set-timezone Asia/Shanghai
systemctl enable --now chrony

# === Prometheus 二进制 ===
cd /usr/local
wget https://github.com/prometheus/prometheus/releases/download/v3.15.0/prometheus-3.15.0.linux-amd64.tar.gz
tar xf prometheus-3.15.0.linux-amd64.tar.gz
ln -s prometheus-3.15.0.linux-amd64 prometheus
cd prometheus && mkdir -p bin conf data
mv prometheus promtool bin/ && mv prometheus.yml conf/
useradd -r -s /usr/sbin/nologin prometheus
chown -R prometheus:prometheus /usr/local/prometheus/
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl daemon-reload && systemctl enable --now prometheus

# === Node Exporter（每台被监控机）===
cd /usr/local
wget https://github.com/prometheus/node_exporter/releases/download/v1.12.1/node_exporter-1.12.1.linux-amd64.tar.gz
tar xf node_exporter-1.12.1.linux-amd64.tar.gz
ln -s node_exporter-1.12.1.linux-amd64 node_exporter
# 服务文件见 2.3，然后：
systemctl daemon-reload && systemctl enable --now node_exporter

# === Grafana ===
cd /usr/local/src
wget https://dl.grafana.com/oss/release/grafana_13.2.2_amd64.deb
apt -y install ./grafana_13.2.2_amd64.deb
systemctl enable --now grafana-server

# === Pushgateway ===
cd /usr/local
wget https://github.com/prometheus/pushgateway/releases/download/v1.11.3/pushgateway-1.11.3.linux-amd64.tar.gz
tar xf pushgateway-1.11.3.linux-amd64.tar.gz
ln -s pushgateway-1.11.3.linux-amd64 pushgateway
# 服务文件见 2.7，然后：
systemctl daemon-reload && systemctl enable --now pushgateway

# === 每次改配置固定两步 ===
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus

# === 推送 / 删除指标 ===
echo "some_metric 3.14" | curl --data-binary @- http://【监控服务器IP】:9091/metrics/job/some_job
curl -X DELETE http://【监控服务器IP】:9091/metrics/job/some_job
```

---

## 本阶段常见坑与解决

**坑 1：命令不存在（command not found）**

- 新手做法：照着敲 `wget`、`tar`、`ss`，系统提示找不到。
- 报错原样：`bash: wget: command not found`。
- 根本原因：最小化安装的镜像不带这些工具。
- 解决：

```bash
apt -y install wget curl tar iproute2
```

RHEL 系：`yum -y install wget curl tar iproute`。
- 预防：初始化时先执行 2.0.2 的工具安装。

**坑 2：权限不足（Permission denied）**

- 报错原样：`mkdir: cannot create directory '/usr/local/xxx': Permission denied`；或服务写数据时报 `open data/xxx: permission denied`。
- 根本原因：普通用户无权写系统目录；或服务用户对数据目录没有属主权限。
- 解决：系统级操作切 root（`sudo -i`）；目录授权：

```bash
chown -R prometheus:prometheus /usr/local/prometheus/
```

- 预防：先想清楚"这条命令该用谁执行"，服务目录安装后立即 chown。

**坑 3：端口被占用（Address already in use）**

- 报错原样：`listen tcp 0.0.0.0:9090: bind: address already in use`。
- 根本原因：已有进程占用该端口（常见于 apt 装过又装二进制、容器和宿主重复）。
- 解决：

```bash
ss -lntp | grep 9090
# 查到 PID 后停掉旧进程：
systemctl stop prometheus
# 或停掉旧容器：
docker rm -f prometheus
```

- 预防：同一台机器上一种方式只装一套；先查端口再启动。

**坑 4：YAML 配置语法错误**

- 报错原样：`yaml: unmarshal errors: cannot unmarshal ... ` 或 `parsing YAML file prometheus.yml: yaml: line 12: did not find expected '-' indicator`。
- 根本原因：Tab 缩进、缩进层级不对、冒号后没空格。
- 解决：用 `promtool check config 路径` 定位行号，改空格缩进（推荐 2 空格），通过后再 reload。
- 预防：编辑器开启"显示空白字符"，只复制手册里完整配置块。

**坑 5：空目录挂载覆盖了容器内默认配置**

- 新手做法：`-v /opt/prometheus:/etc/prometheus` 挂载一个空目录。
- 现象：容器启动即退出，日志报 `Error: unable to load config file: open /etc/prometheus/prometheus.yml: no such file`。
- 根本原因：绑定挂载会用宿主机目录**整体覆盖**容器内目录，空目录把默认配置盖没了。
- 解决：先在宿主机目录放好 `prometheus.yml`，或先 `docker cp` 拷出默认配置；只挂单个文件也行：`-v /etc/prometheus.yml:/etc/prometheus/prometheus.yml`。
- 预防：挂载前确认宿主机源路径里有内容。

**坑 6：容器启动后立刻退出（Exited）**

- 报错/现象：`docker ps -a` 显示 Exited (1)，`docker logs prometheus` 有配置/路径错误。
- 根本原因：配置文件不存在、参数写错、数据目录权限不对。
- 解决：`docker logs --tail 50 prometheus` 看具体原因，按对应坑修复后 `docker rm -f prometheus` 重新 run。
- 预防：启动命令里加 `--restart=always`，但**更要先排掉根因**，否则会反复重启。

**坑 7：国内源/加速器配错**

- 报错原样：`Cannot initiate the connection to mirrors.xxx:80 ... Connection timed out`；拉镜像 `Error response from daemon: Get ...: net/http: TLS handshake timeout`。
- 根本原因：源地址写错、加速器失效。
- 解决：apt 源用手册里的阿里云/清华地址；daemon.json 里删掉失效加速器、保留可用的，`systemctl restart docker`。
- 预防：安装包优先从 GitHub Releases 下载（慢则加 ghproxy 代理前缀）；容器加速器多配两个做备份。

**坑 8：安全组/防火墙没放端口**

- 报错原样：浏览器 `10.0.0.10 拒绝了连接请求`；本地 curl 正常、外部不行。
- 根本原因：ufw/firewalld/云安全组未放行。
- 解决：

```bash
ufw allow 9090/tcp        # Ubuntu
firewall-cmd --add-port=9090/tcp --permanent && firewall-cmd --reload   # RHEL
```

云服务器再到控制台安全组加规则。
- 预防：按 2.0.4 端口表一次性放齐。

**坑 9：服务只监听 127.0.0.1**

- 报错/现象：`ss -lntp` 显示 `127.0.0.1:9090`，外部访问被拒。
- 根本原因：监听地址绑了回环地址，只接受本机连接。
- 解决：启动参数显式加 `--web.listen-address=0.0.0.0:9090`，重启服务。
- 预防：所有需要外部访问的服务都监听 `0.0.0.0`。

**坑 10：日志撑爆磁盘**

- 现象：磁盘 100%、服务异常；容器 json 日志无限增长。
- 根本原因：没配日志轮转。
- 解决：daemon.json 配置 `log-opts`（见 2.1.6）；已撑大先清：

```bash
sh -c 'truncate -s 0 /var/lib/docker/containers/*/*-json.log'
```

- 预防：部署 Docker 时就配好单文件大小与份数。

**坑 11：时间不同步导致图不显示/告警延迟**

- 现象：Grafana 面板 No data，机器时间与实际差几分钟以上。
- 解决：

```bash
timedatectl set-timezone Asia/Shanghai
systemctl enable --now chrony
```

- 预防：把时间同步纳入主机初始化必做项。

**坑 12：中文乱码**

- 现象：页面、输出中文显示为问号或方块。
- 根本原因：未设置 UTF-8 字符集。
- 解决：

```bash
apt -y install locales
locale-gen en_US.UTF-8 zh_CN.UTF-8
export LANG=en_US.UTF-8
```

- 预防：系统初始化时安装 UTF-8 locale。

**坑 13：honor_labels 没开，标签变成 exported_ 前缀**

- 现象：推送的指标上 `job` 标签变成了 `pushgateway`，原始 job 变成 `exported_job`，查询对不上。
- 根本原因：默认 honor_labels=false，Prometheus 用自己的标签覆盖。
- 解决：pushgateway 的 job 配置加 `honor_labels: true`，reload。
- 预防：记住采集 Pushgateway 必开此项。

**坑 14：Pushgateway 旧数据误导**

- 现象：任务早已失败/下线，Grafana 仍显示最后一次推的值。
- 根本原因：Pushgateway 不自动删数据。
- 解决：任务逻辑里失败时推 0/异常状态，或结束时主动 DELETE 对应分组；定期清理。
- 预防：推送脚本设计好"过期与删除"逻辑，别只推一次就不管。

---
# 阶段三：PromQL 查询语言与自定义 Exporter

## 阶段目标

- 理解四种数据类型（即时向量、范围向量、标量、字符串）；
- 熟练使用标签选择器、范围选择器、offset；
- 分清 Counter、Gauge、Histogram、Summary 四种指标类型及适用场景；
- 会用算术/比较/逻辑运算符、向量匹配、聚合运算、常用函数写出实用查询；
- 能用 Python、Go 开发自定义 Exporter，并在 Grafana 里为自定义指标画图。

所有查询都在 Prometheus 自带界面（`http://【监控服务器IP】:9090`）顶部 **Graph** 页面完成：输入表达式 → 点 **Execute** → 看 Table/Graph。

---

## 3.1 指标数据基础

### 3.1.1 时间序列与向量

- **时间序列数据**：按时间顺序记录系统状态变化的数据，每个数据称为一个**样本（Sample）**；周期性采集后形成离散的样本序列，这个序列也叫**向量（Vector）**。
- **类比**：把多条序列放在同一坐标系（横轴时间、纵轴序列），就形成一个由数据点组成的矩阵——就像一张每格都有数字的表格。
- Prometheus 靠**指标名 + 标签集**唯一定义一条时间序列：指标名说明"测的是什么属性"，标签是在这个属性上再细分的维度。

### 3.1.2 数据模型与样本

指标名有两种等价写法：

```text
<metric name>{<label name>=<label value>, …}
{__name__="metric name", <label name>=<label value>, …}
```

第二种把指标名当成一个特殊标签 `__name__`，常用于内部处理和按名字正则匹配。

**每个样本由两部分组成**：

| 组成 | 内容 |
| --- | --- |
| key（键） | 指标名 + 标签 + 时间戳（毫秒精度） |
| value（值） | float64 浮点数 |

务必记住的规则：

- 指标名相同、标签不同 → 不同的时间序列；
- **更改任何标签值（包括增、删标签）都会创建新序列**；
- 标签要尽量稳定，否则图形、告警、记录规则会失效。

---

## 3.2 PromQL 基础

### 3.2.1 它是什么

PromQL（Prometheus Query Language）是 Prometheus 内置的**函数式表达式语言**，用来实时查找、聚合时序数据。结果可以画图、在表达式浏览器里看表格，或通过 HTTP API 给外部系统用。默认以**当前时间**为基准取数。

### 3.2.2 四种表达式结果类型

| 类型 | 含义 | 类比 |
| --- | --- | --- |
| **Instant Vector 即时向量** | 同一时间戳下，每条序列各一个样本 | "此刻全班每个人的体温" |
| **Range Vector 范围向量** | 一段时间内，每条序列的一串样本 | "过去一小时每个人每 15 秒的体温" |
| **Scalar 标量** | 一个简单浮点数 | "此刻教室平均体温 36.7" |
| **String 字符串** | 一个简单字符串（当前基本未使用） | 一句话 |

**字面量写法**：

```text
# 字符串：单引号、双引号、反引号都行；反引号里的转义符不生效
"this is a string"
'these are unescaped: \n \t'
`these are not unescaped: \n ' " \t`

# 数字：整数、小数、负数
2      2.43      -2.43
```

### 3.2.3 使用要点（非常容易报错的地方）

1. **画图只支持即时向量**：Graph 图表面板只能画即时向量；
2. **rate 等速率函数必须吃范围向量**：即 `rate(指标[5m])`，中括号不能少；
3. **范围向量不能直接画图**，否则报错：

```text
Error executing query: invalid expression type "range vector" for range query, must be Scalar or instant Vector
```

所以范围向量几乎总是配合 `rate`、`increase`、`avg_over_time` 等函数使用，函数输出即时向量后才能画图。

### 3.2.4 数据选择器

通用样式：

```text
metrics_name{标签筛选}[时间范围] offset 偏移量
```

#### 3.2.4.1 即时向量选择器

由"指标名（可选）+ 匹配器（可选，写在 {} 里）"组成，二者至少给一个。

**用法 1：只给指标名，取该指标全部序列的最新值**

```promql
node_filefd_allocated
prometheus_http_requests_total
```

`http_requests_total` 和 `http_requests_total{}` 完全等价。

**用法 2：用 __name__ 按名字匹配多个指标**

```promql
{__name__="prometheus_http_requests_total"}
{__name__=~"^prometheus_http_.*"}
```

`=~` 是正则匹配，第二条能匹配所有以 `prometheus_http_` 开头的指标。

**用法 3：只给匹配器（跨指标名）**

```promql
{method="get"}
```

返回所有带 `method="get"` 标签的序列，可能来自不同指标。

**用法 4：指标名 + 匹配器组合**

```promql
http_requests_total{method="get"}
prometheus_http_requests_total{handler="/-/reload"}
```

**四种匹配器（Matcher）**：

| 操作符 | 含义 | 示例 |
| --- | --- | --- |
| `=` | 精确相等 | `{job="prometheus"}` |
| `!=` | 不相等 | `{instance!="localhost:9090"}` |
| `=~` | 正则匹配（**整串完全匹配，不是包含**） | `{instance=~"10.0.0.(11|12):9100"}` |
| `!~` | 正则不匹配 | `{instance!~"10.0.0.1[0-9]:9100"}` |

匹配规则细节：

- 匹配**空标签值**时，所有"未定义该标签"的序列也符合条件。例如 `http_requests_total{env=""}` 会匹配所有没有 env 标签或 env 为空的序列；
- 正则是**完全锚定**的，必须匹配标签整个值。想表达"以 ge 开头"，要写 `method=~"ge.*"`，只写 `"^ge"` 匹配不到；
- 多值用 `|`（或）：`env=~"staging|testing|development"`；
- 选择器至少包含一个指标名，或一个非空标签条件，**不能写 `{job=~".*"}`、`{job=""}` 这种"全选空条件"**。

正则示例（在你的环境里替换 IP 试）：

```promql
node_memory_MemAvailable_bytes{instance=~"10.0.0.20.:9100"}
node_memory_MemAvailable_bytes{instance=~"10.0.0.20[12]:9100"}
node_memory_MemAvailable_bytes{instance=~"10.0.0.20[1-3]:9100"}
node_memory_MemAvailable_bytes{instance=~"10.0.0.20.*:9100"}
node_memory_MemAvailable_bytes{instance=~"10.0.0.20[0-9]:9100"}
node_memory_MemAvailable_bytes{instance=~"10.0.0.20[^01]:9100"}
node_memory_MemAvailable_bytes{instance!~"10.0.0.20[12]:9100"}
```

正则符号速记：`.` 任意单个字符；`.*` 任意多个字符；`[12]` 是 1 或 2；`[1-3]` 是 1～3；`[^01]` 是除 0、1 外的字符。

#### 3.2.4.2 范围向量选择器

在即时选择器后加 `[时间范围]`：

```promql
prometheus_http_requests_total{job="prometheus"}[5m]
```

读法：过去 5 分钟内该指标的所有样本，以表格呈现。

时间单位：`s` 秒、`m` 分、`h` 时、`d` 天、`w` 周、`y` 年。必须用**整数**，可从大到小串联：`1h30m` 合法，`1.5h` 非法。

::: tip
范围向量里各序列的时间戳不会严格对齐：Prometheus 会把抓取分散在时间点前后以均衡负载。所以 Prometheus 在趋势上准确，但不是分毫不差——这也是它不能用于计费的原因之一。
:::

#### 3.2.4.3 offset 偏移修饰符

offset 改变取数的**时间基准**，紧跟在选择器后面，是一个整体、不能拆开：

```promql
# 此刻该指标的值
prometheus_http_requests_total
# 5 分钟前该指标的值
prometheus_http_requests_total offset 5m
prometheus_http_requests_total{code="200"} offset 5m
# 范围 + 偏移：1 天之前的那 5 分钟数据
http_requests_total[5m] offset 1d
http_requests_total{handler="/metrics"}[5m] offset 3m
```

`[5m] offset 3m` 的含义：以 3 分钟前为终点，往前取 5 分钟的数据。

### 3.2.5 四种指标类型

先在任意 exporter 上统计一下类型分布，命令（在监控服务器普通终端执行）：

```bash
curl -s http://【监控服务器IP】:9090/metrics | awk '$2=="TYPE"{type[$NF]++}END{for(i in type){print type[i],i}}'
```

参数解释：`awk '$2=="TYPE"'` 挑出第二列是 TYPE 的行，`$NF` 是最后一列（类型名），统计每种类型出现次数。预期输出类似：

```text
74 gauge
7 histogram
12 summary
93 counter
```

#### Counter（计数器）

- **是什么**：单调递增的累计值，只增不减，进程重启时归零重新计数；
- **类比**：像汽车的**总里程表**，只会往上走，熄火重启后小表可能归零但累计逻辑不变；
- **典型指标**：请求总数、错误总数、任务完成数、网络收发包总数。**不能用它表示会减少的值**。

Counter 一般不直接看总数，而配合 `rate`、`irate`、`increase`、`topk` 看变化：

```promql
# 请求总数排名前 3 的序列
topk(3, http_requests_total)
# 2 小时内每秒平均增长速率（平均值，会抹平突发）
rate(http_requests_total[2h])
# 瞬时速率（取范围内最后两个点，能反映突发）
irate(http_requests_total[2h])
```

#### Gauge（仪表盘/瞬时值）

- **是什么**：可任意上下波动的瞬时数值；
- **类比**：像**温度计、体重秤**，当前是多少就是多少，可升可降；
- **典型指标**：CPU 使用率、内存/磁盘剩余、当前并发连接数、队列积压、温度。

Gauge 常做求和、平均、最值，也配合 `predict_linear`（预测）、`delta`（差值）：

```promql
# 2 小时内 CPU 温度的变化量（末值减首值）
delta(cpu_temp_celsius{host="【监控服务器IP】"}[2h])
# 按线性回归预测 4 小时后的值（磁盘容量预警常用）
predict_linear(node_filesystem_free_bytes{mountpoint="/"}[1h], 4*3600)
```

#### Histogram（直方图）

- **是什么**：统计数据**分布**——把观测值按区间（bucket，存储桶）计数，再用函数算分位数；
- **类比**：像统计**考试成绩分布**：0～60 分多少人、60～80 分多少人、80～100 分多少人；
- **典型场景**：请求响应时间分布（0～50ms 多少、50ms～2s 多少、10s 以上多少）、响应大小分布。

Prometheus 的桶是**累积（cumulative）**的：每个桶包含它之前所有桶的样本，因此叫累积直方图，维护成本低。一个 Histogram 指标 `<basename>` 会生成三类序列：

```promql
# 各桶的累计样本数，le（小于等于）是桶的上界；+Inf 桶包含全部样本
<basename>_bucket{le="<上界>"}
# 所有观测值总和
<basename>_sum
# 观测总次数（本质是 Counter）
<basename>_count
```

真实样例：

```text
# TYPE prometheus_tsdb_compaction_chunk_range_seconds histogram
prometheus_tsdb_compaction_chunk_range_seconds_bucket{le="100"} 0
prometheus_tsdb_compaction_chunk_range_seconds_bucket{le="400"} 0
prometheus_tsdb_compaction_chunk_range_seconds_bucket{le="6.5536e+06"} 6028
prometheus_tsdb_compaction_chunk_range_seconds_bucket{le="+Inf"} 6028
prometheus_tsdb_compaction_chunk_range_seconds_sum 1.0734846288e+10
prometheus_tsdb_compaction_chunk_range_seconds_count 6028
```

分位数用 `histogram_quantile()` 在**服务端**估算（假设桶内线性分布，结果是近似值，桶越粗越不准）：

```promql
# 过去 10 分钟请求耗时的第 90 百分位（P90）
histogram_quantile(0.9, rate(prometheus_http_request_duration_seconds_bucket[10m]))
```

#### Summary（摘要）

- **是什么**：和 Histogram 类似，但**分位数在客户端直接算好**并暴露；
- **类比**：Histogram 像老师拿原始成绩自己算百分位；Summary 像课代表提前算好各百分位交给老师；
- **典型指标**：Go GC 停顿时间 `go_gc_duration_seconds`、抓取间隔 `prometheus_target_interval_length_seconds`。

一个 Summary 生成：

```promql
<basename>{quantile="0.5"}      # 客户端算好的中位数
<basename>{quantile="0.9"}      # P90
<basename>{quantile="0.99"}     # P99
<basename>_sum
<basename>_count
```

真实样例：

```text
# HELP go_gc_duration_seconds A summary of the pause duration of garbage collection cycles.
# TYPE go_gc_duration_seconds summary
go_gc_duration_seconds{quantile="0"} 3.4414e-05
go_gc_duration_seconds{quantile="0.5"} 6.5102e-05
go_gc_duration_seconds{quantile="1"} 0.001090964
go_gc_duration_seconds_sum 0.02311494
go_gc_duration_seconds_count 229
```

#### Histogram 与 Summary 对比（高频面试题）

| 对比项 | Histogram | Summary |
| --- | --- | --- |
| 分位数在哪算 | 服务端 PromQL 估算 | 客户端预先算好 |
| 能否聚合后再算分位 | **能**（先聚合桶再 histogram_quantile） | **不能**（分位数无法跨实例聚合） |
| 灵活性 | 任意指定分位数、可改桶 | 只能用客户端定义好的分位点 |
| 查询性能 | 计算消耗服务端资源 | 查询快 |
| 准确度 | 近似，取决于桶粒度 | 对该客户端较准 |
| 资源开销 | 客户端只做分桶，开销小 | 客户端计算分位，开销略大 |

经验：需要**跨实例聚合**（如整个服务的 P99）选 Histogram；只关心单实例、且查询性能敏感可考虑 Summary。

---

## 3.3 PromQL 运算

### 3.3.1 二元运算符

**算术运算符**：

| 符号 | 含义 |
| --- | --- |
| `+` `-` `*` `/` | 加、减、乘、除 |
| `%` | 取模（余数） |
| `^` | 幂（乘方） |

**比较运算符**：`==`（等于）、`!=`（不等）、`>`、`<`、`>=`、`<=`。

**逻辑/集合运算符**：`and`、`or`、`unless`——**只能在两个即时向量之间使用，标量不能参与**。

**优先级（从高到低）**：

```text
1. ^
2. *  /  %
3. +  -
4. == != <= < >= >
5. and  unless
6. or
```

同级左结合（幂运算右结合）；可用 `()` 改变次序。

**算术运算示例**：

```promql
# GC 平均停顿 = 总停顿 / 次数
go_gc_duration_seconds_sum / go_gc_duration_seconds_count

# 空闲内存换算成 MB
node_memory_MemFree_bytes / (1024 * 1024)

# 可用内存占比（百分比）
node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes * 100

# 内存使用率（百分比）
(node_memory_MemTotal_bytes - node_memory_MemFree_bytes) / node_memory_MemTotal_bytes * 100

# 根分区磁盘使用率（百分比）
(node_filesystem_size_bytes{mountpoint="/"} - node_filesystem_free_bytes{mountpoint="/"}) / node_filesystem_size_bytes{mountpoint="/"} * 100
```

**比较运算示例**：

```promql
# 内存使用率超过 95% 的序列（不满足的序列直接不返回）
(node_memory_MemTotal_bytes - node_memory_MemFree_bytes) / node_memory_MemTotal_bytes > 0.95

# 内存利用率是否超过 80%：加 bool 后不做过滤，满足返回 1、不满足返回 0
(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100 > bool 80

# 请求数超过 1000 时返回 1，否则 0
prometheus_http_requests_total > bool 1000
```

`bool` 的作用：默认比较运算符会**过滤掉**不满足条件的序列；加 `bool` 后不过滤，而是把比较结果写成 0/1，形成新序列——做"状态指示"时用。

**集合运算示例**：

```promql
# 并集 or：两侧序列都保留（标签完全相同的以左侧为准）
node_memory_MemTotal_bytes{instance="10.0.0.104:9100"} or node_memory_MemFree_bytes{instance="10.0.0.105:9100"}

# 交集 and：只保留"在右侧也存在"的左侧序列
node_memory_MemTotal_bytes{instance="10.0.0.101:9100"} and node_memory_MemFree_bytes{instance="10.0.0.104:9100"}

# 补集 unless：从左侧剔除"在右侧也存在"的序列
node_memory_MemTotal_bytes{job="node_exporter"} unless node_memory_MemTotal_bytes{instance="10.0.0.104:9100"}
```

`and`/`or`/`unless` 操作的是完整表达式（向量），不是单个数字。

### 3.3.2 向量匹配

两侧向量做运算时，默认按"全部标签完全相同"一一配对。标签对不上时用下面关键字调整：

| 关键字 | 作用 |
| --- | --- |
| `on(标签列表)` | 只用列出的标签做匹配 |
| `ignoring(标签列表)` | 匹配时忽略列出的标签 |
| `group_left(标签列表)` | 允许**左多右少**（多对一） |
| `group_right(标签列表)` | 允许**左多右少的反向**（一对多） |

**一对一匹配**：

```promql
# 各方法 500 错误占该方法总请求的比例；忽略 code 标签后按 method 配对
method_code:http_errors:rate5m{code="500"} / ignoring(code) method:http_requests:rate5m
```

示例输入与结果：

```text
method_code:http_errors:rate5m{method="get", code="500"} 24
method_code:http_errors:rate5m{method="post", code="500"} 6
method:http_requests:rate5m{method="get"} 600
method:http_requests:rate5m{method="post"} 120

结果：
{method="get"} 0.04      # 24 / 600
{method="post"} 0.05     # 6 / 120
```

没有 `ignoring(code)` 时，两侧标签集不同（一侧多 code）无法匹配；`put`、`del` 方法在另一侧没有对应项，不会出现在结果里。

**多对一（group_left）**：

```promql
# 左侧每个 method 有 code=500/404 多条，右侧每个 method 一条，用 group_left
method_code:http_errors:rate5m / ignoring(code) group_left method:http_requests:rate5m
```

结果：

```text
{method="get", code="500"} 0.04     # 24 / 600
{method="get", code="404"} 0.05     # 30 / 600
{method="post", code="500"} 0.05    # 6 / 120
{method="post", code="404"} 0.175   # 21 / 120
```

`group_left/right` 括号里还可以列出"需要从另一侧带过来的标签"。一对多把 `group_left` 换成 `group_right` 即可。

### 3.3.3 聚合运算

聚合运算符（注意：它们**不是函数**，语法上不需要用 by 时直接 `sum(...)`），常见 11 种：

| 运算符 | 作用 |
| --- | --- |
| `sum` | 求和 |
| `min` / `max` | 最小 / 最大值 |
| `avg` | 平均值 |
| `count` | 统计序列条数 |
| `count_values` | 按样本值计数（把值变成新标签） |
| `stddev` / `stdvar` | 标准差 / 方差（衡量波动） |
| `topk` / `bottomk` | 值最大 / 最小的前 k 条序列 |
| `quantile` | 聚合分位数 |

**分组关键字**：

| 关键字 | 含义 |
| --- | --- |
| `by (标签列表)` | 只按列出的标签分组 |
| `without (标签列表)` | 排除列出的标签，按其余所有标签分组 |

两种等价写法：

```promql
sum(node_memory_MemTotal_bytes) by (instance)
sum by (instance) (node_memory_MemTotal_bytes)
```

聚合示例：

```promql
# 显示系统版本
node_os_version
# 统计 Ubuntu 主机数量
count(node_os_version{id="ubuntu"})
# 按版本值计数，新标签名叫 os_version
count_values("os_version", node_os_version)
# 全部主机内存总和
sum(node_memory_MemTotal_bytes)
# 按实例分别求内存总量
sum(node_memory_MemTotal_bytes) by (instance)
# 每台主机的 CPU 核数（system 模式的 CPU 条目数 = 核数）
count(node_cpu_seconds_total{mode="system"}) by (instance)
# 最大请求数，按 handler、instance 分组
max(prometheus_http_requests_total) by (handler, instance)
# 值最大的前 5 条 / 最小的前 5 条
topk(5, prometheus_http_requests_total)
bottomk(5, prometheus_http_requests_total)
# 排除 instance、job 后分组求和
sum(prometheus_http_requests_total) without (instance, job)
# 仅按 mode 分组求和
sum(node_cpu_seconds_total) by (mode)
```

`count_values("os_version", node_os_version)` 的典型结果：

```text
{os_version="22.04"} 4
{os_version="20.04"} 2
```

**占比类查询（注意两侧结构必须匹配）**：

```promql
# /metrics 请求占所有请求的百分比（两侧都聚合成无维度的单值，才能相除）
sum(prometheus_http_requests_total{handler="/metrics", instance="localhost:9090"})
  / sum(prometheus_http_requests_total{instance="localhost:9090"})

# 200 响应占比
sum(prometheus_http_requests_total{code="200", handler="/-/ready"})
  / sum(prometheus_http_requests_total{handler="/-/ready"})

# Nginx 某接口 200 占比
sum(nginx_http_requests_total{path="/api", method="GET", code="200"})
  / sum(nginx_http_requests_total{path="/api", method="GET"})
```

::: warning
下面这种写法会报错或对不上：左侧是带一堆标签的明细序列，右侧是 `sum(...) by (...)` 聚合后的向量，两侧标签结构不同、无法一一匹配，除法没有结果：

```promql
# 错误示范：左明细、右聚合，结构不兼容
prometheus_http_requests_total{code="200"} / sum(prometheus_http_requests_total) by (handler, instance)
```

正确做法：**两侧都先聚合成相同标签维度再相除**（如上一组示例）。
:::

### 3.3.4 常用功能函数

官方提供约 40 个函数，按类别掌握常用的即可。

**取整与数学**：

```promql
ceil(node_load15 * 10)      # 向上取整
floor(node_load15 * 10)     # 向下取整
round(node_load15 * 10)     # 四舍五入
abs(指标)                    # 绝对值
sqrt(指标)                   # 平方根；ln/log2/log10 对数，exp 指数
```

**Counter 变化类（最高频）**：

```promql
# increase：区间内的增长量（末值减首值）
increase(node_cpu_seconds_total{cpu="0", mode="idle"}[1m])

# CPU 使用率（用 increase 写法，与 rate 等价思路）
(1 - sum(increase(node_cpu_seconds_total{mode="idle"}[1m])) by (instance)
   / sum(increase(node_cpu_seconds_total[1m])) by (instance)) * 100

# rate：区间内每秒平均增量 = (末值-首值)/秒数
rate(node_disk_read_bytes_total[1m])
# 网卡每秒发送 MB
rate(node_network_transmit_bytes_total{device="eth0"}[1m]) / 1024 / 1024

# irate：取区间内最后两个点算瞬时速率
irate(node_disk_read_bytes_total[1m])

# resets：区间内 Counter 被重置（归零）的次数
resets(指标[5m])
```

**rate 与 irate 的区别（高频）**：

| 对比 | rate | irate |
| --- | --- | --- |
| 计算 | 区间所有点算速率后取平均 | 只取最后两个点 |
| 图像 | 平缓，**会削平短时峰值** | 尖锐，能反映突发 |
| 适用 | 缓慢变化的 Counter、告警阈值（避免毛刺误报） | 快速变化的 Counter、看实时峰值 |

经验：**告警用 rate（避免毛刺误报），看实时尖峰用 irate**；irate 的区间建议至少包含 2 个以上样本。

**Gauge 变化类**：

```promql
delta(指标[2h])        # 末值减首值（变化量）
idelta(指标[2h])       # 区间内相邻样本差值的最新一个
deriv(指标[1h])        # 线性回归斜率（每秒变化趋势）
predict_linear(指标[1h], 4*3600)   # 预测 4 小时后的值
holt_winters(指标[30m], 0.5, 0.5)  # 指数平滑，降噪
```

**子区间聚合（_over_time 系列，Gauge/Counter 通用）**：

```promql
min_over_time(指标[5m])
max_over_time(指标[5m])
avg_over_time(指标[5m])
sum_over_time(指标[5m])
count_over_time(指标[5m])
quantile_over_time(0.95, 指标[5m])
stddev_over_time(指标[5m])
stdvar_over_time(指标[5m])
last_over_time(指标[5m])
```

**取样与缺失判断**：

```promql
sort(指标)              # 按值升序
sort_desc(指标)         # 降序
changes(指标[5m])       # 区间内值变化次数
clamp_max(指标, 100)    # 超过 100 的压成 100
clamp_min(指标, 0)      # 小于 0 的抬成 0
scalar(即时向量)        # 取单条序列转成标量
vector(标量)            # 标量转成无标签即时向量
absent(指标)            # 指标存在返回空；不存在返回 1（用于"指标缺失"告警）
absent_over_time(指标[1h])   # 区间内完全没样本时返回 1
```

absent 示例：

```promql
# 指标名写错/没采集时，返回 absent 结果（值为 1），可据此告警
absent(node_memory_SwapTotal_bytes)
```

**时间类函数**：

```promql
time()                # 当前 Unix 时间戳（秒）
hour() minute() month() year()
day_of_month() day_of_week() days_in_month()
timestamp(即时向量)    # 样本自身的时间戳
```

time 示例：

```promql
# 每台主机已运行多少小时
(time() - node_boot_time_seconds) / 3600
# 全部主机运行小时总和
sum(time() - node_boot_time_seconds) / 3600
```

**标签类函数**：

```promql
# label_join：把多个标签值拼成一个新标签
label_join(指标, "新标签", "分隔符", "源标签1", "源标签2")
# label_replace：用正则从源标签提取内容写入新标签
label_replace(指标, "新标签", "替换串", "源标签", "正则")
```

---
## 3.4 定制开发 Exporter

### 3.4.1 指标的五种提供方式

Prometheus 能监控的指标，来源有：

1. **Prometheus 内置**（自身指标）；
2. **程序仪表（Instrumentation）**：应用自带指标功能，如 Zookeeper、GitLab、Grafana；
3. **额外 Exporter**：第三方翻译程序，如 Node Exporter；
4. **Pushgateway**（短任务）；
5. **自行编程实现**：需要开发能力，自定义业务指标（转化率、下单量等）。

本质上，一个 metric 就是服务启动后自动生成的一个 HTTP URL，访问它就能拿到监控项。生产中大量业务指标（转化率、各渠道下单数）官方没有现成指标，就要自己开发标准的 `/metrics` 接口。

各语言客户端库：

```text
Go:      https://github.com/prometheus/client_golang
Python:  https://github.com/prometheus/client_python
文档:    https://prometheus.github.io/client_python/
Java:    https://github.com/prometheus/client_java
Rust:    https://github.com/prometheus/client_rust
```

### 3.4.2 Python 实现自定义 Exporter

#### 3.4.2.1 准备环境（推荐 apt 直接装）

在**应用服务器 app01**（示例 10.0.0.12）上执行，用户 root。

```bash
apt update && apt -y install python3 python3-pip python3-flask python3-prometheus-client
mkdir -p /data/code
```

Ubuntu 24.04 仓库已包含 Flask 和 prometheus-client，最省事。

**如果用 pip 安装（22.04 或仓库没有时），先配清华 pip 源**：

```bash
pip3 config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
pip3 install flask prometheus_client
pip3 list | grep -Ei 'flask|prometheus'
```

pip 配置文件实际路径 `/root/.config/pip/pip.conf`，内容：

```ini
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
```

**备选 pip 源（清华不通时）**：阿里云 `https://mirrors.aliyun.com/pypi/simple`。

#### 3.4.2.2 最简三步示例（先建立感性认识）

第 1 步：安装客户端（上一步已装）；
第 2 步：把下面内容存成 `/data/code/three_step.py`：

```python
from prometheus_client import start_http_server, Summary
import random
import time

# 创建一个指标，记录处理耗时和请求
REQUEST_TIME = Summary('request_processing_seconds', 'Time spent processing request')

# 用装饰器给函数计时
@REQUEST_TIME.time()
def process_request(t):
    """模拟处理请求：睡 t 秒"""
    time.sleep(t)

if __name__ == '__main__':
    # 启动 HTTP 服务暴露指标
    start_http_server(8000)
    # 不断产生请求
    while True:
        process_request(random.random())
```

第 3 步：运行并访问 `http://【应用服务器IP】:8000/` 查看指标：

```bash
python3 /data/code/three_step.py
```

#### 3.4.2.3 指标对象的设计方式

prometheus_client 中各类型指标的构造方式（了解参数）：

```python
from prometheus_client import Counter, Gauge, Summary
from prometheus_client.core import CollectorRegistry

class Monitor:
    def __init__(self):
        # 自建收集器注册表
        self.collector_registry = CollectorRegistry(auto_describe=False)

        # Summary：名称、说明、标签列表、注册表
        self.summary_metric = Summary(
            name="summary_metric_name",
            documentation="summary_metric_desc",
            labelnames=("label1", "label2", "label3"),
            registry=self.collector_registry)

        # Gauge
        self.gauge_metric = Gauge(
            name="gauge_metric_name",
            documentation="gauge_metric_desc",
            labelnames=("method", "code", "uri"),
            registry=self.collector_registry)

        # Counter
        self.counter_metric = Counter(
            name="counter_metric_name",
            documentation="counter_metric_desc",
            labelnames=("method", "code", "uri"),
            registry=self.collector_registry)
```

#### 3.4.2.4 完整 Flask 项目（应用接口 + metrics 同端口）

创建 `/data/code/prometheus_metrics_demo.py`：

```python
#!/usr/bin/python3
from prometheus_client import Counter, Summary, generate_latest
from flask import Flask, Response
import time

app = Flask(__name__)

# 创建监控指标
REQUEST_TIME = Summary('request_processing_seconds', 'Time spent processing request')
REQUEST_COUNT = Counter('request_count', 'Total request count')

@app.route('/')
@REQUEST_TIME.time()
def hello():
    REQUEST_COUNT.inc()
    return {"return": "success OK!"}

@app.route('/metrics')
def metrics():
    # 返回 Prometheus 格式指标
    return Response(generate_latest(), mimetype='text/plain')

if __name__ == '__main__':
    # 一个 Flask 同时提供业务接口和 metrics 接口
    app.run(host='0.0.0.0', port=8000)
```

启动：

```bash
python3 /data/code/prometheus_metrics_demo.py
```

预期输出：

```text
 * Serving Flask app 'prometheus_metrics_demo'
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:8000
 * Running on http://10.0.0.12:8000
```

::: warning
Flask 自带的是**开发服务器**，生产环境请用 Gunicorn/uWSGI 等 WSGI 服务器启动，并配 systemd 管理、开机自启。例如：`apt -y install gunicorn && gunicorn -w 4 -b 0.0.0.0:8000 prometheus_metrics_demo:app`。
:::

#### 3.4.2.5 制造访问并观察指标

每访问一次根路径，`request_count_total` 增加 1。写压测脚本 `/data/code/curl_metrics.sh`：

```bash
cat > /data/code/curl_metrics.sh <<'EOF'
#!/bin/bash
while true; do
  sleep_num=$(($RANDOM%3+1))
  curl_num=$(($RANDOM%50+1))
  for c_num in $(seq $curl_num); do
    curl -s http://127.0.0.1:8000 >/dev/null 2>&1
  done
  sleep $sleep_num
done
EOF
chmod +x /data/code/curl_metrics.sh
nohup bash /data/code/curl_metrics.sh >/dev/null 2>&1 &
```

参数解释：`$RANDOM%3+1` 生成 1～3 的随机秒数；`seq N` 生成 1～N；`nohup ... &` 让脚本后台持续跑。

查看自定义指标：

```bash
curl -s http://127.0.0.1:8000/metrics | grep -A3 -E 'request_count|request_processing'
```

预期输出（数值不断增长）：

```text
# HELP request_processing_seconds Time spent processing request
# TYPE request_processing_seconds summary
request_processing_seconds_count 123.0
request_processing_seconds_sum 5.67
# HELP request_count_total Total request count
# TYPE request_count_total counter
request_count_total 123.0
```

#### 3.4.2.6 Prometheus 集成

回到**监控服务器**，编辑 `/usr/local/prometheus/conf/prometheus.yml` 追加：

```yaml
  - job_name: 'my_metric'
    static_configs:
      - targets:
          - '【应用服务器IP】:8000'
        labels:
          app: 'flask_web'
```

检查生效：

```bash
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus
```

浏览器 `http://【监控服务器IP】:9090/targets` 看到 `my_metric` 为 UP；Graph 查 `request_count_total` 有数据。常用速率查询：

```promql
rate(request_count_total{job="my_metric"}[5m])
irate(request_count_total{job="my_metric"}[5m])
```

记得在应用服务器放通 8000 端口（ufw/安全组）。

### 3.4.3 Golang 实现自定义 Exporter

**第 1 步：安装 Go**

```bash
apt update && apt -y install golang
go version
```

**第 2 步：写代码**，创建 `/data/code/go-exporter/main.go`：

```go
package main

import (
	"net/http"

	"github.com/prometheus/client_golang/prometheus/promhttp"
)

func main() {
	// 在 /metrics 暴露默认注册表
	http.Handle("/metrics", promhttp.Handler())
	http.ListenAndServe(":9527", nil)
}
```

**第 3 步：配置国内 Go 代理并拉依赖**

```bash
cd /data/code/go-exporter
go env -w GOPROXY=https://goproxy.cn,direct
go mod init my_metric
go get github.com/prometheus/client_golang/prometheus/promhttp
go mod tidy
```

参数解释：`GOPROXY=https://goproxy.cn,direct` 用七牛云 Go 代理（`direct` 表示代理没有时回源）；**备选**阿里云 `https://mirrors.aliyun.com/goproxy/`。

**第 4 步：编译运行**

```bash
# 交叉编译环境变量（本机编译可省略）
export CGO_ENABLED=0 GOARCH=amd64 GOOS=linux
go build -o exporter_demo
./exporter_demo
```

验证（另开终端）：

```bash
curl -s http://127.0.0.1:9527/metrics | head -10
```

预期输出：

```text
# HELP go_gc_cycles_automatic_gc_cycles_total Count of completed GC cycles generated by the Go runtime.
# TYPE go_gc_cycles_automatic_gc_cycles_total counter
go_gc_cycles_automatic_gc_cycles_total 0
# HELP go_gc_duration_seconds A summary of the pause duration of garbage collection cycles.
# TYPE go_gc_duration_seconds summary
```

同样在 Prometheus 加一个指向 `【应用服务器IP】:9527` 的 job 即可。

---

## 3.5 基于 PromQL 在 Grafana 做自定义看板

### 3.5.1 Grafana 基础回顾

- **数据源（Data Source）**：提供数据的存储系统；**仪表盘（Dashboard）**：组织面板（Panel）的容器；
- Grafana 支持 TSDB（Prometheus、InfluxDB）、日志（Loki、ES）、追踪（Jaeger、Zipkin）、SQL（MySQL、PostgreSQL）等数据源；
- 可视化样式有两种来源：**默认可视化类型**，以及用 `grafana-cli` 从插件市场安装的**可视化插件**。

插件市场地址：

```text
https://grafana.com/plugins/
```

### 3.5.2 面板的操作菜单

把鼠标放到面板标题上，出现小三角，点开：

| 菜单项 | 作用 |
| --- | --- |
| View（快捷键 v） | 全屏查看面板 |
| Edit（快捷键 e） | 编辑面板（最常用） |
| Share | 分享面板（链接/快照/嵌入） |
| Explore（快捷键 x） | 到 Explore 页深入分析 |
| More | 复制、复制为、查看 JSON、导出 CSV、删除等 |

Edit 页底部四个配置图标：

| 图标 | 配置内容 |
| --- | --- |
| Query | 查询表达式（A、B、C 多个查询） |
| Visualize（Visualization） | 图形样式 |
| General | 标题、描述、透明等 |
| Alert | 面板告警（新版 Grafana 已转向统一告警，了解） |

### 3.5.3 绘图案例：QPS、变化率、平均耗时三条曲线

**需求与对应 PromQL**：

```promql
# 1. 每分钟请求数量（QPS 曲线用速率，这里演示每分钟增量）
increase(request_count_total{job="my_metric"}[1m])

# 2. 每分钟请求量变化率（瞬时速率）
irate(request_count_total{job="my_metric"}[1m])

# 3. 请求处理平均耗时（总耗时 / 次数）
request_processing_seconds_sum{job="my_metric"}
  / request_processing_seconds_count{job="my_metric"}
```

**第 1 个面板的制作步骤**：

1. 点左侧 **+ → Dashboard → Add visualization**，选择 Prometheus 数据源；
2. 在 Query 区把第一条 PromQL 粘到查询框（Metrics）；
3. 设置 **Legend（图例）** 为 `{{instance}}_request_count`；
4. 点查询右侧的"小眼睛/刷新"预览，确认有曲线；
5. 切到 **Visualization**：默认就是 Time series（折线图）；可设置坐标轴、单位（如 none/short）、堆叠等；X 轴 Mode 默认按时间；
6. 切到 **General**：填面板标题；
7. 右上角 **Save dashboard**，命名保存。

::: tip
Legend 里 `{{instance}}` 会被替换成实际标签值；如果标签变量不生效，检查查询是否处于可刷新状态（点一次刷新/小眼睛）。
:::

**追加其余面板**：在 Dashboard 顶部点 **Add → Visualization**（Add panel），重复上面步骤做出第 2、3 个面板。

**调整布局**：拖动面板标题可移动位置；拖面板右下角小三角可改变大小；最后再 Save 一次。

**制作流程总结（通用 SOP）**：

1. 了解业务、分析要展示的指标；
2. 创建 Dashboard；
3. 逐个创建 Panel、写 PromQL；
4. 完善可视化样式、图例、单位；
5. 保存，需要时再加告警。

---

## 本阶段命令速查表

```bash
# === Python Exporter（app01）===
apt -y install python3 python3-pip python3-flask python3-prometheus-client
mkdir -p /data/code
# prometheus_metrics_demo.py 内容见 3.4.2.4，然后：
python3 /data/code/prometheus_metrics_demo.py
# 生产用 gunicorn：
apt -y install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 prometheus_metrics_demo:app

# pip 换源
pip3 config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# === Go Exporter ===
apt -y install golang
go env -w GOPROXY=https://goproxy.cn,direct
cd /data/code/go-exporter
go mod init my_metric
go get github.com/prometheus/client_golang/prometheus/promhttp
go build -o exporter_demo && ./exporter_demo

# === Prometheus 每次改配置 ===
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus

# === 命令行查指标（不打开浏览器）===
curl -s http://127.0.0.1:9100/metrics | grep node_load1
```

**PromQL 速记**：

```promql
# 主机 CPU 使用率（按实例）
100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)
# 内存使用率
(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100
# 根分区使用率
100 * (1 - node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"})
# 系统负载（按 CPU 核数归一）
node_load1 / count by (instance) (node_cpu_seconds_total{mode="idle"})
# QPS
sum by (instance) (rate(request_count_total[5m]))
# P99 延迟
histogram_quantile(0.99, sum by (le) (rate(xxx_bucket[5m])))
```

---

## 本阶段常见坑与解决

**坑 1：范围向量直接画图**

- 报错原样：`invalid expression type "range vector" for range query, must be Scalar or instant Vector`。
- 原因：Graph 只吃即时向量。
- 解决：外面套函数，如 `rate(指标[5m])`、`increase(指标[5m])`、`avg_over_time(指标[5m])`。

**坑 2：rate 忘了加 [区间]**

- 报错原样：`parse error: expected type range vector in call to function "rate", got instant vector`。
- 解决：参数必须是范围向量 `rate(指标[5m])`。

**坑 3：正则写成"包含"逻辑**

- 现象：`{instance=~"10.0.0.1"}` 匹配不到 `10.0.0.11`，或 `{method=~"^ge"}` 匹配不到 `get`。
- 原因：PromQL 正则是整串完全锚定。
- 解决：补 `.*`，如 `instance=~"10.0.0.1.*"`、`method=~"ge.*"`。

**坑 4：Summary 分位数无法聚合**

- 现象：`avg(go_gc_duration_seconds{quantile="0.99"})` 算出来的"全局 P99"没有统计意义。
- 原因：分位数不能跨实例算术平均。
- 解决：需要全局分位请改用 Histogram，聚合桶后用 `histogram_quantile`。

**坑 5：pip / go 拉包超时**

- 报错原样：`ReadTimeoutError: HTTPSConnectionPool(host='pypi.org', port=443): Read timed out`；Go 报 `dial tcp: lookup proxy.golang.org: no such host` 或超时。
- 解决：pip 用清华/阿里源；Go 用 `goproxy.cn`；命令见速查表。

**坑 6：Flask 开发服务器直接上生产**

- 现象：高并发下性能差、警告 `This is a development server`。
- 解决：用 Gunicorn/uWSGI 启动并配 systemd、开机自启、Restart。

**坑 7：Grafana Legend 不显示标签值**

- 现象：图例显示成整条 PromQL 语句。
- 解决：Legend 填 `{{标签名}}`，如 `{{instance}}`，并刷新查询。

**坑 8：除法两侧结构不匹配导致空结果**

- 现象：写了占比查询但没有任何输出，也不报错。
- 原因：左右向量标签集不同、无法配对。
- 解决：两侧用 `sum ... by (相同标签)` 聚合成相同维度，或用 `ignoring/group_left` 明确匹配规则。

**坑 9：自定义指标没写 # TYPE，类型为 untyped**

- 现象：指标存在但类型显示 untyped，部分函数/看板行为异常。
- 解决：客户端库正常使用 Counter/Gauge 对象即可自动生成 TYPE；手写文本时补上 `# TYPE 名字 counter/gauge/...`。

---
# 阶段四：标签管理

## 阶段目标

- 分清默认标签、应用标签、自定义标签，以及 `__` 私有标签的作用；
- 理解指标从"被发现"到"入库"的完整生命周期；
- 说清 `relabel_configs` 与 `metric_relabel_configs` 的本质区别；
- 熟练使用 replace、keep、drop、labelmap、labeldrop、hashmod 等动作完成过滤目标、删除指标、改写标签。

---

## 4.1 标签简介

标签的核心功能是**对数据分组和分类、过滤筛选**。常见管理场景：

1. 删除不必要的指标；
2. 从指标中删除敏感或不需要的标签；
3. 添加、编辑、修改标签值或标签格式。

标签按来源分三类：

| 分类 | 来源 | 形式 | 例子 |
| --- | --- | --- | --- |
| 默认标签 | Prometheus 内置 | `__keyname__` | `__address__`、`__scheme__` |
| 应用标签 | 被监控应用内置 | `keyname` | Node Exporter 的 `cpu`、`mode` |
| 自定义标签 | 用户自己定义 | `keyname` | static_configs 里 labels 写的 `env` |

### 4.1.1 添加自定义标签

在 job 的 `static_configs` 里用 `labels` 给整组目标附加标签：

```yaml
scrape_configs:
  - job_name: 'node_exporter'
    static_configs:
      - targets: ['【Web服务器IP】:9100', '【应用服务器IP】:9100', '【数据库服务器IP】:9100']
        labels:
          node: "worker node"
          type: "test"
  - job_name: 'zookeeper'
    static_configs:
      - targets: ['【应用服务器IP】:7000']
        labels: {app: 'zookeeper', type: 'dev'}
```

YAML 中标签既可以写成缩进的字典格式，也可以写成一行 `{键: '值'}`，两种都合法。改完 `promtool check config` + `systemctl reload prometheus`，在 Targets 页能看到新标签。

---

## 4.2 指标的生命周期

### 4.2.1 私有标签

私有标签以 `__` 开头，承载监控目标的默认元数据：

| 私有标签 | 含义 |
| --- | --- |
| `__address__` | 目标地址 `host:port` |
| `__scheme__` | 请求协议 http/https |
| `__metrics_path__` | 指标 URL 路径，默认 `/metrics` |
| `__param_<name>` | URL 查询参数（如果有） |
| `__meta_*` | 服务发现产生的元数据（不同发现机制各不同） |

### 4.2.2 Prometheus 数据处理流程

1. 每个 `scrape_interval`，Prometheus 检查要执行的 Job；
2. Job 按"发现配置"生成 target 列表——**服务发现**；
3. 服务发现返回 target 列表，元数据标签都以 `__meta_` 开头；同时设置 `__scheme__`、`__address__`、`__metrics_path__`，URL 参数以 `__param_` 开头；
4. 对发现的每个目标，执行 **relabel_configs（重新标记目标）**：
   - 把元数据标签里的信息附加到指标上；
   - 过滤目标（决定这个 target 采不采）；
5. 执行数据抓取；
6. 抓取来的指标在**保存前**执行 **metric_relabel_configs（重新标记指标）**：
   - 删除不必要的指标；
   - 删除敏感标签；
   - 添加、修改标签；
7. 指标写入 TSDB。

两个默认行为要记住：

- 指标上的 `instance` 标签默认值来自 `__address__`；
- relabel 完成后，所有 `__` 开头的标签都会被**移除**；relabel 过程中需要临时存值，请用 `__tmp` 前缀，避免与内置标签冲突。

---

## 4.3 relabel_configs 与 metric_relabel_configs 的区别

| 区别 | relabel_configs | metric_relabel_configs |
| --- | --- | --- |
| 执行时机 | **抓取之前**，服务发现之后 | **抓取之后、入库之前**（最后一步） |
| 针对对象 | **target 目标本身** | target 上的 **metric 指标** |
| 典型用途 | 过滤目标、改写地址/协议/路径、补充标签 | 删除指标/标签、修改指标标签 |
| drop 的含义 | 整个目标不采（Targets 页直接看不到/不抓） | 只丢弃匹配指标，目标仍在采 |

一句话：**relabel 决定"采谁、怎么采"；metric_relabel 决定"采回来的哪些指标留、怎么改"**。

---

## 4.4 配置字段与动作详解

### 4.4.1 通用字段

```yaml
scrape_configs:
  - job_name: 'prometheus'
    relabel_configs:
      - source_labels: [标签名, ...]
        separator: ';'          # 把多个 source_labels 的值串联时的分隔符，默认 ;
        regex: '(.*)'           # 对串联后的值做匹配，默认 (.*)
        replacement: '$1'       # 替换值，默认 $1（正则第 1 个捕获组）
        target_label: '标签名'   # replace/hashmod 时写入的目标标签
        action: 'replace'       # 动作，默认 replace
```

| 字段 | 作用 |
| --- | --- |
| `source_labels` | 参与处理的源标签列表 |
| `separator` | 多个源标签值拼接的分隔符 |
| `regex` | 匹配标签值（replace/keep/drop）或标签名（labelmap/labeldrop）的正则 |
| `replacement` | 写入的新值，支持 `$1`、`${1}` 捕获组引用 |
| `target_label` | 被写入/创建的标签名 |
| `action` | 执行的动作 |

### 4.4.2 动作（action）一览

| action | 作用 |
| --- | --- |
| **replace**（默认） | 源标签值拼接后匹配 regex，用 replacement 给 target_label 赋值；标签不存在则新建 |
| **keep** | 拼接值匹配 regex 才保留，否则丢弃 |
| **drop** | 拼接值匹配 regex 就丢弃，否则保留（与 keep 相反） |
| **hashmod** | 对源标签拼接值做 hash（配合 `modulus` 字段），结果写入 target_label，常用于**分片** |
| **labelmap** | regex 匹配**标签名**，把匹配到的标签复制成 `replacement` 指定的新标签名，**旧标签保留** |
| **labelkeep** | regex 匹配标签名才保留（白名单），其余删除 |
| **labeldrop** | regex 匹配标签名就删除（黑名单） |
| **lowercase / uppercase** | 把源标签拼接值转成小/大写写入 target_label |
| **keepequal / dropequal** | 按源标签与目标标签值是否相等保留/丢弃（高级，少用） |

::: warning
labeldrop/labelkeep 会真的删标签，而**标签是序列唯一性约束**：删标签后若两条序列变得完全相同，系统会出问题。改/加标签会创建新序列。务必想清楚再删。
:::

### 4.4.3 全局外部标签 external_labels

`global` 段可设置外部标签，用于与外部系统通信（联邦、远程存储、Alertmanager）时附加到序列/告警上：

```yaml
global:
  external_labels:
    cluster: 'chengdu-prod'
    replica: 'prometheus-a'
```

典型用途：双机高可用时用 `replica` 区分两台 Prometheus；多集群联邦/远程存储时用 `cluster` 标识来源集群。

---

## 4.5 标签管理案例

### 4.5.1 案例 1：生成 endpoint 标签

把协议、地址、路径拼成完整访问端点：

```yaml
scrape_configs:
  - job_name: 'node_exporter'
    static_configs:
      - targets: ['【Web服务器IP】:9100', '【应用服务器IP】:9100', '【数据库服务器IP】:9100']
    relabel_configs:
      - source_labels: [__scheme__, __address__, __metrics_path__]
        regex: '(http|https)(.*)'
        separator: ''
        target_label: 'endpoint'
        replacement: '${1}://${2}'
        action: replace
```

要点：`separator: ''`（空串）让三个标签值无分隔符拼接；正则两个捕获组分别拿到协议和"地址+路径"，replacement 拼成 `http://10.0.0.11:9100/metrics` 写入新标签 endpoint。

### 4.5.2 案例 2：labelmap 改名 + labeldrop 删旧标签

```yaml
    relabel_configs:
      # 第一步：把 job、app 标签复制成 job_name、app_name，旧标签仍在
      - regex: '(job|app)'
        replacement: '${1}_name'
        action: labelmap
      # 第二步：删除原来的 job、app 标签
      - regex: '(job|app)'
        action: labeldrop
      # 第三步：再把 endpoint 的值复制给新标签 myendpoint
      - source_labels: [endpoint]
        target_label: 'myendpoint'
```

注意规则**按顺序执行**：先 labelmap 复制、再 labeldrop 删旧，顺序反了就复制不到。

### 4.5.3 案例 3：删除 go 开头的指标

```yaml
scrape_configs:
  - job_name: 'node_exporter'
    static_configs:
      - targets: ['【Web服务器IP】:9100']
    metric_relabel_configs:
      - source_labels: [__name__]
        regex: 'go.*'
        action: drop
```

要点：删**指标**用 `metric_relabel_configs`；`__name__` 代表指标名。reload 后新采集的数据里不再有 `go_*` 指标（已经存进 TSDB 的历史数据不受影响）。

删除 Node Exporter 网络收包指标，完整配置如下（把 regex 换成 `node_network_receive.*`）：

```yaml
scrape_configs:
  - job_name: 'node_exporter'
    static_configs:
      - targets: ['【Web服务器IP】:9100']
    metric_relabel_configs:
      - source_labels: [__name__]
        regex: 'node_network_receive.*'
        action: drop
```

replace 示例（把 id 标签中 `/` 开头的值替换成固定串写入新标签）：

```yaml
    metric_relabel_configs:
      - source_labels: [id]
        regex: '/.*'
        replacement: '123456'
        target_label: 'replace_id'
```

### 4.5.4 案例 4：Kubernetes endpoints 重新打签

下面是 K8s 动态环境的经典 relabel（完整 K8s 采集见阶段十一）：

```yaml
  - job_name: 'kubernetes-service-endpoints'
    kubernetes_sd_configs:
      - role: endpoints
    relabel_configs:
      # 只采集注解 prometheus.io/scrape: "true" 的服务
      - source_labels: [__meta_kubernetes_service_annotation_prometheus_io_scrape]
        action: keep
        regex: 'true'
      # 注解 prometheus.io/scheme 覆盖协议
      - source_labels: [__meta_kubernetes_service_annotation_prometheus_io_scheme]
        action: replace
        target_label: __scheme__
        regex: '(https?)'
      # 注解 prometheus.io/path 覆盖指标路径
      - source_labels: [__meta_kubernetes_service_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: '(.+)'
      # 注解 prometheus.io/port 覆盖采集端口
      - source_labels: [__address__, __meta_kubernetes_service_annotation_prometheus_io_port]
        action: replace
        target_label: __address__
        regex: '([^:]+)(?::\d+)?;(\d+)'
        replacement: '$1:$2'
      # 把服务的 K8s 原生标签提升为指标标签
      - action: labelmap
        regex: '__meta_kubernetes_service_label_(.+)'
      # 命名空间、服务名固定标签
      - source_labels: [__meta_kubernetes_namespace]
        action: replace
        target_label: 'kubernetes_namespace'
      - source_labels: [__meta_kubernetes_service_name]
        action: replace
        target_label: 'kubernetes_name'
```

这套注解（`prometheus.io/scrape|scheme|path|port`）是 K8s 服务暴露指标的通用约定，阶段十一还会用到。

### 4.5.5 案例 5：Consul 发现目标后的 relabel

```yaml
  - job_name: 'consul'
    honor_labels: true
    consul_sd_configs:
      - server: '【Consul服务器IP】:8500'
        services: []
    relabel_configs:
      - source_labels: [__meta_consul_service]
        target_label: 'consul_service'
      - source_labels: [__meta_consul_dc]
        target_label: 'datacenter'
      - source_labels: [__meta_consul_tags]
        target_label: 'app'
      # Consul 自身服务没有 metrics，丢弃
      - source_labels: [__meta_consul_service]
        regex: 'consul'
        action: drop
```

Consul 服务发现的完整内容见阶段六。

---

## 本阶段命令速查表

```bash
# 编辑配置
vim /usr/local/prometheus/conf/prometheus.yml

# 固定两步：检查 + 生效
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus

# 命令行验证某标签/指标是否还在
curl -s http://【监控服务器IP】:9090/metrics | grep -c 'go_'
curl -s http://【Web服务器IP】:9100/metrics | grep node_load1
```

**常用 relabel 片段速记**：

```yaml
# 只采指定目标（relabel，抓取前）
relabel_configs:
  - source_labels: [__address__]
    regex: '10\.0\.0\.(11|12):9100'
    action: keep

# 丢弃指定指标（metric_relabel，入库前）
metric_relabel_configs:
  - source_labels: [__name__]
    regex: 'go_.*'
    action: drop

# 分片：对地址 hash 后取模（两台 Prometheus 各采一半）
relabel_configs:
  - source_labels: [__address__]
    modulus: 2
    target_label: __tmp_hash
    action: hashmod
  - source_labels: [__tmp_hash]
    regex: '0'        # 第二台写 1
    action: keep
```

---

## 本阶段常见坑与解决

**坑 1：把 relabel_configs 当 metric_relabel_configs 用**

- 现象：想删某个指标，写在 relabel_configs 里，结果要么不生效、要么整个目标消失。
- 原因：relabel 作用于 target、在抓取前，此时还没有指标可删；`__name__` 也尚未确定。
- 解决：删指标/改指标标签一律写 `metric_relabel_configs`；过滤目标才用 `relabel_configs`。

**坑 2：正则少写 .*，keep/drop 不生效**

- 现象：`regex: 'go'` 想删所有 go 指标，结果只删了名字恰好叫 go 的。
- 原因：正则整串匹配，`go` 只匹配字面量 go。
- 解决：写 `go.*`；需要前后缀时显式写全。

**坑 3：labeldrop 删标签导致序列冲突**

- 报错/现象：删标签后查询出现重复样本，日志报 `duplicate sample for timestamp`。
- 原因：标签是序列唯一约束，删成相同标签后两条序列撞车。
- 解决：去掉该 labeldrop 规则；确需删除，先确认不会让序列失去区分度。

**坑 4：规则顺序写反**

- 现象：先 labeldrop 再 labelmap，复制不出新标签。
- 原因：relabel 严格按书写顺序执行，源标签已被删就匹配不到。
- 解决：先复制/改名、后删除；改完逐条 promtool 检查。

**坑 5：__tmp 临时标签与内置标签冲突**

- 现象：临时值覆盖了系统标签，行为异常。
- 解决：临时存储统一用 `__tmp` 前缀命名（如 `__tmp_hash`），不要自创其他 `__` 开头标签。

**坑 6：reload 后以为历史数据也被删了**

- 现象：配了 drop 指标规则，但 Grafana 里还能看到过去的 go 指标。
- 原因：metric_relabel 只影响**新采集**的数据，已入库的历史数据要等保留期过期或手动删除。
- 解决：这是正常现象；如需立即清理历史数据，用 TSDB 管理接口（阶段十）或等过期。

---
# 阶段五：记录规则与告警

## 阶段目标

- 会写**记录规则**，把复杂查询预先算好；
- 理解告警从"规则计算"到"通知到人"的完整链路；
- 部署并配置 **Alertmanager**，实现去重、分组、路由、抑制、静默；
- 打通**邮件、企业微信、钉钉**三种通知渠道；
- 掌握 Alertmanager 高可用集群的搭建。

告警是监控系统最有价值的部分：人不可能 24 小时盯屏，程序自动巡检并报警，是业务稳定性的决定性保障。

---

## 5.1 记录规则

### 5.1.1 规则简介

Prometheus 支持两类规则：**记录规则（Recording Rules）**和**告警规则（Alerting Rules）**。它们写在 YAML 文件里，通过主配置的 `rule_files` 加载，由 Prometheus 按 `evaluation_interval` 周期执行。

```yaml
rule_files:
  - "first_rules.yml"
  - "second_rules.yml"
  - "../rules/*.yml"
```

相对路径是相对于 `prometheus.yml` 所在目录。改规则后让 Prometheus 重新加载：

```bash
promtool check rules 规则文件.yml
systemctl reload prometheus
```

`promtool check rules` 语法正确时打印解析后的规则并以状态码 0 退出；有错误时打印错误并以 1 退出。

### 5.1.2 记录规则说明

- **是什么**：记录规则把一个 PromQL 表达式预先、周期性地跑一遍，把结果存成一组**新的时间序列**。
- **类比**：像给一长串命令起"别名"——以后直接用短名字拿结果，不用每次重算。
- **为什么需要**：复杂查询（跨很多序列聚合）实时跑会有延迟，仪表盘每次刷新都重复算同样的表达式很浪费；预计算结果查询速度快得多，告警规则也可以直接引用。

**规则文件语法**：

```yaml
groups:
  - name: example              # 规则组名，必须唯一
    interval: 10s              # 本组评估间隔，默认取 global.evaluation_interval
    limit: 0                   # 记录规则：最多生成多少条序列；告警规则：最多多少条告警，默认 0 不限制
    rules:
      - record: job:http_inprogress_requests:sum    # 新指标名（推荐 命名空间:指标:粒度 三段式，冒号分隔）
        expr: sum(http_inprogress_requests) by (job)   # 要执行的 PromQL
        labels:                                  # 给结果附加的标签（可选）
          标签名: 标签值
```

::: tip
记录规则生成的指标名推荐用冒号三段式，如 `instance:node_cpu:avg_rate5m`，表示"按 instance 维度、node_cpu 指标、5 分钟平均速率"，一眼看出来源与粒度。冒号是规则专用，自己手写指标不要用。
:::

### 5.1.3 记录规则案例

**案例 1：给 Flask 应用的"平均处理耗时"做预计算**

原始表达式很长：

```promql
request_processing_seconds_sum{job="my_metric"} / request_processing_seconds_count{job="my_metric"}
```

创建规则文件 `/usr/local/prometheus/rules/prometheus_record_rules.yml`：

```yaml
groups:
  - name: myrules
    rules:
      - record: request_process_per_time
        expr: request_processing_seconds_sum{job="my_metric"} / request_processing_seconds_count{job="my_metric"}
        labels:
          app: flask
          role: web
      - record: request_count_per_minute
        expr: increase(request_count_total{job="my_metric"}[1m])
        labels:
          app: flask
          role: web
```

检查并在主配置加载：

```bash
promtool check rules /usr/local/prometheus/rules/prometheus_record_rules.yml
```

预期输出：

```text
Checking /usr/local/prometheus/rules/prometheus_record_rules.yml
  SUCCESS: 2 rules found
```

编辑 `/usr/local/prometheus/conf/prometheus.yml`，确认有：

```yaml
rule_files:
  - "../rules/*.yml"
```

整体检查并生效：

```bash
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus
```

预期输出：

```text
Checking /usr/local/prometheus/conf/prometheus.yml
  SUCCESS: 1 rule files found
SUCCESS: /usr/local/prometheus/conf/prometheus.yml is valid prometheus config file syntax
Checking /usr/local/prometheus/rules/prometheus_record_rules.yml
  SUCCESS: 2 rules found
```

验证：等一两个评估周期后，在 Graph 查 `request_process_per_time` 能直接拿到结果；Status → Rules 页能看到这两条规则及其状态。Grafana 面板以后直接用新指标名即可，刷新明显变快。

**案例 2：系统主机相关指标的记录规则**

创建 `/usr/local/prometheus/rules/node_record_rules.yml`：

```yaml
groups:
  - name: custom_rules
    interval: 5s
    rules:
      # 每台主机 CPU 使用率（百分比）
      - record: instance:node_cpu:avg_rate5m
        expr: 100 - avg by (instance) (irate(node_cpu_seconds_total{job="node_exporter", mode="idle"}[5m])) * 100
      # 每台主机内存使用率（百分比）
      - record: instance:node_memory_used:percent
        expr: 100 - (100 * node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)
      # 根分区剩余百分比
      - record: instance:root:node_filesystem_free_percent
        expr: 100 * node_filesystem_free_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}
```

**案例 3：MySQL 相关记录规则**（阶段七用到，先放在这里）

创建 `/usr/local/prometheus/rules/mysql_record_rules.yml`：

```yaml
groups:
  - name: mysqld_rules
    rules:
      # 主从延迟秒数（考虑手工配置的 SQL 延迟）
      - record: instance:mysql_slave_lag_seconds
        expr: mysql_slave_status_seconds_behind_master - mysql_slave_status_sql_delay
      # 心跳法计算的主从延迟
      - record: instance:mysql_heartbeat_lag_seconds
        expr: mysql_heartbeat_now_timestamp_seconds - mysql_heartbeat_stored_timestamp_seconds
      # 事务速率（commit + rollback）
      - record: job:mysql_transactions:rate5m
        expr: sum without (command) (rate(mysql_global_status_commands_total{command=~"(commit|rollback)"}[5m]))
```

---

## 5.2 告警原理与 Alertmanager 部署

### 5.2.1 告警链路总览

Prometheus 的告警能力分成**两个独立部分**：

1. **Prometheus 端**：定义**告警规则（Alert Rule）**，周期计算表达式；条件满足并持续 `for` 时长后，把告警**发送给 Alertmanager**；
2. **Alertmanager 端**：管理这些告警——**去重、分组、路由、静默、抑制**，最终通过邮件、企业微信、钉钉、Webhook 等渠道发出通知。

数据流向：

![Prometheus 告警链路](/guide/diagrams/alerting-flow.svg)

### 5.2.2 Alertmanager 的五大特性

| 特性 | 作用 |
| --- | --- |
| **去重 Deduplication** | 多个相同告警只保留一条（高可用多实例场景尤其重要） |
| **分组 Grouping** | 把相似告警合并成一条通知。例如一台主机宕机可能同时触发几十条告警，分组后只发一条，避免告警风暴、便于定位 |
| **路由 Route** | 按标签把告警送到不同接收人/媒介（critical 发给管理层、warning 发给运维） |
| **抑制 Inhibition** | 某条告警存在时，压制由它引发的其他告警（主机挂了，就不必再报这台主机上的服务异常） |
| **静默 Silence** | 按标签在指定时间内不发通知，常用于例行维护；在 Web 页面设置 |

### 5.2.3 二进制部署 Alertmanager

在**监控服务器 monitor** 上执行，用户 root。

**第 1 步：下载解压**

```bash
cd /usr/local
wget https://github.com/prometheus/alertmanager/releases/download/v0.34.1/alertmanager-0.34.1.linux-amd64.tar.gz
tar xf alertmanager-0.34.1.linux-amd64.tar.gz
ln -s alertmanager-0.34.1.linux-amd64 alertmanager
cd alertmanager
mkdir -p bin conf data
mv alertmanager amtool bin/
mv alertmanager.yml conf/
```

备选（GitHub）：

```text
https://github.com/prometheus/alertmanager/releases/download/v0.34.1/alertmanager-0.34.1.linux-amd64.tar.gz
```

`amtool` 是 Alertmanager 的命令行工具，可以检查配置、管理静默、查询告警。

**第 2 步：建用户、授权**

```bash
id prometheus &>/dev/null || useradd -r -s /usr/sbin/nologin prometheus
chown -R prometheus:prometheus /usr/local/prometheus/ /usr/local/alertmanager/
```

**第 3 步：创建服务文件**

```bash
cat > /etc/systemd/system/alertmanager.service <<'EOF'
[Unit]
Description=Prometheus Alertmanager
Documentation=https://prometheus.io/docs/alerting/alertmanager/
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=prometheus
Group=prometheus
ExecStart=/usr/local/alertmanager/bin/alertmanager \
  --config.file=/usr/local/alertmanager/conf/alertmanager.yml \
  --storage.path=/usr/local/alertmanager/data \
  --web.listen-address=0.0.0.0:9093 \
  --cluster.listen-address=0.0.0.0:9094
ExecReload=/bin/kill -HUP $MAINPID
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

参数解释：

| 参数 | 作用 |
| --- | --- |
| `--config.file` | 配置文件路径 |
| `--storage.path` | 告警/静默状态存储目录 |
| `--web.listen-address` | Web UI 与 API 端口，默认 9093；**建议显式写 0.0.0.0** |
| `--cluster.listen-address` | 集群 Gossip 通信端口，默认 9094，高可用必用 |

**第 4 步：启动、验证**

```bash
systemctl daemon-reload
systemctl enable --now alertmanager
ss -lntup | grep -E '9093|9094'
```

预期输出：

```text
tcp LISTEN 0 4096 *:9093 *:* users:(("alertmanager",pid=...))
tcp LISTEN 0 4096 *:9094 *:* users:(("alertmanager",pid=...))
udp UNCONN 0 4096 *:9094 *:* users:(("alertmanager",pid=...))
```

9093 是 Web/API 端口，9094 是集群端口（TCP+UDP）。浏览器访问 `http://【监控服务器IP】:9093` 能看到 Alertmanager 界面。

### 5.2.4 Prometheus 对接 Alertmanager

编辑 `/usr/local/prometheus/conf/prometheus.yml` 的 `alerting` 段：

```yaml
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - '【监控服务器IP】:9093'
```

也支持文件发现写法：

```yaml
alerting:
  alertmanagers:
    - file_sd_configs:
        - files:
            - targets/alertmanager*.yaml
```

对应 `/usr/local/prometheus/conf/targets/alertmanager.yaml`：

```yaml
- targets:
    - '【监控服务器IP】:9093'
  labels:
    app: alertmanager
```

检查生效：

```bash
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus
```

建议同时把 Alertmanager 自身纳入监控，在 `scrape_configs` 加：

```yaml
  - job_name: 'alertmanager'
    static_configs:
      - targets: ['【监控服务器IP】:9093']
```

### 5.2.5 Alertmanager 配置文件结构

配置文件路径：`/usr/local/alertmanager/conf/alertmanager.yml`，共**五个模块**：

| 模块 | 作用 |
| --- | --- |
| `global` | 全局配置：SMTP 邮件、企业微信 API、解析超时等 |
| `templates` | 通知模板文件路径 |
| `route` | 路由树根节点，定义分组与默认接收者 |
| `receivers` | 接收者列表，每个接收者配置邮件/微信/Webhook |
| `inhibit_rules` | 抑制规则 |

检查配置文件：

```bash
amtool check-config /usr/local/alertmanager/conf/alertmanager.yml
```

预期输出：

```text
Checking '/usr/local/alertmanager/conf/alertmanager.yml'  SUCCESS
Found:
  - global config
  - route
  - 1 inhibit rules
  - 1 receivers
  - 0 templates
  SUCCESS
```

`global` 段常用参数：

| 参数 | 作用 |
| --- | --- |
| `resolve_timeout` | 多长时间没再收到告警就标记为 resolved（恢复），默认 5m |
| `smtp_smarthost` | SMTP 服务器地址:端口 |
| `smtp_from` | 发件人地址 |
| `smtp_auth_username/password` | SMTP 登录名与授权码 |
| `smtp_require_tls` | 是否要求 TLS，默认 true；用 25 端口非加密时设 false |
| `wechat_api_url` | 企业微信 API 地址 |
| `wechat_api_corp_id` | 企业 ID |
| `wechat_api_secret` | 应用 Secret |

`route` 段常用参数：

| 参数 | 作用 | 推荐值 |
| --- | --- | --- |
| `receiver` | **默认接收者，必填**，否则启动失败 | — |
| `group_by` | 按哪些标签分组，如 `['alertname','cluster']` | — |
| `group_wait` | 首次收到一组告警后等多久再发（等同组其他告警到齐） | 10～30s |
| `group_interval` | 同组新增告警合并通知的最小间隔 | 5m |
| `repeat_interval` | 未恢复告警重复提醒的间隔 | 至少 3h |
| `continue` | 匹配后是否继续匹配后续子路由，默认 false | — |
| `routes` | 子路由列表 | — |

::: warning
`repeat_interval` 不要设得太短（如 10 秒）：邮件渠道发送过于频繁会被 SMTP 服务器拒绝，也会对接收人造成轰炸。生产建议 3～4 小时。
:::

---
## 5.3 告警规则

### 5.3.1 告警规则语法

告警规则与记录规则写在同样的 groups 结构里，一条告警规则由以下部分组成：

```yaml
groups:
  - name: example
    rules:
      - alert: HighRequestLatency          # 告警名称（会成为 alertname 标签）
        expr: job:request_latency_seconds:mean5m{job="myjob"} > 0.5   # 布尔条件表达式
        for: 10m                           # 条件持续多久才真正告警，默认 0
        labels:                            # 附加标签（路由分组靠它）
          severity: warning
          project: myproject
        annotations:                       # 注释信息（通知正文用，不参与匹配）
          summary: "Instance {{ $labels.instance }} 请求延迟过高"
          description: "{{ $labels.instance }} job {{ $labels.job }} 延迟已超过 0.5s 达 10 分钟，当前值 {{ $value }}"
```

字段解释：

| 字段 | 作用 |
| --- | --- |
| `alert` | 告警名称，要能直接表达告警内容 |
| `expr` | PromQL 条件，有结果（条件成立）即为异常 |
| `for` | 条件持续满足这么久才告警；期间状态为 **pending**，之后 **firing**。应大于抓取间隔，避免偶发抖动误报 |
| `labels` | 告警标签，`severity` 是约定俗成的级别标签 |
| `annotations` | 通知里展示的详情；`{{ $labels.x }}` 取标签值，`{{ $value }}` 取触发值 |

表达式太复杂时，建议先用记录规则预计算，告警规则直接引用记录结果，避免实时计算延迟。

社区有大量现成告警规则（强烈推荐参考）：

```text
https://samber.github.io/awesome-prometheus-alerts/
```

**Node Exporter 常用告警规则**（完整版见上面链接，这里给核心几条），创建 `/usr/local/prometheus/rules/node_alert_rules.yml`：

```yaml
groups:
  - name: node-exporter
    rules:
      # 主机宕机（目标采集失败）
      - alert: HostDown
        expr: up{job="node_exporter"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "主机宕机 (instance {{ $labels.instance }})"
          description: "{{ $labels.instance }} 已无法采集超过 1 分钟"

      # 可用内存不足 10%
      - alert: HostOutOfMemory
        expr: node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes * 100 < 10
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "内存不足 (instance {{ $labels.instance }})"
          description: "可用内存低于 10%，当前值 = {{ $value }}"

      # CPU 使用率超过 80%
      - alert: HostHighCpuLoad
        expr: 100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[2m])) * 100) > 80
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "CPU 使用率过高 (instance {{ $labels.instance }})"
          description: "CPU 使用率 > 80%，当前值 = {{ $value }}"

      # CPU iowait 超过 5%（说明磁盘或网络成瓶颈）
      - alert: HostCpuHighIowait
        expr: avg by (instance) (rate(node_cpu_seconds_total{mode="iowait"}[5m])) * 100 > 5
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "CPU iowait 过高 (instance {{ $labels.instance }})"
          description: "iowait > 5%，当前值 = {{ $value }}"

      # 磁盘可用空间不足 10%
      - alert: HostOutOfDiskSpace
        expr: (node_filesystem_avail_bytes * 100) / node_filesystem_size_bytes < 10
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "磁盘空间不足 (instance {{ $labels.instance }})"
          description: "{{ $labels.mountpoint }} 可用空间低于 10%，当前值 = {{ $value }}"

      # conntrack 连接跟踪表使用超过 80%
      - alert: HostConntrackLimit
        expr: node_nf_conntrack_entries / node_nf_conntrack_entries_limit > 0.8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "conntrack 表接近上限 (instance {{ $labels.instance }})"
          description: "连接跟踪条目超过上限的 80%，当前值 = {{ $value }}"
```

### 5.3.2 告警的三种状态

在 Prometheus 的 Alerts 页面可看到：

| 状态 | 含义 |
| --- | --- |
| **Inactive** | 条件未触发，一切正常 |
| **Pending** | 条件已触发，但还没满足 `for` 持续时间，不发通知 |
| **Firing** | 条件触发且持续足够时间，已发送给 Alertmanager |

### 5.3.3 邮件告警案例

**第 1 步：开启邮箱 SMTP 授权码**

在邮箱网页后台开启 SMTP 服务并生成**授权码**（注意是授权码，不是邮箱登录密码）。QQ 邮箱、163 邮箱、企业邮箱后台都有"POP3/SMTP 服务"开关，开启后按提示用手机发短信获取授权码。

**第 2 步：编写告警规则**

创建 `/usr/local/prometheus/rules/flask_alert_rules.yml`：

```yaml
groups:
  - name: flask_web
    rules:
      - alert: InstanceDown
        expr: up{job="my_metric"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Instance {{ $labels.instance }} 停止工作"
          description: "{{ $labels.instance }} job {{ $labels.job }} 已经停止 1 分钟以上"
```

**第 3 步：配置 Alertmanager 邮件**

编辑 `/usr/local/alertmanager/conf/alertmanager.yml`（以 163 邮箱、25 端口非加密为例）：

```yaml
global:
  resolve_timeout: 1m
  smtp_smarthost: 'smtp.163.com:25'
  smtp_from: '【你的发件邮箱】'
  smtp_auth_username: '【你的发件邮箱】'
  smtp_auth_password: '【邮箱授权码】'
  smtp_hello: '163.com'
  smtp_require_tls: false

route:
  group_by: ['alertname', 'cluster']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 3h
  receiver: 'email'

receivers:
  - name: 'email'
    email_configs:
      - to: '【收件邮箱】'
        send_resolved: true
```

参数解释：`send_resolved: true` 表示故障恢复后也发一封标题带 `[Resolved]` 的恢复通知。

检查并重启：

```bash
amtool check-config /usr/local/alertmanager/conf/alertmanager.yml
systemctl restart alertmanager
```

**第 4 步：验证**

停掉 Flask 应用（在 app01 上 `Ctrl+C` 或停止服务），等待 1 分钟以上：

- Prometheus Alerts 页：`InstanceDown` 从 Pending 变 Firing；
- Alertmanager 页面：能看到这条告警；
- 收件邮箱：收到告警邮件；
- 恢复 Flask 后：收到恢复邮件。

::: tip
QQ 邮箱如用 465 端口（SSL），需要保留 TLS 相关配置（`smtp_require_tls: true`）；用 25 端口非加密时设 false。若 25 端口被云厂商封禁（部分云厂商默认封禁 25 端口防垃圾邮件），改用 465/587 端口。
:::

---

## 5.4 告警模板

### 5.4.1 模板说明

默认通知内容较简单，可以用 Go 模板语法自定义通知的标题、正文、表格。模板里可引用：

- `{{ $labels.标签名 }}`：触发告警的标签值；
- `{{ $value }}`：触发数值；
- `.Alerts`：本次通知里的所有告警（Firing/Resolved）；
- `$alert.StartsAt / EndsAt`：开始/恢复时间。

### 5.4.2 邮件表格模板

**第 1 步：创建模板文件** `/usr/local/alertmanager/tmpl/email.tmpl`：

```text
{{ define "test.html" }}
<table border="1">
  <tr>
    <th>报警项</th>
    <th>实例</th>
    <th>报警阈值</th>
    <th>开始时间</th>
  </tr>
  {{ range $i, $alert := .Alerts }}
  <tr>
    <td>{{ index $alert.Labels "alertname" }}</td>
    <td>{{ index $alert.Labels "instance" }}</td>
    <td>{{ index $alert.Annotations "value" }}</td>
    <td>{{ $alert.StartsAt }}</td>
  </tr>
  {{ end }}
</table>
{{ end }}
```

语法解释：`{{ define "名字" }}...{{ end }}` 定义一个可按名字调用的模板；`range` 遍历每条告警；`index $alert.Labels "alertname"` 从标签字典里取 alertname 的值。

**第 2 步：加载并调用模板**，编辑 `alertmanager.yml`：

```yaml
templates:
  - '../tmpl/*.tmpl'

receivers:
  - name: 'email'
    email_configs:
      - to: '【收件邮箱】'
        send_resolved: true
        headers:
          subject: '[WARN] 报警邮件'
        html: '{{ template "test.html" . }}'
```

注意：模板调用 `{{ template ... }}` 要用单引号括住；headers 用字典写法时不要加单引号。

**第 3 步：在告警规则的 annotations 里补 value**（模板里用到了 `Annotations.value`）：

```yaml
        annotations:
          summary: "Instance {{ $labels.instance }} 停止工作"
          description: "{{ $labels.instance }} job {{ $labels.job }} 已经停止 1 分钟以上"
          value: "{{ $value }}"
```

检查生效：

```bash
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus
amtool check-config /usr/local/alertmanager/conf/alertmanager.yml
systemctl restart alertmanager
```

### 5.4.3 更丰富的邮件正文模板

`/usr/local/alertmanager/tmpl/email_full.tmpl`：

```text
{{ define "email.html" }}
{{- if gt (len .Alerts.Firing) 0 -}}
{{ range .Alerts }}
========== start ==========<br>
告警程序: prometheus_alert <br>
告警级别: {{ .Labels.severity }} <br>
告警类型: {{ .Labels.alertname }} <br>
告警主机: {{ .Labels.instance }} <br>
告警主题: {{ .Annotations.summary }} <br>
告警详情: {{ .Annotations.description }} <br>
触发时间: {{ .StartsAt.Format "2006-01-02 15:04:05" }} <br>
========== end ==========<br>
{{ end }}{{ end -}}

{{- if gt (len .Alerts.Resolved) 0 -}}
{{ range .Alerts }}
========== start ==========<br>
告警级别: {{ .Labels.severity }} <br>
告警类型: {{ .Labels.alertname }} <br>
告警主机: {{ .Labels.instance }} <br>
恢复时间: {{ .EndsAt.Format "2006-01-02 15:04:05" }} <br>
========== end ==========<br>
{{ end }}{{ end -}}
{{ end }}
```

::: tip
`"2006-01-02 15:04:05"` 是 Go 语言固定的日期时间格式占位符（可以记成 1月2日 下午3点4分5秒），不要改成别的数字，否则时间显示会错。
:::

---

## 5.5 告警路由

### 5.5.1 路由树说明

`route` 是一棵基于标签匹配的**树**：

- 所有告警从**根路由**进入；根路由必须匹配所有告警，**不能写匹配条件**，它的 `receiver` 是默认接收者；
- 告警依次遍历 `routes` 子路由，遇到第一个匹配的分支就用该分支的接收者（`continue: false`，默认）；
- 设 `continue: true` 则匹配后继续往后匹配，可实现一条告警发往多个渠道。

**新版用 `matchers` 替代了旧的 `match` / `match_re`**。matcher 写法和 PromQL 选择器一致，支持 `=`、`!=`、`=~`、`!~`：

```yaml
route:
  receiver: 'email'
  group_by: ['alertname', 'cluster']
  group_wait: 10s
  group_interval: 5m
  repeat_interval: 3h
  routes:
    - receiver: 'leader-team'
      matchers:
        - severity = "critical"
    - receiver: 'ops-team'
      matchers:
        - severity =~ "warning|info"
```

### 5.5.2 路由案例：不同级别发给不同团队

需求：服务终止（critical）发给管理团队；QPS 异常（warning）发给运维团队；都没匹配则走默认 email。

**第 1 步：告警规则** `/usr/local/prometheus/rules/flask_alert_route.yml`：

```yaml
groups:
  - name: flask_web
    rules:
      - alert: InstanceDown
        expr: up{job="my_metric"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Instance {{ $labels.instance }} 停止工作"
          description: "{{ $labels.instance }} job {{ $labels.job }} 已经停止 1 分钟以上"
          value: "{{ $value }}"

  - name: flask_QPS
    rules:
      - alert: InstanceQPSIsHigh
        expr: increase(request_count_total{job="my_metric"}[1m]) > 500
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Instance {{ $labels.instance }} QPS 持续过高"
          description: "{{ $labels.instance }} job {{ $labels.job }} QPS 持续过高"
          value: "{{ $value }}"
```

**第 2 步：Alertmanager 路由配置**：

```yaml
global:
  resolve_timeout: 5m
  smtp_smarthost: 'smtp.163.com:25'
  smtp_from: '【你的发件邮箱】'
  smtp_auth_username: '【你的发件邮箱】'
  smtp_auth_password: '【邮箱授权码】'
  smtp_require_tls: false

templates:
  - '../tmpl/*.tmpl'

route:
  group_by: ['instance', 'cluster']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 3h
  receiver: 'email'
  routes:
    - receiver: 'leader-team'
      matchers:
        - severity = "critical"
    - receiver: 'ops-team'
      matchers:
        - severity =~ "^(warning)$"

receivers:
  - name: 'email'
    email_configs:
      - to: '【默认收件邮箱】'
        send_resolved: true
        html: '{{ template "test.html" . }}'
        headers:
          subject: '[WARN] 报警邮件'
  - name: 'leader-team'
    email_configs:
      - to: '【管理团队邮箱】'
        send_resolved: true
        html: '{{ template "test.html" . }}'
        headers:
          subject: '[CRITICAL] 应用服务报警邮件'
  - name: 'ops-team'
    email_configs:
      - to: '【运维团队邮箱】'
        send_resolved: true
        html: '{{ template "test.html" . }}'
        headers:
          subject: '[WARNING] QPS 负载报警邮件'
```

检查：

```bash
amtool check-config /usr/local/alertmanager/conf/alertmanager.yml
systemctl restart alertmanager
```

预期输出显示 `Found: ... 3 receivers`。

**第 3 步：验证**

- 停 Flask：critical 命中 leader-team 分支，管理团队收到邮件；
- 制造每分钟超过 500 次访问（把压测脚本循环次数调大）：warning 命中 ops-team；
- 如果把规则里 `severity: critical` 误拼成别的词（如 `criticaL`），所有子路由都匹配不上，告警会走根路由的默认 email——这是排查"该收的人没收到告警"时的一个重要思路。

### 5.5.3 路由嵌套与多渠道

子路由还可以继续嵌套 `routes`，也可以一条告警同时通知多渠道：

```yaml
  routes:
    - receiver: 'multi-channel'
      matchers:
        - job =~ "mysql|java"
      continue: true          # 匹配后继续向下，实现多渠道
      routes:
        - receiver: 'dba-team'
          matchers:
            - job = "mysql"
```

---

## 5.6 告警抑制

### 5.6.1 抑制原理

当 A 服务（被依赖方）故障，依赖它的 B 服务也会异常并触发一堆"连带告警"。抑制规则让"A 的告警存在时，B 的告警不再发"，把注意力集中到真正的根因。

判定逻辑（三要素）：

1. **源告警（source）**：已经存在的、更根本的告警（如主机宕机 critical）；
2. **目标告警（target）**：新产生的、可能由源告警引发的告警；
3. **equal**：源和目标告警在这些标签上的值必须完全相同（确保是同一处业务，避免误抑制）。

新版推荐用 `source_matchers` / `target_matchers`：

```yaml
inhibit_rules:
  - source_matchers:
      - severity = "critical"
    target_matchers:
      - severity = "warning"
    equal: ['instance']
```

含义：同一 instance 上，critical 告警存在时，该 instance 的 warning 告警被抑制。

### 5.6.2 抑制案例

需求：Flask 服务终止（critical）时，不再触发同节点的 QPS 异常（warning）。

**第 1 步：告警规则**（在 5.5.2 基础上增加一条 QPS 为零的 warning 规则）：

```yaml
  - name: flask_QPS
    rules:
      - alert: InstanceQPSIsLow
        expr: up{job="my_metric"} == 0
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Instance {{ $labels.instance }} QPS 异常为零"
          description: "{{ $labels.instance }} job {{ $labels.job }} QPS 异常为 0"
          value: "{{ $value }}"
```

**第 2 步：在 alertmanager.yml 末尾加抑制规则**：

```yaml
inhibit_rules:
  - source_matchers:
      - severity = "critical"
    target_matchers:
      - severity = "warning"
    equal:
      - instance
```

**第 3 步：验证**

```bash
amtool check-config /usr/local/alertmanager/conf/alertmanager.yml
systemctl restart alertmanager
```

停掉 Flask：此时 critical 和 warning 条件同时成立，但因为抑制，只收到 critical 告警，warning 被压制，避免了告警风暴。

::: warning
`equal` 里的标签必须在两类告警上都真实存在且值一致，抑制才会生效。排查"抑制不生效"：先确认源/目标匹配器写对、再确认 equal 标签值完全相同。
:::

---
## 5.7 企业微信告警

### 5.7.1 三种微信告警方式

1. 个人微信号发送（需借助第三方工具，不推荐）；
2. 公众号发送（个人公众号功能受限，可用官方测试接口体验）；
3. **企业微信（企业号）发送——推荐**，注册企业无需认证、免费、接口稳定。

公众号测试接口地址：

```text
https://mp.weixin.qq.com/debug/cgi-bin/sandbox?t=sandbox/login
```

### 5.7.2 企业微信后台准备

**第 1 步：注册企业微信**，访问：

```text
https://work.weixin.qq.com/
```

用个人微信扫码，按提示填写企业信息即可（无需认证、无数量限制）。进入"我的企业"页面，记下**企业 ID（CorpID）**。

**第 2 步：创建部门和人员**

- 在"通讯录"里创建一个告警部门（如"运维部"），点部门名可看到**部门 ID（PartyID，如 2）**；
- 把要接收告警的人加入部门（微信邀请或手动添加）。

**第 3 步：创建自建应用**

"应用管理 → 自建 → 创建应用"，填名称、选可见范围（选刚才的部门）。创建后记下：

- **AgentId**（如 1000004）；
- **Secret**（应用密钥，点"查看"可能需要在企业微信里确认）。

**第 4 步：先用命令行验证接口可用**

获取 access_token：

```bash
curl -H "Content-Type: application/json" \
  -d '{"corpid":"【企业ID】","corpsecret":"【应用Secret】"}' \
  https://qyapi.weixin.qq.com/cgi-bin/gettoken
```

预期输出：

```text
{"errcode":0,"errmsg":"ok","access_token":"一长串token","expires_in":7200}
```

发一条测试消息（token 有效期 2 小时）：

```bash
curl -H "Content-Type: application/json" -d '{
  "toparty": "【部门ID】",
  "msgtype": "text",
  "agentid": "【AgentId】",
  "text": {"content": "PromAlert 告警测试"},
  "safe": "0"
}' "https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=【上一步的token】"
```

预期输出：

```text
{"errcode":0,"errmsg":"ok","msgid":"..."}
```

成员的微信（会在企业微信里，同时可收到微信插件通知）收到测试消息，说明四个关键信息都正确。

### 5.7.3 Alertmanager 配置企业微信

编辑 `/usr/local/alertmanager/conf/alertmanager.yml`：

```yaml
global:
  resolve_timeout: 1m
  wechat_api_url: 'https://qyapi.weixin.qq.com/cgi-bin/'
  wechat_api_corp_id: '【企业ID】'

templates:
  - '../tmpl/*.tmpl'

route:
  group_by: ['instance', 'cluster']
  group_wait: 10s
  group_interval: 5m
  repeat_interval: 3h
  receiver: 'email'
  routes:
    # 只有 critical 才发企业微信，warning 走默认邮件
    - receiver: 'wechat'
      matchers:
        - severity = "critical"

receivers:
  - name: 'email'
    email_configs:
      - to: '【默认收件邮箱】'
        send_resolved: true

  - name: 'wechat'
    wechat_configs:
      - to_party: '【部门ID】'
        # to_user: '@all'   # 也可以发给企业所有人
        agent_id: '【AgentId】'
        api_secret: '【应用Secret】'
        send_resolved: true
        message: '{{ template "wechat.default.message" . }}'
```

字段解释：`to_party` 接收部门；`agent_id` 自建应用 ID；`api_secret` 应用密钥（也可以写在 global 的 `wechat_api_secret`）；`message` 指定消息内容模板。

### 5.7.4 企业微信消息模板

创建 `/usr/local/alertmanager/tmpl/wechat.tmpl`：

```text
{{ define "wechat.default.message" }}
{{- if gt (len .Alerts.Firing) 0 -}}
{{- range $index, $alert := .Alerts -}}
{{- if eq $index 0 }}
========== 监控报警 ==========
告警状态：{{ .Status }}
告警级别：{{ .Labels.severity }}
告警类型：{{ $alert.Labels.alertname }}
故障主机：{{ $alert.Labels.instance }}
告警主题：{{ $alert.Annotations.summary }}
告警详情：{{ $alert.Annotations.description }}
触发阈值：{{ .Annotations.value }}
故障时间：{{ ($alert.StartsAt.Add 28800e9).Format "2006-01-02 15:04:05" }}
========== end ==========
{{- end }}
{{- end }}
{{- end }}
{{- if gt (len .Alerts.Resolved) 0 -}}
{{- range $index, $alert := .Alerts -}}
{{- if eq $index 0 }}
========== 异常恢复 ==========
告警类型：{{ .Labels.alertname }}
告警状态：{{ .Status }}
告警主题：{{ $alert.Annotations.summary }}
告警详情：{{ $alert.Annotations.description }}
故障时间：{{ ($alert.StartsAt.Add 28800e9).Format "2006-01-02 15:04:05" }}
恢复时间：{{ ($alert.EndsAt.Add 28800e9).Format "2006-01-02 15:04:05" }}
实例信息：{{ $alert.Labels.instance }}
========== end ==========
{{- end }}
{{- end }}
{{- end }}
{{- end }}
```

::: tip
企业微信服务器按 UTC 时间处理，模板里 `$alert.StartsAt.Add 28800e9` 是把时间加回 8 小时（28800 秒 = 8 小时），显示成北京时间。`.Add 28800e9` 中 28800e9 是 28800 秒对应的纳秒数。
:::

检查并重启：

```bash
amtool check-config /usr/local/alertmanager/conf/alertmanager.yml
systemctl restart alertmanager
```

验证：停 Flask 触发 critical，企业微信收到格式整齐的告警；恢复后收到恢复通知。高并发触发的 warning 只发邮件、不发微信。

---

## 5.8 钉钉告警

Prometheus 不直接支持钉钉，但 Alertmanager 支持 **Webhook**：用开源的 **prometheus-webhook-dingtalk** 做格式转换（钉钉机器人只接受它自己规定的 JSON 格式）。

### 5.8.1 创建钉钉机器人

**第 1 步：准备钉钉 PC 端**（手机端不能添加机器人），下载页：

```text
https://www.dingtalk.com/
```

注册/登录后创建一个团队组织（右上角"创建企业/组织/团队"，按提示完成）。

**第 2 步：建告警群**：右上角"+"→ 发起群聊 → 选项目群类型，拉入相关同事。

**第 3 步：添加自定义机器人**：群设置 → 智能群助手 → 添加机器人 → 选择"自定义（通过 Webhook 接入自定义服务）"。

**第 4 步：安全设置（三选一或组合）**：

| 安全方式 | 说明 |
| --- | --- |
| 自定义关键词 | 消息必须包含指定词（如 `PromAlert`），最简单 |
| 加签 | 每次请求带时间戳和 HMAC-SHA256 签名，**最安全，推荐** |
| IP 地址段 | 只接受指定出口 IP |

创建完成后**务必保存 Webhook 地址**（含 access_token）：

```text
https://oapi.dingtalk.com/robot/send?access_token=【你的token】
```

### 5.8.2 先用命令验证机器人

只用关键词时：

```bash
WEBHOOK_URL="https://oapi.dingtalk.com/robot/send?access_token=【你的token】"
curl -H "Content-Type: application/json" \
  -d '{"msgtype":"text","text":{"content":"PromAlert - 钉钉告警测试"}}' \
  ${WEBHOOK_URL}
```

预期输出：

```text
{"errcode":0,"errmsg":"ok"}
```

消息不含关键词时会被拒绝：

```text
{"errcode":310000,"errmsg":"keywords not in content"}
```

**加签方式**：需要先用 Secret（以 `SEC` 开头）生成时间戳和签名。Python 脚本 `/usr/local/bin/create_dingtalk_sign.py`：

```python
#!/usr/bin/python3
import time, hmac, hashlib, base64
import urllib.parse

timestamp = str(round(time.time() * 1000))
secret = '【你的加签Secret，SEC开头】'
secret_enc = secret.encode('utf-8')

string_to_sign = '{}\n{}'.format(timestamp, secret)
string_to_sign_enc = string_to_sign.encode('utf-8')

hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))

print("Timestamp:", timestamp)
print("Sign:", sign)
```

运行：

```bash
python3 /usr/local/bin/create_dingtalk_sign.py
```

预期输出：

```text
Timestamp: 1770000000000
Sign: KAHQEy%2BV7mbs5oaEuXX%2FlBaimtGEQar5un2YgeYv7Dw%3D
```

把时间戳、签名拼到 Webhook 地址后即可发送（签名有有效期，需现取现用）：

```bash
curl -H 'Content-Type: application/json' -d '{
  "msgtype": "markdown",
  "markdown": {
    "title": "PromAlert 告警信息",
    "text": "## 问题详情 \n### 问题级别：严重 \n### 问题类型：MySQL 服务"
  }
}' "https://oapi.dingtalk.com/robot/send?access_token=【你的token】&timestamp=【时间戳】&sign=【签名】"
```

### 5.8.3 部署 prometheus-webhook-dingtalk

在**监控服务器 monitor** 上执行，用户 root。

**第 1 步：下载安装**

```bash
cd /usr/local
wget https://github.com/timonwong/prometheus-webhook-dingtalk/releases/download/v2.1.0/prometheus-webhook-dingtalk-2.1.0.linux-amd64.tar.gz
tar xf prometheus-webhook-dingtalk-2.1.0.linux-amd64.tar.gz
ln -s prometheus-webhook-dingtalk-2.1.0.linux-amd64 dingtalk
cd dingtalk
mkdir -p bin conf
mv prometheus-webhook-dingtalk bin/
cp config.example.yml conf/config.yml
```

GitHub 下载慢时，在前面加 GitHub 代理前缀（如 `https://ghproxy.net/`、`https://gh-proxy.com/`，代理可能变动）。

**第 2 步：配置钉钉目标**，编辑 `/usr/local/dingtalk/conf/config.yml`：

```yaml
## 请求超时
timeout: 5s

## 自定义模板路径（可选）
templates:
  - contrib/templates/dingtalk.tmpl

## 默认消息使用自定义模板（可选）
default_message:
  title: '{{ template "_ding.link.title" . }}'
  text: '{{ template "_ding.link.content" . }}'

## 目标（钉钉机器人），可配多个（webhook1、webhook2……）
targets:
  webhook1:
    url: https://oapi.dingtalk.com/robot/send?access_token=【你的钉钉token】
    # 加签 Secret（用关键词安全方式时此行可省）
    secret: 【你的加签Secret，SEC开头】
```

**第 3 步：创建服务文件**

```bash
cat > /etc/systemd/system/dingtalk-webhook.service <<'EOF'
[Unit]
Description=Prometheus Webhook DingTalk
After=network-online.target

[Service]
Type=simple
User=prometheus
Group=prometheus
ExecStart=/usr/local/dingtalk/bin/prometheus-webhook-dingtalk \
  --config.file=/usr/local/dingtalk/conf/config.yml \
  --web.listen-address=0.0.0.0:8060
ExecReload=/bin/kill -HUP $MAINPID
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
chown -R prometheus:prometheus /usr/local/dingtalk/
systemctl daemon-reload
systemctl enable --now dingtalk-webhook
ss -lntp | grep 8060
```

参数解释：`--web.listen-address` 是 webhook 接收地址端口（默认 8060）；Alertmanager 会把告警 POST 到 `http://【监控服务器IP】:8060/dingtalk/webhook1/send`。

**第 4 步：手工测试 webhook**

```bash
curl "http://localhost:8060/dingtalk/webhook1/send" \
  -H 'Content-Type: application/json' -d '{
    "msgtype": "markdown",
    "markdown": {
      "title": "PromAlert 告警信息",
      "text": "## 问题详情 \n### 问题级别：严重 \n### 问题类型：测试"
    }
  }'
```

预期输出：`OK`，钉钉群收到消息。

如果钉钉机器人同时设置了"自定义关键词"而消息里没有，日志报：

```text
msg="Failed to send notification to DingTalk" respCode=310000 respMsg="keywords not in content"
```

::: tip
使用 prometheus-webhook-dingtalk 时，安全设置建议**只用加签**（插件生成的消息不一定包含你的关键词）；若一定要用关键词，要保证模板里每条消息都带该词（如把关键词写进固定标题）。
:::

### 5.8.4 Alertmanager 对接钉钉

编辑 `alertmanager.yml`，增加接收者与路由：

```yaml
route:
  receiver: 'email'
  routes:
    - receiver: 'dingtalk'
      matchers:
        - severity = "critical"

receivers:
  - name: 'email'
    email_configs:
      - to: '【默认收件邮箱】'
        send_resolved: true

  - name: 'dingtalk'
    webhook_configs:
      - url: 'http://【监控服务器IP】:8060/dingtalk/webhook1/send'
        send_resolved: true
```

检查生效：

```bash
amtool check-config /usr/local/alertmanager/conf/alertmanager.yml
systemctl restart alertmanager
```

验证：停 Flask，钉钉群收到告警卡片；恢复后收到恢复通知。

### 5.8.5 自定义钉钉模板（带图标、分区展示）

**第 1 步：准备两张全网可访问的图标**（放自己的网站/对象存储，如七牛云、阿里 OSS）：

```text
http://【你的图标域名】/images/ERROR.png
http://【你的图标域名】/images/OK.png
```

**第 2 步：创建模板** `/usr/local/dingtalk/contrib/templates/dingtalk.tmpl`：

```text
{{ define "__subject" }}[{{ .Status | toUpper }}{{ if eq .Status "firing" }}:{{ .Alerts.Firing | len }}{{ end }}] {{ .GroupLabels.SortedPairs.Values | join " " }}{{ end }}
{{ define "__alertmanagerURL" }}{{ .ExternalURL }}/#/alerts?receiver={{ .Receiver }}{{ end }}

{{ define "___text_alert_list" }}{{ range . }}
---
**告警主题：** {{ .Labels.alertname | upper }}
**告警级别：** {{ .Labels.severity | upper }}
**触发时间：** {{ dateInZone "2006-01-02 15:04:05" (.StartsAt) "Asia/Shanghai" }}
**事件信息：** {{ range .Annotations.SortedPairs }} {{ .Value | markdown | html }} {{ end }}
**事件标签：**
{{ range .Labels.SortedPairs }}{{ if and (ne (.Name) "severity") (ne (.Name) "team") }}> - {{ .Name }}: {{ .Value | markdown | html }}
{{ end }}{{ end }}
{{ end }}{{ end }}

{{ define "___text_resolve_list" }}{{ range . }}
---
**告警主题：** {{ .Labels.alertname | upper }}
**告警级别：** {{ .Labels.severity | upper }}
**触发时间：** {{ dateInZone "2006-01-02 15:04:05" (.StartsAt) "Asia/Shanghai" }}
**结束时间：** {{ dateInZone "2006-01-02 15:04:05" (.EndsAt) "Asia/Shanghai" }}
**事件信息：** {{ range .Annotations.SortedPairs }} {{ .Value | markdown | html }} {{ end }}
{{ end }}{{ end }}

{{ define "_default.content" }}
[{{ .Status | toUpper }}{{ if eq .Status "firing" }}:{{ .Alerts.Firing | len }}{{ end }}] **[{{ index .GroupLabels "alertname" }}]({{ template "__alertmanagerURL" . }})**
{{ if gt (len .Alerts.Firing) 0 -}}
![警报图标](http://【你的图标域名】/images/ERROR.png)
**======== PromAlert 告警触发 ========**
{{ template "___text_alert_list" .Alerts.Firing }}
{{- end }}
{{ if gt (len .Alerts.Resolved) 0 -}}
![恢复图标](http://【你的图标域名】/images/OK.png)
**======== PromAlert 告警恢复 ========**
{{ template "___text_resolve_list" .Alerts.Resolved }}
{{- end }}
{{ end }}
{{ define "_default.title" }}{{ template "__subject" . }}{{ end }}
{{ define "_ding.link.title" }}{{ template "_default.title" . }}{{ end }}
{{ define "_ding.link.content" }}{{ template "_default.content" . }}{{ end }}
```

**第 3 步：确认 config.yml 已加载该模板**（即 5.8.3 第 2 步的 templates 与 default_message 配置），重启：

```bash
systemctl restart dingtalk-webhook
```

触发告警后，钉钉消息会带图标、按分区展示级别/时间/标签，恢复消息带 OK 图标。

---

## 5.9 Alertmanager 高可用

### 5.9.1 Gossip 协议原理

- **是什么**：Alertmanager 内置 **Gossip（流言）协议**，多个实例之间通过它同步告警、静默、通知状态。
- **为什么需要**：如果多台 Alertmanager 各自收到相同告警，没有状态同步就会**重复发送通知**；Gossip 保证同一条告警最终只发一次。
- **工作方式**：类似流言传播——节点把状态随机告诉其他节点，其他节点再继续传播，最终集群所有节点状态收敛一致；有 Push（主动推状态）和 Pull（主动询问新状态）两种方式。

### 5.9.2 关键启动参数

| 参数 | 作用 |
| --- | --- |
| `--web.listen-address` | 本实例 Web 端口（默认 9093） |
| `--cluster.listen-address` | Gossip 集群通信地址（默认 9094），**集群必配** |
| `--cluster.peer` | 加入集群时指向**已有节点**的集群地址（首个节点不填，后续节点必填） |
| `--cluster.peer-timeout` | 连接对端超时 |

### 5.9.3 跨主机两节点集群

**节点 A（第一台，监控服务器）**：

```bash
alertmanager \
  --web.listen-address=":9093" \
  --cluster.listen-address=":9094" \
  --config.file=/usr/local/alertmanager/conf/alertmanager.yml \
  --storage.path=/usr/local/alertmanager/data
```

**节点 B（第二台主机）**，启动时 peer 指向节点 A：

```bash
alertmanager \
  --web.listen-address=":9093" \
  --cluster.listen-address=":9094" \
  --cluster.peer=【节点A的IP】:9094 \
  --config.file=/usr/local/alertmanager/conf/alertmanager.yml \
  --storage.path=/usr/local/alertmanager/data
```

两台机器的 `alertmanager.yml` 内容保持一致（通知状态靠 Gossip 同步）。

**Prometheus 同时把两个 Alertmanager 都写上**：

```yaml
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - '【节点A的IP】:9093'
            - '【节点B的IP】:9093'
```

### 5.9.4 单机多实例（学习/测试用）

实例 A1：

```bash
alertmanager --web.listen-address=":9093" \
  --cluster.listen-address="127.0.0.1:8001" \
  --config.file=/usr/local/alertmanager/conf/alertmanager.yml \
  --storage.path=/data/alertmanager/
```

实例 A2：

```bash
alertmanager --web.listen-address=":9094" \
  --cluster.listen-address="127.0.0.1:8002" \
  --cluster.peer=127.0.0.1:8001 \
  --config.file=/usr/local/alertmanager/conf/alertmanager.yml \
  --storage.path=/data/alertmanager2/
```

### 5.9.5 Docker Compose 三节点集群

```yaml
version: '3.6'

networks:
  monitoring:
    driver: bridge

volumes:
  am01_data: {}
  am02_data: {}
  am03_data: {}

services:
  alertmanager01:
    image: prom/alertmanager:v0.34.1
    restart: always
    volumes:
      - ./alertmanager/:/etc/alertmanager/
      - am01_data:/alertmanager
    networks:
      - monitoring
    ports:
      - "9093:9093"
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
      - '--cluster.listen-address=0.0.0.0:9094'
      - '--cluster.peer-timeout=15s'

  alertmanager02:
    image: prom/alertmanager:v0.34.1
    restart: always
    volumes:
      - ./alertmanager/:/etc/alertmanager/
      - am02_data:/alertmanager
    networks:
      - monitoring
    ports:
      - "19093:9093"
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
      - '--cluster.listen-address=0.0.0.0:9094'
      - '--cluster.peer=alertmanager01:9094'
      - '--cluster.peer-timeout=15s'

  alertmanager03:
    image: prom/alertmanager:v0.34.1
    restart: always
    volumes:
      - './alertmanager/:/etc/alertmanager/'
      - am03_data:/alertmanager
    networks:
      - monitoring
    ports:
      - "29093:9093"
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
      - '--cluster.listen-address=0.0.0.0:9094'
      - '--cluster.peer=alertmanager01:9094'
      - '--cluster.peer-timeout=15s'
```

Prometheus 端 targets 写三个：`【监控服务器IP】:9093`、`【监控服务器IP】:19093`、`【监控服务器IP】:29093`。

验证：在任一 Alertmanager 页面 Status → Cluster Info 能看到 3 个成员；创建一个静默，几秒后会同步到其他实例；触发告警只收到一次通知。

::: warning
生产建议：① Alertmanager 至少部署 2 个实例（奇数个更利于投票，常用 3 个）；② Prometheus 自身的高可用是"双机采同样的目标 + external_labels 加 replica 标签 + 远程存储去重"，注意区分 Alertmanager HA 与 Prometheus HA；③ 各实例配置要保持一致。
:::

---

## 5.10 一体化告警平台 PrometheusAlert（可选了解）

PrometheusAlert 是国产开源的一体化告警中心，内置钉钉、企业微信、飞书、邮件等模板，带 Web 管理界面。项目地址：

```text
https://github.com/feiyu563/PrometheusAlert
```

Docker 快速体验：

```bash
docker run -d \
  -p 8080:8080 \
  -e PA_LOGIN_USER=prometheusalert \
  -e PA_LOGIN_PASSWORD=prometheusalert \
  -e PA_TITLE=PrometheusAlert \
  -e PA_OPEN_FEISHU=1 \
  -e PA_OPEN_DINGDING=1 \
  -e PA_OPEN_WEIXIN=1 \
  feiyu563/prometheus-alert:v5.0.0
```

浏览器访问 `http://【监控服务器IP】:8080`，默认用户名/密码 `prometheusalert/prometheusalert`。生产使用请固定镜像版本、改默认密码，并按其文档把 Alertmanager 的 webhook 指向它。

---

## 本阶段命令速查表

```bash
# === 记录规则 ===
vim /usr/local/prometheus/rules/xxx_record_rules.yml
promtool check rules /usr/local/prometheus/rules/xxx_record_rules.yml
# prometheus.yml: rule_files 加 "../rules/*.yml"，然后：
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus

# === Alertmanager ===
# 下载（GitHub，慢则在链接前加 https://ghproxy.net/）
wget https://github.com/prometheus/alertmanager/releases/download/v0.34.1/alertmanager-0.34.1.linux-amd64.tar.gz
# 服务文件见 5.2.3，然后：
systemctl daemon-reload
systemctl enable --now alertmanager
amtool check-config /usr/local/alertmanager/conf/alertmanager.yml
systemctl restart alertmanager

# === 钉钉插件 ===
# 下载（GitHub，慢则加 https://ghproxy.net/ 前缀）
wget https://github.com/timonwong/prometheus-webhook-dingtalk/releases/download/v2.1.0/prometheus-webhook-dingtalk-2.1.0.linux-amd64.tar.gz
# 服务文件见 5.8.3，然后：
systemctl enable --now dingtalk-webhook

# === 企业微信 token 验证 ===
curl -H "Content-Type: application/json" -d '{"corpid":"【企业ID】","corpsecret":"【应用Secret】"}' https://qyapi.weixin.qq.com/cgi-bin/gettoken
```

---

## 本阶段常见坑与解决

**坑 1：告警一直 Pending 不变 Firing**

- 现象：告警页面状态停在 Pending，Alertmanager 收不到。
- 原因：`for` 时间没到；或故障时好时坏、条件没有"持续"满足，计时不断被重置。
- 解决：确认 `for` 时长并等待；排查目标是否抖动（看抓取间隔、网络稳定性）。

**坑 2：Alertmanager 启动失败**

- 报错原样：`level=fatal ... root route must have a receiver`；或 `failed to parse configuration file: yaml: ...`。
- 原因：根路由没写 receiver；YAML 语法错误。
- 解决：根路由补 `receiver`；`amtool check-config` 定位错误后修正。

**坑 3：该收告警的人没收到（子路由没匹配）**

- 现象：告警存在，但指定团队没收到，被默认接收者接走。
- 原因：matcher 标签值拼错（大小写敏感，如 critical 拼成 criticaL）；标签根本没出现在告警上。
- 解决：核对告警规则 labels 与路由 matchers 完全一致；在 Alertmanager 页面看告警实际标签。

**坑 4：钉钉/企业微信收不到消息**

- 报错原样：钉钉 `respCode=310000 respMsg="keywords not in content"`；企业微信 `{"errcode":40014,"errmsg":"invalid access_token"}`。
- 原因：消息不含关键词/签名错误；token 过期（2 小时）或 corpid/secret 错误。
- 解决：钉钉改用加签或保证消息含关键词；微信重新获取 token、核对企业 ID 与应用 Secret。

**坑 5：高可用下重复收到告警**

- 现象：同一条告警被发送多次。
- 原因：实例间 Gossip 没连通（9094 端口未放通、peer 地址写错）。
- 解决：检查 `--cluster.listen-address`、`--cluster.peer`；放通 9094 TCP/UDP；Status → Cluster Info 确认成员到齐。

**坑 6：抑制规则不生效**

- 现象：critical 存在，warning 仍发出来。
- 原因：source/target 匹配器不对，或 equal 标签值不一致。
- 解决：amtool 检查配置；确认两类告警 equal 标签（如 instance）值完全相同。

**坑 7：静默设置后所有告警都不发/静默不生效**

- 现象：设置静默后范围过大；或多实例间静默没同步。
- 原因：静默匹配条件写太宽；Gossip 未同步。
- 解决：精确指定静默标签；维护结束及时删除静默（Expire 时间不要设太长）；确认集群同步正常。

**坑 8：邮件发不出去**

- 报错原样：`dial tcp smtp.163.com:25: i/o timeout` 或 `535 Error: authentication failed`。
- 原因：25 端口被云厂商封禁；授权码错误。
- 解决：改用 465（SSL，保留 TLS）或 587；重新生成并核对授权码。

---
# 阶段六：服务发现

## 阶段目标

- 理解为什么静态配置在大规模、动态环境下不够用；
- 掌握**文件、DNS、Consul、Kubernetes API** 四种服务发现；
- 会用 Consul 注册服务并让 Prometheus 自动纳入监控。

## 6.1 服务发现原理

- **是什么**：服务发现让 Prometheus 不再依赖手写的 `static_configs` 目标列表，而是从**服务注册中心**自动获取、检测、分类目标，目标变动（新增、下线）也能自动更新。
- **类比**：静态配置像把朋友电话手抄在本子上，换号了就得手动改；服务发现像通讯录 App，朋友换号自动同步。
- **为什么需要**：Pull 模型必须先知道每个目标的位置。小环境手抄没问题；中大型、云环境里实例频繁增删，静态配置维护不过来。

Prometheus 提供二十多种发现机制，常用的：

| 方式 | 说明 |
| --- | --- |
| 静态服务发现 | `static_configs` 手写 `ip:port` |
| 文件服务发现 | 目标写在 YAML/JSON 文件里，Prometheus 周期重读 |
| DNS 服务发现 | 定期查询一组 DNS 域名（A/AAAA/SRV 记录）发现目标 |
| Consul 服务发现 | 基于 Consul 注册中心动态发现 |
| HTTP 服务发现 | 从返回 static_config 列表的 HTTP 端点（JSON）获取目标，便于接入自定义发现 |
| Kubernetes API 发现 | 把 Node、Service、Endpoint、Pod、Ingress 等资源对象作为目标 |

发现原理分三步：

1. 配置处理模块按 `scrape_configs` 的发现协议生成对应的 Discoverer，各自去发现目标，放入目标列表；
2. DiscoveryManager 每 5 秒检查一次目标列表，有变更就放进同步消息池；
3. scrape 组件监听消息池，reload 后把新目标纳入抓取。

---

## 6.2 文件服务发现

- **是什么**：目标写在 YAML/JSON 文件中，Prometheus 定期重读；不依赖任何平台或第三方，是最简单通用的动态发现。
- **文件来源**：可手写，也可由 Ansible/SaltStack 等配置管理工具、或基于 CMDB 的脚本生成。
- **注意**：不要在原文件上直接边写边存（Prometheus 可能读到写了一半的文件）；正确做法是先写到临时文件再 `mv` 原子替换。

**第 1 步：建目录**

```bash
mkdir -p /usr/local/prometheus/conf/targets
```

**第 2 步：创建目标文件**

`/usr/local/prometheus/conf/targets/prometheus-server.yml`：

```yaml
- targets:
    - '【监控服务器IP】:9090'
  labels:
    app: prometheus-server
    job: prometheus-server
```

`/usr/local/prometheus/conf/targets/node.yml`：

```yaml
- targets:
    - '【监控服务器IP】:9100'
  labels:
    app: prometheus
    job: prometheus
- targets:
    - '【Web服务器IP】:9100'
    - '【应用服务器IP】:9100'
    - '【数据库服务器IP】:9100'
  labels:
    app: node-exporter
    job: node
```

`/usr/local/prometheus/conf/targets/flask.yml`：

```yaml
- targets:
    - '【应用服务器IP】:8000'
  labels:
    app: flask-web
    job: my_metric
```

**第 3 步：在 prometheus.yml 配置发现**

```yaml
scrape_configs:
  - job_name: 'file_sd_prometheus'
    scrape_interval: 10s
    file_sd_configs:
      - files:
          - targets/prometheus-server.yml
        refresh_interval: 10s

  - job_name: 'file_sd_node'
    file_sd_configs:
      - files:
          - targets/node.yml
        refresh_interval: 10s

  - job_name: 'file_sd_flask'
    file_sd_configs:
      - files:
          - targets/flask.yml
        refresh_interval: 10s
```

参数解释：`files` 要加载的文件列表，支持 glob 通配符（如 `targets/*.yml`），相对路径相对于 prometheus.yml 所在目录；`refresh_interval` 重读间隔，默认 5m。

**第 4 步：检查生效**

```bash
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus
```

验证：Targets 页所有目标出现，且带文件里定义的标签。文件发现会自动附加元标签 `__meta_filepath`（文件完整路径），可在 relabel 中使用。

**第 5 步：体验动态增删**

编辑 `node.yml`，加一行新主机（如 `'【新主机IP】:9100'`），保存后等一个 refresh 周期，无需重启 Prometheus，新目标自动出现；删掉某行，目标自动消失。

**JSON 格式**（等价写法，更适合程序生成），`targets/node.json`：

```json
[
  {
    "targets": ["【监控服务器IP】:9100"],
    "labels": {"app": "prometheus", "job": "prometheus"}
  },
  {
    "targets": ["【Web服务器IP】:9100", "【应用服务器IP】:9100"],
    "labels": {"app": "node-exporter", "job": "node"}
  }
]
```

YAML 转 JSON 可用 `jq`、在线工具或 Python，注意 JSON 里字段是 `targets`（带 s）。

---

## 6.3 DNS 服务发现

- **是什么**：定期查询一组 DNS 域名来发现目标，依赖 A、AAAA、SRV 记录；用哪台 DNS 由 Prometheus 服务器的 `/etc/resolv.conf` 决定。
- **SRV 记录**：服务资源记录，说明"某个域名下有哪些服务器、端口、优先级"，格式 `_<服务>._<协议>.<域名> TTL IN SRV 优先级 权重 端口 目标主机`。一条 SRV 记录可对应多台主机，便于批量发现。

### 6.3.1 部署 DNS（BIND）

在一台主机（可用监控服务器兼任）执行，用户 root：

```bash
apt update && apt -y install bind9 bind9utils bind9-doc bind9-host
named -v
```

**配置正向区域**，追加到 `/etc/bind/named.conf.default-zones`：

```text
zone "magedu.com" {
    type master;
    file "/etc/bind/magedu.com.zone";
};
```

**创建区域文件** `/etc/bind/magedu.com.zone`：

```text
$TTL 604800
@   IN  SOA ns.magedu.com. admin.magedu.com. (
            1        ; Serial（每次修改加 1）
            604800   ; Refresh
            86400    ; Retry
            2419200  ; Expire
            604800 )  ; Negative Cache TTL
    IN  NS  master
master  IN  A   【DNS服务器IP】
node1   IN  A   【Web服务器IP】
node2   IN  A   【应用服务器IP】
node3   IN  A   【数据库服务器IP】
flask   IN  A   【应用服务器IP】
```

检查并生效：

```bash
named-checkconf
named-checkzone magedu.com /etc/bind/magedu.com.zone
rndc reload
systemctl restart named
```

让 Prometheus 服务器使用这台 DNS（netplan 示例 `/etc/netplan/01-netcfg.yaml`）：

```yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    eth0:
      addresses:
        - 【监控服务器IP】/24
      routes:
        - to: default
          via: 【网关IP】
      nameservers:
        addresses: [【DNS服务器IP】]
```

应用并验证解析：

```bash
netplan apply
dig node1.magedu.com
host node1.magedu.com
```

### 6.3.2 配置 SRV 记录

在 `/etc/bind/magedu.com.zone` 追加（对应上面的 A 记录，端口 9100 是 node_exporter）：

```text
_prometheus._tcp.magedu.com. 1H IN SRV 10 10 9100 node1.magedu.com.
_prometheus._tcp.magedu.com. 1H IN SRV 10 10 9100 node2.magedu.com.
_prometheus._tcp.magedu.com. 1H IN SRV 10 10 9100 node3.magedu.com.
```

字段：`10` 优先级（小的优先）、`10` 权重（同优先级按权重分流）、`9100` 端口、最后是目标主机名。生效：

```bash
rndc reload
host -t srv _prometheus._tcp.magedu.com
```

预期输出：

```text
_prometheus._tcp.magedu.com has SRV record 10 10 9100 node1.magedu.com.
_prometheus._tcp.magedu.com has SRV record 10 10 9100 node2.magedu.com.
_prometheus._tcp.magedu.com has SRV record 10 10 9100 node3.magedu.com.
```

### 6.3.3 Prometheus 使用 DNS 发现

```yaml
scrape_configs:
  # 单个主机：用 A 记录，需显式指定端口
  - job_name: 'dns_sd_flask'
    dns_sd_configs:
      - names: ['flask.magedu.com']
        type: A
        port: 8000
        refresh_interval: 10s

  # 批量主机：用 SRV 记录（端口从记录里取）
  - job_name: 'dns_sd_node'
    dns_sd_configs:
      - names: ['_prometheus._tcp.magedu.com']
        refresh_interval: 10s
```

参数解释：`names` 要查询的域名列表；`type` 记录类型，默认 SRV（可选 A、AAAA）；非 SRV 时用 `port` 指定端口；`refresh_interval` 默认 30s。

检查生效：

```bash
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus
```

增删 SRV/A 记录后，Ubuntu 有本地 DNS 缓存，必要时清缓存：

```bash
systemctl restart systemd-resolved.service
rndc reload
```

---

## 6.4 Consul 服务发现

### 6.4.1 Consul 简介

- **是什么**：Consul 是一个服务发现与配置工具，提供服务注册、健康检查、KV 存储、多数据中心支持，自带 Web UI。
- **类比**：微服务互相找不到对方，Consul 就是"公司前台+通讯录"，每个服务报到登记，要找谁问前台，前台还会定期确认人还在不在（健康检查）。
- **为什么需要**：微服务拆分后服务间跨进程、跨机房通信，需要知道对方位置、避开不健康副本。

**关键概念**：

| 概念 | 说明 |
| --- | --- |
| Agent | 每个节点上常驻的守护进程，分 **Client** 和 **Server** 两种模式 |
| Client | 不保存数据，转发 RPC 给 Server，相对无状态 |
| Server | 参与 Raft 选举、维护集群状态与数据；单数据中心建议 3～5 个 |
| Raft | 强一致性协议，保证 Server 间服务注册信息、KV 数据同步与 Leader 选举 |
| Gossip | 节点间成员发现、健康检查、状态广播（最终一致），LAN 池用于机房内、WAN 池跨机房 |

Consul 端口：

| 端口 | 用途 |
| --- | --- |
| 8500 | HTTP API 与 Web UI |
| 8300 | Server RPC（同数据中心 Server 间） |
| 8301 | Serf LAN（同机房节点通信） |
| 8302 | Serf WAN（跨机房 Server 通信） |
| 8600 | DNS 服务 |

### 6.4.2 部署 Consul

**方式 1：官方仓库安装（Ubuntu）**

```bash
wget -O - https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/hashicorp.list
apt update && apt -y install consul
consul version
```

RHEL 系：

```bash
yum install -y yum-utils
yum-config-manager --add-repo https://rpm.releases.hashicorp.com/RHEL/hashicorp.repo
yum -y install consul
```

**方式 2：二进制安装（推荐，版本可控）**

```bash
cd /usr/local
CONSUL_VERSION=1.22.7
wget https://releases.hashicorp.com/consul/${CONSUL_VERSION}/consul_${CONSUL_VERSION}_linux_amd64.zip
apt -y install unzip
unzip consul_${CONSUL_VERSION}_linux_amd64.zip -d /usr/local/bin/
consul version
```

准备用户、目录：

```bash
id consul &>/dev/null || useradd -r -s /usr/sbin/nologin consul
mkdir -p /data/consul /etc/consul.d
chown -R consul:consul /data/consul /etc/consul.d
```

创建服务文件（单机 Server，注意把 bind 改成本机 IP）：

```bash
cat > /etc/systemd/system/consul.service <<'EOF'
[Unit]
Description="HashiCorp Consul"
Documentation=https://developer.hashicorp.com/consul/docs
Requires=network-online.target
After=network-online.target

[Service]
Type=simple
User=consul
Group=consul
ExecStart=/usr/local/bin/consul agent -server -bind=【监控服务器IP】 -client=0.0.0.0 -ui -bootstrap-expect=1 -data-dir=/data/consul -node=consul -config-dir=/etc/consul.d
KillMode=process
Restart=on-failure
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable --now consul
ss -lntup | grep -E '8500|8600'
```

参数解释：

| 参数 | 作用 |
| --- | --- |
| `-server` | 以 Server 模式运行（否则是 Client） |
| `-bind` | 集群内部通信地址，多网卡必须显式指定 |
| `-client` | HTTP/DNS/RPC 监听地址，默认 127.0.0.1，要对外提供改 0.0.0.0 |
| `-ui` | 启用内置 Web UI（8500） |
| `-bootstrap-expect` | 期望的 Server 数量，达到后才引导集群；单机设 1 |
| `-data-dir` | 状态数据目录 |
| `-node` | 节点名，集群内唯一 |
| `-config-dir` | 配置目录，加载其中 .json/.hcl 文件 |

浏览器访问 `http://【监控服务器IP】:8500` 能看到 Consul UI。

**方式 3：Docker / Compose**

```bash
docker run -d --name consul --restart=always -p 8500:8500 \
  hashicorp/consul:1.22 agent -server -client=0.0.0.0 -bootstrap-expect=1 -ui
```

### 6.4.3 Consul 集群（了解）

3 个 Server 节点时，第一个节点：

```bash
consul agent -server -bind=【节点1IP】 -client=0.0.0.0 -ui -bootstrap -data-dir=/data/consul -node=node1
```

第二、三个节点（用 `-retry-join` 加入，`-bootstrap-expect 3`）：

```bash
consul agent -server -bind=【节点2IP】 -client=0.0.0.0 -retry-join=【节点1IP】 -bootstrap-expect=3 -data-dir=/data/consul -node=node2
consul agent -server -bind=【节点3IP】 -client=0.0.0.0 -retry-join=【节点1IP】 -bootstrap-expect=3 -data-dir=/data/consul -node=node3
```

查看成员：

```bash
consul members
```

预期输出：

```text
Node    Address          Status  Type    Build    Protocol  DC   Partition  Segment
node1   【节点1IP】:8301  alive   server  1.22.7   2         dc1  default    <all>
node2   【节点2IP】:8301  alive   server  1.22.7   2         dc1  default    <all>
node3   【节点3IP】:8301  alive   server  1.22.7   2         dc1  default    <all>
```

### 6.4.4 注册与注销服务

**HTTP API 方式**，注册 node1 上的 node_exporter：

```bash
curl -X PUT -d '{
  "id": "node1-exporter",
  "name": "node-exporter",
  "address": "【Web服务器IP】",
  "port": 9100,
  "tags": ["node"],
  "checks": [{"http": "http://【Web服务器IP】:9100/metrics", "interval": "5s"}]
}' http://【监控服务器IP】:8500/v1/agent/service/register
```

也可把 JSON 存成文件再注册：

```bash
curl -X PUT --data @nodes.json http://【监控服务器IP】:8500/v1/agent/service/register
```

健康检查会定期访问 `http://【Web服务器IP】:9100/metrics`，检查失败服务标记为不健康。

**命令行方式**，`node1.json`：

```json
{
  "service": {
    "id": "node1-exporter",
    "name": "node-exporter",
    "address": "node1.magedu.com",
    "port": 9100,
    "tags": ["node"],
    "checks": [{"http": "http://node1.magedu.com:9100/metrics", "interval": "5s"}]
  }
}
```

注册/注销：

```bash
consul services register node1.json
consul services deregister -id node1-exporter
```

HTTP API 注销：

```bash
curl -X PUT http://【监控服务器IP】:8500/v1/agent/service/deregister/node1-exporter
```

常用查询 API：

```bash
curl http://【监控服务器IP】:8500/v1/catalog/datacenters
curl http://【监控服务器IP】:8500/v1/catalog/nodes
curl http://【监控服务器IP】:8500/v1/catalog/services
curl http://【监控服务器IP】:8500/v1/catalog/service/node-exporter
```

### 6.4.5 Prometheus 使用 Consul 发现

Consul 发现的目标会带元标签：`__meta_consul_address`、`__meta_consul_dc`、`__meta_consul_node`、`__meta_consul_service`、`__meta_consul_service_id`、`__meta_consul_service_address`、`__meta_consul_service_port`、`__meta_consul_tags`。

在 prometheus.yml 加：

```yaml
  - job_name: 'consul'
    honor_labels: true
    consul_sd_configs:
      - server: '【监控服务器IP】:8500'
        # services: []        # 默认发现所有服务；也可指定名称，如 ['node-exporter']
        # tags: ['node']      # 只保留带指定 tag 的服务
        refresh_interval: 30s
    relabel_configs:
      - source_labels: ['__meta_consul_service']
        target_label: 'consul_service'
      - source_labels: ['__meta_consul_dc']
        target_label: 'datacenter'
      - source_labels: ['__meta_consul_tags']
        target_label: 'app'
      # Consul 自身内置服务也叫 consul，但不提供 /metrics，丢弃避免报错
      - source_labels: ['__meta_consul_service']
        regex: 'consul'
        action: drop
```

参数解释：`server` Consul 地址；`services` 要发现的服务名列表，空为全部；`tags` 按标签过滤；`refresh_interval` 默认 30s。

检查生效：

```bash
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus
```

验证：在 Consul 注册一个新服务，几十秒内 Prometheus Targets 页自动出现；注销后自动消失。

---

## 6.5 Kubernetes API 服务发现

- **是什么**：直接对接 Kubernetes API Server，把 Node、Service、Endpoints（含 EndpointSlice）、Pod、Ingress 资源作为目标，每种资源对应一个 **role**。
- **认证**：Prometheus 跑在集群内时，自动使用 Pod 里 `/var/run/secrets/kubernetes.io/serviceaccount/` 的 CA 证书和 Token；集群外可用 `api_server` + kubeconfig/认证信息。

| role | 发现对象 | 典型用途 |
| --- | --- | --- |
| `node` | 每个节点（kubelet） | 采集 kubelet、cAdvisor |
| `pod` | 每个 Pod 的每个容器端口 | 采集业务 Pod |
| `service` | 每个 Service 的端口 | 对 Service 做黑盒监控 |
| `endpoints` / `endpointslice` | 每个 Endpoint 端口 | 采集 Service 后端、API Server |
| `ingress` | 每个 Ingress 的 path | 对 Ingress 做黑盒监控 |

部分常用元标签：

| role | 元标签举例 |
| --- | --- |
| node | `__meta_kubernetes_node_name`、`__meta_kubernetes_node_label_<x>`、`__meta_kubernetes_node_address_<类型>` |
| pod | `__meta_kubernetes_namespace`、`__meta_kubernetes_pod_name`、`__meta_kubernetes_pod_ip`、`__meta_kubernetes_pod_label_<x>`、`__meta_kubernetes_pod_node_name`、`__meta_kubernetes_pod_controller_kind` |
| service | `__meta_kubernetes_service_name`、`__meta_kubernetes_service_cluster_ip`、`__meta_kubernetes_service_port_number`、`__meta_kubernetes_service_type`、`__meta_kubernetes_service_label_<x>` |
| endpoints | `__meta_kubernetes_endpoints_name`、`__meta_kubernetes_endpoint_ready`、`__meta_kubernetes_endpoint_port_name` |
| ingress | `__meta_kubernetes_ingress_name`、`__meta_kubernetes_ingress_scheme`、`__meta_kubernetes_ingress_path` |

**集群内典型配置**（完整示例见官方 `prometheus-kubernetes.yml`）：

```yaml
scrape_configs:
  # API Server：endpoints role，只保留 default/kubernetes 的 https 端口
  - job_name: 'kubernetes-apiservers'
    kubernetes_sd_configs:
      - role: endpoints
    scheme: https
    tls_config:
      ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
    relabel_configs:
      - source_labels: [__meta_kubernetes_namespace, __meta_kubernetes_service_name, __meta_kubernetes_endpoint_port_name]
        action: keep
        regex: default;kubernetes;https

  # 节点 kubelet：通过 API Server 代理访问
  - job_name: 'kubernetes-nodes'
    scheme: https
    tls_config:
      ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
    kubernetes_sd_configs:
      - role: node
    relabel_configs:
      - action: labelmap
        regex: __meta_kubernetes_node_label_(.+)
      - target_label: __address__
        replacement: kubernetes.default.svc:443
      - source_labels: [__meta_kubernetes_node_name]
        target_label: __metrics_path__
        regex: (.+)
        replacement: /api/v1/nodes/${1}/proxy/metrics

  # 业务 Pod：只采集带 prometheus.io/scrape: "true" 注解的 Pod
  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
    tls_config:
      insecure_skip_verify: true
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: 'true'
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
      - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        target_label: __address__
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
      - action: labelmap
        regex: __meta_kubernetes_pod_label_(.+)
```

业务方通过 Pod/Service 注解声明采集方式（这是社区约定）：

| 注解 | 作用 |
| --- | --- |
| `prometheus.io/scrape: "true"` | 是否采集 |
| `prometheus.io/port: "端口"` | 采集端口 |
| `prometheus.io/path: "/metrics"` | 指标路径 |
| `prometheus.io/scheme: "http"` | http/https |

::: tip
生产中通常不会手写这么多 role 配置，而是用 **kube-prometheus-stack**（Helm）或 Prometheus Operator 自动生成，阶段十一详细讲。这里理解 role 与 relabel 的对应关系即可。
:::

---

## 本阶段命令速查表

```bash
# === 文件发现 ===
mkdir -p /usr/local/prometheus/conf/targets
vim /usr/local/prometheus/conf/targets/xxx.yml
# prometheus.yml: file_sd_configs 配 files + refresh_interval
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus

# === DNS（BIND）===
apt -y install bind9
named-checkconf && rndc reload
host -t srv _prometheus._tcp.magedu.com
systemctl restart systemd-resolved.service   # 清本地 DNS 缓存

# === Consul ===
# 二进制
wget https://releases.hashicorp.com/consul/1.22.7/consul_1.22.7_linux_amd64.zip
unzip consul_1.22.7_linux_amd64.zip -d /usr/local/bin/
systemctl enable --now consul
consul members
# 注册 / 注销
consul services register xxx.json
consul services deregister -id 服务ID
curl -X PUT http://【监控服务器IP】:8500/v1/agent/service/deregister/服务ID
```

---

## 本阶段常见坑与解决

**坑 1：改了文件发现目标不生效**

- 现象：编辑目标文件后 Prometheus 没反应。
- 原因：没到 `refresh_interval`；文件 YAML 语法错误；路径写错（相对路径是相对 prometheus.yml）。
- 解决：等待一个周期；`promtool check config` 检查；核对 files 路径。

**坑 2：直接编辑目标文件导致目标时有时无**

- 报错/现象：Targets 页短暂报错或目标不全。
- 原因：Prometheus 正好在你保存的瞬间读到写了一半的文件。
- 解决：写到临时文件再 `mv 临时文件 正式文件`（原子替换）；用脚本生成时也这样做。

**坑 3：DNS 发现不到目标**

- 现象：dns_sd 配置后目标为空。
- 原因：SRV 记录没配对（type 默认 SRV，却只建了 A 记录）；resolv.conf 没用自建 DNS；DNS 缓存。
- 解决：A 记录要配 `type: A` + `port`；确认 `/etc/resolv.conf` 指向自建 DNS；重启 systemd-resolved。

**坑 4：Consul 启动超时/失败**

- 报错原样：`Job for consul.service failed because a timeout was exceeded`；日志 `No known Consul servers`。
- 原因：多网卡没指定 bind；`bootstrap-expect` 数量达不到；client 模式下没有可连的 Server。
- 解决：显式 `-bind=本机IP`；单机用 `-bootstrap-expect=1`；确认 Server 已启动、8300/8301 端口放通。

**坑 5：Consul 里的 consul 服务导致 Targets 报错**

- 报错原样：目标 `server="Consul Agent"` 采集返回 404/连接拒绝。
- 原因：Consul 内置服务注册在 8300/8500，并不暴露 /metrics。
- 解决：relabel 中 drop 掉 `__meta_consul_service = "consul"`（见 6.4.5）。

**坑 6：K8s 发现 403/无权限**

- 报错原样：`server returned HTTP 403 Forbidden`。
- 原因：ServiceAccount 没有对对应资源的 list/watch 权限（RBAC）。
- 解决：给 ServiceAccount 绑定 ClusterRole（get/list/watch nodes、pods、services、endpoints 等）；阶段十一有完整 RBAC 示例。

**坑 7：节点名/服务名含非法字符**

- 报错原样：`Node name "xxx.xxx.com" will not be discoverable via DNS due to invalid characters`。
- 原因：Consul 节点名只允许字母数字和短横线，不能带域名点号。
- 解决：节点名用短横线命名（如 `consul-node1`），不要用完整域名。

---
# 阶段七：各类 Exporter 实战

## 阶段目标

- 掌握 Node Exporter 的高级用法（systemd 服务状态、textfile 自定义指标）；
- 部署并使用 **MySQL、Redis、Nginx、Consul、Java（JMX）、HAProxy、Blackbox** 的 Exporter；
- 每个组件都完成"部署 → 采集 → Grafana 看板"闭环。

Exporter 分三类：**应用内置**（Prometheus、Grafana、Zookeeper、MinIO 等自带指标）、**应用外置**（MySQL、Redis 等需单独装 Exporter）、**定制开发**（阶段三已讲）。

## 7.1 Node Exporter 高级采集

### 7.1.1 systemd 服务状态采集

- **是什么**：node_exporter 加 `--collector.systemd` 参数后，会采集系统中所有 systemd 服务的状态，指标为 `node_systemd_unit_state`。
- **为什么需要**：可以监控关键服务（nginx、mysql、sshd）是否在运行，服务挂了直接告警，不必为每个服务单独做探测。
- **指标形态**：每个服务有多种状态（active、inactive、failed、activating、deactivating），当前所处状态值为 1，其余为 0。

**第 1 步：修改 node_exporter 服务文件**

在被监控主机（如 web01）编辑 `/etc/systemd/system/node_exporter.service`（若用阶段二的二进制安装路径），把 ExecStart 改为：

```text
ExecStart=/usr/local/node_exporter/bin/node_exporter \
  --collector.systemd \
  --collector.systemd.unit-include=".*(ssh|nginx|mysql|redis|node_exporter).*\.service"
```

参数解释：

| 参数 | 作用 |
| --- | --- |
| `--collector.systemd` | 启用 systemd 采集器 |
| `--collector.systemd.unit-include` | 正则，只采集匹配的服务；不写则采集全部服务（数量多时指标量大） |
| `--collector.systemd.unit-exclude` | 正则，排除匹配的服务 |

::: warning
只显示**已安装**的服务，没安装的不会出现；unit-include/exclude 依赖 `--collector.systemd`，单独写不生效。正则要匹配服务的完整单元名（如 `nginx.service`），所以模式末尾要留 `\.service`。
:::

**第 2 步：重启验证**

```bash
systemctl daemon-reload
systemctl restart node_exporter
curl -s localhost:9100/metrics | grep node_systemd_unit_state
```

预期输出（节选）：

```text
node_systemd_unit_state{name="nginx.service",state="active"} 1
node_systemd_unit_state{name="nginx.service",state="inactive"} 0
node_systemd_unit_state{name="nginx.service",state="failed"} 0
node_systemd_unit_state{name="ssh.service",state="active"} 1
```

**第 3 步：告警规则**（服务异常即告警），创建 `/usr/local/prometheus/rules/systemd_alert_rules.yml`：

```yaml
groups:
  - name: systemd-services
    rules:
      - alert: ServiceIsDown
        expr: node_systemd_unit_state{state="active"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "服务 {{ $labels.name }} 已停止"
          description: "{{ $labels.instance }} 上的 {{ $labels.name }} 非 active 超过 1 分钟"
```

### 7.1.2 textfile 自定义指标采集器

- **是什么**：textfile 采集器会读取指定目录下的 `*.prom` 文本文件，把文件里写好的指标一并暴露出去（默认已启用）。
- **类比**：像在 node_exporter 门口放一个"意见箱"，你的脚本把数值按格式写成纸条丢进去，node_exporter 帮你上报。
- **为什么需要**：适合采集没有专门 Exporter 的指标——比如备份是否成功、证书剩余天数、硬件 RAID 状态、业务批处理结果，用 shell 脚本就能接入。

**第 1 步：建目录并指定**

```bash
mkdir -p /var/lib/node_exporter/textfile
```

修改 node_exporter 的 ExecStart，追加：

```text
  --collector.textfile.directory=/var/lib/node_exporter/textfile
```

**第 2 步：写一个 .prom 文件**

`/var/lib/node_exporter/textfile/backup.pom`（注意文件名以 .prom 结尾）：

```text
# HELP backup_last_success_timestamp 最近一次备份成功的时间戳
# TYPE backup_last_success_timestamp gauge
backup_last_success_timestamp{job="mysql_backup"} 1770000000
# HELP backup_files_count 当前备份文件数量
# TYPE backup_files_count gauge
backup_files_count 7
```

格式要求：每个指标建议有 `# HELP`（说明）和 `# TYPE`（类型）行；指标名、标签写法和 Prometheus 文本格式一致。

**第 3 步：用脚本生成指标（典型用法）**

创建 `/usr/local/bin/write_backup_metrics.sh`：

```bash
#!/bin/bash
METRIC_DIR=/var/lib/node_exporter/textfile
TMP=${METRIC_DIR}/.backup.prom.tmp

# 查找最近一次备份文件（假设备份放在 /data/backup）
LAST=$(find /data/backup -name '*.sql.gz' -printf '%T@\n' 2>/dev/null | sort -n | tail -1 | cut -d. -f1)
COUNT=$(find /data/backup -name '*.sql.gz' 2>/dev/null | wc -l)
[ -z "$LAST" ] && LAST=0

cat > "$TMP" <<EOF
# HELP backup_last_success_timestamp 最近备份成功时间戳
# TYPE backup_last_success_timestamp gauge
backup_last_success_timestamp ${LAST}
# HELP backup_files_count 备份文件数量
# TYPE backup_files_count gauge
backup_files_count ${COUNT}
EOF
mv "$TMP" ${METRIC_DIR}/backup.prom
```

::: tip
脚本一定要先写临时文件再 `mv` 成 .prom——node_exporter 可能正好在你写文件时读取，原子替换避免读到一半。加计划任务：`crontab -e` 加 `5 * * * * /usr/local/bin/write_backup_metrics.sh`。
:::

重启并验证：

```bash
chmod +x /usr/local/bin/write_backup_metrics.sh
bash /usr/local/bin/write_backup_metrics.sh
systemctl restart node_exporter
curl -s localhost:9100/metrics | grep backup_
```

预期输出：

```text
backup_last_success_timestamp{job="mysql_backup"} 1.77e+09
backup_files_count 7
```

---

## 7.2 MySQL 监控（mysqld_exporter）

- **是什么**：mysqld_exporter 连到 MySQL，把数据库状态（连接数、QPS、慢查询、主从延迟、缓冲池等）转成 Prometheus 指标，默认端口 **9104**。
- **为什么需要**：数据库是业务核心，连接数打满、主从延迟、慢查询激增都要提前发现。

### 7.2.1 MySQL 端准备

在**数据库服务器 db01** 执行，用户 root。

**第 1 步：安装 MySQL**

```bash
apt update && apt -y install mysql-server
systemctl enable --now mysql
```

**第 2 步：（可选）允许远程连接**

Exporter 与 MySQL 同机则不用改。不同机时编辑 `/etc/mysql/mysql.conf.d/mysqld.cnf`，把原值 `bind-address = 127.0.0.1` 改为 `bind-address = 0.0.0.0`，然后 `systemctl restart mysql`，并放通 3306 端口。

**第 3 步：创建监控用户并授权**

```bash
mysql
```

```sql
CREATE USER 'exporter'@'localhost' IDENTIFIED BY '【exporter用户密码】' WITH MAX_USER_CONNECTIONS 3;
GRANT PROCESS, REPLICATION CLIENT, SELECT ON *.* TO 'exporter'@'localhost';
FLUSH PRIVILEGES;
```

权限解释：`PROCESS` 查看所有线程/连接；`REPLICATION CLIENT` 查看主从状态；`SELECT` 查询各系统库。`MAX_USER_CONNECTIONS 3` 限制监控用户连接数，避免 Exporter 异常时占满数据库连接。

若 Exporter 在其他主机，再建 `'exporter'@'【监控服务器网段】'`（如 `'exporter'@'10.0.0.%'`）并同样授权。

### 7.2.2 安装 mysqld_exporter

在 db01 执行，用户 root。

**第 1 步：下载解压**

```bash
cd /usr/local
wget https://github.com/prometheus/mysqld_exporter/releases/download/v0.20.0/mysqld_exporter-0.20.0.linux-amd64.tar.gz
tar xf mysqld_exporter-0.20.0.linux-amd64.tar.gz
ln -s mysqld_exporter-0.20.0.linux-amd64 mysqld_exporter
cd mysqld_exporter
mkdir -p bin
mv mysqld_exporter bin/
```

备选（GitHub）：

```text
https://github.com/prometheus/mysqld_exporter/releases/download/v0.20.0/mysqld_exporter-0.20.0.linux-amd64.tar.gz
```

**第 2 步：创建数据源配置** `/usr/local/mysqld_exporter/.my.cnf`：

```ini
[client]
host=127.0.0.1
port=3306
user=exporter
password=【exporter用户密码】
```

收紧权限：

```bash
chmod 640 /usr/local/mysqld_exporter/.my.cnf
id prometheus &>/dev/null || useradd -r -s /usr/sbin/nologin prometheus
chown -R prometheus:prometheus /usr/local/mysqld_exporter
```

**第 3 步：创建服务文件**

```bash
cat > /etc/systemd/system/mysqld_exporter.service <<'EOF'
[Unit]
Description=Prometheus MySQL Exporter
After=network.target

[Service]
Type=simple
User=prometheus
Group=prometheus
ExecStart=/usr/local/mysqld_exporter/bin/mysqld_exporter \
  --config.my-cnf=/usr/local/mysqld_exporter/.my.cnf \
  --web.listen-address=0.0.0.0:9104
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable --now mysqld_exporter
ss -lntp | grep 9104
```

验证：

```bash
curl -s localhost:9104/metrics | grep -E 'mysql_up|mysql_global_status_threads_connected'
```

预期输出：

```text
mysql_up 1
mysql_global_status_threads_connected 8
```

`mysql_up` 为 1 表示 Exporter 成功连上数据库；为 0 说明连接/认证有问题。

### 7.2.3 Prometheus 采集与 Grafana 看板

在 prometheus.yml 加：

```yaml
  - job_name: 'mysqld_exporter'
    static_configs:
      - targets: ['【数据库服务器IP】:9104']
        labels:
          app: mysql
```

```bash
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus
```

Grafana 导入看板（推荐 17320 中文版，另有 7362、14057、11323）：

```text
https://grafana.com/grafana/dashboards/17320-mysql-overview/
```

### 7.2.4 Docker Compose 方式

```yaml
version: '3.6'

networks:
  monitoring:
    driver: bridge

volumes:
  mysqld_data: {}

services:
  mysqld:
    image: mysql:8.0
    restart: always
    volumes:
      - mysqld_data:/var/lib/mysql
    environment:
      MYSQL_ROOT_PASSWORD: 【root密码】
    networks:
      - monitoring
    ports:
      - "3306:3306"

  mysqld-exporter:
    image: prom/mysqld-exporter:v0.20.0
    restart: always
    command:
      - --collect.global_status
      - --collect.info_schema.innodb_metrics
      - --collect.engine_innodb_status
      - --collect.binlog_size
    environment:
      DATA_SOURCE_NAME: exporter:【exporter用户密码】@(mysqld:3306)/
    networks:
      - monitoring
    ports:
      - "9104:9104"
    depends_on:
      - mysqld
```

启动后在 MySQL 里创建 exporter 用户（容器网段，如 `'exporter'@'172.%.%.%'`），授权同上。

---

## 7.3 Redis 监控（redis_exporter）

- **是什么**：redis_exporter 连接 Redis，采集内存使用、连接数、命中率、过期/淘汰键、主从等指标，默认端口 **9121**。
- **为什么需要**：Redis 内存满、被 OOM、命中率骤降都会直接影响业务。

### 7.3.1 Redis 端准备

在 db01（或独立缓存服务器）执行：

```bash
apt update && apt -y install redis-server
```

编辑 `/etc/redis/redis.conf`：

- 原值 `bind 127.0.0.1 -::1`，需要远程访问时改为 `bind 0.0.0.0`；
- 取消注释并设置密码：`requirepass 【Redis密码】`；

```bash
systemctl restart redis-server
```

验证密码生效：

```bash
redis-cli -a 【Redis密码】 ping
```

预期输出：`PEMON`（警告会提示命令行用密码不安全，属正常）。

### 7.3.2 安装 redis_exporter

**第 1 步：下载解压**

```bash
cd /usr/local
wget https://github.com/oliver006/redis_exporter/releases/download/v1.92.1/redis_exporter-v1.92.1.linux-amd64.tar.gz
tar xf redis_exporter-v1.92.1.linux-amd64.tar.gz
ln -s redis_exporter-v1.92.1.linux-amd64 redis_exporter
cd redis_exporter
mkdir bin
mv redis_exporter bin/
```

**第 2 步：创建服务文件**

```bash
id prometheus &>/dev/null || useradd -r -s /usr/sbin/nologin prometheus
chown -R prometheus:prometheus /usr/local/redis_exporter

cat > /etc/systemd/system/redis_exporter.service <<'EOF'
[Unit]
Description=Prometheus Redis Exporter
After=network.target

[Service]
Type=simple
User=prometheus
Group=prometheus
ExecStart=/usr/local/redis_exporter/bin/redis_exporter \
  -redis.addr=redis://127.0.0.1:6379 \
  -redis.password=【Redis密码】 \
  -web.listen-address=0.0.0.0:9121
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable --now redis_exporter
ss -lntp | grep 9121
```

参数解释：`-redis.addr` Redis 地址（单机或集群节点，集群可逗号分隔多个）；`-redis.password` 密码；无密码可省。多个不同密码的实例可用 `-redis.addr-key`/环境变量 `REDIS_ADDR1` 等方式，见项目文档。

验证：

```bash
curl -s localhost:9121/metrics | grep -E 'redis_up|redis_connected_clients'
```

预期输出：

```text
redis_up 1
redis_connected_clients 1
```

### 7.3.3 采集与看板

prometheus.yml 加：

```yaml
  - job_name: 'redis_exporter'
    static_configs:
      - targets: ['【数据库服务器IP】:9121']
        labels:
          app: redis
```

```bash
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus
```

Grafana 看板推荐 763、11835、14615：

```text
https://grafana.com/grafana/dashboards/763-redis-dashboard/
```

### 7.3.4 Kubernetes 方式（了解）

Redis 与 redis_exporter 同 Pod 两个容器（redis_exporter 镜像 `oliver006/redis_exporter:v1.92.1`，端口 9121），再建 Service 暴露；Prometheus 采集该 Service。生产更推荐用 Redis Operator 或在 Pod 注解里声明采集。

---
## 7.4 Nginx 监控

Nginx 自身不暴露指标，有三种实现：

| 方式 | 原理 | 适用场景 |
| --- | --- | --- |
| **nginx-prometheus-exporter（推荐）** | 官方 exporter 采集 Nginx 的 stub_status 状态页 | 绝大多数 Nginx，无需重新编译 |
| nginx-lua-prometheus | Lua 库在 Nginx 内直接记录指标，需 lua-nginx-module（OpenResty） | 需要按 URI/维度细分的场景 |
| nginx-vts + nginx-vts-exporter | 编译加 vts 模块输出 JSON 状态，exporter 采集 | 需要虚拟主机维度流量统计 |

### 7.4.1 方式一：nginx-prometheus-exporter

**第 1 步：开启 stub_status**

在 web01 安装 Nginx：

```bash
apt update && apt -y install nginx
```

创建 `/etc/nginx/conf.d/status.conf`：

```nginx
server {
    listen 8888;
    server_name localhost;

    location /basic_status {
        stub_status;
        access_log off;
        allow 127.0.0.1;
        allow 10.0.0.0/8;
        deny all;
    }
}
```

也可以直接在默认站点 `/etc/nginx/sites-enabled/default` 的 server 块里加 `location /basic_status { stub_status; }`。

生效并查看：

```bash
nginx -t
systemctl reload nginx
curl 127.0.0.1:8888/basic_status
```

预期输出：

```text
Active connections: 1
server accepts handled requests
 3 3 3
Reading: 0 Writing: 1 Waiting: 0
```

字段含义：`Active connections` 当前活跃连接数；`accepts` 已接受的总连接；`handled` 已处理的总连接（正常与 accepts 相等，差值即被丢弃的连接）；`requests` 总请求数；`Reading` 正在读请求头的连接；`Writing` 正在返回响应的连接；`Waiting` 等待中的空闲连接（keepalive）。

**第 2 步：启动 exporter 容器**

```bash
docker run -d --name nginx-exporter --restart=always -p 9113:9113 \
  nginx/nginx-prometheus-exporter:1.5.3 \
  --nginx.scrape-uri=http://【Web服务器IP】:8888/basic_status
```

参数解释：`--nginx.scrape-uri` stub_status 页面地址（Exporter 要能访问到，注意上面 allow 放行）。默认监听 9113。

验证：

```bash
curl -s localhost:9113/metrics | grep -E 'nginx_up|nginx_connections_active|nginx_http_requests_total'
```

预期输出：

```text
nginx_connections_accepted 3
nginx_connections_active 1
nginx_connections_handled 3
nginx_connections_reading 0
nginx_connections_waiting 0
nginx_connections_writing 1
nginx_http_requests_total 3
nginx_up 1
```

**第 3 步：采集与看板**

prometheus.yml 加：

```yaml
  - job_name: 'nginx_exporter'
    static_configs:
      - targets: ['【Web服务器IP】:9113']
        labels:
          app: nginx
```

```bash
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus
```

Grafana 看板 11199、14900：

```text
https://grafana.com/grafana/dashboards/11199-nginx/
```

**Docker Compose 一体化**（Nginx + exporter）：

```yaml
version: '3.6'

networks:
  monitoring:
    driver: bridge

services:
  nginx:
    image: nginx:1.27
    restart: always
    volumes:
      - ./nginx/stub_status-server.conf:/etc/nginx/conf.d/stub_status-server.conf:ro
    networks:
      - monitoring
    ports:
      - "80:80"

  nginx-exporter:
    image: nginx/nginx-prometheus-exporter:1.5.3
    restart: always
    command:
      - '--nginx.scrape-uri=http://nginx:8080/stub_status'
    networks:
      - monitoring
    ports:
      - "9113:9113"
    depends_on:
      - nginx
```

`stub_status-server.conf` 里 server 监听 8080，location 为 `/stub_status { stub_status; }`。

### 7.4.2 方式二：nginx-lua-prometheus（了解）

使用 OpenResty 或编译了 lua-nginx-module 的 Nginx，`lua_shared_dict prometheus_metrics 10m;` 定义共享内存，init_by_lua 初始化计数器（请求总数、延迟直方图等），log_by_lua 里逐请求记录，再用一个 content_by_lua location 调用 `prom:collect()` 输出指标。项目地址：

```text
https://github.com/knyar/nginx-lua-prometheus
```

### 7.4.3 方式三：nginx-vts（了解）

编译 Nginx 时 `--add-module=/path/nginx-module-vts`，http 块加 `vhost_traffic_status_zone;`，status location 用 `vhost_traffic_status_display` 暴露 HTML/JSON（`/status/format/json`）；nginx-vts-exporter 用 `-nginx.scrape_uri=http://nginx/status/format/json` 采集，默认端口 9913，Grafana 看板 2949。

```text
https://github.com/vozlt/nginx-module-vts
https://github.com/hnlq715/nginx-vts-exporter
```

---

## 7.5 Consul 监控（consul_exporter）

- **是什么**：consul_exporter 调用 Consul API，把各节点、服务的健康状态转为指标，默认端口 **9107**。
- **为什么需要**：Consul 作为注册中心，其自身及被注册服务的健康状态需要被监控。

**第 1 步：下载解压**（在 Consul 主机或独立主机）

```bash
cd /usr/local
wget https://github.com/prometheus/consul_exporter/releases/download/v0.13.0/consul_exporter-0.13.0.linux-amd64.tar.gz
tar xf consul_exporter-0.13.0.linux-amd64.tar.gz
ln -s consul_exporter-0.13.0.linux-amd64 consul_exporter
cd consul_exporter
mkdir bin
mv consul_exporter bin/
```

**第 2 步：创建服务文件**

```bash
id consul &>/dev/null || useradd -r -s /usr/sbin/nologin consul
chown -R consul:consul /usr/local/consul_exporter

cat > /etc/systemd/system/consul_exporter.service <<'EOF'
[Unit]
Description=Prometheus Consul Exporter
After=network.target

[Service]
Type=simple
User=consul
ExecStart=/usr/local/consul_exporter/bin/consul_exporter \
  --consul.server=http://127.0.0.1:8500 \
  --web.listen-address=:9107
Restart=always

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable --now consul_exporter
```

Exporter 与 Consul 不同机时，`--consul.server` 指向实际地址。

验证：

```bash
curl -s localhost:9107/metrics | grep -E 'consul_catalog_services|consul_catalog_service_node_healthy'
```

预期输出：

```text
consul_catalog_service_node_healthy{node="consul",service_id="consul",service_name="consul"} 1
consul_catalog_services 5
```

采集：prometheus.yml 加 job 指向 `【Consul服务器IP】:9107`。Grafana 看板 12049。

---

## 7.6 Java 应用监控（JMX Exporter）

- **是什么**：JMX Exporter 以 **Java Agent** 方式随 Java 应用启动，把 JVM（内存、GC、线程）和应用通过 JMX 暴露的 MBean 转成 Prometheus 指标，端口由启动参数指定（如 9527）。
- **JMX 是什么**：Java 管理扩展，是 Java 应用标准的管理/监控接口，Tomcat、Kafka、Spring 等都通过它暴露内部状态。
- **为什么需要**：JVM 堆内存、GC 频率、线程数是 Java 应用排障与容量规划的核心依据。

JMX Exporter 有两种用法：**javaagent 模式（推荐，随应用启动）**和 standalone HTTP Server 模式（独立进程远程拉取 JMX）。

### 7.6.1 准备 Java 环境（以 Tomcat 为例）

包安装（Ubuntu 24.04 是 tomcat10，22.04 是 tomcat9）：

```bash
apt update && apt -y install tomcat10
systemctl enable --now tomcat10
ss -lntp | grep 8080
```

### 7.6.2 部署 JMX Exporter

**第 1 步：下载 agent jar 与配置**

```bash
mkdir -p /opt/jmx_exporter
cd /opt/jmx_exporter
wget https://github.com/prometheus/jmx_exporter/releases/download/1.6.0/jmx_prometheus_javaagent-1.6.0.jar
wget -O tomcat.yml https://raw.githubusercontent.com/prometheus/jmx_exporter/1.6.0/examples/tomcat.yml
```

::: tip
1.1.0 之后的新版 jar 只在 GitHub Releases 发布（Maven Central 上该制品最新只到 1.0.1）。GitHub 下载慢时，在 URL 前加 `https://ghproxy.net/` 等代理，或在能访问的机器下载后拷贝。
:::

配置文件 `tomcat.yml` 定义如何把 MBean 转成指标（节选，完整文件从上面地址获取）：

```yaml
lowercaseOutputLabelNames: true
lowercaseOutputName: true
rules:
  - pattern: 'Catalina<type=GlobalRequestProcessor, name=\"(\w+-\w+)-(\d+)\"><>(\w+):'
    name: tomcat_$3_total
    labels:
      port: "$2"
      protocol: "$1"
    help: Tomcat global $3
    type: COUNTER
  - pattern: 'Catalina<type=ThreadPool, name="(\w+-\w+)-(\d+)"><>(currentThreadCount|currentThreadsBusy|keepAliveCount):'
    name: tomcat_threadpool_$3
    labels:
      port: "$2"
      protocol: "$1"
    type: GAUGE
```

字段解释：`pattern` 匹配 MBean 名称的正则，括号捕获组用 `$1/$2...` 引用；`name` 生成的指标名；`labels` 从捕获组生成标签；`type` 指标类型；`lowercaseOutputName/Labels` 把输出统一成小写（避免大小写不一致的重复序列）。

**第 2 步：让 Tomcat 加载 agent**

包安装的 Tomcat，编辑 `/usr/share/tomcat10/bin/catalina.sh`，在文件靠前位置（OS support 注释附近）加一行：

```bash
JAVA_OPTS="-javaagent:/opt/jmx_exporter/jmx_prometheus_javaagent-1.6.0.jar=9527:/opt/jmx_exporter/tomcat.yml"
```

格式：`-javaagent:jar路径=端口:配置文件路径`。端口 9527 是 agent 暴露指标的端口。

**第 3 步：重启验证**

```bash
systemctl restart tomcat10
ps aux | grep jmx_prometheus
ss -lntp | grep 9527
curl -s localhost:9527/metrics | grep -E 'jvm_memory_used_bytes|tomcat_requestcount_total'
```

预期输出（节选）：

```text
jvm_memory_used_bytes{area="heap",id="G1 Eden Space"} 1.234567E7
tomcat_requestcount_total{port="8080",protocol="http-bio"} 15
```

**第 4 步：采集与看板**

prometheus.yml 加：

```yaml
  - job_name: 'java_tomcat'
    static_configs:
      - targets: ['【应用服务器IP】:9527']
        labels:
          app: tomcat
```

Grafana 看板 8704、14845（导入后把面板的 job 变量改成实际 job 名）：

```text
https://grafana.com/grafana/dashboards/8704-jvm/
```

### 7.6.3 其他 Java 应用的通用做法

- **Spring Boot**：更推荐直接引入 `micrometer-registry-prometheus`，应用原生暴露 `/actuator/prometheus`，无需 JMX agent；
- **Kafka / ZooKeeper / 其他中间件**：同样把 `-javaagent:...jar=端口:配置.yml` 加进启动脚本（Kafka 加在 `KAFKA_OPTS`），配置文件用仓库 examples 目录下对应的 kafka.yml、zookeeper.yml；
- **二进制 Tomcat**：把 jar 和 yml 放进 `tomcat/bin/`，在 `catalina.sh` 加 JAVA_OPTS，`catalina.sh stop && catalina.sh start` 即可。

---

## 7.7 HAProxy 监控

两种方式：**haproxy_exporter 采集状态页 CSV**，或 **HAProxy 2.x 内置 Prometheus 输出**。

### 7.7.1 方式一：haproxy_exporter

**第 1 步：开启 HAProxy 状态页**

```bash
apt update && apt -y install haproxy
```

编辑 `/etc/haproxy/haproxy.cfg`，加：

```text
listen stats
    mode http
    bind 0.0.0.0:9999
    stats enable
    stats uri /haproxy-status
    stats auth admin:【状态页密码】
```

重启：

```bash
systemctl restart haproxy
curl -u admin:【状态页密码】 http://127.0.0.1:9999/haproxy-status;csv | head -2
```

`;csv` 后缀让状态页输出 CSV，exporter 解析的就是它。

**第 2 步：部署 exporter**

```bash
cd /usr/local
wget https://github.com/prometheus/haproxy_exporter/releases/download/v0.15.0/haproxy_exporter-0.15.0.linux-amd64.tar.gz
tar xf haproxy_exporter-0.15.0.linux-amd64.tar.gz
ln -s haproxy_exporter-0.15.0.linux-amd64 haproxy_exporter
cd haproxy_exporter
mkdir bin
mv haproxy_exporter bin/
```

创建服务文件：

```bash
id prometheus &>/dev/null || useradd -r -s /usr/sbin/nologin prometheus
chown -R prometheus:prometheus /usr/local/haproxy_exporter

cat > /etc/systemd/system/haproxy_exporter.service <<'EOF'
[Unit]
Description=Prometheus HAProxy Exporter
After=network.target

[Service]
Type=simple
User=prometheus
ExecStart=/usr/local/haproxy_exporter/bin/haproxy_exporter \
  --haproxy.scrape-uri="http://admin:【状态页密码】@127.0.0.1:9999/haproxy-status;csv" \
  --web.listen-address=:9101
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable --now haproxy_exporter
```

也支持 socket 方式：`--haproxy.scrape-uri=unix:/run/haproxy/admin.sock`。

验证：

```bash
curl -s localhost:9101/metrics | grep -E 'haproxy_up|haproxy_frontend_http_requests_total'
```

采集：prometheus.yml 加 job 指向 9101。Grafana 看板 2428。

### 7.7.2 方式二：HAProxy 内置 /metrics（推荐）

Ubuntu 22.04/24.04 包安装的 HAProxy 2.4+ 默认编译了 Prometheus 支持（`USE_PROMEX=1`，`haproxy -vv` 可确认）。在 frontend 里加一行：

```text
frontend stats
    bind *:9999
    stats enable
    stats uri /haproxy-status
    http-request use-service prometheus-exporter if { path /metrics }
```

重启后直接访问：

```bash
systemctl restart haproxy
curl -s http://127.0.0.1:9999/metrics | grep haproxy_frontend
```

Prometheus 直接采集 `【HAProxyIP】:9999` 的普通 job 即可，无需 exporter。Grafana 看板 12693（注意内置方式与 exporter 方式的看板不通用）。

---

## 7.8 Blackbox 黑盒监控

- **是什么**：blackbox_exporter 从**外部**探测目标——HTTP/HTTPS 返回码与内容、TCP 端口连通、DNS 解析、ICMP（ping）、gRPC、TLS 证书，默认端口 **9115**。
- **类比**：不像其他 Exporter 站在机器"屋里"看内部指标，黑盒监控像在"门外"敲门，验证用户实际能不能访问。
- **为什么需要**：服务进程活着不代表用户能访问（防火墙、DNS、证书过期、首页报错都可能出问题），黑盒探测模拟真实访问，是可用性的最后一道验证。

### 7.8.1 部署 blackbox_exporter

**第 1 步：下载解压**（部署在监控服务器 monitor）

```bash
cd /usr/local
wget https://github.com/prometheus/blackbox_exporter/releases/download/v0.28.0/blackbox_exporter-0.28.0.linux-amd64.tar.gz
tar xf blackbox_exporter-0.28.0.linux-amd64.tar.gz
ln -s blackbox_exporter-0.28.0.linux-amd64 blackbox_exporter
cd blackbox_exporter
mkdir -p bin conf
mv blackbox_exporter bin/
mv blackbox.yml conf/
```

**第 2 步：配置模块** `/usr/local/blackbox_exporter/conf/blackbox.yml`：

```yaml
modules:
  http_2xx:
    prober: http
    timeout: 5s
    http:
      valid_http_versions: ["HTTP/1.1", "HTTP/2.0"]
      valid_status_codes: []        # 空表示接受 2xx
      method: GET
      preferred_ip_protocol: ip4
  http_post_2xx:
    prober: http
    http:
      method: POST
  tcp_connect:
    prober: tcp
    timeout: 5s
  dns_udp:
    prober: dns
    timeout: 5s
    dns:
      query_name: "www.magedu.com"
      query_type: "A"
      valid_rcodes: [NOERROR]
  icmp:
    prober: icmp
    timeout: 5s
```

模块（module）= 一套探测方式定义；常用 prober：`http`、`tcp`、`dns`、`icmp`、`grpc`。HTTP 模块还支持：`fail_if_ssl`/`fail_if_not_ssl`（要求必须不是/必须是 HTTPS）、`fail_if_body_matches_regexp`（正文匹配正则则失败，可检测页面报错文案）、TLS 证书校验等。

**第 3 步：创建服务文件**

::: warning
ICMP 探测需要发送原始套接字（raw socket）。普通用户运行需要相应权限；最简单稳妥的方式是以 root 运行 blackbox_exporter，或给二进制授予 CAP_NET_RAW 能力：`setcap cap_net_raw,cap_net_admin=eip /usr/local/blackbox_exporter/bin/blackbox_exporter`，再用普通用户运行。
:::

```bash
cat > /etc/systemd/system/blackbox_exporter.service <<'EOF'
[Unit]
Description=Prometheus Blackbox Exporter
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/blackbox_exporter/bin/blackbox_exporter \
  --config.file=/usr/local/blackbox_exporter/conf/blackbox.yml \
  --web.listen-address=:9115
Restart=on-failure
LimitNOFILE=100000

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable --now blackbox_exporter
ss -lntp | grep 9115
```

**第 4 步：先用浏览器/URL 手工验证模块**

访问（先探测本机 9115 自己）：

```text
http://【监控服务器IP】:9115/probe?target=www.baidu.com&module=http_2xx
```

页面返回 `probe_success 1` 表示探测成功；失败时返回 `probe_success 0` 并附带 `probe_*` 诊断指标（如 DNS 解析失败、超时）。

### 7.8.2 Prometheus 配置黑盒采集

黑盒采集的 relabel 套路是固定的，**三类探测都一样**：把目标地址从 `__address__` 挪到 `__param_target`（作为 probe 的 target 参数），再把 `__address__` 改成 blackbox_exporter 自身地址。

**ICMP（ping 连通性）**：

```yaml
  - job_name: 'blackbox-icmp'
    metrics_path: /probe
    params:
      module: [icmp]
    static_configs:
      - targets:
          - '【Web服务器IP】'
          - '【应用服务器IP】'
          - '【数据库服务器IP】'
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: 【监控服务器IP】:9115
```

**TCP 端口连通**：

```yaml
  - job_name: 'blackbox-tcp'
    metrics_path: /probe
    params:
      module: [tcp_connect]
    static_configs:
      - targets:
          - '【Web服务器IP】:80'
          - '【数据库服务器IP】:3306'
          - '【数据库服务器IP】:6379'
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: 【监控服务器IP】:9115
```

**HTTP/HTTPS 网站**：

```yaml
  - job_name: 'blackbox-http'
    metrics_path: /probe
    params:
      module: [http_2xx]
    static_configs:
      - targets:
          - 'http://【Web服务器IP】'
          - 'https://www.baidu.com'
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: url
      - target_label: __address__
        replacement: 【监控服务器IP】:9115
```

检查生效：

```bash
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus
```

验证：Targets 页出现各探测目标，`probe_success` 为 1。HTTPS 目标还会自动得到 `probe_tls_version_info`、`probe_ssl_earliest_cert_expiry`（证书最早到期时间）等指标。

**黑盒告警规则**，创建 `/usr/local/prometheus/rules/blackbox_alert_rules.yml`：

```yaml
groups:
  - name: blackbox
    rules:
      - alert: BlackboxProbeFailed
        expr: probe_success == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "探测失败：{{ $labels.instance }}"
          description: "目标 {{ $labels.instance }} 探测失败超过 1 分钟"

      - alert: SSLCertExpiringSoon
        expr: (probe_ssl_earliest_cert_expiry - time()) / 86400 < 30
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "证书即将过期：{{ $labels.instance }}"
          description: "证书剩余有效期不足 30 天"
```

Grafana 看板 9965、13587：

```text
https://grafana.com/grafana/dashboards/9965-blackbox-exporter/
```

### 7.8.3 Docker Compose 方式

```yaml
version: '3.6'
services:
  blackbox_exporter:
    image: prom/blackbox-exporter:v0.28.0
    restart: always
    volumes:
      - ./blackbox.yml:/etc/blackbox_exporter/blackbox.yml:ro
    command:
      - '--config.file=/etc/blackbox_exporter/blackbox.yml'
    ports:
      - "9115:9115"
```

容器里做 ICMP 探测需加 `cap_add: [NET_RAW, NET_ADMIN]`。

---

## 本阶段命令速查表

| 组件 | 端口 | 关键配置/命令 |
| --- | --- | --- |
| node systemd | 9100 | `--collector.systemd --collector.systemd.unit-include="..."` |
| node textfile | 9100 | `--collector.textfile.directory=/var/lib/node_exporter/textfile` |
| mysqld_exporter | 9104 | `--config.my-cnf=/usr/local/mysqld_exporter/.my.cnf` |
| redis_exporter | 9121 | `-redis.addr=redis://127.0.0.1:6379 -redis.password=...` |
| nginx exporter | 9113 | `--nginx.scrape-uri=http://IP:8888/basic_status` |
| consul_exporter | 9107 | `--consul.server=http://127.0.0.1:8500` |
| JMX agent | 9527 | `-javaagent:jar=9527:配置.yml` |
| haproxy_exporter | 9101 | `--haproxy.scrape-uri=".../haproxy-status;csv"` |
| blackbox | 9115 | `--config.file=blackbox.yml`，采集固定 relabel 三件套 |

```bash
# 通用验证三连
ss -lntp | grep 端口
curl -s localhost:端口/metrics | grep 组件_up
promtool check config /usr/local/prometheus/conf/prometheus.yml && systemctl reload prometheus
```

---

## 本阶段常见坑与解决

**坑 1：mysqld_exporter 的 mysql_up 为 0**

- 报错/现象：`mysql_up 0`，日志 `Error 1045: Access denied for user 'exporter'@...`。
- 原因：密码错、用户 host 不匹配、权限不足。
- 解决：核对 .my.cnf；确认 exporter 连接来源 IP 对应的用户已创建并授权（PROCESS、REPLICATION CLIENT、SELECT）。

**坑 2：redis_exporter 指标为空/redis_up 为 0**

- 报错/现象：日志 `NOAUTH Authentication required` 或 `dial tcp ... connect: connection refused`。
- 原因：没配密码/密码错；bind 限制；端口不通。
- 解决：`-redis.password` 与 requirepass 一致；确认 bind 0.0.0.0、放通 6379。

**坑 3：Nginx exporter 报 404/连接拒绝**

- 报错/现象：`nginx_up 0`，日志 `Unexpected status code 404`。
- 原因：stub_status 没开或 URI 写错；访问被 deny。
- 解决：确认 location、curl 状态页有输出；放行 exporter 来源 IP。

**坑 4：JMX agent 启动后应用起不来**

- 报错原样：`Error opening zip file or JAR manifest missing : /opt/jmx_exporter/jmx_prometheus_javaagent-1.6.0.jar`。
- 原因：jar 路径错/下载不完整；配置文件路径错。
- 解决：核对 jar 与 yml 绝对路径、重新下载；`java -jar` 前先确认文件非空。

**坑 5：JMX 指标名重复/大小写混乱**

- 现象：同一指标出现大小写两套序列，看板数据分裂。
- 原因：未开 lowercaseOutputName/lowercaseOutputLabelNames。
- 解决：配置文件开头设置两者为 true。

**坑 6：ICMP 探测全部失败**

- 报错/现象：`probe_success 0`，日志 `socket: permission denied`。
- 原因：普通用户无 raw socket 权限。
- 解决：root 运行，或 `setcap cap_net_raw,cap_net_admin=eip blackbox_exporter`；容器加 NET_RAW capability。

**坑 7：黑盒目标全部失败，但 exporter 本身正常**

- 报错/现象：所有 probe 目标 0，手工访问 exporter URL 报 `probe_dns_lookup_time_seconds` 相关错误。
- 原因：监控服务器 DNS 解析不了目标；目标被防火墙拦；relabel 写错（target 没传对）。
- 解决：在监控机上 curl/ping 目标自查；核对 relabel 三件套顺序。

**坑 8：textfile 指标不出现**

- 报错/现象：.prom 文件写了但 metrics 里没有。
- 原因：目录没配对、文件后缀不是 .prom、文件正在写（临时文件被读到报错）、指标格式错误。
- 解决：核对 `--collector.textfile.directory`；临时文件写完再 mv；看 node_exporter 日志里的 textfile 解析报错。

**坑 9：HAProxy 内置 /metrics 不输出**

- 报错/现象：访问 /metrics 返回状态页而非指标。
- 原因：未编译 USE_PROMEX，或没配 `http-request use-service prometheus-exporter`。
- 解决：`haproxy -vv | grep PROMEX`；frontend 加对应行；否则改用 exporter 方式。

---
# 阶段八：cAdvisor 容器监控

## 阶段目标

- 理解为什么 Node Exporter 不适合监控容器；
- 用 cAdvisor 采集所有运行中容器的 CPU、内存、网络、文件系统指标；
- 完成 Prometheus 采集与 Grafana 看板。

## 8.1 cAdvisor 简介

- **是什么**：cAdvisor（Container Advisor，容器顾问）是 Google 开源的容器监控守护进程，收集、聚合、处理并导出本机所有运行容器的资源隔离参数、资源使用历史、直方图和网络统计，默认在 8080 端口暴露 `/metrics`。
- **类比**：Node Exporter 是给"整栋房子"装的总电表，cAdvisor 是给房子里每个"集装箱房间"单独装的电表水表。
- **为什么需要**：容器共享宿主机内核、数量多、生命周期短，需要按容器维度统计资源；cAdvisor 通过 Linux 的 cgroups 获取这些数据。

要点：

- 一个 cAdvisor **只监控一台主机**；Kubernetes 中以 DaemonSet 部署到每个节点；
- cAdvisor 内置在 kubelet 中；Kubernetes 1.12 之后移除了 cAdvisor 独立的 4194 端口；
- 项目主页：`https://github.com/google/cadvisor`。

## 8.2 Docker 方式部署 cAdvisor（推荐）

在**运行容器的主机**（如 app01）执行，用户 root。

**第 1 步：准备 Docker**

```bash
apt update && apt -y install docker.io
```

配置镜像加速与日志轮转，编辑 `/etc/docker/daemon.json`：

```json
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://docker.1panel.live",
    "https://hub.rat.dev"
  ],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "3"
  }
}
```

```bash
systemctl restart docker
docker info | grep -A3 'Registry Mirrors'
```

**第 2 步：启动 cAdvisor 容器**

```bash
VERSION=v0.60.6
docker run -d \
  --volume=/:/rootfs:ro \
  --volume=/var/run:/var/run:ro \
  --volume=/sys:/sys:ro \
  --volume=/var/lib/docker/:/var/lib/docker:ro \
  --volume=/dev/disk/:/dev/disk:ro \
  --publish=8080:8080 \
  --detach=true \
  --name=cadvisor \
  --restart=always \
  --privileged \
  --device=/dev/kmsg \
  ghcr.io/google/cadvisor:$VERSION
```

挂载参数解释：

| 挂载 | 作用 |
| --- | --- |
| `/:/rootfs:ro` | 只读挂载宿主机根文件系统，用于识别容器在宿主机上的路径 |
| `/var/run:/var/run:ro` | 读取容器运行时的 socket 等信息 |
| `/sys:/sys:ro` | 读取 cgroups 资源统计（核心数据来源） |
| `/var/lib/docker:/var/lib/docker:ro` | 读取 Docker 容器/镜像层信息 |
| `/dev/disk:/dev/disk:ro` | 读取磁盘设备信息 |

其他参数：`--privileged` 授予特权（cAdvisor 需要访问 cgroups、设备）；`--device=/dev/kmsg` 提供内核日志设备；`ro` 表示只读，保证 cAdvisor 不会改动宿主机。

::: tip
镜像已迁移到 GitHub 容器仓库 `ghcr.io/google/cadvisor`。拉不下来时用国内镜像：`registry.cn-beijing.aliyuncs.com/wangxiaochun/cadvisor:v0.51.0`（第三方同步，版本可能滞后），或通过加速代理拉取。使用 containerd 运行时时，把 `/var/lib/docker` 挂载换成 `/var/lib/containerd`。
:::

**第 3 步：验证**

```bash
ss -lntp | grep 8080
curl -s localhost:8080/metrics | grep -E 'cadvisor_version_info|container_memory_usage_bytes'
```

预期输出（节选）：

```text
cadvisor_version_info{cadvisorRevision="...",cadvisorVersion="v0.60.6",dockerVersion="..."} 1
container_memory_usage_bytes{id="/",image="",name=""} 1.23e+09
```

浏览器访问 `http://【应用服务器IP】:8080/` 能看到 cAdvisor 自带的容器列表界面。

## 8.3 二进制方式（备选）

```bash
cd /usr/local
wget https://github.com/google/cadvisor/releases/download/v0.60.6/cadvisor-v0.60.6-linux-amd64
install cadvisor-v0.60.6-linux-amd64 /usr/local/bin/cadvisor
```

创建服务文件 `/etc/systemd/system/cadvisor.service`：

```text
[Unit]
Description=cAdvisor
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/cadvisor -port=8080
Restart=on-failure
LimitNOFILE=100000

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable --now cadvisor
```

::: warning
cAdvisor 需要读取 cgroups 与设备信息，**不能以普通用户启动（权限不足）**；二进制方式用 root 运行，容器方式用 privileged。
:::

## 8.4 Prometheus 采集

编辑 `/usr/local/prometheus/conf/prometheus.yml` 加：

```yaml
  - job_name: 'cadvisor'
  static_configs:
    - targets:
        - '【应用服务器IP】:8080'
      labels:
        app: cadvisor
```

有多台容器主机就把它们都列进 targets，或用文件发现管理。

```bash
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus
```

验证：Targets 页 cadvisor 目标为 UP。

## 8.5 cAdvisor 常用指标

| 指标 | 类型 | 含义 |
| --- | --- | --- |
| `container_cpu_usage_seconds_total` | counter | 容器累计 CPU 占用时间（秒） |
| `container_cpu_user_seconds_total` | counter | 累计用户态 CPU 时间 |
| `container_cpu_system_seconds_total` | counter | 累计内核态 CPU 时间 |
| `container_cpu_load_average_10s` | gauge | 过去 10 秒容器 CPU 平均负载 |
| `container_cpu_cfs_throttled_seconds_total` | counter | 容器被 CPU 限流（throttle）的累计时间 |
| `container_memory_usage_bytes` | gauge | 容器当前内存使用量 |
| `container_memory_working_set_bytes` | gauge | 工作集内存（**判断 OOM 的主要依据**） |
| `container_memory_max_usage_bytes` | gauge | 历史最大内存使用量 |
| `container_spec_memory_limit_bytes` | gauge | 容器内存限制（未限制为 0） |
| `container_network_receive_bytes_total` | counter | 网络累计接收字节 |
| `container_network_transmit_bytes_total` | counter | 网络累计发送字节 |
| `container_network_receive_errors_total` | counter | 网络接收错误累计 |
| `container_fs_reads_bytes_total` | counter | 文件系统累计读取字节 |
| `container_fs_writes_bytes_total` | counter | 文件系统累计写入字节 |
| `container_start_time_seconds` | gauge | 容器启动时间戳 |
| `machine_cpu_cores` | gauge | 宿主机 CPU 核数 |
| `machine_memory_bytes` | gauge | 宿主机总内存 |

## 8.6 常用 PromQL

**单个容器 CPU 使用率（百分比，按容器名）**：

```promql
sum(rate(container_cpu_usage_seconds_total{image!="",name="【容器名】"}[1m])) by (name) * 100
```

**所有容器 CPU 使用率**：

```promql
sum(rate(container_cpu_usage_seconds_total{image!="",name=~".+"}[1m])) by (name) * 100
```

`{image!=""}` 过滤掉宿主机自身的聚合序列，只保留真正的容器；`name=~".+"` 要求 name 非空。

**容器内存使用率（相对限制值）**：

```promql
container_memory_working_set_bytes{image!=""} / container_spec_memory_limit_bytes{image!=""} * 100
```

::: warning
如果容器启动时**没有设置内存限制**，`container_spec_memory_limit_bytes` 为 0，上面的除法会得到无意义的无穷大或被忽略。生产必须给容器设内存限制（docker `--memory`、compose `mem_limit`/`deploy.resources`）。
:::

**容器网络接收速率（字节/秒）**：

```promql
sum(rate(container_network_receive_bytes_total{image!=""}[1m])) by (name)
```

**容器网络发送速率**：

```promql
sum(rate(container_network_transmit_bytes_total{image!=""}[1m])) by (name)
```

**容器磁盘写入速率**：

```promql
sum(rate(container_fs_writes_bytes_total{image!=""}[1m])) by (name)
```

## 8.7 Grafana 看板

Grafana 导入看板 **193**（经典 Docker 监控）或 **14282**：

```text
https://grafana.com/grafana/dashboards/193
https://grafana.com/grafana/dashboards/14282
```

看板若没有按容器过滤的下拉框，可自定义变量：看板设置 → Variables → New，变量名如 `container_name`，查询用：

```promql
label_values(container_memory_usage_bytes{image!=""}, name)
```

保存后顶部出现容器名下拉框，面板查询里用 `{name=~"$container_name"}` 过滤。

## 8.8 Kubernetes DaemonSet 方式（了解）

cAdvisor 以 DaemonSet 部署到每个节点（含 master，用 tolerations 容忍控制面污点），hostNetwork 使用宿主机网络，挂载宿主机的 /、/var/run、/sys、/var/lib/docker（containerd 环境为 /var/lib/containerd）、/dev/disk。关键结构：

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: cadvisor
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app: cadvisor
  template:
    metadata:
      labels:
        app: cadvisor
    spec:
      tolerations:
        - key: node-role.kubernetes.io/control-plane
          operator: Exists
          effect: NoSchedule
      hostNetwork: true
      restartPolicy: Always
      volumes:
        - name: root
          hostPath: {path: /}
        - name: run
          hostPath: {path: /var/run}
        - name: sys
          hostPath: {path: /sys}
        - name: docker
          hostPath: {path: /var/lib/docker}
        - name: dev
          hostPath: {path: /dev/disk}
      containers:
        - name: cadvisor
          image: ghcr.io/google/cadvisor:v0.60.6
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 8080
          volumeMounts:
            - {name: root, mountPath: /rootfs}
            - {name: run, mountPath: /var/run}
            - {name: sys, mountPath: /sys}
            - {name: docker, mountPath: /var/lib/docker}
            - {name: dev, mountPath: /dev/disk}
```

::: tip
现代 Kubernetes 中 kubelet 已内置 cAdvisor，kube-prometheus-stack 通过采集 kubelet 的 `/metrics/cadvisor` 端点即可获得容器指标，通常不需要再单独部署 cAdvisor DaemonSet——阶段十一详述。
:::

---

## 本阶段命令速查表

```bash
# 启动 cAdvisor（容器方式）
docker run -d --name=cadvisor --restart=always -p 8080:8080 \
  -v /:/rootfs:ro -v /var/run:/var/run:ro -v /sys:/sys:ro \
  -v /var/lib/docker:/var/lib/docker:ro -v /dev/disk:/dev/disk:ro \
  --privileged --device=/dev/kmsg \
  ghcr.io/google/cadvisor:v0.60.6

# 验证
curl -s localhost:8080/metrics | grep cadvisor_version_info

# Prometheus 采集 job 指向 8080
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus

# Grafana 看板
# 193 / 14282
```

---

## 本阶段常见坑与解决

**坑 1：cAdvisor 容器启动即退出**

- 报错/现象：`docker ps` 看不到，`docker logs cadvisor` 报挂载/权限错误。
- 原因：挂载路径不存在；缺少 privileged。
- 解决：确认宿主机挂载源存在；加 `--privileged --device=/dev/kmsg`。

**坑 2：拉取 ghcr.io 镜像超时**

- 报错原样：`Error response from daemon: Head "https://ghcr.io/...": dial tcp ... i/o timeout`。
- 原因：ghcr.io 在国内访问不稳定。
- 解决：用国内同步镜像（如阿里云个人同步仓库）或镜像加速；先在能访问的机器 `docker pull` 后 `docker save` 离线拷贝，再 `docker load`。

**坑 3：指标里把宿主机也当成容器**

- 现象：查询出现 name 为空、id 为 `/` 的超大序列。
- 原因：cAdvisor 同时输出宿主机聚合数据。
- 解决：查询统一加 `{image!=""}` 或 `{name=~".+"}` 过滤。

**坑 4：内存使用率算出来是无穷大/异常**

- 现象：内存面板数据离谱。
- 原因：容器没设内存限制，limit 为 0。
- 解决：给容器设内存限制；或改用相对宿主机总内存计算：`container_memory_working_set_bytes / machine_memory_bytes`。

**坑 5：containerd 环境下容器信息为空**

- 现象：cAdvisor 正常但看不到 containerd 容器。
- 原因：挂载的是 /var/lib/docker，而运行时是 containerd。
- 解决：挂载改为 `/var/lib/containerd:/var/lib/containerd:ro`。

**坑 6：8080 端口冲突**

- 报错原样：`docker: Error response from daemon: driver failed programming external connectivity on endpoint ... Bind for 0.0.0.0:8080 failed: port is already allocated.`
- 原因：宿主机 8080 已被其他服务占用。
- 解决：`ss -lntp | grep 8080` 找到占用者；改用 `-p 其他端口:8080`。

---
# 阶段九：Prometheus 联邦（Federation）

## 阶段目标

- 理解单个 Prometheus 的容量瓶颈；
- 掌握**分层联邦**的配置方法，实现"分节点采集、中心节点汇总"；
- 清楚联邦的能力边界（它不是高可用、不是长期存储）。

## 9.1 联邦说明

- **是什么**：联邦允许一台 Prometheus 从另一台 Prometheus 的 `/federate` 端点抓取数据。下层（从）节点各自采集一批目标，上层（主/中心）节点只从下层节点拉取汇总数据，Grafana 接中心节点。
- **类比**：像公司层级汇报——每个组长（从 Prometheus）统计本组数据，经理（中心 Prometheus）只汇总各组长的报表，不必直接管每个人。
- **为什么需要**：一台 Prometheus 能管理的目标数量有限，目标和序列持续增长后单机压力越来越大；联邦把采集压力分散到多台。

两种模式：

| 模式 | 说明 |
| --- | --- |
| **分层联邦（常用）** | 树形拓扑，上层从大量下层节点拉取**聚合**序列，可扩展到数十个数据中心、百万节点；下层保留实例级明细，上层只存作业级聚合 |
| 跨服务联邦 | 一个服务的 Prometheus 从另一个服务的 Prometheus 拉取选定数据，在单台里同时拥有两个数据集做查询/告警 |

**联邦的能力边界（务必清楚）**：

- 它**不是真正的高可用方案**（中心节点挂了全局视图就没了）；
- 它**不是全量存储**（上层只存匹配到的、通常是聚合后的指标）；
- 查询能力有限，适合做**全局视图和汇总指标**——中心节点只看各集群 CPU、内存、SLA、核心业务指标；
- 想要真正的 HA、全量指标和长期存储，需要 VictoriaMetrics、Thanos 等方案（阶段十讲 VictoriaMetrics）。

## 9.2 实战：分层联邦

### 9.2.1 规划

在星辰电商环境中扩展两台机器演示联邦：

| 角色 | 地址 |
| --- | --- |
| Prometheus 主（中心）节点 | 【监控服务器IP】（即 monitor，10.0.0.10） |
| 联邦从节点 1 | 【联邦节点1IP】（如 10.0.0.15） |
| 联邦从节点 2 | 【联邦节点2IP】（如 10.0.0.16） |
| Node Exporter（从节点1 负责） | 【Web服务器IP】、【应用服务器IP】 |
| Node Exporter（从节点2 负责） | 【数据库服务器IP】 |

### 9.2.2 部署各节点

三台 Prometheus 安装方法完全一样，按阶段二的二进制方式在从节点 1、从节点 2 各装一套 Prometheus（版本 3.15.0）；所有被监控主机按阶段二装好 Node Exporter。

### 9.2.3 配置从节点采集 Node Exporter

**从节点 1** 编辑 `/usr/local/prometheus/conf/prometheus.yml`：

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
scrape_configs:
  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]
  - job_name: "node_exporter"
    static_configs:
      - targets:
          - "【Web服务器IP】:9100"
          - "【应用服务器IP】:9100"
```

**从节点 2** 的 prometheus.yml：

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
scrape_configs:
  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]
  - job_name: "node_exporter"
    static_configs:
      - targets:
          - "【数据库服务器IP】:9100"
```

两台分别检查生效：

```bash
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus
```

验证：各自 Targets 页 node_exporter 目标为 UP，能查到本片区主机的指标。

### 9.2.4 配置中心节点汇总

`/federate` 端点返回所选时间序列的当前值。必须至少传一个 `match[]` URL 参数（即时向量选择器），多个 match[] 取并集。

在**中心节点（monitor）**编辑 `/usr/local/prometheus/conf/prometheus.yml`，追加两个 job：

```yaml
  - job_name: 'federate-01'
    scrape_interval: 15s
    honor_labels: true
    metrics_path: '/federate'
    params:
      'match[]':
        - '{job="prometheus"}'
        - '{job="node_exporter"}'
        - '{__name__=~"node.*"}'
    static_configs:
      - targets:
          - '【联邦节点1IP】:9090'

  - job_name: 'federate-02'
    scrape_interval: 15s
    honor_labels: true
    metrics_path: '/federate'
    params:
      'match[]':
        - '{job="prometheus"}'
        - '{job="node_exporter"}'
        - '{__name__=~"node.*"}'
    static_configs:
      - targets:
          - '【联邦节点2IP】:9090'
```

逐字段解释：

| 字段 | 作用 |
| --- | --- |
| `metrics_path: /federate` | 从源节点的联邦端点采集（默认采集路径是 /metrics，这里必须改） |
| `honor_labels: true` | **关键**：不覆盖源节点暴露的标签（如 instance、job），否则中心会把目标地址写成从节点地址，数据全乱 |
| `params.match[]` | 选择要拉取哪些序列；**不写 match[] 不会采集任何数据** |
| match 示例 `{job="node_exporter"}` | 只拉该 job 的数据，job 名必须与从节点配置的 job_name 完全匹配 |
| match 示例 `{__name__=~"node.*"}` | 拉所有以 node 开头的指标；多个 match 条件之间是**或（并集）**关系 |

检查生效：

```bash
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus
```

### 9.2.5 验证

- 中心节点 Targets 页：federate-01、federate-02 为 UP；
- 在中心节点 Graph 查询 `node_os_info`，能看到分布在各从节点后面的所有主机；
- 查询 `up`，能看到从节点及其下属目标；
- Grafana 数据源仍接中心节点，导入 8919 看板，能展示全部主机数据。

### 9.2.6 从节点扩容

在**从节点 1** 的 node_exporter job 里加新主机：

```yaml
  - job_name: "node_exporter"
    static_configs:
      - targets:
          - "【Web服务器IP】:9100"
          - "【应用服务器IP】:9100"
          - "【新主机IP】:9100"
```

```bash
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus
```

等一个抓取周期，中心节点自动汇总到新主机数据，**中心节点无需改动**——这就是联邦分层带来的扩展性：下层扩容不影响上层。

## 9.3 联邦层级拓扑

![Prometheus 联邦分层拓扑](/guide/diagrams/federation-hierarchy.svg)

::: tip
生产建议：① 中心节点只采集**记录规则产出的聚合指标**（如 `instance:node_cpu:avg_rate5m`），大幅减少上层序列量；② 中心节点可双活（两台采同样的从节点，配合 external_labels 区分）；③ 跨数据中心时从节点部署在各机房本地，中心通过内网专线/VPN 拉取。
:::

---

## 本阶段命令速查表

```bash
# 从节点：正常配置本地采集 job
# 中心节点：联邦 job 四要素
#   metrics_path: /federate
#   honor_labels: true
#   params.match[]: [选择器,...]
#   static_configs.targets: [从节点IP:9090]
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus

# 中心节点验证汇总结果
# Graph 查询 up 或 node_os_info，应看到所有片区主机
```

---

## 本阶段常见坑与解决

**坑 1：中心节点采集不到任何数据**

- 现象：federate 目标 UP，但查不到从节点的业务指标。
- 原因：没配 `match[]`，或 match 的 job 名与从节点 job_name 不一致。
- 解决：至少配一个 match[]；核对 job 名完全一致（大小写敏感）。

**坑 2：中心节点数据的 instance 全变成从节点地址**

- 现象：主机明细数据串了、标签不对。
- 原因：没设 `honor_labels: true`，中心用目标地址（从节点）覆盖了原始 instance 标签。
- 解决：联邦 job 必须 `honor_labels: true`。

**坑 3：metrics_path 忘了改**

- 报错/现象：federate 目标采集报错或数据不对。
- 原因：默认抓 /metrics，拿到的是从节点自身指标而非联邦数据。
- 解决：显式配置 `metrics_path: /federate`。

**坑 4：中心节点序列量爆炸**

- 现象：中心节点很快也扛不住。
- 原因：用 `{__name__=~".+"}` 把从节点全量明细都拉上来了。
- 解决：只拉聚合指标/记录规则结果；分层存储明细与汇总。

**坑 5：误以为联邦做了高可用**

- 现象：中心节点宕机后全局视图丢失。
- 原因：联邦是数据汇总方案，不是 HA。
- 解决：中心双活；真正 HA + 长期存储用 VictoriaMetrics/Thanos（阶段十）。

---
# 阶段十：Prometheus 存储与 VictoriaMetrics

## 阶段目标

- 理解本地 TSDB 的数据组织方式与保留策略；
- 会估算磁盘容量；
- 部署 **VictoriaMetrics 单机版和集群版**作为长期远程存储；
- 完成 Prometheus remote_write/remote_read 与 Grafana 对接。

## 10.1 本地 TSDB

### 10.1.1 存储机制（三句话）

- Prometheus 内置时序数据库 TSDB：最新数据先放内存（Head 块），同时写预写日志 WAL 防丢失；
- 每 2 小时把内存数据刷成一个不可修改的 Block（块）落盘，后台再把小块压缩合并成大块；
- 超过保留期限的块被删除。

### 10.1.2 数据目录结构

数据目录默认 `/usr/local/prometheus/data`：

```text
data/
├── 01GH5S5W4PDFXCS40VF7NZCP0G/     # 2 小时块（目录名是 ULID）
│   ├── chunks/                     # 时序数据，段文件如 000001，单段上限 512MB
│   ├── index                       # 索引：按指标名+标签定位序列在 chunks 中的位置
│   ├── meta.json                   # 块元数据（样本数、时间范围、压缩级别）
│   └── tombstones                  # 软删除标记（删除不立即清数据，查询时过滤）
├── chunks_head/                    # 内存 Head 块通过 mmap 映射的近期数据
├── wal/                            # 预写日志，段默认 128MB，含 checkpoint
├── lock
└── queries.active
```

WAL 是"先写日志再改数据"的顺序日志，崩溃后重放 WAL 即可恢复；至少保留 3 个 WAL 段，高流量实例保留更多以覆盖 2 小时原始数据。

### 10.1.3 本地存储参数

在服务文件 ExecStart 配置：

| 参数 | 作用 |
| --- | --- |
| `--storage.tsdb.path` | 数据目录，默认安装目录下 data |
| `--storage.tsdb.retention.time` | 数据保留时间，默认 15d；如 `30d`、`90d` |
| `--storage.tsdb.retention.size` | 块数据总磁盘上限（不含 WAL），如 `100GB`；**超限先删最旧数据** |
| `--storage.tsdb.wal-compression` | WAL 压缩，默认开启 |

::: warning
retention.time 和 retention.size **任一满足就删旧数据**。retention.size 不是单段文件大小，是所有块的总量。生产建议两个都设：时间兜底 + 空间兜底，防止磁盘被写爆。
:::

### 10.1.4 磁盘容量估算

公式：

```text
所需磁盘 = 保留秒数 × 每秒摄入样本数 × 每样本字节数
```

Prometheus 本地压缩后每样本约 1～2 字节（Gorilla 压缩），规划时按 2 字节、再乘 2～3 倍冗余（WAL、chunks_head 峰值）较稳妥。

示例：每秒摄入 10000 样本、保留 30 天：

```text
30×86400 秒 × 10000 × 2 字节 ≈ 518 GB（块数据），再留 WAL/Head 冗余
```

磁盘最小尺寸主要取决于 wal 和 chunks_head 的峰值空间（每 2 小时达一次峰值）。

## 10.2 VictoriaMetrics 简介

- **是什么**：VictoriaMetrics（VM）是 Go 实现的、可水平扩展的时序数据库与监控方案，可作为 Prometheus 的长期存储，兼容 Prometheus 查询 API（Grafana 可直接把它当 Prometheus 数据源）。
- **为什么需要**：本地 TSDB 是单点、不支持集群；VM 解决高可用、水平扩展和长期存储，且数据本地持久化，查询性能优于依赖对象存储的 Thanos。
- **版本选择**：数据摄入低于 100 万样本/秒用**单机版**（单机本身不内置告警，告警可用 vmalert）；需要水平拆分、多租户用**集群版**。

官方资源：

```text
官网：https://victoriametrics.com/
文档：https://docs.victoriametrics.com/
单机文档：https://docs.victoriametrics.com/single-server-victoriametrics/
集群文档：https://docs.victoriametrics.com/cluster-victoriametrics/
```

## 10.3 单机版部署

在**监控服务器 monitor**（或独立存储主机）执行，用户 root。

**第 1 步：下载**

```bash
cd /usr/local/src
VM_VERSION=v1.152.0
wget https://github.com/VictoriaMetrics/VictoriaMetrics/releases/download/${VM_VERSION}/victoria-metrics-linux-amd64-${VM_VERSION}.tar.gz
tar xf victoria-metrics-linux-amd64-${VM_VERSION}.tar.gz
mv victoria-metrics-prod /usr/local/bin/
```

::: tip
不要下载 enterprise（企业版，需授权）。GitHub 慢时可在 URL 前加 `https://ghproxy.net/` 等代理。
:::

**第 2 步：用户与目录**

```bash
useradd -r -s /usr/sbin/nologin victoriametrics
mkdir -p /data/victoriametrics
chown victoriametrics:victoriametrics /data/victoriametrics
```

**第 3 步：服务文件**

```bash
cat > /etc/systemd/system/victoriametrics.service <<'EOF'
[Unit]
Description=VictoriaMetrics
Documentation=https://docs.victoriametrics.com/single-server-victoriametrics/
After=network.target

[Service]
Type=simple
User=victoriametrics
Group=victoriametrics
ExecStart=/usr/local/bin/victoria-metrics-prod \
  -httpListenAddr=0.0.0.0:8428 \
  -storageDataPath=/data/victoriametrics \
  -retentionPeriod=6 \
  -loggerTimezone=Asia/Shanghai
Restart=on-failure
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable --now victoriametrics
ss -lntp | grep 8428
```

参数解释：`-httpListenAddr` 监听地址，默认 8428；`-storageDataPath` 数据目录；`-retentionPeriod` 保留时长，不带后缀单位是**月**（如 6 = 6 个月），也支持 h/d/w/y；`-loggerTimezone` 日志时区。

**第 4 步：Prometheus 远程写入**，编辑 `/usr/local/prometheus/conf/prometheus.yml`，与 global 平级加：

```yaml
remote_write:
  - url: http://【监控服务器IP】:8428/api/v1/write
```

```bash
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus
```

**第 5 步：验证**

- VM 自带查询界面：`http://【监控服务器IP】:8428/vmui`，能查到 Prometheus 写入的指标；
- Grafana 添加 Prometheus 类型数据源，URL 填 `http://【监控服务器IP】:8428`，保存测试成功；
- 导入 1860 等看板时选这个数据源，数据正常展示。

Docker 方式（备选）：

```bash
docker run -d --name victoriametrics --restart=always -p 8428:8428 \
  -v /data/victoriametrics:/victoria-metrics-data \
  victoriametrics/victoria-metrics:v1.152.0
```

## 10.4 集群版

### 10.4.1 组件与端口

| 组件 | 职责 | 端口 |
| --- | --- | --- |
| **vminsert** | 接收写入（实现 remote_write），按指标名+标签一致性哈希分片到 vmstorage；无状态、易扩容 | 8480（HTTP） |
| **vmstorage** | 存储数据（有状态），节点间互不交互，分片与副本由 vminsert/vmselect 处理 | 8482（HTTP）、8400（对 vminsert）、8401（对 vmselect） |
| **vmselect** | 接收查询（实现 remote_read），向各 vmstorage 查询后合并返回；无状态 | 8481（HTTP） |
| vmagent | 替代 Prometheus 做抓取，支持多后端、本地缓存，pull/push 都支持 | 8429 |
| vmalert | 告警/记录规则执行，配合 VM 使用 | 8880 |

多租户端点格式：

```text
写入：http://<vminsert>:8480/insert/<accountID>/prometheus
查询：http://<vmselect>:8481/select/<accountID>/prometheus
```

`<accountID>` 是租户标识（如 0）。副本由 vminsert 的 `-replicationFactor` 控制，生产推荐 2 或 3；副本自动写到哈希环的相邻节点。一个 vmstorage 故障时约丢失 1/N 历史数据（N 为 storage 数），有副本则不丢。

### 10.4.2 二进制部署（3 节点，每节点跑三个组件）

在**三个节点**（如 10.0.0.201、202、203）分别执行。

**第 1 步：下载集群二进制**

```bash
cd /usr/local/src
VM_VERSION=v1.152.0
wget https://github.com/VictoriaMetrics/VictoriaMetrics/releases/download/${VM_VERSION}/victoria-metrics-linux-amd64-${VM_VERSION}-cluster.tar.gz
tar xf victoria-metrics-linux-amd64-${VM_VERSION}-cluster.tar.gz -C /usr/local/bin/
ls /usr/local/bin/ | grep vm
```

解压得到 `vminsert-prod`、`vmselect-prod`、`vmstorage-prod`。

**第 2 步：vmstorage（每个节点，注意 IP 不同）**

```bash
useradd -r -s /usr/sbin/nologin victoriametrics
mkdir -p /data/vmstorage
chown -R victoriametrics:victoriametrics /data/vmstorage

cat > /etc/systemd/system/vmstorage.service <<'EOF'
[Unit]
Description=VM storage
After=network.target

[Service]
Type=simple
User=victoriametrics
ExecStart=/usr/local/bin/vmstorage-prod \
  -httpListenAddr :8482 \
  -vminsertAddr :8400 \
  -vmselectAddr :8401 \
  -storageDataPath /data/vmstorage \
  -loggerTimezone Asia/Shanghai
Restart=on-failure
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable --now vmstorage
ss -lntp | grep -E '8482|8400|8401'
```

**第 3 步：vminsert（每个节点，storageNode 列全部三个 storage）**

```bash
cat > /etc/systemd/system/vminsert.service <<'EOF'
[Unit]
Description=VM insert
After=network.target

[Service]
Type=simple
User=victoriametrics
ExecStart=/usr/local/bin/vminsert-prod \
  -httpListenAddr :8480 \
  -storageNode=10.0.0.201:8400,10.0.0.202:8400,10.0.0.203:8400 \
  -replicationFactor=2
Restart=on-failure
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable --now vminsert
ss -lntp | grep 8480
```

**第 4 步：vmselect（每个节点）**

```bash
cat > /etc/systemd/system/vmselect.service <<'EOF'
[Unit]
Description=VM select
After=network.target

[Service]
Type=simple
User=victoriametrics
ExecStart=/usr/local/bin/vmselect-prod \
  -httpListenAddr :8481 \
  -storageNode=10.0.0.201:8401,10.0.0.202:8401,10.0.0.203:8401 \
  -dedup.minScrapeInterval=1ms
Restart=on-failure
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable --now vmselect
ss -lntp | grep 8481
```

`-dedup.minScrapeInterval` 用于副本数据去重（replicationFactor>1 时需要）。

集群拓扑：

![VictoriaMetrics 集群拓扑](/guide/diagrams/victoriametrics-cluster.svg)

**第 5 步：Prometheus 对接集群**，编辑 prometheus.yml：

```yaml
remote_write:
  - url: http://10.0.0.201:8480/insert/0/prometheus
  - url: http://10.0.0.202:8480/insert/0/prometheus
  - url: http://10.0.0.203:8480/insert/0/prometheus
remote_read:
  - url: http://10.0.0.201:8481/select/0/prometheus
  - url: http://10.0.0.202:8481/select/0/prometheus
  - url: http://10.0.0.203:8481/select/0/prometheus
```

写多个 remote_write 是为了高可用（任一 vminsert 可用即可写入，配合去重）；也可以只写一个，前面挂负载均衡。

**第 6 步：Grafana 与负载均衡**

Grafana 数据源 URL 填任一 vmselect：`http://10.0.0.201:8481/select/0/prometheus`。生产建议用 HAProxy 对 vmselect（8481）、vminsert（8480）做 TCP 负载均衡，数据源与写入地址统一用 VIP。HAProxy 示例：

```text
listen vmselect-8481
    bind 10.0.0.200:8481
    mode tcp
    server vmselect1 10.0.0.201:8481 check inter 1s fall 3 rise 5
    server vmselect2 10.0.0.202:8481 check inter 1s fall 3 rise 5
    server vmselect3 10.0.0.203:8481 check inter 1s fall 3 rise 5
```

验证：导入 8919、11074、13824 等看板，选 VM 数据源，数据正常；停掉一个 vmstorage，查询与写入仍可用（副本+去重生效）。

::: warning
生产最佳实践：① vmstorage 数量变更必须同步反映到所有 vminsert/vmselect 的 storageNode 列表；② 扩容按"数据多则加 storage、查询多则加 select、写入多则加 insert"；③ storage 数据目录务必挂独立数据盘并做好备份/快照；④ 镜像/二进制不要用 latest，固定版本。
:::

---

## 本阶段命令速查表

```bash
# === 本地保留策略（prometheus 服务文件）===
# --storage.tsdb.retention.time=30d
# --storage.tsdb.retention.size=100GB

# === VM 单机 ===
systemctl enable --now victoriametrics   # 8428
# prometheus.yml: remote_write url .../api/v1/write

# === VM 集群（每节点三服务）===
systemctl enable --now vmstorage vminsert vmselect
# 端口：8480 insert / 8481 select / 8482 storage http / 8400 / 8401

# === 验证 ===
curl -s http://【监控服务器IP】:8428/metrics | grep vm_rows_inserted_total
```

---

## 本阶段常见坑与解决

**坑 1：磁盘很快被写满**

- 现象：Prometheus 数据盘告警/写满。
- 原因：没设 retention 或保留过长；高基数标签导致序列爆炸。
- 解决：设 retention.time + size；排查高基数标签（如把 user_id、request_id 当标签）。

**坑 2：单机 VM 数据没保留够时间**

- 现象：历史数据很快没了。
- 原因：`-retentionPeriod` 不带后缀单位是**月**，但可能误写或磁盘超限触发删除。
- 解决：明确单位（如 `180d`、`6`）；同时检查磁盘空间是否先触顶。

**坑 3：集群写入报 storage 不可达**

- 报错原样：`cannot obtain connection to vmstorage ... dial tcp 10.0.0.201:8400: connect: connection refused`。
- 原因：vmstorage 未启动；8400/8401 端口未放通；storageNode 地址写错。
- 解决：先确保所有 vmstorage 健康；放通端口；核对 storageNode 列表。

**坑 4：副本数据重复展示**

- 现象：同一条数据在 Grafana 出现两份。
- 原因：replicationFactor>1 但 vmselect 没开去重。
- 解决：vmselect 加 `-dedup.minScrapeInterval`（如 1ms 或与抓取间隔一致）。

**坑 5：改了 vmstorage 数量后数据错乱/缺失**

- 现象：扩缩容 storage 后部分序列查不到。
- 原因：vminsert/vmselect 的 storageNode 列表没同步更新。
- 解决：所有 insert/select 同步更新并重启；集群扩缩容按官方文档的分片再平衡流程操作。

**坑 6：下载了 enterprise 版本启动报授权错误**

- 报错原样：启动提示 license required / enterprise feature。
- 原因：误下企业版。
- 解决：下载不带 enterprise 后缀的开源版（victoria-metrics / -cluster 包）。

**坑 7：远程写入后 VM 里没数据**

- 现象：remote_write 配了但 vmui 查不到。
- 原因：URL 路径错（单机用 /api/v1/write，集群用 /insert/0/prometheus）；网络不通。
- 解决：核对端点路径；在 Prometheus 服务器 curl VM 地址验证连通；看 Prometheus 日志 remote_write 报错。

---
# 阶段十一：Kubernetes 集成 Prometheus

## 阶段目标

- 掌握在 Kubernetes 中部署 Prometheus 的三种方式：**YAML、Helm、Operator**；
- 会用 ServiceMonitor、PodMonitor、Probe、PrometheusRule 等 CRD；
- 完成对 API Server、kubelet、cAdvisor、业务 Pod、Controller、Scheduler、Node Exporter 的完整监控。

Kubernetes 是 Prometheus 最典型的使用场景：Pod 频繁创建销毁，静态配置完全不可行，必须用服务发现。

## 11.1 方式一：YAML 文件部署

YAML 方式需要自己写全：Namespace、ServiceAccount、ClusterRole/ClusterRoleBinding（RBAC）、ConfigMap（prometheus.yml）、Deployment/StatefulSet、Service。

### 11.1.1 RBAC 权限

Prometheus 需要通过 API Server 发现资源，ClusterRole 至少包含：

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: prometheus
rules:
  - apiGroups: [""]
    resources:
      - nodes
      - nodes/proxy
      - nodes/metrics
      - services
      - endpoints
      - pods
      - ingresses
      - configmaps
    verbs: ["get", "list", "watch"]
  - apiGroups: ["networking.k8s.io"]
    resources: ["ingresses", "ingresses/status"]
    verbs: ["get", "list", "watch"]
  - apiGroups: ["discovery.k8s.io"]
    resources: ["endpointslices"]
    verbs: ["get", "list", "watch"]
  - nonResourceURLs: ["/metrics"]
    verbs: ["get"]
```

`get/list/watch` 分别是读取单个、列全部、监听变更；服务发现必须有 list 和 watch。

### 11.1.2 ConfigMap 与 Deployment

官方示例（推荐直接参考，持续更新）：

```text
https://github.com/prometheus/prometheus/blob/main/documentation/examples/prometheus-kubernetes.yml
```

把该文件内容放进 ConfigMap 的 data，Deployment 挂载到 `/etc/prometheus/prometheus.yml`，启动参数 `--config.file=/etc/prometheus/prometheus.yml`。

最小可用示例（含 API Server、节点、Pod 三类采集）：

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s
    scrape_configs:
      - job_name: 'kubernetes-apiservers'
        kubernetes_sd_configs:
          - role: endpoints
        scheme: https
        tls_config:
          ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
        bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
        relabel_configs:
          - source_labels: [__meta_kubernetes_namespace, __meta_kubernetes_service_name, __meta_kubernetes_endpoint_port_name]
            action: keep
            regex: default;kubernetes;https
      - job_name: 'kubernetes-pods'
        kubernetes_sd_configs:
          - role: pod
        relabel_configs:
          - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
            action: keep
            regex: 'true'
          - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_port]
            target_label: __address__
            regex: ([^:]+)(?::\d+)?;(\d+)
            replacement: $1:$2
          - action: labelmap
            regex: __meta_kubernetes_pod_label_(.+)
```

Deployment 关键片段（生产建议用 StatefulSet + PVC，见 11.2）：

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels: {app: prometheus}
  template:
    metadata:
      labels: {app: prometheus}
    spec:
      serviceAccountName: prometheus
      containers:
        - name: prometheus
          image: prom/prometheus:v3.15.0
          args:
            - --config.file=/etc/prometheus/prometheus.yml
            - --storage.tsdb.path=/prometheus
            - --storage.tsdb.retention.time=15d
            - --web.enable-lifecycle
          ports:
            - containerPort: 9090
          volumeMounts:
            - name: config
              mountPath: /etc/prometheus
            - name: data
              mountPath: /prometheus
      volumes:
        - name: config
          configMap: {name: prometheus-config}
        - name: data
          emptyDir: {}
```

::: warning
emptyDir 数据随 Pod 删除而丢失，**只能用于测试**。生产必须用 StatefulSet + PVC（动态供给），见 Helm 部分。
:::

## 11.2 方式二：Helm 部署

Helm 把上面的资源模板化，是最常用的部署方式。两个常用 chart：

| chart | 内容 |
| --- | --- |
| `prometheus-community/prometheus` | Prometheus + Alertmanager（子 chart），较精简 |
| `prometheus-community/kube-prometheus-stack` | **全家桶（推荐）**：Operator + Prometheus + Alertmanager + Grafana + kube-state-metrics + node-exporter + 全套默认规则 |

### 11.2.1 安装 prometheus chart

**第 1 步：添加仓库**

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
```

**第 2 步：准备 values** `prom-values.yaml`（需要提前有 StorageClass，如 `sc-nfs`）：

```yaml
server:
  global:
    scrape_interval: 1m
    scrape_timeout: 10s
    evaluation_interval: 1m

  ingress:
    enabled: true
    ingressClassName: nginx
    hosts:
      - prometheus.【你的域名】
    path: /
    pathType: Prefix

  persistentVolume:
    enabled: true
    accessModes: ["ReadWriteOnce"]
    size: 8Gi
    storageClass: "sc-nfs"
    mountPath: /data

  replicaCount: 1

  service:
    enabled: true
    type: ClusterIP
    servicePort: 9090

alertmanager:
  enabled: true
  persistence:
    size: 2Gi
    storageClass: "sc-nfs"
    accessModes: ["ReadWriteOnce"]
```

**第 3 步：安装**

```bash
helm install prometheus prometheus-community/prometheus \
  --namespace monitoring --create-namespace \
  --values prom-values.yaml
```

验证：

```bash
kubectl get pods,svc -n monitoring
```

### 11.2.2 （可选）prometheus-adapter

prometheus-adapter 把 Prometheus 指标转成 Kubernetes 自定义指标 API，供 HPA 使用：

```bash
helm install prometheus-adapter prometheus-community/prometheus-adapter \
  --namespace monitoring \
  --set prometheus.url=http://prometheus-server.monitoring.svc \
  --set prometheus.port=9090
```

### 11.2.3 （推荐）kube-prometheus-stack

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

cat > stack-values.yaml <<'EOF'
prometheus:
  prometheusSpec:
    retention: 15d
    retentionSize: "10GiB"
    resources:
      requests: {cpu: 200m, memory: 500Mi}
      limits: {cpu: "1", memory: 1Gi}
    storageSpec:
      volumeClaimTemplate:
        spec:
          storageClassName: sc-nfs
          accessModes: ["ReadWriteOnce"]
          resources:
            requests:
              storage: 20Gi

alertmanager:
  alertmanagerSpec:
    storage:
      volumeClaimTemplate:
        spec:
          storageClassName: sc-nfs
          accessModes: ["ReadWriteOnce"]
          resources:
            requests:
              storage: 5Gi

grafana:
  enabled: true
  adminPassword: 【Grafana管理员密码】
  ingress:
    enabled: true
    ingressClassName: nginx
    hosts:
      - grafana.【你的域名】
EOF

helm install kps prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  --values stack-values.yaml
```

::: tip
国内拉取 `quay.io`、`registry.k8s.io`、`ghcr.io` 镜像可能失败。两种解决：① 提前把镜像同步到私有仓库，用 `--set` 覆盖镜像地址；② 配置容器运行时的镜像加速。chart 版本固定（如 91.8.0），不要用不确定的最新版直接上生产。
:::

## 11.3 方式三：Operator（kube-prometheus）

### 11.3.1 Operator 原理（三句话）

- Prometheus Operator 是一个自定义控制器，用 Kubernetes 声明式方式管理 Prometheus 监控套件；
- 它通过一组 CRD 描述监控对象，Operator 监听这些 CRD 并自动生成/更新 Prometheus 配置；
- 业务方只需创建 ServiceMonitor 等对象，不必手写 prometheus.yml。

核心 CRD：

| CRD | 作用 |
| --- | --- |
| `Prometheus` | 定义 Prometheus Server 实例（副本、版本、存储、规则引用） |
| `Alertmanager` | 定义 Alertmanager 实例 |
| `ServiceMonitor` | 声明如何采集一组 Service（通过 label 选择） |
| `PodMonitor` | 声明如何采集一组 Pod |
| `Probe` | 黑盒监控（Ingress 或静态目标） |
| `PrometheusRule` | 声明式定义告警/记录规则 |
| `AlertmanagerConfig` | 声明式定义 Alertmanager 配置段 |
| `ScrapeConfig` | 直接提供 scrape_config 配置段（支持 Consul 等发现） |

### 11.3.2 获取清单

```bash
cd /usr/local
VERSION=0.19.0
wget https://github.com/prometheus-operator/kube-prometheus/archive/refs/tags/v${VERSION}.tar.gz
tar xf v${VERSION}.tar.gz -C /usr/local
cd /usr/local/kube-prometheus-${VERSION}
```

目录结构：

| 目录 | 内容 |
| --- | --- |
| `manifests/setup/` | CRD、Operator 命名空间与 Operator 自身（先装） |
| `manifests/` | Prometheus、Alertmanager、Grafana、各 Exporter、默认规则（后装） |

### 11.3.3 修改 Service 访问方式

编辑 `manifests/prometheus-service.yaml`，改为 NodePort（或 LoadBalancer）：

```yaml
spec:
  type: NodePort
  ports:
    - name: web
      port: 9090
      targetPort: web
      nodePort: 30090
```

同样修改 `manifests/grafana-service.yaml`（nodePort 30030）、`manifests/alertmanager-service.yaml`（nodePort 30093）。

### 11.3.4 替换镜像（国内环境）

查看所有镜像：

```bash
grep -h 'image:' manifests/*.yaml manifests/setup/*.yaml | sort -u
```

把 quay.io / registry.k8s.io / ghcr.io 的镜像改成私有仓库地址（批量 sed 或逐个编辑），提前在私有仓库准备好这些镜像。

### 11.3.5 安装

```bash
kubectl create ns monitoring

# 先装 setup（CRD + Operator）
kubectl apply -f manifests/setup/
# 若提示 "Too long"（一行内容过长），改用：
kubectl create -f manifests/setup/

# 等待 Operator 就绪
kubectl get pods -n monitoring

# 再装监控组件
kubectl apply -f manifests/
```

::: warning
使用 Calico 网络插件时，默认 NetworkPolicy 可能阻止访问，需要删除：

```bash
kubectl delete -f manifests/prometheus-networkPolicy.yaml
kubectl delete -f manifests/grafana-networkPolicy.yaml
kubectl delete -f manifests/alertmanager-networkPolicy.yaml
```
:::

验证：

```bash
kubectl get pods -n monitoring
kubectl get svc -n monitoring
```

预期：prometheus-k8s、alertmanager-main（3 副本）、grafana、node-exporter（DaemonSet）、kube-state-metrics、blackbox-exporter、prometheus-operator 全部 Running。

Operator 拓扑：

![Kubernetes Operator 监控拓扑](/guide/diagrams/kubernetes-operator.svg)

---
## 11.4 使用：业务接入监控

### 11.4.1 ServiceMonitor 接入业务

业务 Deployment + Service 正常部署，然后创建 ServiceMonitor。

**第 1 步：业务 Deployment**（示例）：

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: metrics-app
spec:
  replicas: 2
  selector:
    matchLabels: {app: metrics-app}
  template:
    metadata:
      labels: {app: metrics-app}
    spec:
      containers:
        - name: metrics-app
          image: registry.cn-beijing.aliyuncs.com/【你的命名空间】/metrics-app:v0.1
          ports:
            - name: web
              containerPort: 80
          resources:
            requests: {cpu: 100m, memory: 128Mi}
            limits: {cpu: 500m, memory: 256Mi}
```

**第 2 步：Service**：

```yaml
apiVersion: v1
kind: Service
metadata:
  name: metrics-app
  labels:
    app: metrics-app
spec:
  type: ClusterIP
  ports:
    - name: web
      port: 80
      targetPort: web
  selector:
    app: metrics-app
```

**第 3 步：ServiceMonitor**：

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: metrics-app
  namespace: monitoring
  labels:
    release: kps
spec:
  selector:
    matchLabels:
      app: metrics-app
  endpoints:
    - port: web
      interval: 15s
      path: /metrics
```

字段解释：`selector.matchLabels` 选择带这些标签的 Service；`endpoints.port` 用 Service 端口名（不是数字）；`path` 指标路径；`labels.release` 要与 Prometheus CRD 里 serviceMonitorSelector 匹配（kube-prometheus-stack 装的默认要求带 `release=<release名>`，自己装的 kube-prometheus 通常无此要求——不生效时先查这里）。

### 11.4.2 Probe：黑盒监控外部/内部目标

```yaml
apiVersion: monitoring.coreos.com/v1
kind: Probe
metadata:
  name: web-probe
  namespace: monitoring
spec:
  jobName: http-get
  interval: 60s
  module: http_2xx
  prober:
    url: blackbox-exporter.monitoring.svc:19115
    scheme: http
    path: /probe
  targets:
    staticConfig:
      static:
        - http://www.【你的域名】
        - https://www.baidu.com
```

### 11.4.3 PrometheusRule：告警/记录规则

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: business-rules
  namespace: monitoring
  labels:
    prometheus: k8s
    role: alert-rules
spec:
  groups:
    - name: business.rules
      rules:
        - alert: BusinessPodDown
          expr: up{pod=~"metrics-app.*"} == 0
          for: 1m
          labels:
            severity: critical
          annotations:
            summary: "业务 Pod 异常：{{ $labels.pod }}"
```

### 11.4.4 验证查询

- 浏览器访问 `http://【任一节点IP】:30090`（NodePort），Targets 页面能看到 ServiceMonitor 自动生成的采集 job；
- 查询每个 Pod 的 CPU：

```promql
sum(rate(container_cpu_usage_seconds_total{image!="", pod!=""}[1m])) by (pod)
```

- Alertmanager：`http://【节点IP】:30093`；
- Grafana：`http://【节点IP】:30030`，默认账号 admin，首次登录改密；导入 8919 等看板时选默认 Prometheus 数据源。

## 11.5 Ingress 定制

不想用 NodePort 时，用 Ingress 统一暴露。先确保已部署 ingress-nginx controller，然后：

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: monitoring-ingress
  namespace: monitoring
  annotations:
    nginx.ingress.kubernetes.io/proxy-body-size: "100m"
spec:
  ingressClassName: nginx
  rules:
    - host: prom.【你的域名】
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: prometheus-k8s
                port: {number: 9090}
    - host: alert.【你的域名】
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: alertmanager-main
                port: {number: 9093}
    - host: grafana.【你的域名】
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: grafana
                port: {number: 3000}
```

```bash
kubectl apply -f monitoring-ingress.yaml
kubectl get ingress -n monitoring
```

域名解析到 Ingress Controller 的地址后，三个域名分别访问。

## 11.6 采集 Controller Manager 与 Scheduler

默认监控不到这两个控制面组件，需要两步：开放监听地址、创建 Service + Endpoints。

### 11.6.1 开放监听地址

在 master 节点编辑静态 Pod 清单（kubelet 会自动重建 Pod）：

`/etc/kubernetes/manifests/kube-controller-manager.yaml`，确认/修改：

```text
- --bind-address=0.0.0.0
```

`/etc/kubernetes/manifests/kube-scheduler.yaml`，同样：

```text
- --bind-address=0.0.0.0
```

等待控制面 Pod 重建：

```bash
kubectl get pods -n kube-system | grep -E 'controller-manager|scheduler'
```

### 11.6.2 创建 Service + Endpoints（Controller Manager）

```yaml
apiVersion: v1
kind: Service
metadata:
  name: kube-controller-manager
  namespace: kube-system
  labels:
    app.kubernetes.io/name: kube-controller-manager
spec:
  clusterIP: None
  ports:
    - name: https-metrics
      port: 10257
      targetPort: 10257
---
apiVersion: v1
kind: Endpoints
metadata:
  name: kube-controller-manager
  namespace: kube-system
  labels:
    app.kubernetes.io/name: kube-controller-manager
subsets:
  - addresses:
      - ip: 【master节点IP】
    ports:
      - name: https-metrics
        port: 10257
```

::: tip
新版控制面组件只暴露 https 端口（10257 controller、10259 scheduler），旧的 http 端口（10252/10251）已废弃。多 master 时把所有 master IP 都写进 addresses。
:::

### 11.6.3 创建 Service + Endpoints（Scheduler）

```yaml
apiVersion: v1
kind: Service
metadata:
  name: kube-scheduler
  namespace: kube-system
  labels:
    app.kubernetes.io/name: kube-scheduler
spec:
  clusterIP: None
  ports:
    - name: https-metrics
      port: 10259
      targetPort: 10259
---
apiVersion: v1
kind: Endpoints
metadata:
  name: kube-scheduler
  namespace: kube-system
  labels:
    app.kubernetes.io/name: kube-scheduler
subsets:
  - addresses:
      - ip: 【master节点IP】
    ports:
      - name: https-metrics
        port: 10259
```

```bash
kubectl apply -f kube-controller-svc.yaml
kubectl apply -f kube-scheduler-svc.yaml
kubectl get ep -n kube-system | grep -E 'controller|scheduler'
```

### 11.6.4 ServiceMonitor 采集

创建对应的 ServiceMonitor（端口名 https-metrics，scheme HTTPS，跳过证书校验）：

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: control-plane
  namespace: monitoring
  labels:
    release: kps
spec:
  selector:
    matchExpressions:
      - key: app.kubernetes.io/name
        operator: In
        values: [kube-controller-manager, kube-scheduler]
  namespaceSelector:
    matchNames: [kube-system]
  endpoints:
    - port: https-metrics
      scheme: https
      interval: 30s
      tlsConfig:
        insecureSkipVerify: true
      bearerTokenFile: /var/run/secrets/kubernetes.io/serviceaccount/token
```

验证：Targets 出现 control-plane 组件，`workqueue_*`、`scheduler_*` 指标可查。

## 11.7 Node Exporter DaemonSet

kube-prometheus-stack 已自带 node-exporter DaemonSet。若单独部署：

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: node-exporter
  namespace: monitoring
  labels: {app: node-exporter}
spec:
  selector:
    matchLabels: {app: node-exporter}
  template:
    metadata:
      labels: {app: node-exporter}
    spec:
      hostNetwork: true
      hostPID: true
      tolerations:
        - key: node-role.kubernetes.io/control-plane
          operator: Exists
          effect: NoSchedule
      containers:
        - name: node-exporter
          image: prom/node-exporter:v1.12.1
          args:
            - --path.procfs=/host/proc
            - --path.sysfs=/host/sys
            - --path.rootfs=/host/root
          ports:
            - name: metrics
              containerPort: 9100
              hostPort: 9100
          volumeMounts:
            - {name: proc, mountPath: /host/proc, readOnly: true}
            - {name: sys, mountPath: /host/sys, readOnly: true}
            - {name: root, mountPath: /host/root, readOnly: true}
      volumes:
        - name: proc
          hostPath: {path: /proc}
        - name: sys
          hostPath: {path: /sys}
        - name: root
          hostPath: {path: /}
```

::: warning
容器内看到的 /proc、/sys 是容器自己的，必须通过 `--path.procfs/sysfs/rootfs` 指向宿主机挂载路径，否则采集到的是容器指标而非宿主机。
:::

ServiceMonitor/采集由 stack 自动完成；Grafana 1860 看板展示节点数据。

---

## 本阶段命令速查表

```bash
# Helm 仓库
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# 安装全家桶
helm install kps prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace -f stack-values.yaml

# kube-prometheus 清单方式
kubectl apply -f manifests/setup/
kubectl apply -f manifests/

# 查看
kubectl get pods,svc,ingress -n monitoring

# 业务接入
kubectl apply -f deployment.yaml service.yaml servicemonitor.yaml

# 查看 Operator 自动生成的配置
kubectl get secret prometheus-k8s -n monitoring \
  -o jsonpath='{.data.prometheus\.yaml\.gz}' | base64 -d | gzip -d | less

# 升级 / 卸载
helm upgrade kps prometheus-community/kube-prometheus-stack -n monitoring -f stack-values.yaml
helm uninstall kps -n monitoring
```

---

## 本阶段常见坑与解决

**坑 1：ServiceMonitor 创建了但不采集**

- 现象：ServiceMonitor 存在，Targets 里没有对应 job。
- 原因：ServiceMonitor 的 labels 不被 Prometheus CRD 的 serviceMonitorSelector 接受（stack 默认要求 `release=<名字>`）；namespace 不对；selector 没选中 Service。
- 解决：补 release 标签；确认 Service 标签与 matchLabels 一致；确认 endpoints.port 用的是端口**名**。

**坑 2：Pod 采集报连接拒绝/404**

- 报错/现象：目标 DOWN，日志 404 page not found。
- 原因：容器没暴露 /metrics 或端口/路径配错。
- 解决：kubectl exec 进 Pod curl localhost:端口/metrics 自查；修正 port/path。

**坑 3：镜像拉不下来（ImagePullBackOff）**

- 报错原样：`Failed to pull image "quay.io/...": rpc error ... timeout`。
- 原因：quay.io、registry.k8s.io 国内访问受限。
- 解决：同步到私有仓库并覆盖镜像地址；配置加速；离线 load。

**坑 4：控制面组件监控不到**

- 现象：controller/scheduler 目标为空。
- 原因：bind-address 是 127.0.0.1；Endpoints 写错；用了已废弃的 http 端口。
- 解决：bind 改 0.0.0.0；用 https 10257/10259；确认 Endpoints 指向 master IP。

**坑 5：Node Exporter 数据不对（数值异常小）**

- 现象：节点 CPU/内存数据明显错误。
- 原因：没配 path.procfs/sysfs，采集的是容器视角。
- 解决：挂载宿主机 /proc、/sys、/ 并配 path 参数。

**坑 6：Calico 下无法访问监控页面**

- 报错/现象：Service/Pod 正常但访问超时。
- 原因：默认 NetworkPolicy 拦截。
- 解决：删除对应 networkPolicy 或按文档放通。

**坑 7：helm install 报 PVC Pending**

- 报错原样：`pod has unbound immediate PersistentVolumeClaims`。
- 原因：没有可用 StorageClass 或名字写错。
- 解决：`kubectl get sc` 确认；storageClass 填实际名称；或临时用 emptyDir 测试。

**坑 8：Prometheus 配置改了不生效**

- 现象：手动改配置无效。
- 原因：Operator 管理的配置由 CRD 自动生成，手改会被覆盖。
- 解决：改 ServiceMonitor/PrometheusRule 等 CRD，而不是直接改 prometheus.yml。

---
# 完整实战流程汇总（SOP）

## SOP 1：新机器接入监控（Node Exporter）

1. 新主机完成初始化（换源、主机名、时区、时间同步）；
2. 安装 node_exporter（二进制 9100 或容器），配置 systemd 开机自启；
3. 放通 9100 端口（监控服务器到本机）；
4. 在监控侧：静态配置加 target，或文件发现 targets/node.yml 加一行，或 Consul 注册；
5. Prometheus Targets 确认 UP；
6. Grafana 看板确认该主机出现；
7. 确认主机宕机、CPU、内存、磁盘告警规则覆盖该目标。

## SOP 2：新业务服务接入监控

1. 应用暴露 /metrics（内置或引入 client 库）；
2. 确定 Job 名、关键业务标签（app、env、region）；
3. 配置采集（静态/文件发现/Consul/K8s 用 ServiceMonitor）；
4. 编写业务黄金指标看板（QPS、错误率、延迟、饱和度）；
5. 编写业务告警规则并演练触发；
6. 通知渠道确认（邮件/企微/钉钉）。

## SOP 3：Prometheus 配置发布与回滚

**发布**：

1. 备份当前配置：`cp prometheus.yml prometheus.yml.bak.$(date +%F)`；
2. 编辑配置；
3. `promtool check config prometheus.yml`（规则用 promtool check rules）；
4. `systemctl reload prometheus` 或 `curl -X POST http://localhost:9090/-/reload`；
5. Targets、Rules 页面验证。

**回滚**：

1. `cp prometheus.yml.bak.日期 prometheus.yml`；
2. promtool 检查；
3. reload；
4. 验证恢复。

## SOP 4：告警维护窗口（静默）

1. Alertmanager → Silences → New Silence；
2. 精确填写匹配标签（如 instance=某主机），不要用过宽条件；
3. 设置开始/结束时间（维护预计时长，宁短勿长）；
4. 维护结束后若提前完成，手动删除该 Silence；
5. 多实例/集群下确认静默已同步。

## SOP 5：扩容（单机 → 联邦/集群存储）

1. 评估瓶颈：采集目标过多（CPU/内存）→ 加 Prometheus 分片或联邦；存储不足 → 扩盘或上 VictoriaMetrics；
2. 联邦：新增从节点承接部分 Job，中心节点加 federate job；
3. 存储：部署 VM 单机/集群，Prometheus 配 remote_write；
4. 灰度切换数据源，观察一段时间；
5. 更新看板与告警归属。

## SOP 6：备份与恢复

**备份内容**：prometheus.yml、rules 目录、Alertmanager 配置与模板（这些是核心资产，体量小）。

```bash
BACKUP_DIR=/data/backup/prometheus
mkdir -p ${BACKUP_DIR}
tar czf ${BACKUP_DIR}/prometheus-conf-$(date +%F).tar.gz \
  -C /usr/local/prometheus conf rules
tar czf ${BACKUP_DIR}/am-conf-$(date +%F).tar.gz \
  -C /usr/local/alertmanager conf tmpl
```

**历史数据备份**：本地 TSDB 可用快照 API：

```bash
curl -X POST http://localhost:9090/api/v1/admin/tsdb/snapshot
# 快照生成在 data/snapshots/<快照ID>
```

**恢复**：

1. 重装 Prometheus/Alertmanager（同版本）；
2. 解压配置备份到原路径；
3. 数据快照拷回 data 目录；
4. 启动服务，检查配置、规则、目标、看板。

::: warning
Prometheus 数据备份不是常规必需（它是监控数据，可重新采集），**配置和规则必须备份**。长期历史数据建议直接存 VictoriaMetrics 并对其数据盘做快照/备份。
:::

## SOP 7：日常巡检清单

- Prometheus、Alertmanager、Grafana 服务状态；
- Prometheus 自身指标：`prometheus_tsdb_head_series`（序列数）、`prometheus_sd_failed_configs`、`prometheus_notifications_failed_total`、`prometheus_remote_storage_failed_samples_total`；
- 磁盘水位（data 目录增长）；
- Targets 是否有 DOWN；
- 告警是否正常送达（定期演练）；
- 时间同步状态。

---

# 常见问题排查（FAQ）

**Q1：Target 显示 DOWN 怎么排查？**

按顺序：① 被监控机服务是否启动、端口是否监听（ss -lntp）；② 监控机能否连通（curl http://目标IP:端口/metrics、ping、telnet）；③ 防火墙/安全组是否放通；④ 服务是否监听 0.0.0.0（只监听 127.0.0.1 外部访问不了）；⑤ 看 Target 页该目标的 Error 提示。

**Q2：告警触发了但收不到通知？**

① Alertmanager 是否在运行、Prometheus alerting 配置地址是否正确；② 告警状态是否到 Firing（Pending 不发）；③ 路由 matchers 是否匹配、receiver 是否配置正确；④ 是否被静默或抑制；⑤ Alertmanager 日志与 `prometheus_notifications_*` 指标；⑥ 邮件看 SMTP 报错、钉钉/企微看渠道侧报错。

**Q3：磁盘涨得特别快？**

① 查序列数 `prometheus_tsdb_head_series` 是否高基数爆炸；② 是否有标签值无限增长（user_id、request_id、IP 当标签）；③ retention 是否过长；④ 用 metric_relabel 丢弃无用高基数指标；⑤ 缩短保留或上远程存储。

**Q4：Grafana 面板没数据？**

① 数据源测试是否通过；② 面板 Job 变量与实际 job 名是否一致；③ 时间范围是否选对；④ 直接在 Prometheus 查该 PromQL 验证表达式；⑤ 看板与组件版本是否匹配。

**Q5：容器重启后数据/配置丢失？**

① 配置是否通过挂载持久化；② 数据目录是否挂载数据卷；③ 容器方式是否用了 restart 策略；④ 生产用 StatefulSet/PVC 或宿主机目录挂载。

**Q6：Prometheus 内存占用越来越高？**

① 序列数是否持续增长（高基数）；② 采集目标是否过多，考虑分片/联邦；③ Head 块 2 小时刷盘是正常波动；④ 调整处理并发、减少不必要的指标采集。

**Q7：图表出现毛刺/数据断点？**

① 抓取是否超时（scrape_timeout 太短、目标负载高）；② 网络抖动；③ 时间是否同步；④ 查看 `scrape_duration_seconds`、`up` 历史。

**Q8：修改配置后 Prometheus 报错启动失败？**

① 不要直接重启，先用 promtool check config 定位；② 常见是 YAML 缩进、重复 key、正则非法；③ 修复后再 reload；④ 无法快速修复时用备份配置回滚。

---

# 面试自测

1. Prometheus 的整体架构和数据流向？Pull 模型的优缺点？
2. Prometheus 有哪四种指标类型？Histogram 和 Summary 的区别与选择？
3. PromQL 的四种结果类型？rate 和 increase、irate 的区别？
4. Counter 和 Gauge 的区别？哪些指标必须用 Counter？
5. Job 和 Instance 的关系？`up` 指标的含义和用途？
6. relabel_configs 和 metric_relabel_configs 的区别和发生时机？
7. 记录规则解决什么问题？命名规范是什么？
8. 告警的完整链路？Pending 和 Firing 的区别，for 的作用？
9. Alertmanager 的分组、抑制、静默、路由分别解决什么问题？
10. Alertmanager 高可用如何实现？Gossip 的作用？
11. Prometheus 服务发现有哪些方式？Kubernetes 有哪些 role？
12. ServiceMonitor 的工作原理？为什么创建了 ServiceMonitor 却不生效？
13. Prometheus 联邦的适用场景和能力边界？
14. 本地 TSDB 的存储机制？WAL、Block、压缩分别是什么？
15. Prometheus 单机瓶颈如何解决？VictoriaMetrics 集群有哪些组件和端口？
16. 如何监控 Prometheus 自身？关键自身指标有哪些？
17. Pushgateway 的适用场景和缺点？
18. Blackbox 监控和普通 Exporter 监控的区别？
19. 四个黄金信号是什么？如何用 PromQL 实现？
20. 一条告警规则应该包含哪些要素？如何避免告警风暴？

---

# 相关速查（官网地址）

| 项目 | 官网 / 文档 |
| --- | --- |
| Prometheus 官网 | https://prometheus.io/ |
| Prometheus 文档 | https://prometheus.io/docs/introduction/overview/ |
| Prometheus 下载 | https://prometheus.io/download/ |
| PromQL 查询基础 | https://prometheus.io/docs/prometheus/latest/querying/basics/ |
| PromQL 函数 | https://prometheus.io/docs/prometheus/latest/querying/functions/ |
| 配置说明 | https://prometheus.io/docs/prometheus/latest/configuration/configuration/ |
| 告警规则 | https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/ |
| 联邦 | https://prometheus.io/docs/prometheus/latest/federation/ |
| Alertmanager 文档 | https://prometheus.io/docs/alerting/latest/alertmanager/ |
| Alertmanager 配置 | https://prometheus.io/docs/alerting/latest/configuration/ |
| 通知模板 | https://prometheus.io/docs/alerting/latest/notifications/ |
| 高可用 | https://github.com/prometheus/alertmanager#high-availability |
| Node Exporter | https://github.com/prometheus/node_exporter |
| MySQL Exporter | https://github.com/prometheus/mysqld_exporter |
| Redis Exporter | https://github.com/oliver006/redis_exporter |
| Blackbox Exporter | https://github.com/prometheus/blackbox_exporter |
| Pushgateway | https://github.com/prometheus/pushgateway |
| JMX Exporter | https://github.com/prometheus/jmx_exporter |
| nginx-prometheus-exporter | https://github.com/nginxinc/nginx-prometheus-exporter |
| HAProxy Exporter | https://github.com/prometheus/haproxy_exporter |
| Consul Exporter | https://github.com/prometheus/consul_exporter |
| cAdvisor | https://github.com/google/cadvisor |
| 钉钉 Webhook | https://github.com/timonwong/prometheus-webhook-dingtalk |
| PrometheusAlert | https://github.com/feiyu563/PrometheusAlert |
| VictoriaMetrics 官网 | https://victoriametrics.com/ |
| VictoriaMetrics 文档 | https://docs.victoriametrics.com/ |
| VM 集群文档 | https://docs.victoriametrics.com/cluster-victoriametrics/ |
| Prometheus Operator | https://github.com/prometheus-operator/prometheus-operator |
| kube-prometheus | https://github.com/prometheus-operator/kube-prometheus |
| Helm Charts | https://github.com/prometheus-community/helm-charts |
| Grafana 官网 | https://grafana.com/ |
| Grafana 看板市场 | https://grafana.com/grafana/dashboards/ |
| 现成告警规则集 | https://samber.github.io/awesome-prometheus-alerts/ |
| GitHub 代理（加速下载） | https://ghproxy.net/ （备选 https://gh-proxy.com/ 、https://ghfast.top/ ） |
| 清华镜像站 | https://mirrors.tuna.tsinghua.edu.cn/ |
| 阿里云镜像站 | https://mirrors.aliyun.com/ |
| Go 模块代理 | https://goproxy.cn/ |
| pip 清华源 | https://pypi.tuna.tsinghua.edu.cn/simple |

---

# 附录：延伸阅读（可选）

- 《Site Reliability Engineering》（Google SRE 书）：监控方法论与四个黄金信号的出处，在线版 https://sre.google/sre-book/monitoring-distributed-systems/（需科学上网）；国内平替：https://www.cnblogs.com/lhxBlogs/p/17924893.html
- Facebook Gorilla 论文：理解 TSDB 高压缩存储，https://www.vldb.org/pvldb/vol8/p1816-teller.pdf
- Prometheus 官方最佳实践：指标命名、标签使用，https://prometheus.io/docs/practices/naming/
- Kubernetes 可观测性体系：Metrics Server、cAdvisor、kube-state-metrics 的分工
- Thanos：另一类 Prometheus 长期存储与高可用方案，https://thanos.io/
- OpenTelemetry：可观测性标准（Metrics/Traces/Logs 融合），https://opentelemetry.io/
- Grafana Loki：与 Prometheus 同风格的日志聚合方案，https://grafana.com/oss/loki/
