import type { Article } from '../types'

const articles: Article[] = [
  {
    group: '方法论',
    title: '架构设计方法论',
    link: '/guide/architecture-methodology',
    sub: '高可用/高性能/可扩展/安全/成本/可观测六大目标的取舍；单体→云原生演进；CAP/BASE/一致性；限流/降级/熔断；设计流程',
  },
  {
    group: '方法论',
    title: '容量估算与服务器选型',
    link: '/guide/architecture-capacity-sizing',
    sub: '从日 PV 推算峰值 QPS，各层单机承载经验值，日 PV 1 万~1 亿五档机器数量与配置清单，3 年预留与压测校验',
  },
  {
    group: '方法论',
    title: '高可用与容灾模式',
    link: '/guide/architecture-ha-blueprints',
    sub: '单点→主备→双活→集群→两地三中心→异地多活演进；分层负载均衡；MySQL/Redis/MQ 高可用；脑裂防护；RTO/RPO；备份 3-2-1',
  },
  {
    group: '行业实战',
    title: '实战：门户 / 官网架构',
    link: '/guide/arch-case-website',
    sub: '静态站点 + CDN + Nginx 的高性价比架构，日 PV 百万级内容站怎么扛',
  },
  {
    group: '行业实战',
    title: '实战：电商架构',
    link: '/guide/arch-case-ecommerce',
    sub: '下单/购物车/库存的读写分离、分库分表、缓存与 MQ 削峰、大促洪峰应对',
  },
  {
    group: '行业实战',
    title: '实战：微服务架构',
    link: '/guide/arch-case-microservice',
    sub: '服务拆分边界、注册发现、网关、配置中心、链路追踪与治理落地',
  },
  {
    group: '行业实战',
    title: '实战：App 后端架构',
    link: '/guide/arch-case-app',
    sub: '移动 App 的长连接、推送、接口网关、鉴权与海量终端接入设计',
  },
  {
    group: '行业实战',
    title: '实战：金融 / 支付架构',
    link: '/guide/arch-case-banking',
    sub: '强一致、账务安全、异地多活、合规审计与极高可用要求下的取舍',
  },
  {
    group: '行业实战',
    title: '实战：游戏架构',
    link: '/guide/arch-case-game',
    sub: '长连接网关、游戏服分区、状态同步、对战实时性与开服合服',
  },
  {
    group: '行业实战',
    title: '实战：IM 即时通讯架构',
    link: '/guide/arch-case-im',
    sub: '消息投递、在线状态、群消息扩散、离线消息与多端同步的高并发设计',
  },
]

export default articles
