---
title: "yq · YAML 处理"
description: "yq 读取/修改 YAML 字段（K8s 清单、Ansible vars、配置文件），与 jq 语法相通。参数中文分级，含批量改镜像 tag 实战。"
---

# yq · YAML 处理

> 命令手册 · [开发与效率](/commands/devtools/) ｜ 频率：偶尔用
> jq 处理 JSON，yq 处理 YAML。K8s 清单、Ansible 变量、各种配置都是 YAML，脚本里改字段用 yq 比 sed 稳。

## 一句话用途

在脚本里精确读/改 YAML 字段，不破坏格式与注释。

## 高频场景速查

```bash
yq '.metadata.name' deploy.yaml                 # 取字段
yq '.spec.replicas = 3' deploy.yaml             # 改字段（mikefarah yq v4）
yq -i '.spec.replicas = 3' deploy.yaml          # -i 原地改
yq '.spec.template.spec.containers[0].image' deploy.yaml   # 取镜像
yq -i '.spec.template.spec.containers[0].image = "app:v2"' deploy.yaml
yq -o=json '.' config.yaml                      # YAML 转 JSON
```

## 参数详解

| 参数/写法 | 含义 |
|---|---|
| `.a.b` | 取嵌套字段 |
| `.a = 值` | 赋值 |
| `-i` | 原地修改文件 |
| `-o=json` / `-o=yaml` | 输出格式转换 |
| `eval-all` / `ea` | 多文档处理 |
| `.[0]` | 数组下标 |

::: warning 两个 yq 别混
市场有两个 yq：mikefarah/yq（Go，v4 语法如上）和 kislyuk/yq（Python，jq 包装）。语法不同，装错会报错。本文用 mikefarah v4。
:::

## 运维实战

**CI 里改镜像 tag**：`yq -i '.spec.template.spec.containers[0].image = "harbor.example.com/app:'$SHA'"' deploy.yaml`，再 kubectl apply。比 sed 替换可靠（不怕格式差异）。

**批量取 Ansible 变量**：`yq '.mysql_port' vars.yml`。

## 相关命令

[jq](./jq)（JSON） · [kubectl](/services/container/kubernetes/03-功能) · [Ansible](/services/cicd/ansible)

## 官方文档

- yq（mikefarah）：<https://mikefarah.gitbook.io/yq/>