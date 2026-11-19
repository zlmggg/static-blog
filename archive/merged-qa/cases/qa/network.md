---
title: "网络与连通性问题"
description: "从 TCP/IP 基础到 DNS、端口、抓包和网站打不开。按“协议基础 → 部署接入 → 运行排障”的顺序阅读。 阅读方式：先看问题自己答一遍，再看「答」对照；按阶段顺序读，更容易把知识点串成业务链路。"
---
# 网络与连通性问题

> 从 TCP/IP 基础到 DNS、端口、抓包和网站打不开。按“协议基础 → 部署接入 → 运行排障”的顺序阅读。
>
> 阅读方式：先看问题自己答一遍，再看「答」对照；按阶段顺序读，更容易把知识点串成业务链路。

## 一、部署前：协议基础

### Q1：TCP 为什么三次握手、四次挥手？

**答：**

结论先说：三次握手是为了**双方都确认彼此的收发能力正常**，并同步初始序列号；四次挥手是因为 TCP 全双工，两个方向要各自关闭。

第一次，客户端发 `SYN`，带初始序号 `seq=x`，表示"我想连你，我的起始序号是 x"。第二次，服务端回 `SYN+ACK`，`ack=x+1`、`seq=y`，表示"我收到了，也同意连你，我的起始序号是 y"。第三次，客户端再发 `ACK`，`ack=y+1`，表示"我也收到你的序号了"。三次之后双方都知道对方能收能发。为什么不是两次？因为如果只有两次，历史重复的 SYN 会让服务端白等资源——第三次握手就是让服务端确认客户端此刻真的在线。

挥手要四次是因为全双工：主动方发 `FIN` 表示"我不发了"，被动方先回 `ACK`，但此时被动方可能还有数据要发，等它发完再发自己的 `FIN`，主动方再回 `ACK`。所以 FIN 和 ACK 不能合并，要分四次。

最后一个关键点：主动关闭方发完最后一个 ACK 后要进 `TIME_WAIT`，等 `2MSL`（最大报文生存时间的两倍）。原因是要保证最后一个 ACK 能到达对方（丢了对方会重发 FIN），同时让本次连接的所有旧报文在网络中消亡，避免影响下一条同四元组的连接。线上如果 `TIME_WAIT` 过多，可以开 `tcp_tw_reuse`，但不要轻易开 `tw_recycle`（NAT 场景会出问题）。

### Q2：TCP 和 UDP 区别及场景？

**答：**

结论：TCP 是面向连接、可靠、字节流的协议；UDP 是无连接、尽力而为、数据报的协议。

第一，TCP 面向连接，要先三次握手，断开要四次挥手；UDP 发数据前不需要握手，直接往 socket 里写就行，所以延迟低、开销小。

第二，TCP 保证可靠：有序列号、确认应答、超时重传、滑动窗口、拥塞控制（慢启动、拥塞避免、快重传、快恢复），数据按序到达、不丢不重。UDP 不保证，丢了就丢了、后发的可能先到，可靠性由应用层自己做。

第三，TCP 是字节流，没有报文边界，会粘包；UDP 是一条一条的数据报，有边界，发多大收多大。

第四，开销上 TCP 头部至少 20 字节，还要维护连接状态、拥塞窗口；UDP 头部只有 8 字节。

场景上：要求可靠传输的用 TCP，比如 HTTP/HTTPS、SSH、MySQL、Redis、文件下载、邮件；要求低延迟、能容忍少量丢包的用 UDP，比如 DNS 查询（53 端口）、视频会议、直播、游戏实时位置、QUIC/HTTP3、NTP。现在很多新场景（WebRTC、游戏）干脆在 UDP 上自己做一层可靠传输，就是为了既快又可控。

### Q3：HTTPS 加密过程？

**答：**

结论：HTTPS = HTTP + TLS，核心思想是**用非对称加密协商出一个对称密钥，之后全程对称加密**，再用证书证明服务器身份。

简化流程（TLS 1.2 为例）：第一，客户端 `Client Hello`，带上支持的 TLS 版本、加密套件列表、一个随机数 `client random`。第二，服务端 `Server Hello`，选定加密套件，给另一个随机数 `server random`，然后把自己的证书（含公钥、域名、有效期、CA 签名）一起发回来。第三，客户端验证证书：先看证书链能不能追溯到本机信任的根 CA，再看域名是否匹配、是否过期、有没有被吊销（CRL/OCSP）。验证通过后，客户端生成一个 `pre-master secret`，用服务器公钥加密发过去。第四，双方用 `client random + server random + pre-master secret` 各自算出会话密钥 `session key`。第五，之后所有业务数据都用这个对称密钥（AES-GCM 之类）加密传输。

TLS 1.3 把这个过程压缩到 1-RTT，甚至 0-RTT，握手更快，并且废弃了 RSA 密钥交换、固定用 ECDHE 前向 secrecy——意思是即使服务器私钥以后泄露，历史抓包也解不开，这就是前向安全。

为什么不全用非对称？因为非对称太慢，不适合传大量数据；为什么不全用对称？因为对称密钥怎么安全地交给对方是个死结。所以两者结合：非对称解决"密钥怎么安全传"，对称解决"数据怎么快加密"。

### Q4：常见 HTTP 状态码？

**答：**

结论：状态码分 5 类，3 位数字，第一位是大类。我按类背。

2xx 成功：`200 OK` 正常返回；`201 Created` 新建成功（POST）；`204 No Content` 成功但没返回体，常用于 DELETE。

3xx 重定向：`301 Moved Permanently` 永久重定向，浏览器会缓存，换域名、HTTP 跳 HTTPS 用；`302 Found` 临时重定向，每次都重新请求；`304 Not Modified` 协商缓存命中，浏览器带 `If-None-Match`/`If-Modified-Since`，服务器资源没变就回 304，浏览器用本地缓存。注意 301/302 历史上 POST 会被改成 GET，303/307/308 专门规范了这一点，307/308 保持方法不变。

4xx 客户端错误：`400 Bad Request` 请求参数/格式错；`401 Unauthorized` 没登录或 token 失效，要认证；`403 Forbidden` 认证了但没权限；`404 Not Found` 路由/资源不存在；`405 Method Not Allowed` 方法不对；`429 Too Many Requests` 触发限流。

5xx 服务端错误：`500 Internal Server Error` 后端代码抛异常；`502 Bad Gateway` 反向代理（Nginx）拿不到后端响应，后端挂了或端口不通；`503 Service Unavailable` 服务暂时不可用，一般是过载或维护；`504 Gateway Timeout` 代理等后端超时了。

实际排障最容易混淆的是 502 和 504 的区别：502 是"连都没连上/后端直接拒了"，504 是"连上了但后端处理太慢超时"。排查思路我在 Nginx 那题展开。

## 二、部署与接入：DNS 与端口

### Q5：DNS 解析过程？

**答：**

结论：浏览器输入域名后，DNS 查询走一个**多级缓存 + 递归迭代**的过程。

第一步，先查浏览器自身缓存（Chrome 有 1 分钟左右的 DNS 缓存），没命中再查操作系统缓存（`nscd`/`systemd-resolved`），再读 `/etc/hosts`。

第二步，还没命中就发请求给**本地递归 DNS**，也就是 `/etc/resolv.conf` 里配的那个（一般是运营商或 223.5.5.5、119.29.29.29）。这一步对客户端来说是**递归查询**——我要一个最终答案，你别让我再跑。

第三步，递归服务器自己开始**迭代查询**：先问根域名服务器（`.`，全球 13 组根），根说".com 的事你去找顶级域服务器"；再问 `.com` 顶级域，它说"`example.com` 去找它的权威 NS"；最后问权威服务器，拿到 A 记录 `1.2.3.4`。

第四步，递归服务器把结果缓存下来（按 TTL），返回给客户端，客户端也缓存一份。

常用记录类型：`A` 把域名转 IPv4；`AAAA` 转 IPv6；`CNAME` 别名，指向另一个域名；`MX` 邮件服务器；`NS` 指定该域的权威服务器；`TXT` 做 SPF/域名验证。

排查用 `dig example.com`，重点看 `ANSWER SECTION` 和 `Query time`；`dig +trace` 看完整迭代路径；`dig @8.8.8.8 example.com` 指定别的 DNS 服务器对比。线上域名突然解析错，第一件事就是 `dig` 对比本地和公共 DNS 的结果，再看是不是 TTL 没生效还是权威记录被改了。

### Q6：端口不通怎么排查？

**答：**

结论：端口不通按"**服务有没有监听 → 防火墙放没放行 → 包有没有到达 → 客户端连没连上**"四段查。

第一段，服务端看监听。`ss -tlnp | grep 8080`（或 `netstat -tlnp`），看这个端口有没有进程在 LISTEN，绑的是 `0.0.0.0` 还是 `127.0.0.1`——如果只绑本地回环，外部根本连不进来，要改成 `0.0.0.0` 或具体网卡 IP。没监听就去查服务为什么没起来：`systemctl status xxx`、`journalctl -u xxx -f`、看应用日志。

第二段，看防火墙。`iptables -L -n -v` 看 INPUT 链；`firewall-cmd --list-all`（firewalld）；`ufw status`（Ubuntu）。云服务器还要去控制台看安全组，很多人服务器内部防火墙关了但安全组没放行 8080。

第三段，确认包到底有没有到服务器。在服务端抓包：`tcpdump -i any port 8080 -nn`，然后从客户端 `nc -vz server_ip 8080`。如果抓包完全没看到 SYN 进来，说明包被中间网络/安全组拦了；如果看到 SYN 进来但没回 SYN+ACK，那是本机防火墙 DROP 了；如果 SYN+ACK 都回了但客户端说连不上，那是回程路由或 conntrack 问题。

第四段，客户端这边再确认：`telnet server_ip 8080`、`nc -vz server_ip 8080`、`curl -v telnet://server_ip:8080`。也可以在服务端本机先 `curl 127.0.0.1:8080` 自检，本地通外部不通，问题一定在网络路径/防火墙层。

容器场景还要加一步：`docker ps` 看端口映射 `-p 8080:80` 有没有写对，`docker inspect <容器>` 看实际映射到哪个宿主端口。

## 三、运行与排障：从现象到证据

### Q7：网站打不开如何系统排查？

**答：**

结论：从客户端到服务端**一层一层往下剥**，先定位是哪一层断了，再在那一层深挖，不要一上来就登服务器。

第一，先确认本机网络。`ping baidu.com` 看通不通；如果 ping 域名不通但 `ping 220.181.38.148` 通，那就是 DNS 问题，转第三层。如果连 IP 都不通，`ping 网关`、`ip route` 看默认路由，`ip addr` 看自己有没有拿到地址。

第二，测端口。`telnet example.com 443` 或 `nc -vz example.com 443`，TCP 三次握手能不能完成。不通就 `traceroute example.com` 或 `mtr --tcp --port 443 example.com` 看路径上哪一跳开始丢包。

第三，查 DNS。`dig example.com` 或 `nslookup example.com`，看返回的 A 记录对不对；`dig +trace example.com` 看递归到哪一步挂了。必要时换 `dig @223.5.5.5 example.com` 对比公共 DNS，判断是本地解析器问题还是权威记录问题。

第四，测应用层。`curl -I -v https://example.com`，看 TCP 连上没、TLS 握手成没、HTTP 状态码是多少。返回 502/504 说明已经到 Nginx 了，问题在后端；连接被拒说明后端服务没起。

第五，上服务端。先看服务自己：`ss -tlnp | grep 443` 确认在监听；`systemctl status nginx`、`docker ps` 看容器状态；`tail -f /var/log/nginx/error.log`。再看防火墙：`iptables -L -n`、`firewall-cmd --list-all`，云厂商还要看安全组。最后才上 `tcpdump -i eth0 port 443 -nn -w /tmp/web.pcap` 抓包回 Wireshark 分析。

一套下来基本能定位：本机→DNS→网络路径→端口→应用→服务端日志/防火墙。

### Q8：tcpdump 常用用法？

**答：**

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

## 延伸阅读

- [网络命令速查](/reference/network-commands)
- [Linux 网络专题](/guide/linux-network)
