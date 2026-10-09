---
category: 监控
difficulty: 中级
---

# Prometheus 实战 06：告警通知、路由与高可用

> **Prometheus 实战系列（共 10 篇）**
> ← 上一篇 [Prometheus 实战 05](./monitor-prometheus-05-rules-alertmanager) ｜ 下一篇 [Prometheus 实战 07](./monitor-prometheus-07-discovery-exporters) →
> [返回监控索引](./monitor)

### 5.4 告警模板

#### 5.4.1 模板说明

默认通知内容较简单，可以用 Go 模板语法自定义通知的标题、正文、表格。模板里可引用：

- `{{ $labels.标签名 }}`：触发告警的标签值；
- `{{ $value }}`：触发数值；
- `.Alerts`：本次通知里的所有告警（Firing/Resolved）；
- `$alert.StartsAt / EndsAt`：开始/恢复时间。

#### 5.4.2 邮件表格模板

**第 1 步：创建模板文件** `/usr/local/alertmanager/tmpl/email.tmpl`：

```text
{{ define "test.html" }}
<table border="1">
  <tr>
    <th>报警项</th>
    <th>实例</th>
    <th>报警阈值</th>
    <th>开始时间</th>
  </tr>
  {{ range $i, $alert := .Alerts }}
  <tr>
    <td>{{ index $alert.Labels "alertname" }}</td>
    <td>{{ index $alert.Labels "instance" }}</td>
    <td>{{ index $alert.Annotations "value" }}</td>
    <td>{{ $alert.StartsAt }}</td>
  </tr>
  {{ end }}
</table>
{{ end }}
```

语法解释：`{{ define "名字" }}...{{ end }}` 定义一个可按名字调用的模板；`range` 遍历每条告警；`index $alert.Labels "alertname"` 从标签字典里取 alertname 的值。

**第 2 步：加载并调用模板**，编辑 `alertmanager.yml`：

```yaml
templates:
  - '../tmpl/*.tmpl'

receivers:
  - name: 'email'
    email_configs:
      - to: '【收件邮箱】'
        send_resolved: true
        headers:
          subject: '[WARN] 报警邮件'
        html: '{{ template "test.html" . }}'
```

注意：模板调用 `{{ template ... }}` 要用单引号括住；headers 用字典写法时不要加单引号。

**第 3 步：在告警规则的 annotations 里补 value**（模板里用到了 `Annotations.value`）：

```yaml
        annotations:
          summary: "Instance {{ $labels.instance }} 停止工作"
          description: "{{ $labels.instance }} job {{ $labels.job }} 已经停止 1 分钟以上"
          value: "{{ $value }}"
```

检查生效：

```bash
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus
amtool check-config /usr/local/alertmanager/conf/alertmanager.yml
systemctl restart alertmanager
```

#### 5.4.3 更丰富的邮件正文模板

`/usr/local/alertmanager/tmpl/email_full.tmpl`：

```text
{{ define "email.html" }}
{{- if gt (len .Alerts.Firing) 0 -}}
{{ range .Alerts }}
========== start ==========<br>
告警程序: prometheus_alert <br>
告警级别: {{ .Labels.severity }} <br>
告警类型: {{ .Labels.alertname }} <br>
告警主机: {{ .Labels.instance }} <br>
告警主题: {{ .Annotations.summary }} <br>
告警详情: {{ .Annotations.description }} <br>
触发时间: {{ .StartsAt.Format "2006-01-02 15:04:05" }} <br>
========== end ==========<br>
{{ end }}{{ end -}}

{{- if gt (len .Alerts.Resolved) 0 -}}
{{ range .Alerts }}
========== start ==========<br>
告警级别: {{ .Labels.severity }} <br>
告警类型: {{ .Labels.alertname }} <br>
告警主机: {{ .Labels.instance }} <br>
恢复时间: {{ .EndsAt.Format "2006-01-02 15:04:05" }} <br>
========== end ==========<br>
{{ end }}{{ end -}}
{{ end }}
```

::: tip
`"2006-01-02 15:04:05"` 是 Go 语言固定的日期时间格式占位符（可以记成 1月2日 下午3点4分5秒），不要改成别的数字，否则时间显示会错。
:::

---

### 5.5 告警路由

#### 5.5.1 路由树说明

`route` 是一棵基于标签匹配的**树**：

- 所有告警从**根路由**进入；根路由必须匹配所有告警，**不能写匹配条件**，它的 `receiver` 是默认接收者；
- 告警依次遍历 `routes` 子路由，遇到第一个匹配的分支就用该分支的接收者（`continue: false`，默认）；
- 设 `continue: true` 则匹配后继续往后匹配，可实现一条告警发往多个渠道。

**新版用 `matchers` 替代了旧的 `match` / `match_re`**。matcher 写法和 PromQL 选择器一致，支持 `=`、`!=`、`=~`、`!~`：

```yaml
route:
  receiver: 'email'
  group_by: ['alertname', 'cluster']
  group_wait: 10s
  group_interval: 5m
  repeat_interval: 3h
  routes:
    - receiver: 'leader-team'
      matchers:
        - severity = "critical"
    - receiver: 'ops-team'
      matchers:
        - severity =~ "warning|info"
```

#### 5.5.2 路由案例：不同级别发给不同团队

需求：服务终止（critical）发给管理团队；QPS 异常（warning）发给运维团队；都没匹配则走默认 email。

**第 1 步：告警规则** `/usr/local/prometheus/rules/flask_alert_route.yml`：

```yaml
groups:
  - name: flask_web
    rules:
      - alert: InstanceDown
        expr: up{job="my_metric"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Instance {{ $labels.instance }} 停止工作"
          description: "{{ $labels.instance }} job {{ $labels.job }} 已经停止 1 分钟以上"
          value: "{{ $value }}"

  - name: flask_QPS
    rules:
      - alert: InstanceQPSIsHigh
        expr: increase(request_count_total{job="my_metric"}[1m]) > 500
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Instance {{ $labels.instance }} QPS 持续过高"
          description: "{{ $labels.instance }} job {{ $labels.job }} QPS 持续过高"
          value: "{{ $value }}"
```

**第 2 步：Alertmanager 路由配置**：

```yaml
global:
  resolve_timeout: 5m
  smtp_smarthost: 'smtp.163.com:25'
  smtp_from: '【你的发件邮箱】'
  smtp_auth_username: '【你的发件邮箱】'
  smtp_auth_password: '【邮箱授权码】'
  smtp_require_tls: false

templates:
  - '../tmpl/*.tmpl'

route:
  group_by: ['instance', 'cluster']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 3h
  receiver: 'email'
  routes:
    - receiver: 'leader-team'
      matchers:
        - severity = "critical"
    - receiver: 'ops-team'
      matchers:
        - severity =~ "^(warning)$"

receivers:
  - name: 'email'
    email_configs:
      - to: '【默认收件邮箱】'
        send_resolved: true
        html: '{{ template "test.html" . }}'
        headers:
          subject: '[WARN] 报警邮件'
  - name: 'leader-team'
    email_configs:
      - to: '【管理团队邮箱】'
        send_resolved: true
        html: '{{ template "test.html" . }}'
        headers:
          subject: '[CRITICAL] 应用服务报警邮件'
  - name: 'ops-team'
    email_configs:
      - to: '【运维团队邮箱】'
        send_resolved: true
        html: '{{ template "test.html" . }}'
        headers:
          subject: '[WARNING] QPS 负载报警邮件'
```

检查：

```bash
amtool check-config /usr/local/alertmanager/conf/alertmanager.yml
systemctl restart alertmanager
```

预期输出显示 `Found: ... 3 receivers`。

**第 3 步：验证**

- 停 Flask：critical 命中 leader-team 分支，管理团队收到邮件；
- 制造每分钟超过 500 次访问（把压测脚本循环次数调大）：warning 命中 ops-team；
- 如果把规则里 `severity: critical` 误拼成别的词（如 `criticaL`），所有子路由都匹配不上，告警会走根路由的默认 email——这是排查"该收的人没收到告警"时的一个重要思路。

#### 5.5.3 路由嵌套与多渠道

子路由还可以继续嵌套 `routes`，也可以一条告警同时通知多渠道：

```yaml
  routes:
    - receiver: 'multi-channel'
      matchers:
        - job =~ "mysql|java"
      continue: true          # 匹配后继续向下，实现多渠道
      routes:
        - receiver: 'dba-team'
          matchers:
            - job = "mysql"
```

---

### 5.6 告警抑制

#### 5.6.1 抑制原理

当 A 服务（被依赖方）故障，依赖它的 B 服务也会异常并触发一堆"连带告警"。抑制规则让"A 的告警存在时，B 的告警不再发"，把注意力集中到真正的根因。

判定逻辑（三要素）：

1. **源告警（source）**：已经存在的、更根本的告警（如主机宕机 critical）；
2. **目标告警（target）**：新产生的、可能由源告警引发的告警；
3. **equal**：源和目标告警在这些标签上的值必须完全相同（确保是同一处业务，避免误抑制）。

新版推荐用 `source_matchers` / `target_matchers`：

```yaml
inhibit_rules:
  - source_matchers:
      - severity = "critical"
    target_matchers:
      - severity = "warning"
    equal: ['instance']
```

含义：同一 instance 上，critical 告警存在时，该 instance 的 warning 告警被抑制。

#### 5.6.2 抑制案例

需求：Flask 服务终止（critical）时，不再触发同节点的 QPS 异常（warning）。

**第 1 步：告警规则**（在 5.5.2 基础上增加一条 QPS 为零的 warning 规则）：

```yaml
  - name: flask_QPS
    rules:
      - alert: InstanceQPSIsLow
        expr: up{job="my_metric"} == 0
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Instance {{ $labels.instance }} QPS 异常为零"
          description: "{{ $labels.instance }} job {{ $labels.job }} QPS 异常为 0"
          value: "{{ $value }}"
```

**第 2 步：在 alertmanager.yml 末尾加抑制规则**：

```yaml
inhibit_rules:
  - source_matchers:
      - severity = "critical"
    target_matchers:
      - severity = "warning"
    equal:
      - instance
```

**第 3 步：验证**

```bash
amtool check-config /usr/local/alertmanager/conf/alertmanager.yml
systemctl restart alertmanager
```

停掉 Flask：此时 critical 和 warning 条件同时成立，但因为抑制，只收到 critical 告警，warning 被压制，避免了告警风暴。

::: warning
`equal` 里的标签必须在两类告警上都真实存在且值一致，抑制才会生效。排查"抑制不生效"：先确认源/目标匹配器写对、再确认 equal 标签值完全相同。
:::

---
### 5.7 企业微信告警

#### 5.7.1 三种微信告警方式

1. 个人微信号发送（需借助第三方工具，不推荐）；
2. 公众号发送（个人公众号功能受限，可用官方测试接口体验）；
3. **企业微信（企业号）发送——推荐**，注册企业无需认证、免费、接口稳定。

公众号测试接口地址：

```text
https://mp.weixin.qq.com/debug/cgi-bin/sandbox?t=sandbox/login
```

#### 5.7.2 企业微信后台准备

**第 1 步：注册企业微信**，访问：

```text
https://work.weixin.qq.com/
```

用个人微信扫码，按提示填写企业信息即可（无需认证、无数量限制）。进入"我的企业"页面，记下**企业 ID（CorpID）**。

**第 2 步：创建部门和人员**

- 在"通讯录"里创建一个告警部门（如"运维部"），点部门名可看到**部门 ID（PartyID，如 2）**；
- 把要接收告警的人加入部门（微信邀请或手动添加）。

**第 3 步：创建自建应用**

"应用管理 → 自建 → 创建应用"，填名称、选可见范围（选刚才的部门）。创建后记下：

- **AgentId**（如 1000004）；
- **Secret**（应用密钥，点"查看"可能需要在企业微信里确认）。

**第 4 步：先用命令行验证接口可用**

获取 access_token：

```bash
curl -H "Content-Type: application/json" \
  -d '{"corpid":"【企业ID】","corpsecret":"【应用Secret】"}' \
  https://qyapi.weixin.qq.com/cgi-bin/gettoken
```

预期输出：

```text
{"errcode":0,"errmsg":"ok","access_token":"一长串token","expires_in":7200}
```

发一条测试消息（token 有效期 2 小时）：

```bash
curl -H "Content-Type: application/json" -d '{
  "toparty": "【部门ID】",
  "msgtype": "text",
  "agentid": "【AgentId】",
  "text": {"content": "PromAlert 告警测试"},
  "safe": "0"
}' "https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=【上一步的token】"
```

预期输出：

```text
{"errcode":0,"errmsg":"ok","msgid":"..."}
```

成员的微信（会在企业微信里，同时可收到微信插件通知）收到测试消息，说明四个关键信息都正确。

#### 5.7.3 Alertmanager 配置企业微信

编辑 `/usr/local/alertmanager/conf/alertmanager.yml`：

```yaml
global:
  resolve_timeout: 1m
  wechat_api_url: 'https://qyapi.weixin.qq.com/cgi-bin/'
  wechat_api_corp_id: '【企业ID】'

templates:
  - '../tmpl/*.tmpl'

route:
  group_by: ['instance', 'cluster']
  group_wait: 10s
  group_interval: 5m
  repeat_interval: 3h
  receiver: 'email'
  routes:
    # 只有 critical 才发企业微信，warning 走默认邮件
    - receiver: 'wechat'
      matchers:
        - severity = "critical"

receivers:
  - name: 'email'
    email_configs:
      - to: '【默认收件邮箱】'
        send_resolved: true

  - name: 'wechat'
    wechat_configs:
      - to_party: '【部门ID】'
        # to_user: '@all'   # 也可以发给企业所有人
        agent_id: '【AgentId】'
        api_secret: '【应用Secret】'
        send_resolved: true
        message: '{{ template "wechat.default.message" . }}'
```

字段解释：`to_party` 接收部门；`agent_id` 自建应用 ID；`api_secret` 应用密钥（也可以写在 global 的 `wechat_api_secret`）；`message` 指定消息内容模板。

#### 5.7.4 企业微信消息模板

创建 `/usr/local/alertmanager/tmpl/wechat.tmpl`：

```text
{{ define "wechat.default.message" }}
{{- if gt (len .Alerts.Firing) 0 -}}
{{- range $index, $alert := .Alerts -}}
{{- if eq $index 0 }}
========== 监控报警 ==========
告警状态：{{ .Status }}
告警级别：{{ .Labels.severity }}
告警类型：{{ $alert.Labels.alertname }}
故障主机：{{ $alert.Labels.instance }}
告警主题：{{ $alert.Annotations.summary }}
告警详情：{{ $alert.Annotations.description }}
触发阈值：{{ .Annotations.value }}
故障时间：{{ ($alert.StartsAt.Add 28800e9).Format "2006-01-02 15:04:05" }}
========== end ==========
{{- end }}
{{- end }}
{{- end }}
{{- if gt (len .Alerts.Resolved) 0 -}}
{{- range $index, $alert := .Alerts -}}
{{- if eq $index 0 }}
========== 异常恢复 ==========
告警类型：{{ .Labels.alertname }}
告警状态：{{ .Status }}
告警主题：{{ $alert.Annotations.summary }}
告警详情：{{ $alert.Annotations.description }}
故障时间：{{ ($alert.StartsAt.Add 28800e9).Format "2006-01-02 15:04:05" }}
恢复时间：{{ ($alert.EndsAt.Add 28800e9).Format "2006-01-02 15:04:05" }}
实例信息：{{ $alert.Labels.instance }}
========== end ==========
{{- end }}
{{- end }}
{{- end }}
{{- end }}
```

::: tip
企业微信服务器按 UTC 时间处理，模板里 `$alert.StartsAt.Add 28800e9` 是把时间加回 8 小时（28800 秒 = 8 小时），显示成北京时间。`.Add 28800e9` 中 28800e9 是 28800 秒对应的纳秒数。
:::

检查并重启：

```bash
amtool check-config /usr/local/alertmanager/conf/alertmanager.yml
systemctl restart alertmanager
```

验证：停 Flask 触发 critical，企业微信收到格式整齐的告警；恢复后收到恢复通知。高并发触发的 warning 只发邮件、不发微信。

---

### 5.8 钉钉告警

Prometheus 不直接支持钉钉，但 Alertmanager 支持 **Webhook**：用开源的 **prometheus-webhook-dingtalk** 做格式转换（钉钉机器人只接受它自己规定的 JSON 格式）。

#### 5.8.1 创建钉钉机器人

**第 1 步：准备钉钉 PC 端**（手机端不能添加机器人），下载页：

```text
https://www.dingtalk.com/
```

注册/登录后创建一个团队组织（右上角"创建企业/组织/团队"，按提示完成）。

**第 2 步：建告警群**：右上角"+"→ 发起群聊 → 选项目群类型，拉入相关同事。

**第 3 步：添加自定义机器人**：群设置 → 智能群助手 → 添加机器人 → 选择"自定义（通过 Webhook 接入自定义服务）"。

**第 4 步：安全设置（三选一或组合）**：

| 安全方式 | 说明 |
| --- | --- |
| 自定义关键词 | 消息必须包含指定词（如 `PromAlert`），最简单 |
| 加签 | 每次请求带时间戳和 HMAC-SHA256 签名，**最安全，推荐** |
| IP 地址段 | 只接受指定出口 IP |

创建完成后**务必保存 Webhook 地址**（含 access_token）：

```text
https://oapi.dingtalk.com/robot/send?access_token=【你的token】
```

#### 5.8.2 先用命令验证机器人

只用关键词时：

```bash
WEBHOOK_URL="https://oapi.dingtalk.com/robot/send?access_token=【你的token】"
curl -H "Content-Type: application/json" \
  -d '{"msgtype":"text","text":{"content":"PromAlert - 钉钉告警测试"}}' \
  ${WEBHOOK_URL}
```

预期输出：

```text
{"errcode":0,"errmsg":"ok"}
```

消息不含关键词时会被拒绝：

```text
{"errcode":310000,"errmsg":"keywords not in content"}
```

**加签方式**：需要先用 Secret（以 `SEC` 开头）生成时间戳和签名。Python 脚本 `/usr/local/bin/create_dingtalk_sign.py`：

```python
#!/usr/bin/python3
import time, hmac, hashlib, base64
import urllib.parse

timestamp = str(round(time.time() * 1000))
secret = '【你的加签Secret，SEC开头】'
secret_enc = secret.encode('utf-8')

string_to_sign = '{}\n{}'.format(timestamp, secret)
string_to_sign_enc = string_to_sign.encode('utf-8')

hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))

print("Timestamp:", timestamp)
print("Sign:", sign)
```

运行：

```bash
python3 /usr/local/bin/create_dingtalk_sign.py
```

预期输出：

```text
Timestamp: 1770000000000
Sign: KAHQEy%2BV7mbs5oaEuXX%2FlBaimtGEQar5un2YgeYv7Dw%3D
```

把时间戳、签名拼到 Webhook 地址后即可发送（签名有有效期，需现取现用）：

```bash
curl -H 'Content-Type: application/json' -d '{
  "msgtype": "markdown",
  "markdown": {
    "title": "PromAlert 告警信息",
    "text": "## 问题详情 \n### 问题级别：严重 \n### 问题类型：MySQL 服务"
  }
}' "https://oapi.dingtalk.com/robot/send?access_token=【你的token】&timestamp=【时间戳】&sign=【签名】"
```

#### 5.8.3 部署 prometheus-webhook-dingtalk

在**监控服务器 monitor** 上执行，用户 root。

**第 1 步：下载安装**

```bash
cd /usr/local
wget https://github.com/timonwong/prometheus-webhook-dingtalk/releases/download/v2.1.0/prometheus-webhook-dingtalk-2.1.0.linux-amd64.tar.gz
tar xf prometheus-webhook-dingtalk-2.1.0.linux-amd64.tar.gz
ln -s prometheus-webhook-dingtalk-2.1.0.linux-amd64 dingtalk
cd dingtalk
mkdir -p bin conf
mv prometheus-webhook-dingtalk bin/
cp config.example.yml conf/config.yml
```

GitHub 下载慢时，在前面加 GitHub 代理前缀（如 `https://ghproxy.net/`、`https://gh-proxy.com/`，代理可能变动）。

**第 2 步：配置钉钉目标**，编辑 `/usr/local/dingtalk/conf/config.yml`：

```yaml
## 请求超时
timeout: 5s

## 自定义模板路径（可选）
templates:
  - contrib/templates/dingtalk.tmpl

## 默认消息使用自定义模板（可选）
default_message:
  title: '{{ template "_ding.link.title" . }}'
  text: '{{ template "_ding.link.content" . }}'

## 目标（钉钉机器人），可配多个（webhook1、webhook2……）
targets:
  webhook1:
    url: https://oapi.dingtalk.com/robot/send?access_token=【你的钉钉token】
    # 加签 Secret（用关键词安全方式时此行可省）
    secret: 【你的加签Secret，SEC开头】
```

**第 3 步：创建服务文件**

```bash
cat > /etc/systemd/system/dingtalk-webhook.service <<'EOF'
[Unit]
Description=Prometheus Webhook DingTalk
After=network-online.target

[Service]
Type=simple
User=prometheus
Group=prometheus
ExecStart=/usr/local/dingtalk/bin/prometheus-webhook-dingtalk \
  --config.file=/usr/local/dingtalk/conf/config.yml \
  --web.listen-address=0.0.0.0:8060
ExecReload=/bin/kill -HUP $MAINPID
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
chown -R prometheus:prometheus /usr/local/dingtalk/
systemctl daemon-reload
systemctl enable --now dingtalk-webhook
ss -lntp | grep 8060
```

参数解释：`--web.listen-address` 是 webhook 接收地址端口（默认 8060）；Alertmanager 会把告警 POST 到 `http://【监控服务器IP】:8060/dingtalk/webhook1/send`。

**第 4 步：手工测试 webhook**

```bash
curl "http://localhost:8060/dingtalk/webhook1/send" \
  -H 'Content-Type: application/json' -d '{
    "msgtype": "markdown",
    "markdown": {
      "title": "PromAlert 告警信息",
      "text": "## 问题详情 \n### 问题级别：严重 \n### 问题类型：测试"
    }
  }'
```

预期输出：`OK`，钉钉群收到消息。

如果钉钉机器人同时设置了"自定义关键词"而消息里没有，日志报：

```text
msg="Failed to send notification to DingTalk" respCode=310000 respMsg="keywords not in content"
```

::: tip
使用 prometheus-webhook-dingtalk 时，安全设置建议**只用加签**（插件生成的消息不一定包含你的关键词）；若一定要用关键词，要保证模板里每条消息都带该词（如把关键词写进固定标题）。
:::

#### 5.8.4 Alertmanager 对接钉钉

编辑 `alertmanager.yml`，增加接收者与路由：

```yaml
route:
  receiver: 'email'
  routes:
    - receiver: 'dingtalk'
      matchers:
        - severity = "critical"

receivers:
  - name: 'email'
    email_configs:
      - to: '【默认收件邮箱】'
        send_resolved: true

  - name: 'dingtalk'
    webhook_configs:
      - url: 'http://【监控服务器IP】:8060/dingtalk/webhook1/send'
        send_resolved: true
```

检查生效：

```bash
amtool check-config /usr/local/alertmanager/conf/alertmanager.yml
systemctl restart alertmanager
```

验证：停 Flask，钉钉群收到告警卡片；恢复后收到恢复通知。

#### 5.8.5 自定义钉钉模板（带图标、分区展示）

**第 1 步：准备两张全网可访问的图标**（放自己的网站/对象存储，如七牛云、阿里 OSS）：

```text
http://【你的图标域名】/images/ERROR.png
http://【你的图标域名】/images/OK.png
```

**第 2 步：创建模板** `/usr/local/dingtalk/contrib/templates/dingtalk.tmpl`：

```text
{{ define "__subject" }}[{{ .Status | toUpper }}{{ if eq .Status "firing" }}:{{ .Alerts.Firing | len }}{{ end }}] {{ .GroupLabels.SortedPairs.Values | join " " }}{{ end }}
{{ define "__alertmanagerURL" }}{{ .ExternalURL }}/#/alerts?receiver={{ .Receiver }}{{ end }}

{{ define "___text_alert_list" }}{{ range . }}
---
**告警主题：** {{ .Labels.alertname | upper }}
**告警级别：** {{ .Labels.severity | upper }}
**触发时间：** {{ dateInZone "2006-01-02 15:04:05" (.StartsAt) "Asia/Shanghai" }}
**事件信息：** {{ range .Annotations.SortedPairs }} {{ .Value | markdown | html }} {{ end }}
**事件标签：**
{{ range .Labels.SortedPairs }}{{ if and (ne (.Name) "severity") (ne (.Name) "team") }}> - {{ .Name }}: {{ .Value | markdown | html }}
{{ end }}{{ end }}
{{ end }}{{ end }}

{{ define "___text_resolve_list" }}{{ range . }}
---
**告警主题：** {{ .Labels.alertname | upper }}
**告警级别：** {{ .Labels.severity | upper }}
**触发时间：** {{ dateInZone "2006-01-02 15:04:05" (.StartsAt) "Asia/Shanghai" }}
**结束时间：** {{ dateInZone "2006-01-02 15:04:05" (.EndsAt) "Asia/Shanghai" }}
**事件信息：** {{ range .Annotations.SortedPairs }} {{ .Value | markdown | html }} {{ end }}
{{ end }}{{ end }}

{{ define "_default.content" }}
[{{ .Status | toUpper }}{{ if eq .Status "firing" }}:{{ .Alerts.Firing | len }}{{ end }}] **[{{ index .GroupLabels "alertname" }}]({{ template "__alertmanagerURL" . }})**
{{ if gt (len .Alerts.Firing) 0 -}}
![警报图标](http://【你的图标域名】/images/ERROR.png)
**======== PromAlert 告警触发 ========**
{{ template "___text_alert_list" .Alerts.Firing }}
{{- end }}
{{ if gt (len .Alerts.Resolved) 0 -}}
![恢复图标](http://【你的图标域名】/images/OK.png)
**======== PromAlert 告警恢复 ========**
{{ template "___text_resolve_list" .Alerts.Resolved }}
{{- end }}
{{ end }}
{{ define "_default.title" }}{{ template "__subject" . }}{{ end }}
{{ define "_ding.link.title" }}{{ template "_default.title" . }}{{ end }}
{{ define "_ding.link.content" }}{{ template "_default.content" . }}{{ end }}
```

**第 3 步：确认 config.yml 已加载该模板**（即 5.8.3 第 2 步的 templates 与 default_message 配置），重启：

```bash
systemctl restart dingtalk-webhook
```

触发告警后，钉钉消息会带图标、按分区展示级别/时间/标签，恢复消息带 OK 图标。

---

### 5.9 Alertmanager 高可用

#### 5.9.1 Gossip 协议原理

- **是什么**：Alertmanager 内置 **Gossip（流言）协议**，多个实例之间通过它同步告警、静默、通知状态。
- **为什么需要**：如果多台 Alertmanager 各自收到相同告警，没有状态同步就会**重复发送通知**；Gossip 保证同一条告警最终只发一次。
- **工作方式**：类似流言传播——节点把状态随机告诉其他节点，其他节点再继续传播，最终集群所有节点状态收敛一致；有 Push（主动推状态）和 Pull（主动询问新状态）两种方式。

#### 5.9.2 关键启动参数

| 参数 | 作用 |
| --- | --- |
| `--web.listen-address` | 本实例 Web 端口（默认 9093） |
| `--cluster.listen-address` | Gossip 集群通信地址（默认 9094），**集群必配** |
| `--cluster.peer` | 加入集群时指向**已有节点**的集群地址（首个节点不填，后续节点必填） |
| `--cluster.peer-timeout` | 连接对端超时 |

#### 5.9.3 跨主机两节点集群

**节点 A（第一台，监控服务器）**：

```bash
alertmanager \
  --web.listen-address=":9093" \
  --cluster.listen-address=":9094" \
  --config.file=/usr/local/alertmanager/conf/alertmanager.yml \
  --storage.path=/usr/local/alertmanager/data
```

**节点 B（第二台主机）**，启动时 peer 指向节点 A：

```bash
alertmanager \
  --web.listen-address=":9093" \
  --cluster.listen-address=":9094" \
  --cluster.peer=【节点A的IP】:9094 \
  --config.file=/usr/local/alertmanager/conf/alertmanager.yml \
  --storage.path=/usr/local/alertmanager/data
```

两台机器的 `alertmanager.yml` 内容保持一致（通知状态靠 Gossip 同步）。

**Prometheus 同时把两个 Alertmanager 都写上**：

```yaml
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - '【节点A的IP】:9093'
            - '【节点B的IP】:9093'
```

#### 5.9.4 单机多实例（学习/测试用）

实例 A1：

```bash
alertmanager --web.listen-address=":9093" \
  --cluster.listen-address="127.0.0.1:8001" \
  --config.file=/usr/local/alertmanager/conf/alertmanager.yml \
  --storage.path=/data/alertmanager/
```

实例 A2：

```bash
alertmanager --web.listen-address=":9094" \
  --cluster.listen-address="127.0.0.1:8002" \
  --cluster.peer=127.0.0.1:8001 \
  --config.file=/usr/local/alertmanager/conf/alertmanager.yml \
  --storage.path=/data/alertmanager2/
```

#### 5.9.5 Docker Compose 三节点集群

```yaml
version: '3.6'

networks:
  monitoring:
    driver: bridge

volumes:
  am01_data: {}
  am02_data: {}
  am03_data: {}

services:
  alertmanager01:
    image: prom/alertmanager:v0.34.1
    restart: always
    volumes:
      - ./alertmanager/:/etc/alertmanager/
      - am01_data:/alertmanager
    networks:
      - monitoring
    ports:
      - "9093:9093"
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
      - '--cluster.listen-address=0.0.0.0:9094'
      - '--cluster.peer-timeout=15s'

  alertmanager02:
    image: prom/alertmanager:v0.34.1
    restart: always
    volumes:
      - ./alertmanager/:/etc/alertmanager/
      - am02_data:/alertmanager
    networks:
      - monitoring
    ports:
      - "19093:9093"
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
      - '--cluster.listen-address=0.0.0.0:9094'
      - '--cluster.peer=alertmanager01:9094'
      - '--cluster.peer-timeout=15s'

  alertmanager03:
    image: prom/alertmanager:v0.34.1
    restart: always
    volumes:
      - './alertmanager/:/etc/alertmanager/'
      - am03_data:/alertmanager
    networks:
      - monitoring
    ports:
      - "29093:9093"
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
      - '--cluster.listen-address=0.0.0.0:9094'
      - '--cluster.peer=alertmanager01:9094'
      - '--cluster.peer-timeout=15s'
```

Prometheus 端 targets 写三个：`【监控服务器IP】:9093`、`【监控服务器IP】:19093`、`【监控服务器IP】:29093`。

验证：在任一 Alertmanager 页面 Status → Cluster Info 能看到 3 个成员；创建一个静默，几秒后会同步到其他实例；触发告警只收到一次通知。

::: warning
生产建议：① Alertmanager 至少部署 2 个实例（奇数个更利于投票，常用 3 个）；② Prometheus 自身的高可用是"双机采同样的目标 + external_labels 加 replica 标签 + 远程存储去重"，注意区分 Alertmanager HA 与 Prometheus HA；③ 各实例配置要保持一致。
:::

---

### 5.10 一体化告警平台 PrometheusAlert（可选了解）

PrometheusAlert 是国产开源的一体化告警中心，内置钉钉、企业微信、飞书、邮件等模板，带 Web 管理界面。项目地址：

```text
https://github.com/feiyu563/PrometheusAlert
```

Docker 快速体验：

```bash
docker run -d \
  -p 8080:8080 \
  -e PA_LOGIN_USER=prometheusalert \
  -e PA_LOGIN_PASSWORD=prometheusalert \
  -e PA_TITLE=PrometheusAlert \
  -e PA_OPEN_FEISHU=1 \
  -e PA_OPEN_DINGDING=1 \
  -e PA_OPEN_WEIXIN=1 \
  feiyu563/prometheus-alert:v5.0.0
```

浏览器访问 `http://【监控服务器IP】:8080`，默认用户名/密码 `prometheusalert/prometheusalert`。生产使用请固定镜像版本、改默认密码，并按其文档把 Alertmanager 的 webhook 指向它。

---

### 本阶段命令速查表

```bash
# === 记录规则 ===
vim /usr/local/prometheus/rules/xxx_record_rules.yml
promtool check rules /usr/local/prometheus/rules/xxx_record_rules.yml
# prometheus.yml: rule_files 加 "../rules/*.yml"，然后：
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus

# === Alertmanager ===
# 下载（GitHub，慢则在链接前加 https://ghproxy.net/）
wget https://github.com/prometheus/alertmanager/releases/download/v0.34.1/alertmanager-0.34.1.linux-amd64.tar.gz
# 服务文件见第 5 篇 5.2.3，然后：
systemctl daemon-reload
systemctl enable --now alertmanager
amtool check-config /usr/local/alertmanager/conf/alertmanager.yml
systemctl restart alertmanager

# === 钉钉插件 ===
# 下载（GitHub，慢则加 https://ghproxy.net/ 前缀）
wget https://github.com/timonwong/prometheus-webhook-dingtalk/releases/download/v2.1.0/prometheus-webhook-dingtalk-2.1.0.linux-amd64.tar.gz
# 服务文件见 5.8.3，然后：
systemctl enable --now dingtalk-webhook

# === 企业微信 token 验证 ===
curl -H "Content-Type: application/json" -d '{"corpid":"【企业ID】","corpsecret":"【应用Secret】"}' https://qyapi.weixin.qq.com/cgi-bin/gettoken
```

---

### 本阶段常见坑与解决

**坑 1：告警一直 Pending 不变 Firing**

- 现象：告警页面状态停在 Pending，Alertmanager 收不到。
- 原因：`for` 时间没到；或故障时好时坏、条件没有"持续"满足，计时不断被重置。
- 解决：确认 `for` 时长并等待；排查目标是否抖动（看抓取间隔、网络稳定性）。

**坑 2：Alertmanager 启动失败**

- 报错原样：`level=fatal ... root route must have a receiver`；或 `failed to parse configuration file: yaml: ...`。
- 原因：根路由没写 receiver；YAML 语法错误。
- 解决：根路由补 `receiver`；`amtool check-config` 定位错误后修正。

**坑 3：该收告警的人没收到（子路由没匹配）**

- 现象：告警存在，但指定团队没收到，被默认接收者接走。
- 原因：matcher 标签值拼错（大小写敏感，如 critical 拼成 criticaL）；标签根本没出现在告警上。
- 解决：核对告警规则 labels 与路由 matchers 完全一致；在 Alertmanager 页面看告警实际标签。

**坑 4：钉钉/企业微信收不到消息**

- 报错原样：钉钉 `respCode=310000 respMsg="keywords not in content"`；企业微信 `{"errcode":40014,"errmsg":"invalid access_token"}`。
- 原因：消息不含关键词/签名错误；token 过期（2 小时）或 corpid/secret 错误。
- 解决：钉钉改用加签或保证消息含关键词；微信重新获取 token、核对企业 ID 与应用 Secret。

**坑 5：高可用下重复收到告警**

- 现象：同一条告警被发送多次。
- 原因：实例间 Gossip 没连通（9094 端口未放通、peer 地址写错）。
- 解决：检查 `--cluster.listen-address`、`--cluster.peer`；放通 9094 TCP/UDP；Status → Cluster Info 确认成员到齐。

**坑 6：抑制规则不生效**

- 现象：critical 存在，warning 仍发出来。
- 原因：source/target 匹配器不对，或 equal 标签值不一致。
- 解决：amtool 检查配置；确认两类告警 equal 标签（如 instance）值完全相同。

**坑 7：静默设置后所有告警都不发/静默不生效**

- 现象：设置静默后范围过大；或多实例间静默没同步。
- 原因：静默匹配条件写太宽；Gossip 未同步。
- 解决：精确指定静默标签；维护结束及时删除静默（Expire 时间不要设太长）；确认集群同步正常。

**坑 8：邮件发不出去**

- 报错原样：`dial tcp smtp.163.com:25: i/o timeout` 或 `535 Error: authentication failed`。
- 原因：25 端口被云厂商封禁；授权码错误。
- 解决：改用 465（SSL，保留 TLS）或 587；重新生成并核对授权码。

---
