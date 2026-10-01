# kubectl 进阶排障命令详解：events / debug / explain / wait / diff

> 本文是 [云原生排障命令速查](../cloudnative-commands) 中「kubectl 进阶排障」一组命令的从 0 到 1 详解，本篇一次讲清 `kubectl get events`、`kubectl debug`（临时容器 / node 调试）、`kubectl explain`、`kubectl wait`、`kubectl diff`。
> 目标：基础的 `get/describe/logs/exec` 之外，这几条是「Pod 起不来、状态不对、想知道字段怎么填、想等它就绪」时的进阶武器。
> 环境依据：Kubernetes 1.35（站内 2026-09 基准；临时容器 Ephemeral Containers 自 1.25 起 GA）。本沙箱未装 kubectl，选项据 kubernetes.io 官方命令参考核对（官方参考页当前已滚动到 v1.37，下列 flags 在 1.35 同样适用），示例标注「据官方文档」。

## 一、命令是干什么的

基础 kubectl（`get`/`describe`/`logs`/`exec`）能看一个资源的现状，但排障经常还需要：

- **这个集群/这个 Pod 最近到底发生了什么？** → `kubectl get events`（事件流）
- **Pod 里是个精简镜像、连 `sh` 都没有，怎么进去看？** → `kubectl debug` 注入**临时调试容器**（不改原 Pod、不重启）
- **某个 YAML 字段到底怎么填、支持哪些子字段？** → `kubectl explain`（离线查 API 字段文档）
- **脚本里怎么等一个 Pod Ready、或等它被删掉？** → `kubectl wait`
- **apply 之前先知道会改坏什么？** → `kubectl diff`

> 类比：`events` 像系统的「最近事件日志」；`debug` 像给一个没装工具的机器「远程塞一个带全套工具的随身 U 盘系统」而不重装它；`explain` 像内置的「字段说明书」；`wait` 像「等绿灯再走」；`diff` 像 `git diff`，先看改动再提交。

## 二、命令语法

```bash
kubectl get events [(-A | --field-selector=... | --sort-by=...)] [flags]
kubectl debug (POD | TYPE/NAME | node/NAME) -it --image=IMG [--target=容器] [flags]
kubectl explain TYPE.FIELD [--recursive] [--api-version=...]
kubectl wait --for=condition=READY|delete|create RESOURCE [--timeout=...]
kubectl diff -f FILE
```

- `POD/TYPE/NAME`：要调试的对象；`node/节点名` 表示调试节点；
- `-it`：`--stdin` + `--tty`，交互式 attach 进调试会话；
- `--for`：wait 要等的条件。

## 三、选项全表（对照官方命令参考）

### 1. `kubectl get events`：看事件

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-A`，`--all-namespaces` | 跨**所有命名空间**看事件 | 全局看集群出了啥（最常用） |
| `--field-selector=K=V` | 按字段过滤，如 `type=Warning`、`reason=FailedScheduling` | 只看 Warning / 只看某个原因 |
| `--sort-by=.metadata.creationTimestamp` | 按创建时间**正序**排 | 按时间线还原事故经过 |
| `-o wide` / `-o json` | 多列信息 / 机器可读 | 脚本处理 |
| `--since=5m` | 只看最近 5 分钟事件 | 事件太多时收窄范围 |

> 事件默认按「最近在前」排，很乱；排障时几乎都加 `--sort-by=.metadata.creationTimestamp` 正序看，或 `--field-selector type=Warning` 只看警告。

### 2. `kubectl debug`：临时调试容器

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-it` | 分配终端并 attach 进调试会话 | 交互式排障（几乎必加） |
| `--image=IMG` | 调试用镜像（如 `busybox`/`nicolaka/netshoot`/`ubuntu`） | 原容器没工具时塞个带工具的镜像 |
| `--target=容器名` | 临时容器**共享目标容器的进程/PID 命名空间** | 进去 `ps`/`ls /proc/<pid>/root` 看目标容器内部 |
| `--copy-to=新名` | 复制一个 Pod 来调试（改镜像/改命令），不动原 Pod | 原 Pod 不能动、要改命令复现时 |
| `--set-image=容器=镜像` | 配合 `--copy-to`，改某容器镜像 | 临时把镜像换成带调试符号的版本 |
| `-c NAME`，`--container=NAME` | 指定调试容器名 | 自定义名字时 |
| `--profile=PROFILE` | 调试 profile：`general`(默认)/`baseline`/`restricted`/`netadmin`/`sysadmin` | `netadmin` 给网络工具、`sysadmin` 给宿主级权限 |
| `--attach` | 启动后自动 attach | 默认在 `-i` 时为 true |
| node/NAME 形式 | 在**节点**上起调试 Pod，节点宿主文件系统挂到 `/host` | 节点本身坏了（kubelet、磁盘、网络）时 |

> `kubectl debug node/mynode -it --image=ubuntu` 起的 Pod 里，宿主机根目录挂在 `/host`，进去后 `chroot /host` 或直接 `ls /host/var/log` 就能翻节点日志。

### 3. `kubectl explain`：查字段文档

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `--recursive`，`-R` | **递归**打印该资源所有字段（含嵌套） | 写 Deployment 前看全字段树 |
| `--max-depth=N` | 配合 `--recursive`，只展开 N 层 | 字段太多想限制深度 |
| `--api-version=GROUP/VERSION` | 指定 API 版本 | 资源在多版本间字段有差异时 |
| `-o plaintext-openapiv2` | 用 OpenAPI v2 格式输出 | 老版本/特殊场景 |

> 用法：`kubectl explain pods.spec.containers` 直接问「这个字段是啥、有哪些子字段」，不用上网查。

### 4. `kubectl wait`：等条件

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `--for=condition=Ready` | 等资源状态变成 `Ready`（可 `=false`） | 部署完等 Pod 就绪再跑下一步 |
| `--for=delete` | 等资源**被删除** | 配合 `kubectl delete` 等彻底删干净 |
| `--for=create` | 等资源**被创建** | 别人正在异步创建时 |
| `--for=jsonpath='{.status.x}'=V` | 等某字段等于某值 | 等 LoadBalancer 分到 ingress IP |
| `--timeout=DURATION` | 超时（默认 `30s`；负数=等一周） | 流水线里别无限等 |
| `-l`，`--selector` | 按标签选一批资源一起等 | 等一组 Pod 全 Ready |
| `-f FILE` | 等文件里定义的资源 | 跟 manifest 配套 |

### 5. `kubectl diff`：预览改动

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-f FILE`，`-k DIR` | 对指定 manifest/Kustomize 目录做 dry-run diff | `apply` 前先看会改什么 |
| `--server-side` | 用服务端 apply 语义算 diff | 与 server-side apply 一致时 |

> `kubectl diff` 不修改集群，只输出「如果 apply 会产生的差异」，是安全的上线预检。

## 四、由浅入深的典型示例

以下示例输出为「据官方文档」或示意。

### 示例 1：按时间正序看全集群事件

```bash
kubectl get events -A --sort-by=.metadata.creationTimestamp
```

```text
NAMESPACE   LAST SEEN   TYPE      REASON              OBJECT          MESSAGE
default     10:02:11    Warning   FailedScheduling    pod/api-xxx    0/3 nodes are available: 3 Insufficient cpu.
default     10:02:30    Normal    Pulled              pod/api-xxx    Container image "..." already present on this node
default     10:02:31    Normal    Created             pod/api-xxx    Created container api
```

> 正序读下来，就是一条完整的时间线：为什么没调度、镜像拉没拉到、容器起没起。

### 示例 2：只看 Warning 事件

```bash
kubectl get events -A --field-selector type=Warning
```

> 排障时先把 Normal 噪音滤掉，只看警告，定位快很多。

### 示例 3：给没有 shell 的容器注入临时调试容器

```bash
kubectl debug api-pod-xxx -it --image=busybox --target=api
```

据官方文档说明：这会在**不重启、不替换原 Pod** 的前提下，往运行中的 Pod 里加一个临时容器，并通过 `--target=api` 共享 `api` 容器的进程命名空间；进去后可以 `ps`、`ls /proc/1/root` 看那个精简容器里到底有什么文件。

> 前提：集群开启 EphemeralContainers（1.25+ 默认 GA）。

### 示例 4：在节点上调试，挂宿主根目录

```bash
kubectl debug node/node-01 -it --image=ubuntu
```

```text
Creating debugging pod node-debugger-node-01-xxxx with container debugger on node node-01.
If you don't see a command prompt, try pressing enter.
root@node-01:/# ls /host
bin  boot  dev  etc  home  proc  sys  var  ...
```

> 节点宿主文件系统挂在 `/host`。查节点日志：`chroot /host` 后当成本机操作；或 `cat /host/var/log/pods/...`。

### 示例 5：查 Deployment 字段怎么写

```bash
kubectl explain deployment.spec --recursive --max-depth=2
```

> 忘了 `resources.limits` 怎么写？`kubectl explain deployment.spec.template.spec.containers.resources` 直接查。

### 示例 6：等 Pod Ready，再跑下一步

```bash
kubectl wait --for=condition=Ready pod/api-xxx --timeout=60s
```

```text
pod/api-xxx condition met
```

> 写流水线/脚本时，`wait` 替代手工 `sleep`，就绪即继续。

### 示例 7：等资源被删干净

```bash
kubectl delete pod api-xxx
kubectl wait --for=delete pod/api-xxx --timeout=60s
```

> 滚动发布/清理脚本里，确保 Pod 真没了再往下走。

### 示例 8：apply 前先 diff

```bash
kubectl diff -f deploy.yaml
```

> 输出类似 `kubectl apply --server-dry-run` 的差异，绿色/红色标出新增与删除，确认无误再 `kubectl apply -f deploy.yaml`。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `kubectl get events -A --sort-by=.metadata.creationTimestamp` | 按时间线还原事故 |
| `kubectl get events -A --field-selector type=Warning` | 只看警告 |
| `kubectl debug POD -it --image=busybox --target=容器` | 注入临时调试容器 |
| `kubectl debug node/节点 -it --image=ubuntu` | 进节点看 `/host` |
| `kubectl explain pods.spec.containers --recursive` | 查字段写法 |
| `kubectl wait --for=condition=Ready pod/x --timeout=60s` | 等就绪 |
| `kubectl wait --for=delete pod/x` | 等删干净 |
| `kubectl diff -f app.yaml` | apply 前预览改动 |

## 六、RHEL 系与 Debian 系差异

`kubectl` 是客户端 Go 二进制，**RHEL/Rocky 与 Ubuntu/Debian 用法一致**，只取决于客户端版本与集群 API 版本，不取决于操作系统。注意：

- `kubectl debug` 注入临时容器依赖集群侧 EphemeralContainers 能力（1.25+ GA）；老集群若未开启会报错，此时改用 `--copy-to` 复制 Pod 的方式；
- `--target` 共享进程命名空间要求容器 `shareProcessNamespace` 语义成立，若目标 Pod 设了非 root 且严格 profile，部分调试 profile 可能受限（官方文档有提示）；
- `kubectl wait --timeout` 默认 30s，脚本里记得按业务调大。

## 七、新手易错点

1. **临时容器不持久**：Pod 重建即消失，别把它当常驻调试入口，排完即走；它也不会出现在 `kubectl get pods` 的正常重启计数里。
2. **`--target` 不是随便填**：要填目标容器的名字，不是 Pod 名；填错就只是另起了个独立容器，看不到目标进程。
3. **`debug node/` 的文件系统在 `/host`**：不是直接在节点根目录操作，记得路径都带 `/host` 前缀。
4. **events 会被定期清理**：kube-controller-manager 默认约 1 小时后删旧事件，事故后要尽快抓 `--sort-by` 时间线。
5. **`wait` 会卡住直到超时**：条件永远不满足时它干等到 `--timeout`，脚本里务必带超时。
6. **危险/开销提示**：`debug --profile=sysadmin`、`--copy-to` 改镜像起的 Pod 拥有较高权限；节点调试 Pod 能看到宿主全部文件，用完即删。`drain` 节点前确认 PDB 与副本冗余，别把服务一次性驱逐光。

## 八、相关命令与文档

- 速查页：[云原生排障命令速查](../cloudnative-commands)
- 基础 get/describe/logs/exec：[kubectl 命令速查](../kubectl-commands)
- Helm release 排障：[helm-troubleshoot](./helm-troubleshoot)
- 用 jsonpath 取字段：[jsonpath 与 jq](./jsonpath-jq)
- 节点容器层排障：[crictl](./crictl) 、[ctr](./ctr)
- eBPF/内核观测：[Linux eBPF 指南](../../guide/linux-ebpf)
- 官方文档：https://kubernetes.io/docs/reference/kubectl/generated/kubectl_debug/ 、https://kubernetes.io/docs/reference/kubectl/generated/kubectl_wait/ 、https://kubernetes.io/docs/reference/kubectl/generated/kubectl_explain/ ；临时容器：https://kubernetes.io/docs/tasks/debug/debug-application/debug-running-pod/
