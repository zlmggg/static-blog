---
title: "集群生命周期与证书速查：kubeadm、etcdctl、kubelet"
description: "本文是 云原生命令速查 中「集群生命周期」的详解。集群架构与初始化实战见 K8s 集群架构。 官方文档：kubeadm ｜ kubeadm 证书 ｜ etcd 运维"
---
# 集群生命周期与证书速查：kubeadm、etcdctl、kubelet

> 本文是 [云原生命令速查](../cloudnative-commands#集群生命周期与证书) 中「集群生命周期」的详解。集群架构与初始化实战见 [K8s 集群架构](/guide/container-k8s-01-architecture-cluster)。
>
> 官方文档：[kubeadm](https://kubernetes.io/docs/reference/setup-tools/kubeadm/) ｜ [kubeadm 证书](https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-certs/) ｜ [etcd 运维](https://etcd.io/docs/latest/op-guide/maintenance/)

## 一、kubeadm 常用命令

| 命令 | 作用 |
|---|---|
| `kubeadm init --pod-network-cidr=10.244.0.0/16` | 初始化控制面 |
| `kubeadm join 控制面IP:6443 --token ... --discovery-token-ca-cert-hash sha256:...` | 工作节点加入 |
| `kubeadm token create --print-join-command` | 生成新的加入命令（token 过期时） |
| `kubeadm token list` | 查看有效 token |
| `kubeadm token delete <token>` | 删除 token |
| `kubeadm upgrade plan` | 查看可升级版本与组件 |
| `kubeadm upgrade apply v1.30.0` | 升级控制面 |
| `kubeadm upgrade node` | 升级工作节点上的 kubelet 配置 |
| `kubeadm config images list` | 查看当前版本需要的镜像 |
| `kubeadm reset` | 清空本机集群配置（谨慎） |

标准升级顺序（单控制面示例）：

```bash
# 控制面
kubeadm upgrade plan
kubeadm upgrade apply v1.30.0
systemctl restart kubelet

# 工作节点（逐台）
kubectl drain 节点 --ignore-daemonsets --delete-emptydir-data
apt install -y kubeadm=1.30.* kubelet=1.30.* kubectl=1.30.*
kubeadm upgrade node
systemctl restart kubelet
kubectl uncordon 节点
```

## 二、证书检查与续期

```bash
kubeadm certs check-expiration          # 看所有证书到期时间
kubeadm certs renew all                 # 续期全部（1.15+）
kubeadm certs renew apiserver           # 只续某一张
systemctl restart kubelet               # 让 kubelet 重新加载证书
```

重点证书：

| 证书 | 用途 | 过期后果 |
|---|---|---|
| `apiserver` | API Server 服务端证书 | `kubectl` 连接失败、组件通信用不了 |
| `apiserver-kubelet-client` | API Server 访问 kubelet | `logs/exec` 失败 |
| `front-proxy-client` | 聚合层 | 聚合 API 异常 |
| `etcd-server` / `etcd-peer` | etcd 集群通信 | etcd 集群不可用 |
| `sa.key` / `sa.pub` | ServiceAccount 签名 | 已签发 token 失效 |

> kubelet 客户端证书默认会自动轮转（`rotateCertificates: true`）；`kubeadm` 管理的证书不会自动续，需要定时任务或升级时处理。

## 三、etcdctl 健康与备份

```bash
export ETCDCTL_API=3
export ETCD_ENDPOINTS=https://127.0.0.1:2379
export ETCD_FLAGS="--cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key"

etcdctl --endpoints=$ETCD_ENDPOINTS $ETCD_FLAGS endpoint health
etcdctl --endpoints=$ETCD_ENDPOINTS $ETCD_FLAGS endpoint status --write-out=table
etcdctl --endpoints=$ETCD_ENDPOINTS $ETCD_FLAGS member list --write-out=table
```

备份与恢复：

```bash
# 备份（在任一 etcd 节点执行）
etcdctl --endpoints=$ETCD_ENDPOINTS $ETCD_FLAGS snapshot save /var/backups/etcd-$(date +%F-%H%M).db

# 校验备份
etcdctl snapshot status /var/backups/etcd-2026-11-18.db --write-out=table

# 恢复（先停 kubelet 与静态 Pod，恢复后改 data-dir 权限）
etcdctl snapshot restore /var/backups/etcd-2026-11-18.db \
  --data-dir=/var/lib/etcd-restore
```

维护：

```bash
etcdctl --endpoints=$ETCD_ENDPOINTS $ETCD_FLAGS defrag
etcdctl --endpoints=$ETCD_ENDPOINTS $ETCD_FLAGS alarm list
etcdctl --endpoints=$ETCD_ENDPOINTS $ETCD_FLAGS alarm disarm
```

## 四、kubelet 与静态 Pod

```bash
systemctl status kubelet
journalctl -u kubelet -n 100 --no-pager
systemctl restart kubelet

# 配置与静态 Pod
cat /var/lib/kubelet/config.yaml
ls -l /etc/kubernetes/manifests/     # apiserver/controller-manager/scheduler/etcd 的静态 Pod
```

控制面组件是静态 Pod：改 `/etc/kubernetes/manifests/*.yaml` 后 kubelet 会自动重建，不需要 `kubectl apply`。

## 五、控制面故障排查顺序

```bash
kubectl get nodes                      # 1. 节点是否 Ready
kubectl get pods -n kube-system         # 2. 控制面 Pod 是否在跑
crictl ps -a | grep -E 'kube-apiserver|etcd|kube-controller'   # 3. 容器是否反复重启
journalctl -u kubelet -n 200 --no-pager # 4. kubelet 报错
etcdctl endpoint health                 # 5. etcd 是否健康
```

常见根因：证书过期、etcd 磁盘慢/满、静态 Pod 配置写错、控制面时间不同步、VIP/网络不通。

## 六、官方文档与相关

- kubeadm 参考：https://kubernetes.io/docs/reference/setup-tools/kubeadm/
- kubeadm 集群升级：https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-upgrade/
- 证书管理：https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-certs/
- etcd 运维指南：https://etcd.io/docs/latest/op-guide/maintenance/
- etcd 灾难恢复：https://etcd.io/docs/latest/op-guide/recovery/
- kubelet 配置：https://kubernetes.io/docs/reference/config-api/kubelet-config.v1beta1/
- 速查页：[云原生排障命令速查](../cloudnative-commands#集群生命周期与证书)
- 节点维护：[kubectl 节点维护](../cmd-kubectl/node-maintenance)
- 集群架构：[K8s 集群架构](/guide/container-k8s-01-architecture-cluster)
