# kubectl port-forward 命令详解：把集群里的端口转到本地

> 本文是 [kubectl 命令速查](../kubectl-commands#调试与排障) 中 `kubectl port-forward` 的从 0 到 1 详解。
> 目标：把 `kubectl port-forward --help` 里的每个选项讲清楚，多看几遍后，你在服务器上敲 `--help` 就知道该用哪个选项。
> 环境依据：kubectl 客户端，对应 **Kubernetes 1.35**（本机沙箱未安装，选项依据 K8s 官方命令参考核实；示例输出均为「示意，据 K8s 官方文档」）。

## 一、命令是干什么的

`port-forward` 在你**本地机器**上开一个端口，把流量转发到集群里某个 Pod / Service / Deployment 的端口上。这样你在本机浏览器或 `curl localhost:8080` 就能访问集群内部的服务，不用暴露成 NodePort/LoadBalancer。

- 调试一个 ClusterIP 服务，本地直接访问；
- 连集群里的数据库（MySQL/Redis）做本地客户端调试。

> 类比：port-forward 像在你电脑和集群之间拉了一根临时水管——你本地的 8080 接到 Pod 的 80，流量经 apiserver 走过去。它是**临时调试通道**，不是正式暴露服务的方式。

## 二、命令语法

```bash
kubectl port-forward 类型/名 [选项] [本地端口:]远程端口 [...更多对]
```

- `类型/名`：`pod/名`、`service/名`、`deployment/名`；省略类型默认 `pod`；
- `本地端口:远程端口`：本地监听哪个端口、转发到远端哪个端口；只写一个端口表示本地和远端同端口；
- 命令会**前台阻塞**，`Ctrl+C` 断开。

```bash
kubectl port-forward pod/mypod 8888:5000
```

## 三、选项全表（对照 `kubectl port-forward --help`）

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `pod/名` | 转发到某个 Pod | 最直接 |
| `service/名` | 转发到 Service 选中的 Pod | 用 Service 名更稳 |
| `deployment/名` | 转发到 Deployment 管的某个 Pod | 不关心具体 Pod |
| `本地:远程` | 端口映射，如 `8888:5000` | 核心 |
| `:5000` | 本地随机分配端口 | 本地端口被占时 |
| `--address=地址` | 监听地址，默认 `localhost` | 想让局域网其他机器也访问时用 `0.0.0.0` |
| `--address=localhost,10.19.21.23` | 同时监听多个地址 | 本机+指定网卡 |
| `--pod-running-timeout=时长` | 等 Pod 起来的超时 | Pod 还没 Ready 时 |

## 四、由浅入深的典型示例

### 示例 1：本地 8888 转发到 Pod 的 5000

```bash
kubectl port-forward pod/mypod 8888:5000
```

输出（示意，据 K8s 官方文档）：

```text
Forwarding from 127.0.0.1:8888 -> 5000
Forwarding from [::1]:8888 -> 5000
```

> 然后本机 `curl http://localhost:8888` 就打到 Pod 的 5000 端口。命令前台挂着，别关。

### 示例 2：本地和远端同端口

```bash
kubectl port-forward pod/mypod 5000 6000
```

> 本地 5000→Pod 5000、本地 6000→Pod 6000，一对对写。

### 示例 3：转发到 Service

```bash
kubectl port-forward service/myservice 8443:https
```

> 用 Service 名 + 端口名（`https`），kubectl 自动选后端 Pod。比盯单个 Pod 稳。

### 示例 4：转发到 Deployment

```bash
kubectl port-forward deployment/mydeployment 5000:6000
```

> Deployment 重建 Pod 后，重新跑一次命令即可（会话随选中 Pod 终止而结束）。

### 示例 5：监听所有地址（让别人也能访问）

```bash
kubectl port-forward --address 0.0.0.0 pod/mypod 8888:5000
```

> 默认只绑 `localhost`；加 `--address 0.0.0.0` 后，同网段其他机器也能通过你这台机的 IP:8888 访问。

### 示例 6：本地随机端口

```bash
kubectl port-forward pod/mypod :5000
```

输出（示意，据 K8s 官方文档）：

```text
Forwarding from 127.0.0.1:随机端口 -> 5000
```

> 本地端口被占时，让 kubectl 随机挑一个空闲端口。

### 示例 7：连集群里的数据库调试

```bash
kubectl port-forward svc/mysql 3306:3306
```

> 本机用 MySQL 客户端连 `127.0.0.1:3306`，实际打到集群里的 MySQL Service。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `kubectl port-forward pod/名 8080:80` | 本地 8080→Pod 80（**最常用**） |
| `kubectl port-forward svc/名 8080:80` | 转发到 Service |
| `kubectl port-forward deploy/名 8080:80` | 转发到 Deployment |
| `kubectl port-forward --address 0.0.0.0 pod/名 8080:80` | 监听所有网卡 |
| `kubectl port-forward pod/名 :80` | 本地随机端口 |

## 六、RHEL 系与 Debian 系差异

port-forward 经 apiserver 转发，与本机发行版无关，两系**用法一致**。

## 七、新手易错点

1. **命令前台挂着别关**：port-forward 是前台进程，关了终端就断；要长期挂着用 `nohup` 或开 tmux。
2. **只绑 localhost**：默认只有本机能访问；要让别人访问加 `--address 0.0.0.0`（注意安全风险）。
3. **Pod 重建后连接断**：会话随选中 Pod 终止而结束，重跑命令即可。
4. **它不是正式暴露服务**：port-forward 只适合调试；对外提供服务用 Service/Ingress。
5. **端口冲突**：本地端口被占会报 `bind: address already in use`，换个本地端口或用 `:远程` 随机分配。
6. **走 apiserver，性能一般**：调试够用，别拿它当生产流量通道。
7. **Service 转发写端口名也行**：`8443:https` 里 `https` 是 Service 端口名，不是 Pod 端口。

## 八、相关命令与文档

- 速查页：[kubectl 命令速查](../kubectl-commands#调试与排障)
- 进容器：[exec 详解](./exec)
- 看日志：[logs 详解](./logs)
- 概念补课（Service/Ingress）：[存储与 Ingress](../../guide/container-k8s-03-storage-ingress)
- 官方命令参考：https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands#port-forward
