---
category: 容器
difficulty: 初级
date: 2024-04-08
---

# ImagePullBackOff 排障（2024-04-08）

## 现象

新发布的 Pod 一直起不来，卡在镜像拉取：

```text
kubectl get pods
NAME                     READY   STATUS             RESTARTS   AGE
api-v2-5f9c8d7b4-x9m2n   0/1     ImagePullBackOff   0          8m
```

describe 看事件：

```text
Warning  Failed   Failed to pull image "harbor.internal/proj/api:v2.1.0":
  rpc error: code = NotFound desc = manifest unknown: manifest unknown
Warning  Failed   Error: ImagePullBackOff
```

## 环境

| 组件 | 版本 |
|---|---|
| Kubernetes | 1.29.2 |
| 容器运行时 | containerd 1.7.12 |
| 镜像仓库 | 公司 Harbor（harbor.internal） |
| 镜像地址 | harbor.internal/proj/api:v2.1.0 |

## 定位过程

### 1. describe 看具体拉取错误

```bash
kubectl describe pod api-v2-5f9c8d7b4-x9m2n | grep -A3 Events
```

按报错关键词分类：

| 报错关键词 | 根因 |
|---|---|
| `manifest unknown` / `not found` | tag 不存在 / 镜像地址拼错 |
| `denied: unauthorized` / `authentication required` | 没配 imagePullSecrets |
| `dial tcp ... timeout` | 网络到仓库不通 |
| `http: server gave HTTP response` | 仓库是 HTTP，containerd 没加白名单 |

### 2. 本次：manifest unknown（tag 不存在）

报错 `manifest unknown` 最常见原因：

- tag `v2.1.0` 在 Harbor 里**根本不存在**（打错了，或者 CI 还没 push 上去）。
- 镜像地址 project 路径写错。

去 Harbor 控制台确认该 tag 是否存在，或在节点上手动拉：

```bash
# 在节点上用 crictl 手动拉，复现同样错误
crictl pull harbor.internal/proj/api:v2.1.0
# 同样报 manifest unknown → 确认是 tag 问题
```

### 3. 认证类：私有仓库没配 imagePullSecrets

如果报错是 `unauthorized`，说明 Pod 没带仓库凭证：

```bash
# 先确认节点上能不能手动 docker/crictl login 拉
crictl pull harbor.internal/proj/api:v2.1.0
# 节点手动能拉、k8s 拉不到 → 是 Pod 没配 imagePullSecrets
```

检查 Pod 用的 ServiceAccount 或 Deployment 有没有 imagePullSecrets：

```bash
kubectl get deploy api-v2 -o yaml | grep -A3 imagePullSecrets
```

### 4. 网络/HTTP 类

```bash
# 节点上测到仓库连通
curl -k -I https://harbor.internal/v2/ --max-time 5
# containerd 配置 HTTP 仓库：/etc/containerd/config.toml 里配置 hosts
```

## 根因

| 层级 | 说明 |
|---|---|
| 直接原因 | 发布用的 tag `v2.1.0` 在 Harbor 上不存在（CI 构建失败/打错 tag） |
| 流程原因 | CD 流水线没校验镜像是否存在就触发部署 |

## 解决步骤

### 止血

1. 确认正确 tag：去 Harbor 看实际推上去的是哪个 tag，或重新触发 CI 构建。

```bash
# 改 Deployment 用确认存在的 tag
kubectl set image deploy/api-v2 api=harbor.internal/proj/api:v2.0.9
# 或修正为正确 tag
kubectl set image deploy/api-v2 api=harbor.internal/proj/api:v2.1.0
```

2. 如果是认证问题，先建 dockerconfigjson secret 并挂到 ServiceAccount：

```bash
kubectl create secret docker-registry harbor-pull-secret \
  --docker-server=harbor.internal \
  --docker-username=ci-puller \
  --docker-password='xxx' \
  -n prod

# 挂到 default serviceaccount（该命名空间下 Pod 自动用）
kubectl patch serviceaccount default -p \
  "{\"imagePullSecrets\":[{\"name\":\"harbor-pull-secret\"}]}" -n prod
```

### 根治

1. CD 流水线加前置校验：部署前先确认 manifest 存在，不存在就失败不部署。

2. 私有仓库统一用 pull secret 挂在 namespace default SA，避免每个 Deployment 重复配。

3. 镜像 tag 规范：优先用不可变 tag（git sha），避免 `latest` 漂移。

## 验证与预防

```bash
kubectl get pod                # 镜像拉取成功，进入 Running
crictl pull <image>            # 节点手动拉通
```

- 监控：ImagePullBackOff 事件告警。
- 规范：CD 流水线校验镜像存在；私有仓库用 imagePullSecrets；不用 latest tag。
- 排障套路：先 describe 看报错关键词，归类后对症。

## 相关

- 命令速查：[kubectl 命令速查](/reference/kubectl-commands) ｜ [云原生排障命令速查](/reference/cloudnative-commands) ｜ [Docker 命令速查](/reference/docker-commands)
- 同组短文：[Pod Pending](/cases/t-k8s-pod-pending) ｜ [CrashLoopBackOff](/cases/t-k8s-crashloopbackoff) ｜ [节点 NotReady](/cases/t-k8s-node-notready)
