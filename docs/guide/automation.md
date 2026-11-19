---
title: "自动化与 IaC"
description: "本页聚合 配置管理、持续集成/持续交付、GitOps 和基础设施即代码（IaC），目标是把重复工作自动化、用代码管理基础设施。"
---
# 自动化与 IaC

> 本页聚合 **配置管理、持续集成/持续交付、GitOps 和基础设施即代码（IaC）**，目标是把重复工作自动化、用代码管理基础设施。

## 文章索引

### 配置管理自动化

::: idx

| 文章 | 解决什么问题 | 状态 |
|---|---|---|
| [Ansible](/services/cicd/ansible) | Inventory、Ad-Hoc、Playbook、常用模块、Roles、Vault、Galaxy | ✅ 已完成 |

:::

### 持续集成 / 持续交付

::: idx

| 文章 | 解决什么问题 | 状态 |
|---|---|---|
| [Git / GitLab / Jenkins](/guide/devops-cicd-advanced#合并资料) | Git 版本控制、GitLab 部署管理、Jenkins 自由风格/Pipeline | ✅ 已完成 |
| [GitOps（GitLab CI / ArgoCD）](/guide/devops-cicd-advanced#合并资料) | GitLab CI 流水线、ArgoCD 持续部署、GitOps 工作流 | ✅ 已完成 |

:::

### 基础设施即代码

::: idx

| 文章 | 解决什么问题 | 状态 |
|---|---|---|
| [Terraform](./automation-terraform) | HCL 语法、Provider、State 管理、云服务器（ECS/CVM）、模块化 | ✅ 已完成 |

:::

### SRE 编程

::: idx

| 文章 | 解决什么问题 | 状态 |
|---|---|---|
| [Python 运维自动化](/services/cicd/ansible) | subprocess、paramiko、requests 调 API、数据处理、综合实战工具 | ✅ 已完成 |

:::

## 命令速查

- 相关命令及自动化脚本：[Linux 命令速查](/reference/linux-commands)
- 容器化部署相关：[Docker 命令速查](/reference/docker-commands)、[kubectl 命令速查](/reference/kubectl-commands)

<!-- merged-qa-faq:start -->
## 常见问题 FAQ

> 云服务器与自动化问题的高频问题已并入本页。默认只显示问题，点开查看完整答案。

### 一、部署前：云平台选型与架构

<details>
<summary>Q1：核心云产品有哪些？分别干什么？</summary>

**答：**

我按"一台业务跑在云上需要哪几块"来记，以阿里云/腾讯云/华为云这类国内主流公有云为例，核心产品分七层讲。

第一是计算层，对应阿里云 ECS、腾讯云 CVM、华为云 ECS，就是一台带 CPU/内存/磁盘的云服务器，需要选实例规格、镜像、公网带宽，弹性伸缩组（Auto Scaling）能按 CPU 指标自动增减机器。

第二是网络层，核心是 VPC 私有网络，自己划网段（如 192.168.0.0/16），下面分子网；云上没有传统交换机的概念，靠**安全组**做四层访问控制（相当于分布式防火墙，按端口/协议/来源放行），靠网络 ACL 做子网级规则。对外还有 NAT 网关让内网机器出公网、EIP 弹性公网 IP、负载均衡 SLB/CLB（四层 CLB、七层 ALB）。

第三是存储层，系统盘加数据盘（云盘），对象存储 OSS/COS 存静态文件、图片、备份，按量付费、自带多副本。

第四是数据库层，RDS 托管 MySQL/PostgreSQL，自带主从、备份、只读实例，不用自己搭主从复制；还有 Redis 缓存、消息队列 Kafka/RocketMQ。

第五是身份权限层，IAM 给员工/程序建子账号、分配最小权限策略，用 AccessKey 调 API，坚决不把主账号密钥写进代码。

最后配上云解析 DNS、CDN 回源加速、云监控 CloudMonitor。一句话：云上运维的思维是"一切都是可编排的资源"，机器挂了不是去修，而是扩容再拉起新实例。

</details>

<details>
<summary>Q2：云上运维和自建 IDC 机房有什么差异？</summary>

**答：**

这是个高频对比题，我从六个维度说。

第一是**资源获取方式**：自建要买物理服务器、上架、布线、装系统，周期几周到几个月；云上是分钟级开 ECS，`open` 一下就有，弹性伸缩峰值时扩、闲时缩，不用为峰值常年养一堆机器。

第二是**成本模型**：自建是 CapEx，前期一次性买硬件，3-5 年折旧；云上是 OpEx，按使用量付费，但要警惕"成本漂移"——机器开了不关、云盘超配、带宽按固定峰值买，账单会很贵。所以云上要做成本优化：包年包月压稳定负载、按量+弹性伸缩扛波峰、用 OSS 低频归档、定期清理闲置 EIP 和快照。

第三是**运维边界**：自建从机房电力、硬件、RAID、BIOS 都得自己管；云上是**责任共担**——云厂商管物理机、网络虚拟化、存储多副本，我管操作系统、中间件、应用、数据和权限。比如 ECS 宕机厂商帮你迁移，但系统盘被我写满、MySQL 慢查询是我的事。

第四是**高可用手段**：自建靠双机热备、共享存储；云上靠多可用区（AZ）部署——同一 region 下选两个电力网络隔离的 AZ，SLB 把流量分到两边，一个 AZ 整体故障另一个顶得住，这比自己做双活省事得多。

第五是**自动化程度**：云上一切有 OpenAPI，Ansible、Terraform 直接调云 API 开资源，基础设施即代码，不用人去机房插 U 盘。

第六是**风险点**：自建怕硬件坏、断电；云上怕账号泄露、配置错（比如把 0.0.0.0/0 放开到数据库端口）、厂商区域级故障。所以我特别重视 IAM 最小权限和安全组白名单。

一句话：自建重资产、重体力，云上重编排、重成本和权限治理。

</details>

<details>
<summary>Q3：如何在云上设计一套高可用架构？</summary>

**答：**

我设计高可用就一条主线：**消除所有单点**，原则是冗余、无状态、自动切换。

具体分层讲。接入层：DNS 解析到 **SLB/CLB**，后面挂至少两台以上应用服务器，SLB 做健康检查，一台挂了自动摘流量。应用层：服务做成**无状态**——本地不存会话，会话放 Redis，文件放 OSS，这样任意一台挂了另一台无缝接管，也能随便加机器水平扩容。

机房层：跨**多可用区**部署，应用和数据库主库所在区故障时，备区能接。数据层：RDS 开主从复制和自动故障切换，从库扛读、主库扛写，定期自动备份；缓存放 Redis 哨兵或集群。

弹性与容灾：配弹性伸缩组，CPU 超阈值自动加机器，低于阈值自动缩；关键数据做 **3-2-1 备份**——三份副本、两种介质、一份异地。最后配上云监控告警，SLB 后端健康检查失败、RDS 主从延迟都要告警。

在这套 X99 + PVE 家庭实验里，对应的体会是：用 PVE 把一台物理机切成多台虚机，最开始所有实验挤在一台 VM 里，后来拆成独立节点、给关键组件做冗余，才真正理解"无状态 + 负载均衡 + 自动切换"为什么是生产架构的标配。

</details>

### 二、部署与自动化：配置管理与流水线

<details>
<summary>Q4：Ansible 原理和常用模块？</summary>

**答：**

Ansible 是我做批量配置管理的主力工具，核心特点是**无 Agent**：被控机器不用装客户端，控制机通过 SSH 连过去执行，靠 Python 临时脚本完成任务，执行完就删，所以上手快、干净。

它的几个核心概念我脱口能讲：一是 **inventory** 主机清单，一个 ini 或 yaml 文件把机器按组分类，比如 `[web]`、`[db]`，里面写 IP、SSH 用户、密钥；二是 **module** 模块，真正干活的是模块，常用的有 `yum`/`apt` 装包、`copy` 下发文件、`file` 建目录改权限、`service` 管服务启停、`shell`/`command` 跑命令、`git` 拉代码、`template` 用 Jinja2 模板渲染配置；三是 **playbook** 用 YAML 写一套编排剧本，按 tasks 顺序执行；四是 **roles** 把一套任务拆成 tasks/handlers/templates/vars 目录，做成可复用角色。

它最大的优点是**幂等**：模块会先检查目标状态，已经是期望状态就不动，重复跑不会出错，这跟自己写 shell 脚本最大的区别就在这——shell 跑两次可能重复装，Ansible 跑一百次结果都一样。

云上落地我常这么用：刚用 Terraform 开出一批 ECS，立刻用 Ansible playbook 做初始化——关闭密码登录、配 SSH 密钥、装基础监控 agent、统一 hosts、调内核参数。ad-hoc 临时批量操作就用 `ansible web -m shell -a "uptime" -f 20`，`-f 20` 是并发 20 台。

</details>

<details>
<summary>Q5：Terraform 是做什么的？</summary>

**答：**

Terraform 是**基础设施即代码（IaC）**工具，把云上要开的资源用 HCL 语言写成代码，版本化管理，而不是点网页控制台。

工作流我背得很熟：写好 `.tf` 文件后，第一步 `terraform init` 初始化、下载 provider（比如阿里云的 `alicloud`）；第二步 `terraform plan` 干跑，告诉"我打算新建、修改、删除哪些资源"，这一步只看不动手，是我特别看重的安全检查；第三步 `terraform apply` 真正执行；不要了就 `terraform destroy` 一键清干净。

它的核心是 **state 文件**，记录云上真实资源和代码的对应关系，相当于一本账本。生产上 state 不能放本地，要放到远端（比如 OSS + 锁），防止多人同时改把状态写乱、或者两人各 `apply` 一遍把资源冲掉。

我在云上用它管什么：一台 VPC、几个子网、一组 ECS 安全组规则、SLB、RDS 参数，全部代码化。好处是**可重复、可审计**——环境要复制到 staging，直接 `apply` 一份；谁改了资源，git diff 一目了然；还能多云，同一套思路换个 provider 就能管 AWS。它和 Ansible 的分工我也会讲清：Terraform 负责"开资源"（生命周命），Ansible 负责"装完软件后怎么配置"，业界常组合用，边界清楚。

</details>

<details>
<summary>Q6：完整 CI/CD 流程？</summary>

**答：**

结论：CI/CD 是"代码提交到上线"的自动化流水线，分 **CI（持续集成）→ CD（持续交付/部署）** 两大段。

CI 段：开发 push 代码到 Git，自动触发流水线。第一步**拉代码、装依赖**（`npm ci`、`mvn dependency:go-offline`）；第二步**静态检查和单元测试**（lint、`mvn test`、`npm test`、覆盖率统计）；第三步**构建制品**——Java 打 jar/war、前端打 dist、更重要的是**打 Docker 镜像**，tag 用 commit SHA 或版本号，推到镜像仓库（Harbor/ACR）。任何一步失败立即中止，通知开发。

CD 段：制品 ready 后，先**部署到测试环境**，自动跑集成测试、E2E 测试（Cypress/Playwright）、接口自动化；测试通过后**人工审批或自动部署预发环境**（和生产同构）；预发验证通过，再**发布到生产**。生产发布不是一把梭，要用蓝绿/金丝雀/滚动策略，发布过程中监控错误率和指标，异常自动回滚。最后发钉钉/飞书通知。

整个流水线的关键原则：**一切自动化、制品不可变**——测试环境用的镜像和生产用的是同一个镜像，不靠"重新构建一次"换环境，避免"我这能跑你那不行"。环境差异用 ConfigMap/配置中心解决，不打进镜像。失败要能一键回滚，回滚也是自动化的，不要人肉登服务器。

</details>

<details>
<summary>Q7：Jenkins 和 GitLab CI 区别？</summary>

**答：**

结论：Jenkins 是独立的通用 CI 服务器，插件生态最猛；GitLab CI 是和 GitLab 仓库一体、用 `.gitlab-ci.yml` 描述流水线，轻量、开箱即用。

第一，**架构和集成**。Jenkins 是独立部署的服务，Master 调度、Agent 干活，要自己装、自己升级、自己备份。它支持任何 Git 仓库（GitHub/GitLab/Gitee）。GitLab CI 直接内置在 GitLab 里，你在仓库根目录放个 `.gitlab-ci.yml`，push 就触发，不用单独装 CI 服务器，Runner 也是轻量 agent。

第二，**Pipeline 定义方式**。Jenkins 早期用自由风格 UI 配置，现在也支持 Jenkinsfile（Groovy 写在仓库里），但 Groovy 写复杂逻辑学习曲线陡。GitLab CI 就是 YAML 声明 stages/jobs/script，简洁直观，新人半天就能上手。

第三，**插件生态**。Jenkins 赢麻了，1800+ 插件，几乎能接任何工具，企业里老牌项目、复杂流水线基本都是 Jenkins。代价是插件多了容易版本冲突、安全漏洞一堆，要定期升。GitLab CI 内置了绝大多数常用能力，插件没 Jenkins 多但够用。

第四，**资源和成本**。Jenkins Master-Agent 模型灵活，能把编译任务甩给不同机器；GitLab Runner 也支持 Docker executor、shell executor，单机小团队够用。

怎么选：团队已经在用 GitLab、流水线不复杂，直接 GitLab CI，省事；已经有 Jenkins 集群、需要极度定制化、对接各种私有系统，继续 Jenkins。现在新起的小团队用 GitHub Actions / GitLab CI 的越来越多，Jenkins 更多是存量维护。

</details>

### 三、发布与运行：发布策略

<details>
<summary>Q8：常见发布策略？</summary>

**答：**

结论：三种主流发布策略——**滚动、蓝绿、金丝雀**，区别在"新旧版本并存多久、流量怎么切、回滚快不快、成本高不高"。

**滚动发布（Rolling Update）**：老版本 Pod 一个一个被新版本替换，K8s Deployment 默认就是。优点：不需要双倍机器，资源省；缺点：发布过程中新老版本同时在线，要保证 API 向后兼容；回滚要把过程倒着再滚一遍，慢一点。最常用，K8s 原生 `maxSurge/maxUnavailable` 控制节奏。

**蓝绿发布（Blue-Green）**：起一套全新的绿色环境跑新版本，老的蓝色环境原样不动；验证绿色没问题，流量一次性从蓝切到绿（改 Nginx upstream、Service selector、负载均衡权重）。优点：**回滚极快**，切回蓝就行，几秒钟；缺点：要双倍资源，成本高。核心业务、对回滚速度要求高的用。

**金丝雀发布（Canary）**：先让一小部分流量（比如 1%、5%）到新版本，观察一段时间（错误率、延迟、业务指标），没问题再逐步放大到 10%、30%、100%。优点：风险最小，出问题只影响一小撮用户；缺点：周期长、要监控和流量切分能力（Ingress/Nginx 按权重、Istio 按百分比）。

对比：

| 策略 | 资源成本 | 回滚速度 | 风险 | 适用 |
|---|---|---|---|---|
| 滚动 | 低（约 1.25 倍） | 中 | 中 | 日常迭代 |
| 蓝绿 | 高（双倍） | 极快 | 低 | 核心、大版本 |
| 金丝雀 | 中 | 快（切回权重） | 最低 | 大流量、核心链路 |

K8s 上怎么落地：滚动用 Deployment 原生；蓝绿用两套 Deployment 切 Service selector；金丝雀用 Ingress 注解（`nginx.ingress.kubernetes.io/canary-weight: "10"`）或 Istio VirtualService。三种都要配合监控（Prometheus/Grafana、错误率、SLO）和自动回滚。

</details>

<!-- merged-qa-faq:end -->
