---
category: 容器
difficulty: 初级
date: 2023-07-25
---

# Pod 一直 Pending 排障（2023-07-25）

## 现象

发布新服务后，Pod 一直停在 `Pending` 状态，半天起不来：

```text
kubectl get pods
NAME                     READY   STATUS    RESTARTS   AGE
myapp-6f9c8b7d5-x2k9p    0/1     Pending   0          10m
```

`kubectl describe pod` 最后几行 Events 有原因。

## 环境

| 组件 | 版本 |
|---|---|
| Kubernetes | 1.27.4（kubeadm 集群，3 master + 5 worker） |
| CNI | Calico 3.26 |
| 容器运行时 | containerd 1.7.3 |
| 问题 Pod | 申请 `requests.cpu=4, memory=8Gi` |

## 定位过程

### 1. describe Pod 看调度事件

```bash
kubectl describe pod myapp-6f9c8b7d5-x2k9p | tail -30
```

Events 是关键。Pending 的原因几乎都写在这里：

```text
Events:
  Type     Reason            Message
  ----     ------            -------
  Warning  FailedScheduling  0/8 nodes are available:
           3 Insufficient cpu,
           2 node(s) had taint {node-role.kubernetes.io/control-plane:},
           3 node(s) had volume node affinity conflict.
```

一次列出所有不可调度原因，按概率逐个查。

### 2. 常见 Pending 原因对照表

| Events 关键词 | 根因 | 排查/解决 |
|---|---|---|
| `Insufficient cpu/memory` | 节点资源不够 | 看节点余量，降 requests 或加节点 |
| `had taint ... not tolerated` | 节点有污点，Pod 没容忍 | 加 toleration 或换节点 |
| `node affinity mismatch` | 亲和性选不中节点 | 看 nodeSelector/affinity |
| `pod has unbound immediate PersistentVolumeClaims` | PVC 没绑定上 | 查 PVC/PV/StorageClass |
| `1 node(s) were excluded` | 端口/资源冲突 | 看 hostPort 等 |

### 3. 本次：Insufficient cpu + PVC 亲和冲突

先看节点资源余量：

```bash
kubectl top nodes
kubectl describe nodes | grep -A5 "Allocated resources"
```

发现 5 个 worker 的可分配 CPU 都已被占满（其他大 Pod 占着），新 Pod 要 4 核没节点给得起。

再看 PVC：

```bash
kubectl get pvc
# STATUS 是 Pending 还是 Bound
kubectl describe pvc <pvc-name>
# Events: waiting for a volume to be created... volume node affinity conflict
```

`volume node affinity conflict`：PVC 绑定的 PV 是**某可用区本地盘**，但 Pod 被调度到别的可用区节点， affinity 冲突。

### 4. 看污点/亲和

```bash
# 节点污点
kubectl describe node worker-1 | grep Taints
# 输出：Taints: <none> 或 node-role/control-plane:NoSchedule
```

## 根因

| 层级 | 说明 |
|---|---|
| 直接原因 | 集群可分配 CPU 不足 + 本地盘 PVC 与调度节点跨可用区亲和冲突 |
| 容量原因 | 业务增长后没及时扩 worker 节点 |
| 存储原因 | 用了本地 PV，绑死了可用区，调度范围被限制 |

## 解决步骤

### 止血

1. 临时把 Pod 的 requests 调小，先挤进去跑起来：

```bash
kubectl scale deploy myapp --replicas=0   # 先缩到 0
# 编辑 deploy，把 requests.cpu 从 4 降到 2，再扩回来
kubectl edit deploy myapp
kubectl scale deploy myapp --replicas=3
```

2. 如果是本地盘 PVC 卡住，临时换一个同可用区节点的 PV，或用网络存储（StorageClass）替代本地盘。

### 根治

1. 扩容节点：给集群加 worker，资源水位控制在 70% 以下：

```bash
# kubeadm 节点加入流程略；云厂商则加节点池
kubectl get nodes
```

2. 规范 requests/limits：不要 requests 过大，按实际用量设（用 `kubectl top pod` 观测真实用量）。

3. 有状态服务用**网络存储 StorageClass**（如 ceph、云盘），不要绑死本地盘，避免调度亲和冲突。

## 验证与预防

```bash
kubectl get pod -o wide        # 应 Running 且分配到节点
kubectl describe pod <pod>     # Events 有 "Successfully assigned"
```

- 监控：节点资源分配率（CPU/内存 requests 占比）配告警，>80% 预警扩容。
- 规范：requests 按真实用量设；本地盘 StatefulSet 用 volumeBindingMode: WaitForFirstConsumer。
- 容量：大促前预估资源，提前扩节点。

## 相关

- 命令速查：[kubectl 命令速查](/reference/kubectl-commands) ｜ [云原生排障命令速查](/reference/cloudnative-commands)
- 同组短文：[CrashLoopBackOff](/cases/t-k8s-crashloopbackoff) ｜ [OOMKilled](/cases/t-k8s-oomkilled) ｜ [ImagePullBackOff](/cases/t-k8s-imagepullbackoff)
