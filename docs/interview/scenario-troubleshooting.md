# 故障排查实战

::: tip 本篇定位
先给通用排障方法论，再把高频综合故障场景按"现场处置 + 根因定位 + 预防"三段式讲透。
:::

## 高频面试题

### Q1：你的通用排障思路是什么？

**我的答案：**

我排障就一句话：**先止损，后定位，再复盘**，不能一上来就埋头查根因把故障时间越拖越长。

第一步**明确现象和影响**：先确认是什么挂了、影响多大、是全部用户还是部分、从什么时候开始的，别自己一个人闷头看，第一时间在故障群同步。

第二步**先止损**：能恢复优先恢复——有新版本发布就先回滚，流量大就先扩容，某个下游拖垮就先熔断降级。**恢复业务永远比找根因优先级高**，根因可以等业务活了再查。

第三步**分层定位**，我习惯从外往内一层层剥：**监控 → 网络 → 系统 → 中间件 → 应用**。先看监控大盘确认是哪一层红了，别猜；网络层用 `ping`/`ss`/`tcpdump` 看通不通、连接有没有堆积；系统层用 `top`/`iostat`/`free` 看 CPU 内存磁盘 IO；中间件层看 MySQL、Redis、MQ；应用层看日志。每一层都用证据验证假设，排除一层就划掉一层。

第四步**找根因**：定位到具体点后连续追问"为什么"，比如 OOM 是因为缓存没设上限。

第五步**写复盘**：故障时间线、根因、止血动作、改进项（加告警、改配置、补压测），跟进到人。

我在家庭实验室踩过的坑让我体会最深：很多故障不是"坏了"，而是某个参数没配对，所以养成了"先看监控和日志拿证据，再动手"的习惯。

---

### Q2：网站突然打不开了，怎么处理？

**我的答案：**

按"现场处置 → 根因定位 → 预防"三段讲。

**现场处置（先恢复）**：我先判断是个别用户还是全站、是自己这边还是所有用户——换个网络/手机流量试，`curl -I https://www.example.com` 看返回码。如果是全站 5xx，先看最近有没有发版，有就立刻回滚上一版本；SLB 后面健康检查如果后端全挂，先扩容或切到备用集群。

**根因定位（分层剥）**：从外往里。一是 **DNS**，`dig www.example.com` 看解析对不对、是不是解析到了错误 IP；二是 **接入层**，看 SLB/CDN 是不是被刷爆、带宽是不是打满（云监控看带宽监控）；三是**网络连通**，在服务器上 `ss -lntp` 看 Nginx 到底监听了没有，`systemctl status nginx` 看服务起没起，`tail -f /var/log/nginx/error.log` 看报错；四是**系统层**，`top` 看 CPU 是不是打满、`df -h` 看磁盘是不是写满、`free -m` 看内存；五是**应用层**，`tail -f` 应用日志，看是不是连不上数据库把请求 hang 住了。

我给个判断诀窍：`curl` 返回 **502/504** 通常是后端应用挂了或超时，重点查应用和它依赖的 DB/Redis；返回 **连接超时**多半是安全组/防火墙没放行或服务没监听；返回 **53/解析失败**先查 DNS。

**预防**：接入层做健康检查和自动摘除、监控 5xx 率和证书到期、关键页面拨探活、变更走灰度。

---

### Q3：接口大面积超时，怎么查？

**我的答案：**

**现场处置**：先看是某个接口还是一批接口、是全机房还是单实例。若是某个下游（比如支付）拖慢把线程池占满导致大面积超时，先在网关层对这个下游做**熔断/降级**，让主流程先能用；同时扩容应用实例，把排队的请求消化掉。

**根因定位**：超时本质是"请求处理时间超过了超时阈值"，我顺着调用链查。第一步看监控大盘，是应用自己 CPU/内存飙了，还是某个依赖变慢了——四大黄金信号里看延迟 P99 是哪一跳拉高的。第二步看**依赖**：连数据库的话，`show processlist` 看有没有慢查询/锁等待（`show engine innodb status` 看死锁）；连 Redis 的话看是不是 bigkey、慢日志。第三步看**资源**：`ss -s` 看 TIME_WAIT 是不是堆积到把连接打满、`ulimit -n` 文件句柄是不是耗尽、网络是不是丢包（`mtr`/`tcpdump`）。第四步看**日志和链路**，在 Kibana 按 trace_id 把慢请求串出来，定位卡在 SQL 还是外部 HTTP 调用。

我最常背的一句：大面积超时十有八九是某个下游变慢、把应用线程池/连接池占死，**雪崩效应**——所以别只盯应用本身，往下游查。

**预防**：接口超时和线程池参数合理配置、对下游加超时+重试+熔断（Sentinel/Resilience4j）、数据库慢查询监控和索引优化、做全链路压测摸容量上限。

---

### Q4：数据库连接数被打满（too many connections），怎么处理？

**我的答案：**

**现场处置**：报错就是应用报 `ERROR 1040 Too many connections`。紧急止血先看 `show processlist;` 找出大量 Sleep 或卡住的连接，把明显异常的批量 kill 掉腾位置；如果是连接池没释放导致，重启应用节点快速回收连接。临时还能调大 `max_connections` 救急，但这是饮鸩止渴。

**根因定位**：第一步 `show status like 'Threads_connected';` 看当前连接数、`show variables like 'max_connections';` 看上限。第二步**分析来源**：`select user,host,db,count(*) from information_schema.processlist group by user,host,db order by count(*) desc;` 看是哪个应用、哪台机器连得最多。第三步找原因：最常见是**应用连接池配置过大**（每台 maxPoolSize 配 200，几十台机器 ×200 直接顶满 MySQL 上限）；或者连接泄漏——用完不归还，连接越积越多；再或者慢查询把连接占着不放。

**预防**：这题我会强调——连接数不是越多越好。正确做法是应用侧**连接池大小要算着配**（参考公式：连接数 ≈ ((核心数*2)+有效磁盘数)，一般几十足够），别无脑开大；用 RDS 这种托管库自带连接池；开启慢查询日志定位长事务；监控 `Threads_connected` 接近阈值就告警；做读写分离把读压力分走。

---

### Q5：K8s 节点 NotReady 怎么排查？

**我的答案：**

**现场处置**：先 `kubectl get nodes` 确认哪个节点 NotReady、持续多久了。业务上先把这个节点上的 Pod 腾挪——`kubectl drain <node> --ignore-daemonsets --delete-emptydir-data` 把 Pod 疏散走，让业务漂到别的节点；如果节点彻底坏了就 `kubectl delete node` 剔除，在云上再补一台。

**根因定位**：NotReady 是 kubelet 上报给控制面的状态为 Unknown/NotReady，我按四层查。第一步 `kubectl describe node <node>` 看 Conditions，事件里会直接写原因，比如 `KubeletNotReady runtime network not ready`、`DiskPressure`、`PIDPressure`、内存压力。第二步登节点看 kubelet：`systemctl status kubelet`、`journalctl -u kubelet -f`，看是不是 kubelet 挂了或容器运行时（containerd）没起来。第三步看**资源压力**：`df -h` 看容器镜像/日志把磁盘写满了（DiskPressure 最常见）、`free -h` 看内存、`pidof containerd` 看运行时。第四步看**网络**：`crictl ps` 看容器、`ip route`/CNI 插件是否正常、节点时间是否同步（NTP 不对会导致证书校验失败）。

我常见的根因就三个：磁盘被日志/镜像写满、kubelet/containerd 崩了、节点时间不同步。修好后 `kubectl uncordon <node>` 重新允许调度。

**预防**：节点磁盘监控和镜像垃圾回收（`imageGCHighThresholdPercent`）、kubelet 存活告警、系统时间统一 NTP、节点池留冗余容量。

---

### Q6：磁盘被写满（No space left on device）怎么办？

**我的答案：**

**现场处置**：先 `df -h` 看是哪个挂载点 100%。发现写满后别急着删——先定位大文件。用 `du -sh /* 2>/dev/null | sort -rh | head` 一层层往下找，常见元凶是日志目录 `/var/log`、容器日志 `/var/lib/docker/containers`、丢在根目录的 core dump、被删了但还被进程持有句柄的文件。这里有个经典坑：文件删掉了磁盘没释放，因为还有进程开着它——`lsof | grep deleted` 能查到，真正释放要重启那个进程或清空它打开的 fd。

紧急清理：定位到是应用日志就 `: > big.log` 截断（用 `>` 清空而不是 `rm`，避免句柄问题）；是容器日志就清 `/var/lib/docker/containers/*/*-json.log`。**千万不要直接 rm 正在被写的大日志**，要么 truncate 要么先确认没有进程占用。

**根因定位**：问清楚为什么涨上来——是日志没轮转（`logrotate` 没配）、还是某次调试 core dump、还是 Docker 镜像堆积、还是数据库 binlog 没清理。

**预防**：这题我会强调几条。第一配 `logrotate` 按天轮转、按大小切、保留 N 份、自动压缩；第二容器日志设大小上限（docker `daemon.json` 里 `max-size`/`max-file`，或 K8s 用 `containerLogMaxSize`）；第三监控磁盘使用率到 75% 就告警，别等 100%；第四把数据盘和系统盘分开挂载，别让日志写爆根分区把系统搞挂。

---

## 相关链接

- [相关文档](/cases/troubleshooting)
- [网络排障](/interview/network-troubleshooting)
