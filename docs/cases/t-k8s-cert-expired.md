---
category: 容器
difficulty: 中级
date: 2025-05-21
---

# K8s 集群证书过期（2025-05-21）

## 现象

集群突然全挂，kubectl 全部报错：

```text
kubectl get nodes
Unable to connect to the server: x509: certificate has expired or is not yet valid
```

master 上 kubelet、apiserver 各种证书校验失败，Pod 也起不来。kubeadm 集群跑了快一年没动过证书。

## 环境

| 组件 | 版本 |
|---|---|
| Kubernetes | 1.31.1（kubeadm 部署） |
| 证书签发 | kubeadm 自签 CA（默认有效期 10 年） |
| 触发 | 集群运行超过 1 年，客户端证书到期 |

## 定位过程

### 1. 确认是证书过期

```bash
# kubeadm 直接看证书有效期
kubeadm certs check-expiration
```

输出：

```text
CERTIFICATE                EXPIRES                  RESIDUAL TIME
apiserver                  May 10, 2026 09:00 UTC   11d    <-- 快到期
apiserver-kubelet-client   May 10, 2026 09:00 UTC   11d
front-proxy-client         May 10, 2026 09:00 UTC   11d
```

> kubeadm 签发的**客户端证书默认 1 年有效期**（CA 本身 10 年）。满 1 年就会过期。

### 2. 手动看某张证书的过期时间

```bash
openssl x509 -in /etc/kubernetes/pki/apiserver.crt -noout -dates
# notAfter=May 10 09:00:00 2026 GMT
```

### 3. kubelet 证书过期的特殊情况

kubelet 证书也会过期，且 kubelet 有自动轮转，但如果 `--rotate-certificates` 没开或 kubelet.conf 过期，节点会 NotReady：

```bash
# 看 kubelet 证书
openssl x509 -in /var/lib/kubelet/pki/kubelet-client-current.pem -noout -dates
```

## 根因

| 层级 | 说明 |
|---|---|
| 直接原因 | kubeadm 签发的 apiserver 等客户端证书满 1 年到期，apiserver 与 kubelet/组件间 TLS 校验失败 |
| 流程原因 | 从没人检查证书有效期，没有到期告警 |

## 解决步骤

### 止血（紧急续期）

1. 如果还没完全过期，先自动续期（kubeadm 一键更新所有证书）：

```bash
# 在每个 master 节点执行
kubeadm certs renew all
```

> `renew all` 会用现有 CA 重新签发所有客户端证书，续 1 年。CA 本身（/etc/kubernetes/pki/ca.crt）10 年不用动。

2. 重启 apiserver / controller-manager / scheduler 等静态 Pod 让新证书生效：

```bash
# 静态 Pod 在 /etc/kubernetes/manifests/，重启容器即可
cd /etc/kubernetes/manifests
# 简单做法：mv 出去再 mv 回来触发 kubelet 重建
mv kube-apiserver.yaml /tmp/ && sleep 5 && mv /tmp/kube-apiserver.yaml .
# controller-manager / scheduler / etcd 同理（etcd 不用动证书）
```

3. 更新 kubeconfig（kubectl 用的 admin 证书也被 renew 了）：

```bash
# kubeadm renew 会自动改 /etc/kubernetes/admin.conf
# 把新的 admin.conf 拷到 ~/.kube/config
cp /etc/kubernetes/admin.conf ~/.kube/config
```

```bash
kubectl get nodes   # 恢复正常
```

### kubelet 证书过期

```bash
# 如果 kubelet 证书过期导致 NotReady
kubeadm certs renew admin.conf
systemctl restart kubelet
```

### 根治

1. 开启 kubelet 证书自动轮转（kubeadm 默认已开），并定期检查：

```bash
# /var/lib/kubelet/config.yaml
rotateCertificates: true
serverTLSBootstrap: true
```

2. 加监控/定时任务，提前 30 天告警证书到期：

```bash
# 每周跑一次 check-expiration
kubeadm certs check-expiration | grep -v "certificate is not..." 
```

3. 长期方案：升级 k8s 版本时 kubeadm 会续证书；或部署 cert-manager 管理业务证书。

## 验证与预防

```bash
kubeadm certs check-expiration    # RESIDUAL TIME 应为 ~364d
kubectl get nodes                 # 正常
```

- 监控：证书到期时间告警（<30 天）。
- 规范：每年定期 `kubeadm certs renew all`；升级 k8s 版本顺带续证书。
- 备份：续证书前备份 /etc/kubernetes/pki 整个目录。

## 相关

- 命令速查：[云原生排障命令速查](/reference/cloudnative-commands) ｜ [kubectl 命令速查](/reference/kubectl-commands)
- 同组短文：[节点 NotReady](/cases/t-k8s-node-notready) ｜ [etcd 故障](/cases/t-k8s-etcd-failure)
