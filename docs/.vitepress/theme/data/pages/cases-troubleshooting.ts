import type { Article } from '../types'

const articles: Article[] = [
  // 系统启动
  { group: '系统启动', title: '开机进 GRUB rescue / 内核升级后起不来', sub: 'grub.cfg 仍指向已被删除的旧内核', tags: ['ls /boot/', 'grub2-mkconfig -o /boot/grub2/grub.cfg'], link: '/cases/t-grub-rescue-boot' },
  // CPU
  { group: 'CPU', title: 'CPU 飙高、load 高但业务不忙', sub: '死循环、全表扫描、自旋锁', tags: ['top -o %CPU', 'pidstat 1', 'perf top'], link: '/cases/t-cpu-high-load' },
  // 内存
  { group: '内存', title: '进程被 OOM Killer 杀、内存泄漏', sub: '无界缓存 / JVM 堆外泄漏', tags: ['dmesg | grep -i oom', 'free -h', 'jmap -heap'], link: '/cases/t-memory-leak-oom' },
  { group: '内存', title: 'swap 占用高、系统变慢', sub: '堆外泄漏 + swappiness 过高', tags: ['vmstat 1', 'cat /proc/sys/vm/swappiness'], link: '/cases/t-swap-high-usage' },
  // 磁盘与文件系统
  { group: '磁盘与文件系统', title: 'No space left 但 df 有空间', sub: '日志暴涨 / rm 后句柄未释放', tags: ['df -h', 'du -xh /', 'lsof +L1'], link: '/cases/t-disk-space-full' },
  { group: '磁盘与文件系统', title: 'No space left 但 df -h 空', sub: 'inode 被海量小文件吃光', tags: ['df -i', 'find / -xdev -type f | wc -l'], link: '/cases/t-inode-exhausted' },
  { group: '磁盘与文件系统', title: '掉电后分区变只读、挂载失败', sub: 'ext4 元数据不一致', tags: ['dmesg | grep -i ext4', 'mount -o remount,ro'], link: '/cases/t-filesystem-fsck-corrupt' },
  { group: '磁盘与文件系统', title: 'NFS 报 Stale file handle', sub: 'NFS 服务端重启，客户端句柄缓存失效', tags: ['showmount -e nfs-server', 'umount -lf'], link: '/cases/t-nfs-stale-handle' },
  // 权限
  { group: '权限', title: 'Permission denied 访问文件/站点', sub: '属主错误 / SELinux 上下文不对', tags: ['ls -l', 'id', 'getenforce', 'ls -Z'], link: '/cases/t-permission-ownership' },
  // 进程与 fd
  { group: '进程与 fd', title: 'Too many open files', sub: 'CLOSE_WAIT 泄漏打满单进程 fd', tags: ['ulimit -n', 'lsof -p <pid> | wc -l', 'ss -s'], link: '/cases/t-too-many-open-files' },
  { group: '进程与 fd', title: '进程 D 状态不响应、杀不掉', sub: 'NFS/磁盘 IO 硬等待', tags: ["ps -eo stat,pid,cmd | grep '^D'", 'cat /proc/<pid>/stack'], link: '/cases/t-process-d-state-hang' },
  // 网络连通性
  { group: '网络连通性', title: 'ping 不通 / 丢包 / 高延迟', sub: '上联拥塞、链路丢包', tags: ['mtr --tcp -P 80 <ip>', 'ping'], link: '/cases/t-net-unreachable-mtr' },
  { group: '网络连通性', title: '连接超时（不是 refused）', sub: '防火墙/安全组丢包', tags: ['iptables -L -n', 'tcpdump -i eth0 port 80', '安全组规则'], link: '/cases/t-connection-timeout-firewall' },
  // DNS
  { group: 'DNS', title: '域名解析超时/失败', sub: '防火墙挡 UDP53、resolv.conf 错', tags: ['dig @223.5.5.5 example.com', 'cat /etc/resolv.conf'], link: '/cases/t-dns-resolution-fail' },
  // 端口与连接
  { group: '端口与连接', title: 'Connection refused', sub: '服务没起 / 只监听 127.0.0.1', tags: ['ss -tlnp', 'lsof -i :80'], link: '/cases/t-port-connection-refused' },
  // TCP 与 MTU
  { group: 'TCP 与 MTU', title: 'TCP 重传率高、接口慢', sub: '光模块/网线 CRC 丢包', tags: ['nstat -az | grep retrans', 'ip -s link', 'ethtool'], link: '/cases/t-tcp-retransmission' },
  { group: 'TCP 与 MTU', title: '能 ping 但 TCP 握手后卡住', sub: '隧道 MTU 黑洞、MSS 不匹配', tags: ['tracepath', 'ip link', 'ping -M do -s 1472'], link: '/cases/t-mtu-black-hole' },
  // 证书与时间
  { group: '证书与时间', title: '浏览器报证书过期/链不全', sub: '续期脚本被删、中间证书漏配', tags: ['openssl s_client -connect x:443 -showcerts'], link: '/cases/t-tls-cert-expired' },
  { group: '证书与时间', title: 'TLS/JWT 鉴权突然失败', sub: '机器时差太大（>几分钟）', tags: ['timedatectl', 'chronyc tracking'], link: '/cases/t-clock-unsynced' },
  // Web 服务 502 / 504
  { group: 'Web 服务 502 / 504', title: 'Nginx 502 Bad Gateway', sub: 'upstream 挂/池满 RST', tags: ['nginx -t', 'tail /var/log/nginx/error.log', '看 upstream'], link: '/cases/t-nginx-502' },
  { group: 'Web 服务 502 / 504', title: 'Nginx 504 Gateway Timeout', sub: '后端慢 SQL 超 proxy_read_timeout', tags: ['看 upstream_response_time', '后端慢查询'], link: '/cases/t-nginx-504-timeout' },
  { group: 'Web 服务 502 / 504', title: 'PHP-FPM 502、池打满', sub: 'max_children 被慢请求占满', tags: ['pm.status_path', 'ps aux | grep php-fpm'], link: '/cases/t-phpfpm-502' },
  { group: 'Web 服务 502 / 504', title: 'Tomcat OOM/崩溃', sub: '全表导出撑爆堆', tags: ['jstat -gcutil', 'hs_err_pid*.log'], link: '/cases/t-tomcat-oom-crash' },
  { group: 'Web 服务 502 / 504', title: 'LB 后端被摘', sub: '健康检查超时（FullGC）', tags: ['LB 监控', '后端 GC 日志'], link: '/cases/t-lb-backend-ejected' },
  // MySQL
  { group: 'MySQL', title: 'Too many connections', sub: 'max_connections 小 + 连接池超时不匹配', tags: ['SHOW PROCESSLIST', "SHOW STATUS LIKE 'Threads_connected'"], link: '/cases/t-mysql-too-many-connections' },
  { group: 'MySQL', title: '从库数据慢半拍', sub: '大事务回放慢、并行复制退化', tags: ['SHOW REPLICA STATUS\\G', 'performance_schema.replication_applier_status_by_worker'], link: '/cases/t-mysql-replica-lag' },
  { group: 'MySQL', title: '查询越来越慢', sub: '缺联合索引、全表扫描', tags: ['EXPLAIN', 'mysqldumpslow'], link: '/cases/t-mysql-slow-query' },
  { group: 'MySQL', title: '死锁报错 1213', sub: '加锁顺序不一致 + 间隙锁', tags: ['SHOW ENGINE INNODB STATUS\\G', 'data_locks'], link: '/cases/t-mysql-deadlock' },
  { group: 'MySQL', title: '实例起不来', sub: '掉电致 InnoDB 页损坏', tags: ['mysqld 前台跑', 'error log'], link: '/cases/t-mysql-cannot-start' },
  // Redis
  { group: 'Redis', title: 'OOM command not allowed', sub: '大 key + 无 TTL 打满 maxmemory', tags: ['INFO memory', 'redis-cli --bigkeys'], link: '/cases/t-redis-memory-oom' },
  { group: 'Redis', title: 'DB 被打、命中率骤降', sub: '穿透/击穿/雪崩', tags: ['INFO stats', '--hotkeys'], link: '/cases/t-redis-cache-avalanche' },
  { group: 'Redis', title: '切换后双主/主从漂移', sub: '旧主未隔离、缺 fencing', tags: ['INFO replication', 'SENTINEL masters'], link: '/cases/t-redis-sentinel-failover' },
  // MQ / 集群
  { group: 'MQ / 集群', title: 'Kafka consumer lag 暴涨', sub: '消费慢触发 rebalance 停摆', tags: ['kafka-consumer-groups.sh --describe'], link: '/cases/t-kafka-consumer-lag' },
  { group: 'MQ / 集群', title: '集群出现双 leader', sub: '网络分区旧主未卸任', tags: ['各节点 /role', 'ZK 选主节点'], link: '/cases/t-cluster-split-brain' },
  // Docker
  { group: 'Docker', title: 'No swap limit support', sub: '内核未开 swapaccount', tags: ['docker info', '改 grub swapaccount=1'], link: '/cases/t-docker-swap' },
  { group: 'Docker', title: 'dockerd 起不来', sub: 'daemon.json 语法错/数据盘未挂', tags: ['dockerd 前台跑', 'python3 -m json.tool'], link: '/cases/t-docker-daemon-fail' },
  { group: 'Docker', title: '容器写满磁盘', sub: '悬空镜像/日志未轮转', tags: ['docker system df', 'docker system prune'], link: '/cases/t-docker-storage-driver' },
  { group: 'Docker', title: '容器间/出网不通', sub: 'FORWARD 默认 DROP、DNS', tags: ['iptables -L FORWARD', 'docker exec ... /etc/resolv.conf'], link: '/cases/t-docker-network-bridge' },
  { group: 'Docker', title: '镜像拉取失败', sub: '直连 Docker Hub 超时/未认证', tags: ['docker pull', 'crictl pull'], link: '/cases/t-docker-image-pull-fail' },
  // Kubernetes
  { group: 'Kubernetes', title: 'Pod 一直 Pending', sub: '资源不足/PVC 亲和/污点', tags: ['kubectl describe pod'], link: '/cases/t-k8s-pod-pending' },
  { group: 'Kubernetes', title: 'ImagePullBackOff', sub: 'tag 不存在/未配 pull secret', tags: ['kubectl describe pod Events'], link: '/cases/t-k8s-imagepullbackoff' },
  { group: 'Kubernetes', title: 'CrashLoopBackOff', sub: '探针误杀/启动命令错', tags: ['kubectl logs --previous', 'describe 看 Exit Code'], link: '/cases/t-k8s-crashloopbackoff' },
  { group: 'Kubernetes', title: '容器 OOMKilled(137)', sub: 'JVM 超 limits/内存泄漏', tags: ['kubectl describe pod', 'kubectl top pod'], link: '/cases/t-k8s-oomkilled' },
  { group: 'Kubernetes', title: 'Service/Ingress 不通', sub: 'selector 与 label 不一致', tags: ['kubectl get endpoints', 'kubectl describe ingress'], link: '/cases/t-k8s-service-ingress' },
  { group: 'Kubernetes', title: '节点 NotReady', sub: '磁盘满/kubelet/容器运行时', tags: ['kubectl describe node', 'journalctl -u kubelet'], link: '/cases/t-k8s-node-notready' },
  { group: 'Kubernetes', title: 'API 卡顿、etcd space exceeded', sub: 'etcd DB 达 quota', tags: ['etcdctl endpoint status', 'alarm list'], link: '/cases/t-k8s-etcd-failure' },
  { group: 'Kubernetes', title: 'x509 certificate has expired', sub: 'kubeadm 证书满 1 年', tags: ['kubeadm certs check-expiration'], link: '/cases/t-k8s-cert-expired' },
  // 安全
  { group: '安全', title: 'CPU 100%、/tmp 陌生二进制', sub: 'SSH 弱口令爆破后植入挖矿', tags: ['top', 'grep "Failed password" /var/log/auth.log', 'crontab -l'], link: '/cases/t-mining-trojan' },
  { group: '安全', title: 'Web 目录多了一句话木马', sub: 'CMS 上传漏洞', tags: ['find ... -newer', 'Nginx access log 溯源'], link: '/cases/t-webshell-investigation' },
  { group: '安全', title: '服务器周期性连境外 IP', sub: '被控回连 C2 / DNS 隧道', tags: ['ss -tunlp', 'lsof -i', 'tcpdump port 53'], link: '/cases/t-malicious-c2-traffic' },
]

export default articles
