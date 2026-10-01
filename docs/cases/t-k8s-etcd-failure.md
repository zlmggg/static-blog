---
category: 容器
difficulty: 高级
date: 2024-06-19
---

# etcd 故障 / 空间满 / 不一致（2024-06-19）

## 现象

K8s 集群整体卡顿，API Server 响应极慢，kubectl 命令经常超时。master 节点上 etcd 报空间不足：

```text
# etcd 日志
etcdserver: mvcc: database space exceeded
etcdserver: failed to send out heartbeat on time
```

监控上 etcd 磁盘使用率冲到 90%+。

## 环境

| 组件 | 版本 |
|---|---|
| Kubernetes | 1.29.2（kubeadm） |
| etcd | 3.5.10（3 节点静态 Pod，独立盘） |
| 数据盘 | /var/lib/etcd（独立 SSD） |
| 触发 | 集群跑了 2 年，没做过 defrag |

## 定位过程

### 1. 确认是 etcd 空间满

```bash
# 在 master 上看 etcd endpoint 状态与空间
ETCDCTL_API=3 etcdctl --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  endpoint status --write-out=table
```

输出关键：

```text
+-------------------------+------------------+---------+---------+-----------+------------+
|        ENDPOINT         |        DB SIZE   |  LEARNER |  RAFT TERM |  INDEX |
+-------------------------+------------------+---------+---------+-----------+------------+
| https://10.0.1.11:2379  |     2.1 GB       |   false  |    12      |  882134  |
+-------------------------+------------------+---------+---------+-----------+------------+
```

`DB SIZE` 接近 quota（默认 2GB），触发了 `database space exceeded`。

> etcd 默认 `--quota-backend-bytes=2GB`，到了会**进入只读模式**，API Server 所有写操作失败，集群表现为卡顿/不响应。

### 2. 看碎片整理前的真实占用

etcd 删数据后空间不会自动还给文件系统（只是标记空闲），需要 defrag：

```bash
# 看磁盘真实使用 vs etcd 内部
du -sh /var/lib/etcd/member/snap/db
```

### 3. 看是否有大量 key 堆积（常见于 lease/事件泄漏）

```bash
etcdctl --endpoints=... --cacert=... --cert=... --key=... \
  --command-timeout=30s alarm list
```

## 根因

| 层级 | 说明 |
|---|---|
| 直接原因 | etcd DB 体积达到 2GB quota，进入只读保护模式 |
| 原因 | 长期未做碎片整理，已删除的 key 空间未回收；历史版本堆积 |
| 流程 | 没人监控 etcd DB 大小，没做定期 defrag |

## 解决步骤

### 止血

1. 先解除 alarm（临时恢复可写，但不解决根本）：

```bash
etcdctl ... alarm disarm
```

2. **逐个节点做 defrag**（注意：必须一个一个来，不要同时做，defrag 期间该节点暂时不可用）：

```bash
# 先 defrag follower，最后 defrag leader
# 在节点 1：
etcdctl ... defrag /2379
# 等该节点变回 healthy 再下一个
etcdctl ... endpoint health
```

defrag 后 DB 文件会明显缩小。

### 根治

1. defrag 后，如果 DB 仍然很大，说明 key 真的多，可调大 quota：

```bash
# kubeadm 集群改 /etc/kubernetes/manifests/etcd.yaml
- --quota-backend-bytes=8589934592     # 8GB
```

> 改静态 Pod manifest，kubelet 会自动重建 etcd 容器。建议同时把 etcd 数据盘换更大的 SSD。

2. 定期压缩 + defrag（cron）：

```bash
# 每周低峰做一次
etcdctl ... compact $(etcdctl ... endpoint status | grep -oE 'rev:[0-9]+' | head -1)
etcdctl ... defrag
```

3. 治理 key 堆积：检查是否有大量未清理的 lease/事件（如大量 ConfigMap/Secret 频繁更新）。

4. 定期备份 snapshot：

```bash
etcdctl ... snapshot save /backup/etcd-$(date +%F).db
etcdctl ... snapshot status /backup/etcd-xxx.db
```

## 验证与预防

```bash
etcdctl ... endpoint health          # 三节点 all is healthy
etcdctl ... endpoint status         # DB SIZE 明显下降
```

- 监控：etcd DB 大小 / quota 占比告警（>80%）；alarm 触发告警。
- 规范：定期（每周/每月）compact + defrag；定期做 snapshot 备份与恢复演练。
- 容量：根据集群规模合理设 quota + 数据盘容量。

## 相关

- 命令速查：[云原生排障命令速查](/reference/cloudnative-commands) ｜ [kubectl 命令速查](/reference/kubectl-commands)
- 同组短文：[集群证书过期](/cases/t-k8s-cert-expired) ｜ [节点 NotReady](/cases/t-k8s-node-notready)
