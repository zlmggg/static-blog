---
category: 监控
difficulty: 高级
---

# Prometheus 实战 10：Kubernetes 集成与 SOP/FAQ

> **Prometheus 实战系列（共 10 篇）**
> ← 上一篇 [Prometheus 实战 09](./monitor-prometheus-09-container-federation-storage)
> [返回监控索引](./monitor)

## 阶段十一：Kubernetes 集成 Prometheus

### 阶段目标

- 掌握在 Kubernetes 中部署 Prometheus 的三种方式：**YAML、Helm、Operator**；
- 会用 ServiceMonitor、PodMonitor、Probe、PrometheusRule 等 CRD；
- 完成对 API Server、kubelet、cAdvisor、业务 Pod、Controller、Scheduler、Node Exporter 的完整监控。

Kubernetes 是 Prometheus 最典型的使用场景：Pod 频繁创建销毁，静态配置完全不可行，必须用服务发现。

### 11.1 方式一：YAML 文件部署

YAML 方式需要自己写全：Namespace、ServiceAccount、ClusterRole/ClusterRoleBinding（RBAC）、ConfigMap（prometheus.yml）、Deployment/StatefulSet、Service。

#### 11.1.1 RBAC 权限

Prometheus 需要通过 API Server 发现资源，ClusterRole 至少包含：

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: prometheus
rules:
  - apiGroups: [""]
    resources:
      - nodes
      - nodes/proxy
      - nodes/metrics
      - services
      - endpoints
      - pods
      - ingresses
      - configmaps
    verbs: ["get", "list", "watch"]
  - apiGroups: ["networking.k8s.io"]
    resources: ["ingresses", "ingresses/status"]
    verbs: ["get", "list", "watch"]
  - apiGroups: ["discovery.k8s.io"]
    resources: ["endpointslices"]
    verbs: ["get", "list", "watch"]
  - nonResourceURLs: ["/metrics"]
    verbs: ["get"]
```

`get/list/watch` 分别是读取单个、列全部、监听变更；服务发现必须有 list 和 watch。

#### 11.1.2 ConfigMap 与 Deployment

官方示例（推荐直接参考，持续更新）：

```text
https://github.com/prometheus/prometheus/blob/main/documentation/examples/prometheus-kubernetes.yml
```

把该文件内容放进 ConfigMap 的 data，Deployment 挂载到 `/etc/prometheus/prometheus.yml`，启动参数 `--config.file=/etc/prometheus/prometheus.yml`。

最小可用示例（含 API Server、节点、Pod 三类采集）：

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s
    scrape_configs:
      - job_name: 'kubernetes-apiservers'
        kubernetes_sd_configs:
          - role: endpoints
        scheme: https
        tls_config:
          ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
        bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
        relabel_configs:
          - source_labels: [__meta_kubernetes_namespace, __meta_kubernetes_service_name, __meta_kubernetes_endpoint_port_name]
            action: keep
            regex: default;kubernetes;https
      - job_name: 'kubernetes-pods'
        kubernetes_sd_configs:
          - role: pod
        relabel_configs:
          - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
            action: keep
            regex: 'true'
          - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_port]
            target_label: __address__
            regex: ([^:]+)(?::\d+)?;(\d+)
            replacement: $1:$2
          - action: labelmap
            regex: __meta_kubernetes_pod_label_(.+)
```

Deployment 关键片段（生产建议用 StatefulSet + PVC，见 11.2）：

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels: {app: prometheus}
  template:
    metadata:
      labels: {app: prometheus}
    spec:
      serviceAccountName: prometheus
      containers:
        - name: prometheus
          image: prom/prometheus:v3.15.0
          args:
            - --config.file=/etc/prometheus/prometheus.yml
            - --storage.tsdb.path=/prometheus
            - --storage.tsdb.retention.time=15d
            - --web.enable-lifecycle
          ports:
            - containerPort: 9090
          volumeMounts:
            - name: config
              mountPath: /etc/prometheus
            - name: data
              mountPath: /prometheus
      volumes:
        - name: config
          configMap: {name: prometheus-config}
        - name: data
          emptyDir: {}
```

::: warning
emptyDir 数据随 Pod 删除而丢失，**只能用于测试**。生产必须用 StatefulSet + PVC（动态供给），见 Helm 部分。
:::

### 11.2 方式二：Helm 部署

Helm 把上面的资源模板化，是最常用的部署方式。两个常用 chart：

| chart | 内容 |
| --- | --- |
| `prometheus-community/prometheus` | Prometheus + Alertmanager（子 chart），较精简 |
| `prometheus-community/kube-prometheus-stack` | **全家桶（推荐）**：Operator + Prometheus + Alertmanager + Grafana + kube-state-metrics + node-exporter + 全套默认规则 |

#### 11.2.1 安装 prometheus chart

**第 1 步：添加仓库**

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
```

**第 2 步：准备 values** `prom-values.yaml`（需要提前有 StorageClass，如 `sc-nfs`）：

```yaml
server:
  global:
    scrape_interval: 1m
    scrape_timeout: 10s
    evaluation_interval: 1m

  ingress:
    enabled: true
    ingressClassName: nginx
    hosts:
      - prometheus.【你的域名】
    path: /
    pathType: Prefix

  persistentVolume:
    enabled: true
    accessModes: ["ReadWriteOnce"]
    size: 8Gi
    storageClass: "sc-nfs"
    mountPath: /data

  replicaCount: 1

  service:
    enabled: true
    type: ClusterIP
    servicePort: 9090

alertmanager:
  enabled: true
  persistence:
    size: 2Gi
    storageClass: "sc-nfs"
    accessModes: ["ReadWriteOnce"]
```

**第 3 步：安装**

```bash
helm install prometheus prometheus-community/prometheus \
  --namespace monitoring --create-namespace \
  --values prom-values.yaml
```

验证：

```bash
kubectl get pods,svc -n monitoring
```

#### 11.2.2 （可选）prometheus-adapter

prometheus-adapter 把 Prometheus 指标转成 Kubernetes 自定义指标 API，供 HPA 使用：

```bash
helm install prometheus-adapter prometheus-community/prometheus-adapter \
  --namespace monitoring \
  --set prometheus.url=http://prometheus-server.monitoring.svc \
  --set prometheus.port=9090
```

#### 11.2.3 （推荐）kube-prometheus-stack

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

cat > stack-values.yaml <<'EOF'
prometheus:
  prometheusSpec:
    retention: 15d
    retentionSize: "10GiB"
    resources:
      requests: {cpu: 200m, memory: 500Mi}
      limits: {cpu: "1", memory: 1Gi}
    storageSpec:
      volumeClaimTemplate:
        spec:
          storageClassName: sc-nfs
          accessModes: ["ReadWriteOnce"]
          resources:
            requests:
              storage: 20Gi

alertmanager:
  alertmanagerSpec:
    storage:
      volumeClaimTemplate:
        spec:
          storageClassName: sc-nfs
          accessModes: ["ReadWriteOnce"]
          resources:
            requests:
              storage: 5Gi

grafana:
  enabled: true
  adminPassword: 【Grafana管理员密码】
  ingress:
    enabled: true
    ingressClassName: nginx
    hosts:
      - grafana.【你的域名】
EOF

helm install kps prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  --values stack-values.yaml
```

::: tip
国内拉取 `quay.io`、`registry.k8s.io`、`ghcr.io` 镜像可能失败。两种解决：① 提前把镜像同步到私有仓库，用 `--set` 覆盖镜像地址；② 配置容器运行时的镜像加速。chart 版本固定（如 91.8.0），不要用不确定的最新版直接上生产。
:::

### 11.3 方式三：Operator（kube-prometheus）

#### 11.3.1 Operator 原理（三句话）

- Prometheus Operator 是一个自定义控制器，用 Kubernetes 声明式方式管理 Prometheus 监控套件；
- 它通过一组 CRD 描述监控对象，Operator 监听这些 CRD 并自动生成/更新 Prometheus 配置；
- 业务方只需创建 ServiceMonitor 等对象，不必手写 prometheus.yml。

核心 CRD：

| CRD | 作用 |
| --- | --- |
| `Prometheus` | 定义 Prometheus Server 实例（副本、版本、存储、规则引用） |
| `Alertmanager` | 定义 Alertmanager 实例 |
| `ServiceMonitor` | 声明如何采集一组 Service（通过 label 选择） |
| `PodMonitor` | 声明如何采集一组 Pod |
| `Probe` | 黑盒监控（Ingress 或静态目标） |
| `PrometheusRule` | 声明式定义告警/记录规则 |
| `AlertmanagerConfig` | 声明式定义 Alertmanager 配置段 |
| `ScrapeConfig` | 直接提供 scrape_config 配置段（支持 Consul 等发现） |

#### 11.3.2 获取清单

```bash
cd /usr/local
VERSION=0.19.0
wget https://github.com/prometheus-operator/kube-prometheus/archive/refs/tags/v${VERSION}.tar.gz
tar xf v${VERSION}.tar.gz -C /usr/local
cd /usr/local/kube-prometheus-${VERSION}
```

目录结构：

| 目录 | 内容 |
| --- | --- |
| `manifests/setup/` | CRD、Operator 命名空间与 Operator 自身（先装） |
| `manifests/` | Prometheus、Alertmanager、Grafana、各 Exporter、默认规则（后装） |

#### 11.3.3 修改 Service 访问方式

编辑 `manifests/prometheus-service.yaml`，改为 NodePort（或 LoadBalancer）：

```yaml
spec:
  type: NodePort
  ports:
    - name: web
      port: 9090
      targetPort: web
      nodePort: 30090
```

同样修改 `manifests/grafana-service.yaml`（nodePort 30030）、`manifests/alertmanager-service.yaml`（nodePort 30093）。

#### 11.3.4 替换镜像（国内环境）

查看所有镜像：

```bash
grep -h 'image:' manifests/*.yaml manifests/setup/*.yaml | sort -u
```

把 quay.io / registry.k8s.io / ghcr.io 的镜像改成私有仓库地址（批量 sed 或逐个编辑），提前在私有仓库准备好这些镜像。

#### 11.3.5 安装

```bash
kubectl create ns monitoring

# 先装 setup（CRD + Operator）
kubectl apply -f manifests/setup/
# 若提示 "Too long"（一行内容过长），改用：
kubectl create -f manifests/setup/

# 等待 Operator 就绪
kubectl get pods -n monitoring

# 再装监控组件
kubectl apply -f manifests/
```

::: warning
使用 Calico 网络插件时，默认 NetworkPolicy 可能阻止访问，需要删除：

```bash
kubectl delete -f manifests/prometheus-networkPolicy.yaml
kubectl delete -f manifests/grafana-networkPolicy.yaml
kubectl delete -f manifests/alertmanager-networkPolicy.yaml
```
:::

验证：

```bash
kubectl get pods -n monitoring
kubectl get svc -n monitoring
```

预期：prometheus-k8s、alertmanager-main（3 副本）、grafana、node-exporter（DaemonSet）、kube-state-metrics、blackbox-exporter、prometheus-operator 全部 Running。

Operator 拓扑：

![Kubernetes Operator 监控拓扑](/guide/diagrams/kubernetes-operator.svg)

---
### 11.4 使用：业务接入监控

#### 11.4.1 ServiceMonitor 接入业务

业务 Deployment + Service 正常部署，然后创建 ServiceMonitor。

**第 1 步：业务 Deployment**（示例）：

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: metrics-app
spec:
  replicas: 2
  selector:
    matchLabels: {app: metrics-app}
  template:
    metadata:
      labels: {app: metrics-app}
    spec:
      containers:
        - name: metrics-app
          image: registry.cn-beijing.aliyuncs.com/【你的命名空间】/metrics-app:v0.1
          ports:
            - name: web
              containerPort: 80
          resources:
            requests: {cpu: 100m, memory: 128Mi}
            limits: {cpu: 500m, memory: 256Mi}
```

**第 2 步：Service**：

```yaml
apiVersion: v1
kind: Service
metadata:
  name: metrics-app
  labels:
    app: metrics-app
spec:
  type: ClusterIP
  ports:
    - name: web
      port: 80
      targetPort: web
  selector:
    app: metrics-app
```

**第 3 步：ServiceMonitor**：

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: metrics-app
  namespace: monitoring
  labels:
    release: kps
spec:
  selector:
    matchLabels:
      app: metrics-app
  endpoints:
    - port: web
      interval: 15s
      path: /metrics
```

字段解释：`selector.matchLabels` 选择带这些标签的 Service；`endpoints.port` 用 Service 端口名（不是数字）；`path` 指标路径；`labels.release` 要与 Prometheus CRD 里 serviceMonitorSelector 匹配（kube-prometheus-stack 装的默认要求带 `release=<release名>`，自己装的 kube-prometheus 通常无此要求——不生效时先查这里）。

#### 11.4.2 Probe：黑盒监控外部/内部目标

```yaml
apiVersion: monitoring.coreos.com/v1
kind: Probe
metadata:
  name: web-probe
  namespace: monitoring
spec:
  jobName: http-get
  interval: 60s
  module: http_2xx
  prober:
    url: blackbox-exporter.monitoring.svc:19115
    scheme: http
    path: /probe
  targets:
    staticConfig:
      static:
        - http://www.【你的域名】
        - https://www.baidu.com
```

#### 11.4.3 PrometheusRule：告警/记录规则

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: business-rules
  namespace: monitoring
  labels:
    prometheus: k8s
    role: alert-rules
spec:
  groups:
    - name: business.rules
      rules:
        - alert: BusinessPodDown
          expr: up{pod=~"metrics-app.*"} == 0
          for: 1m
          labels:
            severity: critical
          annotations:
            summary: "业务 Pod 异常：{{ $labels.pod }}"
```

#### 11.4.4 验证查询

- 浏览器访问 `http://【任一节点IP】:30090`（NodePort），Targets 页面能看到 ServiceMonitor 自动生成的采集 job；
- 查询每个 Pod 的 CPU：

```promql
sum(rate(container_cpu_usage_seconds_total{image!="", pod!=""}[1m])) by (pod)
```

- Alertmanager：`http://【节点IP】:30093`；
- Grafana：`http://【节点IP】:30030`，默认账号 admin，首次登录改密；导入 8919 等看板时选默认 Prometheus 数据源。

### 11.5 Ingress 定制

不想用 NodePort 时，用 Ingress 统一暴露。先确保已部署 ingress-nginx controller，然后：

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: monitoring-ingress
  namespace: monitoring
  annotations:
    nginx.ingress.kubernetes.io/proxy-body-size: "100m"
spec:
  ingressClassName: nginx
  rules:
    - host: prom.【你的域名】
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: prometheus-k8s
                port: {number: 9090}
    - host: alert.【你的域名】
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: alertmanager-main
                port: {number: 9093}
    - host: grafana.【你的域名】
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: grafana
                port: {number: 3000}
```

```bash
kubectl apply -f monitoring-ingress.yaml
kubectl get ingress -n monitoring
```

域名解析到 Ingress Controller 的地址后，三个域名分别访问。

### 11.6 采集 Controller Manager 与 Scheduler

默认监控不到这两个控制面组件，需要两步：开放监听地址、创建 Service + Endpoints。

#### 11.6.1 开放监听地址

在 master 节点编辑静态 Pod 清单（kubelet 会自动重建 Pod）：

`/etc/kubernetes/manifests/kube-controller-manager.yaml`，确认/修改：

```text
- --bind-address=0.0.0.0
```

`/etc/kubernetes/manifests/kube-scheduler.yaml`，同样：

```text
- --bind-address=0.0.0.0
```

等待控制面 Pod 重建：

```bash
kubectl get pods -n kube-system | grep -E 'controller-manager|scheduler'
```

#### 11.6.2 创建 Service + Endpoints（Controller Manager）

```yaml
apiVersion: v1
kind: Service
metadata:
  name: kube-controller-manager
  namespace: kube-system
  labels:
    app.kubernetes.io/name: kube-controller-manager
spec:
  clusterIP: None
  ports:
    - name: https-metrics
      port: 10257
      targetPort: 10257
---
apiVersion: v1
kind: Endpoints
metadata:
  name: kube-controller-manager
  namespace: kube-system
  labels:
    app.kubernetes.io/name: kube-controller-manager
subsets:
  - addresses:
      - ip: 【master节点IP】
    ports:
      - name: https-metrics
        port: 10257
```

::: tip
新版控制面组件只暴露 https 端口（10257 controller、10259 scheduler），旧的 http 端口（10252/10251）已废弃。多 master 时把所有 master IP 都写进 addresses。
:::

#### 11.6.3 创建 Service + Endpoints（Scheduler）

```yaml
apiVersion: v1
kind: Service
metadata:
  name: kube-scheduler
  namespace: kube-system
  labels:
    app.kubernetes.io/name: kube-scheduler
spec:
  clusterIP: None
  ports:
    - name: https-metrics
      port: 10259
      targetPort: 10259
---
apiVersion: v1
kind: Endpoints
metadata:
  name: kube-scheduler
  namespace: kube-system
  labels:
    app.kubernetes.io/name: kube-scheduler
subsets:
  - addresses:
      - ip: 【master节点IP】
    ports:
      - name: https-metrics
        port: 10259
```

```bash
kubectl apply -f kube-controller-svc.yaml
kubectl apply -f kube-scheduler-svc.yaml
kubectl get ep -n kube-system | grep -E 'controller|scheduler'
```

#### 11.6.4 ServiceMonitor 采集

创建对应的 ServiceMonitor（端口名 https-metrics，scheme HTTPS，跳过证书校验）：

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: control-plane
  namespace: monitoring
  labels:
    release: kps
spec:
  selector:
    matchExpressions:
      - key: app.kubernetes.io/name
        operator: In
        values: [kube-controller-manager, kube-scheduler]
  namespaceSelector:
    matchNames: [kube-system]
  endpoints:
    - port: https-metrics
      scheme: https
      interval: 30s
      tlsConfig:
        insecureSkipVerify: true
      bearerTokenFile: /var/run/secrets/kubernetes.io/serviceaccount/token
```

验证：Targets 出现 control-plane 组件，`workqueue_*`、`scheduler_*` 指标可查。

### 11.7 Node Exporter DaemonSet

kube-prometheus-stack 已自带 node-exporter DaemonSet。若单独部署：

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: node-exporter
  namespace: monitoring
  labels: {app: node-exporter}
spec:
  selector:
    matchLabels: {app: node-exporter}
  template:
    metadata:
      labels: {app: node-exporter}
    spec:
      hostNetwork: true
      hostPID: true
      tolerations:
        - key: node-role.kubernetes.io/control-plane
          operator: Exists
          effect: NoSchedule
      containers:
        - name: node-exporter
          image: prom/node-exporter:v1.12.1
          args:
            - --path.procfs=/host/proc
            - --path.sysfs=/host/sys
            - --path.rootfs=/host/root
          ports:
            - name: metrics
              containerPort: 9100
              hostPort: 9100
          volumeMounts:
            - {name: proc, mountPath: /host/proc, readOnly: true}
            - {name: sys, mountPath: /host/sys, readOnly: true}
            - {name: root, mountPath: /host/root, readOnly: true}
      volumes:
        - name: proc
          hostPath: {path: /proc}
        - name: sys
          hostPath: {path: /sys}
        - name: root
          hostPath: {path: /}
```

::: warning
容器内看到的 /proc、/sys 是容器自己的，必须通过 `--path.procfs/sysfs/rootfs` 指向宿主机挂载路径，否则采集到的是容器指标而非宿主机。
:::

ServiceMonitor/采集由 stack 自动完成；Grafana 1860 看板展示节点数据。

---

### 本阶段命令速查表

```bash
# Helm 仓库
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# 安装全家桶
helm install kps prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace -f stack-values.yaml

# kube-prometheus 清单方式
kubectl apply -f manifests/setup/
kubectl apply -f manifests/

# 查看
kubectl get pods,svc,ingress -n monitoring

# 业务接入
kubectl apply -f deployment.yaml service.yaml servicemonitor.yaml

# 查看 Operator 自动生成的配置
kubectl get secret prometheus-k8s -n monitoring \
  -o jsonpath='{.data.prometheus\.yaml\.gz}' | base64 -d | gzip -d | less

# 升级 / 卸载
helm upgrade kps prometheus-community/kube-prometheus-stack -n monitoring -f stack-values.yaml
helm uninstall kps -n monitoring
```

---

### 本阶段常见坑与解决

**坑 1：ServiceMonitor 创建了但不采集**

- 现象：ServiceMonitor 存在，Targets 里没有对应 job。
- 原因：ServiceMonitor 的 labels 不被 Prometheus CRD 的 serviceMonitorSelector 接受（stack 默认要求 `release=<名字>`）；namespace 不对；selector 没选中 Service。
- 解决：补 release 标签；确认 Service 标签与 matchLabels 一致；确认 endpoints.port 用的是端口**名**。

**坑 2：Pod 采集报连接拒绝/404**

- 报错/现象：目标 DOWN，日志 404 page not found。
- 原因：容器没暴露 /metrics 或端口/路径配错。
- 解决：kubectl exec 进 Pod curl localhost:端口/metrics 自查；修正 port/path。

**坑 3：镜像拉不下来（ImagePullBackOff）**

- 报错原样：`Failed to pull image "quay.io/...": rpc error ... timeout`。
- 原因：quay.io、registry.k8s.io 国内访问受限。
- 解决：同步到私有仓库并覆盖镜像地址；配置加速；离线 load。

**坑 4：控制面组件监控不到**

- 现象：controller/scheduler 目标为空。
- 原因：bind-address 是 127.0.0.1；Endpoints 写错；用了已废弃的 http 端口。
- 解决：bind 改 0.0.0.0；用 https 10257/10259；确认 Endpoints 指向 master IP。

**坑 5：Node Exporter 数据不对（数值异常小）**

- 现象：节点 CPU/内存数据明显错误。
- 原因：没配 path.procfs/sysfs，采集的是容器视角。
- 解决：挂载宿主机 /proc、/sys、/ 并配 path 参数。

**坑 6：Calico 下无法访问监控页面**

- 报错/现象：Service/Pod 正常但访问超时。
- 原因：默认 NetworkPolicy 拦截。
- 解决：删除对应 networkPolicy 或按文档放通。

**坑 7：helm install 报 PVC Pending**

- 报错原样：`pod has unbound immediate PersistentVolumeClaims`。
- 原因：没有可用 StorageClass 或名字写错。
- 解决：`kubectl get sc` 确认；storageClass 填实际名称；或临时用 emptyDir 测试。

**坑 8：Prometheus 配置改了不生效**

- 现象：手动改配置无效。
- 原因：Operator 管理的配置由 CRD 自动生成，手改会被覆盖。
- 解决：改 ServiceMonitor/PrometheusRule 等 CRD，而不是直接改 prometheus.yml。

---
## 完整实战流程汇总（SOP）

### SOP 1：新机器接入监控（Node Exporter）

1. 新主机完成初始化（换源、主机名、时区、时间同步）；
2. 安装 node_exporter（二进制 9100 或容器），配置 systemd 开机自启；
3. 放通 9100 端口（监控服务器到本机）；
4. 在监控侧：静态配置加 target，或文件发现 targets/node.yml 加一行，或 Consul 注册；
5. Prometheus Targets 确认 UP；
6. Grafana 看板确认该主机出现；
7. 确认主机宕机、CPU、内存、磁盘告警规则覆盖该目标。

### SOP 2：新业务服务接入监控

1. 应用暴露 /metrics（内置或引入 client 库）；
2. 确定 Job 名、关键业务标签（app、env、region）；
3. 配置采集（静态/文件发现/Consul/K8s 用 ServiceMonitor）；
4. 编写业务黄金指标看板（QPS、错误率、延迟、饱和度）；
5. 编写业务告警规则并演练触发；
6. 通知渠道确认（邮件/企微/钉钉）。

### SOP 3：Prometheus 配置发布与回滚

**发布**：

1. 备份当前配置：`cp prometheus.yml prometheus.yml.bak.$(date +%F)`；
2. 编辑配置；
3. `promtool check config prometheus.yml`（规则用 promtool check rules）；
4. `systemctl reload prometheus` 或 `curl -X POST http://localhost:9090/-/reload`；
5. Targets、Rules 页面验证。

**回滚**：

1. `cp prometheus.yml.bak.日期 prometheus.yml`；
2. promtool 检查；
3. reload；
4. 验证恢复。

### SOP 4：告警维护窗口（静默）

1. Alertmanager → Silences → New Silence；
2. 精确填写匹配标签（如 instance=某主机），不要用过宽条件；
3. 设置开始/结束时间（维护预计时长，宁短勿长）；
4. 维护结束后若提前完成，手动删除该 Silence；
5. 多实例/集群下确认静默已同步。

### SOP 5：扩容（单机 → 联邦/集群存储）

1. 评估瓶颈：采集目标过多（CPU/内存）→ 加 Prometheus 分片或联邦；存储不足 → 扩盘或上 VictoriaMetrics；
2. 联邦：新增从节点承接部分 Job，中心节点加 federate job；
3. 存储：部署 VM 单机/集群，Prometheus 配 remote_write；
4. 灰度切换数据源，观察一段时间；
5. 更新看板与告警归属。

### SOP 6：备份与恢复

**备份内容**：prometheus.yml、rules 目录、Alertmanager 配置与模板（这些是核心资产，体量小）。

```bash
BACKUP_DIR=/data/backup/prometheus
mkdir -p ${BACKUP_DIR}
tar czf ${BACKUP_DIR}/prometheus-conf-$(date +%F).tar.gz \
  -C /usr/local/prometheus conf rules
tar czf ${BACKUP_DIR}/am-conf-$(date +%F).tar.gz \
  -C /usr/local/alertmanager conf tmpl
```

**历史数据备份**：本地 TSDB 可用快照 API：

```bash
curl -X POST http://localhost:9090/api/v1/admin/tsdb/snapshot
# 快照生成在 data/snapshots/<快照ID>
```

**恢复**：

1. 重装 Prometheus/Alertmanager（同版本）；
2. 解压配置备份到原路径；
3. 数据快照拷回 data 目录；
4. 启动服务，检查配置、规则、目标、看板。

::: warning
Prometheus 数据备份不是常规必需（它是监控数据，可重新采集），**配置和规则必须备份**。长期历史数据建议直接存 VictoriaMetrics 并对其数据盘做快照/备份。
:::

### SOP 7：日常巡检清单

- Prometheus、Alertmanager、Grafana 服务状态；
- Prometheus 自身指标：`prometheus_tsdb_head_series`（序列数）、`prometheus_sd_failed_configs`、`prometheus_notifications_failed_total`、`prometheus_remote_storage_failed_samples_total`；
- 磁盘水位（data 目录增长）；
- Targets 是否有 DOWN；
- 告警是否正常送达（定期演练）；
- 时间同步状态。

---

## 常见问题排查（FAQ）

**Q1：Target 显示 DOWN 怎么排查？**

按顺序：① 被监控机服务是否启动、端口是否监听（ss -lntp）；② 监控机能否连通（curl http://目标IP:端口/metrics、ping、telnet）；③ 防火墙/安全组是否放通；④ 服务是否监听 0.0.0.0（只监听 127.0.0.1 外部访问不了）；⑤ 看 Target 页该目标的 Error 提示。

**Q2：告警触发了但收不到通知？**

① Alertmanager 是否在运行、Prometheus alerting 配置地址是否正确；② 告警状态是否到 Firing（Pending 不发）；③ 路由 matchers 是否匹配、receiver 是否配置正确；④ 是否被静默或抑制；⑤ Alertmanager 日志与 `prometheus_notifications_*` 指标；⑥ 邮件看 SMTP 报错、钉钉/企微看渠道侧报错。

**Q3：磁盘涨得特别快？**

① 查序列数 `prometheus_tsdb_head_series` 是否高基数爆炸；② 是否有标签值无限增长（user_id、request_id、IP 当标签）；③ retention 是否过长；④ 用 metric_relabel 丢弃无用高基数指标；⑤ 缩短保留或上远程存储。

**Q4：Grafana 面板没数据？**

① 数据源测试是否通过；② 面板 Job 变量与实际 job 名是否一致；③ 时间范围是否选对；④ 直接在 Prometheus 查该 PromQL 验证表达式；⑤ 看板与组件版本是否匹配。

**Q5：容器重启后数据/配置丢失？**

① 配置是否通过挂载持久化；② 数据目录是否挂载数据卷；③ 容器方式是否用了 restart 策略；④ 生产用 StatefulSet/PVC 或宿主机目录挂载。

**Q6：Prometheus 内存占用越来越高？**

① 序列数是否持续增长（高基数）；② 采集目标是否过多，考虑分片/联邦；③ Head 块 2 小时刷盘是正常波动；④ 调整处理并发、减少不必要的指标采集。

**Q7：图表出现毛刺/数据断点？**

① 抓取是否超时（scrape_timeout 太短、目标负载高）；② 网络抖动；③ 时间是否同步；④ 查看 `scrape_duration_seconds`、`up` 历史。

**Q8：修改配置后 Prometheus 报错启动失败？**

① 不要直接重启，先用 promtool check config 定位；② 常见是 YAML 缩进、重复 key、正则非法；③ 修复后再 reload；④ 无法快速修复时用备份配置回滚。

---

## 面试自测

1. Prometheus 的整体架构和数据流向？Pull 模型的优缺点？
2. Prometheus 有哪四种指标类型？Histogram 和 Summary 的区别与选择？
3. PromQL 的四种结果类型？rate 和 increase、irate 的区别？
4. Counter 和 Gauge 的区别？哪些指标必须用 Counter？
5. Job 和 Instance 的关系？`up` 指标的含义和用途？
6. relabel_configs 和 metric_relabel_configs 的区别和发生时机？
7. 记录规则解决什么问题？命名规范是什么？
8. 告警的完整链路？Pending 和 Firing 的区别，for 的作用？
9. Alertmanager 的分组、抑制、静默、路由分别解决什么问题？
10. Alertmanager 高可用如何实现？Gossip 的作用？
11. Prometheus 服务发现有哪些方式？Kubernetes 有哪些 role？
12. ServiceMonitor 的工作原理？为什么创建了 ServiceMonitor 却不生效？
13. Prometheus 联邦的适用场景和能力边界？
14. 本地 TSDB 的存储机制？WAL、Block、压缩分别是什么？
15. Prometheus 单机瓶颈如何解决？VictoriaMetrics 集群有哪些组件和端口？
16. 如何监控 Prometheus 自身？关键自身指标有哪些？
17. Pushgateway 的适用场景和缺点？
18. Blackbox 监控和普通 Exporter 监控的区别？
19. 四个黄金信号是什么？如何用 PromQL 实现？
20. 一条告警规则应该包含哪些要素？如何避免告警风暴？

---

## 相关速查（官网地址）

| 项目 | 官网 / 文档 |
| --- | --- |
| Prometheus 官网 | https://prometheus.io/ |
| Prometheus 文档 | https://prometheus.io/docs/introduction/overview/ |
| Prometheus 下载 | https://prometheus.io/download/ |
| PromQL 查询基础 | https://prometheus.io/docs/prometheus/latest/querying/basics/ |
| PromQL 函数 | https://prometheus.io/docs/prometheus/latest/querying/functions/ |
| 配置说明 | https://prometheus.io/docs/prometheus/latest/configuration/configuration/ |
| 告警规则 | https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/ |
| 联邦 | https://prometheus.io/docs/prometheus/latest/federation/ |
| Alertmanager 文档 | https://prometheus.io/docs/alerting/latest/alertmanager/ |
| Alertmanager 配置 | https://prometheus.io/docs/alerting/latest/configuration/ |
| 通知模板 | https://prometheus.io/docs/alerting/latest/notifications/ |
| 高可用 | https://github.com/prometheus/alertmanager#high-availability |
| Node Exporter | https://github.com/prometheus/node_exporter |
| MySQL Exporter | https://github.com/prometheus/mysqld_exporter |
| Redis Exporter | https://github.com/oliver006/redis_exporter |
| Blackbox Exporter | https://github.com/prometheus/blackbox_exporter |
| Pushgateway | https://github.com/prometheus/pushgateway |
| JMX Exporter | https://github.com/prometheus/jmx_exporter |
| nginx-prometheus-exporter | https://github.com/nginxinc/nginx-prometheus-exporter |
| HAProxy Exporter | https://github.com/prometheus/haproxy_exporter |
| Consul Exporter | https://github.com/prometheus/consul_exporter |
| cAdvisor | https://github.com/google/cadvisor |
| 钉钉 Webhook | https://github.com/timonwong/prometheus-webhook-dingtalk |
| PrometheusAlert | https://github.com/feiyu563/PrometheusAlert |
| VictoriaMetrics 官网 | https://victoriametrics.com/ |
| VictoriaMetrics 文档 | https://docs.victoriametrics.com/ |
| VM 集群文档 | https://docs.victoriametrics.com/cluster-victoriametrics/ |
| Prometheus Operator | https://github.com/prometheus-operator/prometheus-operator |
| kube-prometheus | https://github.com/prometheus-operator/kube-prometheus |
| Helm Charts | https://github.com/prometheus-community/helm-charts |
| Grafana 官网 | https://grafana.com/ |
| Grafana 看板市场 | https://grafana.com/grafana/dashboards/ |
| 现成告警规则集 | https://samber.github.io/awesome-prometheus-alerts/ |
| GitHub 代理（加速下载） | https://ghproxy.net/ （备选 https://gh-proxy.com/ 、https://ghfast.top/ ） |
| 清华镜像站 | https://mirrors.tuna.tsinghua.edu.cn/ |
| 阿里云镜像站 | https://mirrors.aliyun.com/ |
| Go 模块代理 | https://goproxy.cn/ |
| pip 清华源 | https://pypi.tuna.tsinghua.edu.cn/simple |

---

## 附录：延伸阅读（可选）

- 《Site Reliability Engineering》（Google SRE 书）：监控方法论与四个黄金信号的出处，在线版 https://sre.google/sre-book/monitoring-distributed-systems/（需科学上网）；国内平替：https://www.cnblogs.com/lhxBlogs/p/17924893.html
- Facebook Gorilla 论文：理解 TSDB 高压缩存储，https://www.vldb.org/pvldb/vol8/p1816-teller.pdf
- Prometheus 官方最佳实践：指标命名、标签使用，https://prometheus.io/docs/practices/naming/
- Kubernetes 可观测性体系：Metrics Server、cAdvisor、kube-state-metrics 的分工
- Thanos：另一类 Prometheus 长期存储与高可用方案，https://thanos.io/
- OpenTelemetry：可观测性标准（Metrics/Traces/Logs 融合），https://opentelemetry.io/
- Grafana Loki：与 Prometheus 同风格的日志聚合方案，https://grafana.com/oss/loki/
