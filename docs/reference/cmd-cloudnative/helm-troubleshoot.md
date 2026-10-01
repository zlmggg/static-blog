# Helm 排障命令详解：status / history / rollback / get / template / lint

> 本文是 [云原生排障命令速查](../cloudnative-commands) 中「Helm（release 排障）」一组命令的从 0 到 1 详解，本篇一次讲清 `helm status`、`helm history`、`helm rollback`、`helm get`、`helm template`、`helm lint` 与 `--dry-run`。
> 目标：把这些命令的每个选项讲清楚，看多了以后，一个 chart 装上去不灵时，你知道先用哪条、再用哪条把它查明白、退回去。
> 环境依据：Helm 4.3（站内 2026-09 版本基准；helm.sh 官方命令文档当前渲染版本号为 4.3.0，由 spf13/cobra 于 2026-09-09 自动生成）。本沙箱未装 helm，以下选项与输出均据官方文档核对，示例标注「据官方文档」。

## 一、命令是干什么的

Helm 是 Kubernetes 的「包管理器」：一个 chart 就是一坨带模板的 K8s 清单 + 默认参数，`helm install/upgrade` 把它渲染成真正的 Deployment、Service、Ingress 等对象提交给集群。一个被 Helm 管理的应用实例叫一个 **release**。

排障时最常见的烦恼是：「我 `helm upgrade` 之后服务起不来，到底是哪一步坏了？」这一组命令就是用来回答下面几个问题的：

- **这个 release 现在到底是什么状态？** → `helm status`
- **它过去改过几版、每版成没成功？** → `helm history`
- **退回上一个好版本怎么退？** → `helm rollback`
- **集群里现在实际跑的清单和生效参数长什么样？** → `helm get manifest / values`
- **不碰集群，光在本地把模板渲出来看对不对？** → `helm template`、`helm lint`、`--dry-run`

> 类比：Helm 之于 K8s，就像 `apt/yum` 之于系统包，`helm history/rollback` 就像「软件商店的历史版本记录 + 一键回退」，`helm template` 就像 `make -n`（干跑一遍看会做什么，不真做）。

## 二、命令语法

```bash
helm status RELEASE_NAME [flags]
helm history RELEASE_NAME [flags]
helm rollback RELEASE_NAME [REVISION] [flags]
helm get SUBCOMMAND RELEASE_NAME [flags]
helm template CHART [flags]
helm lint CHART [flags]
```

- `RELEASE_NAME`：你 `helm install` 时起的 release 名字（用 `helm list` 查）；
- `REVISION`：修订号（history 里那个 `REVISION` 列）；省略或写 `0` 表示「退回上一版」；
- `CHART`：本地 chart 目录、打包好的 `.tgz`，或 `repo/chart` 这种仓库引用；
- 全局可加 `-n, --namespace` 指定命名空间（不写就用当前 kubeconfig 的命名空间）。

最基础的一条：

```bash
helm status my-release
```

## 三、选项全表（对照官方 `helm xxx --help`）

下面按命令分组列出。短选项与等价长选项写在同一格。

### 1. `helm status`：看 release 当前状态

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-o FORMAT`，`--output=FORMAT` | 输出格式：`table`/`json`/`yaml`（默认 table） | 想把状态喂给脚本、或看完整资源列表时用 `json` |
| `--revision int` | 查看**指定历史修订**的状态，而不是当前版 | 怀疑回退后状态不对、想对照某一版时 |
| `-n`，`--namespace` | 指定命名空间 | release 不在默认命名空间时（也可 `helm -n ns status`） |
| `--kube-context` | 用哪个 kubeconfig context | 本地配了多个集群时 |

> status 会打印：上次部署时间、所在命名空间、release 状态（`deployed`/`failed`/`pending-install`/`pending-upgrade`/`pending-rollback`/`superseded`/`uninstalled` 等）、修订号、说明、该 release 包含的资源列表，以及 chart 自带的 notes。

### 2. `helm history`：看修订历史

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-o FORMAT`，`--output=FORMAT` | 输出格式 `table`/`json`/`yaml` | 记录每次版本变化做留痕时 |
| `--max` | 只显示最近 N 条 | 历史很长时翻最近几版 |

> history 输出核心是 `REVISION`（修订号）、`UPDATED`、`STATUS`、`CHART`、`DESCRIPTION` 几列。回滚就靠这里的 `REVISION`。

### 3. `helm rollback`：回退到某修订

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `REVISION`（位置参数） | 回退到第几版；**省略或 0 = 退回上一版** | 刚 upgrade 炸了，直接 `helm rollback name` |
| `--wait` | 等资源就绪才算成功（可带策略 `watcher`/`hookOnly`/`legacy`） | 生产回滚，要确认 Pod 真起来了 |
| `--wait-for-jobs` | 配合 `--wait`，连 Job 跑完一起等 | chart 里带 Job 类钩子时 |
| `--timeout DURATION` | 单个 K8s 操作超时（默认 5m0s） | 回滚卡住时放大 |
| `--no-hooks` | 回滚时**不跑 pre/post hook** | hook 本身有问题、想纯换清单时 |
| `--dry-run=client\|server` | 模拟回滚，不落盘（`client` 不连集群，`server` 在服务端模拟） | 回滚前先看会动什么 |
| `--cleanup-on-fail` | 回滚失败时清掉这次新建的资源 | 避免回滚半途留下脏资源 |
| `--description string` | 给这次回滚写条说明（≤256 字符） | history 里能看懂为什么回滚 |

### 4. `helm get`：取 release 的各类信息（带子命令）

| 子命令 | 取什么 | 什么场景用 |
|---|---|---|
| `helm get manifest NAME` | 该 release **渲染出的全部 K8s 清单** | 排查「集群里到底被渲染成了什么」（最常用） |
| `helm get values NAME` | 该 release **实际生效的 values**（只含你覆盖过的） | 确认参数到底生效没 |
| `helm get values NAME -a` | `--all`，连同 chart 默认值一起打印 | 想看完整生效值时 |
| `helm get hooks NAME` | 该 release 定义的 **helm hook**（pre-install/post-upgrade Job 等） | hook 没跑、卡住时排查 |
| `helm get notes NAME` | chart 自带的**使用说明**（install 末尾那段） | 忘了访问地址/命令时翻出来 |
| `helm get metadata NAME` | release 元数据（版本、命名空间、修订） | 脚本里取版本号 |
| `helm get all NAME` | 上面 manifest+values+hooks+notes 全打出来 | 一次性全量导出存档 |

> `helm get` 自身只有 `-h`；多数子命令支持 `--revision` 看历史某版。

### 5. `helm template`：本地渲染，不碰集群

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-f VALUES`，`--values=VALUES` | 指定 values 文件（可多次） | 用你自己的参数渲染 |
| `--set k=v` | 命令行临时覆盖单个值 | 临时改一个参数看渲染结果 |
| `--namespace` | 渲染时带上命名空间 | 模板里用到 `.Release.Namespace` 时 |
| `--show-only=KIND/NAME` | 只渲染某个资源 | 模板报错时单独看那一段 |
| `--debug` | 渲染出错时打印上下文/原始模板 | 排模板语法/函数错误 |
| `--api-versions` | 告知 cluster 支持的 API 版本 | 模板里 `lookup`/`capabilities` 相关时 |

### 6. `helm lint` 与 `--dry-run`

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `helm lint CHART` | 静态检查 chart 语法/依赖/模板问题，**不连集群** | 改完 chart 先 lint 再提交（CI 里必跑） |
| `--dry-run`（install/upgrade/rollback 通用） | 试运行：渲染并打印会提交的清单，**不真正写集群** | 上线前看「会变什么」 |
| `--debug` | 打印渲染后的清单与详细日志 | 配合 `--dry-run` 看模板到底渲成啥 |

> Helm 4 里 `--dry-run` 取值为 `none`（正常）/`client`（纯客户端模拟、不连集群）/`server`（连集群但不持久化），默认 `none`。

## 四、由浅入深的典型示例

以下示例输出为「据官方文档」或示意，本沙箱未接集群，不代表本机实跑。

### 示例 1：看一个 release 当前状态

```bash
helm status my-release
```

据官方文档，输出大致包含（示意）：

```text
NAME: my-release
LAST DEPLOYED: Tue Sep 30 10:00:00 2026
NAMESPACE: default
STATUS: deployed
REVISION: 3
TEST SUITE:     None
LAST TEST SUITE: None
NOTES:
1. Get the application URL by running:
     export POD_NAME=$(kubectl get pods --namespace default -l "app.kubernetes.io/name=my" -o jsonpath="{.items[0].metadata.name}")
```

> 先看 `STATUS`：`deployed` 才正常；`failed`/`pending-upgrade` 就要继续查。

### 示例 2：看修订历史，找该回退到哪版

```bash
helm history my-release
```

```text
REVISION    UPDATED                     STATUS          CHART           APP VERSION
1           Tue Sep 29 09:00:00 2026     deployed        my-1.0.0        1.0.0
2           Tue Sep 30 08:00:00 2026     failed          my-1.1.0        1.1.0
3           Tue Sep 30 09:30:00 2026     deployed        my-1.0.0        1.0.0
```

> 第 2 版 `failed` 了，想退回第 1 版就是 `helm rollback my-release 1`。

### 示例 3：一键回退到上一版

```bash
helm rollback my-release
```

> 省略修订号即回退到「当前版的上一版」。生产上建议加 `--wait --timeout=5m`：

```bash
helm rollback my-release 1 --wait --timeout=5m --description "回滚到 1.0.0，1.1.0 启动探针失败"
```

### 示例 4：看集群里实际渲染出的清单

```bash
helm get manifest my-release
```

> 这一步最关键：upgrade 后行为不对时，把这里渲染出的 Deployment/Service 与你预期的 values 对一遍，常常一眼看出 `image.tag`、`resources`、`env` 哪里没生效。

### 示例 5：看生效了哪些 values

```bash
helm get values my-release
```

```text
image:
  tag: "1.1.0"
replicaCount: 2
```

> 这只显示**你显式覆盖过**的值；想看连 chart 默认值在内的全量：`helm get values my-release -a`。

### 示例 6：本地干跑升级，不碰集群

```bash
helm upgrade my-release ./mychart -f values-prod.yaml --dry-run=server --debug
```

> `--dry-run=server` 会连 apiserver、渲染并 diff 出「真要提交时会变什么」，但不落盘；`--debug` 把渲染后的清单打出来。上线前强烈建议先跑一遍。

### 示例 7：纯本地渲染 + lint

```bash
helm lint ./mychart
helm template my-release ./mychart -f values-prod.yaml --debug
```

> `lint` 不连集群，只做静态体检；`template` 把模板渲成 YAML 打到屏幕，模板函数写错（如 `{{ .Values.x.y }}` 路径不存在）会在这里报错。

### 示例 8：看 hook 为什么卡住

```bash
helm get hooks my-release
```

> 升级一直 `pending-upgrade`，往往是 pre-install/post-upgrade 这个 hook Job 没成功。把这里列出来的 hook Job 名字拿到 `kubectl describe job` 去看日志。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `helm status -n ns NAME` | 看 release 现在啥状态 |
| `helm history NAME` | 列修订，找回退目标 |
| `helm rollback NAME` | 退回上一版（生产加 `--wait`） |
| `helm get manifest NAME` | 看集群里真实渲染的清单 |
| `helm get values NAME -a` | 看完整生效参数 |
| `helm template . -f v.yaml --debug` | 本地渲染排模板错 |
| `helm upgrade . --dry-run=server --debug` | 上线前预演会改什么 |
| `helm lint .` | chart 静态体检 |

## 六、RHEL 系与 Debian 系差异

Helm 是单个 Go 二进制，**RHEL/Rocky 与 Ubuntu/Debian 上用法完全一致**，没有包名或路径差异。仅需注意：

- 版本以你实际安装为准：`helm version` 看 `v4.3.x`。各发行版仓库里的 helm 可能偏旧，生产排障机建议直接从 helm.sh 官方 Release 下对应版本二进制；
- Helm 4 后端存储驱动默认 `secret`，历史条数受 `--history-max`（默认 10）与环境变量 `HELM_MAX_HISTORY` 限制；
- 本机没有 `crictl`/容器运行时时，`helm template`、`helm lint` 仍可本地用（它们不连集群）。

## 七、新手易错点

1. **`helm status` 显示 `failed` 不等于资源被删了**：失败那版的资源还在集群里，回滚前先 `helm get manifest` 看清楚。
2. **回滚不会自动清理 hook 失败现场**：卡住的 pre/post hook Job 要自己 `kubectl delete job`，否则反复 pending。
3. **`helm get values` 只看得到你改过的值**：别拿它当「全量配置」，要全量加 `-a/--all`。
4. **`--dry-run` 也分 client/server**：`client` 不连集群、不会做服务端校验；上线预演建议 `server`。
5. **`helm rollback` 本身也是一次新修订**：回滚后 `REVISION` 会 +1，不会把修订号倒回去，history 里能看到。
6. **危险提示**：`helm uninstall`、`helm rollback --force-replace`、`--replace` 会真实删/重建集群资源；先 `--dry-run` 预演，确认 PDB 与副本冗余，别把生产一次性掀掉。
7. **不要在生产长期开 `--debug`**：它打印完整渲染清单与敏感 values，日志量大，用完即关。

## 八、相关命令与文档

- 速查页：[云原生排障命令速查](../cloudnative-commands)
- 基础 kubectl 命令：[kubectl 命令速查](../kubectl-commands)
- 渲染出的清单怎么逐条解读：见 [kubectl 进阶排障](./kubectl-advanced)
- 取资源字段/输出做脚本：见 [jsonpath 与 jq](./jsonpath-jq)
- 概念与部署：[K8s 架构系列指南](../../guide/container-k8s-01-architecture-cluster)
- 官方文档：https://helm.sh/docs/ ；命令：https://helm.sh/docs/helm/helm_status/ 、https://helm.sh/docs/helm/helm_rollback/ 、https://helm.sh/docs/helm/helm_get/
