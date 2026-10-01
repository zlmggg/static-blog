---
category: 容器
difficulty: 高级
date: 2025-03-10
---

# 节点 NotReady 排障（2025-03-10）

## 现象

集群里一个 worker 节点突然变成 NotReady，上面跑的 Pod 被驱逐，业务受损：

```text
kubectl get nodes
NAME        STATUS     ROLES    AGE   VERSION
worker-3    NotReady   worker   420d  v1.31.1
```

## 环境

| 组件 | 版本 |
|---|---|
| Kubernetes | 1.31.1（kubeadm） |
| 容器运行时 | containerd 1.7.18 |
| 节点 OS | Ubuntu 22.04 |
| 故障节点 | worker-3 |

## 定位过程

### 1. 看节点 Conditions，先知道是哪一类 NotReady

```bash
kubectl describe node worker-3 | grep -A20 Conditions
```

常见 Condition 异常对照：

| Condition 异常 | 根因方向 |
|---|---|
| `KubeletReady=False` | kubelet 挂了/没起来 |
| `MemoryPressure=True` | 节点内存吃紧 |
| `DiskPressure=True` | 磁盘满/inode 满 |
| `PIDPressure=True` | 进程数打满 |
| `NetworkUnavailable=True` | CNI 网络没起来 |

本次看到 `KubeletReady=False` 且 reason 是 `KubeletNotReady: runtime network not ready`——**容器运行时/CNI 出问题**。

### 2. 上节点查 kubelet 状态

```bash
ssh worker-3
systemctl status kubelet
journalctl -u kubelet --no-pager -n 80
```

### 3. 查容器运行时

```bash
systemctl status containerd
crictl ps        # 看能不能列容器
crictl info
```

### 4. 常见 NotReady 根因对照表

| kubelet 报错 | 根因 | 解决 |
|---|---|---|
| `failed to run Kubelet: misconfiguration` | kubelet 配置错 | 看 /var/lib/kubelet/config.yaml |
| `runtime network not ready: NetworkReady=false` | CNI 插件没装/Pod 网段没配 | 查 CNI |
| `disk usage on / is 95%` | 磁盘满 | 清理磁盘（见 [Docker 存储](/cases/t-docker-storage-driver)） |
| `certificate has expired` | kubelet 证书过期（见 [证书过期](/cases/t-k8s-cert-expired)） | 续证书 |
| `connection refused 10250` | kubelet 进程没起来 | systemctl restart kubelet |

### 5. 本次实际：磁盘满导致 containerd 起不来

journalctl 里发现：

```text
kubelet: could not resolve: no space left on device
containerd: unable to create snapshot: no space left
```

`df -h` 看节点根分区 100% 满，containerd 写不了镜像层，CNI 也起不来，kubelet 上报 NotReady。

## 根因

| 层级 | 说明 |
|---|---|
| 直接原因 | 节点根分区磁盘满，containerd/CNI 无法写入，kubelet 判定节点 NotReady |
| 诱因 | 节点日志/镜像/容器堆积未清理 |

## 解决步骤

### 止血

1. 上节点清理磁盘，先把根分区腾出来：

```bash
ssh worker-3
# 看谁占满
df -h
du -sh /var/lib/containerd/* 2>/dev/null | sort -h | tail
# 清未使用的镜像和停止的容器
crictl rmi --prune
# 清日志
journalctl --vacuum-size=500M
```

2. 磁盘腾出来后重启 kubelet/containerd：

```bash
systemctl restart containerd
systemctl restart kubelet
```

```bash
# 回到 master 看节点恢复
kubectl get nodes   # worker-3 应很快变 Ready
```

### 根治

1. 节点磁盘加监控，>80% 告警；给 containerd 配日志轮转、定期清理无用镜像。

2. kubelet 配 eviction 阈值，磁盘快满时主动驱逐 Pod 保护节点：

```yaml
# /var/lib/kubelet/config.yaml
evictionHard:
  imagefs.available: "15%"
  memory.available: "200Mi"
  nodefs.available: "10%"
```

3. 系统盘与数据盘分离，容器数据目录挂大盘。

## 验证与预防

```bash
kubectl describe node worker-3 | grep -A12 Conditions   # 全 Normal/False
kubectl get nodes                                       # Ready
```

- 监控：节点 DiskPressure/MemoryPressure/PIDPressure 告警；节点 NotReady 告警。
- 排障套路：describe node 看 Conditions 先定位是哪类压力，再 ssh 上节点查 kubelet/containerd 日志。
- 规范：节点盘容量监控 + kubelet eviction 配置。

## 相关

- 命令速查：[kubectl 命令速查](/reference/kubectl-commands) ｜ [云原生排障命令速查](/reference/cloudnative-commands) ｜ [Linux 命令速查](/reference/linux-commands)
- 同组短文：[etcd 故障](/cases/t-k8s-etcd-failure) ｜ [集群证书过期](/cases/t-k8s-cert-expired) ｜ [OOMKilled](/cases/t-k8s-oomkilled)
