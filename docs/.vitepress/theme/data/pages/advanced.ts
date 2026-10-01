import type { Article } from '../types'

const articles: Article[] = [
  {
    group: '进阶专题',
    title: '小公司 / 传统企业从零落地监控、自动化与 SRE',
    link: '/guide/expert-from-zero',
    sub: '面向人少、预算紧、历史包袱重的团队：怎么从"出了事才知道"一步步走到有监控、有自动化、有 SRE 稳定性思维。不堆大厂架…'
  },
  {
    group: '进阶专题',
    title: '高并发 / 高可用 / 多活：限流降级与流量调度',
    link: '/guide/expert-high-concurrency',
    sub: '面向中高级 SRE/架构：从容量评估（Little\'s Law）讲起，给到限流三种算法的可运行代码、Nginx limi…'
  },
  {
    group: '进阶专题',
    title: '性能调优实战全流程',
    link: '/guide/expert-perf-tuning',
    sub: '面向中高级 SRE/后端：把"感觉慢、压不上去"变成一套可复制的闭环——定目标、压测建基线、按 USE/RED 定位 C…'
  },
  {
    group: '进阶专题',
    title: '安全应急响应：主机被入侵 / 挖矿 / 木马 / WebShell 处置闭环',
    link: '/guide/expert-security-incident',
    sub: '聚焦"机器已经被黑了之后怎么办"——发现迹象、隔离、现场取证、清除后门、溯源入口、加固复盘。与 linux-securi…'
  },
  {
    group: '进阶专题',
    title: '疑难杂症专题：从现象到根因的定位手册',
    link: '/guide/expert-tough-cases',
    sub: '面向中高级 SRE：把生产上最折腾人的七类疑难杂症，按统一结构「现象 → 定位命令 → 根因 → 处置 → 预防」写死。…'
  },
  {
    group: '进阶专题',
    title: '生产配置最佳实践模板（逐项注释"为什么"）',
    link: '/guide/config-best-practices',
    sub: '把生产里最常配的五类——Nginx、MySQL、Redis、Kubernetes、内核 sysctl——整理成可整段复制…'
  }
]

export default articles
