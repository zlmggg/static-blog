# kubectl config 命令详解：管理 kubeconfig 和上下文切换

> 本文是 [kubectl 命令速查](../kubectl-commands#配置与上下文) 中 `kubectl config` 的从 0 到 1 详解。
> 目标：把 `kubectl config` 常用子命令讲清楚，多看几遍后，你在服务器上敲 `--help` 就知道该用哪个选项。
> 环境依据：kubectl 客户端，对应 **Kubernetes 1.35**（本机沙箱未安装，选项依据 K8s 官方命令参考核实；示例输出均为「示意，据 K8s 官方文档」）。

## 一、命令是干什么的

`kubectl config` 用来管理 **kubeconfig 文件**（默认 `~/.kube/config`）——里面存着"有哪些集群、用哪个用户、当前连哪个上下文（context）"。你在多集群之间切换、改默认命名空间，全靠它。

- `current-context`：现在连的是哪个集群？
- `use-context`：切到另一个集群；
- `set-context --current --namespace=xxx`：改默认命名空间。

> 类比：kubeconfig 像手机里的"WiFi 列表"——存了多个 WiFi（集群）的名字、密码（用户凭证），`use-context` 就是点一下连另一个 WiFi。

## 二、命令语法

```bash
kubectl config <子命令> [参数]
```

- kubeconfig 加载顺序：`--kubeconfig` 指定的文件 > `$KUBECONFIG` 环境变量（可合并多个）> `~/.kube/config`；
- 子命令都是改这个配置文件，不碰集群。

```bash
kubectl config get-contexts
```

## 三、选项全表（对照 `kubectl config --help`）

### 1. 查看

| 子命令 | 中文含义 | 什么场景用 |
|---|---|---|
| `current-context` | 打印当前上下文名 | 确认现在连哪个集群（最常用） |
| `get-contexts` | 列出所有上下文 | 看有哪些集群可切 |
| `get-contexts -o name` | 只列名字 | 接脚本 |
| `get-clusters` | 列出配置里的集群 | |
| `get-users` | 列出配置里的用户 | |
| `view` | 打印合并后的 kubeconfig | 看当前生效配置 |
| `view --minify` | 只显示当前上下文用到的部分 | 去掉无关的集群/用户段 |
| `view --raw` | 显示原始证书和敏感字段 | 看真实 token/证书 |

### 2. 切换与修改

| 子命令 | 中文含义 | 什么场景用 |
|---|---|---|
| `use-context 名` | 切换当前上下文 | 切集群（最常用） |
| `set-context 名 --cluster= --user= --namespace=` | 建/改一个上下文 | 把集群+用户+ns 绑一起 |
| `set-context --current --namespace=ns` | 改当前上下文默认 ns | 免了每次 `-n` |
| `set-cluster 名 --server= --certificate-authority=` | 加/改集群段 | 接入新集群 |
| `set-credentials 名 --client-certificate= --token=` | 加/改用户凭证 | 配认证 |
| `rename-context 旧 新` | 重命名上下文 | 名字太难记 |
| `delete-cluster/context/user 名` | 删掉对应段 | 清理 |
| `unset 路径` | 清掉某个字段 | 如 `unset current-context` |

### 3. 全局选项

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `--kubeconfig=文件` | 只操作指定文件，不合并 | 临时操作用别的 config |

## 四、由浅入深的典型示例

### 示例 1：看当前连的是哪个集群

```bash
kubectl config current-context
```

输出（示意，据 K8s 官方文档）：

```text
my-prod-cluster
```

### 示例 2：列出所有上下文

```bash
kubectl config get-contexts
```

输出（示意，据 K8s 官方文档）：

```text
CURRENT   NAME             CLUSTER          AUTHINFO             NAMESPACE
*         my-prod-cluster  prod-cluster     prod-admin
          my-dev-cluster   dev-cluster      dev-admin            dev
```

- `CURRENT` 列的 `*` 是当前在用；
- 一行 = 一个上下文（集群+用户+命名空间的组合）。

### 示例 3：切换到另一个集群

```bash
kubectl config use-context my-dev-cluster
```

输出（示意，据 K8s 官方文档）：

```text
Switched to context "my-dev-cluster".
```

> 之后所有 kubectl 命令都打到 dev 集群了——**切之前想清楚，别在 prod 上误操作**。

### 示例 4：改当前上下文的默认命名空间

```bash
kubectl config set-context --current --namespace=dev
```

> 以后这个上下文下不用每次敲 `-n dev`。切回 default 就再设一次。

### 示例 5：看当前生效的完整配置

```bash
kubectl config view
```

输出（示意，据 K8s 官方文档）：

```yaml
apiVersion: v1
clusters:
- cluster:
    server: https://1.2.3.4:6443
  name: my-prod-cluster
contexts:
- context:
    cluster: my-prod-cluster
    user: prod-admin
  name: my-prod-cluster
current-context: my-prod-cluster
kind: Config
```

> 注意：默认 `view` 会把证书数据做脱敏处理；要看原始敏感字段加 `--raw`。

### 示例 6：只看当前上下文相关的配置

```bash
kubectl config view --minify
```

> `--minify` 把当前没用的集群段、用户段都去掉，输出只剩当前上下文用到的部分，便于分享一份"自包含"的配置。

### 示例 7：接入新集群（建 cluster + user + context）

```bash
kubectl config set-cluster my-cluster --server=https://1.2.3.4 --certificate-authority=ca.crt --embed-certs
kubectl config set-credentials kubeuser --client-certificate=admin.crt --client-key=admin.key --embed-certs
kubectl config set-context my-cluster --cluster=my-cluster --user=kubeuser --namespace=default
kubectl config use-context my-cluster
```

> 三步把一个新集群接进 kubeconfig。

### 示例 8：同时用多个 kubeconfig

```bash
KUBECONFIG=~/.kube/config:~/.kube/kubconfig2 kubectl config view
```

> 用冒号分隔多个文件，view 会合并显示；修改时改在定义它的那个文件里。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `kubectl config current-context` | 看当前集群 |
| `kubectl config get-contexts` | 列所有上下文 |
| `kubectl config use-context 名` | 切集群（**最常用**） |
| `kubectl config set-context --current --namespace=ns` | 改默认 ns |
| `kubectl config view` | 看配置 |
| `kubectl config view --minify` | 只看当前上下文 |
| `kubectl config set-cluster/set-credentials/set-context` | 接入新集群 |

## 六、RHEL 系与 Debian 系差异

config 改的是 `~/.kube/config` 文本文件，两系**用法完全一致**，只是默认路径都在 `$HOME/.kube/` 下。

## 七、新手易错点

1. **在错误的集群上操作**：敲大命令前先 `current-context` 确认连的是 dev 还是 prod。
2. **切了上下文忘了切回来**：在 prod 调试完记得 `use-context` 切回 dev，免得下次误删 prod。
3. **`view` 默认脱敏**：想看真实 token/证书要 `--raw`，别以为配置里没存。
4. **`--raw` 输出含敏感信息**：别随手贴到聊天/工单里。
5. **`set-context --current --namespace` 只改当前上下文**：切到别的上下文后默认 ns 是另一个，别搞混。
6. **多 kubeconfig 合并规则**：`$KUBECONFIG` 用冒号分隔；新建字段写进列表第一个存在的文件。
7. **改坏了直接编辑文件**：`kubectl config` 子命令本质就是改 YAML，熟了也可以直接手编 `~/.kube/config`。

## 八、相关命令与文档

- 速查页：[kubectl 命令速查](../kubectl-commands#配置与上下文)
- 看版本/集群信息：[cluster-info 与 version 详解](./cluster)
- 概念补课（kubeconfig/认证）：[K8s 架构与集群](../../guide/container-k8s-01-architecture-cluster)
- 官方命令参考：https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands#config
