---
title: "服务详解 · 监控与日志"
description: "指标、告警、可视化与日志链路。"
---

# 监控与日志

> 服务详解分组 · 返回 [服务全景](/services/)
> 指标、告警、可视化与日志链路。

## 组内选型导读

Prometheus 采指标、Alertmanager 发告警、Grafana 做可视化，ELK/Filebeat 做日志采集检索。指标与日志两条链路互补，是 SRE 的眼睛。

## 本组服务

::: idx

| 服务 | 篇幅 | 入口 |
|---|---|---|
| Prometheus | 四篇 | [进入](/services/observability/prometheus/01-理论) |
| Grafana | 单页 | [进入](/services/observability/grafana) |
| Alertmanager | 单页 | [进入](/services/observability/alertmanager) |
| ELK / Filebeat | 单页 | [进入](/services/observability/elk) |

:::


## 统一四段模板

每个服务同一套顺序：**01 服务理论**（是什么/核心概念/架构/选型）→ **02 部署方案**（单机→主从→集群/容器化，环境→步骤→验证）→ **03 功能详解**（日常使用 + 专属命令中文详解 + 配置参数）→ **04 实战参考**（企业场景/FAQ/官方文档）。

::: tip 粒度规则
大服务（标"四篇"）一个目录四篇；小服务（标"单页"）一页四段。单服务部署写在服务页内，[部署方案](/deploy/) 只做索引与跨服务组合，不重复。
:::
