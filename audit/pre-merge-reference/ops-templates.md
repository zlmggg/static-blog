---
title: "运维文档模板（变更割接 / 故障报告 / 复盘 / 交接 / 架构评审）"
description: "禾光知寒：SRE 成长档案与运维手册，覆盖 Linux、网络、Docker、Kubernetes、数据库、监控与排障。"

---

# 运维文档模板（变更割接 / 故障报告 / 复盘 / 交接 / 架构评审）

> 本页是**可直接复制的运维文档模板**。每份模板用代码块包裹，整段复制到你的文档系统里再填。
> 用法：右侧「本页目录」跳转，或 `Ctrl+K` 搜索；模板里的 `【】` 是需要你替换的占位。
> 配套：日常逐条判定见 [Checklist 大全](/reference/ops-checklists)；复盘的"为什么这么做"原理见 [事故管理与无指责复盘](/guide/sre-incident)（本页只给可复制模板，不重讲原理）。

---

## 一、变更 / 割接方案

> 适用：发布、扩容、迁移、配置变更、版本升级等所有生产变更。**没有这个模板，就不要在生产动手。**

```markdown
# 变更/割接方案：【系统名-变更内容】

## 1. 背景与目标
- 变更原因：【为什么要做，解决什么问题】
- 变更目标：【期望达到的结果，最好带可验证指标】
- 变更时间窗口：【YYYY-MM-DD HH:MM ~ HH:MM，避开业务高峰】
- 执行人 / 复核人 / 值班人：【姓名（化名）】

## 2. 影响范围
- 影响系统：【哪些服务/链路会受影响】
- 影响用户：【内部/外部、预估影响面】
- 影响级别：【P0/P1/P2，是否有感知】
- 不影响的部分：【明确列出，避免误判】

## 3. 前置检查（动手前必须全部 ✅）
- [ ] 已备份：【数据库/配置/镜像，备份位置】
- [ ] 已确认回滚方案可执行
- [ ] 已通知相关方（业务/开发/客服）
- [ ] 监控与告警已就位，可观察变更过程
- [ ] 已在测试环境预演通过
- [ ] 业务低峰窗口确认

## 4. 操作步骤（按顺序，每步可验证）
1. 【步骤一：命令/操作 + 预期输出】
2. 【步骤二：……】
3. 【步骤三：……】

## 5. 回滚预案（最重要，先想清楚再动手）
- 触发回滚的条件：【出现什么现象立刻回滚】
- 回滚步骤：
  1. 【回滚命令/操作】
  2. 【……】
- 回滚预计耗时：【X 分钟】
- 回滚后验证：【确认业务恢复的检查项】

## 6. 变更后验证
- [ ] 功能验证：【核心功能点测试】
- [ ] 指标验证：【可用性/性能/错误率是否符合预期】
- [ ] 观察期：【变更后持续观察 X 分钟/小时】

## 7. 值班安排
- 变更后 X 小时内值班人：【谁盯】
- 应急联络：【升级路径，多久没恢复要上报】

## 8. 变更结论（事后填写）
- 实际结果：【成功/部分成功/回滚】
- 与方案的偏差：【哪步和预期不一样】
- 遗留问题与后续跟进：【……】
```

---

## 二、故障报告（Postmortem 面向管理层/周知）

> 适用：故障发生后，给团队/管理层一份简明、有结论的报告。**对事不对人，聚焦事实和改进。**

```markdown
# 故障报告：【一句话概括故障现象】

## 1. 时间线
- 发生时间：【YYYY-MM-DD HH:MM】
- 发现/告警时间：【HH:MM】
- 恢复时间：【HH:MM】
- 持续时长：【X 分钟】

## 2. 影响
- 影响范围：【哪些用户/业务/功能】
- 影响程度：【预计影响用户数/订单损失/错误率】
- 业务损失评估：【能估则估，不能则写"评估中"】

## 3. 现象与根因
- 表象：【用户看到什么、监控什么指标异常】
- 根因：【直接原因 + 深层原因，分层写清楚】
- 为什么没提前发现：【监控/流程的缺口】

## 4. 处置过程
- 谁在什么时间做了什么关键操作（简列时间线）
- 最终如何恢复

## 5. 整改行动项（Action Items）
| 序号 | 行动项 | 负责人 | 优先级 | 截止时间 |
|---|---|---|---|---|
| 1 | 【例：增加该指标告警】 | 【化名】 | P1 | 【日期】 |
| 2 | 【……】 | | | |

## 6. 经验教训
- 【这次做得好的】
- 【下次要改进的】
```

---

## 三、无指责复盘模板（Blameless Postmortem）

> 适用：P1/P2 故障后的深度复盘会。**原则：对系统不对人，找防御纵深漏洞，不找人背锅。**
> 原理和为什么这么做见 [事故管理与无指责复盘](/guide/sre-incident)，本模板只给可直接开会用的结构。

```markdown
# 无指责复盘：【故障标题】

> 本复盘遵守"无指责"原则：我们研究系统为什么允许了这次故障，
> 而不是谁犯了错。所有参与者在当时的信息下都做了合理判断。

## 1. 发生了什么（时间线，含所有关键决策点）
- HH:MM 系统状态 / 触发
- HH:MM 告警 / 发现
- HH:MM 某人判断【基于当时信息的合理推断】并采取【动作】
- HH:MM ……
- HH:MM 恢复

## 2. 影响与损失
【范围、时长、业务影响】

## 3. 为什么会发生（按防御纵深分层追问）
- 技术层：【哪个组件/配置/代码引入了问题】
- 监控层：【为什么没更早发现——盲区在哪】
- 流程层：【变更/评审哪里没拦住】
- 组织层：【有没有资源/沟通的系统性问题】

## 4. 为什么没早发现、没早挡住
- 监控盲区：……
- 依赖假设：【我们之前假设了什么，结果假设错了】

## 5. 做得好的地方（也要写）
- 【哪些处置是及时有效的，值得固化】

## 6. 行动项（可验证、有负责人、有截止时间）
| 行动项 | 类别(技术/监控/流程) | 负责人 | 截止 | 完成判定标准 |
|---|---|---|---|---|
| 【例：为该链路加错误率告警】 | 监控 | 【化名】 | 【日期】 | 告警上线并演练触发一次 |

## 7. 是否需要更新文档/预案
- [ ] 更新 Runbook
- [ ] 更新监控
- [ ] 补充自动化/自愈
```

---

## 四、交接文档（系统/岗位交接）

> 适用：人员离职、换班、系统移交。**目标：接手人照着这份文档能把系统跑起来。**

```markdown
# 系统/岗位交接文档：【系统名/岗位名】

## 1. 系统概览
- 这个系统是干什么的：【一句话 + 支撑的业务】
- 架构简图：【贴架构图，关键组件清单】
- 规模：【机器数/QPS/数据量/重要级别】

## 2. 关键信息（接手人最需要的）
- 登录入口、跳板机、密钥/账号位置（注意：不写明文密码）
- 监控大盘地址、关键告警项
- 核心日志位置与排障入口
- 外部依赖：【依赖哪些第三方/其他团队系统】

## 3. 日常运维操作
- 日常巡检：【见 Checklist】
- 常规发布流程：【链接到发布文档/流水线】
- 常见操作手册：【扩缩容、重启、清理等】

## 4. 已知坑与应急预案
- 历史踩过的坑：【……】
- 常见故障与处置：【现象→怎么办】
- 回滚/应急联系人：【升级路径】

## 5. 待办与遗留事项
- 还没做完的优化：【……】
- 已知风险：【……】

## 6. 交接确认
- 交接人 / 接手人 / 日期
- 接手人是否已独立操作过一次关键流程：【是/否】
```

---

## 五、架构评审记录（Architecture Review）

> 适用：新系统设计、重大方案评审。**目标：把权衡和取舍记录下来，避免日后"当初为什么这么设计"。**

```markdown
# 架构评审记录：【方案名】

## 1. 背景与需求
- 要解决的问题：【……】
- 非目标（明确不做什么）：【……】
- 关键约束：【性能/成本/时间/合规】

## 2. 方案与选型
- 选定方案：【架构描述 + 图】
- 关键技术选型及理由：
  | 选型 | 备选 | 最终选择 | 理由（含放弃备选的原因） |
  |---|---|---|---|

## 3. 评审关注点
- 可用性：【单点在哪、如何冗余】
- 扩展性：【瓶颈在哪、如何水平扩展】
- 数据一致性：【……】
- 安全：【鉴权、密钥、合规】
- 成本：【……】
- 可观测性：【监控/日志/告警如何设计】

## 4. 风险与权衡（重要，记录"为什么接受这个代价"）
- 已知风险：【……】
- 我们接受的权衡：【为了 XX，牺牲了 YY】

## 5. 评审结论
- 通过 / 有条件通过 / 打回
- 必须落地的改进项：【……】
- 评审人 / 日期
```

---

## 使用心得（几个提醒）

- **模板是脚手架，不是枷锁。** 小变更不必写满全部章节，但"**回滚预案**"和"**影响范围**"两栏永远不能省。
- **复盘模板一定要写"做得好的地方"**——只写问题会让大家害怕复盘，写了优点才愿意真实暴露问题。
- 行动项必须有**"完成判定标准"**，否则容易变成永远在做的"改进项"。

## 相关速查

- 逐条的上线/巡检/应急判定：[Checklist 大全](/reference/ops-checklists)
- 复盘与事故管理的原理：[事故管理与无指责复盘](/guide/sre-incident)
- SLO 与错误预算（影响范围、可用性评估的依据）：[SLO 与错误预算](/guide/monitor-slo)
- 容量与灾备（回滚、影响评估的依据）：[容量规划、高可用与灾备](/guide/sre-capacity-dr)
- 把模板里的操作自动化：[Python 运维自动化](/guide/automation-ansible#合并资料)

### 官方文档

- Google SRE Book（Postmortem 文化）：https://sre.google/sre-book/postmortem-culture/（需科学上网）；国内平替：https://www.cnblogs.com/lhxBlogs/p/17936005.html
- Google 无指责复盘范例：https://sre.google/resources/postmortem-library/（需科学上网，无国内平替）

<!-- merged-guide-material:start -->
## 合并资料

> 原先单独成页的同主题内容已收进本页；默认折叠，点开看原页全文。

<details>
<summary><strong>生产配置最佳实践模板（逐项注释&quot;为什么&quot;） — 把生产里最常配的五类——Nginx、MySQL、Redis、Kubernetes、内核 sysctl——整理成可整段复制、每行带注释为什么这么设的模板。抄走后按机器规格改数值即可。不重复各数据/服务专题的原理，这里是&#x27;开箱即用的配置基线&#x27;。</strong></summary>

::: tip 本篇定位
把生产里最常配的五类——Nginx、MySQL、Redis、Kubernetes、内核 sysctl——整理成**可整段复制、每行带注释为什么这么设**的模板。抄走后按机器规格改数值即可。不重复各数据/服务专题的原理，这里是"开箱即用的配置基线"。
本篇版本：Nginx 1.30.5（stable）、MySQL 8.4 LTS、Redis 8.x、Kubernetes 1.30+、内核 4.18~7.0。模板为基线，按实际规格调数值。
:::

#### 一、Nginx（1.30.5）

```nginx
# /etc/nginx/nginx.conf —— 通用生产基线
user  nginx;
worker_processes auto;          # 等于 CPU 核数；auto 自动探测，别写死 1，多核才能吃满
error_log  /var/log/nginx/error.log warn;
pid        /run/nginx.pid;

events {
    worker_connections 65535;   # 单 worker 最大连接；要和系统 nofile 一起调
    multi_accept on;            # 一次 accept 尽可能多连接，提升突发吞吐
    use epoll;                  # Linux 高并发用 epoll，别用 select
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    sendfile on;                # 内核态零拷贝发文件，比用户态快
    tcp_nopush on;              # 攒满 MSS 再发，配合 sendfile 提升吞吐
    tcp_nodelay on;             # 长连接小消息不延迟发，降低实时延迟
    keepalive_timeout 65;        # 客户端长连接超时，别太短（频繁建连）也别太长（占资源）
    keepalive_requests 1000;     # 单连接可复用请求数，高并发调大，否则老连接被断

    # 压缩：降带宽，JSON/文本响应体积可降 60%+
    gzip on;
    gzip_min_length 1k;          # 太小的不压，省 CPU
    gzip_types text/plain application/json text/css application/javascript;

    # 安全响应头（防常见 Web 攻击，按业务裁剪）
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options SAMEORIGIN;
    add_header X-XSS-Protection "1; mode=block";

    # 限流：见 expert-high-concurrency，这里给基线
    limit_req_zone $binary_remote_addr zone=perip:10m rate=20r/s;

    server {
        listen 443 ssl;
        server_name example.com;

        ssl_certificate     /etc/nginx/ssl/example.crt;
        ssl_certificate_key /etc/nginx/ssl/example.key;
        ssl_protocols       TLSv1.2 TLSv1.3;   # 禁用旧 SSL/TLS1.0/1.1
        ssl_ciphers         HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;
        ssl_session_cache   shared:SSL:10m;     # 会话复用，减少握手开销
        ssl_session_timeout 1d;

        location /api/ {
            limit_req zone=perip burst=40 nodelay;  # 突发 40 个排队
            limit_req_status 429;
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_http_version 1.1;          # 到上游用 HTTP/1.1，才能用 keepalive
            proxy_set_header Connection "";   # 清空 Connection 头，启用上游长连接
        }
    }
}
```

#### 二、MySQL（8.4 LTS）

```ini
# /etc/my.cnf —— 专库专用基线（假设 16G 内存、SSD）
[mysqld]
user            = mysql
port            = 3306
datadir         = /var/lib/mysql
socket          = /var/lib/mysql/mysql.sock

# —— 连接 ——
max_connections = 500            # 按连接池总和留余量；别盲目 1000+，每连接都吃内存
back_log        = 1024           # 连接请求排队，要和 somaxconn 对齐

# —— InnoDB 最关键的参数 ——
innodb_buffer_pool_size = 10G    # 专用库给物理内存 50%~70%；把热点数据放内存，最影响性能
innodb_log_file_size    = 2G     # redo 日志；大一点减少刷盘频率，但崩溃恢复变慢
innodb_flush_log_at_trx_commit = 1  # 1=每次事务刷盘最安全；性能敏感可评估 2（宕机丢 1s）
innodb_flush_method     = O_DIRECT # 绕过 OS 缓存，避免和 MySQL 双缓存浪费内存

# —— 慢查询与日志 ——
slow_query_log       = ON
slow_query_log_file  = /var/log/mysql/slow.log
long_query_time      = 1          # 超过 1s 记慢查询，找优化对象
log_error            = /var/log/mysql/error.log

# —— 字符集 ——
character_set_server  = utf8mb4   # utf8mb4 才能存 emoji，别用旧 utf8
collation_server      = utf8mb4_0900_ai_ci

# —— 安全 ——
local_infile         = OFF       # 禁用 load data local，防文件读取
skip_symbolic_links  = ON
```

```bash
# 改完重启并验证
systemctl restart mysqld
mysql -e "SHOW VARIABLES LIKE 'innodb_buffer_pool_size';"
mysql -e "SHOW VARIABLES LIKE 'character_set_server';"
```

#### 三、Redis（8.x）

```conf
# /etc/redis/redis.conf —— 基线
bind 0.0.0.0                    # 生产建议绑内网网卡，别裸奔公网
port 6379
protected-mode yes              # 开保护模式，没密码时拒绝外网

# —— 安全（必须）——
requirepass    你的强密码        # 一定要设密码，否则分分钟被挖矿
rename-command FLUSHALL ""      # 禁用危险命令（按需），防误操作/攻击
rename-command CONFIG ""

# —— 内存与淘汰 ——
maxmemory                4gb    # 设上限，别让 Redis 吃满机器内存
maxmemory-policy        allkeys-lru  # 内存满时按 LRU 淘汰；缓存场景必设
maxmemory-samples        5

# —— 持久化（按业务选）——
# RDB：定时快照，恢复快、丢数据多
save 900 1
save 300 10
# AOF：每次写日志，丢数据少、文件大
appendonly yes
appendfsync everysec            # 每秒刷盘，性能与安全折中

# —— 慢日志 ——
slowlog-log-slower-than 10000   # 超过 10ms 记慢日志
slowlog-max-len 128
```

```bash
systemctl restart redis
redis-cli -a 你的强密码 INFO memory | grep used_memory_human
```

#### 四、Kubernetes（1.30+）

```yaml
# 一个生产 Deployment 基线（requests/limits/PDB/探针/NetworkPolicy 思路）
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
spec:
  replicas: 3
  template:
    spec:
      containers:
        - name: app
          image: registry.example.com/app:v1.0.0   # 固定 tag，别用 latest
          resources:
            requests:                # 调度依据：保底资源
              cpu: "500m"
              memory: "512Mi"
            limits:                  # 上限：防止一个 Pod 吃满节点
              cpu: "1"
              memory: "1Gi"
          readinessProbe:            # 就绪探针：没好就不接流量
            httpGet: { path: /health, port: 8080 }
            initialDelaySeconds: 5
            periodSeconds: 5
          livenessProbe:             # 存活探针：挂了自动重启
            httpGet: { path: /health, port: 8080 }
            initialDelaySeconds: 15
            periodSeconds: 10
---
# PDB：保证升级/故障时至少留一个副本可用，不被一次全杀
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: app-pdb
spec:
  minAvailable: 1
  selector:
    matchLabels: { app: app }
---
# NetworkPolicy：默认拒绝跨命名空间访问，只放行需要的
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: app-netpol
spec:
  podSelector: { matchLabels: { app: app } }
  policyTypes: ["Ingress"]
  ingress:
    - from:
        - podSelector: { matchLabels: { role: gateway } }
      ports: [{ protocol: TCP, port: 8080 }]
```

> 数值按实际压测调：`requests` 太小会被频繁驱逐，`limits` 太大会 OOMKilled。JVM 应用记得用 `-XX:MaxRAMPercentage=75` 对齐容器 limit。

#### 五、内核 sysctl（4.18 ~ 7.0）

```ini
# /etc/sysctl.d/99-prod.conf —— 高并发 Web/DB 通用基线

# —— 文件句柄 ——
fs.file-max = 1048576              # 系统级总句柄上限
# 进程级配合 systemd LimitNOFILE=65535 或 limits.conf

# —— TCP 连接队列 ——
net.core.somaxconn = 65535          # 全连接队列，默认 128 太小，高并发必调
net.ipv4.tcp_max_syn_backlog = 65535  # 半连接队列

# —— TIME_WAIT 与本地端口 ——
net.ipv4.tcp_tw_reuse = 1           # 复用 TIME_WAIT 给新出站连接（安全）
# 注意：不要开 tcp_tw_recycle，新内核已废弃，NAT 环境会丢连接
net.ipv4.ip_local_port_range = 1024 65535  # 客户端出口端口范围，压测/外连多必调

# —— TCP 缓冲区（高 BDP 网络可调大）——
net.core.rmem_default = 262144
net.core.wmem_default = 262144
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216

# —— 内存 overcommit（DB 场景建议）——
vm.overcommit_memory = 1           # Redis 推荐 1；MySQL 场景评估 0/2，按业务

# —— 反向路由校验（容器/多网卡环境按需）——
# net.ipv4.conf.all.rp_filter = 2
```

```bash
sysctl --system                     # 加载所有 /etc/sysctl.d/*.conf
sysctl net.core.somaxconn           # 验证生效
```

#### 调参前后对照（基线参考）

| 参数 | 默认 | 基线建议 | 改后收益 |
|---|---|---|---|
| `worker_connections` | 512 | 65535 | 单机并发上限提升 |
| `somaxconn` | 128 | 65535 | 消除 ListenOverflows 丢连接 |
| `innodb_buffer_pool_size` | 128M | 物理内存 50~70% | 热点数据内存命中，查询快数倍 |
| `maxmemory`(Redis) | 无上限 | 4G + LRU | 防止 Redis 吃满机器 |
| `tcp_tw_reuse` | 0 | 1 | 高并发短连接不再端口耗尽 |
| `requests/limits`(K8s) | 不设 | 按压测设 | 节点不被单个 Pod 拖垮 |

::: warning 生产红线
- 所有数值按**实际机器规格和压测结果**调，别照抄——16G 内存和 64G 机器的 buffer_pool 不能一样。
- sysctl 改完用 `sysctl --system` 生效；进程级 nofile 要在 systemd unit 里设，limits.conf 对 systemd 服务常不生效。
- Redis 务必 `requirepass` + 绑内网；MySQL 别开 `local_infile`。
- K8s 镜像 tag 固定具体版本，禁止 `latest`；探针配错会导致服务起不来/频繁重启。
- 改任何生产配置前备份原文件，留回滚命令。
:::

#### 相关速查

- Nginx 原理与更多：[Nginx Web 服务](/guide/services-web-nginx)
- MySQL 进阶：[MySQL 数据](/guide/data-mysql)
- Redis 高可用：[Redis](/guide/data-redis)
- K8s 有状态与安全：[StatefulSet 与安全](/guide/container-k8s-02-pod-service-discovery#合并资料)
- 内核参数详解：[Linux 内核与 sysctl](/guide/linux#合并资料)
- 性能调优全流程：[性能调优实战](/guide/expert-tough-cases#合并资料)
- 配置/上线 Checklist：[/reference/ops-checklists](/reference/ops-checklists)

##### 官方文档

- Nginx 控制参数：https://nginx.org/en/docs/dirindex.html
- MySQL 8.4 服务参数：https://dev.mysql.com/doc/refman/8.4/en/server-options.html
- Redis 配置：https://redis.io/docs/latest/operate/oss_and_stack/management/config/
- Kubernetes 最佳实践：https://kubernetes.io/docs/concepts/configuration/overview/
- sysctl：https://man7.org/linux/man-pages/man5/sysctl.conf.5.html

</details>

<!-- merged-guide-material:end -->
