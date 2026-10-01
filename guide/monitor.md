# 监控与日志

> 本页聚合 **监控告警、日志平台、云原生可观测性、SRE 稳定性和运维安全审计**：Zabbix、Prometheus、ELK、OpenTelemetry、Grafana LGTM、SLO/事故/混沌/灾备、JumpServer 堡垒机。

## 文章索引

### Zabbix

::: idx

| 文章 | 解决什么问题 | 状态 |
|---|---|---|
| [Zabbix 基础](./monitor-zabbix) | 架构、Server/Agent 部署、主机/Items、触发器、告警动作 | ✅ 已完成 |
| [Zabbix 进阶](./monitor-zabbix-advanced) | 模板、图形、自动发现、Proxy、自定义脚本、API、调优 | ✅ 已完成 |

:::

### Prometheus 监控

::: idx

| 文章 | 解决什么问题 | 状态 |
|---|---|---|
| [Prometheus](./monitor-prometheus) | Prometheus、PromQL、Alertmanager、Grafana、联邦集群 | ✅ 已完成 |

:::

### 日志平台

::: idx

| 文章 | 解决什么问题 | 状态 |
|---|---|---|
| [ELK 日志平台](./monitor-elk) | ES/Kibana、Logstash/Filebeat、查询、Nginx 日志案例 | ✅ 已完成 |

:::

### 运维审计

::: idx

| 文章 | 解决什么问题 | 状态 |
|---|---|---|
| [JumpServer 堡垒机](./monitor-jumpserver) | 部署、资产授权、用户管理、会话审计 | ✅ 已完成 |

:::

### 云原生可观测性

::: idx

| 文章 | 解决什么问题 | 状态 |
|---|---|---|
| [OpenTelemetry 统一可观测](./monitor-opentelemetry) | Traces/Metrics/Logs 三支柱、Collector、OTLP、自动/手动插桩 | ✅ 已完成 |
| [Grafana LGTM 栈](./monitor-grafana-stack) | Grafana + Loki/Tempo/Mimir、Jaeger 链路追踪、统一可观测栈 | ✅ 已完成 |

:::

### SRE 稳定性工程

::: idx

| 文章 | 解决什么问题 | 状态 |
|---|---|---|
| [SLO 与错误预算](./monitor-slo) | SLI/SLO/SLA、错误预算、多窗口多燃烧率 Burn Rate 告警 | ✅ 已完成 |
| [事故管理与复盘](./sre-incident) | On-call 值班、应急指挥、时间线、无指责 Postmortem | ✅ 已完成 |
| [混沌工程](./sre-chaos) | Chaos Mesh/Litmus、稳态假设、故障注入、韧性演练 | ✅ 已完成 |
| [容量规划与灾备](./sre-capacity-dr) | 容量规划、变更管理、高可用、RTO/RPO、DR 演练 | ✅ 已完成 |

:::

## 命令速查

- 日志查看（journalctl / tail / dmesg）：[Linux 命令速查](/reference/linux-commands)
- 端口与进程排查：[网络命令速查](/reference/network-commands)
