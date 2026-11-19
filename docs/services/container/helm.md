---
title: "Helm · K8s 包管理与 Kustomize"
description: "Helm 的 Chart/Repository/Release 概念、与 Kustomize 的路线对比、安装、Chart 结构与模板对象、values 覆盖优先级、Release 生命周期命令、从零做 Chart、OCI/Harbor 仓库、排错与生产红线。"
---

# Helm · K8s 包管理与 Kustomize

> 单页四段：理论 → 部署 → 功能 → 实战。返回 [服务详解 · 容器与编排](/services/container/)。K8s 基础见 [Kubernetes](/services/container/kubernetes/01-理论)。

## 01 · 服务理论

直接 `kubectl apply -f` 一套 YAML 就像"手动一个个文件装软件"：环境多了要复制粘贴改镜像 tag、改副本数，升级回滚全靠记。**Helm 之于 K8s，就像 apt/yum 之于 Linux**：

- **Chart** = 安装包，把应用的所有 YAML 模板 + 默认配置打包。
- **Repository** = 应用商店，里面有别人打包好的 Chart（nginx/redis/prometheus）。
- **Release** = 从包装出来、跑在集群里的那一份具体应用。同一 Chart 能装多个 Release（web-prod / web-staging）。

### Helm vs Kustomize：两条路线

| | Helm | Kustomize |
|---|---|---|
| 核心思想 | 模板化：YAML 变填空模板，values 填变量 | 无模板：base 原始 YAML + overlay 打补丁 |
| 能力 | 强（条件/循环/钩子/版本化发布） | 克制（只做字段覆盖，不写逻辑） |
| 适合 | 对外分发、参数化中间件 | 同一基线在多环境做小差异、GitOps |

一句话：**Helm 是"做安装包"，Kustomize 是"改现成配置"**。现实常组合——Helm 包中间件，Kustomize 在 overlay 里对渲染结果打补丁。

## 02 · 部署方案

```bash
# 固定版本手动安装（生产推荐，写死版本号）
wget https://get.helm.sh/helm-v4.3.0-linux-amd64.tar.gz
tar zxf helm-v4.3.0-linux-amd64.tar.gz
sudo mv linux-amd64/helm /usr/local/bin/
helm version
```

Helm 是客户端工具，无需服务端（Helm 3 起移除 Tiller）。Kustomize 已内建在 kubectl（`kubectl kustomize`）。

## 03 · 功能详解

### Chart 结构

```bash
helm create mychart
```

```
mychart/
├── Chart.yaml        # 元信息：名字/版本/appVersion
├── values.yaml       # 默认配置（最常改）
├── charts/           # 依赖子 Chart
└── templates/        # Go template：deployment/service/ingress...
```

### 模板对象与函数

`templates/` 里 `{{ .xxx }}` 是变量插值：`.Release.Name`（发布名）、`.Values.image.tag`（配置值）、`.Chart.AppVersion`。常用函数用管道串：`default`（空值给默认）、`quote`、`toYaml` 配 `nindent`（转 YAML 片段并缩进）、`include`（调命名模板）、`if/with/range`。

```yaml
image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
replicas: {{ .Values.replicaCount | default 1 }}
```

### values 覆盖优先级（低→高）

Chart 内置默认 → 子 Chart 带入 → 父 Chart 的 values 块 → 用户 `-f my-values.yaml` → 命令行 `--set`（最高）。

### Release 生命周期命令

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install myweb ./mychart -n dev --create-namespace --set replicaCount=3
helm list -A                          # 所有 Release
helm upgrade myweb ./mychart --set image.tag=v1.3.0 -n dev
helm history myweb -n dev             # 版本历史
helm rollback myweb 1 -n dev          # 回滚到第 1 版
helm uninstall myweb -n dev           # 卸载
helm template myweb ./mychart         # 本地渲染不安装（调试神器）
helm lint ./mychart                   # 校验
```

## 04 · 实战参考

### OCI / Harbor 仓库（趋势）

Helm 仓库正从老式 HTTP index.yaml 转向 **OCI 制品仓库**，镜像和 Chart 共用一套仓库与权限：

```bash
helm package ./mychart
helm registry login harbor.internal.local -u admin
helm push mychart-0.1.0.tgz oci://harbor.internal.local/chartrepo
helm install myweb oci://harbor.internal.local/chartrepo/mychart --version 0.1.0
```

私有仓库见 [Harbor](/services/container/harbor)。

### Kustomize 速通

```
base/      deployment.yaml service.yaml kustomization.yaml
overlays/prod/   kustomization.yaml prod-patch.yaml
```

```bash
kubectl kustomize overlays/prod      # 渲染最终 YAML
kubectl apply -k overlays/prod       # 直接应用
```

overlay 继承 base，用 patches/replicas/images 只改差异字段，适合多环境小差异。

### 排错与生产红线

| 现象 | 原因 | 解法 |
|---|---|---|
| 渲染出 `<no value>` | Values 路径/缩进错 | helm template 本地渲染对照 |
| 升级后没变化 | 镜像 tag 没变 | 改 tag 或 rollout restart |
| rollback 后还是旧数据 | 回滚的是 Release 记录，PV 数据不回滚 | 数据库先备份 |

::: warning 生产红线
Chart 版本与镜像 tag 都写死，values 里**禁用 latest**；`helm uninstall` 会删资源含 PV 绑定，卸载前先 history、先备份；含密码的 values 别提交 Git。
:::

## 官方文档

- Helm：<https://helm.sh/docs/>
- Chart 模板指南：<https://helm.sh/docs/chart_template_guide/>
- Kustomize：<https://kubectl.docs.kubernetes.io/references/kustomize/>
- Artifact Hub：<https://artifacthub.io/>

---

返回 [服务详解 · 容器与编排](/services/container/)。