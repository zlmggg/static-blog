# Kubernetes

::: tip 本篇定位
覆盖架构、核心资源、服务发现、存储、滚动更新和排错。
:::

## 高频面试题

### Q1：K8s 架构和组件？

**我的答案：**

结论：K8s 分控制面（Master）和工作节点（Node）两层，核心思想是**声明式 API + 调谐循环（reconcile）**。

控制面组件：

- **kube-apiserver**：所有组件的唯一入口，RESTful 接 CRUD，所有操作都经过它，认证鉴权、限流都在这一层。etcd 只被 apiserver 访问。
- **etcd**：分布式 KV 存储，存整个集群的所有状态（Pods、Service、ConfigMap、Secret），Raft 强一致。etcd 挂了集群就懵了，生产要单独备份。
- **kube-scheduler**：watch 新创建的、还没分配节点的 Pod，根据资源请求、亲和性、污点容忍选个合适的节点绑上去（bind）。它只做"选哪台"，不负责启动容器。
- **kube-controller-manager**：一堆控制器的大管家，Node 控制器、Deployment 控制器、ReplicaSet 控制器、Endpoint 控制器都在里面。每个控制器干一件事：不断对比"我现在看到的状态"和"用户声明的期望状态"，不一样就动手调。

工作节点组件：

- **kubelet**：每个节点上的 agent，watch 分配到本节点的 Pod，调容器运行时把容器拉起来、保持住，定期上报 Pod 状态和节点健康。
- **kube-proxy**：每个节点上跑，负责 Service 的网络转发（iptables/ipvs 规则），ClusterIP 怎么转到 Pod 全靠它。
- **容器运行时**：containerd 或 CRI-O，真正跑容器的东西。

整个工作机制一句话：你 `kubectl apply` 一个 Deployment，apiserver 写进 etcd，Deployment 控制器看到后创建 ReplicaSet，ReplicaSet 控制器看到后创建 Pod，scheduler 把 Pod 绑到某节点，那节点 kubelet 调运行时起容器。这就是"声明式"——你只说"我要 3 个副本"，至于怎么凑够 3 个是控制器自己的事。

---

### Q2：Pod 生命周期和状态？

**我的答案：**

结论：Pod 是 K8s 最小调度单位，不是容器，是"一组共享网络/存储的容器集合"。Pod 相位（Phase）有五种：`Pending`（已创建但容器还没起来，可能在调度/拉镜像）、`Running`（已绑定节点，至少一个容器在跑）、`Succeeded`（所有容器正常退出、不再重启）、`Failed`（所有容器都退出、至少一个失败）、`Unknown`（节点失联，kubelet 没上报）。

Pod 里有三种容器：**基础容器（pause 容器）** 负责 hold 住网络和 namespace；**init 容器**（可以多个）按顺序一个个跑完才起主容器，常用来等 DB 就绪、初始化配置；**业务容器**跑主进程。

探针三个，决定 Pod 死活：

- **livenessProbe（存活探针）**：失败就重启容器。程序死锁、僵死时用。
- **readinessProbe（就绪探针）**：失败就把 Pod 从 Service Endpoints 摘下来，不接流量，但不重启容器。程序还在启动、依赖没就绪时用。
- **startupProbe（启动探针）**：慢启动应用专用，启动期间其他探针暂停，避免老应用启动 60 秒被 liveness 误杀。

重启策略 `restartPolicy`：`Always`（默认）、`OnFailure`、`Never`。

优雅终止：Pod 被删时，先把它从 Endpoints 摘掉（不再有新流量），发 `SIGTERM` 给主进程，等 `terminationGracePeriodSeconds`（默认 30 秒），还不退就 `SIGKILL`。所以应用一定要处理 SIGTERM，把在处理的请求做完再退，不然会出现用户看到的连接被掐断。

---

### Q3：Service 类型？

**我的答案：**

结论：Service 是一组 Pod 的稳定访问入口，解决"Pod IP 会变"的问题。四种类型：

第一，**ClusterIP（默认）**。分配一个集群内部虚拟 IP，只有集群内容器能访问。Pod 之间互调用这个，最常用。

第二，**NodePort**。在每个节点上开一个端口（30000~32767），外部访问 `<任一节点IP>:NodePort` 就能到 Service。测试环境、临时服务用，生产一般不直接暴露，端口不好记、不好做 SSL。

第三，**LoadBalancer**。云上给你开一个公网负载均衡器（阿里云 SLB、AWS ELB），自动把流量导到后端 Pod。云厂商收费，适合对外暴露的核心业务。

第四，**ExternalName**。把 Service 映射成一个外部域名（CNAME），`app.example.com -> external.example.com`，集群内用内部域名访问外部服务，做服务抽象用。

还有个 **Headless Service**（`clusterIP: None`），不分配虚拟 IP，DNS 直接返回所有 Pod 的 IP，适合 StatefulSet 这种需要稳定网络身份的场景。

底层怎么实现？kube-proxy 在每个节点上写 iptables（或 ipvs）规则：访问 ClusterIP 的包被 DNAT 到某个后端 Pod IP。ipvs 模式性能更好、规则多时不卡。

七层路由靠 **Ingress**（Nginx Ingress、Traefik），按域名和路径把外部 HTTP 流量分到不同 Service。Service 四层出了集群才能用 NodePort/LB，七层域名路由交给 Ingress。

---

### Q4：滚动更新与回滚？

**我的答案：**

结论：Deployment 默认就是滚动更新，通过 `maxSurge` 和 `maxUnavailable` 两个参数控制节奏，不中断业务。

两个关键参数：`maxSurge` 滚动期间最多比期望副本数多几个（默认 25%）；`maxUnavailable` 滚动期间最多允许几个不可用（默认 25%）。比如期望 4 个副本，maxSurge=25%、maxUnavailable=25%，意思是更新时最多同时存在 5 个 Pod、最少保证 3 个可用。过程就是：起一个新 Pod，等它 Ready，再杀一个旧 Pod，再起一个新的，直到全部换新。

命令：

```bash
kubectl set image deployment/myapp myapp=registry/myapp:v1.2.0
kubectl rollout status deployment/myapp     # 看滚动进度
kubectl rollout history deployment/myapp    # 看历史版本
kubectl rollout undo deployment/myapp       # 回滚到上一版
kubectl rollout undo deployment/myapp --to-revision=3   # 回滚到指定版本
kubectl rollout pause deployment/myapp      # 暂停，灰度一半
kubectl rollout resume deployment/myapp     # 继续
```

注意：滚动更新是否真不中断，取决于 readinessProbe 配没配。新 Pod 没就绪就先不接流量，旧 Pod 不删；如果没配就绪探针，K8s 以为新 Pod 一启动就 ready，可能瞬间把旧 Pod 全杀了、新 Pod 还没起来，业务就抖一下。所以** readinessProbe 是滚动更新不中断的前提**。

回滚本质是把 Deployment 的 Pod 模板切回旧版本，再触发一次滚动更新，很快。镜像标签别用 `latest`，每次发布用明确的版本号或 commit SHA，不然回滚时都不知道回的是哪个。

---

### Q5：Pod 异常如何排查？

**我的答案：**

结论：Pod 异常按"**状态 → describe 事件 → 日志 → 资源 → 网络/配置/存储**"五步查，命令是 `kubectl get/describe/logs`。

第一步，看状态。`kubectl get pods -n ns`，看 STATUS 和 RESTARTS。`Pending` 一般是调度不上；`CrashLoopBackOff` 启动就崩反复重启；`ImagePullBackOff` 镜像拉不下来；`Error` 刚退出。

第二步，`kubectl describe pod <pod> -n ns`，重点看 **Events** 部分。90% 的问题这里直接告诉你：节点资源不够（0/3 nodes available）、镜像拉取失败看 pull secret、探针失败、卷挂载失败、调度被污点拒绝。

第三步，看日志。`kubectl logs <pod> -n ns`；如果容器刚崩、日志没了，加 `--previous` 看上次崩溃的日志：`kubectl logs <pod> --previous`。多容器 Pod 要 `-c <容器名>` 指定。

第四步，进容器验证。`kubectl exec -it <pod> -- sh`，进去 `curl` 自己的端口、看进程、看环境变量。

第五步，分类深挖：

- **调度类**（Pending）：`kubectl describe node` 看资源够不够，有没有 taint 没容忍。
- **镜像类**（ImagePullBackOff）：镜像名/tag 写错、私有仓库 secret 没配、网络拉不动。
- **探针类**（CrashLoopBackOff + Liveness failed）：readiness/liveness 配太严，应用启动慢被反复杀，调大 initialDelaySeconds 或加 startupProbe。
- **资源类**（OOMKilled）：`kubectl describe pod` 看 Last State Reason，限制内存太小，调 `resources.limits`。
- **网络类**：`kubectl get svc endpoints` 看 endpoints 有没有 IP，Service 选对没选对 Pod；跨 namespace DNS 不通就 `nslookup` 查 CoreDNS。
- **配置/存储类**：ConfigMap/Secret 改了没？Volume 挂载失败？describe 里 Events 会写。

---

## 相关链接

- [相关文档](/reference/kubectl-commands)
