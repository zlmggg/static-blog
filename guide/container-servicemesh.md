---
category: 容器
difficulty: 中级
---

# 服务网格与链路追踪实战

::: tip 本篇定位
理解服务网格（Service Mesh）如何用 Sidecar 把服务治理能力从业务代码中剥离，掌握 Istio 的部署与流量管理，并用 SkyWalking 实现分布式链路追踪。本篇版本：Istio 1.31.x、SkyWalking 10.4.0。
:::

## 一、从微服务到服务网格

### 1.1 微服务与服务治理

微服务把单体应用按业务拆分成一组小服务，各自独立开发、部署、扩展。但拆分后，服务间远程通信带来一系列**服务治理**问题：服务发现、负载均衡、调用失败后的熔断降级、限流、灰度发布、认证授权、调用链追踪等。

早期这些能力由应用框架解决，如 Java 的 Spring Cloud（Eureka/Nacos 注册、Ribbon 负载、Hystrix/Sentinel 熔断、Gateway 网关）。缺点是：能力与业务代码耦合，每种语言都要实现一套，升级治理组件要改代码、重新发布。

### 1.2 Kubernetes 解决了一部分

Kubernetes 已经提供了服务发现（CoreDNS）、配置（ConfigMap/Secret）、负载均衡、弹性伸缩、RBAC 等能力。但仍有一些处于"应用与基础设施边缘"的问题（精细的流量路由、熔断、双向认证、请求级指标）难以在基础设施层完全处理。

### 1.3 Sidecar 与服务网格

服务网格引入**边车代理（Sidecar Proxy）**：在每个服务 Pod 中自动注入一个通信代理（如 Envoy），以对应用透明的方式接管该服务所有进出流量。

- 应用之间的实际通信经过代理，称为**数据平面（Data Plane）**；
- 代理还接收控制器下发的配置和策略，称为**控制平面（Control Plane）**；
- 代理据此实现负载均衡、熔断、认证、度量、流量路由，**业务代码无需任何改动**，且与开发语言无关。

![服务网格 Sidecar 模式：每个服务 Pod 内应用与 Envoy Sidecar 在本地通信，服务间经 Sidecar 转发形成数据平面，控制平面 istiod 向各 Sidecar 下发策略](/diagrams/mesh-01.svg)

代表技术：Istio（控制平面）+ Envoy（数据平面）是主流组合，另有 Linkerd、Consul Connect 等。

## 二、Istio 部署

### 2.1 Istio 架构

Istio 分为两部分：

- **数据平面**：注入到每个 Pod 的 Envoy 代理，负责实际转发、安全、收集指标；
- **控制平面**：组件 `istiod`（整合了配置分发、证书签发、服务发现），把用户定义的路由、安全规则转换成 Envoy 能理解的配置并统一下发。

![Istio 架构：用户定义的 VirtualService、DestinationRule 进入 istiod 控制平面，istiod 通过 xDS 向各 Envoy 下发配置并签发 mTLS 证书，Envoy 转发服务流量](/diagrams/mesh-02.svg)

### 2.2 版本与前提

Istio 1.31 支持 Kubernetes 1.32～1.36。安装前确认 K8s 版本在支持范围内、节点和 CoreDNS 正常。

### 2.3 安装 istioctl 并部署

下载并安装 istioctl（以 1.31.1 为例，国内可走加速代理）：

```bash
curl -L https://istio.io/downloadIstio | ISTIO_VERSION=1.31.1 sh
cd istio-1.31.1
cp bin/istioctl /usr/local/bin/
istioctl version
```

安装到集群（default 配置档）：

```bash
istioctl install --set profile=demo -y
kubectl get pods -n istio-system
```

### 2.4 开启 Sidecar 自动注入

给命名空间打上标签后，该命名空间里新建的 Pod 会被自动注入 Envoy：

```bash
kubectl label namespace default istio-injection=enabled
kubectl get namespace --show-labels
```

对已运行的工作负载需要重启一次以触发注入：

```bash
kubectl rollout restart deployment <你的部署名>
kubectl get pods
```

注入成功后，每个业务 Pod 会显示 `2/2 READY`（业务容器 + istio-proxy 容器）。

## 三、流量管理

Istio 用两个核心 CRD 描述流量：

- **VirtualService（虚拟服务）**：定义请求如何路由，可按路径、Header 匹配，可设置权重做灰度，还能配置重试、超时、故障注入；
- **DestinationRule（目标规则）**：定义目标服务的版本子集（subset），以及连接池、异常检测（熔断）等策略。

### 3.1 入口网关 Gateway

```yaml
apiVersion: networking.istio.io/v1
kind: Gateway
metadata:
  name: my-gateway
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 80
      name: http
      protocol: HTTP
    hosts: ["*"]
```

### 3.2 灰度发布（按权重）

VirtualService 把 90% 流量给 v1、10% 给 v2，逐步调大比例完成灰度：

```yaml
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: myapp
spec:
  hosts:
  - myapp
  gateways:
  - my-gateway
  http:
  - route:
    - destination:
        host: myapp
        subset: v1
      weight: 90
    - destination:
        host: myapp
        subset: v2
      weight: 10
```

### 3.3 版本子集与熔断

```yaml
apiVersion: networking.istio.io/v1
kind: DestinationRule
metadata:
  name: myapp
spec:
  host: myapp
  subsets:
  - name: v1
    labels:
      version: v1
  - name: v2
    labels:
      version: v2
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        http2MaxRequests: 1000
    outlierDetection:
      consecutive5xxErrors: 3
      interval: 30s
      baseEjectionTime: 30s
```

`outlierDetection` 即熔断：当某实例连续出现 5xx 达到阈值，就把它临时摘除一段时间，避免请求继续打到异常实例。

## 四、安全与可观测

### 4.1 双向 TLS（mTLS）

Istio 可为网格内服务通信自动加密并做身份认证。全局开启严格模式：

```yaml
apiVersion: security.istio.io/v1
kind: PeerAuthentication
metadata:
  name: default
  namespace: istio-system
spec:
  mtls:
    mode: STRICT
```

STRICT 要求服务间一律走 mTLS；迁移期可用 PERMISSIVE（明文、密文都允许）过渡。证书由 istiod 自动签发和轮换，业务无感。

### 4.2 可观测组件

demo 配置档默认集成了 Prometheus、Grafana、Kiali：

```bash
istioctl dashboard kiali       # 服务拓扑、流量图
istioctl dashboard prometheus  # 指标
istioctl dashboard grafana     # 仪表盘
```

- **Kiali**：可视化服务拓扑、流量走向、校验配置是否正确；
- **Prometheus + Grafana**：采集 Envoy 暴露的请求量、延迟、错误率等指标（RED 指标）。

## 五、分布式链路追踪原理

### 5.1 为什么需要链路追踪

微服务中一个用户请求往往要经过多个服务，一旦变慢或失败，很难判断问题出在哪个环节。链路追踪用于还原请求的完整传播路径、各段耗时和依赖关系。

### 5.2 核心概念

- **Trace（链路）**：一次请求从入口到结束的完整调用链；
- **Span（跨度）**：链路中的一次操作（如一次服务调用、一次数据库查询），记录开始/结束时间和耗时；
- **TraceId**：在请求入口生成的全局唯一标识（类似快递单号），随调用通过 HTTP 请求头向下游传播；
- 各服务把自己的 Span（带 TraceId、SpanId、父 SpanId）上报，后端按 TraceId 把所有 Span 组装成完整链路。

### 5.3 APM 与主流系统

APM（应用性能管理）深入应用内部监控服务、接口的性能，与监控基础设施的传统监控（如 Zabbix）不同。主流链路追踪/APM：SkyWalking、Jaeger、Zipkin、CAT，以及厂商中立的 **OpenTelemetry**（已成为可观测数据采集的事实标准）。

## 六、SkyWalking 部署与接入

### 6.1 架构

SkyWalking 由四部分组成：探针 Agent（Java 字节码增强，无侵入采集）、OAP 分析平台（接收并分析数据）、存储、Web UI。

![SkyWalking 架构：Java 应用挂载 SkyWalking Agent，经 gRPC 11800 上报到 OAP Server，OAP 写入 BanyanDB 或 Elasticsearch，Web UI 经 HTTP 12800 从 OAP 查询展示](/diagrams/mesh-03.svg)

### 6.2 部署 OAP 与 UI

下载并解压（以 10.4.0 为例，可用国内镜像）：

```bash
cd /usr/local
wget https://archive.apache.org/dist/skywalking/java-agent/10.4.0/apache-skywalking-apm-10.4.0.tar.gz
tar xf apache-skywalking-apm-10.4.0.tar.gz
ln -s apache-skywalking-apm-bin skywalking
```

启动（会同时拉起 OAP 和 Webapp）：

```bash
/usr/local/skywalking/bin/startup.sh
ss -tnlp | grep -E '8080|11800|12800'
```

端口说明：UI `8080`、OAP gRPC（接收 Agent）`11800`、OAP HTTP（UI 查询）`12800`。默认存储为 H2，仅供测试；生产在 `config/application.yml` 把存储改为 BanyanDB 或 Elasticsearch。

### 6.3 挂载 Agent

Java Agent 是一个 jar，通过 JVM 参数 `-javaagent` 加载，无需修改业务代码：

```bash
java -javaagent:/usr/local/skywalking/agent/skywalking-agent.jar \
  -Dskywalking.agent.service_name=my-service \
  -Dskywalking.collector.backend_service=OAP地址:11800 \
  -jar your-app.jar
```

也可在 `agent/config/agent.config` 里改服务名和后端地址；Tomcat 则把 `-javaagent` 加到 `CATALINA_OPTS`。容器化时把 agent 目录挂载进镜像并加上 JVM 参数即可。

### 6.4 查看结果

访问 `http://OAP地址:8080`，可看到：服务拓扑图、服务/端点指标、单次请求的 Trace 调用链和各 Span 耗时，并可配置告警。

::: tip 版本说明
SkyWalking 11.0.0 已于 2026-08 发布，官方 UI 换成全新的 Horizon UI、并新增 admin server。学习和求稳可先用 10.4.0，等 11.x 文档和实践成熟后再升级。
:::

## 七、落地考量

- 服务网格会在每个 Pod 增加一个 Sidecar，带来额外 CPU、内存开销和运维复杂度，服务规模小、技术栈单一时未必划算，应按需引入；
- 链路追踪上报和存储有成本，通常配置**采样率**，不必 100% 采集；
- 建议先用可观测（追踪、指标）尝到价值，再逐步启用流量和安全策略。

## 面试自测

1. 什么是服务网格？它解决了 Spring Cloud 类方案的什么痛点？
2. 解释 Sidecar 模式，数据平面和控制平面分别负责什么。
3. 为什么说服务网格对业务代码无侵入、且与语言无关？
4. Istio 的数据平面和控制平面分别用什么组件？istiod 整合了哪些能力？
5. Sidecar 自动注入是怎么实现的？注入成功后 Pod 有什么变化？
6. VirtualService 和 DestinationRule 各负责什么？
7. 如何用 Istio 实现灰度发布？
8. Istio 的熔断对应哪个配置？工作原理是什么？
9. mTLS 是什么？STRICT 和 PERMISSIVE 模式有什么区别？
10. Kiali、Prometheus 在网格里分别提供什么？
11. 什么是 Trace、Span、TraceId？TraceId 如何在服务间传播？
12. 链路追踪后端如何把分散的上报还原成一条完整链路？
13. APM 和 Zabbix 这类基础设施监控有什么区别？
14. OpenTelemetry 是什么？为什么说它是事实标准？
15. SkyWalking 由哪几部分组成？Agent 为什么能做到无侵入？
16. SkyWalking 的 8080、11800、12800 端口分别做什么？
17. SkyWalking 默认存储是什么？生产应该用什么？
18. Java 应用如何接入 SkyWalking Agent？
19. 服务网格和链路追踪会带来哪些性能/资源开销？如何控制？
20. 什么情况下不建议引入服务网格？

## 相关速查

- 命令速查：[kubectl 命令速查](/reference/kubectl-commands)、[Docker 命令速查](/reference/docker-commands)、[网络命令速查](/reference/network-commands)
- 官方资源：
  - Istio 官网：https://istio.io/latest/zh/
  - Istio 文档：https://istio.io/latest/zh/docs/
  - 版本支持：https://istio.io/latest/docs/releases/supported-releases/
  - 流量管理：https://istio.io/latest/zh/docs/concepts/traffic-management/
  - 安装 istioctl：https://istio.io/latest/zh/docs/setup/getting-started/
  - SkyWalking 官网：https://skywalking.apache.org/
  - SkyWalking 文档：https://skywalking.apache.org/docs/
  - SkyWalking 下载：https://skywalking.apache.org/downloads/
  - Java Agent 文档：https://skywalking.apache.org/docs/skywalking-java/latest/en/setup/service-agent/java-agent/
  - OpenTelemetry：https://opentelemetry.io/
  - Envoy 官网：https://www.envoyproxy.io/
  - Kiali：https://kiali.io/

