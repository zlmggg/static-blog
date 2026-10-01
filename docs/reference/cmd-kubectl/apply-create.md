# apply 与 create 命令详解：声明式 vs 命令式创建

> 本文是 [kubectl 命令速查](../kubectl-commands#创建与应用) 中 `kubectl apply` 与 `kubectl create` 的从 0 到 1 详解。
> 目标：把这两个最常用的"创建/更新资源"命令讲清楚，多看几遍后，你在服务器上敲 `--help` 就知道该用哪个选项。
> 环境依据：kubectl 客户端，对应 **Kubernetes 1.35**（本机沙箱未安装，选项依据 K8s 官方命令参考核实；示例输出均为「示意，据 K8s 官方文档」）。

## 一、命令是干什么的

这两个都是"往集群里放资源"，但思路完全不同：

- **`kubectl apply -f 文件.yaml`**：**声明式**。你维护一份 YAML 清单，反复 apply；已存在就更新，不存在就创建。**生产推荐**，配置即代码。
- **`kubectl create`**：**命令式**。一条命令直接建某个具体资源，适合临时快速建（建个 ns、建个 configmap）。

> 类比：`apply` 像"我告诉系统我要的终态长这样，你帮我对齐"；`create` 像"立刻给我建一个"。日常生产 90% 用 `apply`。

## 二、命令语法

```bash
kubectl apply (-f 文件 | -k 目录) [选项]
kubectl create <子命令> 名称 [选项]
```

常用 create 子命令：`deployment`、`namespace`、`configmap`、`secret generic|docker-registry|tls`、`service`、`job`、`cronjob`、`role/clusterrole/binding`。

```bash
kubectl apply -f nginx.yaml
kubectl create namespace dev
```

## 三、选项全表（对照 `kubectl apply/create --help`）

### 1. apply：从哪取配置

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-f 文件`，`--filename` | 从文件创建/更新，可传 URL、目录、`-`(stdin) | 最常用 |
| `-k 目录`，`--kustomize` | 按 kustomization 目录 | 用 kustomize 多环境管理 |
| `-R`，`--recursive` | 递归处理 `-f` 目录 | 目录套目录 |
| `-l 标签`，`--selector` | 配合 `--prune`，只 prune 匹配标签的 | 见下 |

### 2. apply：试运行与删除策略

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `--dry-run=client` | 只打印会发什么，不发请求 | 本地试清单 |
| `--dry-run=server` | 发到服务端校验但不持久化 | 服务端校验 |
| `--prune` | 自动删掉"清单里没有、但由 apply 管着"的资源 | 声明式对齐（Alpha，慎用） |
| `--prune-allowlist=组/版本/种类` | 限定 prune 范围 | 防止误删 |
| `--force` | 跳过优雅删除直接删（配合 prune/替换） | 卡住时强删（危险） |
| `--server-side` | 用服务端 apply（字段管理） | 大清单、多方管理字段时 |
| `--validate=strict\|warn\|ignore` | 输入校验严格度 | 默认 strict |

### 3. create 子命令常用选项

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `--image=镜像`（deployment） | Deployment 跑哪个镜像 | 建 deployment 必填 |
| `--replicas=N`，`-r` | 副本数，默认 1 | 建 deploy 时 |
| `--from-file=路径`（configmap/secret） | 从文件建 | 把配置文件打进 cm |
| `--from-literal=k=v` | 从字面量建 | `--from-literal=app=nginx` |
| `--from-env-file=文件` | 从 env 文件建 | 批量 key=value |
| `--docker-server/--docker-username/--docker-password`（secret docker-registry） | 仓库拉取凭证 | 私有镜像仓库 |
| `--cert=--key=`（secret tls） | TLS 证书/私钥 | 建 Ingress TLS secret |
| `--dry-run=client -o yaml` | 生成 YAML 不创建 | 生成底稿 |

## 四、由浅入深的典型示例

### 示例 1：apply 一份清单（最常用）

```bash
kubectl apply -f nginx.yaml
```

输出（示意，据 K8s 官方文档）：

```text
deployment.apps/nginx created
service/nginx created
```

> 文件里有几个资源就建/更新几个。改了 YAML 再跑一遍同一条命令即可更新。

### 示例 2：apply 整个目录

```bash
kubectl apply -f ./manifests/
```

> 目录下所有 `.yaml` 都会被 apply。

### 示例 3：用 kustomization

```bash
kubectl apply -k ./overlays/prod/
```

> kustomize 管理的多环境，`-k` 指定 overlay 目录。

### 示例 4：dry-run 先看会变什么

```bash
kubectl apply -f nginx.yaml --dry-run=client
```

> 不真正下发，只打印。想在服务端校验就 `--dry-run=server`。

### 示例 5：声明式对齐（prune，慎用）

```bash
kubectl apply --prune -f manifests/ -l app=nginx
```

> 会把"打了 `app=nginx` 标签、但不在 manifests/ 里"的资源自动删掉。**Alpha 功能，务必先 `--dry-run` 看清楚再真跑**。

### 示例 6：create 一个命名空间

```bash
kubectl create namespace dev
```

输出（示意，据 K8s 官方文档）：

```text
namespace/dev created
```

### 示例 7：create 一个 Deployment

```bash
kubectl create deployment my-dep --image=nginx --replicas=3
```

> 一条命令起 3 副本 nginx。正经部署还是建议 apply YAML。

### 示例 8：create configmap（从字面量）

```bash
kubectl create configmap my-config --from-literal=app=nginx --from-literal=port=80
```

> 把 key=value 打包成 ConfigMap 给 Pod 挂环境变量/文件。

### 示例 9：create secret（从字面量 / 从文件）

```bash
kubectl create secret generic db-secret --from-literal=username=admin --from-literal=password=s3cr3t
kubectl create secret tls my-tls --cert=tls.crt --key=tls.key
```

> generic 存任意键值；tls 存证书对；docker-registry 存私有仓库拉取凭证。

### 示例 10：create --dry-run 生成 YAML 底稿

```bash
kubectl create deployment my-dep --image=nginx --dry-run=client -o yaml > my-dep.yaml
```

> 不真建，把生成的 Deployment YAML 存成文件，以后就 `apply -f my-dep.yaml` 维护。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `kubectl apply -f 文件.yaml` | 声明式创建/更新（**最常用**） |
| `kubectl apply -f 目录/` | 应用目录下所有清单 |
| `kubectl apply -k overlay/` | kustomize 多环境 |
| `kubectl apply -f 文件 --dry-run=server` | 服务端校验不落地 |
| `kubectl create namespace dev` | 建命名空间 |
| `kubectl create deployment 名 --image=镜像` | 快速建 Deployment |
| `kubectl create configmap 名 --from-literal=k=v` | 建配置 |
| `kubectl create secret generic 名 --from-literal=k=v` | 建密钥 |
| `kubectl create deploy 名 --image=镜像 --dry-run=client -o yaml` | 生成 YAML 底稿 |

## 六、RHEL 系与 Debian 系差异

`apply`/`create` 操作集群，两系**用法一致**。一个概念区别（不是系统差异）：

- `apply` 需要资源有 `last-applied-configuration` 注解才能做三方 diff；用 `create` 建的资源如果当初没加 `--save-config`，第一次 `apply` 时可能提示要先 `--save-config` 或重新 apply。
- `--prune` 是 Alpha 功能，各版本成熟度不同，1.35 仍标记 Alpha，生产慎用。

## 七、新手易错点

1. **`create` 不能重复建同名资源**：已存在会报 `AlreadyExists`；要更新用 `apply` 或 `edit`。
2. **`apply` 和 `create` 混用会漂移**：一会 `create` 命令式改、一会 `apply` YAML，容易互相覆盖；一个资源建议只用一种方式管理。
3. **`--prune` 是危险功能**：会自动删资源，没 `--dry-run` 先看千万别直接上。
4. **`--dry-run=client` 不做服务端校验**：字段写错可能本地不报错，到 server 才炸；重要清单用 `--dry-run=server`。
5. **secret 用 `--from-literal` 会进 shell 历史**：密码类建议用 `--from-file` 或环境变量传入，避免泄露。
6. **apply 是声明式，别拿它当一次性脚本**：同一清单反复 apply 是正常用法，不是错误。
7. **YAML 里 `---` 分隔多文档**：一个文件写多个资源时用 `---` 分隔，apply 会逐个处理。

## 八、相关命令与文档

- 速查页：[kubectl 命令速查](../kubectl-commands#创建与应用)
- 直接在线改资源：[edit 详解](./edit)
- 改镜像/滚动发布：[rollout 与 set 详解](./rollout-set)
- 删资源：[delete 详解](./delete)
- 概念补课：[K8s 架构与集群](../../guide/container-k8s-01-architecture-cluster)
- 官方命令参考：https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands#apply
