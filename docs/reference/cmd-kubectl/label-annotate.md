# label 与 annotate 命令详解：给资源打标签和备注

> 本文是 [kubectl 命令速查](../kubectl-commands#编辑伸缩与删除) 中 `kubectl label` 与 `kubectl annotate` 的从 0 到 1 详解。
> 目标：把这两个"给资源挂元数据"的命令讲清楚，多看几遍后，你在服务器上敲 `--help` 就知道该用哪个选项。
> 环境依据：kubectl 客户端，对应 **Kubernetes 1.35**（本机沙箱未安装，选项依据 K8s 官方命令参考核实；示例输出均为「示意，据 K8s 官方文档」）。

## 一、命令是干什么的

K8s 里每个对象都能挂两类元数据：

- **Label（标签）**：一对小的 `key=value`，**可被筛选、作路由依据**。Service 靠 label 选 Pod、Deployment 靠 label 管 Pod、`-l` 过滤靠的就是它。
- **Annotation（注解）**：也是 `key=value`，但**不用于筛选**，专门给工具/人存附加信息（描述、构建号、谁改的）。

> 类比：label 像商品上的"分类吊牌"（收银机按吊牌归类、筛选）；annotation 像商品里塞的"说明书/保修卡"（人看，机器不按它分拣）。

## 二、命令语法

```bash
kubectl label [--overwrite] (-f 文件 | 类型 名称) key1=val1 ... keyN=valN
kubectl annotate [--overwrite] (-f 文件 | 类型 名称) key1=val1 ... keyN=valN
```

- 加标签：`key=value`；
- 删标签：`key-`（末尾加个 `-`，不用 `--overwrite`）；
- 改已有值：必须加 `--overwrite`，否则报错。

```bash
kubectl label pod foo unhealthy=true
```

## 三、选项全表（对照 `--help`）

### 1. label

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `类型 名称 key=val` | 加标签 | 最常用 |
| `key-` | 删除该标签（末尾 `-`） | 摘掉标签 |
| `--overwrite` | 允许覆盖已有标签值 | 改已有标签值时（必须加） |
| `-l 标签`，`--selector` | 给匹配标签的资源批量打 | 批量 |
| `--all` | 给该类型所有资源打 | 慎用 |
| `--list` | 列出资源现有标签 | 先看看有哪些标签 |
| `-f 文件` | 对文件里的资源操作 | |
| `--resource-version=版本` | 仅当版本匹配才改 | 乐观锁 |
| `--field-selector=字段=值` | 按字段过滤 | |

### 2. annotate

与 label 几乎同构，差别：

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `key=val` | 加注解 | 存描述/构建信息 |
| `key-` | 删除注解 | 摘掉注解 |
| `--overwrite` | 允许覆盖已有注解 | 改注解时必须加 |
| `--list` | 列出现有注解 | |
| `-l` / `--all` / `-f` / `--resource-version` | 同 label | |

> label key/value 命名规则：以字母数字开头，可含 `-`、`_`、`.`，最多 63 字符；key 可带 `前缀/`（如 `example.com/my-app`）。

## 四、由浅入深的典型示例

### 示例 1：给 Pod 加标签

```bash
kubectl label pods foo unhealthy=true
```

输出（示意，据 K8s 官方文档）：

```text
pod/foo labeled
```

### 示例 2：覆盖已有标签值（必须 --overwrite）

```bash
kubectl label --overwrite pods foo status=unhealthy
```

> 不加 `--overwrite` 会报错 `... already has a value`。

### 示例 3：删除标签

```bash
kubectl label pods foo bar-
```

> `bar-`（末尾减号）= 删掉 `bar` 这个标签，不需要 `--overwrite`。

### 示例 4：批量给所有 Pod 打标签

```bash
kubectl label pods --all status=unhealthy
```

> 给当前 ns 所有 Pod 都打上；慎用。

### 示例 5：按文件打标签

```bash
kubectl label -f pod.json status=unhealthy
```

### 示例 6：给资源加注解（备注）

```bash
kubectl annotate pods foo description='my frontend running nginx'
```

> 注解里可以放较长的描述、构建号、负责人等。

### 示例 7：覆盖注解

```bash
kubectl annotate --overwrite pods foo description='my frontend running nginx'
```

### 示例 8：删除注解

```bash
kubectl annotate pods foo description-
```

> 和删标签一样，末尾加 `-`。

### 示例 9：列出现有标签

```bash
kubectl label pods foo --list
```

> 先看这个 Pod 现在有哪些标签，再决定加/改/删。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `kubectl label pod 名 key=val` | 加标签 |
| `kubectl label --overwrite pod 名 key=新值` | 改标签值 |
| `kubectl label pod 名 key-` | 删标签 |
| `kubectl annotate pod 名 key=val` | 加注解 |
| `kubectl annotate pod 名 key-` | 删注解 |
| `kubectl get pods --show-labels` | 看所有标签（见 [get](./get)） |

## 六、label 与 annotate 的区别

| 维度 | Label | Annotation |
|---|---|---|
| 用途 | 筛选、选路、组内关系 | 存附加元数据，不筛选 |
| 能否 `-l` 选中 | 能 | 不能 |
| 典型内容 | `app=nginx`、`env=prod` | `description=...`、`build=123` |
| 大小 | 小、短 | 可较大（任意字符串） |

## 七、RHEL 系与 Debian 系差异

label/annotate 改的是集群对象，两系**用法一致**。

## 八、新手易错点

1. **改已有值忘了 `--overwrite`**：直接报错；改值一定加。
2. **删标签是 `key-` 不是 `key=`**：末尾减号才是删，写 `key-`。
3. **把该放 annotation 的塞进 label**：长描述、JSON 别往 label 放，label 要短、要可筛选。
4. **改了 Deployment 的 selector 会出大事**：Deployment 的 `.spec.selector` 一旦设定基本不可改；`kubectl set selector` 只对 Service 用，别去动 Deployment selector。
5. **label 命名别用大写/特殊字符**：只允许字母数字 `-` `_` `.` 和可选前缀 `/`。
6. **打错标签影响 Service 选 Pod**：Service 靠 label 选后端，把 Pod 的 `app` 标签改了，流量立刻切走。
7. **`--all` 谨慎**：批量打标签影响面大，先 `-l` 小范围试。

## 九、相关命令与文档

- 速查页：[kubectl 命令速查](../kubectl-commands#编辑伸缩与删除)
- 按标签筛选：[get 详解](./get)
- 节点污点/标签：`kubectl taint`/`kubectl label node`（见官方参考）
- 概念补课（标签与选择器）：[Pod 与服务发现](../../guide/container-k8s-02-pod-service-discovery)
- 官方命令参考：https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands#label
