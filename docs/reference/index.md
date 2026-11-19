---
title: "速查手册"
description: "8 本手册 + 46 篇独立命令详解；其余命令已压缩进各手册的「命令坑点索引」。按 入门 → 进阶 → 高级 排列：越往后越依赖前面的基础。 知道命令名或报错关键词：直接 Ctrl+K。知道要做什么、但不知道用哪条：先看下面的「30 秒定位」。"
---
# 速查手册

> 8 本手册 + 46 篇独立命令详解。其余命令不再单独成页，统一收进各手册末尾的「命令坑点索引」。
>
> 知道命令名或报错关键词：直接 `Ctrl+K`。知道要做什么、但不知道用哪条：先看下面的「30 秒定位」。

## 30 秒定位

| 我要做的事 | 先查这本 |
|---|---|
| 文件、权限、进程、磁盘、包管理 | [Linux 命令速查](/reference/linux-commands) |
| 服务起不来、开机自启、看 journalctl、SSH 免密/传文件 | [Linux 命令速查](/reference/linux-commands) |
| 连不上、丢包、端口、DNS、抓包 | [网络命令速查](/reference/network-commands) |
| HTTPS 证书报错、TLS 握手、带宽压测 | [网络命令速查](/reference/network-commands) |
| 容器起不来、进不去、镜像/网络/卷 | [Docker 命令速查](/reference/docker-commands) |
| 写 Dockerfile、多阶段构建、Compose 编排 | [Docker 命令速查](/reference/docker-commands) |
| 分支、合并、回滚、提交历史 | [Git 工作流速查](/reference/git-commands) |
| Pod、Deployment、Service 排障 | [kubectl 命令速查](/reference/kubectl-commands) |
| Job/CronJob/HPA、节点 cordon/drain | [kubectl 命令速查](/reference/kubectl-commands) |
| Helm、CRI、OTel、Cilium、Ingress、kubeadm/etcd | [云原生命令速查](/reference/cloudnative-commands) |
| 让 AI 按固定格式输出、写可复用提示词 | [AI Prompt 模板](/reference/ai-prompts) |
| 写变更、复盘、交接、架构评审 | [运维文档模板](/reference/ops-templates) |
| 上线前、巡检、应急、安全基线 | [运维模板与清单](/reference/ops-templates#运维检查清单) |
| 让 AI 按固定格式解释/诊断/写脚本 | [AI Prompt 模板](/reference/ai-prompts) |

## 入门 · 单机日常

> 先把一台 Linux 上的事处理顺：文件、权限、进程、磁盘、网络连通性。

::: idx

| 手册 | 用途与覆盖 | 体量 |
|---|---|---|
| [Linux 命令速查](/reference/linux-commands) | 文件与目录、查看与编辑、管道与重定向、grep/sed/awk、用户与权限、进程、内存与性能、磁盘、内核限制、时间任务、包管理，以及 **systemd 服务/日志（systemctl、journalctl）**、**SSH/rsync 远程传输**、**ncdu/smartctl 磁盘巡检**、**tmux/screen 会话保持**、**strace/perf 性能与系统调用**、**logrotate 日志轮转**、**ethtool/iptables/firewalld 网络与防火墙**。忘了参数、要拼组合命令时先查这本。 | 24 篇独立详解 + 坑点索引 |
| [网络命令速查](/reference/network-commands) | ip/ss 查接口与端口，ping/traceroute 查连通，dig 查 DNS，tcpdump 抓包，curl/wget 测 HTTP，另有 **TLS 证书排查（openssl）**、**certbot 证书申请与续期**、**iperf3 带宽压测**、流量监控、ARP、防火墙。排查“连不上、慢、丢包、解析失败”的第一站。 | 7 篇独立详解 + 坑点索引 |

:::

## 进阶 · 容器与版本协作

> 从“操作一台机器”，过渡到“管理应用运行环境”和“多人协作改同一份代码”。

::: idx

| 手册 | 用途与覆盖 | 体量 |
|---|---|---|
| [Docker 命令速查](/reference/docker-commands) | run/ps/exec/logs/inspect、镜像与仓库登录、**Dockerfile 指令与多阶段构建**、buildx 跨平台、网络、存储卷、清理、**Compose 文件与子命令**。容器起不来、进不去、日志在哪看、镜像怎么构建时查。 | 5 篇独立详解 + 坑点索引 |
| [Git 工作流速查](/reference/git-commands) | 初始配置、clone、add/commit/push/pull、log/diff、分支、merge/rebase、远程协作、reset/revert/restore、stash、tag、submodule、reflog/worktree、团队工作流。改坏了要回滚、分支乱了要收拾时查。 | 3 篇独立详解 + 坑点索引 |

:::

## 高级 · 集群与云原生

> 排 Pod、看集群、查运行时与网格；kubectl 不够用时再进云原生那本。

::: idx

| 手册 | 用途与覆盖 | 体量 |
|---|---|---|
| [kubectl 命令速查](/reference/kubectl-commands) | 集群与节点、资源查看、apply/create、edit/scale/delete、describe/logs/exec/port-forward、**Job/CronJob/HPA/PDB**、**cordon/drain/taint 节点维护**、RBAC 权限自检、context、Helm。Pod 不 Ready、发布卡住、节点要升级时按这页查。 | 4 篇独立详解 + 坑点索引 |
| [云原生命令速查](/reference/cloudnative-commands) | **kubeadm 升级与证书续期、etcd 健康/备份/恢复**、Helm release 排障、kubectl 进阶、containerd/CRI、OpenTelemetry Collector、日志与链路、Cilium/eBPF、Ingress 与服务网格。 | 3 篇独立详解 + 坑点索引 |

:::

## 配套 · 模板与清单

> 不属于命令难度序列，但和“少漏步骤、少写废话”直接相关，建议和上面三组配合用。

::: idx

| 手册 | 用途与覆盖 | 体量 |
|---|---|---|
| [AI Prompt 模板](/reference/ai-prompts) | 12 类指令：解释命令/配置、生成 Shell/Python 脚本、日志诊断、告警分析、性能分析、配置安全审查、Runbook、SQL 与正则、方案评审、多 Agent 分工。复制模板、替换占位符即可用。 | 12 类指令 |
| [运维文档模板与清单](/reference/ops-templates) | 变更/割接方案、故障报告、无指责复盘、交接文档、架构评审记录；上线前检查、日常巡检、应急响应、安全基线、容量评估、迁移/割接、灾备演练。要交文档、要复盘时直接套。 | 5 类文档 + 7 份清单 |

:::

## 各领域常见问题 FAQ

> 原先独立的 78 个问答已并入对应领域页末尾；下面按领域给入口，点进去后用「本页目录」跳到「常见问题 FAQ」。

| 领域 | 高频问题 |
|---|---|
| Linux 系统 | [Linux 系统 FAQ](/guide/linux#常见问题-faq) |
| 网络与连通性 | [网络 FAQ](/guide/linux-network#常见问题-faq) |
| 容器与 K8s | [容器与 K8s FAQ](/guide/container#常见问题-faq) |
| 数据库与中间件 | [数据库 FAQ](/guide/data#常见问题-faq) |
| 监控、告警与日志 | [监控 FAQ](/guide/monitor#常见问题-faq) |
| 云服务器与自动化 | [云与自动化 FAQ](/guide/automation#常见问题-faq) |
| 综合场景与排障 | [综合场景 FAQ](/cases/#常见问题-faq) |

## 怎么用

- **查单条命令**：`Ctrl+K` 搜命令名；高频命令有独立详解页，其余命令进对应手册的「命令坑点索引」看最容易踩的坑。
- **查一个场景**：先用上面的「30 秒定位」选手册，再用右侧「本页目录」跳到对应分类。
- **系统补基础**：入门组按顺序过一遍；进阶、高级组按工作用到再查，不必从头背。
- **查完想继续深入**：独立详解页底部有「相关命令与文档」；被合并的命令直接看手册里的坑点索引与官方文档链接。
