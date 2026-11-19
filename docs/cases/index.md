---
title: "排障记录"
description: "故障与排障的单页聚合索引：按分类列出编号化排障记录，点详情看完整排查链路；一句话能说清的小问题记在速记区。统一编号，不用日期。"
---

# 排障记录

> 故障与排障的**单页聚合索引**。按分类列出每条排障记录，统一用**编号**（不用日期）；点「详情」进子页看完整排查链路。
> 一句话能说清的小问题记在下方[速记区](#速记一句话问题)；复杂排查写成详情子页。这些大多是学习时在虚拟机/实验环境复现的典型场景，**不是亲历线上事故**；真实环境搭建与踩坑记在 [我的项目](/projects/)。

## 编号规则

`分类前缀-序号`：L Linux · N 网络 · S 服务 · M MySQL · R Redis · D Docker · K Kubernetes · SEC 安全 · 速 速记。新增记录在对应分类末尾续号。

## 每条详情怎么写

刻意走完整条链路，形成肌肉记忆：

> **现象 → 报错 → 环境（真实版本）→ 定位命令 → 根因 → 止血 / 根治 → 验证预防**

## 分类记录

### Linux

| 编号 | 记录 | 难度 | 关键词 | 详情 |
|---|---|---|---|---|
| L-01 | 磁盘空间写满 | 初 | 磁盘, du, lsof | [详情](/cases/t-disk-space-full) |
| L-02 | 进程 D 状态不可中断假死 | 高 | D状态, NFS, IO等待 | [详情](/cases/t-process-d-state-hang) |

### 网络

| 编号 | 记录 | 难度 | 关键词 | 详情 |
|---|---|---|---|---|
| N-01 | DNS 解析失败 | 初 | DNS, dig, resolv.conf | [详情](/cases/t-dns-resolution-fail) |
| N-02 | TCP 重传率高 | 高 | TCP, 重传, 网卡 | [详情](/cases/t-tcp-retransmission) |

### 服务

| 编号 | 记录 | 难度 | 关键词 | 详情 |
|---|---|---|---|---|
| S-01 | Nginx 502 Bad Gateway | 中 | Nginx, 502, upstream | [详情](/cases/t-nginx-502) |
| S-02 | Nginx 504 Gateway Timeout | 中 | Nginx, 504, 超时 | [详情](/cases/t-nginx-504-timeout) |

### MySQL

| 编号 | 记录 | 难度 | 关键词 | 详情 |
|---|---|---|---|---|
| M-01 | 主从复制延迟排查 | 中 | 主从复制, 并行复制, 大事务 | [详情](/cases/t-mysql-replica-lag) |
| M-02 | 慢查询与索引失效 | 中 | 慢查询, EXPLAIN, 联合索引 | [详情](/cases/t-mysql-slow-query) |
| M-03 | InnoDB 死锁排查 | 高 | 死锁, 间隙锁, RR隔离级 | [详情](/cases/t-mysql-deadlock) |

### Redis

| 编号 | 记录 | 难度 | 关键词 | 详情 |
|---|---|---|---|---|
| R-01 | 内存打满 OOM | 中 | OOM, maxmemory, 淘汰策略, bigkey | [详情](/cases/t-redis-memory-oom) |
| R-02 | 哨兵故障切换/主从漂移 | 高 | 哨兵, 脑裂, fencing | [详情](/cases/t-redis-sentinel-failover) |

### Docker

| 编号 | 记录 | 难度 | 关键词 | 详情 |
|---|---|---|---|---|
| D-01 | dockerd 启动失败 | 中 | dockerd, daemon.json, data-root | [详情](/cases/t-docker-daemon-fail) |
| D-02 | 存储驱动 overlay2 与磁盘满 | 中 | overlay2, 磁盘满, prune | [详情](/cases/t-docker-storage-driver) |
| D-03 | 容器网络不通 | 中 | bridge, iptables FORWARD, DNS | [详情](/cases/t-docker-network-bridge) |

### Kubernetes

| 编号 | 记录 | 难度 | 关键词 | 详情 |
|---|---|---|---|---|
| K-01 | Pod 一直 Pending | 初 | Pending, 资源不足, PVC, 亲和 | [详情](/cases/t-k8s-pod-pending) |
| K-02 | ImagePullBackOff | 初 | ImagePullBackOff, tag, imagePullSecrets | [详情](/cases/t-k8s-imagepullbackoff) |
| K-03 | CrashLoopBackOff | 中 | CrashLoopBackOff, liveness探针, 启动慢 | [详情](/cases/t-k8s-crashloopbackoff) |
| K-04 | 节点 NotReady | 高 | NotReady, kubelet, 磁盘压力 | [详情](/cases/t-k8s-node-notready) |
| K-05 | etcd 故障/空间满/不一致 | 高 | etcd, defrag, quota, snapshot | [详情](/cases/t-k8s-etcd-failure) |

### 安全

| 编号 | 记录 | 难度 | 关键词 | 详情 |
|---|---|---|---|---|
| SEC-01 | 服务器被植入挖矿木马 | 高 | 挖矿木马, SSH爆破, cron | [详情](/cases/t-mining-trojan) |

## 速记（一句话问题）

> 一句话能说清的小问题直接记这里，编号续接，不开详情子页。关键词写全便于 Ctrl+K 搜到。

| 编号 | 现象 / 报错 | 关键词 | 解法 |
|---|---|---|---|
| 速-01 | SSH 连接很慢，要等十几秒 | ssh dns UseDNS 反向解析 | `/etc/ssh/sshd_config` 设 `UseDNS no`，`systemctl restart sshd` |
| 速-02 | df 有空间但无法写入、No space left | inode 满 小文件 | `df -i` 查 inode，清理海量小文件目录（详见 L-01 思路） |
| 速-03 | 启动服务提示 Address already in use | 端口占用 | `ss -tunlp \| grep :80` 或 `lsof -i :80` 找占用进程处理 |
| 速-04 | 新装 Docker，docker info 提示 swap 报错 | docker swap | 内核加 `swapaccount=1` 重启（详见 D-01 相关） |
| 速-05 | 容器长期运行写满宿主机磁盘 | docker json-file 日志 未轮转 | `daemon.json` 配 `"log-opts": {"max-size":"100m","max-file":"3"}` 重启重建容器；临时 `truncate -s 0` 清大日志 |

## 排障短文模板（复杂问题用）

> 新建 `cases/t-简短标题.md`，分配一个分类编号，复制以下结构（**用编号，不用日期**）：

```markdown
# 编号 · 问题标题

## 现象（含完整报错信息）
## 环境（系统版本、相关软件版本）
## 定位过程（用了哪些命令、看到什么）
## 根因
## 解决步骤
## 验证与预防
## 相关命令（链接到命令手册 / 服务详解）
```

## 常用排障入口

- 进程 / 端口 / 文件占用：[进程与系统命令](/commands/system/) · [排障观测](/commands/observe/)
- 网络不通 / DNS / 抓包：[网络命令](/commands/network/)
- 磁盘 / inode / 挂载：[磁盘与存储命令](/commands/storage/)
- 容器异常：[Docker 服务页](/services/container/docker/04-实战)
- K8s 异常：[Kubernetes 服务页](/services/container/kubernetes/04-实战)

---

## 常见问题 FAQ

> 综合场景与故障排查问题的高频问题已并入本页。默认只显示问题，点开查看完整答案。

### 一、部署前：容量与架构设计

<details>
<summary>Q1：怎么做容量评估？QPS、带宽、连接数、磁盘怎么算？</summary>

**答：**

系统设计第一句话永远是"先问规模"，先要几个数：日活用户多少、峰值 QPS 多少、数据存多久。然后把账算清楚，这是好习惯。

**QPS**：假设日活 100 万，平均每人每天访问 20 个接口，一天总请求就是 2000 万。按二八定律，80% 流量集中在 20% 高峰时段（约 4 小时），那平均 QPS ≈ 2000万 × 0.8 / (4×3600) ≈ 1100。峰值一般再乘 2~3 倍，按 **3000 QPS** 去设计。

**带宽**：假设每个响应平均 5KB，3000 QPS × 5KB ≈ 15MB/s ≈ 120Mbps，对外带宽按峰值留余量买 200Mbps，静态图片扔 CDN 回源，源站带宽就省下来了。

**连接数**：每台应用服务器能扛的并发连接取决于文件句柄和线程池。假设单台能稳定扛 500 QPS，3000 QPS 就需要至少 6 台，再留 1~2 台冗余做故障切换，总共 **8 台**。

**磁盘增长**：假设每条业务日志 1KB、每天写 500 万条，一天就是 5GB；数据库按每天新增 100 万行、每行 1KB 算约 1GB/天。按保留 1 年粗算，再乘 2~3 倍冗余，规划存储。

算完我会说：这些数都是粗估，**真实容量靠压测和线上观测校准**，但实际做容量评估时能这样一步步算，就体现"用数字说话"的习惯，而不是上来就堆组件。

</details>

<details>
<summary>Q2：高可用设计有哪些核心原则？</summary>

**答：**

高可用的目标是 SLA，比如要做到 99.95%，一年故障时间不能超过 4 小时。我用五条原则搭。

第一**消除单点**：任何组件都不能只有一份，一台挂了整个系统就得活着。应用多实例、数据库主从、SLB 后面挂多台。

第二**无状态**：应用服务器本身不存会话和文件，会话丢 Redis、文件放 OSS，这样任意一台挂了流量转给别的台无感，也能随便水平加机器。

第三**负载均衡 + 健康检查**：SLB 做分发，自动摘除不健康的后端实例。

第四**故障自动切换**：数据库主从复制 + 自动 failover，Redis 哨兵/集群，跨可用区部署，一个 AZ 挂了另一个顶。

第五**备份 3-2-1**：关键数据三份副本、两种介质、一份异地，定期做恢复演练——备份能不能用，得真恢复一次才算数。

还要配弹性伸缩扛突发流量，加上限流、熔断、降级兜底。我会强调：高可用不是堆机器，是**每一层都问一句"这层挂了会怎样"**，答案不能是"全站崩"。

</details>

<details>
<summary>Q3：完整设计一个高可用 Web 架构（设计范例）</summary>

**答：**

我以"一个面向 100 万日活的电商类 Web 服务"为例，从用户请求一路往后讲，这套可以直接脱稿说。

"假设我们要做一个高可用的 Web 业务，规模刚才算过约 3000 峰值 QPS。用户请求进来，第一步先到 **DNS**，解析到 **CDN**——静态图片、JS、CSS 全放 CDN 和对象存储 OSS，不回源，这样源站压力小一大半。动态请求回源到 **SLB/CLB**，SLB 后面挂 **8 台无状态应用服务器，跨两个可用区部署**，健康检查自动摘挂掉的实例。

应用层做成无状态：登录会话放 **Redis 集群**，Redis 做主从+哨兵保证自己也高可用。读多写少的热点数据（比如商品详情）先查 Redis，miss 才打数据库。

数据层：MySQL 用 **RDS 主从**，主库写、从库读，自动故障切换；大促前加只读实例分摊读压力。再往后是消息队列 **Kafka**，下单这种慢操作异步化，把用户请求先接住再慢慢处理，挡峰值。

整个系统配 **Prometheus + Grafana 监控**，告警接到 Alertmanager；变更走灰度和自动回滚；跨可用区容灾，关键数据做 3-2-1 备份。"

收尾我会主动说权衡："这套架构的代价是组件多、运维复杂。如果业务早期没这么大，我会先单体 + 一台 RDS + 一个 Redis 跑着，等流量真上来再按这条路径演进，而不是一上来就过度设计。"——主动讲权衡是系统设计题的高分动作。

</details>

<details>
<summary>Q4：系统设计题的答题框架是什么？</summary>

**答：**

系统设计不追求一步到位，按固定五步往下走，让排查思路更清楚。

第一步**澄清需求和规模**：先反问——这个服务给谁用、日活多少、要支持读多还是写多、一致性要求多强？别上来就画架构。

第二步**容量估算**：就是 Q1 那套，把 QPS、带宽、存储用口算出来，证明我知道要撑多大。

第三步**画核心组件和数据流**：从接入层（DNS/CDN/SLB）到应用、缓存、数据库、消息队列，先画一个能跑通的最小可用版本，不追求一步到位上微服务。

第四步**补高可用和扩展**：在每个组件上加冗余、做主从、加缓存、加分库分表的演进路径。

第五步**主动讲权衡和瓶颈**：哪块是未来瓶颈、为了一致性牺牲了可用性还是反过来、为什么这么选。

核心态度是：**没有完美架构，只有适合当前规模的权衡**。先做简单能跑的，再随流量演进，比一上来堆一堆高大上组件更稳妥。

</details>

### 二、部署与日常操作

<details>
<summary>Q5：设计一套监控和日志系统？</summary>

**答：**

我按"采集、缓冲、存储、展示、告警、容量"六块讲。

采集层：机器上跑 node_exporter 采系统指标，应用暴露 `/metrics`，日志用 Filebeat（K8s 里用 DaemonSet）采集。中间加一层**缓冲**：日志量突增时先入 Kafka/消息队列削峰，再让 ES 慢慢消费，避免把 ES 直接打垮——这是高可用的关键。

存储层：指标用 Prometheus，数据量大了用远端存储（Thanos/Mimir）做多副本和长期保留；日志存 Elasticsearch，按天建索引、设生命周期，热数据 SSD、冷数据降存储成本。展示层 Grafana 画大盘，Kibana 搜日志。告警层 Alertmanager 做分组、抑制、分级通知。

容量和扩展我会提：Prometheus 本身要做高可用双副本；ES 集群要多分片多副本，别把单分片搞太大；日志设保留周期（比如 30 天）自动清理，否则 ES 先写满。

设计原则一句话：**采集端轻量、中间有削峰、存储可扩展、告警可执行**。

</details>

<details>
<summary>Q6：统计 Nginx 日志的 PV、UV、Top IP、状态码分布？</summary>

**答：**

Nginx 默认访问日志每行格式大概是 `IP - - [时间] "请求" 状态码 字节 ...`，我用 awk 切字段来统计。假设日志是 `/var/log/nginx/access.log`，IP 在第 1 列、状态码在第 9 列。

**PV（总访问量）**就是日志总行数：

```bash
wc -l /var/log/nginx/access.log
```

**访问量 Top10 IP**，这是最常考的一条，我拆开讲：

```bash
awk '{print $1}' /var/log/nginx/access.log | sort | uniq -c | sort -rn | head -n 10
```

逐段解释：`awk '{print $1}'` 把每行第一列（客户端 IP）抽出来；`sort` 先排序，让相同 IP 挨在一起；`uniq -c` 去重并在前面**统计每个 IP 出现次数**；`sort -rn` 按次数**数字倒序**排；`head -n 10` 取前 10。想算 UV（独立 IP 数）就把 `uniq -c` 换成 `sort -u | wc -l`。

**状态码分布**，看 200/404/502 各有多少：

```bash
awk '{print $9}' /var/log/nginx/access.log | sort | uniq -c | sort -rn
```

思路一模一样，只是抽第 9 列状态码。

**只看今天某时段、或只看 5xx**：

```bash
grep '30/Sep/2026' /var/log/nginx/access.log | awk '{print $9}' | grep -E '^5' | wc -l
```

解释：先 `grep` 出 9 月 30 日的行，再抽状态码，`grep -E '^5'` 筛出以 5 开头的 5xx，最后数行数。

我总结个口诀：**awk 抽列 → sort 相邻 → uniq -c 计数 → sort -rn 排序 → head 取前 N**，日志统计万变不离其宗。

</details>

<details>
<summary>Q7：实时查看和过滤日志怎么做？</summary>

**答：**

**实时跟日志**用 `tail -f`：

```bash
tail -f /var/log/nginx/access.log
```

加 `-n 200` 先看最后 200 行再跟。**边跟边过滤**就接 grep：

```bash
tail -f /var/log/nginx/access.log | grep -E '502|504'
```

`-E` 是扩展正则，一次匹配 502 和 504。想同时看上下文就 `grep -C 5 'error'`，`-C 5` 是匹配行前后各 5 行。

**查过去某段时间**不用 tail，用 grep 直接过滤时间段：

```bash
grep '30/Sep/2026:14:' /var/log/nginx/access.log
```

**systemd 管的服务**用 journalctl，比翻文件方便：

```bash
journalctl -u nginx -f              # 实时跟 nginx 服务日志
journalctl -u nginx --since "10 minutes ago"   # 最近 10 分钟
journalctl -u nginx -p err         # 只看 error 级别以上
```

**K8s 里看 Pod 日志**：

```bash
kubectl logs <pod-name> -f                    # 实时跟
kubectl logs <pod-name> --previous            # 容器崩溃前的上一个日志
kubectl logs <pod-name> -c <container>        # 多容器 Pod 指定容器
```

我现场排障的习惯是：先 `tail -f | grep` 盯着复现，复现到一条就拿关键字去 Kibana 搜全量，比在文件里盲翻快。

</details>

<details>
<summary>Q8：批量查找和处理文件怎么做？</summary>

**答：**

**按名字找文件**用 find：

```bash
find /var/log -name "*.log" -type f
```

`/var/log` 是查找起点，`-name` 按文件名（支持通配符），`-type f` 只要文件。按大小找（比如大于 100M 的大日志）：

```bash
find /var/log -type f -size +100M
```

**找到后批量处理**有两种接法。第一种 `find -exec`：

```bash
find /var/log -name "*.log" -mtime +30 -exec rm -f {} \;
```

解释：`-mtime +30` 是 30 天前改过的文件，`-exec ... {} \;` 对每个找到的文件执行删除，`{}` 代表找到的文件名。这就是个经典的"清理 30 天前日志"。

第二种更常用 `xargs`，把 find 的结果管道传给后面：

```bash
find /var/log -name "*.log" -mtime +30 -print0 | xargs -0 rm -f
```

`-print0`/`-0` 用空字符分隔文件名，防止文件名带空格被拆错。xargs 的好处是能控制并发和复用，比如批量打包：

```bash
find /data/backup -name "*.sql" -print0 | xargs -0 tar czf backup.tar.gz
```

**批量改配置**我一般先 `grep -rl "old_str" /etc/app/` 找出哪些文件含旧值，确认后再用 sed 批量替换：

```bash
grep -rl "192.168.1.10" /etc/app/ | xargs sed -i 's/192.168.1.10/10.0.0.5/g'
```

`sed -i` 直接改文件，`g` 全行替换。**生产上我一定会先不带 `-i` 跑一遍看替换结果，或者先备份，绝不在生产直接盲改。**

</details>

<details>
<summary>Q9：跨多台机器批量执行命令怎么做？</summary>

**答：**

**最简单的 for 循环**，靠 SSH 批量跑：

```bash
for ip in 10.0.0.{1..10}; do
  ssh root@$ip "hostname && uptime"
done
```

解释：`{1..10}` 是大展开，循环出 1 到 10 十个 IP；每台 ssh 过去跑 `hostname` 和 `uptime`。批量杀进程、批量看负载都这么干。想等结果就加 `< /dev/null` 防止交互卡住。

**要更稳就用 while 读 IP 列表文件**：

```bash
while read ip; do
  ssh -o ConnectTimeout=5 root@$ip "uptime"
done < hosts.txt
```

`-o ConnectTimeout=5` 是某台连不上别一直卡着。

**但正经生产我用 Ansible ad-hoc**，不用写剧本，一行命令管一组机器：

```bash
ansible web -m shell -a "uptime" -f 20
```

解释：`web` 是 inventory 里的主机组，`-m shell` 用 shell 模块，`-a` 是要执行的命令，`-f 20` 并发 20 台。批量装包：`ansible web -m yum -a "name=nginx state=latest"`；批量改服务：`ansible web -m service -a "name=nginx state=restarted"`。

可以这样对比：临时一次性操作用 for 循环或 ad-hoc，**重复要做、要幂等、要留痕的配置，一定要写成 Ansible playbook 而不是 shell 循环**——这也是 SRE 和"会写脚本"的区别。

</details>

### 三、运行故障与排障

<details>
<summary>Q10：你的通用排障思路是什么？</summary>

**答：**

我排障就一句话：**先止损，后定位，再复盘**，不能一上来就埋头查根因把故障时间越拖越长。

第一步**明确现象和影响**：先确认是什么挂了、影响多大、是全部用户还是部分、从什么时候开始的，别自己一个人闷头看，第一时间在故障群同步。

第二步**先止损**：能恢复优先恢复——有新版本发布就先回滚，流量大就先扩容，某个下游拖垮就先熔断降级。**恢复业务永远比找根因优先级高**，根因可以等业务活了再查。

第三步**分层定位**，我习惯从外往内一层层剥：**监控 → 网络 → 系统 → 中间件 → 应用**。先看监控大盘确认是哪一层红了，别猜；网络层用 `ping`/`ss`/`tcpdump` 看通不通、连接有没有堆积；系统层用 `top`/`iostat`/`free` 看 CPU 内存磁盘 IO；中间件层看 MySQL、Redis、MQ；应用层看日志。每一层都用证据验证假设，排除一层就划掉一层。

第四步**找根因**：定位到具体点后连续追问"为什么"，比如 OOM 是因为缓存没设上限。

第五步**写复盘**：故障时间线、根因、止血动作、改进项（加告警、改配置、补压测），跟进到人。

我在家庭实验室踩过的坑让我体会最深：很多故障不是"坏了"，而是某个参数没配对，所以养成了"先看监控和日志拿证据，再动手"的习惯。

</details>

<details>
<summary>Q11：网站突然打不开了，怎么处理？</summary>

**答：**

按"现场处置 → 根因定位 → 预防"三段讲。

**现场处置（先恢复）**：我先判断是个别用户还是全站、是自己这边还是所有用户——换个网络/手机流量试，`curl -I https://www.example.com` 看返回码。如果是全站 5xx，先看最近有没有发版，有就立刻回滚上一版本；SLB 后面健康检查如果后端全挂，先扩容或切到备用集群。

**根因定位（分层剥）**：从外往里。一是 **DNS**，`dig www.example.com` 看解析对不对、是不是解析到了错误 IP；二是 **接入层**，看 SLB/CDN 是不是被刷爆、带宽是不是打满（云监控看带宽监控）；三是**网络连通**，在服务器上 `ss -lntp` 看 Nginx 到底监听了没有，`systemctl status nginx` 看服务起没起，`tail -f /var/log/nginx/error.log` 看报错；四是**系统层**，`top` 看 CPU 是不是打满、`df -h` 看磁盘是不是写满、`free -m` 看内存；五是**应用层**，`tail -f` 应用日志，看是不是连不上数据库把请求 hang 住了。

我给个判断诀窍：`curl` 返回 **502/504** 通常是后端应用挂了或超时，重点查应用和它依赖的 DB/Redis；返回 **连接超时**多半是安全组/防火墙没放行或服务没监听；返回 **53/解析失败**先查 DNS。

**预防**：接入层做健康检查和自动摘除、监控 5xx 率和证书到期、关键页面拨探活、变更走灰度。

</details>

<details>
<summary>Q12：接口大面积超时，怎么查？</summary>

**答：**

**现场处置**：先看是某个接口还是一批接口、是全机房还是单实例。若是某个下游（比如支付）拖慢把线程池占满导致大面积超时，先在网关层对这个下游做**熔断/降级**，让主流程先能用；同时扩容应用实例，把排队的请求消化掉。

**根因定位**：超时本质是"请求处理时间超过了超时阈值"，我顺着调用链查。第一步看监控大盘，是应用自己 CPU/内存飙了，还是某个依赖变慢了——四大黄金信号里看延迟 P99 是哪一跳拉高的。第二步看**依赖**：连数据库的话，`show processlist` 看有没有慢查询/锁等待（`show engine innodb status` 看死锁）；连 Redis 的话看是不是 bigkey、慢日志。第三步看**资源**：`ss -s` 看 TIME_WAIT 是不是堆积到把连接打满、`ulimit -n` 文件句柄是不是耗尽、网络是不是丢包（`mtr`/`tcpdump`）。第四步看**日志和链路**，在 Kibana 按 trace_id 把慢请求串出来，定位卡在 SQL 还是外部 HTTP 调用。

我最常背的一句：大面积超时十有八九是某个下游变慢、把应用线程池/连接池占死，**雪崩效应**——所以别只盯应用本身，往下游查。

**预防**：接口超时和线程池参数合理配置、对下游加超时+重试+熔断（Sentinel/Resilience4j）、数据库慢查询监控和索引优化、做全链路压测摸容量上限。

</details>

<details>
<summary>Q13：磁盘被写满（No space left on device）怎么办？</summary>

**答：**

**现场处置**：先 `df -h` 看是哪个挂载点 100%。发现写满后别急着删——先定位大文件。用 `du -sh /* 2>/dev/null | sort -rh | head` 一层层往下找，常见元凶是日志目录 `/var/log`、容器日志 `/var/lib/docker/containers`、丢在根目录的 core dump、被删了但还被进程持有句柄的文件。这里有个经典坑：文件删掉了磁盘没释放，因为还有进程开着它——`lsof | grep deleted` 能查到，真正释放要重启那个进程或清空它打开的 fd。

紧急清理：定位到是应用日志就 `: > big.log` 截断（用 `>` 清空而不是 `rm`，避免句柄问题）；是容器日志就清 `/var/lib/docker/containers/*/*-json.log`。**千万不要直接 rm 正在被写的大日志**，要么 truncate 要么先确认没有进程占用。

**根因定位**：问清楚为什么涨上来——是日志没轮转（`logrotate` 没配）、还是某次调试 core dump、还是 Docker 镜像堆积、还是数据库 binlog 没清理。

**预防**：这里要强调几条。第一配 `logrotate` 按天轮转、按大小切、保留 N 份、自动压缩；第二容器日志设大小上限（docker `daemon.json` 里 `max-size`/`max-file`，或 K8s 用 `containerLogMaxSize`）；第三监控磁盘使用率到 75% 就告警，别等 100%；第四把数据盘和系统盘分开挂载，别让日志写爆根分区把系统搞挂。

</details>

<details>
<summary>Q14：数据库连接数被打满（too many connections），怎么处理？</summary>

**答：**

**现场处置**：报错就是应用报 `ERROR 1040 Too many connections`。紧急止血先看 `show processlist;` 找出大量 Sleep 或卡住的连接，把明显异常的批量 kill 掉腾位置；如果是连接池没释放导致，重启应用节点快速回收连接。临时还能调大 `max_connections` 救急，但这是饮鸩止渴。

**根因定位**：第一步 `show status like 'Threads_connected';` 看当前连接数、`show variables like 'max_connections';` 看上限。第二步**分析来源**：`select user,host,db,count(*) from information_schema.processlist group by user,host,db order by count(*) desc;` 看是哪个应用、哪台机器连得最多。第三步找原因：最常见是**应用连接池配置过大**（每台 maxPoolSize 配 200，几十台机器 ×200 直接顶满 MySQL 上限）；或者连接泄漏——用完不归还，连接越积越多；再或者慢查询把连接占着不放。

**预防**：这里要强调——连接数不是越多越好。正确做法是应用侧**连接池大小要算着配**（参考公式：连接数 ≈ ((核心数*2)+有效磁盘数)，一般几十足够），别无脑开大；用 RDS 这种托管库自带连接池；开启慢查询日志定位长事务；监控 `Threads_connected` 接近阈值就告警；做读写分离把读压力分走。

</details>

<details>
<summary>Q15：K8s 节点 NotReady 怎么排查？</summary>

**答：**

**现场处置**：先 `kubectl get nodes` 确认哪个节点 NotReady、持续多久了。业务上先把这个节点上的 Pod 腾挪——`kubectl drain <node> --ignore-daemonsets --delete-emptydir-data` 把 Pod 疏散走，让业务漂到别的节点；如果节点彻底坏了就 `kubectl delete node` 剔除，在云上再补一台。

**根因定位**：NotReady 是 kubelet 上报给控制面的状态为 Unknown/NotReady，我按四层查。第一步 `kubectl describe node <node>` 看 Conditions，事件里会直接写原因，比如 `KubeletNotReady runtime network not ready`、`DiskPressure`、`PIDPressure`、内存压力。第二步登节点看 kubelet：`systemctl status kubelet`、`journalctl -u kubelet -f`，看是不是 kubelet 挂了或容器运行时（containerd）没起来。第三步看**资源压力**：`df -h` 看容器镜像/日志把磁盘写满了（DiskPressure 最常见）、`free -h` 看内存、`pidof containerd` 看运行时。第四步看**网络**：`crictl ps` 看容器、`ip route`/CNI 插件是否正常、节点时间是否同步（NTP 不对会导致证书校验失败）。

我常见的根因就三个：磁盘被日志/镜像写满、kubelet/containerd 崩了、节点时间不同步。修好后 `kubectl uncordon <node>` 重新允许调度。

**预防**：节点磁盘监控和镜像垃圾回收（`imageGCHighThresholdPercent`）、kubelet 存活告警、系统时间统一 NTP、节点池留冗余容量。

</details>
