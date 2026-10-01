# kubectl run 命令详解：快速起一个临时 Pod

> 本文是 [kubectl 命令速查](../kubectl-commands#创建与应用) 中 `kubectl run` 的从 0 到 1 详解。
> 目标：把 `kubectl run --help` 里的每个选项讲清楚，多看几遍后，你在服务器上敲 `kubectl run --help` 就知道该用哪个选项。
> 环境依据：kubectl 客户端，对应 **Kubernetes 1.35**（本机沙箱未安装，选项依据 K8s 官方命令参考核实；示例输出均为「示意，据 K8s 官方文档」）。

## 一、命令是干什么的

`run` 用来**快速在集群里起一个 Pod**，跑指定镜像。它适合临时验证、跑个一次性命令、调试网络，不适合正经部署（正经部署用 Deployment，见 [apply-create 详解](./apply-create)）。

> 类比：`kubectl run` 像 `docker run`——"我就要这台机器上立刻把这个镜像跑起来看看"。区别是它跑在 K8s 集群的某个节点上，而不是你本机。

## 二、命令语法

```bash
kubectl run NAME --image=镜像 [--env="k=v"] [--port=端口] [--dry-run=server|client] [--command] -- [命令] [参数...]
```

- `NAME`：Pod 名；
- `--image`：必填，用哪个镜像；
- `--`：后面跟容器里要执行的命令。

最简单的：

```bash
kubectl run nginx --image=nginx
```

## 三、选项全表（对照 `kubectl run --help`）

### 1. 镜像与运行内容

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `--image=镜像` | 容器用的镜像（必填） | 最核心 |
| `--port=端口` | 容器暴露的端口 | 服务要被访问时 |
| `--env="K=V"` | 设环境变量，可重复 | 传配置进容器 |
| `--command` | 把 `--` 后的参数当作容器的 **command**（而非 args） | 要覆盖镜像ENTRYPOINT时 |
| `--restart=Always\|OnFailure\|Never` | 重启策略 | 跑一次性任务用 `Never` |
| `--overrides=内联JSON` | 用一段 JSON 覆盖生成的对象 | 临时改点字段不想写 YAML |

### 2. 交互与附属

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-i`，`--stdin` | 保持标准输入打开 | 进交互式容器 |
| `-t`，`--tty` | 分配 TTY | 配合 `-i` 进 shell |
| `--rm` | 容器退出后自动删 Pod | 跑一次性命令、不留垃圾 |
| `--labels="k=v,k=v"`，`-l` | 给 Pod 打标签 | 方便后续 `-l` 选中 |
| `--expose` | 同时建一个 ClusterIP Service | 起 Pod 顺便暴露端口 |
| `--image-pull-policy=策略` | 拉镜像策略 | 如 `Always`/`IfNotPresent` |

### 3. 试运行

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `--dry-run=client` | 只打印会创建的对象，不真正发请求 | 先看生成的清单长啥样 |
| `--dry-run=server` | 发到服务端做校验但不持久化 | 服务端校验字段 |
| `-o yaml` | 配合 dry-run 输出 YAML | `run --dry-run=client -o yaml > pod.yaml` 生成底稿 |

## 四、由浅入深的典型示例

### 示例 1：最基本——起一个 nginx Pod

```bash
kubectl run nginx --image=nginx
```

输出（示意，据 K8s 官方文档）：

```text
pod/nginx created
```

### 示例 2：起 Pod 并指定暴露端口

```bash
kubectl run hazelcast --image=hazelcast/hazelcast --port=5701
```

> 告诉集群这个容器要监听 5701 端口。

### 示例 3：设环境变量

```bash
kubectl run hazelcast --image=hazelcast/hazelcast --env="DNS_DOMAIN=cluster" --env="POD_NAMESPACE=default"
```

> 多个 `--env` 重复写即可。

### 示例 4：打标签

```bash
kubectl run hazelcast --image=hazelcast/hazelcast --labels="app=hazelcast,env=prod"
```

> 后面就能 `kubectl get pods -l app=hazelcast` 选中它。

### 示例 5：交互式跑一个一次性命令（像 docker run -it）

```bash
kubectl run -i -t busybox --image=busybox --restart=Never -- rm
```

> `--restart=Never`：退出后不重启；`-i -t`：进去交互。跑完 `--rm` 可自动清理。

### 示例 6：覆盖容器启动命令

```bash
kubectl run nginx --image=nginx --command -- sleep 3600
```

> 默认用镜像的 ENTRYPOINT；加 `--command --` 后，`sleep 3600` 成为容器的命令——起一个 nginx 镜像但只是挂着 sleep，用来占坑调试。

### 示例 7：dry-run 生成 YAML 底稿

```bash
kubectl run nginx --image=nginx --dry-run=client -o yaml
```

输出（示意，据 K8s 官方文档）：

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx
spec:
  containers:
  - image: nginx
    name: nginx
  restartPolicy: Always
```

> 不真正创建，只打印会生成的 YAML。重定向到文件就是一份干净底稿，改完 `kubectl apply -f` 回去。

### 示例 8：用 overrides 临时改字段

```bash
kubectl run nginx --image=nginx --overrides='{"spec":{"containers":[{"name":"nginx","image":"nginx","resources":{"limits":{"memory":"128Mi"}}}]}}'
```

> 不想写完整 YAML，就用 `--overrides` 塞一段 JSON 覆盖默认生成的对象。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `kubectl run 名 --image=镜像` | 快速起 Pod |
| `kubectl run 名 --image=镜像 --port=80` | 起 Pod 暴露端口 |
| `kubectl run 名 --image=镜像 --env=K=V` | 带环境变量 |
| `kubectl run -it busybox --image=busybox --restart=Never -- sh` | 交互式调试容器 |
| `kubectl run 名 --image=镜像 --dry-run=client -o yaml` | 生成 YAML 底稿 |
| `kubectl run 名 --image=镜像 --command -- 命令` | 覆盖启动命令 |

## 六、RHEL 系与 Debian 系差异

`run` 在集群里起 Pod，与本机发行版无关，两系**用法一致**。注意一个历史变化：老版本 `kubectl run` 加 `--generator=run-pod/v1` 之类参数来区分是起 Pod 还是 Deployment，新版本里 `kubectl run` 默认就是起 Pod；要起 Deployment 请用 `kubectl create deployment`（见 [apply-create 详解](./apply-create)）。

## 七、新手易错点

1. **`run` 起的是裸 Pod，不是 Deployment**：裸 Pod 挂了不会自愈、没有滚动更新；正经服务用 `create deployment` / `apply`。
2. **忘了 `--restart=Never` 跑一次性任务**：一次性命令跑完容器退出，默认 `Always` 会让它不停重启成 CrashLoop，跑临时任务务必 `--restart=Never`。
3. **`--` 不能省**：要传容器命令时，`--` 前面是 kubectl 选项，后面才是容器命令，不加 `--command` 时后面被当作 args。
4. **dry-run 不会真创建**：加了 `--dry-run` 放心试，不影响集群。
5. **`run` 起的 Pod 删了就没了**：临时调试完记得 `kubectl delete pod 名` 清理，或加 `--rm`。
6. **镜像名要能被节点拉到**：私有镜像记得配 imagePullSecrets，不然 `run` 出来一直 `ErrImagePull`。

## 八、相关命令与文档

- 速查页：[kubectl 命令速查](../kubectl-commands#创建与应用)
- 正经部署：[apply 与 create 详解](./apply-create)
- 进 Pod 里：[exec 详解](./exec)
- 概念补课：[Pod 与服务发现](../../guide/container-k8s-02-pod-service-discovery)
- 官方命令参考：https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands#run
