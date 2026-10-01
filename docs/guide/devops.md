# DevOps 与平台工程

> 本页聚合 **平台工程与内部开发者平台、CI/CD 与渐进式交付、统一制品库、软件供应链安全（DevSecOps）、密钥与证书管理、FinOps 云成本治理**，目标是把"从代码提交到安全、稳定、可观测地跑在生产"这条链路平台化、自动化、可复制。

## 文章索引

### 平台工程

::: idx

| 文章 | 解决什么问题 | 状态 |
|---|---|---|
| [平台工程与内部开发者平台（IDP）](./devops-platform-engineering) | DevOps 落地困境、IDP 能力分层、Backstage、黄金路径 Golden Path、DevEx、平台团队拓扑 | ✅ 已完成 |

:::

### CI/CD 与交付

::: idx

| 文章 | 解决什么问题 | 状态 |
|---|---|---|
| [CI/CD 进阶与渐进式交付](./devops-cicd-advanced) | GitHub Actions / GitLab CI 深化、分支策略、蓝绿/金丝雀/滚动、Feature Flag、Argo Rollouts / Flagger | ✅ 已完成 |

:::

### 制品管理

::: idx

| 文章 | 解决什么问题 | 状态 |
|---|---|---|
| [制品库 Harbor 与 Nexus](./devops-artifacts) | 统一镜像/制品仓库、Harbor 扫描与复制、Nexus 多格式仓库、制品晋升 promotion、容量与备份 | ✅ 已完成 |

:::

### 安全与供应链

::: idx

| 文章 | 解决什么问题 | 状态 |
|---|---|---|
| [DevSecOps 与软件供应链安全](./devops-devsecops) | 安全左移、SAST/DAST/SCA、Trivy 扫描、Syft SBOM、Cosign 签名、OPA/Kyverno 准入、SLSA | ✅ 已完成 |

:::

### 密钥与成本

::: idx

| 文章 | 解决什么问题 | 状态 |
|---|---|---|
| [密钥与证书管理](./devops-secrets) | Vault 动态密钥与 PKI、Sealed Secrets、External Secrets Operator、cert-manager 自动证书、密钥轮换 | ✅ 已完成 |
| [FinOps 云成本治理](./devops-finops) | FinOps 三阶段、成本标签与分摊、OpenCost/Kubecost、right-sizing、Spot/预留实例、成本告警 | ✅ 已完成 |

:::

## 命令速查

- Git 分支、变基、标签、协作工作流：[Git 命令与协作工作流速查](/reference/git-commands)
- 云原生（Helm / 准入 / 扫描 / 交付）排障命令：[云原生排障命令速查](/reference/cloudnative-commands)
- 已有自动化链路：[Jenkins 与 Git](./automation-jenkins)、[GitOps（ArgoCD）](./automation-gitops)、[Terraform](./automation-terraform)
