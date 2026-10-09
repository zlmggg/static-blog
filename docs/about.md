# 关于本站

## 这是什么网站

**禾光知寒 · SRE Notes** — sresec.com

这是我的个人 SRE 运维知识库，攒的都是 Linux 运维、服务部署、监控告警、日常排障、容器与云原生、自动化这些方向的笔记和实战记录。

现在 AI 是真好用，遇到问题丢给它，多半很快就有答案。可命令、配置、参数这些东西，看过就忘；等到自己上手、尤其是在生产环境，总不能每次都从头问一遍。

所以我把跑通过的方案、踩过的坑都记在这儿。**下次再碰到，搜一下就能很快想起来该怎么处理**，踏实。

要是这些能直接抄走的方案，顺手也帮到了同样在路上的你，那就再好不过了。


## 内容板块

| 板块 | 内容 |
|---|---|
| [速查手册](/reference/linux-commands) | Linux / 网络 / Docker / kubectl 命令速查长文档 |
| [Linux 系统](/guide/linux) | 系统管理、存储、用户权限、Shell、安全加固 |
| [服务部署](/guide/services) | Nginx、Apache/Tomcat、DNS、文件共享 |
| [数据与中间件](/guide/data) | MySQL、Redis、Kafka、Spring Cloud、APISIX |
| [监控与日志](/guide/monitor) | Zabbix、Prometheus、ELK、JumpServer |
| [容器与编排](/guide/container) | Docker、Kubernetes、服务网格、大模型部署 |
| [自动化与 IaC](/guide/automation) | Ansible、Jenkins、GitOps、Terraform |
| [故障与排障](/cases/) | 故障复盘 + 日常排障记录 |

## 如何使用这个站

1. **最快：按 `Ctrl+K`（Mac 为 `Cmd+K`）打开搜索**，输入命令或报错关键词，直接跳转。
2. 想系统浏览：从顶部「操作指南」进入各板块的聚合页。
3. 忘了命令：查「速查手册」长文档，用右侧「本页目录」跳转。

## 关于我

一名 Linux 运维工程师，坐标成都。喜欢把踩过的坑整理成可复制的方案，坚持"用过一次的操作就沉淀成文档"。

- 岗位方向：Linux SRE / 运维开发（容器化、监控告警、自动化方向）
- 技术兴趣：Linux 系统原理、KVM/OpenStack 私有云、Docker 与 Kubernetes、Prometheus/Zabbix 监控、Ansible/Terraform 自动化
- 联系方式 / 邮箱：[zlmops@163.com](mailto:zlmops@163.com)
- GitHub：[嘿嘿嘿](https://github.com/heiheihei)
- Gitee：[本站](https://gitee.com/zlmggg/static-blog)

## 技术栈

本站基于 [VitePress](https://vitepress.dev/zh/) 构建，Markdown 驱动，构建产物为纯静态文件；服务端通过 [Docker](https://www.docker.com/) 运行 [Nginx](https://nginx.org/) 容器进行托管。

内容编写与技术排障由 [豆包 Doubao](https://www.doubao.com) 辅助完成。

## 快速上手

- 欢迎有缘人如果你是新学习的运维同学，欢迎来到这个知识库。
- 不知道从哪开始：看 [学习路线](/roadmap)
- 忘了命令：查 [速查手册](/reference/linux-commands)
- 日常排障：记 [排障记录](/cases/troubleshooting)
