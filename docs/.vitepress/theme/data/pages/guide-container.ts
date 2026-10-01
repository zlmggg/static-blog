import type { Article } from '../types'

const articles: Article[] = [
  {
    group: 'Docker',
    title: 'Docker 实战手册',
    link: '/guide/container-docker',
    sub: '原理、镜像构建/Harbor、存储、网络、Compose 深入'
  },
  {
    group: 'Kubernetes（K8s 系列）',
    title: 'K8s 01：架构与集群部署',
    link: '/guide/container-k8s-01-architecture-cluster',
    sub: '架构、高可用集群安装'
  },
  {
    group: 'Kubernetes（K8s 系列）',
    title: 'K8s 02：Pod 管理与服务发现',
    link: '/guide/container-k8s-02-pod-service-discovery',
    sub: 'Pod/工作负载、Service'
  },
  {
    group: 'Kubernetes（K8s 系列）',
    title: 'K8s 03：存储与 Ingress',
    link: '/guide/container-k8s-03-storage-ingress',
    sub: 'PV/PVC、ConfigMap/Secret、Ingress'
  },
  {
    group: 'Kubernetes（K8s 系列）',
    title: 'K8s 04：有状态服务与安全',
    link: '/guide/container-k8s-04-statefulset-security',
    sub: 'StatefulSet、RBAC、调度、HPA'
  },
  {
    group: 'Kubernetes（K8s 系列）',
    title: 'K8s 05：附录 SOP/FAQ/命令',
    link: '/guide/container-k8s-05-appendix-sop-commands',
    sub: '运维 SOP、常见问题、命令速查'
  },
  {
    group: '服务网格与可观测',
    title: '服务网格',
    link: '/guide/container-servicemesh',
    sub: 'Istio 流量管理、SkyWalking 链路追踪、可观测性'
  },
  {
    group: '大模型部署',
    title: '大模型部署',
    link: '/guide/container-llm',
    sub: '模型格式、vLLM/Ollama、量化、API 服务'
  },
  {
    group: '云原生进阶',
    title: 'Helm 与 Kustomize',
    link: '/guide/container-helm',
    sub: 'Chart/Repository/Release、模板与依赖、Kustomize 覆盖'
  },
  {
    group: '云原生进阶',
    title: 'Operator 与 Gateway API',
    link: '/guide/container-operator',
    sub: 'CRD/Controller 模式、Operator SDK/Kubebuilder、Gateway API'
  }
]

export default articles
