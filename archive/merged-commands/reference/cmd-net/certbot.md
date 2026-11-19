---
title: "certbot 命令详解：Let's Encrypt 证书申请与自动续期"
description: "本文是 网络命令速查 中 TLS 证书的补充；certbot 是 EFF 维护的 ACME 客户端，用 Let's Encrypt 免费证书把 HTTP 站点切成 HTTPS，并自动续期。 目标：知道 webroot、standalone、nginx 三种申请方式的区别，能把续期接进 systemd…"
---
# certbot 命令详解：Let's Encrypt 证书申请与自动续期

> 本文是 [网络命令速查](../network-commands#tls-与证书) 中 TLS 证书的补充；`certbot` 是 EFF 维护的 ACME 客户端，用 Let's Encrypt 免费证书把 HTTP 站点切成 HTTPS，并自动续期。
> 目标：知道 webroot、standalone、nginx 三种申请方式的区别，能把续期接进 systemd timer 或 cron，续期后自动 reload Nginx。

## 一、先搞清楚三件事

1. **证书是给域名签的，不是给 IP 签的**：Let's Encrypt 不签纯 IP 证书；域名必须能解析到这台机器。
2. **HTTP-01 校验要 80 端口可达**：ACME 服务器会访问 `http://域名/.well-known/acme-challenge/...`；如果 80 被封，只能用 DNS-01。
3. **通配符证书必须用 DNS-01**：`*.example.com` 不能走 HTTP-01，需要在 DNS 里加 TXT 记录。

## 二、安装

```bash
# RHEL / Rocky / CentOS
sudo dnf install -y certbot python3-certbot-nginx

# Debian / Ubuntu
sudo apt update && sudo apt install -y certbot python3-certbot-nginx
```

只用 webroot 或 standalone 时，`python3-certbot-nginx` 可以不装；要让 certbot 自动改 Nginx 配置就装它。

## 三、三种申请方式

### 1. webroot：网站已经在跑 Nginx/Apache

适合生产站点，不需要停服务。给 certbot 一个可写的 webroot 目录，它会在下面放校验文件：

```bash
sudo certbot certonly --webroot \
  -w /var/www/html \
  -d example.com -d www.example.com
```

Nginx 里要保证 `/.well-known/acme-challenge/` 能直接映射到 `-w` 指定的目录，例如：

```nginx
location ^~ /.well-known/acme-challenge/ {
    root /var/www/html;
    default_type "text/plain";
}
```

如果站点是容器化的，`-w` 要指向容器内实际挂载的目录，或者把校验目录单独挂出来。

### 2. standalone：机器上没有 Web 服务

certbot 自己起一个临时 HTTP 服务占用 80 端口：

```bash
sudo certbot certonly --standalone -d example.com
```

申请期间 80 端口不能有 Nginx/Apache 占着，否则会冲突。申请完再启动 Web 服务。

### 3. nginx 插件：让 certbot 自动改配置

```bash
sudo certbot --nginx -d example.com -d www.example.com
```

它会申请证书、修改 Nginx 配置、加 443 监听和跳转。适合新站快速上线；生产上如果配置是模板化管理的，建议用 `certonly` 只拿证书，配置自己改，避免 certbot 改乱模板。

### 4. DNS-01：通配符或 80 不可达

```bash
sudo certbot certonly --manual --preferred-challenges dns \
  -d example.com -d '*.example.com'
```

按提示在 DNS 加 TXT 记录，等待生效。手动模式不适合自动续期；生产要用 DNS 插件（如 `certbot-dns-aliyun`、`certbot-dns-cloudflare`）把凭据配置好。

## 四、证书放在哪

默认目录：

```text
/etc/letsencrypt/live/example.com/
├── cert.pem        # 站点证书
├── chain.pem       # 中间证书
├── fullchain.pem   # cert + chain，Nginx 用这个
└── privkey.pem     # 私钥，权限 600
```

Nginx 配置：

```nginx
server {
    listen 443 ssl;
    server_name example.com www.example.com;

    ssl_certificate     /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;
    # 其余 HSTS、session cache 等按站点策略加
}
```

`fullchain.pem` 必须包含中间证书，否则部分客户端会报链不完整。

## 五、自动续期

Let's Encrypt 证书有效期 90 天，certbot 默认在到期前 30 天续期。先演练：

```bash
sudo certbot renew --dry-run
```

确认没问题后，让 systemd timer 或 cron 定期跑：

```bash
# 手动续期（只续快到期的）
sudo certbot renew --quiet

# 续期成功后 reload Nginx
sudo certbot renew --quiet --deploy-hook "systemctl reload nginx"
```

大多数发行版的 certbot 包自带 `certbot-renew.timer`：

```bash
systemctl list-timers | grep certbot
systemctl status certbot-renew.timer
```

如果没有 timer，可以加 cron（每天跑两次，certbot 自己判断是否需要续）：

```cron
0 3,15 * * * root certbot renew --quiet --deploy-hook "systemctl reload nginx"
```

`--deploy-hook` 会写进 `/etc/letsencrypt/renewal/example.com.conf`，之后每次续期成功都会执行；改 hook 要改这个文件或重新申请时带上参数。

## 六、查看、吊销和删除

```bash
# 列出本机所有证书、到期时间、关联域名
sudo certbot certificates

# 吊销证书
sudo certbot revoke --cert-path /etc/letsencrypt/live/example.com/cert.pem

# 删除某个证书及其续期配置
sudo certbot delete --cert-name example.com
```

`delete` 不会自动改 Nginx 配置；删证书前先把站点切到别的证书或下线，否则 reload 会报找不到文件。

## 七、常见问题

### 1. `HTTP-01 challenge ... 404`

- 域名没解析到本机，或解析到了 CDN/WAF；
- 80 端口没放行；
- Nginx 的 `/.well-known/acme-challenge/` 被别的 location 截走；
- webroot 路径和 Nginx `root` 不一致。

先本地验证：

```bash
curl -I http://example.com/.well-known/acme-challenge/test
```

### 2. `Timeout during connect`

云安全组、防火墙、CDN 回源都可能挡 80；先 `ss -tlnp | grep :80` 确认本机在监听，再从外网 `curl`。

### 3. 续期成功但浏览器还是旧证书

证书文件换了，Nginx 没 reload；检查 `--deploy-hook` 是否执行：

```bash
systemctl status certbot-renew.timer
journalctl -u certbot-renew.service -n 50
```

### 4. 触发速率限制

Let's Encrypt 对同一注册域名有签发/重复证书限制。调试时加 `--staging` 用测试环境，不要反复申请生产证书：

```bash
sudo certbot certonly --staging --webroot -w /var/www/html -d example.com
```

测试证书不被浏览器信任，验证流程后删掉再申请生产证书。

### 5. 多域名和新域名

加域名用 `--expand` 或重新跑 `certonly` 带上全部 `-d`：

```bash
sudo certbot certonly --webroot -w /var/www/html \
  -d example.com -d www.example.com -d blog.example.com --expand
```

### 6. 权限问题

`/etc/letsencrypt/live` 和 `archive` 默认只有 root 可读；Nginx 以 root 启动后降权，通常能读；如果让非 root 进程读私钥，要单独做权限或证书分发，不要把 `privkey.pem` 改成全局可读。

## 八、最小上线流程

```bash
# 1. 确认域名解析和 80 可达
dig +short example.com
curl -I http://example.com/

# 2. 用 webroot 申请
sudo certbot certonly --webroot -w /var/www/html -d example.com -d www.example.com

# 3. 改 Nginx 配置，指向 fullchain.pem / privkey.pem
sudo nginx -t && sudo systemctl reload nginx

# 4. 演练续期
sudo certbot renew --dry-run

# 5. 确认 timer
systemctl list-timers | grep certbot
```

## 官方文档

- [Certbot 官方文档](https://eff-certbot.readthedocs.io/en/stable/)
- [Let's Encrypt 文档](https://letsencrypt.org/docs/)
