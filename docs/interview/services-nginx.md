# Nginx 与 Web 服务

::: tip 本篇定位
覆盖 Nginx 架构、反向代理、负载均衡、location 和调优。
:::

## 高频面试题

### Q1：负载均衡算法？

**我的答案：**

结论：Nginx 原生 `upstream` 支持四种负载算法，第三方模块还能加两种，线上最常用的是轮询加权和 ip_hash。

第一，**轮询（round-robin）**，默认方式，按顺序一个一个分，谁也不多谁也不少。后端性能差不多时用它。

第二，**加权轮询（weight）**，`server 10.0.0.1:80 weight=3;`，weight 越大分到的请求越多。机器配置不一样就用权重，性能好的多分。

第三，**ip_hash**，对客户端 IP 做哈希固定分到某台后端。好处是同一会话一定打到同一台机器，解决 session 共享问题；缺点是某台挂了会有一批用户被重映射，而且 hash 不均时可能某台压力大。现在一般不用它做会话粘滞，而是用 Redis 集中存 session。

第四，**least_conn**，把请求发给当前活跃连接数最少的后端。长连接、请求处理时间差异大的场景比轮询合理。

第三方模块两种：`fair`（按后端响应时间分配，响应快的多分）、`url_hash`（按 URL 哈希，让相同 URL 打到同一台，提高缓存命中率），需要额外编译。

配合健康检查：`max_fails=3 fail_timeout=30s`，30 秒内失败 3 次就把这台后端摘 30 秒；`down` 标记下线；`backup` 标记备用机，其他都挂了才上。Nginx 原生只做被动健康检查（转发时才发现挂），主动健康检查要商业版或用 `nginx_upstream_check_module`。

---

### Q2：反向代理和正向代理区别？

**我的答案：**

结论：一句话——**正向代理代理的是客户端，反向代理代理的是服务端**。

正向代理：客户端不知道真正的服务器是谁，代理服务器帮客户端去请求。典型例子：翻墙/VPN、公司出口代理、APT 软件源代理。客户端要主动配置代理地址，服务端看到的是代理的 IP，不知道真实用户是谁。作用是翻墙、突破访问限制、缓存加速、隐藏客户端身份。

反向代理：服务端那一侧的代理，客户端根本不知道背后真正处理请求的是哪台机器，以为直接在跟代理说话。Nginx 就是最典型的反向代理。用户访问 `www.example.com`，DNS 解析到 Nginx，Nginx 再根据规则转给后面的 Tomcat/Node/PHP-FPM 集群。作用有四个：**负载均衡**（把请求分发到多台后端）、**SSL  termination**（证书只在 Nginx 配，后端走 HTTP）、**缓存静态资源**、**统一入口和安全防护**（隐藏后端拓扑、防恶意直接打后端）。

对比一下：正向代理服务客户端，帮客户端翻墙；反向代理服务服务端，帮后端扛流量。我们日常说 Nginx 做"反向代理+负载均衡"就是后者。配置上核心就一行 `proxy_pass http://backend;`，再配合 `proxy_set_header Host $host;`、`X-Real-IP`、`X-Forwarded-For` 把真实客户端信息透传给后端，不然后端日志里全是 Nginx 的 IP。

---

### Q3：location 匹配规则与优先级？

**我的答案：**

结论：Nginx location 匹配优先级从高到低是：**`=` > `^~` > 正则 `~`/`~*`（按配置顺序）> 普通前缀（最长匹配）**。

逐个解释：

- `location = /health`：精确匹配，只能是 `/health`，优先级最高，命中就立刻返回，不再往下找。常用于健康检查、首页。
- `location ^~ /static/`：前缀匹配，命中后**不再继续匹配正则**。长静态资源前缀常用，避免后面 `~ \.js$` 之类正则抢匹配。
- `location ~ \.php$`：正则匹配，区分大小写；`~*` 不区分大小写。多个正则按配置文件里的**从上到下**顺序，第一个命中就用。
- `location /api/`：普通前缀匹配，最长优先，但优先级低于上面三种。

举个例子，请求 `/static/app.js`：先看有没有 `=`，没有；再看 `^~ /static/` 命中了，直接用它，后面就算写了 `~ \.js$` 也不看了。如果没有 `^~`，就会继续往下匹配正则，命中 `~ \.js$` 用正则那条。

两个高频坑：第一，`proxy_pass` 末尾带不带斜杠差别巨大。带斜杠 `proxy_pass http://backend/;` 会把 location 匹配掉的部分替换掉；不带斜杠 `proxy_pass http://backend;` 会把完整 URI 拼上去。比如 `location /api/ { proxy_pass http://backend:8080/; }`，请求 `/api/user` 会变成 `http://backend:8080/user`；不带末尾斜杠就会变成 `http://backend:8080/api/user`。

第二，`try_files $uri $uri/ /index.html;` 是 SPA 前端神器，按顺序找文件，找不到最后回退到 index.html，交给前端路由处理。

---

### Q4：502/504 如何排查？

**我的答案：**

结论：502 是 Nginx 连不上后端，504 是连上了但后端超时，两者都要先在 Nginx 上看错误日志，再上后端那台查。

先看 Nginx 错误日志，最快：`tail -f /var/log/nginx/error.log`。502 一般会看到 `connect() failed (111: Connection refused) while connecting to upstream` 或 `upstream prematurely closed connection`；504 一般是 `upstream timed out (110: Connection timed out) while reading response header from upstream`。

**502 排查路径：**

1. 后端服务到底起没起？上后端机器 `ss -tlnp | grep 8080`，确认端口在监听；`systemctl status tomcat` / `docker ps` 看进程。
2. Nginx 能不能连到后端？在 Nginx 机器上 `curl -v http://10.0.0.5:8080/` 或 `telnet 10.0.0.5 8080`。连不上就查后端防火墙/安全组、Nginx 配置里 upstream 地址端口写对没。
3. 后端是不是崩了/重启中？看后端日志 `journalctl -u tomcat -f`、应用日志，有没有 OOM、OOM Killer 把进程杀了（`dmesg | tail`）。
4. 后端是不是把连接关了？后端处理完请求关连接比 Nginx 快，Keepalive 配置不一致也会 502，Nginx 侧加 `proxy_http_version 1.1; proxy_set_header Connection "";`。
5. 资源问题：后端 CPU/内存打满、连接数被打满（`ulimit -n`）。

**504 排查路径：**

1. 后端确实慢。看后端慢查询、慢接口日志、APM 链路追踪，找到那个耗时长的接口。
2. Nginx 超时配置太短。`proxy_connect_timeout` 默认 60s、`proxy_read_timeout` 60s，长接口要适当调大，但不能乱调大，不然慢请求占着 worker 不放。
3. 后端等 DB/外部服务卡住。上后端机器 `tcpdump -i any port 3306`、`ss -tnp` 看连接状态，`jstack`/`py-spy` 抓栈看卡在哪。
4. 网络问题：Nginx 到后端之间丢包、跨机房专线抖动，用 `mtr`、`tcptrace` 看。

一句话：502 先问"后端活着吗、Nginx 连得通吗"，504 先问"后端为什么这么慢"。

---

## 相关链接

- [相关文档](/guide/services-web-nginx)
