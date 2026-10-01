# 排障记录

> 这里用**表格快速记录日常小问题和报错踩坑**：现象 → 关键词 → 解法。
> 一句话能说清的直接写表格；表格放不下的复杂排查，再单独开一篇短文（模板见底部）。
> 重大、影响业务的故障请写完整 [故障复盘](./)。

## 排障记录表

> 新记录加在表格最上面（倒序）。关键词尽量写全，方便以后 Ctrl+K 搜到。

| 日期 | 现象 / 报错 | 关键词 | 解法 |
|---|---|---|---|
| 2026-09-24 | SSH 连接很慢，要等十几秒 | ssh dns UseDNS 反向解析 | 改 `/etc/ssh/sshd_config` 设 `UseDNS no`，`systemctl restart sshd` |
| 2026-09-24 | df 显示有空间，但无法写入、提示 No space left | inode 满 小文件 | `df -i` 查 inode，清理海量小文件目录 |
| 2026-09-24 | 启动服务提示 Address already in use | 端口占用 | `ss -tunlp \| grep :80` 或 `lsof -i :80` 找到占用进程处理 |
| 2026-09-25 | 新装 Docker ，检查 docker info 提示 swap 相关报错 | docker swap | [详见短文](/cases/t-docker-swap) |
| 2026-09-26 | 容器长期运行后宿主机磁盘被写满，业务容器异常 | docker json-file 日志 未轮转 | `/etc/docker/daemon.json` 配置 `"log-opts": {"max-size": "100m", "max-file": "3"}`，重启 docker 后重建旧容器；临时用 `truncate -s 0` 清空大日志 |

## 排障方法大全

> 按方向分组：**症状 → 可能原因 → 关键命令 → 处置**。每条挂对应排障短文，点进去看完整过程。

::: details 系统启动
| 症状 | 可能原因 | 关键命令 | 处置 / 短文 |
|---|---|---|---|
| 开机进 GRUB rescue / 内核升级后起不来 | grub.cfg 仍指向已被删除的旧内核 | `ls /boot/`、`grub2-mkconfig -o /boot/grub2/grub.cfg` | 重新生成 grub.cfg / 修复内核 → [t-grub-rescue-boot](/cases/t-grub-rescue-boot) |
:::

::: details CPU
| 症状 | 可能原因 | 关键命令 | 处置 / 短文 |
|---|---|---|---|
| CPU 飙高、load 高但业务不忙 | 死循环、全表扫描、自旋锁 | `top -o %CPU`、`pidstat 1`、`perf top` | 定位高 CPU 线程再看栈 → [t-cpu-high-load](/cases/t-cpu-high-load) |
:::

::: details 内存
| 症状 | 可能原因 | 关键命令 | 处置 / 短文 |
|---|---|---|---|
| 进程被 OOM Killer 杀、内存泄漏 | 无界缓存 / JVM 堆外泄漏 | `dmesg \| grep -i oom`、`free -h`、`jmap -heap` | 查泄漏点、调堆参数 → [t-memory-leak-oom](/cases/t-memory-leak-oom) |
| swap 占用高、系统变慢 | 堆外泄漏 + swappiness 过高 | `vmstat 1`、`cat /proc/sys/vm/swappiness` | 调 `vm.swappiness=10`、治泄漏 → [t-swap-high-usage](/cases/t-swap-high-usage) |
:::

::: details 磁盘与文件系统
| 症状 | 可能原因 | 关键命令 | 处置 / 短文 |
|---|---|---|---|
| No space left 但 df 有空间 | 日志暴涨 / rm 后句柄未释放 | `df -h`、`du -xh /`、`lsof +L1` | 清大文件 / truncate 释放句柄 → [t-disk-space-full](/cases/t-disk-space-full) |
| No space left 但 df -h 空 | inode 被海量小文件吃光 | `df -i`、`find / -xdev -type f \| wc -l` | 清小文件目录 → [t-inode-exhausted](/cases/t-inode-exhausted) |
| 掉电后分区变只读、挂载失败 | ext4 元数据不一致 | `dmesg \| grep -i ext4`、`mount -o remount,ro` | 单用户下 `fsck -y` 修复 → [t-filesystem-fsck-corrupt](/cases/t-filesystem-fsck-corrupt) |
| NFS 报 Stale file handle | NFS 服务端重启，客户端句柄缓存失效 | `showmount -e nfs-server`、`umount -lf` | 强制卸载重挂 → [t-nfs-stale-handle](/cases/t-nfs-stale-handle) |
:::

::: details 权限
| 症状 | 可能原因 | 关键命令 | 处置 / 短文 |
|---|---|---|---|
| Permission denied 访问文件/站点 | 属主错误 / SELinux 上下文不对 | `ls -l`、`id`、`getenforce`、`ls -Z` | 改属主 / 还原 SELinux 上下文 → [t-permission-ownership](/cases/t-permission-ownership) |
:::

::: details 进程与 fd
| 症状 | 可能原因 | 关键命令 | 处置 / 短文 |
|---|---|---|---|
| Too many open files | CLOSE_WAIT 泄漏打满单进程 fd | `ulimit -n`、`lsof -p <pid> \| wc -l`、`ss -s` | 调 ulimit、修连接泄漏 → [t-too-many-open-files](/cases/t-too-many-open-files) |
| 进程 D 状态不响应、杀不掉 | NFS/磁盘 IO 硬等待 | `ps -eo stat,pid,cmd \| grep '^D'`、`cat /proc/<pid>/stack` | 恢复 NFS/IO，勿强杀 → [t-process-d-state-hang](/cases/t-process-d-state-hang) |
:::

::: details 网络连通性
| 症状 | 可能原因 | 关键命令 | 处置 / 短文 |
|---|---|---|---|
| ping 不通 / 丢包 / 高延迟 | 上联拥塞、链路丢包 | `mtr --tcp -P 80 <ip>`、`ping` | 逐跳定位丢包点 → [t-net-unreachable-mtr](/cases/t-net-unreachable-mtr) |
| 连接超时（不是 refused） | 防火墙/安全组丢包 | `iptables -L -n`、`tcpdump -i eth0 port 80`、安全组规则 | 放行入方向规则 → [t-connection-timeout-firewall](/cases/t-connection-timeout-firewall) |
:::

::: details DNS
| 症状 | 可能原因 | 关键命令 | 处置 / 短文 |
|---|---|---|---|
| 域名解析超时/失败 | 防火墙挡 UDP53、resolv.conf 错 | `dig @223.5.5.5 example.com`、`cat /etc/resolv.conf` | 放行 53 / 换 DNS → [t-dns-resolution-fail](/cases/t-dns-resolution-fail) |
:::

::: details 端口与连接
| 症状 | 可能原因 | 关键命令 | 处置 / 短文 |
|---|---|---|---|
| Connection refused | 服务没起 / 只监听 127.0.0.1 | `ss -tlnp`、`lsof -i :80` | 改监听 0.0.0.0 或起服务 → [t-port-connection-refused](/cases/t-port-connection-refused) |
:::

::: details TCP 与 MTU
| 症状 | 可能原因 | 关键命令 | 处置 / 短文 |
|---|---|---|---|
| TCP 重传率高、接口慢 | 光模块/网线 CRC 丢包 | `nstat -az \| grep retrans`、`ip -s link`、`ethtool` | 换光模块/网线 → [t-tcp-retransmission](/cases/t-tcp-retransmission) |
| 能 ping 但 TCP 握手后卡住 | 隧道 MTU 黑洞、MSS 不匹配 | `tracepath`、`ip link`、`ping -M do -s 1472` | 调 MSS clamp / MTU → [t-mtu-black-hole](/cases/t-mtu-black-hole) |
:::

::: details 证书与时间
| 症状 | 可能原因 | 关键命令 | 处置 / 短文 |
|---|---|---|---|
| 浏览器报证书过期/链不全 | 续期脚本被删、中间证书漏配 | `openssl s_client -connect x:443 -showcerts` | 重新签/补全链 → [t-tls-cert-expired](/cases/t-tls-cert-expired) |
| TLS/JWT 鉴权突然失败 | 机器时差太大（>几分钟） | `timedatectl`、`chronyc tracking` | 同步 NTP → [t-clock-unsynced](/cases/t-clock-unsynced) |
:::

::: details Web 服务 502 / 504
| 症状 | 可能原因 | 关键命令 | 处置 / 短文 |
|---|---|---|---|
| Nginx 502 Bad Gateway | upstream 挂/池满 RST | `nginx -t`、`tail /var/log/nginx/error.log`、看 upstream | 修后端 → [t-nginx-502](/cases/t-nginx-502) |
| Nginx 504 Gateway Timeout | 后端慢 SQL 超 proxy_read_timeout | 看 `upstream_response_time`、后端慢查询 | 优化慢查询/调超时 → [t-nginx-504-timeout](/cases/t-nginx-504-timeout) |
| PHP-FPM 502、池打满 | max_children 被慢请求占满 | `pm.status_path`、`ps aux \| grep php-fpm` | 提 max_children、治慢 SQL → [t-phpfpm-502](/cases/t-phpfpm-502) |
| Tomcat OOM/崩溃 | 全表导出撑爆堆 | `jstat -gcutil`、`hs_err_pid*.log` | 调堆/流式查 → [t-tomcat-oom-crash](/cases/t-tomcat-oom-crash) |
| LB 后端被摘 | 健康检查超时（FullGC） | LB 监控、后端 GC 日志 | 治 GC、放宽健康检查 → [t-lb-backend-ejected](/cases/t-lb-backend-ejected) |
:::

::: details MySQL
| 症状 | 可能原因 | 关键命令 | 处置 / 短文 |
|---|---|---|---|
| Too many connections | max_connections 小 + 连接池超时不匹配 | `SHOW PROCESSLIST`、`SHOW STATUS LIKE 'Threads_connected'` | 调大连接数、对齐池超时 → [t-mysql-too-many-connections](/cases/t-mysql-too-many-connections) |
| 从库数据慢半拍 | 大事务回放慢、并行复制退化 | `SHOW REPLICA STATUS\G`、`performance_schema.replication_applier_status_by_worker` | 开 WRITESET、分批大事务 → [t-mysql-replica-lag](/cases/t-mysql-replica-lag) |
| 查询越来越慢 | 缺联合索引、全表扫描 | `EXPLAIN`、`mysqldumpslow` | 建联合索引 → [t-mysql-slow-query](/cases/t-mysql-slow-query) |
| 死锁报错 1213 | 加锁顺序不一致 + 间隙锁 | `SHOW ENGINE INNODB STATUS\G`、`data_locks` | 统一加锁顺序/降隔离级 → [t-mysql-deadlock](/cases/t-mysql-deadlock) |
| 实例起不来 | 掉电致 InnoDB 页损坏 | `mysqld` 前台跑、error log | force_recovery 拉起后 dump 重建 → [t-mysql-cannot-start](/cases/t-mysql-cannot-start) |
:::

::: details Redis
| 症状 | 可能原因 | 关键命令 | 处置 / 短文 |
|---|---|---|---|
| OOM command not allowed | 大 key + 无 TTL 打满 maxmemory | `INFO memory`、`redis-cli --bigkeys` | 改淘汰策略、拆大 key → [t-redis-memory-oom](/cases/t-redis-memory-oom) |
| DB 被打、命中率骤降 | 穿透/击穿/雪崩 | `INFO stats`、`--hotkeys` | 布隆/互斥锁/随机过期 → [t-redis-cache-avalanche](/cases/t-redis-cache-avalanche) |
| 切换后双主/主从漂移 | 旧主未隔离、缺 fencing | `INFO replication`、`SENTINEL masters` | min-replicas-to-write + fencing → [t-redis-sentinel-failover](/cases/t-redis-sentinel-failover) |
:::

::: details MQ / 集群
| 症状 | 可能原因 | 关键命令 | 处置 / 短文 |
|---|---|---|---|
| Kafka consumer lag 暴涨 | 消费慢触发 rebalance 停摆 | `kafka-consumer-groups.sh --describe` | 异步化、调 poll 参数 → [t-kafka-consumer-lag](/cases/t-kafka-consumer-lag) |
| 集群出现双 leader | 网络分区旧主未卸任 | 各节点 `/role`、ZK 选主节点 | fencing + 断连即降级 → [t-cluster-split-brain](/cases/t-cluster-split-brain) |
:::

::: details Docker
| 症状 | 可能原因 | 关键命令 | 处置 / 短文 |
|---|---|---|---|
| No swap limit support | 内核未开 swapaccount | `docker info`、改 grub `swapaccount=1` | 加内核参数重启 → [t-docker-swap](/cases/t-docker-swap) |
| dockerd 起不来 | daemon.json 语法错/数据盘未挂 | `dockerd` 前台跑、`python3 -m json.tool` | 修配置/迁 data-root → [t-docker-daemon-fail](/cases/t-docker-daemon-fail) |
| 容器写满磁盘 | 悬空镜像/日志未轮转 | `docker system df`、`docker system prune` | 配 log-opts、定期 prune → [t-docker-storage-driver](/cases/t-docker-storage-driver) |
| 容器间/出网不通 | FORWARD 默认 DROP、DNS | `iptables -L FORWARD`、`docker exec ... /etc/resolv.conf` | 重启 docker 重建规则 → [t-docker-network-bridge](/cases/t-docker-network-bridge) |
| 镜像拉取失败 | 直连 Docker Hub 超时/未认证 | `docker pull`、`crictl pull` | 配加速器/Harbor 代理 → [t-docker-image-pull-fail](/cases/t-docker-image-pull-fail) |
:::

::: details Kubernetes
| 症状 | 可能原因 | 关键命令 | 处置 / 短文 |
|---|---|---|---|
| Pod 一直 Pending | 资源不足/PVC 亲和/污点 | `kubectl describe pod` | 扩节点/修亲和 → [t-k8s-pod-pending](/cases/t-k8s-pod-pending) |
| ImagePullBackOff | tag 不存在/未配 pull secret | `kubectl describe pod` Events | 修 tag/挂 imagePullSecrets → [t-k8s-imagepullbackoff](/cases/t-k8s-imagepullbackoff) |
| CrashLoopBackOff | 探针误杀/启动命令错 | `kubectl logs --previous`、describe 看 Exit Code | 配 startupProbe → [t-k8s-crashloopbackoff](/cases/t-k8s-crashloopbackoff) |
| 容器 OOMKilled(137) | JVM 超 limits/内存泄漏 | `kubectl describe pod`、`kubectl top pod` | 设 -Xmx、流式处理 → [t-k8s-oomkilled](/cases/t-k8s-oomkilled) |
| Service/Ingress 不通 | selector 与 label 不一致 | `kubectl get endpoints`、`kubectl describe ingress` | 修 selector → [t-k8s-service-ingress](/cases/t-k8s-service-ingress) |
| 节点 NotReady | 磁盘满/kubelet/容器运行时 | `kubectl describe node`、journalctl -u kubelet | 清磁盘重启 kubelet → [t-k8s-node-notready](/cases/t-k8s-node-notready) |
| API 卡顿、etcd space exceeded | etcd DB 达 quota | `etcdctl endpoint status`、`alarm list` | compact + defrag → [t-k8s-etcd-failure](/cases/t-k8s-etcd-failure) |
| x509 certificate has expired | kubeadm 证书满 1 年 | `kubeadm certs check-expiration` | `kubeadm certs renew all` → [t-k8s-cert-expired](/cases/t-k8s-cert-expired) |
:::

::: details 安全
| 症状 | 可能原因 | 关键命令 | 处置 / 短文 |
|---|---|---|---|
| CPU 100%、/tmp 陌生二进制 | SSH 弱口令爆破后植入挖矿 | `top`、`grep "Failed password" /var/log/auth.log`、`crontab -l` | 隔离清理、SSH 改密钥登录 → [t-mining-trojan](/cases/t-mining-trojan) |
| Web 目录多了一句话木马 | CMS 上传漏洞 | `find ... -newer`、Nginx access log 溯源 | 删 Webshell、uploads 禁 PHP → [t-webshell-investigation](/cases/t-webshell-investigation) |
| 服务器周期性连境外 IP | 被控回连 C2 / DNS 隧道 | `ss -tunlp`、`lsof -i`、`tcpdump port 53` | 出口封禁、隔离取证 → [t-malicious-c2-traffic](/cases/t-malicious-c2-traffic) |
:::

## 常见排障入口速查

- 进程 / 端口 / 文件占用：[Linux 命令速查](/reference/linux-commands)
- 网络不通 / DNS / 抓包：[网络命令速查](/reference/network-commands)
- 容器异常：[Docker 命令速查](/reference/docker-commands)
- K8s 异常：[kubectl 命令速查](/reference/kubectl-commands)
- 云原生/etcd/容器运行时：[云原生排障命令速查](/reference/cloudnative-commands)

## 排障短文模板（复杂问题用）

> 新建 `cases/t-简短标题.md`，复制以下结构：

```markdown
# 问题标题（YYYY-MM-DD）

## 现象（含完整报错信息）
## 环境（系统版本、相关软件版本）
## 定位过程（用了哪些命令、看到什么）
## 根因
## 解决步骤
## 相关命令（链接到速查长文档）
```
