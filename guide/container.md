# 容器与编排

> 本页聚合 **容器化、容器编排、服务网格和大模型部署**。这是当前运维最核心、最"值钱"的方向。

## 文章索引

### Docker

::: idx

| 文章 | 解决什么问题 | 状态 |
|---|---|---|
| [Docker 实战手册](./container-docker) | 原理、镜像构建/Harbor、存储、网络、Compose 深入 | ✅ 已完成 |

:::

### Kubernetes（K8s 系列）

::: idx

| 文章 | 解决什么问题 | 状态 |
|---|---|---|
| [K8s 01：架构与集群部署](./container-k8s-01-architecture-cluster) | 架构、高可用集群安装 | ✅ 已完成 |
| [K8s 02：Pod 管理与服务发现](./container-k8s-02-pod-service-discovery) | Pod/工作负载、Service | ✅ 已完成 |
| [K8s 03：存储与 Ingress](./container-k8s-03-storage-ingress) | PV/PVC、ConfigMap/Secret、Ingress | ✅ 已完成 |
| [K8s 04：有状态服务与安全](./container-k8s-04-statefulset-security) | StatefulSet、RBAC、调度、HPA | ✅ 已完成 |
| [K8s 05：附录 SOP/FAQ/命令](./container-k8s-05-appendix-sop-commands) | 运维 SOP、常见问题、命令速查 | ✅ 已完成 |

:::

### 服务网格与可观测

::: idx

| 文章 | 解决什么问题 | 状态 |
|---|---|---|
| [服务网格](./container-servicemesh) | Istio 流量管理、SkyWalking 链路追踪、可观测性 | ✅ 已完成 |

:::

### 大模型部署

::: idx

| 文章 | 解决什么问题 | 状态 |
|---|---|---|
| [大模型部署](./container-llm.md) | 模型格式、vLLM/Ollama、量化、API 服务 | ✅ 已完成 |

:::

### 云原生进阶

::: idx

| 文章 | 解决什么问题 | 状态 |
|---|---|---|
| [Helm 与 Kustomize](./container-helm) | Chart/Repository/Release、模板与依赖、Kustomize 覆盖 | ✅ 已完成 |
| [Operator 与 Gateway API](./container-operator) | CRD/Controller 模式、Operator SDK/Kubebuilder、Gateway API | ✅ 已完成 |

:::

## 命令速查

- [Docker 命令速查](/reference/docker-commands)
- [kubectl 命令速查](/reference/kubectl-commands)
