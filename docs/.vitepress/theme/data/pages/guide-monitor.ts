import type { Article } from '../types'

const articles: Article[] = [
  {
    group: 'Zabbix',
    title: 'Zabbix 基础',
    link: '/guide/monitor-zabbix',
    sub: '架构、Server/Agent 部署、主机/Items、触发器、告警动作'
  },
  {
    group: 'Zabbix',
    title: 'Zabbix 进阶',
    link: '/guide/monitor-zabbix-advanced',
    sub: '模板、图形、自动发现、Proxy、自定义脚本、API、调优'
  },
  {
    group: 'Prometheus 监控',
    title: 'Prometheus',
    link: '/guide/monitor-prometheus',
    sub: 'Prometheus、PromQL、Alertmanager、Grafana、联邦集群'
  },
  {
    group: '日志平台',
    title: 'ELK 日志平台',
    link: '/guide/monitor-elk',
    sub: 'ES/Kibana、Logstash/Filebeat、查询、Nginx 日志案例'
  },
  {
    group: '运维审计',
    title: 'JumpServer 堡垒机',
    link: '/guide/monitor-jumpserver',
    sub: '部署、资产授权、用户管理、会话审计'
  },
  {
    group: '云原生可观测性',
    title: 'OpenTelemetry 统一可观测',
    link: '/guide/monitor-opentelemetry',
    sub: 'Traces/Metrics/Logs 三支柱、Collector、OTLP、自动/手动插桩'
  },
  {
    group: '云原生可观测性',
    title: 'Grafana LGTM 栈',
    link: '/guide/monitor-grafana-stack',
    sub: 'Grafana + Loki/Tempo/Mimir、Jaeger 链路追踪、统一可观测栈'
  },
  {
    group: 'SRE 稳定性工程',
    title: 'SLO 与错误预算',
    link: '/guide/monitor-slo',
    sub: 'SLI/SLO/SLA、错误预算、多窗口多燃烧率 Burn Rate 告警'
  },
  {
    group: 'SRE 稳定性工程',
    title: '事故管理与复盘',
    link: '/guide/sre-incident',
    sub: 'On-call 值班、应急指挥、时间线、无指责 Postmortem'
  },
  {
    group: 'SRE 稳定性工程',
    title: '混沌工程',
    link: '/guide/sre-chaos',
    sub: 'Chaos Mesh/Litmus、稳态假设、故障注入、韧性演练'
  },
  {
    group: 'SRE 稳定性工程',
    title: '容量规划与灾备',
    link: '/guide/sre-capacity-dr',
    sub: '容量规划、变更管理、高可用、RTO/RPO、DR 演练'
  }
]

export default articles
