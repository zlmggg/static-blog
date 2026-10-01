# kubectl 命令速查

> Kubernetes 常用命令速查表。深入概念和运维见 [K8s 系列指南](/guide/container-k8s-01-architecture-cluster)。
> 用法：右侧「本页目录」跳转，或 `Ctrl+K` 搜索。
> 提示：可设置别名 `alias k=kubectl`。

## 集群与节点

| 命令 | 说明 |
|---|---|
| [`kubectl cluster-info`](./cmd-kubectl/cluster) | 集群信息 |
| [`kubectl get nodes`](./cmd-kubectl/cluster) | 查看节点状态（-o wide 详情） |
| [`kubectl version`](./cmd-kubectl/cluster) | 客户端/服务端版本 |
| [`kubectl get componentstatuses`](./cmd-kubectl/cluster) | 控制面组件健康状态 |

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
| [`kubectl expose deploy 名 --port=80 --type=NodePort`](./cmd-kubectl/run) | 创建 Service |
| [`kubectl run 名 --image=镜像`](./cmd-kubectl/run) | 快速创建 Pod |

## 编辑、伸缩与删除

| 命令 | 说明 |
|---|---|
| [`kubectl edit deploy 名`](./cmd-kubectl/edit) | 直接编辑资源配置 |
| [`kubectl scale deploy 名 --replicas=3`](./cmd-kubectl/scale) | 手动扩缩容 |
| [`kubectl patch`](./cmd-kubectl/rollout-set) | 局部更新字段 |
| [`kubectl set image deploy 名 容器=新镜像`](./cmd-kubectl/rollout-set) | 更新镜像（滚动发布） |
| [`kubectl rollout status deploy 名`](./cmd-kubectl/rollout-set) | 查看发布状态 |
| [`kubectl rollout undo deploy 名`](./cmd-kubectl/rollout-set) | 回滚到上一版本 |
| [`kubectl delete pod 名`](./cmd-kubectl/delete) | 删除 Pod（会被控制器重建） |
| [`kubectl delete -f 文件.yaml`](./cmd-kubectl/delete) | 按清单删除资源 |
| [`kubectl delete svc 名`](./cmd-kubectl/delete) | 删除指定资源 |

## 调试与排障

| 命令 | 说明 |
|---|---|
| [`kubectl describe pod 名`](./cmd-kubectl/describe) | 查看详情和事件（排查调度/启动失败） |
| [`kubectl logs 名`](./cmd-kubectl/logs) | 查看 Pod 日志 |
| [`kubectl logs -f 名`](./cmd-kubectl/logs) | 实时跟踪日志 |
| [`kubectl logs 名 -c 容器名`](./cmd-kubectl/logs) | 多容器 Pod 指定容器 |
| [`kubectl logs 名 --previous`](./cmd-kubectl/logs) | 查看上一个崩溃容器的日志 |
| [`kubectl exec -it 名 -- bash`](./cmd-kubectl/exec) | 进入 Pod |
| [`kubectl port-forward pod/名 8080:80`](./cmd-kubectl/port-forward) | 本地端口转发到 Pod |
| [`kubectl cp 名:/文件 ./本地`](./cmd-kubectl/cp) | 复制文件 |
| [`kubectl top nodes/pods`](./cmd-kubectl/cluster) | 查看资源使用率（需 metrics-server） |
| [`kubectl get events --sort-by=.metadata.creationTimestamp`](./cmd-cloudnative/kubectl-advanced) | 按时间看集群事件 |

## 配置与上下文

| 命令 | 说明 |
|---|---|
| [`kubectl config get-contexts`](./cmd-kubectl/config) | 列出所有上下文（集群） |
| [`kubectl config current-context`](./cmd-kubectl/config) | 当前上下文 |
| [`kubectl config use-context 名`](./cmd-kubectl/config) | 切换上下文/集群 |
| [`kubectl config set-context --current --namespace=ns`](./cmd-kubectl/config) | 切换默认命名空间 |

## Helm

| 命令 | 说明 |
|---|---|
| [`helm repo add 名 地址`](./cmd-kubectl/helm) | 添加软件仓库 |
| [`helm repo update`](./cmd-kubectl/helm) | 更新仓库索引 |
| [`helm search repo 关键词`](./cmd-kubectl/helm) | 搜索 chart |
| [`helm install 名 chart`](./cmd-kubectl/helm) | 安装 chart |
| [`helm list`](./cmd-kubectl/helm) | 查看已安装 release |
| [`helm upgrade 名 chart`](./cmd-kubectl/helm) | 升级 |
| [`helm uninstall 名`](./cmd-kubectl/helm) | 卸载 |
