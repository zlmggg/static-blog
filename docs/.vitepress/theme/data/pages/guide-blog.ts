import type { Article } from '../types'

const articles: Article[] = [
  {
    group: '现场故事',
    title: '割接 / 上线夜全记录',
    link: '/guide/blog-go-live-night',
    sub: '一次跨 Nginx + K8s + 数据库主从 + DNS 的割接，从傍晚准备到凌晨收尾的完整时间线与“回滚 vs 修复”决策',
  },
  {
    group: '现场故事',
    title: '值班惊魂：一次告警风暴的真实处置',
    link: '/guide/blog-oncall-thriller',
    sub: '告警轰炸下先误判方向、再收敛定位根因（连接池耗尽）、止血与根治的全过程',
  },
  {
    group: '现场故事',
    title: '典型踩坑实录（短案例集）',
    link: '/guide/blog-war-stories',
    sub: '12 条短小踩坑：误删、inode 满、时区、缓存雪崩、连接数打满、改配置没 reload、通配符误伤……',
  },
  {
    group: '排障方法论',
    title: '信息不全时的排障推理框架',
    link: '/guide/blog-troubleshooting-reasoning',
    sub: '高压、信息不全下怎么分层排查、用二分法、最近变更优先、假设-验证、先止血后根治',
  },
  {
    group: '排障方法论',
    title: '现场经验法则与“土办法”',
    link: '/guide/blog-field-rules',
    sub: '30 条排障/操作/安全/沟通的经验法则：先看最近变更、重启前留现场、删除前先移动观察……',
  },
  {
    group: '实战脚本集',
    title: '巡检 / 自愈 / 批量操作脚本集',
    link: '/guide/blog-scripts-ops',
    sub: '批量主机巡检、阈值巡检、服务异常自愈拉起、带白名单与二次确认的批量执行',
  },
  {
    group: '实战脚本集',
    title: '备份 / 清理 / 证书巡检脚本集',
    link: '/guide/blog-scripts-backup',
    sub: '日志切割清理、带校验和与轮转的备份、证书到期巡检、数据一致性校验',
  },
  {
    group: '硬核实战专题',
    title: '性能调优实战全流程',
    link: '/guide/expert-perf-tuning',
    sub: 'USE/RED、wrk/vegeta/k6 压测、四类瓶颈定位、调优参数与前后对比',
  },
  {
    group: '硬核实战专题',
    title: '高并发 / 限流降级与流量调度',
    link: '/guide/expert-high-concurrency',
    sub: '容量评估、令牌桶/漏桶/滑动窗口、熔断降级、灰度与多活 GSLB',
  },
  {
    group: '硬核实战专题',
    title: '疑难杂症专题',
    link: '/guide/expert-tough-cases',
    sub: '内存泄漏、fd/连接耗尽、OOM、卡顿、丢包重传、时钟、脑裂',
  },
  {
    group: '硬核实战专题',
    title: '安全应急响应',
    link: '/guide/expert-security-incident',
    sub: '被入侵/挖矿/木马/webshell 的隔离、取证、清除、溯源与加固闭环',
  },
  {
    group: '硬核实战专题',
    title: '从零落地监控自动化 SRE',
    link: '/guide/expert-from-zero',
    sub: '小公司/传统企业分阶段落地路径、优先级取舍与开源选型',
  },
  {
    group: '硬核实战专题',
    title: '生产配置最佳实践模板',
    link: '/guide/config-best-practices',
    sub: 'Nginx/MySQL/Redis/K8s/内核参数模板，逐项注释为什么这么设',
  },
]

export default articles
