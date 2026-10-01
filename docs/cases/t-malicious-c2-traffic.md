---
category: 安全
difficulty: 高级
date: 2025-08-18
---

# 异常外联 / C2 回连排查（2025-08-18）

## 现象

出口防火墙告警：内网某台服务器在反复连接一个境外可疑 IP，且流量特征很怪（DNS 查询频率异常、小包周期性回连）。安全团队怀疑是主机已被控、在和 C2 服务器通信。

## 环境

| 组件 | 版本 |
|---|---|
| 操作系统 | Rocky Linux 9.4 |
| 可疑主机 | 10.0.5.31（一台业务内网服务器） |
| 告警来源 | 出口防火墙/IDS 检测到异常外联 |
| 可疑目标 | 45.155.xxx.xxx（境外，威胁情报标记为 C2） |

## 定位过程

### 1. 先确认这台机器到底在连谁

```bash
# 看当前所有外联连接
ss -tunlp
# 按外联目标聚合
ss -tnp state established | awk '{print $5}' | sort | uniq -c | sort -rn

# 看进程对应的连接
lsof -i -n -P | grep -v "127.0.0.1"
```

确认：有个进程 `xxxxx` 在周期性连 `45.155.xxx.xxx:443`。

### 2. 定位是哪个进程在连

```bash
# 从连接找进程 PID
ss -tunlp | grep 45.155.xxx.xxx
# 拿到 PID 后
ls -l /proc/<PID>/exe
cat /proc/<PID>/cmdline | tr '\0' ' '
```

### 3. DNS 隐蔽隧道检测

很多 C2 不用直接 IP 连接，而是走 **DNS 隧道**（把数据藏在 DNS 查询里），更隐蔽：

```bash
# 看异常 DNS 查询频率
tcpdump -i any port 50 -nn -c 100 | grep -v "正常域名"

# 看有没有大量查询随机子域的（dns 隧道特征）
# 例如 a1b2c3.random.xxx-domain.com 这种乱码子域
cat /etc/resolv.conf
# 临时挂抓包看 DNS
tcpdump -i any -nn port 53 -w /tmp/dns.pcap
```

异常特征：一个域名下短时间内大量随机字符串子域查询。

### 4. 查历史外联与持久化

```bash
# 看历史连接（netstat 不记历史，看防火墙/IDS 日志）
# 本机看定时任务、启动项是否有可疑回连
crontab -l
systemctl list-units --type=service --state=running

# 看最近新增的二进制
find /usr/local/bin /tmp /dev/shm -type f -mtime -7 -executable
```

## 根因

| 层级 | 说明 |
|---|---|
| 直接原因 | 主机被植入后门，周期性回连境外 C2 服务器接收指令/外带数据 |
| 入侵途径 | 往往是弱口令/漏洞进了内网后横向移动上来的 |

## 解决步骤

### 止血

1. **立刻在出口封禁该 C2 地址**（不要先在主机上杀进程，先断它和 C2 的通信）：

```bash
# 出口防火墙/上游封禁 45.155.xxx.xxx
iptables -A OUTPUT -d 45.155.xxx.xxx -j DROP
```

2. 隔离主机：把它从业务网络切到隔离 VLAN，避免横向扩散。

### 根治

1. 找到恶意进程并清除：

```bash
kill -9 <PID>
# 删对应二进制、启动项、定时任务
```

2. 取证：清除前先**保留证据**——抓 pcap、导出恶意样本、记录入侵时间线，便于溯源和上报：

```bash
# 抓现场样本
cp /proc/<PID>/exe /backup/suspect-sample-$(date +%F)
# 保留 pcap
tcpdump -i any -w /tmp/c2-evidence.pcap -c 1000
```

3. 排查入侵入口：这台机器怎么被打进来的？查 SSH 日志、Web 日志、最近的软件漏洞，从入口堵住，否则清完还会再被打进来（参考 [挖矿木马](/cases/t-mining-trojan)、[Webshell](/cases/t-webshell-investigation)）。

4. **原则：内网机器一旦确认被 C2 控制，最稳妥是备份数据后重装系统**，后门很难清干净。

## 验证与预防

```bash
# 封禁后不再有到该 C2 的连接
ss -tunlp | grep 45.155.xxx.xxx
# 出口监控无异常 DNS 隧道
```

- 监控：出口防火墙做外联白名单（业务服务器不该随便连境外）；异常 DNS 频率告警。
- 预防：最小化暴露面、定期漏扫、内网分段、EDR 部署。
- 应急：发现 C2 通信先封后杀，保留证据，重装优于手动清理。

## 相关

- 命令速查：[网络命令速查](/reference/network-commands) ｜ [Linux 命令速查](/reference/linux-commands)
- 同组短文：[挖矿木马清理](/cases/t-mining-trojan) ｜ [Webshell 排查处置](/cases/t-webshell-investigation)
