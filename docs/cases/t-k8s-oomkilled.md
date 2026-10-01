---
category: 容器
difficulty: 中级
date: 2024-02-14
---

# 容器 OOMKilled 排障（2024-02-14）

## 现象

一个数据处理 Pod 运行一段时间后被杀死，状态反复：

```text
kubectl get pods
NAME                    READY   STATUS      RESTARTS     AGE
batch-job-xxx           1/1     Running     8 (2m ago)   3h
```

describe 看到：

```text
Last State: Terminated
  Reason:   OOMKilled
  Exit Code: 137
```

监控上该容器内存曲线在被杀前一路涨到 limits 上限，然后被一刀切断。

## 环境

| 组件 | 版本 |
|---|---|
| Kubernetes | 1.29.2 |
| 容器运行时 | containerd 1.7.12 |
| Pod 资源限制 | `requests.memory=2Gi, limits.memory=4Gi` |
| 应用 | 批量导入任务，一次加载大数据集到内存 |

## 定位过程

### 1. 确认是 OOMKilled 而不是别的

```bash
kubectl describe pod batch-job-xxx | grep -A5 "Last State"
# Reason: OOMKilled  Exit Code: 137
```

Exit Code 137 = 128 + 9 (SIGKILL)，几乎都是 cgroup 内存超限被内核 OOM Killer 杀。

### 2. 区分是"容器超限"还是"节点整体内存压力"

两种 OOM 场景，处置完全不同：

| 场景 | 特征 | 看哪里 |
|---|---|---|
| 容器自己超 limits | 该容器内存涨到 limits 被杀，节点还有富余 | describe 该 Pod |
| 节点内存压力（Eviction） | 节点整体内存紧张，kubelet 全局驱逐 Pod | 节点 events / kubelet 日志 |

```bash
# 看节点是否处于内存压力
kubectl describe node worker-1 | grep -A5 "Conditions"
# MemoryPressure: True 说明节点整体吃紧

# 看节点上被驱逐的事件
kubectl get events --field-selector reason=Evicted
```

本次节点内存还有富余，是**容器自己超了 4Gi limits**。

### 3. 看容器内存真实用量

```bash
# 实时看 Pod 内存
kubectl top pod batch-job-xxx --containers
```

输出：

```text
POD            NAME          CPU(cores)   MEMORY(bytes)
batch-job-xxx  batch-job     1200m        3890Mi
```

快到 4Gi 上限了。

### 4. 找内存泄漏点

进入容器抓现场（在它被杀前复现）：

```bash
# 看进程内存排行
kubectl exec -it batch-job-xxx -- sh -c "ps aux --sort=-rss | head"
# JVM 应用看堆配置
kubectl exec -it batch-job-xxx -- jmap -heap 1
```

发现 JVM 没设 `-Xmx`，默认按容器内存的 1/4 还是宿主机内存算？JVM 8u131+ 支持容器感知，但镜像里用的 JVM 版本没开 `UseCGroupMemoryLimitForHeap`，导致堆直接用了宿主机内存大小，瞬间冲破容器 limits。

## 根因

| 层级 | 说明 |
|---|---|
| 直接原因 | JVM 堆未按容器 limits 限制，实际使用内存超过 cgroup 4Gi 上限，被 OOM Killer 杀 |
| 配置原因 | 没设 `-Xmx`，JVM 误判可用内存 |
| 业务原因 | 批量任务一次加载太多数据进内存，本就该分批流式处理 |

## 解决步骤

### 止血

1. 临时调大 limits，先让任务跑完：

```bash
kubectl set resources deploy/batch-job --limits=memory=8Gi --requests=memory=2Gi
```

2. 如果是节点内存压力（Eviction）导致的，先驱逐/疏散节点上其他 Pod，给当前 Pod 腾地方。

### 根治

1. JVM 应用必须显式设堆，且留足堆外/元空间余量：

```dockerfile
# Dockerfile
ENV JAVA_OPTS="-Xms1g -Xmx3g -XX:MaxMetaspaceSize=256m"
# limits.memory=4Gi：Xmx=3g 留 1G 给 metaspace/堆外/线程栈，安全
```

> 经验值：`Xmx ≈ limits.memory × 70%`，剩下 30% 给堆外、Metaspace、JIT 等。

2. 大批量任务改成**流式/分批处理**，不要一次把全量数据 load 进内存：

```text
错误：一次性 SELECT 100 万行 List 进内存
正确：游标/分页流式读，边读边处理边写
```

3. 确认 limits 要比 requests 合理（一般 limits 是 requests 的 1~2 倍），不要 limits 设得比真实用量小太多导致频繁 OOM。

## 验证与预防

```bash
kubectl top pod <pod>          # 内存稳定在 limits 以内
kubectl get pod                # RESTARTS 不再增长（无 OOMKilled）
```

- 监控：容器内存用量/limits 比值告警（>80%）；OOMKilled 事件告警。
- 规范：所有 JVM 容器显式设 `-Xmx`；大任务流式处理。
- 容量：按真实峰值设 limits，不要拍脑袋。

## 相关

- 命令速查：[kubectl 命令速查](/reference/kubectl-commands) ｜ [Linux 命令速查](/reference/linux-commands)
- 同组短文：[CrashLoopBackOff](/cases/t-k8s-crashloopbackoff) ｜ [Pod Pending](/cases/t-k8s-pod-pending) ｜ [节点 NotReady](/cases/t-k8s-node-notready)
