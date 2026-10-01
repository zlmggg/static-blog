---
category: 容器
difficulty: 中级
date: 2023-11-13
---

# 容器网络不通排查（2023-11-13）

## 现象

新建的容器之间互相 ping 不通，容器也访问不了外网；但宿主机本身网络正常。宿主机上 `curl 容器IP:端口` 也不通。

```text
# 容器内
root@c1:/# ping 172.17.0.3
PING 172.17.0.3 ... (无响应)

# 容器内访问外网
root@c1:/# curl -I https://www.baidu.com
curl: (7) Failed to connect: No route to host
```

## 环境

| 组件 | 版本 |
|---|---|
| 操作系统 | Rocky Linux 9.2（内核 5.14） |
| Docker | 24.0.6 |
| 网络 | 默认 bridge 网络 `docker0`，网段 172.17.0.0/16 |
| 防火墙 | firewalld 开启 |

## 定位过程

### 1. 先看容器拿到 IP 没有、网卡在不在

```bash
# 容器列表与 IP
docker network inspect bridge
docker inspect <容器名> --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'
```

进入容器看网卡：

```bash
docker exec -it <容器> ip addr
# 应有 eth0: 172.17.0.x/16，且有默认路由
docker exec -it <容器> ip route
# default via 172.17.0.1
```

### 2. 分层排查：容器 → docker0 → 宿主机 → 外网

按这个顺序逐层 ping：

| 层级 | 命令 | 不通说明 |
|---|---|---|
| 容器内 ping 网关 | `ping 172.17.0.1` | 容器→docker0 不通，veth 对没插好 |
| 宿主机 ping 容器 | `ping 172.17.0.2` | docker0→容器 不通 |
| 容器 ping 宿主机外网 IP | `ping <宿主机eth0 IP>` | NAT/转发问题 |
| 容器 ping 公网 | `ping 223.5.5.5` | 转发/NAT 问题 |
| 容器 ping 域名 | `ping www.baidu.com` | DNS 问题 |

### 3. 最常见：iptables FORWARD 链被默认 DROP

Docker 依赖 iptables 的 FORWARD 链做容器间转发。很多系统（或防火墙脚本）会把 FORWARD 默认策略改成 DROP：

```bash
sudo iptables -L FORWARD -n -v | head
# 本次输出：Chain FORWARD (policy DROP)   <-- 默认 DROP！
```

Docker 自己会写 ACCEPT 规则，但如果被 firewalld/自定义脚本清空或覆盖，容器间就不通。

### 4. DNS 不通的单独排查

容器里能 ping IP 但 ping 不通域名，是 DNS 问题：

```bash
docker exec <容器> cat /etc/resolv.conf
# 容器默认用 docker 的 DNS（127.0.0.11 用于自定义网络）或宿主机的
docker exec <容器> nslookup www.baidu.com
```

### 5. 端口映射不通

宿主机 `curl localhost:8080` 访问不到容器：

```bash
# 看端口映射
docker ps --format "table {{.Names}}\t{{.Ports}}"
# 看宿主机端口监听
ss -tlnp | grep 8080
```

## 根因

| 层级 | 说明 |
|---|---|
| 直接原因 | 宿主机防火墙把 iptables FORWARD 默认策略改成 DROP，Docker 的容器转发规则被破坏 |
| 诱因 | 运维手动跑过 `iptables -P FORWARD DROP` 或 firewalld 重启后 Docker 规则未重建 |
| 次要 | 偶发 DNS：容器 /etc/resolv.conf 未正确下发 |

## 解决步骤

### 止血

1. 恢复 FORWARD 链放行 Docker 流量：

```bash
# 方法一：把 FORWARD 默认策略改回 ACCEPT（临时）
sudo iptables -P FORWARD ACCEPT

# 方法二：重启 docker，让它重建 nat/filter 规则（推荐）
sudo systemctl restart docker
```

2. 验证 firewalld 与 Docker 兼容：Rocky/CentOS 上建议：

```bash
# 让 firewalld 信任 docker 网卡
sudo firewall-cmd --permanent --zone=trusted --add-interface=docker0
sudo firewall-cmd --reload
```

### 根治

1. 不要手动改 FORWARD 默认策略。需要自定义防火墙规则时，用 Docker 支持的方式（如 `--icc`、自定义网络）。

2. DNS 问题修复：给容器显式配公共 DNS：

```bash
# /etc/docker/daemon.json
{
  "dns": ["223.5.5.5", "119.29.29.29"]
}
```

重启 docker 生效。

3. 容器间通信用**自定义 bridge 网络**而非默认 docker0（自定义网络内置 DNS 解析）：

```bash
docker network create mynet
docker run -d --net mynet --name web nginx
docker run -d --net mynet --name app myapp
# 同自定义网络内容器可以直接用容器名互访（DNS 解析）
```

## 验证与预防

```bash
# 容器间互通
docker exec c1 ping -c2 c2
# 容器出网
docker exec c1 curl -I https://www.baidu.com
# 端口映射
curl -I http://localhost:8080
```

- 规范：不要手动清空/改 iptables FORWARD；跨容器通信用自定义网络 + 容器名 DNS。
- 排查套路：分层 ping（网关→宿主机→公网 IP→域名），定位是 L2 转发还是 NAT 还是 DNS。

## 相关

- 命令速查：[Docker 命令速查](/reference/docker-commands) ｜ [网络命令速查](/reference/network-commands)
- 同组短文：[dockerd 启动失败](/cases/t-docker-daemon-fail) ｜ [存储驱动 overlay2](/cases/t-docker-storage-driver) ｜ [镜像拉取失败](/cases/t-docker-image-pull-fail)
