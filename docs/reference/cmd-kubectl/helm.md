# Helm 基础命令详解：K8s 的包管理器

> 本文是 [kubectl 命令速查](../kubectl-commands#helm) 中 Helm 的从 0 到 1 详解（站内云原生命令表亦基于 **Helm 4.3**）。
> 目标：把 Helm 最常用的一组命令讲清楚，多看几遍后，你在服务器上敲 `helm --help` 就知道该用哪个选项。
> 环境依据：**Helm 4.3**（已 web.fetch https://helm.sh/docs/ 核实，当前文档首页标注 Version: 4.3.0；本机沙箱未安装 Helm，示例输出为「示意，据官方文档」）。

## 一、命令是干什么的

Helm 是 K8s 的**包管理器**。你不用手写几十份 YAML 去装一个应用（比如 nginx-ingress、Prometheus），而是：

- `helm repo add` 加软件仓库（像 apt 源）；
- `helm install 名 chart` 一键装一套应用；
- `helm upgrade` 升级；`helm uninstall` 卸载；`helm list` 看装了啥。

被管理的"安装包"叫 **Chart**，装出来的一套实例叫 **Release**。

> 类比：Helm 之于 K8s，就像 `apt`/`yum` 之于 Linux 系统——Chart 是软件包，Release 是你装上去的那个实例。一个 Chart 可以在同一集群里装成多个 Release。

> 版本说明：Helm 4 相对 v3 有架构层面的 breaking change，但本文涉及的 repo/install/upgrade/uninstall/list 基础语法与 v3 通用；站内 cloudnative-commands.md 已声明按 Helm 4.3，本文据此。

## 二、命令语法

```bash
helm repo add|update|search ...
helm install <release名> <chart> [--set k=v] [-f values.yaml] [flags]
helm upgrade <release名> <chart> [flags]
helm uninstall <release名>
helm list
```

- `release名`：你给这次安装起的名字；
- `chart`：`仓库名/chart名` 或本地路径或 URL；
- 配置覆盖：`--set`（命令行临时设）或 `-f values.yaml`（整份值文件）。

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
```

## 三、选项全表（对照 `helm --help`）

### 1. 仓库

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `repo add 名 URL` | 添加 chart 仓库 | 第一次用某源 |
| `repo update` | 拉取最新仓库索引 | 装之前先更新索引 |
| `repo search 关键词`，`search repo` | 在仓库里搜 chart | 找包 |
| `repo list` / `repo remove 名` | 列/删仓库 | 管理源 |

### 2. 安装与升级

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `install 名 chart` | 安装一个 Release | 最核心 |
| `upgrade 名 chart` | 升级已有 Release | 改配置/换版本 |
| `--set k=v` | 命令行覆盖单个值 | 临时改一两个参数 |
| `-f values.yaml`，`--values` | 用整份 values 文件覆盖 | 复杂配置 |
| `-n 命名空间`，`--namespace` | 指定命名空间 | 必带（或用 --create-namespace） |
| `--create-namespace` | 命名空间不存在就建 | 一键安装到新 ns |
| `--wait` | 等所有资源 Ready 才算完成 | 脚本里等装完 |
| `--version=ver` | 装指定 chart 版本 | 固定版本 |
| `--dry-run --debug` | 本地渲染不真正装 | 先看会生成什么 |
| `--install`（upgrade 用） | upgrade 时若不存在则安装 | 让 upgrade 兼具安装能力 |

### 3. 查看与卸载

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `list`，`ls` | 列已装 Release | 看装了啥 |
| `list -A` | 所有命名空间 | 全局看 |
| `status 名` | 看某 Release 状态 | 排查装完对不对 |
| `get values 名` | 看生效的 values | 确认配置 |
| `history 名` | 看 Release 修订历史 | 升级历史 |
| `rollback 名 REVISION` | 回滚到某版本 | 升级出问题 |
| `uninstall 名` | 卸载 Release | 删除 |

## 四、由浅入深的典型示例

### 示例 1：加仓库并更新索引

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
```

输出（示意，据官方文档）：

```text
"bitnami" has been added to your repositories
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "bitnami" chart repository
```

### 示例 2：搜索 chart

```bash
helm search repo nginx
```

输出（示意，据官方文档）：

```text
NAME                            CHART VERSION   APP VERSION   DESCRIPTION
bitnami/nginx                   15.x.x          1.27.x        NGINX Open Source...
```

### 示例 3：安装一个 Release

```bash
helm install my-nginx bitnami/nginx -n web --create-namespace
```

输出（示意，据官方文档）：

```text
NAME: my-nginx
LAST DEPLOYED: Wed Sep 30 10:00:00 2026
NAMESPACE: web
STATUS: deployed
REVISION: 1
```

> `STATUS: deployed` 表示装好了；`--create-namespace` 顺手把 `web` ns 建出来。

### 示例 4：用 --set 覆盖配置

```bash
helm install my-nginx bitnami/nginx --set service.type=NodePort --set replicaCount=2
```

> 不改 values 文件，命令行直接盖两个值。

### 示例 5：用 values 文件安装

```bash
helm install my-nginx bitnami/nginx -f my-values.yaml -n web
```

> 复杂配置写进 `my-values.yaml`，用 `-f` 喂进去；生产推荐这种方式（配置即代码）。

### 示例 6：升级（改配置后）

```bash
helm upgrade my-nginx bitnami/nginx -f my-values.yaml --set replicaCount=3
```

> 改了 values 后 upgrade，Helm 会做滚动更新并把 REVISION 加一。

### 示例 7：等待安装完成

```bash
helm install my-nginx bitnami/nginx --wait --timeout=5m
```

> `--wait` 会等到所有 Pod/Service Ready 才返回，CI/脚本里用。

### 示例 8：列已装 Release

```bash
helm list -n web
```

输出（示意，据官方文档）：

```text
NAME       NAMESPACE  REVISION  UPDATED                                 STATUS    CHART         APP VERSION
my-nginx   web        1         2026-09-30 10:00:00.000 +0800           deployed  nginx-15.x.x  1.27.x
```

### 示例 9：卸载

```bash
helm uninstall my-nginx -n web
```

输出（示意，据官方文档）：

```text
release "my-nginx" uninstalled
```

### 示例 10：先 dry-run 看会渲染出什么

```bash
helm install my-nginx bitnami/nginx -f my-values.yaml --dry-run --debug
```

> 不真正装，把渲染出来的 K8s 清单和 debug 信息打印出来，排模板错误。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `helm repo add 名 URL && helm repo update` | 加源并更新（**第一步**） |
| `helm search repo 关键词` | 搜 chart |
| `helm install 名 chart -n ns --create-namespace` | 安装 |
| `helm install 名 chart --set k=v` | 临时覆盖值 |
| `helm install 名 chart -f values.yaml` | 用值文件 |
| `helm upgrade 名 chart -f values.yaml` | 升级 |
| `helm list -A` | 看所有 Release |
| `helm status 名` | 看状态 |
| `helm uninstall 名` | 卸载 |
| `helm rollback 名 N` | 回滚 |

## 六、RHEL 系与 Debian 系差异

Helm 是个二进制客户端，两系用法一致，只是安装方式不同（官方仓库脚本 / 下载二进制）。Helm 4 相对 v3 的 breaking change 主要在服务端/架构侧；本文基础命令在两系、在 v3/v4 上语法通用。

## 七、新手易错点

1. **忘了 `helm repo update`**：刚 add 完源直接 install 可能报 chart not found，先 update 索引。
2. **`--set` 和 `-f` 混用顺序**：后写的覆盖先写的；`--set` 优先级高于 `-f`，注意别互相覆盖出意外。
3. **不指定 `-n` 装到 default**：Release 默认进当前上下文的命名空间；多环境一定显式 `-n`。
4. **装了不知道装哪了**：`helm list -A` 全局找。
5. **升级前没看 values**：`helm get values 名` 先确认当前生效配置，别拿旧 values 直接 upgrade 覆盖掉别人的改动。
6. **`--wait` 卡住**：依赖镜像拉不下来或探针不过时会一直等到 `--timeout`，先用 `--dry-run --debug` 预检。
7. **卸载会删资源但 PVC 可能保留**：有些 chart 的 PVC 默认保留，避免误删数据；要连数据一起删需显式配置。
8. **Helm 管理的资源别用 kubectl 直接改**：直接 `kubectl edit` 改了，下次 `helm upgrade` 会被 Helm 的期望覆盖；要改就改 values。

## 八、相关命令与文档

- 速查页：[kubectl 命令速查](../kubectl-commands#helm)
- 云原生排障命令（含 helm history/rollback/template）：[cloudnative-commands](../cloudnative-commands)
- 声明式部署：[apply 与 create 详解](./apply-create)
- 概念补课：[K8s 架构与集群](../../guide/container-k8s-01-architecture-cluster)
- Helm 官方文档：https://helm.sh/docs/ （Helm 4：https://helm.sh/docs/4.3/）
