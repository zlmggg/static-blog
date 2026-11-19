---
category: DevOps
difficulty: 高级
description: "你已经会写'push 了就跑个脚本'的流水线，但想搞懂 GitHub Actions / GitLab CI 怎么写得专业、安全、可复用，以及怎么把发布从'一把全量替换'升级到蓝绿 / 金丝雀 / 自动回滚。"
---

# CI/CD 进阶与渐进式交付

::: tip 本篇定位
你已经会写"push 了就跑个脚本"的流水线，但想搞懂 **GitHub Actions / GitLab CI 怎么写得专业、安全、可复用**，以及怎么把发布从"一把全量替换"升级到**蓝绿 / 金丝雀 / 自动回滚**。适合已经搭过 Jenkins/GitLab CI、想往企业级流水线和渐进式交付演进的 SRE。
本篇版本：GitHub Actions（托管服务，随平台更新）、GitLab CI 17.x、Argo Rollouts v1.10.0、Flagger v1.44.0、Unleash v8.2.0（自托管需 PostgreSQL 15+）。所有版本以官网当前稳定版为准。
:::

## 一、背景与基础

### 1.1 小白类比：流水线即代码

CI/CD 流水线就像**工厂的自动传送带**：原料（代码）从一头进来，经过一道道工序（编译 → 测试 → 扫漏洞 → 打包镜像 → 部署），成品从另一头出去。**流水线即代码（Pipeline as Code）**就是把这条传送带怎么造写成 YAML **放进 Git**，和代码一起评审、版本化，改流水线提个 MR 就行，不用找管理员点界面。

| 方式 | 问题 | Pipeline as Code 的好处 |
|---|---|---|
| 界面点选配置 | 配置在服务器上，没法评审、没法 diff | 配置进 Git，可评审、可回滚、可复用 |
| 每个项目各写各的 | 标准不统一 | 抽成 reusable 模板，一处改处处生效 |

### 1.2 CI 与 CD 到底各管什么

| 阶段 | 全称 | 干什么 | 失败了会怎样 |
|---|---|---|---|
| CI（持续集成） | Continuous Integration | 合并代码后自动构建、跑测试、出制品 | 拦住坏代码，不进下游 |
| CD（持续交付） | Continuous Delivery | 制品自动部署到类生产环境，**手动点一下才上生产** | 生产保持随时可发布 |
| CD（持续部署） | Continuous Deployment | 合格后**全自动上生产**，无人值守 | 对自动化和回滚能力要求极高 |

## 二、GitHub Actions 深化

### 2.1 三层结构：workflow / job / step

```mermaid
flowchart TB
    WF["workflow 一个 .yml 文件<br>被什么事件触发"]
    WF --> J1["job 1 build<br>跑在一个 runner 上"]
    WF --> J2["job 2 test<br>可与 build 并行"]
    J1 --> S1["step 1 checkout"]
    J1 --> S2["step 2 编译"]
    J2 --> S3["step 3 跑单测"]
    J1 --> J3["job 3 deploy<br>needs: build 完成才跑"]
```

- **workflow / job / step**：workflow 是一个 `.github/workflows/*.yml`（定义触发事件与 job）；job 是跑在干净 VM 上的独立单元，多个默认并行；step 是 job 里的一条命令或一个 `uses:` action。

### 2.2 一个生产级 workflow 完整片段

```yaml
# .github/workflows/build-and-deploy.yml
name: build-and-deploy
# 触发：推 main、打 v* 标签、或对 main 发 PR
on:
  push: { branches: [main], tags: ["v*"] }
  pull_request: { branches: [main] }

# 关键：默认最小权限，整个 workflow 只读（要写权限的 job 单独放开）
permissions:
  contents: read

jobs:
  test:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4          # 缓存依赖，加速 CI
        with: { node-version: "22", cache: "npm" }
      - run: npm ci
      - run: npm run lint
      - run: npm run test:cov
  build:
    needs: test
    runs-on: ubuntu-24.04
    outputs: { image: ${{ steps.meta.outputs.image }} }
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3         # 凭据放 GitHub Secrets
        with:
          registry: harbor.example.com
          username: ${{ secrets.HARBOR_USER }}
          password: ${{ secrets.HARBOR_TOKEN }}
      - name: 生成镜像标签
        id: meta
        run: echo "image=harbor.example.com/team/order:${GITHUB_SHA::12}" >> "$GITHUB_OUTPUT"
      - uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.image }}
  deploy-prod:
    needs: build
    environment: production       # 绑定环境保护（手动审批 / 环境级 secret）
    runs-on: ubuntu-24.04
    if: startsWith(github.ref, 'refs/tags/v')   # 只有打 tag 才上生产
    steps:
      - uses: actions/checkout@v4
      - run: echo "部署 ${{ needs.build.outputs.image }} 到生产"
```

### 2.3 关键进阶点

| 主题 | 要点 | 示例 |
|---|---|---|
| **最小权限 permissions** | 别全仓库 `write-all`；默认 `contents: read`，发版 job 单独放开 | 见上面顶层 `permissions` |
| **缓存 + 并发** | 缓存 node_modules/.m2 提速；同分支新 push 取消旧 run | `cache: npm`；`concurrency.group: ci-${{ github.ref }}` |
| **environment + Secrets** | 生产部署绑 `environment: production` 配手动审批；敏感值放 Secrets 不写进 yml | `${{ secrets.XXX }}` |

### 2.4 Composite Action 与 Reusable Workflow

跨仓库复用流水线有两种方式，别用混：

| 方式 | 用途 | 特点 |
|---|---|---|
| **Composite Action** | 复用一段**步骤组合**（如"装 Go + 缓存 +  lint"） | 在同一个 job 里 `uses:` 进你的步骤 |
| **Reusable Workflow** | 复用一整套**完整 job 编排**（如"标准发布流程"） | 别的仓库 `uses: org/.github/.github/workflows/release.yml@v1` 调用 |

```yaml
# reusable workflow 被调用方写法（业务仓库里，固定版本别用 main）
jobs:
  call-release:
    uses: your-org/.github/workflows/reusable-release.yml@v1.5.0
    with: { image-name: order-service }
    secrets: inherit
```

::: warning 别用 @main 引用 reusable workflow
生产中引用 reusable workflow / 第三方 action 要**固定到具体 tag 或 commit SHA**（如 `@v1.5.0`），不要用 `@main`——上游被改了你不知道。这是供应链安全的基本要求。
:::

## 三、GitLab CI 深化

### 3.1 核心：`.gitlab-ci.yml` 的阶段与作业

GitLab CI 以 `stage` 为流水线阶段、`job` 为作业单元。先看一张图：

```mermaid
flowchart LR
    B["build_job<br>stage: build"] --> U["unit_test"]
    B --> S["scan"]
    U --> D["deploy_prod<br>stage: deploy"]
    S --> D
```

### 3.2 完整 `.gitlab-ci.yml`（含 include / rules / needs DAG）

```yaml
# 全局默认镜像与缓存
image: harbor.example.com/library/golang:1.23
default: { tags: [kubernetes] }
cache:
  key: "$CI_COMMIT_REF_SLUG"
  paths: [.go/pkg/mod/]

# include：抽公共配置，避免一个文件上千行
include:
  - local: "/ci/build-templates.yml"
  - remote: 'https://gitlab.com/your-org/cicd-templates/-/raw/main/security-scan.yml'

variables:
  REGISTRY: harbor.example.com/team/order

# needs 构建 DAG，不被 stage 顺序硬卡
unit_test:
  stage: test
  needs: []                       # 不依赖前置，尽早并行
  script: [go test ./... -cover]
build_image:
  stage: build
  image: harbor.example.com/library/kaniko-project/executor:v1.23.2
  script:
    - echo "{\"auth\":{\"auth\":\"$HARBOR_PULL\"}}" > /kaniko/.docker/config.json
    - /kaniko/executor --context . --dockerfile Dockerfile --destination $REGISTRY:$CI_COMMIT_SHORT_SHA
  only: [main, tags]
# rules：比 only/except 更灵活，可组合 &&/|| 与 changes
deploy_staging:
  stage: deploy
  script: [echo "部署到 staging"]
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
      when: always
    - if: '$CI_COMMIT_BRANCH =~ /^feature\//'
      when: manual              # feature 分支手动触发
    - when: never
deploy_production:
  stage: deploy
  script: [echo "生产只在打 tag 且手动审批后部署"]
  rules:
    - if: '$CI_COMMIT_TAG =~ /^v\d+\.\d+\.\d+$/'
      when: manual
      allow_failure: false
```

### 3.3 include / parent-child / rules / needs 速查

| 特性 | 干什么 | 什么时候用 |
|---|---|---|
| **include / parent-child** | 把 yml 拆出去复用；父流水线按改动模块触发多条子流水线 | 公共模板多仓库共享；monorepo 按服务拆分构建 |
| **needs（DAG）/ rules** | needs 声明 job 依赖跳过串行等待；rules 取代 only/except 灵活决定是否跑 | 让流水线更快、按环境分支定触发策略 |

## 四、分支策略：Trunk-based vs GitFlow

| 维度 | Trunk-based（主干开发） | GitFlow |
|---|---|---|
| 主分支 | 所有人频繁合到 `main`，短生命周期特性分支 | `main` + `develop` + `feature/release/hotfix` 多层分支 |
| 发布频率 | 高频、小批量、持续部署 | 周期性发版，release 分支冻结 |
| 配合手段 | 强依赖 Feature Flag + 自动化测试 | 分支纪律 + 手动切分支 |
| 复杂度 | 低（分支简单），但要求自动化测试和灰度很成熟 | 高（分支多、合并痛苦） |
| 适合 | 云原生、天天发版的互联网团队 | 有固定发版周期、桌面/企业软件 |

> 现代云原生主流是 **Trunk-based + Feature Flag + 渐进式发布**：代码天天合 main，没做完的功能用开关藏起来，发出去也能一键关。

## 五、发布策略对比

| 策略 | 怎么做 | 优点 | 缺点 | 适用 |
|---|---|---|---|---|
| **滚动 Rolling** | 新版本逐步替换旧 Pod（K8s 默认） | 简单、无额外资源 | 新旧版本短暂共存，出问题影响范围边滚动边扩大 | 大多数无状态服务默认 |
| **蓝绿 Blue-Green** | 起一套全新"绿"环境，验证后流量一次性切过去 | 切换快、回滚秒切 | 要双倍资源 | 重要、需要快速回滚的系统 |
| **金丝雀 Canary** | 先放 1%~5% 流量给新版，观察指标，逐步放大 | 风险最小，自动按指标回滚 | 需要流量治理 + 指标观测 | 核心服务、大版本升级 |

> 蓝绿是"两套环境整体切流量"；金丝雀是"同环境内按百分比逐步导流、指标恶化自动回滚"。

## 六、Feature Flag（特性开关）

### 6.1 小白类比

Feature Flag 就像**电灯开关**：代码已上线，但某功能默认"关灯"藏着；产品想灰度给某批用户，远程"开灯"即可，**不用重新发版**，出问题远程关灯秒回退。它解决三件事：① 未完成功能先合并主干（配合 Trunk-based）；② 灰度给特定用户/比例；③ 紧急 kill switch。

### 6.2 自托管 Unleash（v8.2.0）

Unleash 是开源特性开关平台。v8 起要求 **PostgreSQL 15+**。用 Docker Compose 起一个：

```yaml
# docker-compose.yml（自托管 Unleash v8，需 PostgreSQL 15+）
services:
  postgres:
    image: postgres:15-alpine
    environment: { POSTGRES_USER: unleash, POSTGRES_PASSWORD: change-me-strong, POSTGRES_DB: unleash }
  unleash:
    image: unleashorg/unleash-server:v8.2.0
    depends_on: [postgres]
    environment:
      DATABASE_HOST: postgres
      DATABASE_NAME: unleash
      DATABASE_USER: unleash
      DATABASE_PASSWORD: change-me-strong
    ports: ["4242:4242"]
```

应用里用 SDK 判定开关（伪代码）：

```java
// 业务代码里：开关开了才走新逻辑，否则老逻辑
if (unleash.isEnabled("checkout-v2", userContext)) {
    return newCheckoutService.pay(request);
} else {
    return legacyCheckoutService.pay(request);
}
```

## 七、渐进式交付：Argo Rollouts 与 Flagger

前面说的金丝雀，手动一步步调流量太麻烦。**渐进式交付控制器**自动做：先切 5% → 等几分钟看错误率/延迟 → 没问题再切 25%/50%/100%；**指标一旦恶化自动回滚**。

### 7.1 Argo Rollouts vs Flagger

| 维度 | Argo Rollouts | Flagger |
|---|---|---|
| 资源类型 | `Rollout` CRD 替代 Deployment | `Canary` CRD 包装已有 Deployment |
| 流量治理 | 需配合 Istio / NGINX / ALB Ingress | 原生支持 Istio、Linkerd、App Mesh、NGINX |
| 指标分析 | `AnalysisTemplate` 查 Prometheus | `MetricTemplate` + `CanaryAnalysis` |
| 适合谁 | 已经用 Argo CD 的团队 | 已经用 Flux / Service Mesh 的团队 |

### 7.2 Argo Rollouts 完整 Canary 清单（v1.10.0）

```yaml
# 1) AnalysisTemplate：定义"健康指标"（Prometheus 查询）
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata: { name: error-rate }
spec:
  metrics:
    - name: pod-error-rate
      interval: 30s
      successCondition: result[0] <= 0.02     # 错误率 <= 2% 才算健康
      failureLimit: 3
      provider:
        prometheus:
          address: http://prometheus.monitoring.svc:9090
          query: |
            sum(rate(http_requests_total{status=~"5..",service="order"}[2m]))
            / sum(rate(http_requests_total{service="order"}[2m]))
---
# 2) Rollout：用 CRD 替代 Deployment，定义金丝雀步骤
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata: { name: order }
spec:
  replicas: 10
  strategy:
    canary:
      canaryService: order-canary
      stableService: order-stable
      steps:
        - setWeight: 5                 # 先切 5% 流量给新版
        - pause: { duration: 5m }      # 观察 5 分钟
        - analysis: { templates: [{ templateName: error-rate }] }
        - setWeight: 25
        - pause: { duration: 10m }
        - analysis: { templates: [{ templateName: error-rate }] }
        - setWeight: 100               # 全量
  selector: { matchLabels: { app: order } }
  template:
    metadata: { labels: { app: order } }
    spec:
      containers:
        - name: order
          image: harbor.example.com/team/order:v1.4.0
```

```bash
# 安装 Argo Rollouts（固定 v1.10.0）
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/download/v1.10.0/install.yaml
kubectl argo rollouts get rollout order --watch     # 查看发布进度
kubectl argo rollouts abort rollout order           # 手动回滚
```

> 配合 Argo CD 做 GitOps：Argo CD 负责把期望状态写进集群，Rollouts 负责把新版本平滑推上去。

## 八、常见问题排错

| 现象 | 原因 | 解决 |
|---|---|---|
| Actions 里拉私有仓库 action 报 403 | token 权限不足 | 给 `GITHUB_TOKEN` 加 `contents: read`，或用 Fine-grained PAT |
| GitLab CI job 一直 pending | runner 没有匹配标签 | 检查 `tags:` 是否有对应 runner，或 runner 没上线 |
| 金丝雀卡住不继续 | `pause` 时间未到 / analysis 没通过 | `kubectl argo rollouts pause/resume`；查 Prometheus 查询是否报错 |
| Argo Rollouts 流量不切 | 没配 canary/stable Service 或缺流量网关 | 确认 service selector，并接入 Istio/NGINX 流量拆分 |

::: warning 生产红线
- 生产部署必须绑定 **environment 保护 + 手动审批**，禁止 main push 自动直上生产（除非你已有成熟的全自动回滚）。
- 引用第三方 Action / Reusable Workflow **固定到 tag 或 commit SHA**，不要跟 `@main`。
- 金丝雀**一定要配自动回滚指标**（错误率、延迟），否则"自动灰度"只是"自动放大事故"。
- 镜像 tag 固定具体版本，流水线里**禁止用 `latest`** 做部署标签。
- Feature Flag 是临时设施，上线稳定后要**及时清理死开关**，否则代码里全是 if/else 烂尾。
:::

## 相关速查

- 流水线里打的镜像推到哪：[制品库 Harbor 与 Nexus](#合并资料)
- 流水线里要插哪些安全检查：[DevSecOps 与软件供应链安全](#合并资料)
- GitOps 部署底座：[GitOps（ArgoCD）](#合并资料)、[Helm 包管理](/services/container/helm)
- 回滚与稳定性：[SLO 与错误预算](./monitor-slo)、[事故管理](./sre-incident)
- Git 分支操作：[Git 命令与协作工作流速查](/reference/git-commands)

### 官方文档

- GitHub Actions 文档：https://docs.github.com/actions
- 工作流权限与 reusable workflow：https://docs.github.com/actions/sharing-automations/reusing-workflows
- GitLab CI/CD 文档（含 needs DAG）：https://docs.gitlab.com/ci/
- Argo Rollouts 文档与 releases：https://argo-rollouts.readthedocs.io/ 、https://github.com/argoproj/argo-rollouts/releases
- Flagger 文档与 releases：https://docs.flagger.app/ 、https://github.com/fluxcd/flagger/releases
- Unleash 自托管文档与 releases：https://docs.getunleash.io/ 、https://github.com/Unleash/unleash/releases

<!-- merged-guide-material:start -->
## 合并资料

> 原先单独成页的同主题内容已收进本页；默认折叠，点开看原页全文。

<details>
<summary><strong>GitLab CI / ArgoCD — 掌握&#x27;代码一提交，自动构建镜像并自动部署到 Kubernetes&#x27;的整套流水线：GitLab CI 负责构建，ArgoCD 负责把 Git 里声明的配置自动同步到集群。</strong></summary>

::: tip 本篇定位
掌握"代码一提交，自动构建镜像并自动部署到 Kubernetes"的整套流水线：GitLab CI 负责构建，ArgoCD 负责把 Git 里声明的配置自动同步到集群。
本篇版本：GitLab CE 19.4.1（与 [Git/Jenkins 篇](#合并资料)一致）、ArgoCD v3.5.3、Kubernetes v1.30。
:::

#### 一、CI/CD 概念

##### 1.1 小白类比：什么是 CI/CD

你写了个网页应用，以前上线是这样的：本地 `mvn package` 打出 jar → scp 传到服务器 → SSH 上去停旧进程、启新进程。一旦多个人同时改代码、有多套环境（测试/预发/生产），就乱套了：谁传的包？传错版本了没？这次上线改了啥？

CI/CD 就是把"从代码改动到上线"这条路**自动化、标准化、留痕化**：

| 缩写 | 全称 | 通俗理解 | 对应谁干 |
|---|---|---|---|
| CI | Continuous Integration 持续集成 | 代码一提交，自动拉下来编译、跑测试，早发现冲突和错误 | GitLab CI / Jenkins |
| CD | Continuous Delivery 持续交付 | 测过的自动打好镜像、推到镜像仓库，随时可以一键发布 | GitLab CI |
| CD | Continuous Deployment 持续部署 | 更进一步：自动发布到生产，不用人点 | ArgoCD |

> 一句话：**CI 管"把代码变成制品"，CD 管"把制品送到环境里跑起来"。** 本篇前半段 GitLab CI 干 CI + 交付，后半段 ArgoCD 干持续部署。

##### 1.2 推送（Push）vs 拉取（Pull）两种部署模式

传统部署（Jenkins 篇那种）是 **Push 模式**：CI 服务器构建完，**主动 SSH / kubectl 推**到目标机器或集群。问题是：CI 服务器要握有所有环境的部署凭证，权限大、安全风险高。

**GitOps 是 Pull 模式**：不允许 CI 直接碰生产集群，而是让集群里的 ArgoCD **自己盯着 Git 仓库**，发现 Git 里的声明变了，就自己拉下来应用到集群。

```mermaid
flowchart LR
    Dev["开发 push 代码"] --> CI["GitLab CI<br>构建镜像+改 Git 清单"]
    CI --> Reg["镜像仓库"]
    CI --> Git["配置 Git 仓库<br>（声明目标状态）"]
    Git -. 定时/事件盯着 .-> Argo["ArgoCD<br>在集群里"]
    Argo --> K8s["Kubernetes 集群<br>按声明同步"]
    style Git fill:#e8f5e9
    style Argo fill:#e3f2fd
```

##### 1.3 GitOps 三大原则

GitOps 这个词由 Weaveworks 提出，现在是 CNCF 生态里 Kubernetes 部署的事实标准。它有四条铁律（前三条最核心）：

1. **声明式（Declarative）**：整个系统"想要长成什么样"全部用 YAML 描述，存进 Git。不写命令式脚本。
2. **版本控制 + 唯一真实来源（Git as Single Source of Truth）**：集群应该长什么样，以 Git 里的内容为准。要改配置？改 Git，别直接 `kubectl edit` 线上改。
3. **自动调谐（Automated Reconciliation）**：一个 Agent（ArgoCD）持续对比"Git 里声明的状态"和"集群实际状态"，不一致就自动修正（调谐/reconcile）。有人手动在集群里乱改，它会给你改回去。
4. **Agent 软件化**：负责拉取和部署的是经过充分测试的 Agent，而不是临时脚本。

> 类比：GitOps 像"按菜谱做菜"——菜谱（Git）是唯一标准，ArgoCD 是个厨师，每天对照菜谱看菜做对了没，做错了就照着菜谱重做一遍。你想换菜？改菜谱，别冲进厨房直接抢锅。

**为什么用 GitOps**：所有变更都有 Git 提交记录可审计；回滚就是 `git revert`；集群挂了能照着 Git 重建；CI 不用持有生产凭证，安全边界清晰。

#### 二、GitLab CI

##### 2.1 核心概念：`.gitlab-ci.yml`、Runner、Pipeline

GitLab CI 的配置全部写在仓库根目录的 `.gitlab-ci.yml` 里。你 push 代码后，GitLab 会：

1. 触发一条 **Pipeline（流水线）**；
2. Pipeline 按 **Stage（阶段）** 顺序执行若干 **Job（任务）**；
3. 每个 Job 丢给某个 **Runner（执行者，一台装了 gitlab-runner 的机器）** 跑在容器里。

| 概念 | 通俗理解 |
|---|---|
| `stages` | 阶段，如 build → test → deploy，按顺序跑 |
| `stage` | 某个 job 属于哪个阶段 |
| `job` | 具体一条任务，在 Runner 上执行脚本 |
| `image` | job 用哪个容器镜像当执行环境 |
| `tags` | 标签，把 job 调度到带对应标签的 Runner |
| `variables` | 流水线变量（镜像名、tag 等） |
| `artifacts` | job 之间传递产物 |
| `only`/`rules` | 什么分支/条件下才跑这个 job |

> Runner 要单独装并注册到 GitLab（`gitlab-runner register`），一般用 shell 或 docker executor。本篇假设已有一个能跑 docker 的 Runner（dind 或装了 docker 的 shell runner）。

##### 2.2 完整 `.gitlab-ci.yml` 示例

下面是一个 Go/Java 都行的通用模板：**构建镜像 → 推到私有镜像仓库 → 更新配置仓库里的镜像 tag（触发 ArgoCD）**。

```yaml
# 项目根目录 .gitlab-ci.yml
stages:
  - build          # 编译/测试
  - image          # 构建并推送镜像
  - deploy         # 更新配置仓库（触发 ArgoCD 同步）

variables:
  APP_NAME: demo-api
  # 私有镜像仓库地址（在 GitLab Settings → CI/CD → Variables 里配密码更安全）
  REGISTRY: registry.example.com/k8s-apps
  # CI_COMMIT_SHORT_SHA 是 GitLab 内置变量：本次提交短 hash，用作镜像 tag
  IMAGE: "$REGISTRY/$APP_NAME:$CI_COMMIT_SHORT_SHA"

# 全局：只在 main 分支跑部署类 job
workflow:
  rules:
    - if: '$CI_PIPELINE_SOURCE == "push"'

# 阶段一：构建与测试
build:
  stage: build
  image: maven:3.9-eclipse-temurin-21
  tags:
    - docker
  script:
    - mvn -B clean test
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'

# 阶段二：构建 Docker 镜像并推送
docker-image:
  stage: image
  image: docker:27.3.1          # 固定版本，不用 latest
  tags:
    - docker
  services:
    - docker:27.3.1-dind         # DinD：在容器里再起一个 docker 守护进程
  variables:
    DOCKER_TLS_CERTDIR: ""
  script:
    - echo "登录镜像仓库"
    - echo "$REGISTRY_PASSWORD" | docker login registry.example.com -u "$REGISTRY_USER" --password-stdin
    - echo "构建镜像 $IMAGE"
    - docker build -t "$IMAGE" .
    - docker push "$IMAGE"
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'

# 阶段三：把新镜像 tag 写进配置仓库（GitOps 的关键一步）
update-manifest:
  stage: deploy
  image: alpine:3.20
  tags:
    - docker
  before_script:
    - apk add --no-cache git curl
  script:
    - git config --global user.email "ci-bot@example.com"
    - git config --global user.name "ci-bot"
    # 克隆配置仓库（ArgoCD 盯着的那个仓库）
    - git clone https://ci-bot:$GITOPS_TOKEN@gitlab.example.com/k8s/manifests.git
    - cd manifests
    # 用 sed 把 deployment.yaml 里的镜像 tag 换成本次提交 hash
    - sed -i "s|image: registry.example.com/k8s-apps/demo-api:.*|image: registry.example.com/k8s-apps/demo-api:$CI_COMMIT_SHORT_SHA|" deploy/demo-api/deployment.yaml
    - git add deploy/demo-api/deployment.yaml
    - git commit -m "chore: bump demo-api to $CI_COMMIT_SHORT_SHA" || echo "无变化"
    - git push origin main
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
```

要点说明：

- **镜像 tag 用 `$CI_COMMIT_SHORT_SHA`**，不用 `latest`——每次构建有唯一、可追溯的 tag，回滚时知道回退到哪个 hash。
- `REGISTRY_USER`、`REGISTRY_PASSWORD`、`GITOPS_TOKEN` 这些敏感值配在 GitLab 项目 **Settings → CI/CD → Variables** 里，勾选 Masked，不要写进 yml。
- 阶段三**不直接 `kubectl apply`**，而是改配置仓库的 YAML。真正让集群生效的是 ArgoCD。

> 如果项目是前端/其他语言，把 `build` 阶段的镜像和命令换成对应工具（如 `node:22`、`npm ci && npm run build`）即可，`image` 和 `deploy` 两个阶段结构不变。

##### 2.3 看流水线结果

push 后在 GitLab 项目左侧 **Build → Pipelines** 看：三个阶段依次变绿。失败点在哪一眼定位，可从失败阶段重试。

#### 三、ArgoCD 简介

##### 3.1 它是什么

ArgoCD 是一个装在 Kubernetes 集群里的 **GitOps 持续部署控制器**（CNCF 毕业项目）。它本身是一组 Kubernetes 资源，核心干一件事：**盯着一个 Git 仓库，把里面描述的 K8s 资源，自动创建/更新到当前集群，并持续保证"集群现状 == Git 声明"。**

```mermaid
flowchart TD
    subgraph Cluster["Kubernetes 集群"]
        API["ArgoCD API Server<br>Web UI / CLI"]
        Repo["Repo Server<br>解析 Git/Helm/Kustomize"]
        AppCtrl["Application Controller<br>持续调谐"]
    end
    Git[("Git 仓库<br>manifests")] --> Repo
    Repo --> AppCtrl
    AppCtrl --> K8sAPI["Kubernetes API"]
    K8sAPI --> Workload["Deployment/Service/..."]
    API --> Repo
    API --> AppCtrl
```

- **Application Controller**：核心，每 3 分钟（可配）对比 Git 与集群，发现漂移就同步。
- **Repo Server**：把 Git 里的 YAML/Helm/Kustomize 渲染成最终的 K8s 资源。
- **API Server**：提供 Web UI 和 `argocd` 命令行。

##### 3.2 为什么是 Pull 而不是 Push

回到第一节那个对比：

| 对比 | Push（Jenkins 直连 kubectl） | Pull（ArgoCD / GitOps） |
|---|---|---|
| 谁发起部署 | CI 服务器主动推 | 集群内 ArgoCD 主动拉 |
| 生产凭证 | CI 要握生产 kubeconfig，权限极大 | CI 只改 Git，生产 kubeconfig 在集群内 |
| 状态可见性 | 部署完就完了，漂移难发现 | ArgoCD 持续盯着，漂移自动修正 |
| 审计 | 看 CI 日志 | 每一次变更都是一次 Git commit |
| 回滚 | 重新跑流水线 | `git revert` 再 push |

#### 四、ArgoCD 使用

##### 4.1 安装 ArgoCD（v3.5.3）

需要一个可用的 Kubernetes 集群（本篇按 v1.30）和 kubectl：

```bash
# ① 建命名空间
kubectl create namespace argocd

# ② 用官方清单安装（固定版本 v3.5.3）
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/v3.5.3/manifests/install.yaml

# ③ 看 Pod 是否起来（首次拉镜像要等几分钟）
kubectl get pods -n argocd -w
```

预期：

```text
NAME                                                READY   STATUS
argocd-application-controller-0                     1/1     Running
argocd-applicationset-controller-xxxx               1/1     Running
argocd-repo-server-xxxxx                            1/1     Running
argocd-server-xxxxx                                  1/1     Running
```

默认 `argocd-server` 只监听 ClusterIP。实验环境用 `kubectl port-forward` 暴露 Web UI：

```bash
kubectl -n argocd port-forward svc/argocd-server 8080:443
# 浏览器打开 https://localhost:8080 ，首次会提示证书不安全，跳过即可
```

登录：用户名 `admin`，初始密码是一个 Secret 里的随机串：

```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d; echo
# 把输出的密码粘进 Web UI 登录，登录后立刻改密码
```

##### 4.2 定义一个 Application（声明式清单）

ArgoCD 里每个"要管的应用"是一个 `Application` 资源。下面这个清单说清楚三件事：**去哪找 Git、把里面的东西部署到哪个集群、叫什么名字**。

```yaml
# app-demo-api.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: demo-api
  namespace: argocd
spec:
  project: default
  source:
    # GitOps 配置仓库地址（就是 CI 最后 push 的那个仓库）
    repoURL: https://gitlab.example.com/k8s/manifests.git
    targetRevision: main          # 跟踪哪个分支
    path: deploy/demo-api         # 仓库里这个应用的 YAML 所在目录
  destination:
    server: https://kubernetes.default.svc   # 部署到 ArgoCD 所在集群
    namespace: demo
  syncPolicy:
    automated:                    # 自动同步：Git 一变就自动部署
      prune: true                 # Git 里删了的资源，集群里也删
      selfHeal: true              # 集群里被人手动改了，自动改回 Git 声明
    syncOptions:
      - CreateNamespace=true      # 目标 namespace 不存在就自动建
```

应用它：

```bash
kubectl apply -f app-demo-api.yaml

# 查看应用状态
kubectl get applications -n argocd
# NAME       SYNC STATUS   HEALTH STATUS
# demo-api   Synced        Healthy
```

在 Web UI 里也能看到：绿色 Synced + Healthy 表示 Git 与集群一致、应用健康。

##### 4.3 配置仓库里长什么样

`manifests` 仓库（CI 在改的那个）结构很简单：

```text
manifests/
└── deploy/
    └── demo-api/
        ├── deployment.yaml
        └── service.yaml
```

`deployment.yaml`（注意 image tag 会被 CI 的 sed 改掉）：

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: demo-api
  namespace: demo
spec:
  replicas: 2
  selector:
    matchLabels: { app: demo-api }
  template:
    metadata: { labels: { app: demo-api } }
    spec:
      containers:
        - name: demo-api
          image: registry.example.com/k8s-apps/demo-api:9f3c2a1   # ← CI 改成新 commit
          ports:
            - containerPort: 8080
          resources:
            requests: { cpu: "100m", memory: "128Mi" }
            limits:   { cpu: "500m", memory: "512Mi" }
---
apiVersion: v1
kind: Service
metadata:
  name: demo-api
  namespace: demo
spec:
  selector: { app: demo-api }
  ports:
    - port: 80
      targetPort: 8080
```

##### 4.4 手动同步与回滚

- **手动同步**：Web UI 上点 **SYNC**，或命令行 `argocd app sync demo-api`。关掉 `automated` 后就是手动模式，适合变更需要人审批的环境。
- **回滚**：在 Web UI 的 **APP HISTORY AND ROLLBACK** 里选上一个版本点 Rollback；或命令行：

```bash
argocd app history demo-api          # 看同步历史
argocd app rollback demo-api 1       # 回滚到编号 1 那次
```

::: warning 自动同步下的回滚
如果开了 `automated`，ArgoCD 会盯着 Git。**直接 `argocd app rollback` 后，它发现集群和 Git 又不一致，会再被调谐回去。** 所以 GitOps 的正确回滚姿势是：

```bash
# 在 manifests 仓库里把 image tag 改回旧版本号，再 push
git revert <那次 bump 的 commit>
git push
# ArgoCD 检测到 Git 变化，自动同步回旧版本
```
:::

#### 五、落地建议

##### 5.1 完整工作流串起来

把第二、四节拼起来，一次"提交代码 → 线上生效"是这样的：

```mermaid
flowchart TD
    A["开发在业务仓库<br>git push origin main"] --> B["GitLab CI 触发流水线"]
    B --> C["build：跑单元测试"]
    C --> D["image：docker build & push<br>tag=commit-sha"]
    D --> E["deploy：sed 改 manifests 仓库的 image tag<br>git commit & push"]
    E --> F["ArgoCD 监听到 manifests 仓库变更"]
    F --> G["自动 kubectl apply 新 Deployment"]
    G --> H["滚动更新完成<br>Healthy"]
    H --> I{"线上有问题?"}
    I -- 是 --> J["git revert 那次 commit<br>push，ArgoCD 自动回滚"]
```

##### 5.2 多环境管理

测试、预发、生产三套环境，最常见两种做法：

- **分支隔离**：`manifests` 仓库用 `dev` / `staging` / `main` 三个分支，ArgoCD 里每个 Application 的 `targetRevision` 指不同分支。合并到 main 才上生产。
- **目录隔离（推荐）**：单分支 `main`，目录按环境分：`deploy/overlays/dev/`、`overlays/staging/`、`overlays/prod/`（配 Kustomize overlay，dev 用 1 副本、prod 用 3 副本）。Application 各指一个 path。

| 环境 | 副本数 | 同步策略 |
|---|---|---|
| dev | 1 | automated 自动同步 |
| staging | 2 | automated，接生产前演练 |
| prod | 3 | 手动 SYNC，要人确认后发布 |

生产环境建议把 `automated` 关掉，改成"CI 改完 Git，人在 ArgoCD UI 点一下同步"，保留最后一道人工闸门。

##### 5.3 选型建议

- **纯虚拟机/物理机部署**：用 Ansible（见 [Ansible 篇](/services/cicd/ansible)），别硬上 ArgoCD。
- **已经用 Kubernetes、服务数量多**：上 GitOps（ArgoCD），比 Jenkins 直连集群安全、可审计。
- **过渡期**：Jenkins/GitLab CI 负责 CI（编译、测试、构建镜像），部署给 ArgoCD——这也是本篇推荐的分工，CI 不碰生产集群凭证。

#### 六、注意事项与排错

| 现象 | 原因 | 处理 |
|---|---|---|
| Application 一直 `OutOfSync` | 集群现状和 Git 有差异 | 点 SYNC；或有人手动改了资源，确认后让 ArgoCD 对齐 |
| `Synced` 但 `Degraded`/`Missing` | 资源在 K8s 里创建失败 | `kubectl describe` 看事件，多半是镜像拉不下来/配置错 |
| 镜像拉不下来 `ImagePullBackOff` | 私有仓库没配 imagePullSecret | 在目标 namespace 建 `kubectl create secret docker-registry` |
| ArgoCD 拉不到私有 Git 仓库 | 仓库私有，没配凭证 | ArgoCD 里 `argocd repo add` 配用户名/Token |
| CI push 了但 ArgoCD 没反应 | 自动同步间隔或 webhook 没配 | 手动 SYNC 验证；生产建议配 GitLab webhook 事件触发 |
| dind 构建报 `Cannot connect to the Docker daemon` | 没开 dind service 或 TLS 问题 | 确认 `services: docker:dind` 与 `DOCKER_TLS_CERTDIR: ""` |

::: warning 生产红线
- ArgoCD 开了 `selfHeal: true` 后，**禁止再直接 `kubectl edit` 改线上资源**——会被自动改回。要改就改 Git。
- 私有镜像仓库凭证、GitLab Token 一律放 CI/CD Variables（Masked），不要硬编码进 `.gitlab-ci.yml` 或 Application 清单。
- 生产发布保留人工确认（关掉 automated 或加审批），别让每个 push 直接上生产。
:::

#### 相关速查

- [kubectl 命令速查](/reference/kubectl-commands)
- Git / GitLab / Jenkins 基础与 CI：[Git / GitLab / Jenkins 持续集成](#合并资料)
- 批量主机配置（非 K8s 环境）：[Ansible 运维自动化](/services/cicd/ansible)

##### 官方文档

- GitLab CI/CD 文档：https://docs.gitlab.com/ci/
- `.gitlab-ci.yml` 关键字参考：https://docs.gitlab.com/ci/yaml/
- ArgoCD 官方文档：https://argo-cd.readthedocs.io/
- ArgoCD 安装清单（选版本）：https://github.com/argoproj/argo-cd/releases
- ArgoCD Application 清单说明：https://argo-cd.readthedocs.io/en/stable/core_concepts/

</details>

<details>
<summary><strong>Git / GitLab / Jenkins 持续集成实战 — 掌握版本控制 Git、私有代码托管 GitLab，并用 Jenkins 实现从代码提交到自动构建、打包、部署的持续集成（CI/CD）。本篇版本：GitLab CE 19.4.1、Jenkins LTS 2.568.3。</strong></summary>

::: tip 本篇定位
掌握版本控制 Git、私有代码托管 GitLab，并用 Jenkins 实现从代码提交到自动构建、打包、部署的持续集成（CI/CD）。本篇版本：GitLab CE 19.4.1、Jenkins LTS 2.568.3。
:::

#### 一、Git 版本控制

##### 1.1 Git 是什么

Git 是分布式版本控制系统，记录文件的修改历史，支持回退、分支、多人协作。与集中式版本库不同，每个开发者本地都有完整的版本库，可离线提交，再与远程同步。

##### 1.2 三个工作区域

Git 文件在三个区域间流转，这是理解所有 Git 命令的基础：

- **工作区（Working Directory）**：你实际看到、正在编辑的文件；
- **暂存区（Stage/Index）**：`git add` 后、改动被临时存放的地方，对应 `.git/index`；
- **版本库（Repository）**：`git commit` 后，暂存区的改动被永久记录到版本库，对应 `.git` 目录。

![Git 三区流转：工作区经 git add 到暂存区，再经 git commit 到版本库，版本库经 push 到远程，远程经 pull 或 clone 回到工作区](/diagrams/jenkins-01.svg)

##### 1.3 初始配置与建库

安装并配置提交者信息（每次提交都会记录，Windows 提交前必须先配置）：

```bash
apt install -y git
git config --global user.name "你的名字"
git config --global user.email "你的邮箱"
git config --global init.defaultBranch main   # 新仓库默认分支用 main
git config --global --list                     # 查看全局配置
```

配置作用域：`--global` 对当前用户生效（保存在 `~/.gitconfig`），`--system` 对所有用户（`/etc/gitconfig`），默认 `--local` 只对当前仓库（`.git/config`）。

在现有目录建库，或克隆远程库：

```bash
git init                 # 当前目录初始化为 Git 仓库
git init --bare repo.git # 裸仓库（无工作区），专门充当远程仓库
git clone <仓库URL>      # 克隆远程仓库到本地
```

##### 1.4 日常命令

```bash
git status               # 查看当前状态（哪些改动未提交）
git add <文件>           # 添加到暂存区（. 表示全部）
git commit -m "说明"     # 提交到版本库
git diff                 # 工作区 vs 暂存区
git diff --staged        # 暂存区 vs 上次提交
git log --oneline --graph # 查看提交历史
git checkout -- <文件>   # 丢弃工作区改动（危险，不可恢复）
git restore <文件>       # 同上，新版写法
git reset --soft HEAD~1  # 撤销上次 commit（保留改动到暂存区）
git rm <文件>            # 同时从工作区和版本库删除
git mv 旧名 新名          # 改名
git stash                # 暂存当前未提交的改动，之后可恢复
```

##### 1.5 分支管理

分支让你在不影响主线的情况下并行开发：

```bash
git branch               # 列出本地分支
git branch <分支名>       # 创建分支
git switch <分支名>       # 切换分支（新版，旧写法 checkout）
git switch -c <分支名>    # 创建并切换
git merge <分支名>        # 把指定分支合并到当前分支
git branch -d <分支名>    # 删除已合并的分支
git branch -r            # 列出远程分支
```

经典的 **GitFlow** 分支模型用几类固定分支管理发布：`master`（生产）、`develop`（开发主线）、`feature/*`（功能分支，从 develop 拉出再合回）、`release/*`（发布准备，合回 master 和 develop）、`hotfix/*`（生产紧急修复，从 master 拉出、修复后合回 master 和 develop）。小团队也常采用更简单的主干开发。

##### 1.6 远程协作

```bash
git remote -v                       # 查看远程仓库
git remote add origin <URL>         # 关联远程仓库
git push -u origin main             # 首次推送并建立跟踪
git push origin <分支>              # 推送分支
git push origin --tags              # 推送标签
git fetch origin                    # 拉取远程更新但不自动合并
git pull origin main                # 拉取并合并（= fetch + merge）
```

`.gitignore` 文件用来声明不纳入版本库的文件（如 `node_modules/`、`*.log`、密钥文件）。

#### 二、GitLab 私有代码托管

##### 2.1 GitLab 与 Omnibus

GitLab 是基于 Web 的 Git 仓库管理平台，提供代码托管、评审、Issue、CI/CD 等功能。它组件众多（Web、后台任务、PostgreSQL、Redis、Gitaly 等），官方通过 **Omnibus GitLab** 安装包把所有组件打包在一起、用 Chef 自动编排，安装和升级都很方便。统一管理命令是 `gitlab-ctl`。

从 GitLab 12.1 起，官方 Linux 包只支持 PostgreSQL，不再支持 MySQL。

##### 2.2 硬件要求

GitLab 比较吃资源，官方建议生产内存 4 GB 以上、较新版本建议 8 GB 左右。小内存机器可用于实验但要加 swap、并调小并发。磁盘根据代码量和 CI 产物准备。

##### 2.3 安装 GitLab CE 19.4.1

以 Ubuntu 24.04（noble）为例，从清华镜像下载 Omnibus 包：

```bash
apt update && apt install -y curl openssh-server ca-certificates perl
cd /root
wget https://mirrors.tuna.tsinghua.edu.cn/gitlab-ce/ubuntu/pool/noble/main/g/gitlab-ce/gitlab-ce_19.4.1-ce.0_amd64.deb
apt install ./gitlab-ce_19.4.1-ce.0_amd64.deb -y
```

::: tip 版本号与镜像目录
上面是 19.4.1 的标准包名（`gitlab-ce_<版本>-ce.0_amd64.deb`）。若镜像里小版本已更新，可到 https://mirrors.tuna.tsinghua.edu.cn/gitlab-ce/ubuntu/pool/noble/main/g/gitlab-ce/ 目录里选需要的版本。RHEL/Rocky 用对应 yum 镜像目录下的 rpm 包，安装方式一致。
:::

##### 2.4 配置并初始化

编辑主配置文件 `/etc/gitlab/gitlab.rb`，设置访问地址（可用域名或 IP）：

```ruby
external_url 'http://gitlab.example.com'
# 可选：直接指定 root 初始密码（不指定则随机生成）
gitlab_rails['initial_root_password'] = '你的强密码'
```

执行重新配置，让 Omnibus 按配置初始化并启动所有服务（首次较慢）：

```bash
gitlab-ctl reconfigure
gitlab-ctl status
```

若没有在配置里指定 root 密码，随机密码保存在 `/etc/gitlab/initial_root_password`（该文件在首次 reconfigure 后约 24 小时自动删除，请及时查看保存）。

::: tip 常用命令
`gitlab-ctl reconfigure`（改完 gitlab.rb 后执行）、`gitlab-ctl restart|status`、`gitlab-ctl tail`（看日志）。改 external_url 后必须重新 reconfigure。
:::

##### 2.5 用户、组、项目与角色

- **用户**：管理员在管理区创建用户（邮箱不能重复），创建后可编辑用户、设置初始密码；
- **组（Group）**：一个组里可放多个项目，把开发者加入组并赋予角色，便于按团队批量管理；
- **项目（Project）**：代码仓库归属于个人或组，可选择初始化 README；
- **权限角色（组内 5 级）**：

| 角色 | 主要权限 |
|---|---|
| Guest | 只能提 Issue、发评论，不能读写代码库 |
| Reporter | 能克隆/查看代码，不能提交（适合 QA、产品） |
| Developer | 能克隆、开发、提交、推送非保护分支（普通开发） |
| Maintainer | 能管理项目、保护分支、合并到主干 |
| Owner | 组/项目最高权限，可改设置、管理成员 |

本地通过 HTTP 或 SSH 推拉代码，SSH 方式需在用户"个人设置 → SSH 密钥"里添加本机公钥。

#### 三、Jenkins 安装

##### 3.1 安装 Java

Jenkins LTS 2.568.3 需要 **Java 17 或 21**（Java 必须先于 Jenkins 安装；若后装 Java 需要重启系统）：

```bash
apt update
apt install -y openjdk-21-jdk
java -version
```

##### 3.2 添加 Jenkins 仓库并安装

以 Ubuntu 为例，使用清华镜像的 LTS 仓库（比官方源快）：

```bash
# 添加 Jenkins 仓库密钥
wget -q -O /usr/share/keyrings/jenkins-keyring.asc \
  https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key

# 添加清华 LTS 软件源
echo "deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] \
  https://mirrors.tuna.tsinghua.edu.cn/jenkins/debian-stable binary/" \
  > /etc/apt/sources.list.d/jenkins.list

apt update
apt install -y jenkins
systemctl enable --now jenkins
ss -tnlp | grep 8080
```

::: tip 也可以直接下载 deb
在 https://mirrors.tuna.tsinghua.edu.cn/jenkins/debian-stable/ 下载对应版本（如 jenkins_2.568.3_all.deb），用 `apt install ./jenkins_2.568.3_all.deb` 安装，效果相同。RHEL/Rocky 用对应 yum 源或 rpm。
:::

##### 3.3 初始化向导

浏览器访问 `http://服务器IP:8080`：

1. 查看初始管理员密码：

```bash
cat /var/lib/jenkins/secrets/initialAdminPassword
```

2. 粘贴密码进入；
3. 选择"安装推荐插件"（Install suggested plugins），等待安装；
4. 创建第一个管理员用户并保存；
5. 实例配置保持默认，进入 Jenkins 主界面。

##### 3.4 中文界面

在 **Manage Jenkins → Plugins（插件管理）** 搜索安装 `Localization: Chinese (Simplified)`，安装后重启即可显示中文；若部分仍为英文，可配合 `Locale` 插件在全局设置里把默认语言设为 `zh_CN`。

#### 四、自由风格任务

自由风格（Freestyle）项目通过界面配置一个构建任务，适合入门理解 CI 的各个环节。

##### 4.1 准备构建环境（JDK / Maven）

Java 项目需要构建工具，常用 Maven。两种方式：

- **自动安装（推荐新手）**：在 **Manage Jenkins → Tools（全局工具配置）** 里配置 JDK、Maven，勾选自动安装，Jenkins 会在首次构建时自动下载；
- **手动安装**：在服务器上装好并配置 Maven，国内建议改 Maven 镜像加速（编辑 `/etc/maven/settings.xml`，mirror 指向阿里云 Maven 源）。

##### 4.2 配置凭据

在 **Manage Jenkins → Credentials（凭据）** 添加，常用两类：

- **用户名/密码**：用于拉取 GitLab 私有仓库（填 GitLab 账号密码或访问令牌）；
- **SSH 密钥**：用于 Jenkins 免密登录目标部署机。可在服务器上以 jenkins 用户生成密钥并把公钥拷到目标机：

```bash
su - jenkins
ssh-keygen
ssh-copy-id root@目标机IP
```

##### 4.3 创建自由风格项目

新建 Item 选 Freestyle project，按构建环节配置：

1. **源码管理**：选 Git，填仓库 URL，选择凭据，指定分支（如 `*/main`）；
2. **构建触发器**：可先选手动，后续用 webhook（见第六节）；
3. **构建步骤**：如调用 Maven 执行 `clean package -Dmaven.test.skip=true` 打成 jar/war；
4. **构建后操作**：通过 "Publish over SSH" 或在构建步骤里用 SSH 把产物传到目标机、执行部署脚本（停旧进程、替换包、启动新进程）；
5. 可加 **邮件通知（E-mail Notification）**，构建失败时发送。

##### 4.4 构建脚本思路

部署脚本通常包含：备份旧版本 → 停止旧服务 → 替换新包 → 启动服务 → 健康检查。把脚本放在目标机，由 Jenkins 通过 SSH 调用，比把大量命令堆在 Jenkins 界面更清晰可复用。

#### 五、Pipeline 流水线

##### 5.1 声明式 Pipeline

Pipeline 用代码（Jenkinsfile）描述整个交付流程，可版本化、可可视化、可分阶段，是 Jenkins 的主流用法。声明式基本结构：

```groovy
pipeline {
  agent any
  tools {
    jdk 'jdk-21'
    maven 'maven-3.9'
  }
  environment {
    IMAGE = "registry.example.com/demo/myapp"
    TAG   = "${BUILD_NUMBER}"
  }
  stages {
    stage('拉取代码') {
      steps {
        git branch: 'main', credentialsId: 'gitlab-cred', url: 'http://gitlab.example.com/devops/myapp.git'
      }
    }
    stage('测试') {
      steps { sh 'mvn clean test' }
    }
    stage('打包') {
      steps { sh 'mvn -Dmaven.test.skip=true clean package' }
    }
    stage('构建镜像') {
      steps { sh 'docker build -t ${IMAGE}:${TAG} .' }
    }
    stage('推送镜像') {
      steps {
        withCredentials([usernamePassword(credentialsId: 'registry-cred',
          usernameVariable: 'REG_USER', passwordVariable: 'REG_PASS')]) {
          sh 'docker login -u ${REG_USER} -p ${REG_PASS} registry.example.com'
          sh 'docker push ${IMAGE}:${TAG}'
        }
      }
    }
    stage('部署') {
      steps {
        sh 'ssh root@目标机 "docker rm -f myapp; docker run -d --name myapp -p 80:8080 ${IMAGE}:${TAG}"'
      }
    }
  }
  post {
    success { echo '流水线成功' }
    failure { echo '流水线失败，请检查' }
  }
}
```

##### 5.2 Jenkinsfile 放哪里

- 新建 Pipeline 任务，在 Pipeline 定义里选 "Pipeline script from SCM"，指向代码库里的 `Jenkinsfile`，这样流水线和代码一起版本管理（推荐）；
- 也可直接在任务里写 Pipeline script 做快速测试。

##### 5.3 阶段视图

Pipeline 运行后，Jenkins 会展示各阶段（Stage View），每个阶段成功/失败一目了然，失败时可从失败的阶段定位问题并重试。

#### 六、实战：提交代码自动构建部署

把上面环节串起来，实现"开发者 push 代码 → Jenkins 自动构建部署"：

![CI/CD 全流程：开发者 push 到 GitLab，GitLab 经 Webhook 通知 Jenkins，Jenkins 拉取代码后依次编译测试、打包构建镜像、推送制品，再 SSH 部署到目标机并通知结果](/diagrams/jenkins-02.svg)

配置步骤：

1. Jenkins 安装 **GitLab 插件**（会带来 GitLab 触发器）；
2. 在 GitLab 管理区允许外发请求：**Admin Area → Settings → Network → Outbound requests**，勾选允许；
3. 在 Jenkins 自由风格/Pipeline 任务里开启 GitLab 触发器，生成并复制 Webhook URL 和 secret token；
4. 在 GitLab 对应项目的 **Settings → Webhooks** 里填入 Jenkins 的 URL，保存；
5. 用 "Test → Push events" 验证连通；
6. 之后修改代码并 `git commit && git push`，Jenkins 会自动触发整条流水线。

![声明式 Pipeline 各阶段：拉取代码、测试、打包、构建镜像、推送、部署依次进行](/diagrams/jenkins-03.svg)

#### 本章自测

1. Git 是集中式还是分布式？分布式体现在哪里？
2. 说清 Git 的工作区、暂存区、版本库，以及 add、commit、push 分别在哪些区域间流转。
3. git config 的 global/system/local 作用域分别保存在哪里？
4. git reset、git restore、git checkout 在撤销改动时有什么区别和风险？
5. git stash 有什么用？
6. 描述 GitFlow 分支模型中 master、develop、feature、release、hotfix 的关系。
7. git fetch 和 git pull 有什么区别？
8. .gitignore 的作用？
9. GitLab 的 Omnibus 安装方式解决了什么问题？统一管理命令是什么？
10. GitLab 为什么只支持 PostgreSQL？
11. GitLab 安装后 root 初始密码在哪里？为什么要尽快保存？
12. 改了 external_url 之后为什么要执行 reconfigure？
13. GitLab 的 Guest、Reporter、Developer、Maintainer、Owner 权限有什么区别？
14. Jenkins 对 Java 版本有什么要求？Java 应该什么时候装？
15. Jenkins 初始管理员密码在哪个文件？首次访问要做哪些初始化？
16. Jenkins 凭据里用户名密码和 SSH 密钥分别用于什么场景？
17. 自由风格任务从源码到部署一般配置哪几个环节？
18. 什么是声明式 Pipeline？相比自由风格有什么优势？
19. Jenkinsfile 为什么推荐放在代码库、从 SCM 读取？
20. Pipeline 的 post 块能做什么？
21. 如何实现"push 代码自动触发 Jenkins 构建"？GitLab 端要开启什么？
22. 简述 CI/CD 的含义，以及一条流水线通常包含哪些阶段。

#### 相关速查

- 命令速查：[Linux 命令速查](/reference/linux-commands)、[Docker 命令速查](/reference/docker-commands)、[kubectl 命令速查](/reference/kubectl-commands)
- 官方资源：
  - Git 官方文档：https://git-scm.com/doc
  - Git 常用命令（中文手册）：https://git-scm.com/book/zh/v2
  - GitLab 官网：https://about.gitlab.com/
  - GitLab 官方文档：https://docs.gitlab.com/
  - Omnibus GitLab：https://gitlab.com/gitlab-org/omnibus-gitlab
  - GitLab CE 清华镜像：https://mirrors.tuna.tsinghua.edu.cn/gitlab-ce/
  - Jenkins 官网：https://www.jenkins.io/
  - Jenkins 用户文档：https://www.jenkins.io/doc/
  - Jenkins LTS 更新日志：https://www.jenkins.io/changelog-stable/
  - Jenkins 清华镜像：https://mirrors.tuna.tsinghua.edu.cn/jenkins/
  - Pipeline 语法参考：https://www.jenkins.io/doc/book/pipeline/syntax/
  - 阿里云 Maven 镜像：https://developer.aliyun.com/mvn/guide

</details>

<details>
<summary><strong>制品库 Harbor 与 Nexus — CI 构建出的镜像、Jar、npm 包、Helm Chart 总得有个统一、可信、可管的地方存放和分发。这篇讲清楚为什么需要统一制品库、Harbor（容器镜像仓库）怎么玩、Nexus（多格式二进制仓库）怎么玩、制品怎么在流水线里晋升（promotion），以及容量和备份怎么搞。适合给团队搭私有制品中…</strong></summary>

::: tip 本篇定位
CI 构建出的镜像、Jar、npm 包、Helm Chart 总得有个**统一、可信、可管**的地方存放和分发。这篇讲清楚为什么需要统一制品库、**Harbor**（容器镜像仓库）怎么玩、**Nexus**（多格式二进制仓库）怎么玩、制品怎么在流水线里**晋升（promotion）**，以及容量和备份怎么搞。适合给团队搭私有制品中心的 SRE。
本篇版本：Harbor v2.15.5、Sonatype Nexus Repository 3.96.3（Community 版）。所有版本以官网当前稳定版为准。
:::

#### 一、背景与基础

##### 1.1 小白类比：制品库是公司的"中央物流仓 + 中转站"

流水线每次构建都会产出一个"成品"：Docker 镜像、Java 的 Jar、前端的 npm 包、Helm Chart。这些成品要有地方放，还要能被别的环境拉下来跑。

如果没有统一制品库，会发生什么？

- 每台机器各自从 Docker Hub / Maven Central 拉，**国内又慢又经常被限流**；
- 测试环境构建完镜像直接 `docker save | scp` 拷到生产，**没法追溯、没法复用**；
- 谁能推镜像、哪个版本上线了，**完全靠口口相传**。

制品库就是**公司中央仓库**：
- **托管（hosted）**：存放我们自己构建出来的成品；
- **代理缓存（proxy）**：替公司去公网拉第三方依赖，第一次拉了就缓存下来，全公司共用，又快又稳；
- ** group 聚合**：把上面两类打包成一个地址给开发用，开发不用记多个地址。

> 一句话：**Harbor 主打容器镜像，Nexus 主打 Maven/npm 等多语言二进制**，两者经常一起用。

##### 1.2 Harbor vs Nexus 怎么选

| 维度 | Harbor | Nexus Repository |
|---|---|---|
| 核心定位 | 容器镜像（OCI）仓库 | 通用二进制制品仓库 |
| 擅长格式 | Docker/OCI 镜像、Helm Chart | Maven、npm、PyPI、NuGet、Docker、Go、Helm 等几十种 |
| 强项 | 镜像复制、漏洞扫描、 RBAC、镜像签名、保留策略 | 多语言代理缓存、仓库类型齐全、生态成熟 |
| 一句话 | "公司的镜像仓库" | "公司的依赖超市 + 成品仓库" |

#### 二、Harbor

##### 2.1 核心概念

| 概念 | 作用 |
|---|---|
| **Project（项目）** | 顶层隔离单元，对应一个团队/业务，下面放多个镜像仓库 |
| **成员角色** | 项目管理员 / 开发者 / 访客，控制谁能推、谁能拉 |
| **标签保留 Tag Retention** | 自动只保留最近 N 个 tag，旧的清掉，防止磁盘爆 |
| **不可变不可变规则 Immutable** | 已推送的 tag 禁止覆盖，杜绝"同一个 tag 内容变了" |
| **复制 Replication** | 多套 Harbor 之间/到云 Registry 同步镜像 |
| **漏洞扫描** | 内置 Trivy 对镜像做 CVE 扫描 |
| **代理缓存 Proxy Cache** | 作为 Docker Hub 等的 pull-through 缓存 |

##### 2.2 安装（离线安装包，固定 v2.15.5）

```bash
# 下载对应版本离线安装包（固定 v2.15.5）
tar xzvf harbor-offline-installer-v2.15.5.tgz
cd harbor

# 复制并修改配置
cp harbor.yml.tmpl harbor.yml
vim harbor.yml
#   hostname: harbor.example.com
#   https: 关 443 / 配证书
#   harbor_admin_password: 强密码

# 预生成配置并安装
./prepare
sudo ./install.sh

# 验证：访问 https://harbor.example.com，默认用户 admin
docker compose ps        # 由 docker compose 起的 core/portal/registry/...
```

##### 2.3 日常操作与 CI 集成

```bash
# 登录
docker login harbor.example.com -u admin

# 打标签并推送
docker tag myapp:v1.4.0 harbor.example.com/team-order/myapp:v1.4.0
docker push harbor.example.com/team-order/myapp:v1.4.0

# 用 API 触发镜像扫描
curl -u "admin:$HARBOR_PWD" -X POST \
  "https://harbor.example.com/api/v2.0/projects/team-order/repositories/myapp/artifacts/v1.4.0/scan"
```

##### 2.4 保留策略与不可变规则（防止磁盘爆炸）

```yaml
# 在 Harbor 项目 → 保留策略（Retention）里配（示意）
# 规则：每个仓库只保留最近 10 个镜像，其余自动删除
rules:
  - template: "recently_pushed_n_repos"
    params:
      repos: 10          # 只留最近 10 个 tag
    scope: { retain: "latest" }
```

> **不可变规则（Immutable Tag）**：上线后 `v1.4.0` 一旦推送就锁死，任何人不能再往这个 tag 推别的镜像。这非常重要——否则有人不小心覆盖了 `v1.4.0`，生产拉到的和当初测的不是同一个东西。

##### 2.5 高可用（HA）

Harbor 单体安装适合小团队。生产多实例部署要点：

| 组件 | HA 做法 |
|---|---|
| harbor-core / portal / jobservice | 起多个副本，前面挂负载均衡 |
| PostgreSQL / Redis | 用外部高可用 PG / Redis，不要用容器内嵌的 |
| 镜像存储（registry 后端） | 共用对象存储（S3/OSS/MinIO），不要本地磁盘 |
| 证书 | 统一在 LB 层终结 TLS |

#### 三、Nexus Repository

##### 3.1 三种仓库类型（必懂）

| 类型 | 作用 | 小白类比 |
|---|---|---|
| **proxy（代理）** | 代理公网源（Maven Central、npmjs），第一次拉了缓存 | 公司统一代购，一次买全公司用 |
| **hosted（托管）** | 存我们自己发布的内部包 | 自家产品仓库 |
| **group（组）** | 把 proxy + hosted 聚合成一个地址 | 一个门牌号进所有货架 |

开发只需要配**一个 group 地址**：要第三方包自动走 proxy 缓存，要内部包自动走 hosted。

##### 3.2 部署 Nexus 3.96.3

```bash
# 用官方镜像起（固定 3.96.3），数据挂到宿主机
docker run -d --name nexus \
  -p 8081:8081 \
  -v /data/nexus:/nexus-data \
  sonatype/nexus3:3.96.3

# 初始 admin 密码在容器里
docker exec nexus cat /nexus-data/admin.password
```

##### 3.3 各类仓库配置要点

| 格式 | proxy 远程地址 | hosted 用途 |
|---|---|---|
| Maven (maven-central) | https://repo1.maven.org/maven2/ | 内部 release / snapshots |
| npm (npm-proxy) | https://registry.npmjs.org/ | 内部私有 npm 包 |
| PyPI (pypi-proxy) | https://pypi.org | 内部 Python 包 |
| Docker (docker-group) | pull-through 代理 Docker Hub | 内部镜像（可与 Harbor 互补） |
| Helm (helm-proxy) | https://charts.helm.sh/stable | 内部 Chart 仓库 |

开发端配置示例（npm 指向 Nexus group）：

```bash
npm config set registry http://nexus.example.com:8081/repository/npm-group/
```

Maven `settings.xml`：

```xml
<mirror>
  <id>nexus</id>
  <mirrorOf>*</mirrorOf>
  <url>http://nexus.example.com:8081/repository/maven-group/</url>
</mirror>
```

#### 四、制品晋升（Promotion）流程

制品库不是"堆在一起"，而是按环境分级。**同一个镜像**在不同环境"晋升"，而不是每个环境重新构建。

```mermaid
flowchart LR
    DEV["开发提交"] --> CI["CI 构建"]
    CI --> STG["staging 项目<br>测试镜像 + 扫描通过"]
    STG -->|人工/自动评审| PROD["production 项目<br>晋升后的生产镜像"]
    STG -. 漏洞高危则阻断 .-> BLOCK["⛔ 不允许晋升"]
    subgraph REG["Harbor 项目分层"]
        STG
        PROD
    end
```

> 小白类比：晋升像**毕业升年级**。制品在 staging "考试"（测试 + 安全扫描）及格了，才"升"到 production。全程**镜像 digest 不变**，保证"测的就是上的"。

```bash
# 用 Harbor 复制/API 把同一 digest 从 staging 晋升到 production 项目（示意）
# 注意：复制的是同一份 blob，不重新上传，省空间
curl -u "admin:$PWD" -X POST \
  "https://harbor.example.com/api/v2.0/projects/staging/repositories/myapp/artifacts/v1.4.0/additions" \
  -H "Content-Type: application/json" \
  -d '{"dest_project_name":"production","override":true}'
```

#### 五、CI/CD 集成完整示例

```yaml
# .github/workflows/publish.yml（推镜像到 Harbor + 晋升）
name: publish-artifact
on:
  push:
    tags: ["v*"]
jobs:
  publish:
    runs-on: ubuntu-24.04
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: docker/login-action@v3
        with:
          registry: harbor.example.com
          username: ${{ secrets.HARBOR_USER }}
          password: ${{ secrets.HARBOR_TOKEN }}
      - uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: harbor.example.com/staging/myapp:${GITHUB_REF_NAME}
      - name: 扫描镜像（高危阻断）
        run: |
          trivy image --exit-code 1 --severity HIGH,CRITICAL \
            harbor.example.com/staging/myapp:${GITHUB_REF_NAME}
      - name: 晋升到 production
        run: |
          curl -u "admin:${HARBOR_PWD}" -X POST \
            "https://harbor.example.com/api/v2.0/projects/staging/repositories/myapp/artifacts/${GITHUB_REF_NAME}/additions" \
            -H "Content-Type: application/json" \
            -d '{"dest_project_name":"production"}'
```

#### 六、容量与备份

| 事项 | 建议 |
|---|---|
| 磁盘规划 | 镜像很占空间，预留长期增长；开启**保留策略**只留最近 N 个 tag |
| 垃圾回收 GC | Harbor 定期跑 `docker-compose.yml` 里的垃圾回收，清理删除后无引用的 blob |
| 大文件存储 | 生产 registry 后端用对象存储（S3/OSS），别用本地磁盘 |
| Nexus 备份 | 备份 `/nexus-data` 目录（含 blob store + 数据库），停服或用在线备份工具 |
| Harbor 备份 | 备份数据库（PG）+ 镜像存储（对象存储）；升级前必备份 |

```bash
# Harbor 垃圾回收（先设为只读，再跑 GC）
docker compose stop harbor-core
docker compose run --rm registry garbage-collect /etc/registry/config.yml
docker compose start harbor-core
```

#### 七、常见问题排错

| 现象 | 原因 | 解决 |
|---|---|---|
| docker push 报 unauthorized | 没登录 / 项目无权限 | `docker login`；确认账号在该 Project 的开发者角色 |
| push 报 toomanyrequests | 没走代理缓存，直连 Docker Hub 限流 | 配 Harbor Proxy Cache 或 Nexus docker proxy |
| 磁盘被打爆 | 没配 tag 保留策略，历史镜像无限堆积 | 配置 retention，定期 GC；清理无用 tag |
| 同名 tag 被覆盖引发事故 | 没开不可变规则 | 项目里开启 Immutable Tag 规则 |
| Nexus 代理拉 npm 包 401/超时 | 远程地址错 / 公司代理未配 | 检查 proxy remote URL，配置 Nexus 出站 HTTP 代理 |
| 晋升后生产拉不到镜像 | production 项目没授权给部署节点 | 给 K8s 节点 docker secret 配 production 项目的 pull 权限 |

::: warning 生产红线
- 镜像 tag 固定版本号，**开启不可变规则**，禁止覆盖已发布 tag；禁止生产用 `latest`。
- 生产 Harbor/Nexus **必须 HTTPS + 强密码 + 最小权限账号**，CI 用机器人账号（robot account）而非 admin。
- 定期跑垃圾回收与保留策略，**镜像存储用对象存储**，并纳入备份。
- 晋升路径要"测试环境扫过的镜像 digest 原样进生产"，不要在生产重新构建。
- 升级前先备份数据库与制品存储，先在测试环境验证升级路径。
:::

#### 相关速查

- 流水线里镜像要先过安全扫描：[DevSecOps 与软件供应链安全](#合并资料)
- 镜像签名后在仓库里怎么验：[DevSecOps（Cosign 签名）](#合并资料)
- 容器基础：[Docker 命令速查](/reference/docker-commands)、[K8s 命令速查](/reference/kubectl-commands)
- 部署打包：[Helm 包管理](/services/container/helm)

##### 官方文档

- Harbor 官网：https://goharbor.io/
- Harbor 文档：https://goharbor.io/docs/
- Harbor releases：https://github.com/goharbor/harbor/releases
- Sonatype Nexus Repository 下载：https://help.sonatype.com/en/download.html
- Sonatype Nexus 文档：https://help.sonatype.com/
- Nexus 2026 release notes：https://help.sonatype.com/en/nexus-repository-2026-release-notes.html

</details>

<details>
<summary><strong>DevSecOps 与软件供应链安全 — 安全不能再等上线前&#x27;临时抱佛脚&#x27;。这篇讲安全左移：在 CI/CD 流水线每个节点自动插哪些检查（SAST/DAST/SCA/镜像扫描/SBOM/签名/准入），用什么开源工具（Trivy、Syft、Cosign、SonarQube、Kyverno），以及 SLSA 供应链等级是什么。适合要把&#x27;安全检查…</strong></summary>

::: tip 本篇定位
安全不能再等上线前"临时抱佛脚"。这篇讲**安全左移**：在 CI/CD 流水线每个节点自动插哪些检查（SAST/DAST/SCA/镜像扫描/SBOM/签名/准入），用什么开源工具（Trivy、Syft、Cosign、SonarQube、Kyverno），以及 SLSA 供应链等级是什么。适合要把"安全检查"自动化进流水线、堵住软件供应链攻击的 SRE。
本篇版本：Trivy v0.74.0、SonarQube Community Build 26.9.0.129388、Syft v1.43.0、Cosign v3.0.6、Kyverno（开源准入策略引擎）。所有版本以官网当前稳定版为准。
:::

#### 一、背景与基础

##### 1.1 小白类比：把安检门装进流水线

传统安全像**机场只在登机口查一次证**：临上线前安全同学手扫一遍，问题多、慢、还容易漏。

**DevSecOps = 把安检门搬到传送带的每一道工序上**：代码刚提交就查代码质量，依赖一下载就查有没有已知漏洞，镜像一构建就扫漏洞+生成物料清单，镜像推送时**签名**，部署到 K8s 时准入控制器再验一遍签名。哪道工序不合格，传送带直接停，坏东西流不到生产。

> 核心理念：**Security as Code / 安全左移**——把安全做成流水线里自动跑的检查，而不是上线前的人工审批。

##### 1.2 流水线安全检查点全景

```mermaid
flowchart LR
    DEV["开发者提交代码"]--> G1["阶段1 源码"]
    G1 --> SAST["SAST 静态扫描<br>SonarQube/Semgrep"]
    G1 --> SCA["SCA 依赖扫描<br>查第三方漏洞"]
    SAST --> BUILD["构建镜像"]
    SCA --> BUILD
    BUILD --> G2["阶段2 制品"]
    G2 --> IMG["Trivy 镜像扫描"]
    G2 --> SBOM["Syft 生成 SBOM"]
    G2 --> SIGN["Cosign 签名"]
    IMG --> REG["推送到制品库"]
    SBOM --> REG
    SIGN --> REG
    REG --> DEP["部署到 K8s"]
    DEP --> G3["阶段3 运行时准入"]
    G3 --> ADM["Kyverno/OPA<br>验签名 + 策略"]
    G3 --> DAST["DAST 动态扫描<br>运行态探活"]
```

##### 1.3 各类扫描一表分清

| 缩写 | 全称 | 扫什么 | 类比 | 工具 |
|---|---|---|---|---|
| **SAST** | 静态应用安全测试 | 源码本身的漏洞/坏味道（不运行程序） | 对着菜谱找错别字 | SonarQube、Semgrep |
| **SCA** | 软件成分分析 | 第三方依赖里的已知 CVE、许可证 | 检查食材是不是过期 | Trivy（fs/repo）、Dependabot |
| **DAST** | 动态应用安全测试 | 运行中的服务探活找漏洞 | 点菜试吃看会不会拉肚子 | OWASP ZAP |
| **镜像扫描** | —— | 镜像里的系统包/应用依赖漏洞 | 开箱前扫整箱货 | Trivy |
| **IaC 扫描** | —— | Terraform/K8s YAML 配置错误 | 检查消防设计图 | Trivy tf |

#### 二、SAST：SonarQube 与 Semgrep

##### 2.1 SonarQube Community Build 26.9

SonarQube 是最主流的代码质量与安全扫描平台，开箱看 Bug、漏洞、坏味道、测试覆盖率。社区版免费，支持 20+ 语言。

```bash
# 用 Docker 起社区版（固定版本号）
docker run -d --name sonarqube \
  -p 9000:9000 \
  -v sonarqube_data:/opt/sonarqube/data \
  sonarqube:26.9.0.129388-community
# 首次访问 http://服务器:9000，默认 admin/admin，立即改密码
```

CI 里用 scanner 扫（在仓库根目录）：

```bash
docker run \
  -e SONAR_HOST_URL="http://sonarqube:9000" \
  -e SONAR_TOKEN="$SONAR_TOKEN" \
  -v "$PWD:/usr/src" \
  sonarsource/sonar-scanner-cli:6 \
  sonar-scanner \
  -Dsonar.projectKey=order-service \
  -Dsonar.sources=.
```

##### 2.2 Semgrep（轻量、规则即代码）

Semgrep 适合在 PR 上快速跑自定义规则，比 SonarQube 更轻、规则可自定义。

```bash
# 跑 Semgrep（容器）
docker run --rm -v "${PWD}:/src" semgrep/semgrep:1.112.0 \
  semgrep --config=auto /src --error
# --config=auto 自动选适合该语言的规则集；--error 有高危就退出非 0 阻断
```

#### 三、Trivy：一把瑞士军刀

Trivy 一个二进制搞定**镜像 / 文件系统 / Git 仓库 / IaC / 配置**扫描，是 DevSecOps 的主力。

##### 3.1 常用命令（v0.74.0）

```bash
# 1) 扫镜像（最常用），只报 HIGH/CRITICAL，发现就退出码 1
trivy image --severity HIGH,CRITICAL --exit-code 1 \
  harbor.example.com/team/order:v1.4.0

# 2) 扫本地源码/依赖目录（SCA：查第三方依赖 CVE）
trivy fs --scanners vuln,secret,misconfig ./

# 3) 扫 IaC（Terraform / K8s YAML 的配置错误）
trivy config ./terraform/

# 4) 扫 Git 仓库历史里有没有硬编码密钥
trivy repo --scanners secret https://github.com/your-org/order-service.git

# 输出格式：SARIF（接 GitHub 代码扫描）/ CycloneDX SBOM
trivy image --format sarif --output result.sarif myapp:v1
trivy image --format cyclonedx --output sbom.json myapp:v1
```

##### 3.2 在 GitHub Actions 里集成

```yaml
- name: Trivy 镜像扫描
  uses: aquasecurity/trivy-action@0.35.0      # 固定 tag，注意供应链版本
  with:
    image-ref: harbor.example.com/team/order:v1.4.0
    format: 'sarif'
    output: 'trivy-results.sarif'
    severity: 'CRITICAL,HIGH'
    exit-code: '1'          # 有高危就让流水线失败
- name: 上传 SARIF 到 GitHub 代码扫描
  uses: github/codeql-action/upload-sarif@v3
  with: { sarif_file: 'trivy-results.sarif' }
```

::: warning Trivy Action 供应链事件提醒
历史上 `aquasecurity/trivy-action` / `setup-trivy` 曾被投毒。生产中引用第三方 Action 务必**固定到具体 tag 或 commit SHA**，关注官方安全公告，及时升级到安全版本。
:::

#### 四、SBOM：软件物料清单

##### 4.1 小白类比

SBOM（Software Bill of Materials）就是**这碗菜的食材清单**：镜像里到底打包了哪些开源库、什么版本。一旦某个开源库（如 Log4j）爆了 CVE，你拿着 SBOM 一查就知道"我哪些服务中招了"，不用挨个问。

##### 4.2 用 Syft 生成（v1.43.0）

```bash
# 生成 SPDX 格式 SBOM
syft harbor.example.com/team/order:v1.4.0 -o spdx-json=sbom.spdx.json

# 生成 CycloneDX 格式
syft harbor.example.com/team/order:v1.4.0 -o cyclonedx-json=sbom.cdx.json
```

把 SBOM 随镜像一起存进制品库（附件），便于事后应急响应时快速定位受影响资产。

#### 五、Cosign 镜像签名与验签

光扫描还不够，还要保证"部署到生产的镜像确实是我们 CI 构建出来的、没被人偷偷换过包"。**Cosign（Sigstore 项目）**给镜像签名。

##### 5.1 keyless（无密钥，CI 里最省事）与密钥两种模式

| 模式 | 原理 | 适合 |
|---|---|---|
| **keyless（临时证书）** | CI 里用 OIDC 身份拿短时证书签名，私钥不落盘 | GitHub Actions 等 CI 自动签名，最推荐 |
| **密钥对** | 自己生成/管理 cosign key pair | 离线环境、需要长期验签密钥 |

##### 5.2 CI 里签名 + 集群里验签

```bash
# CI 里 keyless 签名（GitHub Actions 中需 id-token: write 权限）
cosign sign --yes harbor.example.com/team/order:v1.4.0

# 集群侧准入前验签：只允许带我们签名的镜像运行
COSIGN_EXPERIMENTAL=1 cosign verify \
  --certificate-identity-regexp "https://github.com/your-org/*" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  harbor.example.com/team/order:v1.4.0
```

#### 六、准入控制：Kyverno / OPA Gatekeeper

镜像推上去、签好了，部署到 K8s 时还要**准入控制器**在 API Server 拦截：只允许"已签名 + 无 Critical 漏洞 + 不以 root 跑 + 必须设 requests/limits"的 Pod 进集群。

| 工具 | 特点 |
|---|---|
| **Kyverno** | 策略就是 Kubernetes YAML，对 K8s 原生、学习曲线低 |
| **OPA Gatekeeper** | 策略用 Rego 语言表达，灵活但陡峭 |

Kyverno 校验镜像签名的策略片段：

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: verify-image-signatures
spec:
  validationFailureAction: Enforce     # 不合规直接拒绝
  rules:
    - name: verify-cosign-signature
      match:
        any:
          - resources: { kinds: ["Pod"] }
      verifyImages:
        - imageReferences:
            - "harbor.example.com/team/*"
          attestors:
            - entries:
                - keyless:
                    issuer: "https://token.actions.githubusercontent.com"
                    subject: "https://github.com/your-org/*"
```

#### 七、SLSA 供应链等级

SLSA（Supply-chain Levels for Software Artifacts）给软件供应链的"成熟度"分级：

| 等级 | 含义 |
|---|---|
| **SLSA 1** | 构建过程有文档、产出构建说明 |
| **SLSA 2** | 构建在托管平台上、有版本控制、产生签名 provenance |
| **SLSA 3** | 构建平台 hardened、隔离、源码受保护、 provenance 被签名 |
| **SLSA 4** | 双人评审 + 隔离构建 + 可验证的签名来源 |

> 目标不是一步到位 SLSA 4，而是**逐级提升**：有 SBOM、有签名、有 provenance，就已经甩开大部分团队。

#### 八、完整流水线安全阶段示例

```yaml
# .github/workflows/secure-pipeline.yml
name: secure-ci
on: [pull_request]
jobs:
  security:
    runs-on: ubuntu-24.04
    permissions:
      contents: read
      id-token: write          # Cosign keyless 需要
    steps:
      - uses: actions/checkout@v4
      - name: SAST (Semgrep)
        uses: semgrep/semgrep-action@v1
      - name: SCA + 扫密钥 (Trivy fs)
        run: trivy fs --scanners vuln,secret --exit-code 1 .
      - name: 构建并推 staging 镜像
        run: |
          echo "${{ secrets.HARBOR_TOKEN }}" | docker login harbor.example.com -u ci --password-stdin
          docker build -t harbor.example.com/staging/order:${GITHUB_SHA::12} .
          docker push harbor.example.com/staging/order:${GITHUB_SHA::12}
      - name: 镜像漏洞扫描
        run: trivy image --severity CRITICAL --exit-code 1 harbor.example.com/staging/order:${GITHUB_SHA::12}
      - name: 生成 SBOM (Syft)
        run: syft harbor.example.com/staging/order:${GITHUB_SHA::12} -o cyclonedx-json=sbom.json
      - name: 签名 (Cosign keyless)
        uses: sigstore/cosign-installer@v4.0.0
      - run: cosign sign --yes harbor.example.com/staging/order:${GITHUB_SHA::12}
```

#### 九、常见问题排错

| 现象 | 原因 | 解决 |
|---|---|---|
| Trivy 一直报某个旧镜像有 Critical | 基础镜像没更新 | 升级基础镜像重新构建，别只修应用层 |
| Cosign keyless 签名在 CI 失败 | 没开 `id-token: write` | workflow 里加 `permissions: id-token: write` |
| Kyverno 把正常 Pod 全拦了 | 策略 `Enforce` 但规则写错 | 先把 `validationFailureAction` 设 `Audit` 观察，确认无误再切 `Enforce` |
| SonarQube 覆盖率为 0 | 没传覆盖率报告文件 | 跑测试时生成 cobertura/xml 并 `sonar.coverageReportPaths` |
| 扫出硬编码密钥但还在 Git 历史里 | 只在当前文件挡了 | 轮换该密钥（已泄露），用 `git filter-repo` 清历史 |
| SBOM 找不到新引入的依赖 | 锁文件没提交 | 确保 package-lock/go.sum 进仓库再扫 |

::: warning 生产红线
- 高危（CRITICAL）漏洞镜像**禁止晋升生产**；准入策略 `Enforce` 后要先 `Audit` 灰度。
- 所有镜像**必须签名**，集群侧只允许验签通过的镜像运行（防止供应链替换）。
- 第三方 Action / 扫描器 Action **固定 commit SHA**，定期关注投毒公告升级。
- 一旦发现真硬编码密钥：**立即轮换密钥**，光删代码没用，Git 历史里还在。
- 扫描规则别一上来就 `exit-code 1` 卡死所有团队，先设基线、再逐步收紧。
:::

#### 相关速查

- 扫出来的镜像放哪、怎么晋升：[制品库 Harbor 与 Nexus](#合并资料)
- 签名后密钥/证书怎么管：[密钥与证书管理](#合并资料)
- 部署到 K8s 与 GitOps：[GitOps（ArgoCD）](#合并资料)
- 运行时出问题怎么定位：[OpenTelemetry 可观测](/guide/monitor#合并资料)
- K8s 命令：[kubectl 命令速查](/reference/kubectl-commands)

##### 官方文档

- Trivy 文档：https://trivy.dev/
- Trivy releases：https://github.com/aquasecurity/trivy/releases
- SonarQube Community Build 下载：https://www.sonarsource.com/products/sonarqube/downloads/
- SonarQube Community Build 文档：https://docs.sonarsource.com/sonarqube-community-build/
- Semgrep 文档：https://semgrep.dev/docs/
- Syft 文档：https://anchore.com/opensource/
- Syft releases：https://github.com/anchore/syft/releases
- Cosign 文档：https://docs.sigstore.dev/cosign/
- Cosign releases：https://github.com/sigstore/cosign/releases
- Kyverno 文档：https://kyverno.io/
- SLSA 官方：https://slsa.dev/

</details>

<details>
<summary><strong>FinOps 云成本治理 — 云上账单月底一看吓一跳，但说不清&#x27;钱花哪了、哪个业务超支、谁该背这个钱&#x27;。这篇讲 FinOps：怎么让成本可见、可分摊、可优化、可告警，重点在 Kubernetes 上用 OpenCost / Kubecost 按 namespace/label 算账，怎么 right-sizing、用 Spot…</strong></summary>

::: tip 本篇定位
云上账单月底一看吓一跳，但说不清"钱花哪了、哪个业务超支、谁该背这个钱"。这篇讲 **FinOps**：怎么让成本**可见、可分摊、可优化、可告警**，重点在 Kubernetes 上用 **OpenCost / Kubecost** 按 namespace/label 算账，怎么 right-sizing、用 Spot、买预留实例。适合背云预算、想把"乱花钱"变成"按业务算账"的 SRE/平台团队。
本篇版本：OpenCost 1.121.0（CNCF）、Kubecost v3.1（IBM/Apptio）。所有版本以官网当前稳定版为准。
:::

#### 一、背景与基础

##### 1.1 小白类比：从"全家共用一张卡"到"各自记账 AA"

以前物理机房，钱是年初一次性花的，买完服务器就放那，没人天天算成本。上云后资源随用随开，**像手机流量不设套餐随便跑**——开发随手开个大规格机器忘了关，月底账单就爆炸。

FinOps 就是给云开支**装一套"家庭记账 + AA 分摊"系统**：
- **看得见**：每一笔花在哪、哪个业务、哪个团队；
- **分得清**：公共底座成本怎么摊到各业务；
- **省得下**：找出浪费、用更便宜的方式买；
- **管得住**：超预算报警、异常波动告警。

> 关键认知：**FinOps 不是财务一个部门的事**，是工程、财务、业务一起对成本负责。

##### 1.2 FinOps 三阶段

```mermaid
flowchart LR
    A["① Inform 告知<br>看得见钱花哪"] --> B["② Optimize 优化<br>找出浪费省下来"]
    B --> C["③ Operate 运营<br>把成本做进日常流程"]
    C -. 持续反馈 .-> A
```

| 阶段 | 干什么 | 产出 |
|---|---|---|
| **Inform（告知）** | 成本可视化、按标签分摊、出账单报表 | "谁花了多少"一目了然 |
| **Optimize（优化）** | right-sizing、关停闲置、用 Spot、买预留 | 把浪费挤掉 |
| **Operate（运营）** | 预算、告警、把成本指标纳入团队 KPI | 长期可持续 |

##### 1.3 协作角色

| 角色 | 在 FinOps 里的责任 |
|---|---|
| **平台/SRE** | 搭成本工具、做标签规范、优化集群利用率 |
| **开发/业务团队** | 对自己服务的成本负责、按建议 right-size |
| **财务** | 定预算、做分摊口径、出账单 |
| **管理层** | 定成本目标、推动跨团队协作 |

#### 二、成本可视化与分摊

##### 2.1 标签规范（一切分摊的基础）

**没有标签，就没有分摊。** 云上每个资源都要打标签，否则账单是一笔糊涂账。

```yaml
# 强制标签规范（示例，写进 IaC / 准入策略）
team: order            # 哪个团队
app: order-service      # 哪个应用
environment: prod       # 环境
business-unit: trade    # 哪个业务线
cost-center: CC-1001    # 成本中心
```

> 类比：标签就是快递单上的"收件人"。没写收件人的包裹（资源），最后只能大家平摊，没人会主动省。

##### 2.2 共享成本怎么分摊

集群控制面、公共数据库、Ingress 网关这类"大家共用"的成本，不能算在某一个团队头上。常见分摊方式：

| 分摊方式 | 做法 | 适合 |
|---|---|---|
| 按用量分摊 | 谁用的 CPU/内存多谁多付 | 计算资源 |
| 按人头/收入 | 按团队人数或业务收入比例摊 | 公共底座 |
| 固定比例 | 事先约定好比例 | 稳定的公共服务 |

#### 三、Kubernetes 成本：OpenCost 与 Kubecost

K8s 里你申请的是 `requests`，不是实际用量。**成本要按 requests 占整集群的比例来分摊**。

##### 3.1 OpenCost vs Kubecost

| 维度 | OpenCost | Kubecost |
|---|---|---|
| 定位 | CNCF 开源、轻量成本模型 | 商业产品（有免费层），功能全 |
| 强项 | 按 namespace/label 算 K8s 成本、API | 预算、异常告警、right-size 建议、多集群 |
| 适合 | 想自己搭、轻量、可控 | 想要开箱即用的全套成本治理 |

##### 3.2 安装 OpenCost（1.121.0）

```bash
# 安装 OpenCost（固定 chart/镜像版本）
helm repo add opencost https://opencost.io/helm
helm install opencost opencost/opencost \
  --namespace opencost --create-namespace \
  --set image.tag=prod-1.121.0
# 访问 NodePort/Ingress，默认 UI 在 9003 端口
```

```bash
# 按 namespace 看成本（API）
curl http://opencost.opencost.svc:9003/allocation/compute \
  | jq '.[] | {namespace, totalCost}'
```

##### 3.3 Kubecost 看分摊（v3.1）

```bash
# 安装 Kubecost（Helm，固定版本）
helm repo add kubecost https://kubecost.github.io/cost-analyzer/
helm install kubecost kubecost/cost-analyzer \
  --namespace kubecost --create-namespace \
  --set kubecostImage="kubecost/cost-analyzer:v3.1.0"
```

进去后重点看：
- **Allocation**：按 namespace / label 拆每个服务花了多少钱；
- **Right Sizing Recommendations**：哪些 Pod requests 设太大了；
- **Efficiency**：集群整体资源利用率。

#### 四、优化手段

##### 4.1 requests/limits right-sizing（最直接省钱）

很多人图省事把 requests 设得很大，导致**大量资源申请了却没用**，集群被占满又得加机器。

```yaml
# ❌ 反面：requests 远大于实际用量，浪费
resources:
  requests: { cpu: "2", memory: "8Gi" }
  limits:   { cpu: "4", memory: "16Gi" }
```

做法：用监控看**实际 P95 用量**，把 requests 调到略高于实际峰值（留 ~20% 余量）。Kubecost/OpenCost 会直接给建议值。

##### 4.2 弹性伸缩

| 手段 | 干什么 | 省在哪 |
|---|---|---|
| **HPA** | 按 CPU/自定义指标自动增减 Pod 副本 | 波谷少跑副本 |
| **Cluster Autoscaler** | 按 Pod 需求自动增减节点 | 波谷少开节点 |
| **VPA** | 自动调 requests | 避免手设过大 |

##### 4.3 Spot / 抢占式实例

| 实例类型 | 折扣 | 风险 | 适合 |
|---|---|---|---|
| 按量 On-Demand | 原价 | 无 | 有状态、核心在线 |
| **Spot/抢占式** | 1~3 折 | 云厂商可能随时（提前几分钟）回收 | 无状态、可中断、批处理 |
| **预留实例/储蓄计划 RI/Savings** | 买 1~3 年承诺，3~7 折 | 提前承诺 | 长期稳定负载 |

```mermaid
flowchart TB
    CORE["核心在线服务<br>按量 + 预留实例"] --> SAVE["预留实例打底<br>3-7 折"]
    BATCH["批处理/无状态服务"] --> SPOT["Spot 实例<br>1-3 折，容忍中断"]
```

> 组合拳：**稳定基线用预留实例打折，波动部分用 Spot 省钱，两者之间用 On-Demand 兜底**。

##### 4.4 别忽视的隐形账单

| 类别 | 容易浪费的点 |
|---|---|
| **存储** | 旧快照没删、闲置云盘、对象存储冷热不分层 |
| **网络** | 跨区流量、公网出向流量（egress）很贵 |
| **IP/负载均衡** | 闲置的 EIP、没删的 LB |
| **日志/监控** | 日志无限保留、高基数指标打爆存储 |

#### 五、预算与成本异常告警

```yaml
# Kubecost 预算示例：order 团队月预算 $5000，超 80% 告警
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
# （概念示意）在 Kubecost 里配置 budget：
#  scope: namespace:order
#  amount: 5000
#  window: monthly
#  threshold: 0.8        # 用到 80% 就告警
#  notifications: [slack/钉钉 webhook]
```

成本异常告警比预算更灵敏：**昨天还花 $100，今天突然 $500，立刻告警**——通常是有人开了大机器忘了关、或测试环境没销毁。

#### 六、落地步骤

1. **先打通可见性**：装 OpenCost/Kubecost，先能按 namespace 看到钱花哪。
2. **立标签规范**：准入策略强制每个资源带 `team/app/environment` 标签。
3. **出第一份账单报表**：按团队/业务线出月度成本报告，让大家有感知。
4. **做 right-sizing 专项**：按建议把 requests 过大的 Pod 调小，回收节点。
5. **引入弹性 + Spot**：无状态服务上 HPA + Cluster Autoscaler，批处理上 Spot。
6. **买预留实例**：把稳定基线用 RI/储蓄计划覆盖。
7. **设预算与异常告警**：接入 Slack/钉钉，长期运营。
8. **联动容量规划**：成本趋势反推未来 3~6 月的容量与采购。

#### 七、常见问题排错

| 现象 | 原因 | 解决 |
|---|---|---|
| OpenCost 显示成本为 0 | 没配云厂商价格 / 没接 metrics | 配置云厂商 API key 或自定义 pricing，确认 Prometheus 在采集 |
| 某个 namespace 成本特别高 | 大 requests / 闲置 Pod | 看 right-size 建议，下调 requests，删闲置工作负载 |
| 账单和 K8s 成本对不上 | 云账单含网络/存储/控制面，K8s 只算计算 | OpenCost/Kubecost 补接 Cloud Costs 模块 |
| Spot 实例被频繁回收 | 选的机型现货余量少 | 多可用区多机型混合调度，配中断优雅终止 |
| 标签打不齐 | 没准入强制 | 用 Kyverno/OPA 校验：缺标签的资源不让建 |
| 预留实例买多了浪费 | 没看清长期基线就买 | 先按量跑 1~3 个月看清稳态，再买 RI |

::: warning 生产红线
- **标签是 FinOps 的地基**：准入策略强制关键标签，缺标签资源不让创建。
- right-sizing 要**先观测再调整**，别拍脑袋砍 requests，小心砍到 OOM。
- Spot 只用于**可中断的无状态/批处理**，有状态核心数据库别上 Spot。
- 预留实例**先有稳定用量再买**，别为了折扣过度承诺。
- 成本异常告警要接入值班通道，发现"谁开了大机器忘了关"立刻追。
:::

#### 相关速查

- 成本数据来自这些指标：[OpenTelemetry 统一可观测](/guide/monitor#合并资料)
- 容量与灾备：[容量规划、高可用与灾备](./sre-capacity-dr)
- 集群伸缩：[K8s 架构与集群](/services/container/kubernetes/01-理论)
- 基础设施即代码里打标签：[Terraform](./automation-terraform)
- K8s 命令：[kubectl 命令速查](/reference/kubectl-commands)

##### 官方文档

- OpenCost 官网：https://opencost.io/
- OpenCost 文档：https://opencost.io/docs/
- OpenCost releases：https://github.com/opencost/opencost/releases
- Kubecost 文档：https://docs.kubecost.com/
- Kubecost releases：https://github.com/kubecost/kubecost/releases
- FinOps 基金会：https://www.finops.org/

</details>

<details>
<summary><strong>平台工程与内部开发者平台（IDP） — 当团队从几个人涨到几十上百人，&#x27;每个人都要会 K8s、会 Terraform、会配监控和告警&#x27;会变成灾难。这篇讲清楚平台工程（Platform Engineering）到底要解决什么问题、内部开发者平台（IDP）长什么样、Backstage 怎么搭、什么是黄金路径与 DevEx，适合已经在用 Dev…</strong></summary>

::: tip 本篇定位
当团队从几个人涨到几十上百人，"每个人都要会 K8s、会 Terraform、会配监控和告警"会变成灾难。这篇讲清楚**平台工程（Platform Engineering）**到底要解决什么问题、内部开发者平台（IDP）长什么样、Backstage 怎么搭、什么是黄金路径与 DevEx，适合已经在用 DevOps 但开始被"重复造轮子、环境申请慢、踩坑没人兜底"折磨的 SRE/平台团队。
本篇版本：Backstage v1.54.6（CNCF Incubating，Yarn 3 + Node.js 20+）、Spotify 开源并贡献给 CNCF。所有版本以官网当前稳定版为准。
:::

#### 一、背景与基础

##### 1.1 小白类比：从"农家乐"到"连锁中央厨房"

早期 DevOps 像**农家乐**：每个厨师（开发）自己买菜、自己生火、自己刷锅，菜好吃但全靠师傅个人经验，人一走味道就变。团队一大，问题来了：

- 每个新项目都要重新搭一遍"代码仓库 + CI + 环境 + 监控 + 日志 + 权限"，重复劳动；
- 新人入职第一周还在问"测试环境怎么申请""数据库连串写哪"；
- 每个团队各搞各的，监控告警风格五花八门，半夜出事没人知道该看哪个面板；
- SRE 被各种"帮我开个权限""帮我建个 namespace"的工单淹没。

**平台工程就是把农家乐升级成连锁中央厨房**：菜品（服务）怎么做由厨师（开发）定，但灶台、调料、出餐流程、安检（安全合规）、洗碗（日志监控）全部由后厨平台团队统一备好、封装好。开发点菜一样自助就能拿到"标准套餐"，不用每次自己砌灶。

> 一句话：**DevOps 强调"开发自己对生产负责"，平台工程强调"给开发铺好一条好走的路，让他们能又快又稳地自己负责"。**

##### 1.2 DevOps 落地的现实困境

很多公司喊了多年 DevOps，最后发现交付速度并没有质的提升，反而摩擦越来越大。常见困境：

| 困境 | 表现 | 后果 |
|---|---|---|
| 认知负载过重 | 一个开发要懂 Git、CI、K8s、Istio、监控、证书、密钥 | 学习曲线陡，新人上手慢，犯错率高 |
| 重复造轮子 | 每个团队各自写 Helm values、各自接告警 | 标准不统一，SRE 救火成本高 |
| 环境不一致 | 本地、测试、生产配置漂移 | "我本地是好的"经典事故 |
| 自助化不足 | 一切找运维工单排队 | 交付卡在等审批，速度上不去 |
| 看不见全貌 | 一个服务散落在 Git、CI、云控制台、监控里 | 出事找不到负责人、看不到依赖关系 |

平台工程不是否定 DevOps，而是**把 DevOps 中重复、通用、高门槛的那部分沉淀成自助平台**，让开发专注写业务代码。

##### 1.3 平台工程 vs DevOps 关系（不是取代）

| 维度 | DevOps | 平台工程 |
|---|---|---|
| 目标 | 打通开发与运维，打破部门墙 | 用产品化的平台，放大 DevOps 的效率 |
| 谁来做 | 开发 + 运维协作 | 专门的平台团队，把平台当产品做 |
| 交付物 | 流程、文化、工具链 | 自助式内部开发者平台（IDP） |
| 开发体验 | 自己动手，丰衣足食 | 平台给"黄金路径"，开发自助点单 |
| 关系 | 理念与文化 | DevOps 成熟后的**工程化落地手段**，是对 DevOps 的补充而非替代 |

> 业界常说："You cannot build a Platform for DevOps, you build it with DevOps." 平台团队不是新的审批衙门，而是**内部服务团队**。

#### 二、内部开发者平台（IDP）的能力分层

内部开发者平台（Internal Developer Platform, IDP）是一整套**给开发用的自助工具与自服务能力**的集合。它不是某个软件，而是一组工具 + 规范 + 门户的组合。

##### 2.1 能力分层（用图看全局）

```mermaid
flowchart TB
    subgraph L1["体验层 Developer Portal"]
        P["Backstage 软件目录<br>统一入口 / 文档 / 模板"]
    end
    subgraph L2["自服务层 Self-Service"]
        SCAF["Scaffolder 脚手架<br>一键建服务"]
        GOLD["黄金路径模板<br>CI/CD/环境/监控标配"]
    end
    subgraph L3["能力平台层 Platform Capabilities"]
        CI["CI/CD 流水线"]
        DEP["K8s / 发布"]
        OBS["监控日志可观测"]
        SEC["安全 / 密钥 / 制品"]
    end
    subgraph L4["基础设施层 Infrastructure"]
        CLOUD["云账号 / 集群 / 网络 / 存储"]
    end
    P --> SCAF
    P --> GOLD
    SCAF --> CI
    GOLD --> CI
    GOLD --> DEP
    GOLD --> OBS
    GOLD --> SEC
    CI --> CLOUD
    DEP --> CLOUD
```

> 类比：体验层是**手机桌面**，自服务层是**一键换装 App**，能力平台层是**安卓系统 API**，基础设施层是**芯片和电池**。开发通常只碰前两层。

##### 2.2 各层职责

| 层 | 解决什么 | 典型工具 |
|---|---|---|
| 体验层（门户） | 一个入口看清所有服务、负责人、文档、依赖 | Backstage |
| 自服务层 | 不用提工单，自助创建服务/环境/权限 | Backstage Scaffolder、模板 |
| 能力平台层 | 把 CI、部署、监控、安全封装成标准能力 | GitHub Actions/GitLab CI、Argo CD、Prometheus、Vault、Harbor |
| 基础设施层 | 底层云资源，用 IaC 管理 | Terraform、K8s 集群 |

#### 三、Backstage：最主流的开源 IDP 门户

Backstage 由 Spotify 开源（现在是 CNCF 孵化项目），是一个**构建内部开发者门户的框架**——注意它本身不是"装好就完事"的成品软件，而是一个"脚手架 + 插件生态"，你要在它之上搭自己公司的门户。

##### 3.1 四大核心概念

| 概念 | 作用 | 小白类比 |
|---|---|---|
| **Software Catalog（软件目录）** | 登记所有服务/网站/库及其 owner、依赖、生命周期 | 公司的"通讯录 + 组织架构图"，只不过记录的是软件 |
| **Scaffolder（模板脚手架）** | 点一下按钮，按公司标准模板生成新服务仓库（含 CI、Dockerfile、监控） | 装修公司的"样板间"，选一套直接拎包入住 |
| **TechDocs（技术文档）** | 在代码仓库里写 Markdown，自动渲染到门户，文档跟代码在一起 | 文档不再散落各处，服务页直接挂着它的说明书 |
| **插件生态（Plugins）** | 把 CI 状态、监控面板、部署、成本等外部系统嵌进服务页 | 给浏览器装扩展，想要什么功能就插一个 |

##### 3.2 快速创建一个 Backstage 应用

```bash
# 前置：Node.js 20+、Yarn 3（Backstage 官方推荐）
npx --version
node --version

# 用官方创建器生成一个新的 Backstage 应用（版本以创建器当前模板为准）
npx @backstage/createer@latest create my-idp
# 交互式回答：应用名、组织名，等待安装依赖（较久）

cd my-idp
yarn install
yarn dev          # 启动，默认 http://localhost:3000
```

::: tip 版本说明
上面 `npx @backstage/createer@latest` 是滚动脚手架，它每次会拉取当时最新的 Backstage 版本（当前 v1.54.x 线）。装完后看实际版本：

```bash
# 查看后端 / 前端实际安装的 backstage 包版本
cat packages/backend/package.json | grep -E '"@backstage/core-app-api"|"@backstage/plugin-catalog"'
# 例如 "@backstage/core-app-api": "^1.x.x"
```

生产部署不要用 `yarn dev`，用打包后的静态资源 + 后端服务（见官方部署文档）。
:::

##### 3.3 注册一个软件组件到 Catalog

在你的服务仓库里放一个 `catalog-info.yaml`，Backstage 就能"认识"它：

```yaml
# catalog-info.yaml（放在业务服务仓库根目录，随代码一起演进）
apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: order-service
  title: 订单服务
  description: 处理下单、支付回调的核心微服务
  labels:
    tier: "critical"
  annotations:
    # 指向该服务的 TechDocs 目录
    backstage.io/techdocs-ref: dir:.
    # 指向外部 CI/监控（用对应插件解析）
    github.com/project-slug: your-org/order-service
    grafana/dashboard-selector: "order-service"
spec:
  type: service
  lifecycle: production
  owner: team-order          # 必须指向 Catalog 里的一个 Group/User
  system: trade-platform
  providesApis:
    - order-api
```

在 Backstage 里注册这个仓库位置（`app-config.yaml`）：

```yaml
catalog:
  locations:
    - type: url
      target: https://github.com/your-org/order-service/blob/main/catalog-info.yaml
      rules:
        - allow: [Component, API, Resource, System]
```

##### 3.4 Scaffolder 模板（黄金路径的载体）

`templates/service/template.yaml` 定义"一键新建服务"：

```yaml
apiVersion: scaffolder.backstage.io/v1beta3
kind: Template
metadata:
  name: spring-service-template
  title: 标准 Spring Boot 微服务
  description: 内置 CI、Dockerfile、监控、Helm 部署的标准服务模板
spec:
  owner: team-platform
  type: service
  parameters:
    - title: 服务信息
      required: [name, owner]
      properties:
        name:
          title: 服务名
          type: string
          pattern: '^[a-z0-9-]+$'
        owner:
          title: 负责人团队
          type: string
          ui:field: OwnerPicker
  steps:
    - id: fetch
      name: 取模板
      action: fetch:template
      input:
        url: ./skeleton
        values:
          name: "${{ parameters.name }}"
    - id: publish
      name: 建仓库
      action: publish:github
      input:
        repoUrl: "github.com?owner=your-org&repo=${{ parameters.name }}"
    - id: register
      name: 注册到目录
      action: catalog:register
      input:
        repoContentsUrl: "${{ steps.publish.output.repoContentsUrl }}"
        catalogInfoPath: "/catalog-info.yaml"
```

##### 3.5 部署要点

| 事项 | 建议 |
|---|---|
| 数据库 | 生产用 PostgreSQL（默认 sqlite 只适合本地） |
| 认证 | 接公司 OIDC / LDAP / GitHub OAuth，不要裸奔 |
| 部署形态 | 容器化部署（Backend 一个进程 + 前端静态资源），后面挂 K8s Ingress |
| 插件 | 按需安装（CI、K8s、Grafana、Jenkins），别一次装太多拖慢首屏 |
| 配置 | 环境相关配置放 `app-config.production.yaml`，不进 Git |

#### 四、黄金路径 Golden Path 与开发者体验 DevEx

##### 4.1 什么是黄金路径

> **黄金路径（Golden Path）= 平台团队官方认证的"标准做法"。** 它把"如何新建一个合规、可观测、能上生产的服务"封装成一条默认路径，开发只要顺着走，就能自动获得 CI、扫描、监控、日志、告警、证书、密钥——全都配好。

类比：高速公路。你可以自己走小路（自定义一切），但平台团队修好一条**有路灯、有护栏、有应急车道**的高速，默认带你直达生产。走高速默认安全、快；要下道自己折腾，风险自担。

```mermaid
flowchart LR
    DEV["开发"] --> CH{"选择路径"}
    CH -->|黄金路径| G1["一键脚手架<br>标准模板"]
    G1 --> G2["自动 CI/CD<br>自动安全扫描"]
    G2 --> G3["自动监控告警<br>自动日志"]
    G3 --> PROD["生产<br>合规且可观测"]
    CH -->|自定义小路| C1["自己搭<br>自己配"]
    C1 --> C2["踩坑 / 缺监控<br>安全不合规"]
```

##### 4.2 DevEx 的三个核心维度（DX 框架）

开发者体验（Developer Experience）衡量"开发干活得爽不爽"，常从三个维度看：

| 维度 | 含义 | 反面信号 |
|---|---|---|
| **反馈循环（Feedback Loop）** | 从写代码到看到结果有多快（本地启动、CI 跑完、部署上线） | 本地启动 20 分钟、CI 排队半小时 |
| **认知负载（Cognitive Load）** | 开发需要记住/学习多少东西才能完成任务 | 每加个功能要翻 5 个内部 Wiki |
| **心理安全（Psychological Safety）** | 开发敢不敢上线、出问题能不能快速回滚不背锅 | 怕上线、不敢动老服务 |

> 衡量指标可以看：**DORA 四指标**（部署频率、变更前置时间、变更失败率、 MTTR），平台做得好不好，最终落在这四个数字上。

#### 五、平台团队拓扑（Team Topologies）

平台工程怎么和其他团队协作？参考《Team Topologies》：

| 团队类型 | 职责 | 与平台团队关系 |
|---|---|---|
| **平台团队（Platform Team）** | 建 IDP、维护黄金路径、不直接写业务 | 提供"内部产品"，有 roadmap、有用户（开发） |
| ** Stream-aligned 业务团队** | 直接面向业务交付 | 平台的"客户"，自助用平台能力 |
| **Enabling 赋能团队** | 帮业务团队补能力（如安全、数据） | 临时介入，知识转移后撤离 |
| **Complicated-subsystem 子系统团队** | 负责极复杂的部分（如高性能计算） | 被平台包裹，对业务屏蔽复杂度 |

> 关键原则：平台团队对外暴露的是**薄而稳定的"团队 API"（Team API）**——也就是自助门户上的那几个动作（建服务、申请环境、看成本）。内部实现可以随便换（ArgoCD 换 Flux、Prometheus 换别的），但对开发暴露的入口和体验要稳定。

```mermaid
flowchart TB
    subgraph PLAT["平台团队 Platform Team"]
        API["团队 API<br>自助门户 / 黄金路径"]
    end
    B1["业务团队 A"] --> API
    B2["业务团队 B"] --> API
    B3["业务团队 C"] --> API
    API -. 内部实现可替换 .-> CORE["CI / CD / K8s / 监控 / 密钥 / 制品"]
```

#### 六、常见问题排错

| 现象 | 原因 | 解决 |
|---|---|---|
| `yarn dev` 启动报 Node 版本不对 | Backstage 要求 Node.js 20+ | `node -v` 检查，用 nvm 切到 20 LTS |
| 服务注册后 Catalog 里不显示 | `catalog-info.yaml` 路径写错或 owner 不存在 | 确认 target URL 指向原始 raw 文件；确认 `owner` 在 Catalog 中已登记 |
| 前端插件装太多首屏极慢 | 一次性引入大量重型插件 | 按需懒加载，先上 Catalog + Scaffolder + 一个监控插件 |
| Scaffolder 建仓库失败 | GitHub token 权限不足 | 给 Backstage 用的 GitHub App 授予 repo 写权限与 workflow 权限 |
| TechDocs 渲染空白 | 文档旁未配 `techdocs-ref` 或未跑 docs 生成器 | 检查 annotation，确保 Markdown 在仓库内并配置 TechDocs publisher |
| 生产用 sqlite 崩了 | 默认 sqlite 不支持多实例/并发 | 生产切换 PostgreSQL，按官方部署文档配置 |

::: warning 生产红线
- Backstage 是**内部系统，不要暴露公网**：前面必须接 SSO/OIDC 认证，禁止无鉴权裸奔。
- 生产数据库用 **PostgreSQL**，sqlite 只用于本地开发；定时备份数据库。
- 不要把平台团队做成"新审批衙门"：平台是**服务团队**，要衡量开发自助成功率，而不是审批了多少工单。
- 黄金路径要"默认安全"：把安全扫描、密钥管理、镜像签名**预置进模板**，而不是让开发自己记得加。
- 插件接入第三方系统时用**最小权限 token**，并定期轮换。
:::

#### 相关速查

- 平台上铺的自动化底座：[Jenkins 与 Git](#合并资料)、[GitOps（ArgoCD）](#合并资料)、[Terraform](./automation-terraform)
- 服务模板里默认打包的部署能力：[Helm 包管理](/services/container/helm)
- 可观测层：[OpenTelemetry 统一可观测](/guide/monitor#合并资料)
- Git 协作：[Git 命令与协作工作流速查](/reference/git-commands)

##### 官方文档

- Backstage 官网：https://backstage.io/
- Backstage 文档：https://backstage.io/docs/
- Software Catalog 文档：https://backstage.io/docs/features/software-catalog/
- Scaffolder 文档：https://backstage.io/docs/features/software-templates/
- TechDocs 文档：https://backstage.io/docs/features/techdocs/
- Backstage 插件库：https://backstage.io/plugins/
- Backstage 源码与 releases：https://github.com/backstage/backstage/releases

</details>

<details>
<summary><strong>密钥与证书管理 — 数据库密码、API Token、TLS 证书这些&#x27;东西&#x27;到底放哪、怎么不硬编码进 Git、怎么自动轮换？这篇讲 HashiCorp Vault（动态密钥/PKI）、Sealed Secrets（把 K8s Secret 加密进 Git）、External Secrets Operator（把外部密钥…</strong></summary>

::: tip 本篇定位
数据库密码、API Token、TLS 证书这些"东西"到底放哪、怎么不硬编码进 Git、怎么自动轮换？这篇讲 **HashiCorp Vault**（动态密钥/PKI）、**Sealed Secrets**（把 K8s Secret 加密进 Git）、**External Secrets Operator**（把外部密钥同步进集群）、**cert-manager**（证书自动签发轮换），以及密钥轮换策略。适合被"密钥散落各处、轮换靠手工、证书过期半夜告警"折磨的 SRE。
本篇版本：HashiCorp Vault Community Edition 2.1.1、Sealed Secrets controller v0.38.4、External Secrets Operator v2.6.0、cert-manager v1.21.0。所有版本以官网当前稳定版为准。
:::

#### 一、背景与基础

##### 1.1 小白类比：硬编码密钥的痛

最常见的错误做法：把数据库密码直接写在代码配置里、提交进 Git 仓库。

```python
# ❌ 反面教材
DB_PASSWORD = "P@ssw0rd123"   # 就这么裸奔进了 Git
```

问题在哪？
- **Git 历史永远留痕**，删了也能翻出来；仓库一开源/一离职带走，全完；
- **改密码要改代码、重新发版**，慢且高危；
- **谁有密码不知道**，没法审计、没法按人吊销；
- **证书忘了续期**，半夜业务突然挂。

> 正确思路：**密码不写代码、不进 Git、自动生成、自动过期、自动轮换**。下面的工具就是干这个的。

##### 1.2 工具各管一段

| 工具 | 解决什么 | 一句话定位 |
|---|---|---|
| **Vault** | 密钥的"金库+出纳"：集中存放、动态生成、自动过期 | 真正的密钥源（source of truth） |
| **Sealed Secrets** | 想把 Secret 也进 GitOps？用它加密 | Git 里存"密文"，只有集群能解密 |
| **External Secrets Operator** | 把 Vault/云 KMS 里的密钥同步成 K8s Secret | 桥：外部金库 → 集群 |
| **cert-manager** | K8s 里 TLS 证书自动签发/续期 | 证书不手工 renew |

#### 二、HashiCorp Vault

##### 2.1 它是什么 / 核心能力

Vault 是一个**专门管密钥的中心化服务**。它不只是个加密保险柜，最大杀招是**动态密钥**——密码不是你预先设好存进去的，而是应用**用的时候临时申请一个、用完自动过期回收**。

```mermaid
flowchart TB
    APP["应用 / K8s Pod"] -->|认证 + 申请| VAULT["Vault 金库"]
    VAULT --> KV["KV 引擎<br>存静态密钥"]
    VAULT --> DB["数据库引擎<br>动态生成 DB 账号"]
    VAULT --> PKI["PKI 引擎<br>动态签发证书"]
    DB --> MIDDLE["租期 lease<br>到期自动吊销"]
    PKI --> MIDDLE
```

##### 2.2 部署与 unseal（vault 2.1.1）

```bash
# 容器起 Vault（开发模式，仅实验用！）
docker run -d --name vault -p 8200:8200 \
  -e 'VAULT_DEV_ROOT_TOKEN_ID=root' \
  hashicorp/vault:2.1.1

export VAULT_ADDR='http://127.0.0.1:8200'
vault status
```

::: danger 生产不要用 dev 模式
上面 `VAULT_DEV_ROOT_TOKEN_ID` 是**开发模式**，数据一重启就没。生产要 `vault server` 正式模式 + 初始化（`vault operator init`）+ **Shamir 分片 unseal** + 高可用集群。
:::

##### 2.3 KV 引擎：存静态密钥

```bash
# 开启 KV v2 引擎
vault secrets enable -path=secret kv-v2

# 写入一个密钥
vault kv put secret/order/db username=orderapp password=强密码

# 读取
vault kv get secret/order/db
```

##### 2.4 动态数据库账号与 lease（杀手锏）

不要把一个固定的 DB 密码给所有服务。让 Vault 代你**临时开账号**：

```bash
# 1) 配 Vault 连数据库（用一个高权限账号去管理）
vault secrets enable database
vault write database/config/my-pg \
  plugin_name=postgresql-database-plugin \
  connection_url="postgresql://{{username}}:{{password}}@pg:5432/" \
  allowed_roles="order-role" \
  username="vaultadmin" password="管理密码"

# 2) 定义一个角色：申请出来的账号有什么权限、活多久
vault write database/roles/order-role \
  db_name=my-pg \
  creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; GRANT SELECT ON ALL TABLES IN SCHEMA public TO \"{{name}}\";" \
  default_ttl="1h" max_ttl="24h"

# 3) 应用每次要连库，临时申请一个（1 小时后自动吊销）
vault read database/creds/order-role
# Key                Value
# lease_id           database/creds/order-role/abcd1234
# username           v-root-order-role-abcd
# password           A1b2...
# lease_duration     1h
```

> 好处：即使这个临时账号泄露，**1 小时后自动失效**；而且每个实例拿到的账号都不一样，可按 lease 精确吊销。

##### 2.5 PKI 引擎：当内部 CA

Vault 还能当**内部证书颁发机构（私域 CA）**，给内部服务自动签 TLS 证书：

```bash
vault secrets enable pki
vault write pki/root/generate/internal common_name="internal-ca.example.com" ttl=87600h
# 建角色允许签发 *.svc.cluster.local 的证书
vault write pki/roles/k8s allowed_domains="svc.cluster.local" allow_subdomains=true max_ttl=720h
# 签一张证书
vault write pki/issue/k8s common_name="order.svc.cluster.local"
```

##### 2.6 Kubernetes 集成与高可用

- **K8s auth 方法**：应用用自己的 ServiceAccount Token 向 Vault 换密钥，不用人工发 token。
- **HA**：Vault 生产跑 3 节点 Raft 集群，共享存储自动选主；每节点都要 **unseal**（或用 auto-unseal / HSM）。

#### 三、Sealed Secrets

##### 3.1 原理（小白类比）

K8s 原生 Secret 只是 Base64 编码（**不是加密**），谁 `kubectl get secret -o yaml` 都能解码。但 GitOps 又希望所有配置进 Git。矛盾怎么解？

**Sealed Secrets**：集群里跑一个 controller，持有一把**私钥**。开发用对应的**公钥**把普通 Secret 加密成 `SealedSecret` 这个 CRD 存进 Git。这个密文**只有本集群的 controller 能解开**——哪怕 Git 仓库公开，别人拿着密文也解不出原文。

```mermaid
flowchart LR
    DEV["开发者<br>用公钥加密"] -->|kubeseal| SS["SealedSecret 密文<br>存进 Git"]
    SS -->|apply| CTL["集群内 controller<br>持有私钥"]
    CTL -->|解密| SEC["原生 Secret<br>普通 Pod 挂载"]
```

##### 3.2 使用（controller v0.38.4）

```bash
# 安装 controller（固定 v0.38.4）
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.38.4/controller.yaml

# 准备一个普通 Secret，加密成 SealedSecret
kubectl create secret generic db-creds \
  --from-literal=password=强密码 -o yaml --dry-run=client > secret.yaml
kubeseal --format yaml < secret.yaml > sealedsecret.yaml
# sealedsecret.yaml 可以安全提交进 Git；secret.yaml 立刻删掉
```

> 注意：SealedSecret 是**和 namespace+name 绑定**加密的，改了名字/命名空间要重新 seal。

#### 四、External Secrets Operator（ESO）

Sealed Secrets 把密钥"烤进 Git"，但密钥轮换时你得重新 seal。**ESO 反过来：Vault/云 KMS 才是源头，ESO 自动把最新值同步成 K8s Secret**。

```mermaid
flowchart LR
    VAULT["Vault / 云 KMS<br>密钥源"] --> ESO["External Secrets Operator<br>v2.6.0"]
    ESO -->|定期同步| K8S["K8s Secret"]
    K8S --> POD["应用 Pod 挂载"]
```

##### 4.1 对接 Vault 的完整示例

```yaml
# 1) SecretStore：声明"密钥从哪来"（指向 Vault）
apiVersion: external-secrets.io/v1
kind: SecretStore
metadata:
  name: vault-backend
  namespace: order
spec:
  provider:
    vault:
      server: "http://vault.vault.svc:8200"
      path: "secret"           # KV v2 引擎路径
      version: "v2"
      auth:
        kubernetes:           # 用 K8s ServiceAccount 认证
          role: "order-role"
          serviceAccountRef:
            name: "eso-order"
---
# 2) ExternalSecret：声明"要同步哪些 key 成一个 Secret"
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: db-creds
  namespace: order
spec:
  refreshInterval: 1h          # 每小时同步一次（Vault 里改了会自动跟上）
  secretStoreRef:
    name: vault-backend
    kind: SecretStore
  target:
    name: db-creds             # 生成的 K8s Secret 名字
  data:
    - secretKey: password      # K8s Secret 里的 key
      remoteRef:
        key: order/db          # Vault KV 路径
        property: password     # 该路径下的字段
```

```bash
# 安装 ESO v2.6.0（Helm）
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets \
  --version 0.26.0 --namespace external-secrets --create-namespace
```

#### 五、cert-manager：证书自动签发与轮换

##### 5.1 它解决什么

TLS 证书会过期。手工 `certbot` 申请、到期前手工 renew，迟早忘。**cert-manager** 在 K8s 里自动：申请证书 → 验证域名所有权 → 存成 Secret → **到期前自动续期**。

##### 5.2 内部 PKI + 公开证书两种用法

| 用法 | Issuer 类型 | 场景 |
|---|---|---|
| 公开可信证书 | Let's Encrypt（ACME） | 对外的 https 网站 |
| 内部私有 CA | SelfSigned / Vault / 自己的 CA | 集群内部 mTLS |

##### 5.3 安装与示例（v1.21.0）

```bash
# 安装 cert-manager（固定 v1.21.0）
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.21.0/cert-manager.yaml
kubectl wait --namespace cert-manager \
  --for=condition=ready pod --selector=app=cert-manager --timeout=120s
```

用 Let's Encrypt 签一张公开证书：

```yaml
# 1) ClusterIssuer：Let's Encrypt
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: ops@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
      - http01:
          ingress:
            class: nginx
---
# 2) Certificate：申请 example.com 的证书，自动存成 Secret
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: example-tls
  namespace: order
spec:
  secretName: example-tls        # 证书会写到这个 Secret
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  commonName: www.example.com
  dnsNames: [www.example.com, example.com]
  duration: 2160h                # 90 天，到期前自动续
  renewBefore: 360h             # 到期前 15 天开始续
```

Ingress 里直接引用：

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: order
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
    - hosts: [www.example.com]
      secretName: example-tls
  rules:
    - host: www.example.com
      http: { paths: [] }
```

#### 六、密钥轮换策略

| 策略 | 怎么做 | 目标 |
|---|---|---|
| **动态密钥（Vault）** | 租期 1h，用完自动吊销 | 几乎不用"轮换"，因为每把都短命 |
| **静态密钥定期轮换** | Vault 改值 → ESO 每小时同步 → Pod 滚动重启 | 凭证不长期有效 |
| **数据库账号** | Vault 动态账号天然短命 | 泄露窗口小 |
| **证书** | cert-manager 到期自动续 | 永不过期告警 |

> 黄金法则：**能动态就别静态，能短命就别长命**。静态长期密码是事故之源。

#### 七、常见问题排错

| 现象 | 原因 | 解决 |
|---|---|---|
| Vault 重启后读写报 sealed | 没 unseal | `vault operator unseal` 输入 Shamir 分片（生产需多人分片） |
| ESO 创建的 Secret 是空的 | Vault 路径/字段写错、ServiceAccount 无权限 | 看 ExternalSecret 事件：`kubectl describe es`；核对 path 与 role |
| SealedSecret 解密失败 | namespace/name 被改，或换了集群私钥 | 用目标集群公钥重新 `kubeseal`；迁移要备份 controller 私钥 |
| cert-manager 证书一直 Ready=False | DNS/HTTP01 校验没过 | 查 CertificateRequest/Order 事件；确认 Ingress/ DNS 解析通 |
| 证书快过期还没续 | renewBefore 设太近 | 调大 `renewBefore`（如到期前 15 天） |
| 应用读不到 Vault 动态凭证 | K8s auth role 没授权该 ServiceAccount | 在 Vault 里给 role 绑定对应 SA 的 policy |

::: warning 生产红线
- **永远不要把真实密钥提交进 Git**；K8s Secret 默认只 Base64，敏感场景开启 etcd 加密。
- Vault 生产必须：正式模式 + Shamir 分片 unseal + 多节点 HA + **备份**（Raft 快照）。
- 备份好 Sealed Secrets controller 私钥 / Vault 的 unseal key——**丢了就全集群密钥都解不开**。
- 用最小权限：ESO/Vault 给每个应用单独的 role/SA，不要一个 token 走天下。
- 证书与密钥纳入到期监控，提前告警；动态密钥缩短租期以降低泄露影响。
:::

#### 相关速查

- 密钥在流水线里怎么用：[DevSecOps 与软件供应链安全](#合并资料)
- K8s 部署底座：[GitOps（ArgoCD）](#合并资料)、[Helm 包管理](/services/container/helm)
- 加密存储 etcd：[K8s 安全篇](/services/container/kubernetes/01-理论)
- K8s 命令：[kubectl 命令速查](/reference/kubectl-commands)

##### 官方文档

- HashiCorp Vault 文档：https://developer.hashicorp.com/vault/docs
- Vault releases：https://releases.hashicorp.com/vault/
- Sealed Secrets：https://github.com/bitnami-labs/sealed-secrets
- Sealed Secrets releases：https://github.com/bitnami-labs/sealed-secrets/releases
- External Secrets Operator 文档：https://external-secrets.io/
- ESO releases：https://github.com/external-secrets/external-secrets/releases
- cert-manager 文档：https://cert-manager.io/docs/
- cert-manager releases：https://cert-manager.io/docs/releases/
- cert-manager GitHub：https://github.com/cert-manager/cert-manager/releases

</details>

<!-- merged-guide-material:end -->
