---
title: "kubectl 工作负载与弹性速查：Job、CronJob、HPA、PDB"
description: "本文是 kubectl 命令速查 中「工作负载与弹性」的详解。控制器原理见 K8s Pod 与控制器。 官方文档：Job ｜ CronJob ｜ HPA ｜ PDB"
---
# kubectl 工作负载与弹性速查：Job、CronJob、HPA、PDB

> 本文是 [kubectl 命令速查](../kubectl-commands#工作负载与弹性) 中「工作负载与弹性」的详解。控制器原理见 [K8s Pod 与控制器](/guide/container-k8s-02-pod-service-discovery)。
>
> 官方文档：[Job](https://kubernetes.io/docs/concepts/workloads/controllers/job/) ｜ [CronJob](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/) ｜ [HPA](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/) ｜ [PDB](https://kubernetes.io/docs/concepts/workloads/pods/disruptions/)

## 一、Job：一次性任务

```bash
# 跑一个一次性 Pod，直到任务完成
kubectl create job hello --image=busybox:1.36 -- sh -c "echo hello && sleep 5"

# 从 CronJob 手动触发一次（补跑/验证常用）
kubectl create job --from=cronjob/nightly-backup nightly-backup-manual

kubectl get jobs
kubectl describe job hello          # 看 Conditions、Events、失败原因
kubectl logs job/hello              # 看任务输出
kubectl delete job hello
```

关键字段：

| 字段 | 作用 |
|---|---|
| `backoffLimit` | 失败重试次数，默认 6 |
| `activeDeadlineSeconds` | 整个 Job 的超时时间 |
| `completions` / `parallelism` | 需要成功几次 / 并发几个 Pod |
| `ttlSecondsAfterFinished` | 完成后自动清理 Job 的秒数 |

## 二、CronJob：定时任务

```bash
kubectl create cronjob nightly-backup \
  --image=busybox:1.36 \
  --schedule="0 2 * * *" \
  -- sh -c "date; echo backup"

kubectl get cronjobs
kubectl describe cronjob nightly-backup
kubectl get jobs --watch            # 看它每次生成的 Job
```

| 操作 | 命令 |
|---|---|
| 暂停 | `kubectl patch cronjob nightly-backup -p '{"spec":{"suspend":true}}'` |
| 恢复 | `kubectl patch cronjob nightly-backup -p '{"spec":{"suspend":false}}'` |
| 立即触发 | `kubectl create job --from=cronjob/nightly-backup manual-$(date +%s)` |
| 看历史 Job | `kubectl get jobs -l ...`（按 CronJob 生成的标签过滤） |

注意：CronJob 的 `schedule` 使用集群控制器所在时区；需要固定时区时显式设置 `spec.timeZone`（K8s 1.27+）。

## 三、HPA：自动扩缩容

```bash
# 基于 CPU 使用率自动扩缩（需要 metrics-server）
kubectl autoscale deployment web --min=2 --max=10 --cpu-percent=70

kubectl get hpa
kubectl describe hpa web            # 看当前指标、事件、扩缩决策
kubectl get hpa web -o yaml
```

HPA 不生效的常见原因：

1. 没装 `metrics-server`，`kubectl top` 也没数据。
2. Deployment 没写 `resources.requests`，HPA 算不出利用率。
3. 指标已到 `maxReplicas`，或节点资源不足调度。
4. 刚改完 HPA 需要等一个采集周期（默认 15s 左右）。

## 四、PDB：发布/驱逐时的可用性保护

```bash
kubectl get pdb -A
kubectl describe pdb web-pdb
```

| 字段 | 含义 |
|---|---|
| `minAvailable` | 至少保留几个可用副本（数字或百分比） |
| `maxUnavailable` | 最多允许几个不可用 |
| `selector` | 保护哪组 Pod |

`kubectl drain` 前先看 PDB，否则可能卡住驱逐；PDB 太严（如 `minAvailable: 100%`）会让节点永远排不空。

## 五、排障顺序

**Job 一直不完成：**

```bash
kubectl describe job 名          # 看 Events、Pod 状态、BackoffLimitExceeded
kubectl get pods -l job-name=名
kubectl logs pod/名              # 看任务本身报错
```

**CronJob 不触发：**

```bash
kubectl get cronjob 名 -o yaml   # 看 suspend、schedule、lastScheduleTime
kubectl describe cronjob 名      # 看 Events
```

**HPA 不扩容：**

```bash
kubectl top pods                 # 指标是否有数据
kubectl describe hpa 名          # 看 Metrics 与 Conditions
kubectl get deploy 名 -o yaml    # 看 requests/limits
```

## 六、官方文档与相关

- Job：https://kubernetes.io/docs/concepts/workloads/controllers/job/
- CronJob：https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/
- HPA：https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/
- PDB 与干扰预算：https://kubernetes.io/docs/concepts/workloads/pods/disruptions/
- kubectl 命令参考：https://kubernetes.io/docs/reference/kubectl/
- 速查页：[kubectl 命令速查](../kubectl-commands#工作负载与弹性)
- 资源查看与排障：[kubectl get](./get) ｜ [describe](./describe) ｜ [logs](./logs)
- 节点维护：[节点维护与驱逐](./node-maintenance)
