---
title: "Alertmanager · 告警路由与降噪"
description: "Alertmanager 的分组/去重/静默/抑制/路由五大机制、安装与配置、route 路由树与 receiver、inhibit 抑制规则、邮件/钉钉/企业微信 webhook 对接、告警风暴治理。单页四段。"
---

# Alertmanager · 告警路由与降噪

> 单页四段：理论 → 部署 → 功能 → 实战。返回 [服务详解 · 监控与可观测](/services/observability/)。告警产生见 [Prometheus 04](/services/observability/prometheus/04-实战)。

## 01 · 服务理论

Prometheus 只**产生**告警，**发送**靠 Alertmanager。为什么不直接发？因为原始告警又吵又乱：一台机器挂了可能触发几十条相关告警。Alertmanager 做五件事降噪：

- **分组 Grouping**：同类告警合并成一条通知（一个机房断网，发一条"机房 X 网络故障"而不是几百条）。
- **去重 Deduplication**：相同告警不重复发。
- **静默 Silence**：维护期按标签匹配屏蔽告警。
- **抑制 Inhibition**：critical 触发时压住同目标的 warning（机器都挂了，就别再报它 CPU 高）。
- **路由 Routing**：按标签把告警发到不同接收端（数据库告警发 DBA 群）。

## 02 · 部署方案

```bash
wget https://github.com/prometheus/alertmanager/releases/download/v0.34.1/alertmanager-0.34.1.linux-amd64.tar.gz
tar xf alertmanager-0.34.1.linux-amd64.tar.gz
sudo mv alertmanager-0.34.1.linux-amd64/alertmanager /usr/local/bin/
```

systemd 跑 `alertmanager --config.file=/etc/alertmanager/alertmanager.yml --storage.path=/data/alertmanager`，默认 9093 端口。Prometheus 的 alerting 段指向 `10.0.0.10:9093`（见 [Prometheus 02](/services/observability/prometheus/02-部署)）。

## 03 · 功能详解

### 路由树与接收端

```yaml
route:
  receiver: 'default'
  group_by: ['alertname', 'cluster']     # 按这些标签分组
  group_wait: 30s                        # 新组等30s凑齐再发
  group_interval: 5m                     # 同组新告警间隔
  repeat_interval: 4h                    # 未恢复告警重发间隔
  routes:
    - match: { severity: critical }
      receiver: 'oncall'
    - match: { team: dba }
      receiver: 'dba-group'

receivers:
  - name: 'default'
    email_configs:
      - to: 'ops@example.com'
        from: 'alert@example.com'
        smarthost: 'smtp.example.com:465'
        auth_username: 'alert@example.com'
        auth_password: '请替换为SMTP授权码'
  - name: 'oncall'
    webhook_configs:
      - url: 'http://10.0.0.10:8080/webhook'   # 钉钉/企微机器人中转
```

route 是树形：子路由继承父配置，按 match 逐层匹配，命中即停。`group_wait` 让新组等一会儿凑齐同类告警再发，避免一条一条轰炸。

### 抑制规则

```yaml
inhibit_rules:
  - source_match: { severity: critical }
    target_match: { severity: warning }
    equal: ['instance']                  # 同实例的 critical 压住 warning
```

## 04 · 实战参考

### 钉钉/企业微信

Alertmanager 原生支持 email/webhook/PagerDuty 等。钉钉/企微用 **webhook 中转**：起一个 prometheus-webhook-dingtalk 之类的转换服务，把 Alertmanager 的 webhook 转成机器人消息格式。`repeat_interval` 别设太短，否则未恢复告警反复轰炸。

### 告警风暴治理

| 现象 | 原因 | 解法 |
|---|---|---|
| 一次故障几百条通知 | 没分组 | group_by 按 alertname/cluster |
| 维护期一直报 | 没静默 | Web UI 建 Silence 按标签屏蔽 |
| 机器挂了还报 CPU 高 | 没抑制 | inhibit_rules critical 压 warning |
| 告警反复重发 | repeat_interval 太短 | 调大到 4h+ |

**静默操作**：Web UI（9093）→ Silences → New，按标签匹配 + 设时长，维护完自动恢复。

## 官方文档

- Alertmanager：<https://prometheus.io/docs/alerting/latest/alertmanager/>
- 配置：<https://prometheus.io/docs/alerting/latest/configuration/>
- 通知模板：<https://prometheus.io/docs/alerting/latest/notifications/>

---

返回 [服务详解 · 监控与可观测](/services/observability/)。