---
title: "kubectl 命令速查"
description: "Kubernetes 常用命令速查表。深入概念和运维见 K8s 系列指南。 用法：右侧「本页目录」跳转，或 Ctrl+K 搜索。 提示：可设置别名 alias k=kubectl。"
---
# kubectl 命令速查

> Kubernetes 常用命令速查表。深入概念和运维见 [K8s 系列指南](/services/container/kubernetes/01-理论)。
> 用法：右侧「本页目录」跳转，或 `Ctrl+K` 搜索。
> 提示：可设置别名 `alias k=kubectl`。

## 集群与节点

| 命令 | 说明 |
|---|---|
| `kubectl cluster-info` | 集群信息 |
| `kubectl get nodes` | 查看节点状态（-o wide 详情） |
| `kubectl version` | 客户端/服务端版本 |
| `kubectl get componentstatuses` | 控制面组件健康状态 |

## 资源查看

| 命令 | 说明 |
|---|---|
| [`kubectl get pods`](./cmd-kubectl/get) | 查看 Pod（默认 default 命名空间） |
| [`kubectl get pods -A`](./cmd-kubectl/get) | 所有命名空间的 Pod（--all-namespaces） |
| [`kubectl get pods -o wide`](./cmd-kubectl/get) | 显示 Pod IP、所在节点 |
| [`kubectl get svc,deploy,ingress`](./cmd-kubectl/get) | 同时查看多种资源 |
| [`kubectl get all`](./cmd-kubectl/get) | 查看常用全部资源 |
| [`kubectl get pods -n 命名空间`](./cmd-kubectl/get) | 指定命名空间 |
| [`kubectl get pods -w`](./cmd-kubectl/get) | 持续监听变化（watch） |
| [`kubectl get pod 名称 -o yaml`](./cmd-kubectl/get) | 导出 YAML 配置 |
| [`kubectl get pods --show-labels`](./cmd-kubectl/get) | 显示标签 |

**常用资源缩写：** `po`(pod)、`svc`(service)、`deploy`(deployment)、`ing`(ingress)、`cm`(configmap)、`secret`、`ns`(namespace)、`pv/pvc`、`sts`(statefulset)、`ds`(daemonset)。

## 创建与应用

| 命令 | 说明 |
|---|---|
| [`kubectl apply -f 文件.yaml`](./cmd-kubectl/apply-create) | 声明式创建/更新资源（最常用） |
| [`kubectl apply -f 目录/`](./cmd-kubectl/apply-create) | 应用目录下所有清单 |
| [`kubectl create deployment 名 --image=镜像`](./cmd-kubectl/apply-create) | 命令式创建部署 |
| `kubectl expose deploy 名 --port=80 --type=NodePort` | 创建 Service |
| `kubectl run 名 --image=镜像` | 快速创建 Pod |

## 编辑、伸缩与删除

| 命令 | 说明 |
|---|---|
| `kubectl edit deploy 名` | 直接编辑资源配置 |
| `kubectl scale deploy 名 --replicas=3` | 手动扩缩容 |
| `kubectl patch` | 局部更新字段 |
| `kubectl set image deploy 名 容器=新镜像` | 更新镜像（滚动发布） |
| `kubectl rollout status deploy 名` | 查看发布状态 |
| `kubectl rollout undo deploy 名` | 回滚到上一版本 |
| `kubectl delete pod 名` | 删除 Pod（会被控制器重建） |
| `kubectl delete -f 文件.yaml` | 按清单删除资源 |
| `kubectl delete svc 名` | 删除指定资源 |
| `kubectl label / annotate` | 给资源打标签/注解，按标签筛选、变更触发 |

## 节点维护与权限

| 命令 | 说明 |
|---|---|
| `kubectl cordon 节点` | 标记不可调度（已有 Pod 不动） |
| `kubectl drain 节点 --ignore-daemonsets --delete-emptydir-data` | 驱逐节点上的 Pod（升级/维护前） |
| `kubectl uncordon 节点` | 恢复可调度 |
| `kubectl taint nodes 节点 key=value:NoSchedule` | 打污点，阻止普通 Pod 调度 |
| `kubectl taint nodes 节点 key=value:NoSchedule-` | 去掉污点（末尾减号） |
| `kubectl auth can-i create pods` | 检查当前账号权限 |
| `kubectl auth can-i --list` | 列出自己所有被允许的动作 |
| `kubectl get pdb -A` | 驱逐前确认可用性预算 |

> 维护顺序：`cordon → drain → 升级/维护 → uncordon`，drain 前先看 PDB 与副本冗余。详见 节点维护详解。

## 工作负载与弹性

| 命令 | 说明 |
|---|---|
| `kubectl create job 名 --image=镜像 -- 命令` | 创建一次性 Job |
| `kubectl create job --from=cronjob/名 新名` | 手动触发一次 CronJob |
| `kubectl get jobs / cronjobs` | 查看任务状态 |
| `kubectl logs job/名` | 看任务输出 |
| `kubectl autoscale deploy 名 --min=2 --max=10 --cpu-percent=70` | 创建 HPA 自动扩缩 |
| `kubectl get hpa` / `describe hpa 名` | 看当前指标与扩缩决策 |
| `kubectl get pdb -A` | 看 PodDisruptionBudget |

## 调试与排障

| 命令 | 说明 |
|---|---|
| [`kubectl describe pod 名`](./cmd-kubectl/describe) | 查看详情和事件（排查调度/启动失败） |
| [`kubectl logs 名`](./cmd-kubectl/logs) | 查看 Pod 日志 |
| [`kubectl logs -f 名`](./cmd-kubectl/logs) | 实时跟踪日志 |
| [`kubectl logs 名 -c 容器名`](./cmd-kubectl/logs) | 多容器 Pod 指定容器 |
| [`kubectl logs 名 --previous`](./cmd-kubectl/logs) | 查看上一个崩溃容器的日志 |
| `kubectl exec -it 名 -- bash` | 进入 Pod |
| `kubectl port-forward pod/名 8080:80` | 本地端口转发到 Pod |
| `kubectl cp 名:/文件 ./本地` | 复制文件 |
| `kubectl top nodes/pods` | 查看资源使用率（需 metrics-server） |
| [`kubectl get events --sort-by=.metadata.creationTimestamp`](./cmd-cloudnative/kubectl-advanced) | 按时间看集群事件 |

## 配置与上下文

| 命令 | 说明 |
|---|---|
| `kubectl config get-contexts` | 列出所有上下文（集群） |
| `kubectl config current-context` | 当前上下文 |
| `kubectl config use-context 名` | 切换上下文/集群 |
| `kubectl config set-context --current --namespace=ns` | 切换默认命名空间 |

## Helm

| 命令 | 说明 |
|---|---|
| `helm repo add 名 地址` | 添加软件仓库 |
| `helm repo update` | 更新仓库索引 |
| `helm search repo 关键词` | 搜索 chart |
| `helm install 名 chart` | 安装 chart |
| `helm list` | 查看已安装 release |
| `helm upgrade 名 chart` | 升级 |
| `helm uninstall 名` | 卸载 |

<!-- merged-command-pitfalls:start -->
## 命令坑点索引

> 原先逐条拆开的单命令详解已合并到本手册；下面只保留每条命令最容易踩的坑，完整选项和示例不再单独成页。
> 需要看某条命令的完整用法时，先在上方速查表找到它，再看本节对应行。

| 命令 | 最容易踩的坑 | 官方文档 |
|---|---|---|
| `Helm 基础` | 忘了 helm repo update：刚 add 完源直接 install 可能报 chart not found，先 update 索引。 | — |
| `kubectl auth` | 403 了别瞎改 Role：先 can-i 精确定位是哪个 Verb/资源缺权限，再去补 Role。 | — |
| `kubectl config` | 在错误的集群上操作：敲大命令前先 current-context 确认连的是 dev 还是 prod。 | — |
| `kubectl cp` | 容器里没 tar 会失败：报 tar 相关错误时，先 kubectl exec pod -- which tar 确认；没有就用 exec+tar 方案或换带 tar 的镜像。 | — |
| `kubectl delete` | 删 Pod 不等于删服务：由 Deployment/RS 管的 Pod 删了会被重建；要真停服务得删 Deployment。 | — |
| `kubectl edit` | 改完没同步回 YAML：edit 直接改了活对象，但仓库里的清单没变；下次 apply -f 会把 edit 的内容冲掉。 | — |
| `kubectl exec` | 忘了 --：kubectl exec mypod bash 可能把 bash 当成 kubectl 自己的参数报错；容器命令前一定加 --。 | — |
| `kubectl port-forward` | 命令前台挂着别关：port-forward 是前台进程，关了终端就断；要长期挂着用 nohup 或开 tmux。 | — |
| `kubectl run` | run 起的是裸 Pod，不是 Deployment：裸 Pod 挂了不会自愈、没有滚动更新；正经服务用 create deployment / apply。 | — |
| `kubectl scale` | 被 HPA 接管后手动 scale 不生效：你改成 5，HPA 看 CPU 低又给你缩回去；先删 HPA。 | — |
| `kubectl 工作负载与弹性速查` | 原页没有独立坑点段，待补。 | — |
| `kubectl 节点维护速查` | 原页没有独立坑点段，待补。 | — |
| `label 与 annotate` | 改已有值忘了 --overwrite：直接报错；改值一定加。 | — |
| `rollout / set / patch` | set image 后不看 status：发版可能卡住（镜像拉不下来、探针失败），发完一定 rollout status。 | — |
| `集群与节点` | kubectl top 报错不是你命令写错：报 Metrics API not available 是集群没装 metrics-server，先装它（或用 kubectl describe nodes 看 requests/limits 间接估算）。 | — |

<!-- merged-command-pitfalls:end -->

## 相关问答

- Pod、Service、发布与节点排障：[容器与 Kubernetes 问题](/guide/container#常见问题-faq)

## 官方文档

- kubectl 命令参考：https://kubernetes.io/docs/reference/kubectl/
- kubectl 速查表：https://kubernetes.io/docs/reference/kubectl/quick-reference/
- Job / CronJob：https://kubernetes.io/docs/concepts/workloads/controllers/
- HPA：https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/
- 节点驱逐：https://kubernetes.io/docs/tasks/administer-cluster/safely-drain-node/
- RBAC：https://kubernetes.io/docs/reference/access-authn-authz/rbac/
- Helm：https://helm.sh/docs/
