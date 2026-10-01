import type { Article } from '../types'

const articles: Article[] = [
  // 求职准备
  { group: '求职准备', title: '自我介绍', sub: '1/3 分钟版本、表达结构', link: '/interview/prep-introduction' },
  { group: '求职准备', title: '简历与项目经历', sub: 'STAR、项目亮点、追问', link: '/interview/prep-resume' },
  { group: '求职准备', title: '面试流程与策略', sub: '流程、准备清单、复盘', link: '/interview/prep-strategy' },
  // Linux 系统
  { group: 'Linux 系统', title: '系统基础与启动流程', sub: '开机流程、发行版区别、优化', link: '/interview/linux-boot' },
  { group: 'Linux 系统', title: '用户权限与安全', sub: 'rwx、sudo、链接、umask', link: '/interview/linux-user-security' },
  { group: 'Linux 系统', title: '文件系统与存储管理', sub: 'LVM、RAID、inode、磁盘排查', link: '/interview/linux-storage' },
  { group: 'Linux 系统', title: '进程管理与资源监控', sub: 'CPU/内存/负载、僵尸进程', link: '/interview/linux-process' },
  { group: 'Linux 系统', title: 'Shell 编程与文本处理', sub: '语法、grep/awk/sed、find', link: '/interview/linux-shell' },
  // 计算机网络
  { group: '计算机网络', title: 'TCP/IP 与 HTTP', sub: '握手挥手、HTTPS、状态码', link: '/interview/network-tcp-http' },
  { group: '计算机网络', title: '网络服务与排障', sub: 'DNS、端口、抓包', link: '/interview/network-troubleshooting' },
  // 数据库与中间件
  { group: '数据库与中间件', title: 'MySQL 与 MariaDB', sub: '索引、事务、慢查询、主从', link: '/interview/data-mysql' },
  { group: '数据库与中间件', title: 'Redis', sub: '数据类型、持久化、缓存问题', link: '/interview/data-redis' },
  { group: '数据库与中间件', title: 'Nginx 与 Web 服务', sub: '代理、负载均衡、502 排查', link: '/interview/services-nginx' },
  // 容器与云原生
  { group: '容器与云原生', title: 'Docker', sub: '网络、原理、镜像优化、排错', link: '/interview/container-docker' },
  { group: '容器与云原生', title: 'Kubernetes', sub: '架构、Pod、Service、更新', link: '/interview/container-k8s' },
  // 自动化、监控与云
  { group: '自动化、监控与云', title: 'CI/CD 持续交付', sub: '流水线、发布策略', link: '/interview/automation-cicd' },
  { group: '自动化、监控与云', title: '云平台与自动化运维', sub: '云产品、Ansible、Terraform', link: '/interview/automation-cloud' },
  { group: '自动化、监控与云', title: '监控告警与日志', sub: 'Prometheus、告警、ELK', link: '/interview/monitor-observability' },
  // 综合场景题
  { group: '综合场景题', title: '故障排查实战', sub: '排障方法论、综合故障', link: '/interview/scenario-troubleshooting' },
  { group: '综合场景题', title: '系统设计题', sub: '容量评估、高可用设计', link: '/interview/scenario-design' },
  { group: '综合场景题', title: '命令实操题', sub: '日志统计、批量操作', link: '/interview/scenario-commands' },
  // HR 与软素质
  { group: 'HR 与软素质', title: '行为面试题', sub: 'STAR、冲突压力失败', link: '/interview/hr-behavior' },
  { group: 'HR 与软素质', title: '职业规划与谈薪', sub: '规划、薪资、反问、offer', link: '/interview/hr-career' },
]

export default articles
