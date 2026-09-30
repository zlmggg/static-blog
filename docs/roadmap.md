# 学习路线

> 这是一条给"新手期的自己"的推荐学习路径。不用严格按顺序，遇到工作需要可以直接跳到对应板块。
> 每个阶段都配了聚合页和速查手册，建议"边学边动手在虚拟机上敲一遍"。

## 路线全景

```
Linux 基础 → 系统管理 → 常用服务 → 监控告警 → 容器与 K8s → 自动化/IaC → 故障实战
```

## 阶段一：Linux 基础与系统管理

**目标：** 能独立装好系统、连上去、熟练操作文件和命令。

- 安装与初始环境、发行版差异（RHEL / Debian）
- 文件目录、文本三剑客（grep / sed / awk）
- 用户权限、磁盘存储、进程服务、定时任务
- 配合：[Linux 命令速查](/reference/linux-commands)

👉 进入 [Linux 系统指南](/guide/linux)

## 阶段二：网络与安全

**目标：** 理解网络配置，能做基础安全加固。

- 网络接口 / IP / 端口、防火墙 iptables / firewalld / ufw
- SSH 加固、SELinux、SSL 证书、NTP 时间同步
- 配合：[网络命令速查](/reference/network-commands)

👉 见 [Linux 系统指南 - 安全加固](/guide/linux)

## 阶段三：常用服务部署

**目标：** 能独立部署和运维常见服务。

- Web：Nginx（反向代理 / 负载均衡）、Apache、Tomcat
- DNS：BIND 域名解析
- 文件共享：NFS、Samba、FTP

👉 进入 [服务部署指南](/guide/services)

## 阶段四：数据库与中间件

**目标：** 掌握数据服务的部署、优化、备份和高可用。

- MySQL：基础 → 索引优化 → 备份 → 主从复制 / MHA / MyCat
- Redis：持久化、主从 / 哨兵 / Cluster
- Kafka、Spring Cloud（Nacos / Sentinel / Seata / Gateway）、APISIX

👉 进入 [数据与中间件指南](/guide/data)

## 阶段五：监控告警与日志

**目标：** 能搭建监控体系、配置告警、收集分析日志。

- Zabbix（监控项 / 触发器 / 模板 / 自动发现）
- Prometheus + Alertmanager + Grafana
- ELK / Filebeat 日志平台
- JumpServer 堡垒机

👉 进入 [监控与日志指南](/guide/monitor)

## 阶段六：容器与 Kubernetes

**目标：** 掌握容器化和容器编排，这是当前运维最"值钱"的方向。

- Docker：镜像、网络、存储、Compose
- Kubernetes：架构 → 工作负载 → Service/Ingress → 存储 → Helm → 安全 / 调度 / 运维
- 服务网格 Istio、链路追踪、大模型部署
- 配合：[Docker 命令速查](/reference/docker-commands)、[kubectl 命令速查](/reference/kubectl-commands)

👉 进入 [容器与编排指南](/guide/container)

## 阶段七：自动化与 IaC

**目标：** 把重复工作自动化，用代码管理基础设施。

- Ansible 配置管理
- Git / GitLab / Jenkins 流水线
- GitLab CI / ArgoCD（GitOps）
- Terraform 基础设施即代码

👉 进入 [自动化与 IaC 指南](/guide/automation)

## 阶段八：故障实战（贯穿始终）

**目标：** 在真实问题中沉淀经验。

- 日常小问题记到 [排障记录](/cases/troubleshooting)
- 重大故障写 [故障复盘](/cases/)，总结根因和预防措施

## 学习建议

1. **动手优先**：每个知识点都在虚拟机或测试环境实操一遍。
2. **记笔记**：解决一个问题就沉淀一篇，命令补进速查长文档。
3. **重搜索**：本站内容用 `Ctrl+K` 快速检索。
4. **不焦虑进度**：按工作需要驱动学习，用到再深挖。
