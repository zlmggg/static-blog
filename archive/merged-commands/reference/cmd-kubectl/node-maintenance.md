---
title: "kubectl 节点维护速查：cordon、drain、taint"
description: "本文是 kubectl 命令速查 中「节点维护」的详解。节点升级、集群生命周期见 云原生排障命令速查。 官方文档：安全驱逐节点 ｜ 污点与容忍 ｜ 节点维护"
---
# kubectl 节点维护速查：cordon、drain、taint

> 本文是 [kubectl 命令速查](../kubectl-commands#节点维护与权限) 中「节点维护」的详解。节点升级、集群生命周期见 [云原生排障命令速查](../cloudnative-commands#集群生命周期与证书)。
>
> 官方文档：[安全驱逐节点](https://kubernetes.io/docs/tasks/administer-cluster/safely-drain-node/) ｜ [污点与容忍](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/) ｜ [节点维护](https://kubernetes.io/docs/concepts/architecture/nodes/)

## 一、三个动作的区别

| 命令 | 作用 | 影响 |
|---|---|---|
| `kubectl cordon 节点` | 标记不可调度 | 新 Pod 不再调度上来，已有 Pod 继续跑 |
| `kubectl drain 节点` | 驱逐节点上可驱逐的 Pod | 会真正停止并迁移 Pod，服务可能短暂抖动 |
| `kubectl uncordon 节点` | 恢复可调度 | 新 Pod 可以重新调度上来 |

## 二、标准维护流程

```bash
kubectl get nodes -o wide                  # 1. 确认节点状态与版本
kubectl get pods -A -o wide --field-selector spec.nodeName=节点名   # 2. 看上面有哪些 Pod
kubectl get pdb -A                         # 3. 确认驱逐不会破坏可用性预算
kubectl cordon 节点                         # 4. 先停止新调度
kubectl drain 节点 \
  --ignore-daemonsets \
  --delete-emptydir-data \
  --timeout=10m                            # 5. 驱逐
# 6. 维护/升级 kubelet、容器运行时、内核
kubectl uncordon 节点                       # 7. 恢复调度
kubectl get nodes                          # 8. 确认 Ready
```

常用 `drain` 参数：

| 参数 | 作用 |
|---|---|
| `--ignore-daemonsets` | 忽略 DaemonSet Pod（它们本来就不该被驱逐） |
| `--delete-emptydir-data` | 允许删除使用 emptyDir 的 Pod（数据会丢） |
| `--force` | 驱逐没有控制器的裸 Pod（危险，确认后再用） |
| `--timeout` | 超时时间，避免无限等待 |
| `--dry-run=client` | 只打印会做什么，不实际执行 |

## 三、污点（taint）与容忍

```bash
# 查看节点污点
kubectl describe node 节点名 | grep Taints
kubectl get node 节点名 -o jsonpath='{.spec.taints}'

# 打污点：禁止普通 Pod 调度
kubectl taint nodes 节点名 maintenance=true:NoSchedule

# 去掉污点（末尾加 -）
kubectl taint nodes 节点名 maintenance=true:NoSchedule-

# 只影响新调度，不驱逐已有 Pod；要驱赶用 NoExecute
kubectl taint nodes 节点名 maintenance=true:NoExecute
```

三种 effect：

| effect | 对已有 Pod | 对新 Pod |
|---|---|---|
| `NoSchedule` | 不影响 | 不容忍则不调度 |
| `PreferNoSchedule` | 不影响 | 尽量不调度 |
| `NoExecute` | 不容忍会被驱逐 | 不容忍则不调度 |

## 四、驱逐卡住怎么查

| 现象 | 原因 | 处理 |
|---|---|---|
| `cannot evict pod as it would violate the pod's disruption budget` | PDB 不允许再少副本 | 临时调整 PDB，或等副本恢复 |
| 提示 DaemonSet Pod | 没加 `--ignore-daemonsets` | 加该参数 |
| 提示使用 emptyDir | 没加 `--delete-emptydir-data` | 确认数据可丢后加参数 |
| 裸 Pod 无法驱逐 | 没有控制器接管 | 确认后可 `--force`，或手动删 |
| 一直卡住不返回 | Pod 终止慢/有 finalizer | 看 `kubectl describe pod`，必要时加 `--timeout` |

## 五、节点 NotReady 的排查顺序

```bash
kubectl describe node 节点名          # Conditions：MemoryPressure/DiskPressure/PIDPressure
ssh 节点名 systemctl status kubelet    # kubelet 是否活着
ssh 节点名 journalctl -u kubelet -n 100 --no-pager
ssh 节点名 df -h && free -h && ss -lntp | grep 10250
```

常见根因：磁盘满、内存压力、容器运行时挂了、kubelet 证书过期、网络插件异常。

## 六、官方文档与相关

- 安全驱逐节点：https://kubernetes.io/docs/tasks/administer-cluster/safely-drain-node/
- 污点与容忍：https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/
- 节点概念：https://kubernetes.io/docs/concepts/architecture/nodes/
- 集群升级：https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-upgrade/
- 速查页：[kubectl 命令速查](../kubectl-commands#节点维护与权限)
- 工作负载与弹性：[Job/CronJob/HPA/PDB](./workloads)
- 集群生命周期：[云原生排障命令速查](../cloudnative-commands#集群生命周期与证书)
