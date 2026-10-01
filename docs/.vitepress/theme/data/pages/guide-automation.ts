import type { Article } from '../types'

const articles: Article[] = [
  {
    group: '配置管理自动化',
    title: 'Ansible',
    link: '/guide/automation-ansible',
    sub: 'Inventory、Ad-Hoc、Playbook、常用模块、Roles、Vault、Galaxy'
  },
  {
    group: '持续集成 / 持续交付',
    title: 'Git / GitLab / Jenkins',
    link: '/guide/automation-jenkins',
    sub: 'Git 版本控制、GitLab 部署管理、Jenkins 自由风格/Pipeline'
  },
  {
    group: '持续集成 / 持续交付',
    title: 'GitOps（GitLab CI / ArgoCD）',
    link: '/guide/automation-gitops',
    sub: 'GitLab CI 流水线、ArgoCD 持续部署、GitOps 工作流'
  },
  {
    group: '基础设施即代码',
    title: 'Terraform',
    link: '/guide/automation-terraform',
    sub: 'HCL 语法、Provider、State 管理、云服务器（ECS/CVM）、模块化'
  },
  {
    group: 'SRE 编程',
    title: 'Python 运维自动化',
    link: '/guide/sre-python',
    sub: 'subprocess、paramiko、requests 调 API、数据处理、综合实战工具'
  }
]

export default articles
