# 运维开发 / 平台自研

> 本页聚合 **运维写代码、把重复操作产品化、自研运维平台（CMDB / 作业发布 / 工单大屏 / CLI 机器人 / 调度 API）** 六大主题。目标是从"会用工具的 SRE"走向"能造工具、能把经验沉淀成平台的平台工程师"，与第一阶段的 DevOps/IaC 板块互补：[自动化与 IaC](./automation) 讲怎么用现成工具，本页讲怎么自己造轮子。

## 文章索引

### 能力地图（Why & Roadmap）

::: idx

| 文章 | 解决什么问题 | 状态 |
|---|---|---|
| [运维为什么写代码与能力地图](./devdev-why-and-roadmap) | 写代码的价值、技术栈选型、项目驱动学习路径、与 SRE/平台工程的关系 | ✅ 已完成 |

:::

### 自研平台

::: idx

| 文章 | 解决什么问题 | 状态 |
|---|---|---|
| [自研 CMDB 与资产管理](./devdev-platform-cmdb) | 资产模型、ER 关系、FastAPI + SQLAlchemy + MySQL 完整 CRUD、自动采集与对账 | ✅ 已完成 |
| [作业执行与发布平台](./devdev-job-release) | 批量执行通道、Celery + Redis 队列、WebSocket 实时回显、幂等并发、审计与回滚 | ✅ 已完成 |
| [工单系统与监控大屏](./devdev-ticket-dashboard) | 工单状态机与 SLA、Prometheus/CMDB/成本数据聚合、Vue + ECharts 大屏 | ✅ 已完成 |

:::

### CLI 与自动化

::: idx

| 文章 | 解决什么问题 | 状态 |
|---|---|---|
| [运维 CLI 与钉钉/企微机器人](./devdev-cli-bot) | Click/Typer 多子命令 CLI、Go Cobra 对比、机器人加签与 Webhook 自动化 | ✅ 已完成 |
| [任务调度与 API 产品化](./devdev-scheduler-api) | APScheduler/Celery beat、分布式锁、统一 API 封装、权限审计与产品化要素 | ✅ 已完成 |

:::

## 命令速查

- Git 协作与分支工作流：[Git 命令与协作工作流速查](/reference/git-commands)
- K8s / Helm / OpenTelemetry 排障：[云原生命令速查](/reference/cloudnative-commands)
- 让 AI 帮你写平台代码、生成 Prompt：[运维 AI Prompt 速查](/reference/ai-prompts)
