---
category: 架构
difficulty: 中级
---

# 混沌工程

::: tip 本篇定位
与其等线上半夜挂掉才发现「这个服务挂了整个站就瘫了」，不如主动、可控地往系统里「打针」制造故障，提前测出它的韧性。读完你能理解混沌工程的核心思想，并用 Chaos Mesh 在 K8s 上跑一个安全的故障注入实验。
本篇版本：Chaos Mesh v2.8.4（Helm chart `chaos-mesh-2.8.4`）、LitmusChaos 3.32.0。均为 2026-09 官网当前稳定版。
:::

## 一、起源与核心思想

### 1.1 小白类比：「汽车碰撞测试」

新车上市前，厂家会故意把车撞一下，看气囊能不能弹出来、车架够不够硬——**不是盼着车坏，而是在可控环境里提前知道坏起来什么样**。

混沌工程就是给软件系统做「碰撞测试」：主动、可控地制造故障（杀个 Pod、加点网络延迟、堵点磁盘），观察系统会不会优雅降级、能不能自动恢复。

Netflix 当年做了个叫 **Chaos Monkey** 的工具，凌晨随机把生产环境的微服务 Pod 杀掉——逼着工程师把每个服务都做成「挂了也不影响大局」。这就是混沌工程的起点。

### 1.2 稳态假设 Steady-state Hypothesis

做实验前先问自己两个问题：

1. **稳态是什么**：平时系统健康长什么样？（如 P99 延迟 < 300ms、成功率 > 99.9%）
2. **实验后我预期怎样**：杀掉一个 order Pod 后，成功率应该基本不变（因为有副本）。

> 如果实验后稳态和你预期不符——比如杀一个 Pod 成功率就掉了——那就是**发现了一个之前不知道的脆弱点**，这就是混沌实验的价值。

## 二、故障注入类型

| 故障类型 | 具体注入 | 想验证什么 |
|---|---|---|
| Pod/容器杀死 | 随机删 Pod、杀容器 | 副本数够不够、有没有自动拉起 |
| 网络延迟 | 给某服务加 200ms~2s 延迟 | 超时/重试/熔断是否生效 |
| 网络丢包/分区 | 丢 50% 包、把服务和数据库隔离 | 熔断、降级、数据一致性 |
| DNS 故障 | 篡改 DNS 解析 | 服务发现、兜底逻辑 |
| CPU/内存压力 | 打满 CPU、吃满内存 | 限流、OOM 处理、HPA 扩容 |
| 磁盘压力 | 写满磁盘、IO 延迟 | 磁盘满告警、日志轮转 |
| 时钟偏移 | 把节点时间拨快/拨慢 | 证书校验、定时任务、分布式锁 |
| 节点宕机 | 直接 cordon/关机 | 跨可用区调度、故障域隔离 |

## 三、两大工具对比

| 对比 | Chaos Mesh | LitmusChaos |
|---|---|---|
| 定位 | K8s 原生、CRD 一体、上手快 | 平台化、工作流编排强、生态实验库多 |
| 实验定义 | CRD（PodChaos/NetworkChaos 等） | ChaosExperiment + ChaosWorkflow |
| 可视化 | 自带 Dashboard | Chaos Studio UI |
| 适合 | 团队刚入门、想快速在 K8s 上实验 | 企业级、多环境、定期 GameDay 编排 |
| 当前版本 | v2.8.4（2026-08） | 3.32.0（2026-09） |

两者都是 CNCF 项目，都用 CRD 描述实验。下面以 Chaos Mesh 为例。

## 四、部署 Chaos Mesh

```bash
helm repo add chaos-mesh https://charts.chaos-mesh.org
helm install chaos-mesh chaos-mesh/chaos-mesh \
  -n chaos-testing --create-namespace \
  --version 2.8.4 \
  --set dashboard.create=true
```

验证：

```bash
kubectl get pods -n chaos-testing          # controller-manager、chaos-daemon、dashboard 都 Running
# Dashboard: kubectl port-forward svc/chaos-dashboard -n chaos-testing 2333:2333
# 浏览器打开 http://localhost:2333
```

## 五、一个完整可应用的实验 YAML

下面这个实验：**随机杀掉 default 命名空间下带 `app=order` 标签的 1 个 Pod，持续 30 秒**。这是最经典的「杀 Pod」实验，验证你的 Deployment 副本能不能自动补回来。

```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: order-pod-kill
  namespace: default
spec:
  action: pod-kill                 # 动作：杀 Pod
  mode: one                        # 随机选一个 Pod
  selector:
    namespaces: [default]
    labelSelectors:
      app: order
  duration: "30s"                  # 实验持续时间
```

应用并观察：

```bash
kubectl apply -f order-pod-kill.yaml

# 另开一个终端盯着 Pod：会看到一个 order Pod 被杀死后自动重建
kubectl get pods -l app=order -w

# 观察实验状态
kubectl describe podchaos order-pod-kill
```

再看一个「网络延迟」实验（给 order 服务到 Redis 的流量加 500ms 延迟）：

```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: order-network-delay
  namespace: default
spec:
  action: delay
  mode: one
  selector:
    namespaces: [default]
    labelSelectors:
      app: order
  delay:
    latency: "500ms"               # 注入 500ms 延迟
  duration: "5m"
```

实验完清理：

```bash
kubectl delete podchaos order-pod-kill
kubectl delete networkchaos order-network-delay
```

### 5.1 LitmusChaos 工作流示例

LitmusChaos 用 `ChaosExperiment` + `ChaosWorkflow` 编排多步实验，并自带**韧性探针（Probe）**——实验期间自动探活，不达标自动中止。下面是一个「杀 Pod 前先确认服务健康，实验中持续探活」的片段：

```yaml
apiVersion: litmuschaos.io/v1alpha1
kind: ChaosEngine
metadata:
  name: order-pod-delete-engine
  namespace: litmus
spec:
  appinfo:
    appns: default
    applabel: app=order
  chaosServiceAccount: litmus-admin
  experiments:
    - name: pod-delete
      spec:
        components:
          env:
            - name: TOTAL_CHAOS_DURATION
              value: "30"
            - name: CHAOS_INTERVAL
              value: "10"
            - name: APP_PODS
              value: "2"          # 只影响 2 个 Pod，限制爆炸半径
          probe:
            - name: "order-http-probe"
              type: "httpProbe"
              httpProbe/inputs:
                url: "http://order.default.svc/health"
                intervalSeconds: 5
                chaosCheckTimeout: 10
```

```bash
kubectl apply -f order-pod-delete-engine.yaml -n litmus
kubectl get chaosengine order-pod-delete-engine -n litmus
```

> Chaos Mesh 与 Litmus 的实验都能配「实验前后自动探活」，这就是上节说的安全护栏在工具层面的落地——探活不过就自动中止，不会把系统打挂了还在继续注入。

## 六、爆炸半径控制与安全护栏

**混沌工程最大的风险就是把生产搞挂**，所以一定要控制爆炸半径：

```mermaid
flowchart LR
    A["定稳态指标<br>成功率/延迟"] --> B["选最小爆炸半径<br>先 1 个 Pod/1 个可用区"]
    B --> C["设熔断条件<br>指标跌破阈值自动停"]
    C --> D["先在预发/灰度跑"]
    D --> E["再小流量生产"]
    E --> F["逐步扩大"]
```

护栏要点：

- **先在预发环境跑通**，再考虑生产。
- **限定爆炸半径**：`mode: one` 先杀一个，别一上来 `mode: all`。
- **设自动中止**：用 Kubernetes 注解 `chaos-mesh.org/action: stop` 或配 Prometheus 指标联动，成功率跌破阈值自动结束实验。
- **避开高峰窗口**：别在大促期间做实验。
- **有明确的终止预案**：谁有权一键 `kubectl delete` 停掉实验。

## 七、把韧性演练纳入工程流程

- **CI 里跑轻量实验**：每次部署后自动跑一个「杀 Pod」实验，确认服务能自愈，过不了就阻断发布。
- **定期 GameDay**：每季度组织一次故障演练（如模拟整个可用区挂掉），全团队参与，练应急响应。
- **实验要写进 SOP**：每次实验记录假设、过程、结果、发现的问题，沉淀成知识库。

## 八、常见问题排错

| 现象 | 原因 | 解决 |
|---|---|---|
| PodChaos 不生效 | 没选对 Pod/selector 标签 | `kubectl get pods -l app=order` 确认标签匹配 |
| chaos-daemon 不 Ready | 权限/网络问题 | 看 `kubectl logs -n chaos-testing ds/chaos-daemon` |
| NetworkChaos 没延迟 | 节点不支持/没装内核模块 | 确认是 Linux 节点，chaos-daemon 以特权运行 |
| 实验结束故障还在 | Duration 太短/没真正删除 | `kubectl delete` 实验对象，确认 Pod 恢复 |
| 生产误操作影响面大 | 没限制 mode | 用 `mode: fixed-percent` 限定百分比，别用 `all` |

::: warning 生产红线
- **生产做混沌实验必须先在预发验证**，并限定爆炸半径、设好自动中止。
- 实验 CRD 写死命名空间和标签，别用全局 selector 误伤无关服务。
- 避开业务高峰和大促窗口，提前通知值班同学。
- 镜像/chart 版本写死（`2.8.4`、`3.32.0`），禁用 `latest`。
- Chaos Mesh 需要特权容器注入故障，只在受控 K8s 集群安装，别裸装在共享集群。
:::

## 相关速查

- 告警与发现脆弱点：[SLO/SLI、错误预算与 Burn Rate](./monitor-slo)
- 故障后怎么应对：[事故管理与无指责复盘](./sre-incident)
- 高可用与容灾：[容量规划、高可用与灾备](./sre-capacity-dr)
- K8s 基础：[Kubernetes 架构与集群](./container-k8s-01-architecture-cluster)
- 服务韧性（熔断/重试）：[Service Mesh 服务网格](./container-servicemesh)
- 云原生排障命令：[云原生排障命令速查](/reference/cloudnative-commands)
- kubectl 命令：[kubectl 命令速查](/reference/kubectl-commands)

### 官方文档

- Chaos Mesh 官网：https://chaos-mesh.org/
- Chaos Mesh Releases：https://github.com/chaos-mesh/chaos-mesh/releases
- LitmusChaos 官网：https://litmuschaos.io/
- LitmusChaos Releases：https://github.com/litmuschaos/litmus/releases
- Netflix Chaos Monkey：https://github.com/Netflix/chaosmonkey
