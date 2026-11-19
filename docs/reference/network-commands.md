---
title: "网络命令速查"
description: "按网络排查流程聚合的命令速查：接口 → 端口 → 连通性 → 路由 → DNS → 抓包 → HTTP。 用法：右侧「本页目录」跳转，或 Ctrl+K 搜命令名。"
---
# 网络命令速查

> 按网络排查流程聚合的命令速查：接口 → 端口 → 连通性 → 路由 → DNS → 抓包 → HTTP。
> 用法：右侧「本页目录」跳转，或 `Ctrl+K` 搜命令名。

## 网络接口与 IP

| 命令 | 说明 | 示例 |
|---|---|---|
| [`ip addr`](/commands/network/ip-addr-link) | 查看接口和 IP 地址 | `ip a`；`ip a show eth0` |
| [`ip link`](/commands/network/ip-addr-link) | 查看/管理链路状态 | `ip link set eth0 up/down` |
| `ip route` | 查看路由表 | `ip r`；`ip route add default via 网关` |
| `nmcli` | NetworkManager 管理 | `nmcli device status`；`nmcli con show` |
| `ifconfig` | 旧版查看接口（net-tools） | `ifconfig` |
| `ethtool` | 查看网卡物理信息 | `ethtool eth0`（速率/双工） |
| `hostname` | 查看/设置主机名 | `hostnamectl set-hostname myblog` |

**配置 IP（RHEL vs Debian）：**

::: code-group

```bash [Debian/Ubuntu]
# /etc/network/interfaces 或 netplan（/etc/netplan/*.yaml）
sudo netplan apply
```

```bash [RHEL/CentOS]
# /etc/sysconfig/network-scripts/ifcfg-eth0
sudo systemctl restart network
```

:::

## 端口与连接

| 命令 | 说明 | 示例 |
|---|---|---|
| [`ss`](/commands/network/ss) | 查看端口/连接（推荐） | `ss -tunlp`（t TCP、u UDP、l 监听、n 数字、p 进程） |
| [`netstat`](/commands/network/ss) | 旧版查看端口 | `netstat -tunlp` |
| [`lsof -i`](/commands/observe/lsof) | 查端口占用 | `lsof -i :80` |
| `fuser` | 查端口占用进程 | `fuser -v 80/tcp` |

**ss 常用过滤：**

```bash
ss -t state established      # 已建立的TCP连接
ss -tn dst 192.168.1.10      # 到指定IP的连接
ss -s                        # 连接统计汇总
```

## 连通性测试

| 命令 | 说明 | 示例 |
|---|---|---|
| `ping` | ICMP 连通性/延迟 | `ping -c 4 host`（c 次数） |
| `nc` | netcat，端口连通/传输 | `nc -zv host 80`（z 扫描、v 详细） |
| `telnet` | 测试端口连通 | `telnet host 3306` |
| `nmap` | 端口扫描（需安装） | `nmap -p 1-1000 host`；`nmap -sP 网段` |

## 路由追踪

| 命令 | 说明 | 示例 |
|---|---|---|
| `traceroute` | 追踪数据包路径 | `traceroute host` |
| `mtr` | 结合 ping+traceroute，看每跳丢包 | `mtr -r host`（r 报告模式） |
| `tracepath` | 免 root 的路径追踪 | `tracepath host` |

## DNS 查询

> DNS 服务部署（BIND）见 [DNS 域名解析指南](/guide/services#合并资料)，这里是查询命令。

| 命令 | 说明 | 示例 |
|---|---|---|
| [`dig`](/commands/network/dig) | 强大的 DNS 查询工具 | 见下表 |
| [`nslookup`](/commands/network/dig) | 交互式 DNS 查询 | `nslookup domain` |
| [`host`](/commands/network/dig) | 简洁的 DNS 查询 | `host domain` |

**dig 常用：**

```bash
dig example.com                  # 查A记录（默认）
dig example.com MX               # 查MX邮件记录
dig example.com TXT              # 查TXT记录（如SPF）
dig example.com NS               # 查权威DNS
dig -x 8.8.8.8                   # 反向解析（PTR）
dig @8.8.8.8 example.com         # 指定DNS服务器查询
dig example.com +trace           # 从根开始追踪完整解析过程
dig example.com +short           # 只输出结果（简洁）
```

## 抓包

| 命令 | 说明 | 示例 |
|---|---|---|
| [`tcpdump`](/commands/network/tcpdump) | 命令行抓包分析 | 见下表 |

```bash
tcpdump -i eth0                  # 抓指定网卡
tcpdump -i any port 80           # 抓80端口
tcpdump host 192.168.1.10        # 抓与某主机的流量
tcpdump -nn -i eth0 tcp          # nn 不解析名字和端口（更快）
tcpdump -i eth0 -w cap.pcap      # 保存到文件（可用Wireshark打开）
tcpdump -r cap.pcap              # 读取抓包文件
tcpdump -A port 80               # A 以ASCII显示内容（看HTTP明文）
```

## HTTP 测试

| 命令 | 说明 | 示例 |
|---|---|---|
| [`curl`](/commands/network/curl) | 发送 HTTP 请求，测接口 | 见下表 |
| `wget` | 下载文件 | `wget https://x.com/f.tar.gz` |

```bash
curl https://example.com                 # GET请求，显示内容
curl -I https://example.com              # 只看响应头
curl -i https://example.com              # 响应头+内容
curl -o file https://example.com/f       # 保存到文件
curl -X POST -d "a=1&b=2" URL            # POST表单
curl -H "Content-Type: application/json" \
     -d '{"k":"v"}' URL                  # POST JSON
curl -x http://127.0.0.1:7890 URL        # 指定代理
curl -k https://host                     # 跳过证书校验（自签名）
curl -v https://example.com              # v 显示完整过程（排查用）
curl -w "%{http_code} %{time_total}s" -o /dev/null -s URL  # 只看状态码和耗时
```

## TLS 与证书

> HTTPS 连上了但证书报错、证书快到期、想确认链是否完整，看这一节。完整用法见 OpenSSL TLS 排查。

| 命令 | 说明 |
|---|---|
| `openssl s_client -connect 域名:443 -servername 域名` | 完成握手并打印证书链、协议版本 |
| `openssl s_client ... -showcerts` | 输出服务端发送的完整证书链 |
| `openssl x509 -in cert.pem -noout -dates` | 看证书有效期 |
| `openssl x509 -in cert.pem -noout -ext subjectAltName` | 看证书覆盖哪些域名 |
| `openssl verify -CAfile ca.pem cert.pem` | 校验证书链 |
| `openssl s_client ... -alpn h2` | 确认是否协商到 HTTP/2 |
| `certbot` | 申请/续期 Let's Encrypt 证书 | `certbot certonly --webroot -w /var/www/html -d example.com` |

## 流量监控

| 命令 | 说明 | 示例 |
|---|---|---|
| `iftop` | 实时显示各连接带宽 | `sudo iftop -i eth0` |
| `nethogs` | 按进程统计网络流量 | `sudo nethogs eth0` |
| `iperf3 -s` / `iperf3 -c 目标` | 主动压测链路吞吐（两端配合） | `iperf3 -c 10.0.0.12 -P 4 -t 30` |
| [`sar -n DEV`](/reference/linux-commands) | 网卡流量历史 | `sar -n DEV 1` |

## ARP 与邻居

| 命令 | 说明 | 示例 |
|---|---|---|
| `ip neigh` | 查看 ARP 邻居表 | `ip n` |
| `arp` | 旧版 ARP 表 | `arp -n` |
| `arping` | 同网段探测 IP 是否冲突 | `arping -I eth0 192.168.1.1` |

## 防火墙（速查）

> 完整 iptables 见 [iptables 防火墙指南](/guide/linux#合并资料)。

::: code-group

```bash [Debian ufw]
ufw allow 22/tcp        # 放行端口
ufw enable              # 启用
ufw status              # 查看规则
```

```bash [RHEL firewalld]
firewall-cmd --add-port=80/tcp --permanent   # 永久放行
firewall-cmd --reload                         # 重载生效
firewall-cmd --list-all                       # 查看
```

:::
> 防火墙命令从 0 到 1 详解：[iptables](/commands/network/iptables) ｜ nftables ｜ firewalld 与 ufw

<!-- merged-command-pitfalls:start -->
## 命令坑点索引

> 原先逐条拆开的单命令详解已合并到本手册；下面只保留每条命令最容易踩的坑，完整选项和示例不再单独成页。
> 需要看某条命令的完整用法时，先在上方速查表找到它，再看本节对应行。

| 命令 | 最容易踩的坑 | 官方文档 |
|---|---|---|
| `certbot` | 域名没解析到本机，或解析到了 CDN/WAF； | [官方](https://eff-certbot.readthedocs.io/en/stable/) |
| `firewalld 与 ufw` | 远程先放行 SSH 再 enable：这是 ufw/firewalld 最常见的把自己锁门外事故。 | [官方](https://firewalld.org/documentation/) |
| `iftop、nethogs 与 nload` | 都要 root：普通用户看不到流量，前面加 sudo。 | [官方](https://man7.org/linux/man-pages/man8/iftop.8.html) |
| `ip neigh 与 arp` | 邻居表里没有 ≠ 不通：没流量时表是空的，发个包就会自动 ARP 填进来。 | [官方](https://man7.org/linux/man-pages/man8/ip-neighbour.8.html) |
| `ip route` | 没有默认路由就上不了外网：内网互通正常但公网不通，十有八九缺 default。 | [官方](https://man7.org/linux/man-pages/man8/ip-route.8.html) |
| `iperf3 带宽测试速查` | 两端时间不同步不影响 iperf3 结果，但看日志时间要对时。 | — |
| `nc 与 telnet` | nc -zv 没加 -v 就没输出：只探测不打印结果，会以为命令卡死了。 | [官方](https://man7.org/linux/man-pages/man1/nc.1.html) |
| `nftables` | 语句要包单引号：nft 语法里有 ;、{}，不包引号会被 shell 拆开报错。 | — |
| `OpenSSL 证书与 TLS 排查速查` | 原页没有独立坑点段，待补。 | — |
| `ping` | 裸 ping 会一直跑：服务器上务必带 -c N，否则靠 Ctrl+C 停，忘了就一直在刷。 | [官方](https://man7.org/linux/man-pages/man8/ping.8.html) |
| `traceroute、mtr 与 tracepath` | 中间跳 * * * 不一定是故障：很多路由器被配置为不回 ICMP 超时包，链路其实是通的。 | — |
| `wget` | -c 才是续传：不加 -c 重下会覆盖或报错，大文件务必 -c。 | [官方](https://www.gnu.org/software/wget/manual/wget.html) |

<!-- merged-command-pitfalls:end -->

## 相关问答

- DNS、端口、抓包与网站打不开：[网络与连通性问题](/guide/linux-network#常见问题-faq)

## 官方文档

- iproute2（ip/ss）：https://man7.org/linux/man-pages/man8/ip.8.html
- dig（BIND 工具）：https://bind9.readthedocs.io/en/latest/reference.html
- tcpdump：https://www.tcpdump.org/manpages/
- curl：https://curl.se/docs/
- OpenSSL：https://docs.openssl.org/3.0/
- iperf3：https://software.es.net/iperf/
- nftables wiki：https://wiki.nftables.org/
- firewalld：https://firewalld.org/documentation/
