# 网络命令速查

> 按网络排查流程聚合的命令速查：接口 → 端口 → 连通性 → 路由 → DNS → 抓包 → HTTP。
> 用法：右侧「本页目录」跳转，或 `Ctrl+K` 搜命令名。

## 网络接口与 IP

| 命令 | 说明 | 示例 |
|---|---|---|
| [`ip addr`](./cmd-net/ip-addr-link) | 查看接口和 IP 地址 | `ip a`；`ip a show eth0` |
| [`ip link`](./cmd-net/ip-addr-link) | 查看/管理链路状态 | `ip link set eth0 up/down` |
| [`ip route`](./cmd-net/ip-route) | 查看路由表 | `ip r`；`ip route add default via 网关` |
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
| [`ss`](./cmd-net/ss) | 查看端口/连接（推荐） | `ss -tunlp`（t TCP、u UDP、l 监听、n 数字、p 进程） |
| [`netstat`](./cmd-net/ss) | 旧版查看端口 | `netstat -tunlp` |
| [`lsof -i`](./cmd/lsof) | 查端口占用 | `lsof -i :80` |
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
| [`ping`](./cmd-net/ping) | ICMP 连通性/延迟 | `ping -c 4 host`（c 次数） |
| [`nc`](./cmd-net/nc-telnet) | netcat，端口连通/传输 | `nc -zv host 80`（z 扫描、v 详细） |
| [`telnet`](./cmd-net/nc-telnet) | 测试端口连通 | `telnet host 3306` |
| `nmap` | 端口扫描（需安装） | `nmap -p 1-1000 host`；`nmap -sP 网段` |

## 路由追踪

| 命令 | 说明 | 示例 |
|---|---|---|
| [`traceroute`](./cmd-net/traceroute-mtr) | 追踪数据包路径 | `traceroute host` |
| [`mtr`](./cmd-net/traceroute-mtr) | 结合 ping+traceroute，看每跳丢包 | `mtr -r host`（r 报告模式） |
| [`tracepath`](./cmd-net/traceroute-mtr) | 免 root 的路径追踪 | `tracepath host` |

## DNS 查询

> DNS 服务部署（BIND）见 [DNS 域名解析指南](/guide/services-dns)，这里是查询命令。

| 命令 | 说明 | 示例 |
|---|---|---|
| [`dig`](./cmd-net/dig) | 强大的 DNS 查询工具 | 见下表 |
| [`nslookup`](./cmd-net/dig) | 交互式 DNS 查询 | `nslookup domain` |
| [`host`](./cmd-net/dig) | 简洁的 DNS 查询 | `host domain` |

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
| [`tcpdump`](./cmd-net/tcpdump) | 命令行抓包分析 | 见下表 |

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
| [`curl`](./cmd-net/curl) | 发送 HTTP 请求，测接口 | 见下表 |
| [`wget`](./cmd-net/wget) | 下载文件 | `wget https://x.com/f.tar.gz` |

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

## 流量监控

| 命令 | 说明 | 示例 |
|---|---|---|
| [`iftop`](./cmd-net/bandwidth) | 实时显示各连接带宽 | `sudo iftop -i eth0` |
| [`nethogs`](./cmd-net/bandwidth) | 按进程统计网络流量 | `sudo nethogs eth0` |
| [`sar -n DEV`](./cmd/mpstat-sar) | 网卡流量历史 | `sar -n DEV 1` |

## ARP 与邻居

| 命令 | 说明 | 示例 |
|---|---|---|
| [`ip neigh`](./cmd-net/ip-neigh-arp) | 查看 ARP 邻居表 | `ip n` |
| [`arp`](./cmd-net/ip-neigh-arp) | 旧版 ARP 表 | `arp -n` |
| `arping` | 同网段探测 IP 是否冲突 | `arping -I eth0 192.168.1.1` |

## 防火墙（速查）

> 完整 iptables 见 [iptables 防火墙指南](/guide/linux-security-iptables)。

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
> 防火墙命令从 0 到 1 详解：[iptables](./cmd-net/iptables) ｜ [nftables](./cmd-net/nftables) ｜ [firewalld 与 ufw](./cmd-net/firewalld-ufw)
