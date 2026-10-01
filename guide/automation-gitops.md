---
category: 自动化
difficulty: 中级
---

# GitLab CI / ArgoCD

::: tip 本篇定位
掌握"代码一提交，自动构建镜像并自动部署到 Kubernetes"的整套流水线：GitLab CI 负责构建，ArgoCD 负责把 Git 里声明的配置自动同步到集群。
本篇版本：GitLab CE 19.4.1（与 [Git/Jenkins 篇](./automation-jenkins)一致）、ArgoCD v3.5.3、Kubernetes v1.30。
:::

## 一、CI/CD 概念

### 1.1 小白类比：什么是 CI/CD

你写了个网页应用，以前上线是这样的：本地 `mvn package` 打出 jar → scp 传到服务器 → SSH 上去停旧进程、启新进程。一旦多个人同时改代码、有多套环境（测试/预发/生产），就乱套了：谁传的包？传错版本了没？这次上线改了啥？

CI/CD 就是把"从代码改动到上线"这条路**自动化、标准化、留痕化**：

| 缩写 | 全称 | 通俗理解 | 对应谁干 |
|---|---|---|---|
| CI | Continuous Integration 持续集成 | 代码一提交，自动拉下来编译、跑测试，早发现冲突和错误 | GitLab CI / Jenkins |
| CD | Continuous Delivery 持续交付 | 测过的自动打好镜像、推到镜像仓库，随时可以一键发布 | GitLab CI |
| CD | Continuous Deployment 持续部署 | 更进一步：自动发布到生产，不用人点 | ArgoCD |

> 一句话：**CI 管"把代码变成制品"，CD 管"把制品送到环境里跑起来"。** 本篇前半段 GitLab CI 干 CI + 交付，后半段 ArgoCD 干持续部署。

### 1.2 推送（Push）vs 拉取（Pull）两种部署模式

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

### 1.3 GitOps 三大原则

GitOps 这个词由 Weaveworks 提出，现在是 CNCF 生态里 Kubernetes 部署的事实标准。它有四条铁律（前三条最核心）：

1. **声明式（Declarative）**：整个系统"想要长成什么样"全部用 YAML 描述，存进 Git。不写命令式脚本。
2. **版本控制 + 唯一真实来源（Git as Single Source of Truth）**：集群应该长什么样，以 Git 里的内容为准。要改配置？改 Git，别直接 `kubectl edit` 线上改。
3. **自动调谐（Automated Reconciliation）**：一个 Agent（ArgoCD）持续对比"Git 里声明的状态"和"集群实际状态"，不一致就自动修正（调谐/reconcile）。有人手动在集群里乱改，它会给你改回去。
4. **Agent 软件化**：负责拉取和部署的是经过充分测试的 Agent，而不是临时脚本。

> 类比：GitOps 像"按菜谱做菜"——菜谱（Git）是唯一标准，ArgoCD 是个厨师，每天对照菜谱看菜做对了没，做错了就照着菜谱重做一遍。你想换菜？改菜谱，别冲进厨房直接抢锅。

**为什么用 GitOps**：所有变更都有 Git 提交记录可审计；回滚就是 `git revert`；集群挂了能照着 Git 重建；CI 不用持有生产凭证，安全边界清晰。

## 二、GitLab CI

### 2.1 核心概念：`.gitlab-ci.yml`、Runner、Pipeline

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

### 2.2 完整 `.gitlab-ci.yml` 示例

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

### 2.3 看流水线结果

push 后在 GitLab 项目左侧 **Build → Pipelines** 看：三个阶段依次变绿。失败点在哪一眼定位，可从失败阶段重试。

## 三、ArgoCD 简介

### 3.1 它是什么

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

### 3.2 为什么是 Pull 而不是 Push

回到第一节那个对比：

| 对比 | Push（Jenkins 直连 kubectl） | Pull（ArgoCD / GitOps） |
|---|---|---|
| 谁发起部署 | CI 服务器主动推 | 集群内 ArgoCD 主动拉 |
| 生产凭证 | CI 要握生产 kubeconfig，权限极大 | CI 只改 Git，生产 kubeconfig 在集群内 |
| 状态可见性 | 部署完就完了，漂移难发现 | ArgoCD 持续盯着，漂移自动修正 |
| 审计 | 看 CI 日志 | 每一次变更都是一次 Git commit |
| 回滚 | 重新跑流水线 | `git revert` 再 push |

## 四、ArgoCD 使用

### 4.1 安装 ArgoCD（v3.5.3）

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

### 4.2 定义一个 Application（声明式清单）

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

### 4.3 配置仓库里长什么样

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

### 4.4 手动同步与回滚

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

## 五、落地建议

### 5.1 完整工作流串起来

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

### 5.2 多环境管理

测试、预发、生产三套环境，最常见两种做法：

- **分支隔离**：`manifests` 仓库用 `dev` / `staging` / `main` 三个分支，ArgoCD 里每个 Application 的 `targetRevision` 指不同分支。合并到 main 才上生产。
- **目录隔离（推荐）**：单分支 `main`，目录按环境分：`deploy/overlays/dev/`、`overlays/staging/`、`overlays/prod/`（配 Kustomize overlay，dev 用 1 副本、prod 用 3 副本）。Application 各指一个 path。

| 环境 | 副本数 | 同步策略 |
|---|---|---|
| dev | 1 | automated 自动同步 |
| staging | 2 | automated，接生产前演练 |
| prod | 3 | 手动 SYNC，要人确认后发布 |

生产环境建议把 `automated` 关掉，改成"CI 改完 Git，人在 ArgoCD UI 点一下同步"，保留最后一道人工闸门。

### 5.3 选型建议

- **纯虚拟机/物理机部署**：用 Ansible（见 [Ansible 篇](./automation-ansible)），别硬上 ArgoCD。
- **已经用 Kubernetes、服务数量多**：上 GitOps（ArgoCD），比 Jenkins 直连集群安全、可审计。
- **过渡期**：Jenkins/GitLab CI 负责 CI（编译、测试、构建镜像），部署给 ArgoCD——这也是本篇推荐的分工，CI 不碰生产集群凭证。

## 六、注意事项与排错

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

## 相关速查

- [kubectl 命令速查](/reference/kubectl-commands)
- Git / GitLab / Jenkins 基础与 CI：[Git / GitLab / Jenkins 持续集成](./automation-jenkins)
- 批量主机配置（非 K8s 环境）：[Ansible 运维自动化](./automation-ansible)

### 官方文档

- GitLab CI/CD 文档：https://docs.gitlab.com/ci/
- `.gitlab-ci.yml` 关键字参考：https://docs.gitlab.com/ci/yaml/
- ArgoCD 官方文档：https://argo-cd.readthedocs.io/
- ArgoCD 安装清单（选版本）：https://github.com/argoproj/argo-cd/releases
- ArgoCD Application 清单说明：https://argo-cd.readthedocs.io/en/stable/core_concepts/
