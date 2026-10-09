# 文件导航对照表

> 文件名用英文（URL 专业、友好），这里列出**每个英文文件名对应的中文标题**。
> 找文件、加内容对照本表即可。各系列文章均已完成；后续新增内容时，可沿用"✏️ 该节写什么"的中文指引方式标注待补小节。

## 顶层文件

| 文件名 | 中文标题 | 状态 |
|---|---|---|
| `index.md` | 首页 | ✅ |
| `about.md` | 关于本站 | ✅（通用文案已写，【】处替换为本人信息） |
| `roadmap.md` | 学习路线 | ✅ |

## reference/ —— 速查手册（长文档，核心命令已填，可继续补）

| 文件名 | 中文标题 |
|---|---|
| `linux-commands.md` | Linux 命令速查 |
| `network-commands.md` | 网络命令速查 |
| `docker-commands.md` | Docker 命令速查 |
| `kubectl-commands.md` | kubectl 命令速查 |

## guide/ —— 操作指南

### 聚合页（章节首页）

| 文件名 | 中文标题 |
|---|---|
| `linux.md` | Linux 系统管理（聚合页） |
| `services.md` | 服务部署（聚合页） |
| `data.md` | 数据与中间件（聚合页） |
| `monitor.md` | 监控与日志（聚合页） |
| `container.md` | 容器与编排（聚合页） |
| `automation.md` | 自动化与 IaC（聚合页） |

### Linux 系列（✅ 已完成）

| 文件名 | 中文标题 |
|---|---|
| `linux-install.md` | 安装与初始环境 |
| `linux-filesystem.md` | 文件系统 |
| `linux-storage.md` | 磁盘存储 |
| `linux-users.md` | 用户、权限与认证 |
| `linux-process.md` | 进程与服务管理 |
| `linux-cron.md` | 定时任务 |
| `linux-kernel.md` | 内核调优与资源限制 |
| `linux-log.md` | 日志管理 |
| `linux-shell.md` | Shell 脚本编程 |
| `linux-security.md` | 安全加固 |
| `linux-security-iptables.md` | iptables 防火墙 |
| `linux-performance.md` | 性能排查（top/vmstat/iostat/pidstat） |

### 服务系列（✅ 已完成）

| 文件名 | 中文标题 |
|---|---|
| `services-web-nginx.md` | Nginx 实战 |
| `services-web-apache-tomcat.md` | Apache 与 Tomcat |
| `services-dns.md` | DNS 域名解析 |
| `services-file-sharing.md` | 文件共享服务 |

### 数据系列（✅ 已完成）

| 文件名 | 中文标题 |
|---|---|
| `data-mysql.md` | MySQL 基础 |
| `data-mysql-advanced.md` | MySQL 进阶与高可用 |
| `data-redis.md` | Redis |
| `data-kafka.md` | Kafka |
| `data-spring-cloud.md` | Spring Cloud 微服务 |
| `data-apisix-minio.md` | APISIX 与 MinIO |

### 监控系列（✅ 已完成）

| 文件名 | 中文标题 |
|---|---|
| `monitor-zabbix.md` | Zabbix 基础 |
| `monitor-zabbix-advanced.md` | Zabbix 进阶 |
| `monitor-prometheus.md` | Prometheus 监控 |
| `monitor-elk.md` | ELK 日志平台 |
| `monitor-jumpserver.md` | JumpServer 堡垒机 |

### 容器系列（✅ 已完成）

| 文件名 | 中文标题 |
|---|---|
| `container-docker.md` | Docker 实战 |
| `container-k8s-01-architecture-cluster.md` | K8s 01：架构与集群部署 |
| `container-k8s-02-pod-service-discovery.md` | K8s 02：Pod 管理与服务发现 |
| `container-k8s-03-storage-ingress.md` | K8s 03：存储与 Ingress |
| `container-k8s-04-statefulset-security.md` | K8s 04：有状态服务与安全 |
| `container-k8s-05-appendix-sop-commands.md` | K8s 05：运维 SOP 与 FAQ |
| `container-servicemesh.md` | 服务网格与链路追踪 |
| `container-llm.md` | 大模型部署 |

### 自动化系列（✅ 已完成）

| 文件名 | 中文标题 |
|---|---|
| `automation-ansible.md` | Ansible 自动化 |
| `automation-jenkins.md` | Git / GitLab / Jenkins |
| `automation-gitops.md` | GitLab CI / ArgoCD |
| `automation-terraform.md` | Terraform 基础设施即代码 |

## cases/ —— 故障与排障

| 文件名 | 中文标题 |
|---|---|
| `index.md` | 故障复盘（索引 + 模板） |
| `troubleshooting.md` | 排障记录（表格速查） |

## 命名规律

- **前缀 = 板块**：`linux-` / `services-` / `data-` / `monitor-` / `container-` / `automation-`
- **K8s 数字编号**：`container-k8s-01` ~ `05` 按学习顺序
- **聚合页**：直接用板块名（如 `guide/linux.md`）
