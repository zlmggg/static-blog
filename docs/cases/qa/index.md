# 问与答

> 这里是归在排障训练场下的**自测问答库**：每篇按「问题 → 我的答案」组织，技术题按方向分组。
>
> 求职、简历、HR 这类个人内容不再上公开站；技术问题本身留着，因为面试问的和生产环境遇到的是同一批知识点。

## 怎么用

1. 先看问题，出声或写下来自己答一遍；
2. 再对照「我的答案」，记下卡壳的点；
3. 隔几天只看问题再复述一次。忘了关键词就 `Ctrl+K` 搜。

## Linux 系统

| 主题 | 覆盖内容 | 状态 |
|---|---|---|
| [系统基础与启动流程](./linux-boot) | 开机流程、发行版区别、优化 | ✅ 已完成 |
| [用户权限与安全](./linux-user-security) | rwx、sudo、链接、umask | ✅ 已完成 |
| [文件系统与存储管理](./linux-storage) | LVM、RAID、inode、磁盘排查 | ✅ 已完成 |
| [进程管理与资源监控](./linux-process) | CPU/内存/负载、僵尸进程 | ✅ 已完成 |
| [Shell 编程与文本处理](./linux-shell) | 语法、grep/awk/sed、find | ✅ 已完成 |

## 计算机网络

| 主题 | 覆盖内容 | 状态 |
|---|---|---|
| [TCP/IP 与 HTTP](./network-tcp-http) | 握手挥手、HTTPS、状态码 | ✅ 已完成 |
| [网络服务与排障](./network-troubleshooting) | DNS、端口、抓包 | ✅ 已完成 |

## 数据库与中间件

| 主题 | 覆盖内容 | 状态 |
|---|---|---|
| [MySQL 与 MariaDB](./data-mysql) | 索引、事务、慢查询、主从 | ✅ 已完成 |
| [Redis](./data-redis) | 数据类型、持久化、缓存问题 | ✅ 已完成 |
| [Nginx 与 Web 服务](./services-nginx) | 代理、负载均衡、502 排查 | ✅ 已完成 |

## 容器与云原生

| 主题 | 覆盖内容 | 状态 |
|---|---|---|
| [Docker](./container-docker) | 网络、原理、镜像优化、排错 | ✅ 已完成 |
| [Kubernetes](./container-k8s) | 架构、Pod、Service、更新 | ✅ 已完成 |

## 自动化、监控与云

| 主题 | 覆盖内容 | 状态 |
|---|---|---|
| [CI/CD 持续交付](./automation-cicd) | 流水线、发布策略 | ✅ 已完成 |
| [云平台与自动化运维](./automation-cloud) | 云产品、Ansible、Terraform | ✅ 已完成 |
| [监控告警与日志](./monitor-observability) | Prometheus、告警、ELK | ✅ 已完成 |

## 综合场景题

| 主题 | 覆盖内容 | 状态 |
|---|---|---|
| [故障排查实战](./scenario-troubleshooting) | 排障方法论、综合故障 | ✅ 已完成 |
| [系统设计题](./scenario-design) | 容量评估、高可用设计 | ✅ 已完成 |
| [命令实操题](./scenario-commands) | 日志统计、批量操作 | ✅ 已完成 |

## 相关

- 真实故障复盘与排障套路：[排障训练场](/cases/)
- 日常小问题与踩坑记录：[排障记录](/cases/troubleshooting)
