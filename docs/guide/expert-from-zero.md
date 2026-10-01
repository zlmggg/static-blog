---
category: 职业
difficulty: 初级
---

# 小公司 / 传统企业从零落地监控、自动化与 SRE

::: tip 本篇定位
面向人少、预算紧、历史包袱重的团队：怎么从"出了事才知道"一步步走到有监控、有自动化、有 SRE 稳定性思维。不堆大厂架构图，讲**优先级、取舍和怎么争取老板支持**。可结合家庭实验室练手。
本篇版本：Prometheus + Grafana 栈、Grafana Agent/OTel、Ansible、开源选型（2026-09 现状）。
:::

## 一、现实约束：先认清你手里的牌

小公司/传统企业做 SRE，和大厂最大的区别不是技术，是**约束条件**：

| 约束 | 具体表现 | 对落地的影响 |
|---|---|---|
| 人少 | 1~3 个运维兼开发，7×24 值班不现实 | 别上需要专职维护的重平台 |
| 预算有限 | 没有买商业监控的钱 | 选开源、单机就能跑的 |
| 历史包袱 | 老系统没人敢动、没文档 | 先观测再优化，别上来重构 |
| 变更风险 | 业务一停老板就找你 | 先做"只读"监控，不碰业务逻辑 |
| 认知差距 | 老板觉得"服务器不挂就行" | 用事故和钱说话，别讲术语 |

> 心法：**先止血，再治病，最后强身。** 不要一上来就想搞 K8s 多活微服务——你连监控告警都没有，那是给自己挖坑。

## 二、分阶段路线（四步走）

```mermaid
flowchart LR
    S1["阶段1<br>监控止血<br>出事先知道"] --> S2["阶段2<br>标准化与文档<br>机器/配置可复制"]
    S2 --> S3["阶段3<br>自动化<br>重复的事交给脚本"]
    S3 --> S4["阶段4<br>SRE稳定性<br>SLO/容量/演练"]
```

### 阶段 1：监控止血（0~3 个月，优先级最高）

目标：**出事先知道，而不是用户打电话告诉你。**

- 第一步：装一个能跑的监控。单机起步用 **Prometheus + Grafana**（一条 docker compose 起来），node_exporter 采机器指标。
- 先盯最关键的几个黄金指标：CPU、内存、磁盘、负载、关键进程存活、网站/接口探活。
- 告警先接**企微/钉钉机器人**（Webhook），别搞邮件——邮件没人看。
- 告警分级：只有"磁盘快满、服务挂了、CPU 爆了"才打电话/强提醒；其他发群里。

```bash
# 最小可用：docker compose 起 Prometheus + Grafana + node_exporter
# 这一步只花半天，换来"半夜不用靠用户报障"
docker compose up -d
# 然后 Grafana 导入 node_exporter 仪表盘（ID 1860 等社区模板）
```

### 阶段 2：标准化与文档（3~6 个月）

目标：**新机器能半小时配好，配置不再靠记忆。**

- 服务器清单（CMDB 极简版）：一张表/一个 markdown，记录每台机器跑什么、谁负责。
- 配置标准化：Nginx/MySQL/SSH 的配置抽成模板（参考 [config-best-practices](./config-best-practices)），新机器套模板。
- 文档：每个关键服务"怎么部署、怎么重启、日志在哪、出问题找谁"。文档不在多，在**能照着做**。

### 阶段 3：自动化（6~12 个月）

目标：**把你每周重复做的事脚本化。**

- 先 Ansible 批量操作：批量改配置、批量装 agent、批量重启。
- 再自动化重复运维：日志清理、备份校验、证书续期、巡检脚本（参考脚本集思路）。
- CI/CD 先从"自动部署测试环境"开始，别一步到位全自动化发布。

### 阶段 4：SRE 稳定性（12 个月以后）

目标：**从被动救火到主动管理稳定性。**

- 开始定 SLO：核心接口可用性 99.9%，错误率 P99 延迟。
- 容量规划：大促/月底结算前提前评估资源（见 [sre-capacity-dr](./sre-capacity-dr)）。
- 小范围做故障演练：先演练"挂一台机器怎么办"。

## 三、最小可用监控：半天跑起来（可复制）

别被"监控体系"四个字吓到。第一版只要能看到机器指标 + 收到告警就行：

```bash
# docker compose 起 Prometheus + Grafana + node_exporter
mkdir -p /opt/monitor && cd /opt/monitor
cat > compose.yaml <<'EOF'
services:
  prometheus:
    image: prom/prometheus:v3.4.0
    volumes: ["./prometheus.yml:/etc/prometheus/prometheus.yml"]
    ports: ["9090:9090"]
  node_exporter:
    image: prom/node-exporter:v1.9.0
    ports: ["9100:9100"]
  grafana:
    image: grafana/grafana:12.2.0
    ports: ["3000:3000"]
EOF
docker compose up -d
```

```yaml
# prometheus.yml：抓本机 node_exporter，别上来就抓几十台
scrape_configs:
  - job_name: node
    static_configs:
      - targets: ["host.docker.internal:9100"]
```

Grafana 里导入社区 Node Exporter 仪表盘（ID 1860），就能看到 CPU/内存/磁盘。告警先用 Alertmanager 接企微 Webhook：

```yaml
# 两条最关键的告警：服务挂了、磁盘快满
groups:
  - name: basic
    rules:
      - alert: DiskAlmostFull
        expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) < 0.15
        for: 5m
        labels: { severity: critical }
        annotations: { summary: "磁盘剩余不足 15%" }
      - alert: TargetDown
        expr: up == 0
        for: 2m
        labels: { severity: critical }
```

## 四、开源选型（小团队务实版）

| 场景 | 推荐 | 为什么（小团队视角） |
|---|---|---|
| 监控 | Prometheus + Grafana | 生态最大、单机能跑、文档多 |
| 告警 | Alertmanager + 企微/钉钉 Webhook | 不花钱、即时触达 |
| 日志 | 初期用 grep+journald，量大再 ELK/Loki | 别一开始就上重型 ELK |
| 自动化 | Ansible | 无 agent、YAML、上手快 |
| 部署 | 先 docker compose，量大再 K8s | 小机器 K8s 是负担 |
| 密钥/配置 | 初始用加密配置文件，别上 Vault | 人少维护不动重型方案 |

::: tip 家庭实验室练手
用一台旧机/虚拟机（或你自己的 E5 双路主机）搭一套 Prometheus+Grafana+Ansible，就是阶段 1~3 的完整演练。练熟了再搬到公司，比在生产上边做边学稳得多。
:::

## 五、90 天落地清单（照表执行）

| 时间 | 做什么 | 交付物 | 谁受益 |
|---|---|---|---|
| 第 1 周 | 装 Prometheus+Grafana，接入所有机器 | 监控大屏、CPU/磁盘告警 | 运维自己 |
| 第 2 周 | 加业务探活（HTTP 200 探测核心接口）、告警接企微 | "服务挂了 2 分钟内手机响" | 运维+业务 |
| 第 3~4 周 | 建服务器清单（一张表）、关键服务 runbook | CMDB 表 + 每个服务一页文档 | 团队/新人 |
| 第 2 月 | 配备份并**演练一次恢复**（数据库+配置） | 可恢复的备份，不是只会备份 | 老板（数据安全） |
| 第 2 月 | Ansible 批量装 agent、批量改配置 | 一次操作 10 台机器 | 运维效率 |
| 第 3 月 | 日志清理/证书续期/巡检脚本自动化 | 定时任务，不用人工记 | 运维 |
| 第 3 月 | 定第一个 SLO（核心接口可用性）、写一页给老板 | SLO + 上月可用性数据 | 老板/业务对齐 |

> 关键：**第 2 月一定要做"备份恢复演练"**。很多团队备份天天跑，但从没恢复过——真出事才发现备份是坏的。

### 备份优先级（钱少先保数据）

| 优先级 | 对象 | 做法 | 成本 |
|---|---|---|---|
| P0 | 数据库 | 每日 mysqldump/binlog + 异机存一份 | 低 |
| P0 | 配置文件 | nginx/mysql/redis 配置进 git | 极低 |
| P1 | 用户上传文件 | 定时同步到另一块盘/对象存储 | 低 |
| P2 | 系统镜像 | 整机快照（云平台） | 中 |

原则：**备份不在多，在"确定能恢复"**。每月随机挑一个备份做恢复演练，比每天备份却从不验证强。

## 六、怎么争取老板与业务支持

这是小团队最现实的难点。技术人常犯的错是"我觉得好就闷头做"，结果没人买单。

- **用事故说话**：上次宕机损失多少（人时、客户投诉、营业额），监控能避免多少——把它折算成钱。
- **用对比说话**："别的公司半夜告警自动打电话，我们靠用户第二天早上打电话"。
- **先给甜头再要资源**：先花半天做出监控大屏和告警，让老板亲眼看到"出了事手机就响"，比 PPT 管用。
- **要小步预算**：别说"给我十万搞平台"，说"先买一台备用服务器，把磁盘/数据库备份做了"。
- **和业务对齐目标**：SLO 不是运维自嗨，是和业务一起定"核心系统一年能停多久"。

一个可直接套用的汇报话术：

> "上次系统停了 2 小时，客服接了 200 个投诉、影响当天营业额。现在花半天搭监控，以后类似问题 2 分钟就能发现、平均 10 分钟恢复。先从这一台机器、一个核心接口开始，不影响现有业务。"

不说术语，只说"多久发现、多久恢复、上次损失多少"——老板听得懂。

## 七、常见反模式（别踩）

| 反模式 | 后果 | 正解 |
|---|---|---|
| 一上来上 K8s/微服务 | 人少维护不动，比单机更乱 | 先把单机监控和自动化做好 |
| 告警风暴（什么都告） | 告警太多没人看，真问题被淹没 | 先只告关键项，分级 |
| 只监控机器不监控业务 | 服务器绿的，但接口挂了 | 加业务探活（HTTP 状态码） |
| 文档全靠"我知道" | 人一走系统就没人会管 | 关键服务必须有 runbook |
| 不敢动老系统 | 越拖越脆，最后一次大事故 | 先观测、再灰度、保留回滚 |
| 自动化没测试就上生产 | 脚本写错全公司服务重启 | 先在测试机跑、加白名单 |
| 追求工具数量 | 装了十个工具，一个没用熟 | 一个 Prometheus 用熟胜过十个半成品 |

::: warning 生产红线
- 监控先做"只读"，不要上来就改生产配置/重启业务。
- 自动化脚本先在非生产验证， Ansible 先 `--check` 干跑。
- 告警通道要测试：上线前故意触发一次，确认手机真能收到。
- 备份比监控更优先：磁盘监控到了再告不如天天自动备份+定期校验可恢复。
- 小团队的 SRE 是"够用就好"，不是"和大厂对齐"。
:::

## 相关速查

- SLO/错误预算怎么定：[SLO 与可观测](./monitor-slo)
- 容量与灾备：[容量规划与灾备](./sre-capacity-dr)
- Ansible 自动化：[Ansible 配置管理](./automation-ansible)
- CI/CD 渐进落地：[CI/CD 进阶](./devops-cicd-advanced)
- 故障演练入门：[混沌工程](./sre-chaos)
- 配置模板：[生产配置最佳实践](./config-best-practices)
- 巡检/应急 Checklist：[/reference/ops-checklists](/reference/ops-checklists)

### 官方文档

- Prometheus：https://prometheus.io/docs/
- Grafana：https://grafana.com/docs/
- Ansible：https://docs.ansible.com/
- Loki 日志：https://grafana.com/docs/loki/
