# 排障训练场

> 这里是我整理的「**典型故障场景 + 标准排查套路**」，按方向分组、组内由浅入深，用来刻意训练自己“从现象往根因倒推”的排查思路。
>
> 说清楚：这些大多是我学习时整理、在虚拟机 / 实验环境里复现过的典型场景，**不是我亲历的线上事故**；我自己真实环境的搭建和踩坑，记在 [我的项目](/projects/) 里。日常小问题、报错踩坑则随时记到 [排障记录](./troubleshooting)。

## 每条案例怎么写

每条都刻意走完整条链路，逼自己形成肌肉记忆：

> **现象 → 报错 → 环境（真实版本）→ 定位命令 → 根因 → 止血 / 根治 → 验证预防**

## 案例目录

> 共 50 篇，按方向分组，组内按 **初 → 中 → 高** 排序，由浅入深。

### Linux

::: details Linux（11 篇）
| 日期 | 标题 | 难度 | 标签 | 链接 |
|---|---|---|---|---|
| 2020-11-03 | 磁盘空间写满 | 初 | 磁盘, du, lsof | [t-disk-space-full](/cases/t-disk-space-full) |
| 2019-09-15 | inode 耗尽 | 初 | inode, 小文件, postfix | [t-inode-exhausted](/cases/t-inode-exhausted) |
| 2018-07-08 | Permission denied 权限/属主/SELinux | 初 | 权限, SELinux, 属主 | [t-permission-ownership](/cases/t-permission-ownership) |
| 2019-04-12 | GRUB 损坏/内核升级后进 rescue | 中 | GRUB, 启动, 救援模式 | [t-grub-rescue-boot](/cases/t-grub-rescue-boot) |
| 2020-05-22 | 异常掉电后文件系统损坏 | 中 | fsck, ext4, 只读挂载 | [t-filesystem-fsck-corrupt](/cases/t-filesystem-fsck-corrupt) |
| 2021-03-14 | 时间不同步致 TLS/JWT 鉴权失败 | 中 | chrony, NTP, TLS | [t-clock-unsynced](/cases/t-clock-unsynced) |
| 2022-10-27 | Too many open files 句柄耗尽 | 中 | ulimit, fd, lsof | [t-too-many-open-files](/cases/t-too-many-open-files) |
| 2023-12-05 | swap 占用高与 swappiness 调优 | 中 | swap, 内存, swappiness | [t-swap-high-usage](/cases/t-swap-high-usage) |
| 2022-06-18 | CPU 飙高与 load average 定位 | 高 | CPU, top, pidstat | [t-cpu-high-load](/cases/t-cpu-high-load) |
| 2021-08-25 | 内存泄漏与 OOM Killer | 高 | OOM, 内存泄漏, JVM | [t-memory-leak-oom](/cases/t-memory-leak-oom) |
| 2023-02-19 | 进程 D 状态不可中断假死 | 高 | D状态, NFS, IO等待 | [t-process-d-state-hang](/cases/t-process-d-state-hang) |
:::

### 网络

::: details 网络（8 篇）
| 日期 | 标题 | 难度 | 标签 | 链接 |
|---|---|---|---|---|
| 2022-08-30 | DNS 解析失败 | 初 | DNS, dig, resolv.conf | [t-dns-resolution-fail](/cases/t-dns-resolution-fail) |
| 2020-03-17 | Connection refused 端口不通 | 初 | 端口, ss, refused | [t-port-connection-refused](/cases/t-port-connection-refused) |
| 2024-04-08 | HTTPS 证书过期/链不全 | 初 | TLS, 证书, openssl | [t-tls-cert-expired](/cases/t-tls-cert-expired) |
| 2021-05-11 | 网络不通/丢包/高延迟 | 中 | mtr, ping, 丢包 | [t-net-unreachable-mtr](/cases/t-net-unreachable-mtr) |
| 2021-11-09 | 连接超时与防火墙 | 中 | 防火墙, 安全组, iptables | [t-connection-timeout-firewall](/cases/t-connection-timeout-firewall) |
| 2023-09-16 | 负载均衡后端被健康检查摘除 | 中 | 负载均衡, 健康检查, Nginx | [t-lb-backend-ejected](/cases/t-lb-backend-ejected) |
| 2023-07-21 | TCP 重传率高 | 高 | TCP, 重传, 网卡 | [t-tcp-retransmission](/cases/t-tcp-retransmission) |
| 2022-01-14 | MTU 黑洞与 MSS 不匹配 | 高 | MTU, MSS, VPN | [t-mtu-black-hole](/cases/t-mtu-black-hole) |
:::

### 服务

::: details 服务（5 篇）
| 日期 | 标题 | 难度 | 标签 | 链接 |
|---|---|---|---|---|
| 2022-12-11 | Nginx 502 Bad Gateway | 中 | Nginx, 502, upstream | [t-nginx-502](/cases/t-nginx-502) |
| 2023-06-24 | Nginx 504 Gateway Timeout | 中 | Nginx, 504, 超时 | [t-nginx-504-timeout](/cases/t-nginx-504-timeout) |
| 2021-10-19 | PHP-FPM 进程池打满 502 | 中 | PHP-FPM, max_children | [t-phpfpm-502](/cases/t-phpfpm-502) |
| 2019-06-28 | NFS Stale file handle | 中 | NFS, 挂载, stale | [t-nfs-stale-handle](/cases/t-nfs-stale-handle) |
| 2020-08-07 | Tomcat 内存溢出/崩溃 | 高 | Tomcat, OOM, JVM | [t-tomcat-oom-crash](/cases/t-tomcat-oom-crash) |
:::

### MySQL

::: details MySQL（5 篇）
| 日期 | 标题 | 难度 | 标签 | 链接 |
|---|---|---|---|---|
| 2023-04-19 | 连接数打满 Too many connections | 初 | 连接数, 连接池, wait_timeout | [t-mysql-too-many-connections](/cases/t-mysql-too-many-connections) |
| 2022-06-14 | 主从复制延迟排查 | 中 | 主从复制, 并行复制, 大事务 | [t-mysql-replica-lag](/cases/t-mysql-replica-lag) |
| 2020-09-22 | 慢查询与索引失效 | 中 | 慢查询, EXPLAIN, 联合索引 | [t-mysql-slow-query](/cases/t-mysql-slow-query) |
| 2021-11-08 | InnoDB 死锁排查 | 高 | 死锁, 间隙锁, RR隔离级 | [t-mysql-deadlock](/cases/t-mysql-deadlock) |
| 2022-12-05 | 实例无法启动 | 高 | innodb_force_recovery, 崩溃恢复, 数据损坏 | [t-mysql-cannot-start](/cases/t-mysql-cannot-start) |
:::

### Redis

::: details Redis（3 篇）
| 日期 | 标题 | 难度 | 标签 | 链接 |
|---|---|---|---|---|
| 2023-08-11 | 内存打满 OOM | 中 | OOM, maxmemory, 淘汰策略, bigkey | [t-redis-memory-oom](/cases/t-redis-memory-oom) |
| 2024-03-20 | 缓存穿透/击穿/雪崩 | 中 | 缓存击穿, 布隆过滤器, 互斥锁 | [t-redis-cache-avalanche](/cases/t-redis-cache-avalanche) |
| 2023-10-16 | 哨兵故障切换/主从漂移 | 高 | 哨兵, 脑裂, fencing | [t-redis-sentinel-failover](/cases/t-redis-sentinel-failover) |
:::

### MQ / 集群

::: details MQ / 集群（2 篇）
| 日期 | 标题 | 难度 | 标签 | 链接 |
|---|---|---|---|---|
| 2024-05-28 | Kafka 消费积压 / Lag | 中 | consumer-lag, rebalance, 分区 | [t-kafka-consumer-lag](/cases/t-kafka-consumer-lag) |
| 2022-07-09 | 集群脑裂通用排查 | 高 | 脑裂, quorum, fencing | [t-cluster-split-brain](/cases/t-cluster-split-brain) |
:::

### Docker

::: details Docker（5 篇）
| 日期 | 标题 | 难度 | 标签 | 链接 |
|---|---|---|---|---|
| 2026-09-25 | swap 资源限制不生效 No swap limit support | 初 | docker, swap, cgroup | [t-docker-swap](/cases/t-docker-swap) |
| 2024-01-22 | 镜像拉取失败 | 初 | 镜像加速, imagePullSecrets, Harbor | [t-docker-image-pull-fail](/cases/t-docker-image-pull-fail) |
| 2021-05-17 | dockerd 启动失败 | 中 | dockerd, daemon.json, data-root | [t-docker-daemon-fail](/cases/t-docker-daemon-fail) |
| 2022-09-02 | 存储驱动 overlay2 与磁盘满 | 中 | overlay2, 磁盘满, prune | [t-docker-storage-driver](/cases/t-docker-storage-driver) |
| 2023-11-13 | 容器网络不通 | 中 | bridge, iptables FORWARD, DNS | [t-docker-network-bridge](/cases/t-docker-network-bridge) |
:::

### Kubernetes

::: details Kubernetes（8 篇）
| 日期 | 标题 | 难度 | 标签 | 链接 |
|---|---|---|---|---|
| 2023-07-25 | Pod 一直 Pending | 初 | Pending, 资源不足, PVC, 亲和 | [t-k8s-pod-pending](/cases/t-k8s-pod-pending) |
| 2024-04-08 | ImagePullBackOff | 初 | ImagePullBackOff, tag, imagePullSecrets | [t-k8s-imagepullbackoff](/cases/t-k8s-imagepullbackoff) |
| 2023-08-30 | CrashLoopBackOff | 中 | CrashLoopBackOff, liveness探针, 启动慢 | [t-k8s-crashloopbackoff](/cases/t-k8s-crashloopbackoff) |
| 2024-02-14 | 容器 OOMKilled | 中 | OOMKilled, limits, JVM堆 | [t-k8s-oomkilled](/cases/t-k8s-oomkilled) |
| 2025-05-21 | 集群证书过期 | 中 | kubeadm, certs, 证书续期 | [t-k8s-cert-expired](/cases/t-k8s-cert-expired) |
| 2025-01-15 | Service/Ingress 不通 | 高 | Service, Endpoints, kube-proxy, Ingress | [t-k8s-service-ingress](/cases/t-k8s-service-ingress) |
| 2025-03-10 | 节点 NotReady | 高 | NotReady, kubelet, 磁盘压力 | [t-k8s-node-notready](/cases/t-k8s-node-notready) |
| 2024-06-19 | etcd 故障/空间满/不一致 | 高 | etcd, defrag, quota, snapshot | [t-k8s-etcd-failure](/cases/t-k8s-etcd-failure) |
:::

### 安全

::: details 安全（3 篇）
| 日期 | 标题 | 难度 | 标签 | 链接 |
|---|---|---|---|---|
| 2023-09-05 | 服务器被植入挖矿木马 | 高 | 挖矿木马, SSH爆破, cron | [t-mining-trojan](/cases/t-mining-trojan) |
| 2024-07-22 | Web 站点 Webshell 排查处置 | 高 | Webshell, 上传漏洞, 溯源 | [t-webshell-investigation](/cases/t-webshell-investigation) |
| 2025-08-18 | 异常外联 / C2 回连 | 高 | C2, 外联, DNS隧道 | [t-malicious-c2-traffic](/cases/t-malicious-c2-traffic) |
:::

## 真实故障复盘模板

> 上面的案例是“训练场”；等以后真在工作中遇到影响业务的故障，我会用下面这个结构写完整复盘、放进「折腾」，对事不对人地总结根因和预防。
>
> 新建文件时复制以下结构：

```markdown
# 故障标题（YYYY-MM-DD）

## 一、现象
（用户/监控看到了什么，报错信息）

## 二、影响范围
（影响了哪些服务、多少用户、持续多久）

## 三、时间线
- HH:mm 发现 / 告警
- HH:mm 定位到……
- HH:mm 采取……措施
- HH:mm 恢复

## 四、定位过程
（用了哪些命令、看到什么、如何一步步缩小范围）

## 五、根因
（技术根因 + 流程/管理根因）

## 六、修复措施
（临时止血 + 彻底修复）

## 七、复盘与改进
（如何预防，需要补的监控、流程、文档，列出 Action Item 和负责人/时间）

## 八、相关命令速查
（链接到对应速查长文档）
```
