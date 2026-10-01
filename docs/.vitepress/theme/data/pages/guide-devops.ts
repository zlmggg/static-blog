import type { Article } from '../types'

const articles: Article[] = [
  {
    group: '平台工程',
    title: '平台工程与内部开发者平台（IDP）',
    link: '/guide/devops-platform-engineering',
    sub: 'DevOps 落地困境、IDP 能力分层、Backstage、黄金路径 Golden Path、DevEx、平台团队拓扑',
  },
  {
    group: 'CI/CD 与交付',
    title: 'CI/CD 进阶与渐进式交付',
    link: '/guide/devops-cicd-advanced',
    sub: 'GitHub Actions / GitLab CI 深化、分支策略、蓝绿/金丝雀/滚动、Feature Flag、Argo Rollouts / Flagger',
  },
  {
    group: '制品管理',
    title: '制品库 Harbor 与 Nexus',
    link: '/guide/devops-artifacts',
    sub: '统一镜像/制品仓库、Harbor 扫描与复制、Nexus 多格式仓库、制品晋升 promotion、容量与备份',
  },
  {
    group: '安全与供应链',
    title: 'DevSecOps 与软件供应链安全',
    link: '/guide/devops-devsecops',
    sub: '安全左移、SAST/DAST/SCA、Trivy 扫描、Syft SBOM、Cosign 签名、OPA/Kyverno 准入、SLSA',
  },
  {
    group: '密钥与成本',
    title: '密钥与证书管理',
    link: '/guide/devops-secrets',
    sub: 'Vault 动态密钥与 PKI、Sealed Secrets、External Secrets Operator、cert-manager 自动证书、密钥轮换',
  },
  {
    group: '密钥与成本',
    title: 'FinOps 云成本治理',
    link: '/guide/devops-finops',
    sub: 'FinOps 三阶段、成本标签与分摊、OpenCost/Kubecost、right-sizing、Spot/预留实例、成本告警',
  },
]

export default articles
