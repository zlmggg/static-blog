---
title: Spring Cloud 微服务
description: 架构演进与微服务特点、Spring Cloud Alibaba 版本配套、Nacos 注册配置、Sentinel 限流熔断、Seata 分布式事务 AT、Gateway 路由限流、OpenFeign 与链路追踪
category: 数据
difficulty: 中级
---
# Spring Cloud 微服务

::: tip 本篇定位
理解架构演进与微服务本质，掌握 **Spring Cloud Alibaba** 全家桶：**Nacos**（注册 + 配置）、**Sentinel**（限流熔断）、**Seata**（分布式事务）、**Gateway**（网关），并了解 OpenFeign 与链路追踪。
:::

## 先建立全局观：为什么需要这么多组件

单体应用里，方法调用、配置、事务都在一个进程内完成。拆成微服务后，这些原本"天然成立"的事都变成了跨网络问题，需要专门组件解决：

| 单体里天然有的 | 微服务里由谁解决 |
|---|---|
| 我知道调用谁 | 注册中心（Nacos） |
| 配置统一管理 | 配置中心（Nacos） |
| 一个方法直接调用 | OpenFeign / Dubbo |
| 本地事务 | Seata 分布式事务 |
| 一个入口 | Gateway |
| 扛不住流量 | Sentinel 限流熔断 |
| 出问题能排查 | 链路追踪（SkyWalking） |

---

## 一、微服务概述

### 1.1 架构演进

| 阶段 | 特点 | 问题 |
|---|---|---|
| 单体架构 | 所有模块打成一个包部署 | 耦合重、技术栈统一、扩展要整体扩、迭代慢 |
| SOA | 服务化，通过 **ESB（企业服务总线）** 集成 | ESB 笨重、易成单点瓶颈、成本高 |
| **微服务** | 拆成一组小服务，独立进程、独立部署 | 分布式复杂度高 |

### 1.2 微服务特点

- **单一职责**：一个服务只做好一块业务；
- **独立**：独立进程、独立开发部署、独立数据库/技术栈；
- **轻量通信**：REST（HTTP）或 RPC（Dubbo/gRPC）；
- **去中心化治理**：数据、治理各自独立，自动化部署。

### 1.3 优缺点

优点：粒度小易理解、可独立技术栈/扩展、故障隔离、小团队自治。
缺点：服务拆分增加开发/测试/运维复杂度、分布式事务/数据一致性、链路追踪难、服务治理复杂。**小系统盲目拆分反而增加成本。**

### 1.4 Spring Cloud 与版本配套

Spring Cloud 是基于 Spring Boot 的微服务规范与全家桶，国内主流 **Spring Cloud Alibaba**：

| 能力 | 组件 |
|---|---|
| 注册/配置 | Nacos |
| 限流熔断 | Sentinel |
| 分布式事务 | Seata |
| 网关 | Spring Cloud Gateway |
| 服务调用 | OpenFeign / Dubbo |
| 负载均衡 | Spring Cloud LoadBalancer |
| 链路追踪 | Micrometer Tracing + SkyWalking/Zipkin |

::: warning 版本必须配套（重点，最易踩坑）
以当前主流一套为例：

| Spring Boot | Spring Cloud | Spring Cloud Alibaba | JDK |
|---|---|---|---|
| 3.2.x | 2023.0.x (Leyton) | 2023.0.1.x | 17 |

三者版本号没有数字对应关系，必须查官方版本说明对齐；随意混用会出现启动报错、类找不到。
:::

---

## 二、Nacos

Nacos = **注册中心 + 配置中心**。

### 2.1 注册中心

- 服务启动时注册自己的 IP/端口，消费者从 Nacos 拉取实例列表做调用和负载均衡；
- 健康检查：**临时实例**（客户端心跳，AP，Distro 协议）、**非临时实例**（服务端主动探测，CP，Raft）；
- 实例不健康会被摘除。

### 2.2 配置中心

- 统一管理各环境配置，修改后**动态推送、无需重启**；
- 三级隔离：**Namespace（环境，如 dev/test/prod）→ Group（分组）→ Data ID（具体配置文件）**。

### 2.3 部署

```bash
# 单机
docker run -d --name nacos -p 8848:8848 -p 9848:9848 \
  -e MODE=standalone nacos/nacos-server:v2.4.3
# 控制台 http://IP:8848/nacos  默认 nacos/nacos
```

生产集群：至少 **3 节点**、共享 **MySQL** 持久化配置、内部 Raft/Distro 保证一致，前置负载均衡。

### 2.4 应用接入

```yaml
spring:
  application:
    name: user-service
  cloud:
    nacos:
      discovery:
        server-addr: 10.0.0.13:8848
      config:
        server-addr: 10.0.0.13:8848
        file-extension: yaml
        namespace: dev
```

依赖 `spring-cloud-starter-alibaba-nacos-discovery`、`-config`。

---

## 三、Sentinel

Sentinel 做**流量控制、熔断降级、系统负载保护**，替代已停更的 Hystrix。

### 3.1 核心概念：资源与规则

- **资源**：被保护的方法/接口（`@SentinelResource`）；
- **规则**：围绕资源设置的流控/熔断规则。

### 3.2 限流

- 阈值类型：**QPS** 或 **并发线程数**；
- 流控模式：直接、关联（关联资源达阈值限流自己）、链路；
- 流控效果：快速失败、Warm Up（冷启动）、排队等待。

### 3.3 熔断降级

| 策略 | 触发条件 |
|---|---|
| 慢调用比例 | 平均 RT 超过阈值的比例达限 |
| 异常比例 | 异常占比超阈值 |
| 异常数 | 异常条数超阈值 |

熔断后进入 OPEN（拒绝请求）→ 经过时长进入 HALF-OPEN（试探）→ 恢复或继续熔断。

### 3.4 Dashboard 与持久化

```bash
java -Dserver.port=8080 -jar sentinel-dashboard-1.8.8.jar
# 默认 sentinel/sentinel
```

规则默认存内存、重启丢失，生产可持久化到 **Nacos**（数据源 datasource）。

---

## 四、Seata

Seata 解决跨服务/跨库的**分布式事务**。

### 4.1 三个角色

| 角色 | 说明 |
|---|---|
| **TC** | 事务协调器（Seata Server），维护全局事务、驱动提交/回滚 |
| **TM** | 事务管理器，发起/提交/回滚全局事务 |
| **RM** | 资源管理器，管理分支事务与本地资源 |

### 4.2 AT 模式（最常用，自动）

- 每个业务库建 **undo_log** 表；
- 一阶段：执行业务 SQL，同时记录**前镜像/后镜像**到 undo_log，提交本地事务、释放锁；
- 二阶段：全局提交 → 异步删 undo_log；全局回滚 → 按 undo_log **自动反向补偿**。

### 4.3 其他模式

TCC（手动 Try/Confirm/Cancel，无锁、性能高但侵入）、SAGA（长事务）、XA（强一致、资源锁定久）。

### 4.4 部署与接入

```bash
docker run -d --name seata-server -p 8091:8091 -p 7091:7091 \
  apache/seata-server:2.0.0
```

业务加 `spring-cloud-starter-alibaba-seata`，入口方法标注：

```java
@GlobalTransactional
public void createOrder(...) { ... }
```

---

## 五、Gateway

Spring Cloud Gateway 基于 WebFlux/Netty，**非阻塞、高吞吐**，替代 Zuul，作为统一入口。

### 5.1 核心概念

| 概念 | 说明 |
|---|---|
| Route | id + 目标 uri + Predicates + Filters |
| Predicate 断言 | Path、Method、Header、Host、时间、参数 |
| Filter 过滤器 | 加头、改路径、鉴权、限流 |

### 5.2 配置

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: user-service
          uri: lb://user-service        # lb 从 Nacos 按服务名负载均衡
          predicates:
            - Path=/api/user/**
          filters:
            - StripPrefix=2
            - AddRequestHeader=X-From, gateway
```

### 5.3 限流与跨域

- `RequestRateLimiter` 基于 **Redis + 令牌桶**，按用户/IP/接口限流；
- 统一处理跨域 CORS、鉴权、日志、灰度。

---

## 六、服务调用与链路追踪

### 6.1 OpenFeign

声明式 HTTP 调用：定义接口 + `@FeignClient("服务名")`，像调本地方法一样调远程服务，内置负载均衡。

### 6.2 链路追踪

微服务一次请求经过多个服务，需要链路追踪串起调用链（Trace ID / Span ID）。常用 **SkyWalking**（国产、功能全、字节码无侵入）、Micrometer Tracing + Zipkin/Tempo，配合日志定位跨服务问题。

---

## 面试自测

1. 单体、SOA、微服务的区别？微服务有什么优缺点，适合所有项目吗？
2. Spring Boot、Spring Cloud、Spring Cloud Alibaba 版本为什么必须配套？
3. Nacos 注册中心临时实例和非临时实例有什么区别？配置如何做环境隔离？
4. Sentinel 限流的 QPS 和线程数模式、熔断的三种策略分别是什么？
5. Seata 的 TC/TM/RM 角色？AT 模式两阶段怎么做的？
6. Gateway 的 Route/Predicate/Filter 是什么？如何限流？
7. 分布式链路追踪解决什么问题？

## 相关速查

- [Linux 命令速查](/reference/linux-commands)
- Spring Cloud Alibaba：https://sca.aliyun.com/docs/
- Nacos：https://nacos.io/zh-cn/docs/what-is-nacos.html
- Sentinel：https://sentinelguard.io/zh-cn/docs/introduction.html
- Seata：https://seata.apache.org/zh-cn/docs/overview/what-is-seata/
- Gateway：https://docs.spring.io/spring-cloud-gateway/reference/
