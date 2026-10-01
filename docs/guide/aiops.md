# 智能运维与 AI

> 本页聚合 **AI Agent 基础、MCP 协议、Agent 运维实战、RAG 知识库、传统 AIOps**，目标是把大模型/智能体真正用到 SRE 日常——告警归因、日志分析、知识库问答、自动诊断，而不是停留在聊天框里。

## 文章索引

### AI Agent 基础

::: idx

| 文章 | 解决什么问题 | 状态 |
|---|---|---|
| [AI Agent 与 LLM 应用基础](./aiops-agent-basics) | Token、上下文窗口、温度、Prompt 工程、记忆、Function Calling、ReAct/Plan-and-Execute、多 Agent 协作、LangChain/AutoGen 选型 | ✅ 已完成 |

:::

### MCP 与协议

::: idx

| 文章 | 解决什么问题 | 状态 |
|---|---|---|
| [MCP 模型上下文协议](./aiops-mcp) | Host/Client/Server 关系、stdio 与 HTTP 传输、Tools/Resources/Prompts 原语、把 K8s/云/数据库/Git/监控接入 Agent、用官方 SDK 自建 MCP Server | ✅ 已完成 |

:::

### 运维实战

::: idx

| 文章 | 解决什么问题 | 状态 |
|---|---|---|
| [Agent 运维实战](./aiops-agent-practice) | 日志分析、告警归因、故障诊断、自动生成 Runbook、人机协同（human-in-the-loop）安全边界、Dify/n8n/LangGraph 端到端编排 | ✅ 已完成 |

:::

### RAG 与知识库

::: idx

| 文章 | 解决什么问题 | 状态 |
|---|---|---|
| [运维知识库与 RAG](./aiops-rag) | 幻觉与私有知识、文档切分、Embedding 与向量库选型、混合检索与重排、把本知识库接入 LLM、Ollama 私有化方案 | ✅ 已完成 |

:::

### 传统 AIOps

::: idx

| 文章 | 解决什么问题 | 状态 |
|---|---|---|
| [传统 AIOps 与机器学习](./aiops-ml) | 时序异常检测（3-sigma/EWMA/Prophet/孤立森林）、告警降噪聚合关联、Drain 日志模板、根因定位、传统 ML 与 LLM Agent 的分工 | ✅ 已完成 |

:::

## 命令速查

- 运维场景的 AI Prompt 与 Agent 指令模板：[运维 AI Prompt 速查](/reference/ai-prompts)
- 云原生排障与可观测命令：[云原生命令速查](/reference/cloudnative-commands)
- 模型部署相关：[大模型部署](./container-llm)
- 监控数据来源：[Prometheus 监控](./monitor-prometheus)
