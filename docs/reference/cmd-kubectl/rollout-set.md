# rollout / set / patch 命令详解：滚动发布、回滚与局部改字段

> 本文是 [kubectl 命令速查](../kubectl-commands#编辑伸缩与删除) 中 `kubectl rollout`、`kubectl set`、`kubectl patch` 的从 0 到 1 详解。
> 目标：把这组"改工作负载"的命令讲清楚，多看几遍后，你在服务器上敲 `--help` 就知道该用哪个选项。
> 环境依据：kubectl 客户端，对应 **Kubernetes 1.35**（本机沙箱未安装，选项依据 K8s 官方命令参考核实；示例输出均为「示意，据 K8s 官方文档」）。

## 一、命令是干什么的

这一组负责**安全地更新线上服务**：

- `rollout`：管 Deployment/DaemonSet/StatefulSet 的发布过程——看状态、看历史、回滚、重启、暂停；
- `set`：局部改工作负载的字段——换镜像、改资源限制、改环境变量、改 ServiceAccount、改绑定主体；
- `patch`：用一小段 JSON/YAML 精确改某个字段，不用整份 apply。

> 类比：`rollout` 像"版本发布流水线"——发版、看进度、出问题回滚；`set image` 像"只换个 App 安装包"；`patch` 像"只改注册表某一个键值"。

## 二、命令语法

```bash
kubectl rollout status|history|undo|restart|pause|resume 资源/名
kubectl set image|resources|env|selector|subject|serviceaccount 资源/名 键=值...
kubectl patch 资源/名 -p '片段' [--type strategic|merge|json]
```

## 三、选项全表（对照 `--help`）

### 1. rollout 子命令

| 子命令 | 中文含义 | 什么场景用 |
|---|---|---|
| `status 资源/名` | 盯着发布直到完成（默认 watch） | 发版后等它就绪 |
| `history 资源/名` | 看发布历史版本 | 知道有几个 revision |
| `history ... --revision=N` | 看第 N 版的具体配置 | 回滚前对照 |
| `undo 资源/名` | 回滚到上一版 | 发版出问题 |
| `undo ... --to-revision=N` | 回滚到指定版本 | 不只是上一版 |
| `restart 资源/名` | 滚动重启（重建 Pod） | 不换镜像也要重启加载配置 |
| `pause 资源/名` | 暂停，后续更新不生效 | 一次改多处前先暂停 |
| `resume 资源/名` | 恢复被暂停的发布 | 改完放开 |
| `--timeout=时长`（status） | 等发布的超时 | 如 `--timeout=2m` |
| `-l 标签`（restart） | 按标签批量 restart | 如 `restart deploy -l app=nginx` |

### 2. set 子命令

| 子命令 | 中文含义 | 什么场景用 |
|---|---|---|
| `set image 资源/名 容器=镜像` | 改容器镜像（触发滚动发布） | 发新镜像（最常用） |
| `set resources` | 改 CPU/内存 requests/limits | 调资源配额 |
| `set env 资源/名 K=V` | 改 Pod 模板环境变量 | 注入/改配置 |
| `set selector` | 改 Service 的 selector | 较少用 |
| `set subject` | 改 RoleBinding/ClusterRoleBinding 的用户/组/SA | 调授权主体 |
| `set serviceaccount` | 改 Pod 用的 ServiceAccount | 换身份 |
| `--local` | 本地算结果不连 apiserver | 干跑看 YAML |
| `-c 容器`（resources/env） | 指定改哪个容器 | 多容器 |
| `--all` | 选该类型所有资源 | 批量 |

### 3. patch

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-p 片段`，`--patch` | 要打的补丁内容（JSON/YAML） | 最核心 |
| `--patch-file=文件` | 补丁从文件读 | 补丁较长时 |
| `--type=strategic\|merge\|json` | 补丁类型，默认 strategic | 见下 |
| `--subresource=status\|scale` | 改子资源 | 如 patch scale 改副本数 |

三种补丁类型区别：

- `strategic`（默认）：K8s 原生策略合并，对 Pod 列表会按 merge key（如容器名）智能合并；
- `merge`（JSON Merge Patch）：简单地覆盖字段；
- `json`（JSON Patch）：用 `op: add/replace/remove` 精确操作数组下标。

## 四、由浅入深的典型示例

### 示例 1：换镜像发新版本（最常用）

```bash
kubectl set image deployment/nginx nginx=nginx:1.28
```

输出（示意，据 K8s 官方文档）：

```text
deployment.apps/nginx image updated
```

> 改 Deployment 模板里 nginx 容器的镜像，自动触发滚动发布。

### 示例 2：盯发布进度直到完成

```bash
kubectl rollout status deployment/nginx
```

输出（示意，据 K8s 官方文档）：

```text
Waiting for deployment "nginx" rollout to finish: 2 of 3 updated replicas are available...
deployment "nginx" successfully rolled out
```

> 命令会卡住直到滚动完成；想不等就 `--watch=false`。

### 示例 3：看发布历史

```bash
kubectl rollout history deployment/nginx
```

输出（示意，据 K8s 官方文档）：

```text
REVISION  CHANGE-CAUSE
1         kubectl apply --filename=nginx.yaml
2         kubectl set image deployment/nginx nginx=nginx:1.28
```

### 示例 4：回滚到上一版

```bash
kubectl rollout undo deployment/nginx
```

> 发新版挂了，一键退回上一个 revision。

### 示例 5：回滚到指定版本

```bash
kubectl rollout undo deployment/nginx --to-revision=1
```

> 不只退回上一版，可以退回任意历史 revision。

### 示例 6：滚动重启（不换镜像）

```bash
kubectl rollout restart deployment/nginx
```

> 改了 ConfigMap 想让 Pod 重新加载，但镜像没变——用 restart 滚动重建 Pod，而不是手动删。

### 示例 7：暂停 / 恢复

```bash
kubectl rollout pause deployment/nginx
kubectl set env deployment/nginx DB_HOST=10.0.0.5
kubectl set resources deployment/nginx -c nginx --limits=cpu=500m
kubectl rollout resume deployment/nginx
```

> 先 pause，连改几处，再 resume 一次发布，避免改一处发一次。

### 示例 8：改资源限制

```bash
kubectl set resources deployment/nginx -c=nginx --limits=cpu=200m,memory=512Mi --requests=cpu=100m,memory=256Mi
```

> 给 nginx 容器设 request/limit。

### 示例 9：patch 改副本数（merge patch）

```bash
kubectl patch deployment nginx-deployment --subresource='scale' --type='merge' -p '{"spec":{"replicas":2}}'
```

> 用 patch 直接改 scale 子资源。

### 示例 10：patch 改镜像（strategic）

```bash
kubectl patch pod valid-pod -p '{"spec":{"containers":[{"name":"app","image":"nginx:1.28"}]}}'
```

> strategic patch 会按容器名智能合并，不用写整个 containers 数组。

### 示例 11：json patch 按下标改

```bash
kubectl patch pod valid-pod --type='json' -p='[{"op":"replace","path":"/spec/containers/0/image","value":"nginx:1.28"}]'
```

> `op` 支持 add/replace/remove，`path` 是 JSON 指针路径。

### 示例 12：改绑定主体

```bash
kubectl set subject clusterrolebinding admin --serviceaccount=default:serviceaccount1
```

> 把 ClusterRoleBinding admin 绑到某个 ServiceAccount。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `kubectl set image deploy/名 容器=镜像` | 换镜像发版（**最常用**） |
| `kubectl rollout status deploy/名` | 等发布完成 |
| `kubectl rollout history deploy/名` | 看历史版本 |
| `kubectl rollout undo deploy/名` | 回上一版 |
| `kubectl rollout undo deploy/名 --to-revision=1` | 回指定版 |
| `kubectl rollout restart deploy/名` | 滚动重启 |
| `kubectl rollout pause/resume deploy/名` | 暂停/恢复 |
| `kubectl set resources deploy/名 -c 容器 --limits=...` | 改资源 |
| `kubectl patch deploy 名 -p '...'` | 局部改字段 |

## 六、RHEL 系与 Debian 系差异

这些命令操作集群，两系**用法一致**。版本说明：临时容器（`kubectl debug`）自 1.25 起 GA，1.35 稳定可用；`rollout restart` 自 1.21 起可用，老版本没有，别在很老的集群上用。

## 七、新手易错点

1. **set image 后不看 status**：发版可能卡住（镜像拉不下来、探针失败），发完一定 `rollout status`。
2. **undo 回到的版本必须在 history 里**：revision 太多时旧的可能被 GC，`--to-revision` 前先 `history` 看。
3. **patch 三种类型别乱用**：改列表（containers/volumes）优先用默认 strategic；改 CRD 时 strategic 不支持，要用 merge/json。
4. **pause 后忘了 resume**：暂停期间所有更新都不生效，排障半天没反应先看是不是 pause 了。
5. **set image 的 `容器=镜像` 容器名别写错**：名字对不上会报 container not found。
6. **改完镜像记得记 CHANGE-CAUSE**：加 `--record` 能把命令写进注解，history 里才看得懂每版改了啥。
7. **patch 直接改活对象**：和 edit 一样，改完要同步回 Git 清单，否则下次 apply 被覆盖。

## 八、相关命令与文档

- 速查页：[kubectl 命令速查](../kubectl-commands#编辑伸缩与删除)
- 手动扩缩容：[scale 详解](./scale)
- 声明式管理：[apply 与 create 详解](./apply-create)
- 进容器调试：[exec 详解](./exec)
- 概念补课（工作负载滚动更新）：[Pod 与服务发现](../../guide/container-k8s-02-pod-service-discovery)
- 官方命令参考：https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands#rollout
