import type { Article } from '../types'

const articles: Article[] = [
  {
    group: '能力地图（Why & Roadmap）',
    title: '运维为什么写代码与能力地图',
    link: '/guide/devdev-why-and-roadmap',
    sub: '写代码的价值、技术栈选型、项目驱动学习路径、与 SRE/平台工程的关系',
  },
  {
    group: '自研平台',
    title: '自研 CMDB 与资产管理',
    link: '/guide/devdev-platform-cmdb',
    sub: '资产模型、ER 关系、FastAPI + SQLAlchemy + MySQL 完整 CRUD、自动采集与对账',
  },
  {
    group: '自研平台',
    title: '作业执行与发布平台',
    link: '/guide/devdev-job-release',
    sub: '批量执行通道、Celery + Redis 队列、WebSocket 实时回显、幂等并发、审计与回滚',
  },
  {
    group: '自研平台',
    title: '工单系统与监控大屏',
    link: '/guide/devdev-ticket-dashboard',
    sub: '工单状态机与 SLA、Prometheus/CMDB/成本数据聚合、Vue + ECharts 大屏',
  },
  {
    group: 'CLI 与自动化',
    title: '运维 CLI 与钉钉/企微机器人',
    link: '/guide/devdev-cli-bot',
    sub: 'Click/Typer 多子命令 CLI、Go Cobra 对比、机器人加签与 Webhook 自动化',
  },
  {
    group: 'CLI 与自动化',
    title: '任务调度与 API 产品化',
    link: '/guide/devdev-scheduler-api',
    sub: 'APScheduler/Celery beat、分布式锁、统一 API 封装、权限审计与产品化要素',
  },
]

export default articles
