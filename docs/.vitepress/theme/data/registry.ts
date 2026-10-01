export interface BrowserPage {
  /** 聚合页路径 */
  key: string
  /** 数据文件名（不含扩展名，位于 data/pages/）；默认取 key 转换，见命名约定 */
  file: string
  /** 聚合页 H1 */
  title: string
  /** 阅读页返回按钮文案；缺省为 `返回${title}` */
  backLabel?: string
  /** scope='all' 时左栏小标题 */
  heading?: string
  /** scope='group' 时每个 group 的左栏小标题 */
  groupHeadings?: Record<string, string>
  /** 兄弟文章范围：all=整页全部文章；group=仅同 group */
  scope: 'all' | 'group'
  /** 是否参与阅读页 sidebar 生成，默认 true */
  inSidebar?: boolean
  /** 是否有对应 md 消费（false=仅为 sidebar 提供数据，如进阶专题） */
  inBrowser?: boolean
}

export const registry: BrowserPage[] = [
  {
    key: '/cases/',
    file: 'cases-index',
    title: '故障复盘',
    scope: 'group',
    groupHeadings: {
      Linux: 'Linux 方向',
      网络: '网络方向',
      服务: '服务方向',
      MySQL: 'MySQL 方向',
      Redis: 'Redis 方向',
      'MQ / 集群': 'MQ 与集群方向',
      Docker: 'Docker 方向',
      Kubernetes: 'Kubernetes 方向',
      安全: '安全方向'
    }
  },
  {
    key: '/cases/troubleshooting',
    file: 'cases-troubleshooting',
    title: '排障记录',
    scope: 'group',
    inSidebar: false
  },
  { key: '/guide/linux', file: 'guide-linux', title: 'Linux 系统管理', scope: 'all', heading: 'Linux 方向' },
  { key: '/guide/services', file: 'guide-services', title: '服务部署', scope: 'all', heading: '服务部署方向' },
  { key: '/guide/data', file: 'guide-data', title: '数据与中间件', scope: 'all', heading: '数据与中间件方向' },
  { key: '/guide/monitor', file: 'guide-monitor', title: '监控与日志', scope: 'all', heading: '监控与日志方向' },
  { key: '/guide/container', file: 'guide-container', title: '容器与编排', scope: 'all', heading: '容器与编排方向' },
  { key: '/guide/automation', file: 'guide-automation', title: '自动化与 IaC', scope: 'all', heading: '自动化方向' },
  { key: '/guide/devops', file: 'guide-devops', title: 'DevOps 与平台工程', scope: 'all', heading: 'DevOps 方向' },
  { key: '/guide/aiops', file: 'guide-aiops', title: '智能运维与 AI', scope: 'all', heading: 'AIOps 方向' },
  { key: '/guide/architecture', file: 'guide-architecture', title: '架构设计', scope: 'all', heading: '架构设计方向' },
  { key: '/guide/blog', file: 'guide-blog', title: '运维手记', scope: 'all', heading: '手记方向' },
  { key: '/guide/career', file: 'guide-career', title: '职业发展与行业思考', scope: 'all', heading: '职业方向' },
  { key: '/guide/devops-dev', file: 'guide-devops-dev', title: '运维开发与平台自研', scope: 'all', heading: '运维开发方向' },
  {
    key: '/interview/',
    file: 'interview-index',
    title: '面试专区（私有）',
    scope: 'group',
    groupHeadings: {
      '求职准备': '求职准备方向',
      'Linux 系统': 'Linux 系统方向',
      '计算机网络': '计算机网络方向',
      '数据库与中间件': '数据库与中间件方向',
      '容器与云原生': '容器与云原生方向',
      '自动化、监控与云': '自动化监控方向',
      '综合场景题': '综合场景方向',
      'HR 与软素质': 'HR 与软素质方向'
    }
  },
  {
    key: '/roadmap',
    file: 'advanced',
    title: '学习路线',
    backLabel: '返回学习路线',
    scope: 'all',
    heading: '进阶专题',
    inBrowser: false
  }
]
