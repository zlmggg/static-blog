# kubectl jsonpath 与 jq 详解：从 JSON 里精准抠字段

> 本文是 [云原生排障命令速查](../cloudnative-commands) 中「取资源字段做脚本」的从 0 到 1 详解，本篇一次讲清 `kubectl -o jsonpath='{...}'`（含 `range`、转义）与 `jq`（`-r`、`.[]`、`select`、`map`），并把两者对照着讲。
> 目标：面对一大坨 `kubectl get -o json`，你知道怎么用 jsonpath 或 jq 一行命令把想要的字段抠出来、喂给脚本。
> 环境依据：`jq` 1.6（本机已装，下文 jq 示例均为本机实跑真实输出）；`kubectl -o jsonpath` 基于 Kubernetes 1.35 文档（本沙箱未装 kubectl，jsonpath 示例据官方文档，标注「据官方文档」）。

## 一、命令是干什么的

`kubectl get xxx -o json` 会把整个资源对象吐成一大坨 JSON。人眼看很累，脚本更没法直接用。于是有两种「从 JSON 里精准挑字段」的工具：

- **jsonpath**：kubeconfig 内置的输出模板，`kubectl get pods -o jsonpath='{...}'`，**不需要额外装 jq**，适合「就想要 Pod 名列表」这种轻量场景；
- **jq**：独立的命令行 JSON 处理器，功能强得多（过滤、映射、管道），是 Linux 上处理 JSON 的事实标准。

两者都用「点号路径」取字段（`.items[0].metadata.name`），但 jq 支持 `select`、`map`、`[]` 迭代、算术、条件，远比 jsonpath 灵活；jsonpath 胜在跟 kubectl 无缝、不依赖外部工具。

> 类比：jsonpath 像「在 kubectl 输出里写个 XPath 定位」；jq 像「把 JSON 当数据流，用管道一步步加工」，是 JSON 界的 `sed/awk`。

## 二、命令语法

```bash
kubectl get RESOURCE -o jsonpath='{ .路径 }'
echo 'JSON' | jq '筛选/加工表达式'
```

- jsonpath 路径写在单引号里、外层套花括号 `{...}`；
- jq 表达式写在单引号里，输入 JSON 从 stdin 或文件给。

最简单的两个：

```bash
kubectl get pods -o jsonpath='{.items[0].metadata.name}'
echo '{"a":1}' | jq .
```

## 三、选项全表（对照真实 `jq --help` 与 kubectl 输出格式）

### 1. `kubectl -o jsonpath` 常用写法（不是独立命令，是输出格式）

| 写法 | 含义 | 什么场景用 |
|---|---|---|
| `-o jsonpath='{.metadata.name}'` | 取单个标量字段 | 取 Pod 名、命名空间 |
| `-o jsonpath='{.items[*].metadata.name}'` | 取列表里所有元素的某字段 | 列出所有 Pod 名 |
| `-o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.phase}{"\n"}{end}'` | **循环**：每个元素打一行「名 + 状态」 | 做表格化输出（最常用的 range） |
| `{"\n"}` / `{"\t"}` | 输出换行/制表符（必须用双引号包） | 排版 |
| `--template`/jsonpath 文件 | 长模板写到文件用 `--jsonpath-file` | 模板太长塞不进命令行时 |

> 注意：jsonpath 里的转义（换行/制表）必须写成 `{"\n"}`、`{"\t"}` 这种**带双引号**的形式，直接写 `\n` 不生效。

### 2. `jq` 全局选项（本机 `jq --help` 实跑）

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `.` | 原样输出（格式化漂亮打印） | 先看一眼 JSON 长啥样 |
| `-r`，`--raw-output` | 输出**原始字符串**，不带引号 | 取名字/值给 shell 用（极常用） |
| `.[]` | 把数组**拆开**逐个输出 | 遍历数组元素 |
| `.字段` / `.a.b.c` | 取对象字段 | 取嵌套字段 |
| `select(条件)` | **过滤**：保留满足条件的元素 | 只要 env=prod 的 |
| `map(表达式)` | 对数组每个元素做变换 | 给每个端口 ×2 |
| `-s`，`--slurp` | 把多行输入读成一个数组 | 处理 NDJSON |
| `-n`，`--null-input` | 不从输入读，用 `{}` 造 JSON | 生成测试数据 |
| `-c` | 紧凑输出（一行一个） | 给程序消费 |
| `--arg 名 值` | 把 shell 变量传进 jq | 避免在表达式里硬编码 |

## 四、由浅入深的典型示例

### 示例 1：jq 原样格式化（本机实跑）

```bash
echo '{"name":"api","version":1,"enabled":true}' | jq .
```

```text
{
  "name": "api",
  "version": 1,
  "enabled": true
}
```

> 最常用的入门用法：一坨挤在一行的 JSON，`jq .` 立刻排版好看。

### 示例 2：取字段 vs 取「裸值」（本机实跑）

```bash
jq .name demo.json
jq -r .name demo.json
```

```text
"api"        # jq .name：带引号（它是 JSON 字符串）
api          # jq -r .name：去掉引号，纯文本
```

> 关键区别：`jq .name` 输出的是合法 JSON（带引号）；`jq -r .name` 才是给 shell 当变量用的裸值。

### 示例 3：拆数组 `.[]`（本机实跑）

```bash
echo '[10,20,30]' | jq '.[]'
```

```text
10
20
30
```

> `.[]` 把数组拍平成一行一个元素；对应「map 整个数组」就用 `[.[] | ...]` 包起来。

### 示例 4：遍历嵌套数组并变换（本机实跑）

```bash
jq '[.ports[] | . * 2]' demo.json
```

```text
[
  160,
  886
]
```

> `.ports[]` 逐个取出 80/443，`| . * 2` 翻倍，最外层 `[ ]` 再收集成新数组。

### 示例 5：select 过滤 + to_entries（本机实跑）

```bash
jq '.labels | to_entries' demo.json
jq '.tags[] | select(startswith("e"))' demo.json
```

```text
[
  { "key": "env", "value": "prod" },
  { "key": "team", "value": "sre" }
]
"edge"
```

> `select(...)` 是 jq 的「where」：`startswith("e")` 只留下以 e 开头的 tag。

### 示例 6：kubectl jsonpath 列所有 Pod 名（据官方文档）

```bash
kubectl get pods -o jsonpath='{.items[*].metadata.name}'
```

```text
api-7d9f-x2yz  worker-5c8d-abcd  db-0
```

### 示例 7：jsonpath range 做表格（据官方文档）

```bash
kubectl get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.phase}{"\n"}{end}'
```

```text
api-7d9f-x2yz   Running
worker-5c8d-abcd  Pending
db-0            Running
```

> 对照 jq 版本：`kubectl get pods -o json | jq -r '.items[] | "\(.metadata.name)\t\(.status.phase)"'`——做同样的事，jq 表达力更强。

### 示例 8：jsonpath 与 jq 对照（取所有 Running Pod 名）

| 需求 | jsonpath | jq（先 `-o json` 管道） |
|---|---|---|
| 取所有 Pod 名 | `-o jsonpath='{.items[*].metadata.name}'` | `-o json \| jq -r '.items[].metadata.name'` |
| 只取 Running | jsonpath 不擅长过滤 | `-o json \| jq -r '.items[] \| select(.status.phase=="Running") \| .metadata.name'` |

> 结论：**轻量取值用 jsonpath，带过滤/加工用 jq**。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `kubectl get pods -o jsonpath='{.items[*].metadata.name}'` | 列所有 Pod 名 |
| `kubectl get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.phase}{"\n"}{end}'` | 名+状态表格 |
| `echo J \| jq .` | 格式化看 JSON |
| `... \| jq -r '.items[].metadata.name'` | 裸值列出 |
| `... \| jq '.items[] | select(.status.phase=="Running")'` | 过滤 |
| `... \| jq '[.items[].metadata.name]'` | 收集成数组 |

## 六、RHEL 系与 Debian 系差异

- **jq**：两系用法一致，只是包名不同——Debian/Ubuntu `apt install jq`，RHEL/Rocky `dnf install jq`；版本可能略旧（如本机 1.6），核心过滤器 `.`/`.[]`/`select`/`map`/`-r` 各版本都支持。
- **kubectl jsonpath**：不依赖操作系统，随 kubectl 二进制走，两系完全一致。
- 小区别：jsonpath 是 kubectl 内置、零依赖；jq 需要单独装，但几乎所有 SRE 镜像/调试容器里都预装。

## 七、新手易错点

1. **`jq .name` 带引号、`jq -r .name` 才是裸值**：要传给 shell 变量/文件名时忘了 `-r`，会把引号也带进去。
2. **jsonpath 的换行要写 `{"\n"}`**：直接在模板里敲真换行或写 `\n` 不生效，必须是带双引号的 `{"\n"}`。
3. **花括号转义**：jsonpath 整段用单引号包起来；里面需要 shell 变量时用 `$'...'` 或 `--template`，别和 `{}` 混。
4. **`.items[*]` vs `.items[]`**：`[*]` 结果拼成空格分隔字符串；`[]` 在 jq 里是逐个流出。别用混。
5. **select 里字符串比较用 `==`**：`select(.status.phase=="Running")`，别忘了等号两边的引号。
6. **jsonpath 不擅长复杂过滤**：一旦要 `select`/算术/嵌套条件，果断换成 `kubectl -o json | jq ...`。

## 八、相关命令与文档

- 速查页：[云原生排障命令速查](../cloudnative-commands)
- kubectl 进阶：[kubectl-advanced](./kubectl-advanced)
- 基础 kubectl：[kubectl 命令速查](../kubectl-commands)
- 从 JSON 日志里抠字段：见 [logcli](./logcli) 的 `| json` 解析
- 官方文档：jq https://jqlang.github.io/jq/manual/ ；kubectl jsonpath https://kubernetes.io/docs/reference/kubectl/jsonpath/
