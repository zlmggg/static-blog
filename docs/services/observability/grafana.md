---
title: "Grafana · 监控可视化大屏"
description: "Grafana 的数据源/仪表盘/面板/变量模型、安装与 Prometheus 数据源对接、看板导入与自定义变量、告警与权限、生产大屏实战。单页四段。"
---

# Grafana · 监控可视化大屏

> 单页四段：理论 → 部署 → 功能 → 实战。返回 [服务详解 · 监控与可观测](/services/observability/)。数据源 [Prometheus](/services/observability/prometheus/01-理论)。

## 01 · 服务理论

Prometheus 自带 Web UI 只能画简单图，**Grafana 是专业的可视化平台**：把时序数据画成漂亮的仪表盘、大屏，支持几十种数据源（Prometheus/MySQL/ES/Loki…）。

核心模型四层：

- **Data Source（数据源）**：数据从哪来，如 Prometheus。
- **Dashboard（仪表盘）**：一组面板的集合，一个主题一块大屏。
- **Panel（面板）**：单个图表，绑定一条或多条查询。
- **Variable（变量）**：顶部下拉框，让一块看板按实例/接口动态切换，不用为每台机器建一块板。

Grafana 本身不存数据，只负责查询和展示——数据还在 Prometheus 里。

## 02 · 部署方案

```bash
# RHEL 系
sudo dnf install -y grafana
sudo systemctl enable --now grafana-server     # 默认 3000 端口
```

或 Docker：`docker run -d -p 3000:3000 --name grafana grafana/grafana:13.2.2`。浏览器访问 `http://10.0.0.10:3000`，默认 admin/admin，**首次登录必须改密码**。

加 Prometheus 数据源：Configuration → Data Sources → Add → Prometheus，URL 填 `http://10.0.0.10:9090`，Save & Test 成功即可。

## 03 · 功能详解

### 导入现成看板

社区有海量现成看板，输 ID 一键导入：

- **1860**：Node Exporter Full（主机监控最全）。
- **193 / 14282**：Docker 容器监控。
- **7362**：MySQL Overview。

Dashboards → Import → 输 ID → 选数据源 → 导入。

### 自定义变量

看板没有按容器/实例过滤的下拉框时，自己加：Settings → Variables → New，类型 Query，查询如：

```promql
label_values(node_uname_info, instance)
```

保存后顶部出现实例下拉框，面板查询用 `{instance=~"$instance"}` 过滤。一块板看所有机器。

### 面板与告警

面板选可视化类型（Time series/Stat/Gauge/Table），写 PromQL 查询。Grafana 也能配告警（Alerting），但生产告警链路通常走 [Alertmanager](/services/observability/alertmanager) 统一管理，Grafana 专注展示。

## 04 · 实战参考

**典型大屏**：主机总览（1860）+ 业务黄金指标（延迟/流量/错误/饱和度，见 [Prometheus 理论](/services/observability/prometheus/01-理论)）+ 容器监控（193）。用变量做实例/命名空间切换，一块板覆盖全环境。

**常见坑**：

| 现象 | 原因 | 解法 |
|---|---|---|
| 面板 No Data | 数据源没选对/查询写错 | 检查数据源 + Explore 里试查询 |
| 看板全是 N/A | 变量没匹配到序列 | 检查变量查询和 label |
| 时间对不上 | 时区/时间范围 | 看板右上角调时间范围和时区 |

**权限**：生产按团队建 Organization/Folder，Viewer 只读、Editor 改板、Admin 管数据源，别全员 Admin。

## 官方文档

- Grafana：<https://grafana.com/docs/grafana/latest/>
- 看板库：<https://grafana.com/grafana/dashboards/>
- Prometheus 数据源：<https://grafana.com/docs/grafana/latest/datasources/prometheus/>

---

返回 [服务详解 · 监控与可观测](/services/observability/)。