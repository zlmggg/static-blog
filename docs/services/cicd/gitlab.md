---
title: "GitLab · 代码托管与 CI 一体"
description: "GitLab 代码托管 + CI/CD 一体化、与 Jenkins 的选型、omnibus/Docker 部署、.gitlab-ci.yml 的 stages/jobs、Runner 注册与执行器、artifacts/cache、流水线实战。单页四段。"
---

# GitLab · 代码托管与 CI 一体

> 单页四段：理论 → 部署 → 功能 → 实战。返回 [服务详解 · CI/CD 与自动化](/services/cicd/)。专职流水线对比 [Jenkins](/services/cicd/jenkins/01-理论)。

## 01 · 服务理论

GitLab 是**代码托管 + CI/CD 一体化**平台：Git 仓库、MR 评审、Issue、CI 流水线都在一个系统里。它的 CI 是内置的——代码 push 后按仓库里的 `.gitlab-ci.yml` 自动跑流水线，不用额外搭 Jenkins。

### CI 与 CD 各管什么

- **CI（持续集成）**：合并代码后自动构建、跑测试、出制品，拦住坏代码。
- **CD（持续交付）**：制品自动部署到类生产，手动点一下才上生产。
- **CD（持续部署）**：合格后全自动上生产，对回滚能力要求极高。

### GitLab CI vs Jenkins

| | GitLab CI | Jenkins |
|---|---|---|
| 形态 | 与代码托管一体 | 独立自动化服务器 |
| 配置 | 仓库内 .gitlab-ci.yml | Jenkinsfile（也可 SCM） |
| 上手 | 开箱即用 | 插件生态强但需维护 |
| 适合 | 已用 GitLab 的团队 | 复杂编排/多系统集成 |

一句话：代码在 GitLab 就用 GitLab CI 最顺；要高度定制、跨多系统编排选 Jenkins。两者都遵循 **Pipeline as Code**——流水线写成 YAML 进 Git，可评审可回滚。

## 02 · 部署方案

### omnibus 安装（RHEL 系）

```bash
sudo dnf install -y curl policycoreutils openssh-server
curl https://packages.gitlab.com/install/repositories/gitlab/gitlab-ee/script.rpm.sh | sudo bash
sudo EXTERNAL_URL="http://gitlab.example.com" dnf install -y gitlab-ee
```

或 Docker：`docker run -d -p 80:80 --name gitlab gitlab/gitlab-ee:17.x`。首次登录 root 初始密码在 `/etc/gitlab/initial_root_password`（24h 后删，**及时改**）。GitLab 较重，建议 4C8G 起。

### 注册 Runner

Runner 是真正跑 job 的进程，可装在独立机器：

```bash
sudo gitlab-runner register
# 填 GitLab URL、token（项目 Settings→CI/CD→Runners 获取）、executor（shell/docker）
```

executor 选 docker 最干净（每个 job 一个容器），shell 直接用宿主机。

## 03 · 功能详解

### .gitlab-ci.yml

```yaml
stages: [build, test, deploy]

build_image:
  stage: build
  script:
    - docker build -t harbor.example.com/team/app:$CI_COMMIT_SHORT_SHA .
    - docker push harbor.example.com/team/app:$CI_COMMIT_SHORT_SHA

run_test:
  stage: test
  script:
    - npm ci && npm test

deploy_prod:
  stage: deploy
  script:
    - ansible-playbook deploy.yml
  when: manual              # 手动触发上生产
  only: [main]
```

- **stages** 定义阶段顺序，同 stage 的 job 并行，下一 stage 等上一 stage 全过。
- **artifacts** 在 job 间传产物，**cache** 缓存依赖加速（如 node_modules）。
- 凭据放 **Settings→CI/CD→Variables**（ masked/protected），别写进 yml。

## 04 · 实战参考

**典型链路**：push main → build 镜像推 [Harbor](/services/container/harbor) → test → 手动 deploy 用 [Ansible](/services/cicd/ansible) 上线。镜像 tag 用 commit SHA 保证可追溯，禁用 latest。

**常见坑**：

| 现象 | 原因 | 解法 |
|---|---|---|
| job 一直 pending | 没可用 Runner/tag 不匹配 | 注册 Runner、核对 tags |
| 502 | GitLab 内存不足 | 加内存/调 Puma worker |
| 凭据泄露 | 写进 yml | 用 CI Variables + masked |
| 缓存不生效 | cache key/path 错 | 核对 key 与 paths |

完整落地见 [部署方案](/deploy/) 与 [我的项目](/projects/homelab)。

## 官方文档

- GitLab：<https://docs.gitlab.com/>
- CI/CD：<https://docs.gitlab.com/ee/ci/>
- Runner：<https://docs.gitlab.com/runner/>

---

返回 [服务详解 · CI/CD 与自动化](/services/cicd/)。