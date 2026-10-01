# kubectl edit 命令详解：在线直接改集群里的资源

> 本文是 [kubectl 命令速查](../kubectl-commands#编辑伸缩与删除) 中 `kubectl edit` 的从 0 到 1 详解。
> 目标：把 `kubectl edit --help` 里的每个选项讲清楚，多看几遍后，你在服务器上敲 `kubectl edit --help` 就知道该用哪个选项。
> 环境依据：kubectl 客户端，对应 **Kubernetes 1.35**（本机沙箱未安装，选项依据 K8s 官方命令参考核实；示例输出均为「示意，据 K8s 官方文档」）。

## 一、命令是干什么的

`edit` 把集群里某个资源**拉下来，用本机默认编辑器打开，你改完保存，它自动把改动提交回 apiserver**。适合临时、快速地调一个线上资源，不用专门准备 YAML 文件。

- 临时把 Deployment 副本数从 2 改成 4：`kubectl edit deploy nginx`
- 临时改个镜像 tag：edit 里找到 image 字段改了保存即可

> 类比：`edit` 像 `crontab -e`——打开一个临时文件，改完存盘就生效，不用自己找文件在哪。但注意：**edit 改的是集群里的活对象，不是你的清单文件**，改完别忘同步回 Git 里的 YAML。

## 二、命令语法

```bash
kubectl edit (资源/名称 | -f 文件)
```

- `资源/名称`：如 `deployment/nginx`、`svc/registry`、`job.v1.batch/myjob`；
- 打开编辑器：默认 `vi`（Linux）/`notepad`（Windows），可用 `KUBE_EDITOR` 或 `EDITOR` 环境变量改；
- 保存退出即生效；不保存（`:q!`）则不改动。

```bash
kubectl edit deployment/nginx
```

## 三、选项全表（对照 `kubectl edit --help`）

### 1. 编辑哪个资源

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `资源/名称` | 编辑集群里的活资源 | 最常用 |
| `-f 文件`，`--filename` | 编辑本地文件对应的资源 | 对着清单改 |
| `-k 目录`，`--kustomize` | 按 kustomization 目录 | kustomize 场景 |

### 2. 输出格式与行为

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-o yaml`（默认） | 以 YAML 打开编辑 | 默认 |
| `-o json` | 以 JSON 打开编辑 | 习惯 JSON 时 |
| `--save-config` | 把当前配置存进注解，便于以后 apply | 想让这资源以后能 apply 管理 |
| `--windows-line-endings` | 强制 Windows 换行 | Windows 上跨平台编辑 |
| `--subresource=status` | 只编辑 status 子资源 | 改状态子资源（alpha） |
| `--validate=strict\|warn\|ignore` | 保存前校验严格度 | 默认 strict |

## 四、由浅入深的典型示例

### 示例 1：编辑一个 Service

```bash
kubectl edit svc/registry
```

> 会弹出 vi，显示这个 Service 的完整 YAML；找到 `port:` 改成想要的值，`:wq` 保存退出。

输出（示意，据 K8s 官方文档）：

```text
service/registry edited
```

### 示例 2：换个编辑器（nano）

```bash
KUBE_EDITOR="nano" kubectl edit svc/registry
```

> 不熟 vi 就用环境变量指定 nano，免得到了 vi 里不会退。

### 示例 3：编辑 Deployment 并保存配置注解

```bash
kubectl edit deployment/mydeployment -o yaml --save-config
```

> `--save-config` 让这次编辑的内容写进 `last-applied-configuration` 注解，以后才能对它用 `kubectl apply` 做三方 diff。

### 示例 4：指定 API 版本编辑

```bash
kubectl edit job.v1.batch/myjob -o json
```

> 用哪个 API 版本取下来就用哪个版本编辑；多版本资源时写全 `job.v1.batch/myjob`。

### 示例 5：只编辑 status 子资源

```bash
kubectl edit deployment mydeployment --subresource='status'
```

> 一般不用，特殊调试时才碰 status 子资源。

### 示例 6：编辑后想知道改了什么 patch

```bash
kubectl edit deployment/nginx --output-patch
```

> 保存后会额外打印这次实际提交的 patch 内容，便于核对改动。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `kubectl edit deploy/名` | 在线改 Deployment |
| `kubectl edit svc/名` | 在线改 Service |
| `KUBE_EDITOR=nano kubectl edit deploy/名` | 用 nano 编辑 |
| `kubectl edit deploy/名 --save-config` | 编辑并存注解 |
| `kubectl edit deploy/名 -o json` | JSON 格式编辑 |

## 六、与 apply 的区别（重点）

| 维度 | `kubectl edit` | `kubectl apply -f 文件` |
|---|---|---|
| 改的对象 | 集群里的活对象 | 你本地维护的 YAML 文件 |
| 配置即代码 | 否，改完文件里没有 | 是，清单在 Git 里 |
| 适合 | 临时紧急调一下 | 日常、可追溯、可评审 |
| 多人协作 | 容易互相覆盖 | 走 Git PR，可评审 |

**原则**：线上紧急救场可以 `edit`，但改完**一定要把改动同步回仓库里的 YAML**，否则下次 `apply` 会把你的 edit 覆盖掉。

## 七、新手易错点

1. **改完没同步回 YAML**：edit 直接改了活对象，但仓库里的清单没变；下次 `apply -f` 会把 edit 的内容冲掉。改完记得同步清单。
2. **vi 里不会退**：不熟就 `KUBE_EDITOR=nano`；误进 vi 想不保存退出是 `:q!`。
3. **保存报错 ` conflict`**：说明你编辑期间别人改了这个资源，kubectl 会把你的改动存成临时文件，需要重新 `edit` 拉最新版再改。
4. **别 edit `status` 或 `metadata.resourceVersion`**：这些是系统字段，乱改会冲突。
5. **edit 是"改活对象"**：对 Deployment 改 `spec.replicas` 会触发滚动/扩缩，不是纯文本操作。
6. **不保存就什么都没发生**：`:q!` 退出不会改集群，放心试。

## 八、相关命令与文档

- 速查页：[kubectl 命令速查](../kubectl-commands#编辑伸缩与删除)
- 声明式管理：[apply 与 create 详解](./apply-create)
- 改镜像/资源：[rollout 与 set/patch 详解](./rollout-set)
- 扩缩容：[scale 详解](./scale)
- 概念补课：[K8s 架构与集群](../../guide/container-k8s-01-architecture-cluster)
- 官方命令参考：https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands#edit
