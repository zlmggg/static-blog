import type { Article } from '../types'

const articles: Article[] = [
  {
    group: '关系型数据库',
    title: 'MySQL 基础',
    link: '/guide/data-mysql',
    sub: '安装、SQL 基础、用户权限、存储引擎、数据类型'
  },
  {
    group: '关系型数据库',
    title: 'MySQL 进阶与高可用',
    link: '/guide/data-mysql-advanced',
    sub: '索引/EXPLAIN、慢查询、备份恢复、主从复制、MHA/MGR、MyCat、运维排查'
  },
  {
    group: '缓存与消息队列',
    title: 'Redis',
    link: '/guide/data-redis',
    sub: '数据类型、持久化、主从 / 哨兵 / Cluster'
  },
  {
    group: '缓存与消息队列',
    title: 'Kafka',
    link: '/guide/data-kafka',
    sub: '架构、部署、主题 / 分区 / 消费者组'
  },
  {
    group: '微服务与网关',
    title: 'Spring Cloud 全家桶',
    link: '/guide/data-spring-cloud',
    sub: 'Nacos（含集群）、Sentinel、Seata、Gateway'
  },
  {
    group: '微服务与网关',
    title: 'APISIX 与 MinIO',
    link: '/guide/data-apisix-minio',
    sub: 'APISIX 路由/插件、MinIO 对象存储'
  }
]

export default articles
