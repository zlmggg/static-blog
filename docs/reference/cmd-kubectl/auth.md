# kubectl auth 命令详解：can-i 与 RBAC 权限排障

> 本文是 [kubectl 命令速查](../kubectl-commands#调试与排障) 中 `kubectl auth`（`can-i`）的从 0 到 1 详解。
> 目标：把 `kubectl auth can-i --help` 里的每个选项讲清楚，多看几遍后，你在服务器上敲 `--help` 就知道该用哪个选项。
> 环境依据：kubectl 客户端，对应 **Kubernetes 1.35**（本机沙箱未安装，选项依据 K8s 官方命令参考核实；示例输出均为「示意，据 K8s 官方文档」）。

## 一、命令是干什么的

`kubectl auth can-i` 用来**回答一个问题：我（或模拟的某个用户）现在有没有权限做某个操作？** 报 `forbidden` 权限不足时，用它快速定位是缺哪个 Verb/资源。

- `kubectl auth can-i create pods`：我能不能建 Pod？
- `kubectl auth can-i list deployments.apps`：能不能列 Deployment？
- 配合 `--as`：模拟另一个用户，看他能不能干。

> 类比：`can-i` 像站在门口问保安"我现在这个工牌，能进这扇门吗"。报 403 时，先别猜 Role 写漏了，用 `can-i` 一步步试。

## 二、命令语法

```bash
kubectl auth can-i VERB [类型 | 类型/名 | 非资源URL]
```

- `VERB`：`get`、`list`、`watch`、`create`、`update`、`delete`、`*`（全部）；
- `类型`：资源类型（pod、deployments.apps…）；`*` 表示所有；
- 输出只有 `yes` / `no`，退出码 0=yes、1=no。

```bash
kubectl auth can-i create pods
```

## 三、选项全表（对照 `kubectl auth can-i --help`）

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `VERB 类型` | 判断某动作是否允许 | 核心 |
| `--list` | 列出当前身份**所有**被允许的动作 | 一次性看全量权限 |
| `--no-headers` | `--list` 时不打印表头 | 接脚本 |
| `-A`，`--all-namespaces` | 跨所有命名空间判断 | 集群级权限 |
| `-n 命名空间` | 在指定命名空间判断 | 命名空间级权限 |
| `--subresource=log` | 判断子资源，如读日志 `get pods --subresource=log` | 看日志权限 |
| `-q`，`--quiet` | 不打印 yes/no，只靠退出码 | 脚本里判断 |
| `--as=用户`（全局 impersonation） | 模拟成指定用户判断 | 排别人的权限问题 |
| `--as-group=组`（全局 impersonation） | 模拟成指定组 | 排组权限 |

> `--as` / `--as-group` 是 kubectl 全局伪装（impersonation）标志，不是 can-i 独有；用它们你得本身有 `impersonate` 权限。

## 四、由浅入深的典型示例

### 示例 1：我能不能建 Pod

```bash
kubectl auth can-i create pods
```

输出（示意，据 K8s 官方文档）：

```text
yes
```

> `no` 就说明当前身份没权限建 Pod。

### 示例 2：我能不能列 Deployment

```bash
kubectl auth can-i list deployments.apps
```

输出（示意，据 K8s 官方文档）：

```text
no
```

### 示例 3：判断能不能读 Pod 日志

```bash
kubectl auth can-i get pods --subresource=log
```

> 日志是 pod 的子资源，要用 `--subresource=log`，不是直接 `get pods`。

### 示例 4：在指定命名空间判断

```bash
kubectl auth can-i list jobs.batch/bar -n foo
```

> 判断在 `foo` 这个 ns 里能不能列 jobs。

### 示例 5：列出我所有被允许的动作

```bash
kubectl auth can-i --list --namespace=foo
```

输出（示意，据 K8s 官方文档）：

```text
Resources                                      Non-Resource URLs   Resource Names   Verbs
pods                                           []                  []                [get list watch]
pods/log                                       []                  []                [get]
```

> 一目了然这个身份在 `foo` ns 里能干什么、不能干什么。

### 示例 6：模拟另一个用户排障

```bash
kubectl auth can-i delete pods --as=alice --as-group=developers
```

> 报障说"alice 删不了 Pod"，你用 `--as` 模拟她试，不用切她的凭证。

### 示例 7：判断能不能做任意动作（管理员自查）

```bash
kubectl auth can-i '*' '*'
```

> 返回 `yes` 说明你是 cluster-admin 级别。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `kubectl auth can-i <verb> <资源>` | 问"我能不能干这事"（**排 403 首选**） |
| `kubectl auth can-i --list` | 列我所有权限 |
| `kubectl auth can-i get pods --subresource=log` | 查日志权限 |
| `kubectl auth can-i delete pods --as=用户` | 模拟别人 |
| `kubectl auth can-i '*' '*'` | 是否超管 |

## 六、与 RBAC 的关系

`can-i` 背后是 apiserver 里的 RBAC 评估：

- 你报 `forbidden: cannot create pods`，先 `can-i create pods` 确认；
- 返回 `no`，就去看你的 User/ServiceAccount 绑了哪个 Role/ClusterRole，缺哪个 Verb/Resource；
- 批量维护 RBAC 清单用 `kubectl auth reconcile -f rbac.yaml`（比 `apply` 更语义化地合并规则和主体）。

> 说明：较新版本还有 `kubectl auth check-access`（结构化访问审查）子命令，flags 随版本演进，以 `kubectl auth check-access --help` 本机输出为准，本文不展开编造。

## 七、RHEL 系与 Debian 系差异

auth 查的是 apiserver 的 RBAC，两系**用法一致**。

## 八、新手易错点

1. **403 了别瞎改 Role**：先 `can-i` 精确定位是哪个 Verb/资源缺权限，再去补 Role。
2. **子资源要单独判断**：读日志是 `pods/log`、scale 是 `deployments/scale`，`can-i get pods` yes 不代表能读日志。
3. **`--as` 需要 impersonate 权限**：你自己得有权限才能模拟别人，否则先报你没权限。
4. **`yes`/`no` 退出码**：脚本里用退出码（0=允许，1=拒绝），`-q` 可静默。
5. **命名空间级 vs 集群级**：Role 只在 ns 内生效，ClusterRole 才全局；判断时注意 `-n` 和 `-A`。
6. **ServiceAccount 权限**：Pod 里的进程用的是 Pod 挂的 ServiceAccount，不是你本机的 kubeconfig 用户；排 Pod 内权限要 `--as=system:serviceaccount:ns:sa名`。
7. **can-i 是只读查询**：不修改任何东西，放心试。

## 九、相关命令与文档

- 速查页：[kubectl 命令速查](../kubectl-commands#调试与排障)
- 切集群/用户：[config 详解](./config)
- 概念补课（RBAC/ServiceAccount）：[StatefulSet 与安全](../../guide/container-k8s-04-statefulset-security)
- 官方命令参考：https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands#auth
