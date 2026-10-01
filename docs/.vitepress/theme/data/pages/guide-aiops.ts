import type { Article } from '../types'

const articles: Article[] = [
  {
    group: 'AI Agent 基础',
    title: 'AI Agent 与 LLM 应用基础',
    link: '/guide/aiops-agent-basics',
    sub: 'Token、上下文窗口、温度、Prompt 工程、记忆、Function Calling、ReAct/Plan-and-Execute、多 Agent 协作、LangChain/AutoGen 选型',
  },
  {
    group: 'MCP 与协议',
    title: 'MCP 模型上下文协议',
    link: '/guide/aiops-mcp',
    sub: 'Host/Client/Server 关系、stdio 与 HTTP 传输、Tools/Resources/Prompts 原语、把 K8s/云/数据库/Git/监控接入 Agent、用官方 SDK 自建 MCP Server',
  },
  {
    group: '运维实战',
    title: 'Agent 运维实战',
    link: '/guide/aiops-agent-practice',
    sub: '日志分析、告警归因、故障诊断、自动生成 Runbook、人机协同（human-in-the-loop）安全边界、Dify/n8n/LangGraph 端到端编排',
  },
  {
    group: 'RAG 与知识库',
    title: '运维知识库与 RAG',
    link: '/guide/aiops-rag',
    sub: '幻觉与私有知识、文档切分、Embedding 与向量库选型、混合检索与重排、把本知识库接入 LLM、Ollama 私有化方案',
  },
  {
    group: '传统 AIOps',
    title: '传统 AIOps 与机器学习',
    link: '/guide/aiops-ml',
    sub: '时序异常检测（3-sigma/EWMA/Prophet/孤立森林）、告警降噪聚合关联、Drain 日志模板、根因定位、传统 ML 与 LLM Agent 的分工',
  },
]

export default articles
