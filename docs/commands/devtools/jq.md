---
title: "jq · JSON 解析利器"
description: "jq 提取字段、过滤数组、格式化、转换 JSON。curl 接口返回、kubectl -o json、配置文件解析必备，参数与过滤器中文分级。"
---

# jq · JSON 解析利器

> 命令手册 · [开发与效率](/commands/devtools/) ｜ 频率：每天用
> 命令行处理 JSON 的标准工具。curl 接口、kubectl -o json、各种配置返回都是 JSON，jq 提取字段比 grep 靠谱得多。

## 一句话用途

从 JSON 里精确取字段、过滤、格式化、转换——运维解析接口返回的利器。

## 高频场景速查

```bash
echo '{"name":"web","ip":"10.0.0.11"}' | jq '.name'        # 取字段
curl -s api/servers | jq '.[].ip'                          # 数组每项的 ip
curl -s api/servers | jq '.[] | select(.status=="up")'     # 过滤
kubectl get pods -o json | jq '.items[].metadata.name'     # K8s pod 名
cat config.json | jq '.'                                   # 格式化美化
jq -r '.name' file.json                                    # -r 去引号（脚本取值）
```

## 参数与过滤器（按频率分级）

### 每天用

| 写法 | 含义 |
|---|---|
| `.field` | 取字段 |
| `.[]` | 展开数组/对象 |
| `.a.b` | 嵌套取值 |
| `select(条件)` | 过滤 |
| `-r` | 原始输出（去引号，脚本用） |
| `-e` | 按结果设退出码 |

### 偶尔用

| 写法 | 含义 |
|---|---|
| `map(.x)` | 对每项取字段 |
| `length` | 数组长度 |
| `keys` | 对象的键 |
| `sort_by(.x)` | 排序 |
| `group_by(.x)` | 分组 |
| `{a:.x,b:.y}` | 构造新对象 |
| `--arg name val` | 传变量 |

### 很少用

| 写法 | 含义 |
|---|---|
| `to_entries` | 对象转键值数组 |
| `@csv` / `@tsv` | 转 CSV/TSV |
| `reduce` | 累积计算 |

::: tip 易错点
脚本里取值一定加 `-r`，否则带双引号会导致后续比较出错。字段不存在返回 null，用 `// "默认"` 给兜底：`.name // "unknown"`。
:::

## 运维实战

**批量取服务器 IP**：`curl -s api/hosts | jq -r '.[].ip'` 直接拿到纯 IP 列表喂给后续命令。
**统计状态分布**：`jq 'group_by(.status) | map({status:.[0].status, count:length})'`。

## 相关命令

[curl](/commands/network/curl) · [yq](./yq)（YAML） · [kubectl](/services/container/kubernetes/03-功能)

## 官方文档

- jq 手册：<https://jqlang.github.io/jq/manual/>
- jq 教程：<https://jqlang.github.io/jq/tutorial/>