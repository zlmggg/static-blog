# CI/CD 持续交付

::: tip 本篇定位
覆盖 CI/CD 概念、流水线工具、发布策略和可靠部署。
:::

## 高频面试题

### Q1：完整 CI/CD 流程？

**我的答案：**

结论：CI/CD 是"代码提交到上线"的自动化流水线，分 **CI（持续集成）→ CD（持续交付/部署）** 两大段。

CI 段：开发 push 代码到 Git，自动触发流水线。第一步**拉代码、装依赖**（`npm ci`、`mvn dependency:go-offline`）；第二步**静态检查和单元测试**（lint、`mvn test`、`npm test`、覆盖率统计）；第三步**构建制品**——Java 打 jar/war、前端打 dist、更重要的是**打 Docker 镜像**，tag 用 commit SHA 或版本号，推到镜像仓库（Harbor/ACR）。任何一步失败立即中止，通知开发。

CD 段：制品 ready 后，先**部署到测试环境**，自动跑集成测试、E2E 测试（Cypress/Playwright）、接口自动化；测试通过后**人工审批或自动部署预发环境**（和生产同构）；预发验证通过，再**发布到生产**。生产发布不是一把梭，要用蓝绿/金丝雀/滚动策略，发布过程中监控错误率和指标，异常自动回滚。最后发钉钉/飞书通知。

整个流水线的关键原则：**一切自动化、制品不可变**——测试环境用的镜像和生产用的是同一个镜像，不靠"重新构建一次"换环境，避免"我这能跑你那不行"。环境差异用 ConfigMap/配置中心解决，不打进镜像。失败要能一键回滚，回滚也是自动化的，不要人肉登服务器。

---

### Q2：Jenkins 和 GitLab CI 区别？

**我的答案：**

结论：Jenkins 是独立的通用 CI 服务器，插件生态最猛；GitLab CI 是和 GitLab 仓库一体、用 `.gitlab-ci.yml` 描述流水线，轻量、开箱即用。

第一，**架构和集成**。Jenkins 是独立部署的服务，Master 调度、Agent 干活，要自己装、自己升级、自己备份。它支持任何 Git 仓库（GitHub/GitLab/Gitee）。GitLab CI 直接内置在 GitLab 里，你在仓库根目录放个 `.gitlab-ci.yml`，push 就触发，不用单独装 CI 服务器，Runner 也是轻量 agent。

第二，**Pipeline 定义方式**。Jenkins 早期用自由风格 UI 配置，现在也支持 Jenkinsfile（Groovy 写在仓库里），但 Groovy 写复杂逻辑学习曲线陡。GitLab CI 就是 YAML 声明 stages/jobs/script，简洁直观，新人半天就能上手。

第三，**插件生态**。Jenkins 赢麻了，1800+ 插件，几乎能接任何工具，企业里老牌项目、复杂流水线基本都是 Jenkins。代价是插件多了容易版本冲突、安全漏洞一堆，要定期升。GitLab CI 内置了绝大多数常用能力，插件没 Jenkins 多但够用。

第四，**资源和成本**。Jenkins Master-Agent 模型灵活，能把编译任务甩给不同机器；GitLab Runner 也支持 Docker executor、shell executor，单机小团队够用。

怎么选：团队已经在用 GitLab、流水线不复杂，直接 GitLab CI，省事；已经有 Jenkins 集群、需要极度定制化、对接各种私有系统，继续 Jenkins。现在新起的小团队用 GitHub Actions / GitLab CI 的越来越多，Jenkins 更多是存量维护。

---

### Q3：常见发布策略？

**我的答案：**

结论：三种主流发布策略——**滚动、蓝绿、金丝雀**，区别在"新旧版本并存多久、流量怎么切、回滚快不快、成本高不高"。

**滚动发布（Rolling Update）**：老版本 Pod 一个一个被新版本替换，K8s Deployment 默认就是。优点：不需要双倍机器，资源省；缺点：发布过程中新老版本同时在线，要保证 API 向后兼容；回滚要把过程倒着再滚一遍，慢一点。最常用，K8s 原生 `maxSurge/maxUnavailable` 控制节奏。

**蓝绿发布（Blue-Green）**：起一套全新的绿色环境跑新版本，老的蓝色环境原样不动；验证绿色没问题，流量一次性从蓝切到绿（改 Nginx upstream、Service selector、负载均衡权重）。优点：**回滚极快**，切回蓝就行，几秒钟；缺点：要双倍资源，成本高。核心业务、对回滚速度要求高的用。

**金丝雀发布（Canary）**：先让一小部分流量（比如 1%、5%）到新版本，观察一段时间（错误率、延迟、业务指标），没问题再逐步放大到 10%、30%、100%。优点：风险最小，出问题只影响一小撮用户；缺点：周期长、要监控和流量切分能力（Ingress/Nginx 按权重、Istio 按百分比）。

对比：

| 策略 | 资源成本 | 回滚速度 | 风险 | 适用 |
|---|---|---|---|---|
| 滚动 | 低（约 1.25 倍） | 中 | 中 | 日常迭代 |
| 蓝绿 | 高（双倍） | 极快 | 低 | 核心、大版本 |
| 金丝雀 | 中 | 快（切回权重） | 最低 | 大流量、核心链路 |

K8s 上怎么落地：滚动用 Deployment 原生；蓝绿用两套 Deployment 切 Service selector；金丝雀用 Ingress 注解（`nginx.ingress.kubernetes.io/canary-weight: "10"`）或 Istio VirtualService。三种都要配合监控（Prometheus/Grafana、错误率、SLO）和自动回滚。

---

## 相关链接

- [相关文档](/guide/automation-jenkins)
