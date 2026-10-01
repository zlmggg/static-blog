---
category: 网络
difficulty: 初级
date: 2024-04-08
---

# HTTPS 证书过期 / 链不全（2024-04-08）

## 现象

用户访问网站报浏览器警告：

```
NET::ERR_CERT_DATE_INVALID
Your connection is not private
Attackers might be trying to steal your information...
```

或者移动端 App 报错：

```
javax.net.ssl.SSLHandshakeException: Certificate expired
```

服务器上 `curl` 也报错：

```bash
curl -v https://api.example.com
# * SSL certificate problem: certificate has expired
# * Closing connection
# curl: (60) SSL certificate problem: certificate has expired
```

## 环境

- 服务器：Rocky Linux release 9.3 (Blue Onyx)，内核 `5.14.0-362.8.el9.x86_64`
- Web：Nginx 1.24.0
- 证书：Let's Encrypt 通配符证书，有效期 90 天

## 定位过程

### 1. 看证书有效期

```bash
openssl s_client -connect api.example.com:443 -servername api.example.com </dev/null 2>/dev/null | openssl x509 -noout -dates -subject -issuer
# notBefore=Jan  8 00:00:00 2024 GMT
# notAfter=Apr  8 23:59:59 2024 GMT
# subject=CN=*.example.com
# issuer=C=US,O=Let's Encrypt,CN=R3
```

今天是 2024-04-08，证书今天到期。

### 2. 看本机时间对不对

证书校验依赖本机时间，时间错了也会误报：

```bash
date
timedatectl
```

如果本机时间比实际慢，会报 `certificate is not yet valid`；快了会报过期。参考 [时间不同步](/cases/t-clock-unsynced)。

### 3. 看证书链全不全

浏览器/App 报 `unable to get local issuer certificate` 通常是链不全：

```bash
openssl s_client -connect api.example.com:443 -servername api.example.com </dev/null 2>&1 | grep -i "verify\|s:"
# Verify return code: 21 (unable to get local issuer certificate)
#  0 s:CN=*.example.com
#  1 s:CN=R3,O=Let's Encrypt
#  2 s:CN=ISRG Root X1
```

如果只看到 0 层（只有叶子证书），中间证书没配。

### 4. 看 Nginx 配置

```bash
grep -r "ssl_certificate" /etc/nginx/
# ssl_certificate     /etc/nginx/ssl/example.com.crt;
# ssl_certificate_key /etc/nginx/ssl/example.com.key;
```

确认 `.crt` 文件里包含了完整链（叶子 + 中间证书）。

```bash
openssl crl2pkcs7 -nocrl -certfile /etc/nginx/ssl/example.com.crt | openssl pkcs7 -print_certs -noout
# 应该看到 2~3 个证书（叶子 + 中间 + 根）
```

如果只有 1 个，就是链不全。

## 根因

Let's Encrypt 证书 90 天有效期，certbot 自动续期脚本上周被误删，证书到期没续。Nginx 还用着过期的证书，浏览器和 App 全部拒绝信任。

## 解决步骤

### 1. 临时止血：手动续期

如果是 Let's Encrypt：

```bash
# 先装 certbot
dnf install certbot python3-certbot-nginx

# 手动续期
certbot --nginx -d api.example.com
# 或
certbot renew --force-renewal

# 重载 nginx
nginx -t && systemctl reload nginx
```

验证：

```bash
openssl s_client -connect api.example.com:443 -servername api.example.com </dev/null 2>/dev/null | openssl x509 -noout -dates
# notAfter=Jul  7 23:59:59 2024 GMT  新的 90 天
```

### 2. 如果是自签/商业证书

替换证书文件：

```bash
# 备份旧证书
cp /etc/nginx/ssl/example.com.crt /etc/nginx/ssl/example.com.crt.bak

# 放新证书（PEM 格式，包含完整链）
vi /etc/nginx/ssl/example.com.crt
# 粘贴：叶子证书 + 中间证书

nginx -t && systemctl reload nginx
```

### 3. 确保证书链完整

Nginx 配置里 `ssl_certificate` 指向的文件必须是 **fullchain**（叶子+中间），不能只放叶子：

```
ssl_certificate     /etc/nginx/ssl/example.com.fullchain.pem;
ssl_certificate_key /etc/nginx/ssl/example.com.key;
```

Let's Encrypt 默认生成的就是 `fullchain.pem`，用那个。

### 4. 恢复自动续期

```bash
# 确认 cron 或 systemd timer
systemctl list-timers | grep certbot
# certbot.timer

# 手动跑一次续期（dry-run）
certbot renew --dry-run
```

## 验证与预防

- `openssl s_client` 返回 `Verify return code: 0 (ok)`。
- 浏览器访问不再有警告。
- 监控补：证书到期天数（提前 14 天告警）。
- 告警脚本示例：

```bash
#!/bin/bash
EXPIRY=$(echo | openssl s_client -connect api.example.com:443 -servername api.example.com 2>/dev/null | openssl x509 -noout -enddate | cut -d= -f2)
DAYS=$(( ( $(date -d "$EXPIRY" +%s) - $(date +%s) ) / 86400 ))
[ $DAYS -lt 14 ] && echo "证书 $DAYS 天后过期"
```

- 记住：**证书过期一定要提前监控，不要等用户报错才发现**。

## 相关

- 命令速查：[网络命令速查](/reference/network-commands)
- 时间方向：[时间不同步](/cases/t-clock-unsynced)
- 服务方向：[Nginx 502 Bad Gateway](/cases/t-nginx-502)
- 巡检清单：[运维巡检清单](/reference/ops-checklists)
