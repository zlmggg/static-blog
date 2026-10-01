---
category: 容器
difficulty: 高级
date: 2025-01-15
---

# Service / Ingress 不通排障（2025-01-15）

## 现象

外部访问网站超时。集群内 Pod 互相访问 ClusterIP 也偶发不通。Service 已创建、后端 Pod 也 Running，但流量就是到不了容器。

```text
# 外部
curl -I https://api.example.com
curl: (28) Failed to connect: Connection timed out

# 集群内
kubectl exec debug -- curl -I http://my-svc.default.svc.cluster.local
# 连不上
```

## 环境

| 组件 | 版本 |
|---|---|
| Kubernetes | 1.31.1（kubeadm） |
| CNI / 网络 | Calico + kube-proxy（ipvs 模式） |
| Ingress | ingress-nginx controller（Controller 模式） |
| Service | `my-svc` ClusterIP，后端是 `my-app` 的 Pod |

## 定位过程

### 1. 分层排查：从外到内逐层定位

K8s 网络是多层的，按这个顺序逐层测：

| 层级 | 命令 | 不通说明 |
|---|---|---|
| ① Pod 直接访问 | `kubectl exec <pod> -- curl localhost:8080` | 应用本身没起来 |
| ② 同节点另一 Pod 访问 PodIP | `curl <PodIP>:8080` | CNI 网络不通 |
| ③ 跨节点访问 PodIP | `curl <PodIP>:8080` | 跨节点路由/Calico 问题 |
| ④ ClusterIP 访问 | `curl <ClusterIP>` | kube-proxy/iptables 问题 |
| ⑤ Service DNS 解析 | `nslookup my-svc` | CoreDNS 问题 |
| ⑥ Ingress 访问 | `curl -H Host: xxx http://<ingress-ip>` | Ingress 规则问题 |

### 2. 第一步：看 Service 有没有正确选中 Endpoints

这是最常见的坑——Service selector 选不中 Pod，Endpoints 是空的：

```bash
kubectl get svc my-svc
kubectl get endpoints my-svc
```

如果 ENDPOINTS 列是 `<none>`，说明 selector 没匹配到任何 Pod：

```bash
# 对比 Service 的 selector 和 Pod 的 labels
kubectl get svc my-svc -o yaml | grep -A5 selector
kubectl get pods --show-labels
```

本次发现：Service selector 写的是 `app=my-app, version=v1`，但 Pod 实际 label 是 `app=my-app, version=v2`——**标签对不上**，Endpoints 为空。

### 3. Endpoints 正常但 ClusterIP 不通：查 kube-proxy

```bash
# 看 kube-proxy 是否正常
kubectl -n kube-system get pods | grep kube-proxy
# 在节点上看 ipvs 规则有没有这条 service
ipvsadm -ln | grep <ClusterIP>
```

### 4. Ingress 层：规则有没有配对

```bash
kubectl get ingress
kubectl describe ingress my-ingress
# 看 BACKEND 是不是正确的 service:port

# 看 ingress controller 日志
kubectl -n ingress-nginx logs deploy/ingress-nginx-controller --tail=50
```

常见 Ingress 坑：
- `host` 域名和实际访问域名对不上。
- `path` 路径和后端不匹配（`/api` vs `/api/`）。
- ingress-nginx 没安装/没监听。

## 根因

| 层级 | 说明 |
|---|---|
| 直接原因 | Service 的 selector 与后端 Pod labels 不一致，导致 Endpoints 为空，流量无后端可转发 |
| 流程原因 | 发布后改了 Pod label 但没同步改 Service selector |

## 解决步骤

### 止血

1. 修正 selector，让 Service 选中正确的 Pod：

```bash
kubectl edit svc my-svc
# selector:
#   app: my-app
#   version: v2      # 改成 Pod 实际的 label
```

2. 验证 Endpoints 立刻有了后端：

```bash
kubectl get endpoints my-svc
# 应显示 PodIP:port 列表
```

### 根治

1. 规范 label 管理：应用 label 与 Service selector 纳入 code review；推荐用 Helm/Kustomize 统一管理 label。

2. Ingress 排查时确认 host/path 与后端匹配，必要时用 curl 带 Host 头直连 ingress controller IP 定位：

```bash
curl -I -H "Host: api.example.com" http://<ingress-controller-ip>/healthz
```

3. 链路加就绪探针：Pod 没就绪不会进 Endpoints，避免流量打到还没准备好的容器。

## 验证与预防

```bash
kubectl get endpoints my-svc          # 非空
kubectl exec debug -- curl http://my-svc   # 通
curl -I https://api.example.com       # 外部通
```

- 监控：Service Endpoints 为空告警（选中后端数=0 时报警）。
- 排障套路：从 PodIP → ClusterIP → Ingress 逐层测，先看 Endpoints 再查 kube-proxy。
- 规范：label selector 变更要同步检查 Service。

## 相关

- 命令速查：[kubectl 命令速查](/reference/kubectl-commands) ｜ [云原生排障命令速查](/reference/cloudnative-commands) ｜ [网络命令速查](/reference/network-commands)
- 同组短文：[Pod Pending](/cases/t-k8s-pod-pending) ｜ [节点 NotReady](/cases/t-k8s-node-notready) ｜ [ImagePullBackOff](/cases/t-k8s-imagepullbackoff)
