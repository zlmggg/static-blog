---
category: 容器
difficulty: 中级
date: 2023-08-30
---

# Pod CrashLoopBackOff 排障（2023-08-30）

## 现象

发布后 Pod 起来又挂、挂了又拉起，反复重启：

```text
kubectl get pods
NAME                     READY   STATUS             RESTARTS     AGE
myapp-7d9f6b8c5-abcde    0/1     CrashLoopBackOff   12 (65s ago)  15m
```

RESTARTS 计数不断涨，状态在 `Running → Error → CrashLoopBackOff` 之间循环。

## 环境

| 组件 | 版本 |
|---|---|
| Kubernetes | 1.27.4 |
| 容器运行时 | containerd 1.7.3 |
| 应用 | Spring Boot Jar 包镜像 |
| 探针配置 | 刚加了 livenessProbe |

## 定位过程

### 1. 看容器日志

```bash
# 当前容器日志
kubectl logs myapp-7d9f6b8c5-abcde

# 如果容器已经挂了看不到，看上一次崩溃前的日志
kubectl logs myapp-7d9f6b8c5-abcde --previous
```

`--previous` 是关键——很多人只看当前日志，容器已经重启，当前日志是空的。

### 2. describe 看退出码与事件

```bash
kubectl describe pod myapp-7d9f6b8c5-abcde | tail -25
```

看 `Last State` 与 `Exit Code`：

```text
Last State:     Terminated
  Reason:       Error
  Exit Code:    1
  Started:      ...
  Finished:     ...
```

常见 Exit Code 含义：

| Exit Code | 含义 |
|---|---|
| 0 | 正常退出（但不该退出，说明主进程跑完就结束了） |
| 1 | 应用内部错误（看日志栈） |
| 137 | 被 SIGKILL，通常是 OOMKilled（见 [OOMKilled](/cases/t-k8s-oomkilled)） |
| 143 | 被 SIGTERM 正常终止 |
| 139 | 段错误 |

### 3. CrashLoopBackOff 常见原因对照表

| 原因 | 特征 | 排查 |
|---|---|---|
| 启动命令/参数错 | 日志报 command not found / 配置找不到 | 看 CMD/ENTRYPOINT |
| 探针误杀 | 应用启动慢，liveness 太早杀 | 看 startupProbe/liveness 配置 |
| 依赖没就绪 | 连不上 DB/Redis 直接退出 | 日志里连不上下游 |
| 配置/Secret 缺失 | 报环境变量/配置文件不存在 | 查 ConfigMap/Secret |
| 内存不足被 OOM | Exit Code 137 | describe 看 Reason=OOMKilled |

### 4. 本次实际：liveness 探针太早杀

日志显示应用其实在正常启动（Spring Boot 要 60s 才起来），但 describe 里：

```text
Warning  Unhealthy  Liveness probe failed: HTTP probe failed with statuscode: 503
Warning  Killing     Liveness failed, killing container
```

刚加的 livenessProbe 没设 `initialDelaySeconds`，容器一启动 10s 就开始探活，应用还没起来返回 503，被判定不健康杀掉——越杀越重启，越重启越起不来。

## 根因

| 层级 | 说明 |
|---|---|
| 直接原因 | livenessProbe 初始延迟太短，Spring Boot 慢启动期间被探针误杀 |
| 流程原因 | 加探针时没在预发验证慢启动场景 |

## 解决步骤

### 止血

1. 先临时删掉 livenessProbe，让 Pod 能起来：

```bash
kubectl edit deploy myapp
# 注释掉 livenessProbe 段，观察 Pod 正常 Running
```

### 根治

1. 用 **startupProbe** 专门管慢启动，启动期间不做 liveness 判定：

```yaml
readinessProbe:
  httpGet: { path: /actuator/health/readiness, port: 8080 }
  initialDelaySeconds: 10
  periodSeconds: 5
  failureThreshold: 12

# 启动探针：在它成功前，liveness/readiness 都不生效
startupProbe:
  httpGet: { path: /actuator/health/liveness, port: 8080 }
  periodSeconds: 5
  failureThreshold: 30        # 最多等 5*30=150s 启动

livenessProbe:
  httpGet: { path: /actuator/health/liveness, port: 8080 }
  periodSeconds: 10
  failureThreshold: 3
```

2. 区分 readiness（没就绪不接流量，但不杀容器）和 liveness（真死了才杀）。

3. 启动慢的应用在镜像里做 JVM 预热优化，缩短启动时间。

## 验证与预防

```bash
kubectl get pod -w          # 应 Running 且 RESTARTS 不涨
kubectl describe pod <pod>  # 探针正常通过
```

- 规范：慢启动应用必须配 startupProbe；liveness 不要设过短。
- 排障套路：`logs --previous` 看上次崩溃日志 + describe 看 Exit Code/Reason。
- 预发：所有探针变更先在预发观察完整启动周期。

## 相关

- 命令速查：[kubectl 命令速查](/reference/kubectl-commands) ｜ [云原生排障命令速查](/reference/cloudnative-commands)
- 同组短文：[Pod Pending](/cases/t-k8s-pod-pending) ｜ [OOMKilled](/cases/t-k8s-oomkilled) ｜ [ImagePullBackOff](/cases/t-k8s-imagepullbackoff)
