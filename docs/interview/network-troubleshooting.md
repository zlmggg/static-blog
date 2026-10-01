# 网络服务与排障

::: tip 本篇定位
覆盖 DNS、DHCP 和网络排障命令、抓包分析。
:::

## 高频面试题

### Q1：网站打不开如何系统排查？

**我的答案：**

结论：从客户端到服务端**一层一层往下剥**，先定位是哪一层断了，再在那一层深挖，不要一上来就登服务器。

第一，先确认本机网络。`ping baidu.com` 看通不通；如果 ping 域名不通但 `ping 220.181.38.148` 通，那就是 DNS 问题，转第三层。如果连 IP 都不通，`ping 网关`、`ip route` 看默认路由，`ip addr` 看自己有没有拿到地址。

第二，测端口。`telnet example.com 443` 或 `nc -vz example.com 443`，TCP 三次握手能不能完成。不通就 `traceroute example.com` 或 `mtr --tcp --port 443 example.com` 看路径上哪一跳开始丢包。

第三，查 DNS。`dig example.com` 或 `nslookup example.com`，看返回的 A 记录对不对；`dig +trace example.com` 看递归到哪一步挂了。必要时换 `dig @223.5.5.5 example.com` 对比公共 DNS，判断是本地解析器问题还是权威记录问题。

第四，测应用层。`curl -I -v https://example.com`，看 TCP 连上没、TLS 握手成没、HTTP 状态码是多少。返回 502/504 说明已经到 Nginx 了，问题在后端；连接被拒说明后端服务没起。

第五，上服务端。先看服务自己：`ss -tlnp | grep 443` 确认在监听；`systemctl status nginx`、`docker ps` 看容器状态；`tail -f /var/log/nginx/error.log`。再看防火墙：`iptables -L -n`、`firewall-cmd --list-all`，云厂商还要看安全组。最后才上 `tcpdump -i eth0 port 443 -nn -w /tmp/web.pcap` 抓包回 Wireshark 分析。

一套下来基本能定位：本机→DNS→网络路径→端口→应用→服务端日志/防火墙。

---

### Q2：DNS 解析过程？

**我的答案：**

结论：浏览器输入域名后，DNS 查询走一个**多级缓存 + 递归迭代**的过程。

第一步，先查浏览器自身缓存（Chrome 有 1 分钟左右的 DNS 缓存），没命中再查操作系统缓存（`nscd`/`systemd-resolved`），再读 `/etc/hosts`。

第二步，还没命中就发请求给**本地递归 DNS**，也就是 `/etc/resolv.conf` 里配的那个（一般是运营商或 223.5.5.5、119.29.29.29）。这一步对客户端来说是**递归查询**——我要一个最终答案，你别让我再跑。

第三步，递归服务器自己开始**迭代查询**：先问根域名服务器（`.`，全球 13 组根），根说".com 的事你去找顶级域服务器"；再问 `.com` 顶级域，它说"`example.com` 去找它的权威 NS"；最后问权威服务器，拿到 A 记录 `1.2.3.4`。

第四步，递归服务器把结果缓存下来（按 TTL），返回给客户端，客户端也缓存一份。

常用记录类型：`A` 把域名转 IPv4；`AAAA` 转 IPv6；`CNAME` 别名，指向另一个域名；`MX` 邮件服务器；`NS` 指定该域的权威服务器；`TXT` 做 SPF/域名验证。

排查用 `dig example.com`，重点看 `ANSWER SECTION` 和 `Query time`；`dig +trace` 看完整迭代路径；`dig @8.8.8.8 example.com` 指定别的 DNS 服务器对比。线上域名突然解析错，第一件事就是 `dig` 对比本地和公共 DNS 的结果，再看是不是 TTL 没生效还是权威记录被改了。

---

### Q3：端口不通怎么排查？

**我的答案：**

结论：端口不通按"**服务有没有监听 → 防火墙放没放行 → 包有没有到达 → 客户端连没连上**"四段查。

第一段，服务端看监听。`ss -tlnp | grep 8080`（或 `netstat -tlnp`），看这个端口有没有进程在 LISTEN，绑的是 `0.0.0.0` 还是 `127.0.0.1`——如果只绑本地回环，外部根本连不进来，要改成 `0.0.0.0` 或具体网卡 IP。没监听就去查服务为什么没起来：`systemctl status xxx`、`journalctl -u xxx -f`、看应用日志。

第二段，看防火墙。`iptables -L -n -v` 看 INPUT 链；`firewall-cmd --list-all`（firewalld）；`ufw status`（Ubuntu）。云服务器还要去控制台看安全组，很多人服务器内部防火墙关了但安全组没放行 8080。

第三段，确认包到底有没有到服务器。在服务端抓包：`tcpdump -i any port 8080 -nn`，然后从客户端 `nc -vz server_ip 8080`。如果抓包完全没看到 SYN 进来，说明包被中间网络/安全组拦了；如果看到 SYN 进来但没回 SYN+ACK，那是本机防火墙 DROP 了；如果 SYN+ACK 都回了但客户端说连不上，那是回程路由或 conntrack 问题。

第四段，客户端这边再确认：`telnet server_ip 8080`、`nc -vz server_ip 8080`、`curl -v telnet://server_ip:8080`。也可以在服务端本机先 `curl 127.0.0.1:8080` 自检，本地通外部不通，问题一定在网络路径/防火墙层。

容器场景还要加一步：`docker ps` 看端口映射 `-p 8080:80` 有没有写对，`docker inspect <容器>` 看实际映射到哪个宿主端口。

---

### Q4：tcpdump 常用用法？

**我的答案：**

结论：tcpdump 是命令行抓包神器，核心是"选对网卡、写对过滤表达式、存下来用 Wireshark 看"。

最常用的几个例子：

```bash
# 抓 eth0 上 80 端口的包，-n 不解析域名，-nn 连端口也不解析成服务名
tcpdump -i eth0 -nn port 80

# 只抓和某台主机的来往包
tcpdump -i any -nn host 1.2.3.4

# 组合：来自某主机、访问 22 端口
tcpdump -i eth0 -nn src host 192.168.1.10 and dst port 22

# 只抓 TCP 握手包（看 SYN/ACK）
tcpdump -i eth0 -nn 'tcp[tcpflags] & tcp-syn != 0'

# 存成文件，回头用 Wireshark 打开分析
tcpdump -i eth0 -nn -s 0 -w /tmp/web.pcap port 443

# 看文件内容
tcpdump -r /tmp/web.pcap -nn
```

几个关键参数：`-i any` 抓所有网卡；`-nn` 强烈建议加，不然慢还会把自己 DNS 打爆；`-s 0` 抓完整包（默认只抓前 68 字节）；`-c 100` 抓够 100 个就停；`-w` 存盘，`-r` 读回来。

过滤表达式用 BPF 语法，可以用 `and/or/not` 组合 `host/net/port/src/dst/protocol`。线上排查 502、端口不通、TLS 握手失败，最有效的办法就是在 Nginx 那台和后端那台同时抓包，对着看 SYN 到哪去了、RST 是谁发的。复杂协议解析交给 Wireshark：`tcp.analysis.retransmission`、`tcp.stream` 跟一条流，比肉眼看文本高效得多。

---

## 相关链接

- [相关文档](/reference/network-commands)
