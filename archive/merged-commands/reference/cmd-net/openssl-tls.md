---
title: "OpenSSL 证书与 TLS 排查速查"
description: "本文是 网络命令速查 中「TLS 与证书」的详解。HTTPS 原理、证书签发流程见 Linux 安全指南。 官方文档：openssl s_client ｜ openssl x509 ｜ openssl verify"
---
# OpenSSL 证书与 TLS 排查速查

> 本文是 [网络命令速查](../network-commands#tls-与证书) 中「TLS 与证书」的详解。HTTPS 原理、证书签发流程见 [Linux 安全指南](/guide/linux-security)。
>
> 官方文档：[openssl s_client](https://docs.openssl.org/3.0/man1/openssl-s_client/) ｜ [openssl x509](https://docs.openssl.org/3.0/man1/openssl-x509/) ｜ [openssl verify](https://docs.openssl.org/3.0/man1/openssl-verify/)

## 一、一次握手，先看清证书链

```bash
openssl s_client -connect example.com:443 -servername example.com -showcerts </dev/null
```

关注输出里的关键行：

| 输出 | 含义 |
|---|---|
| `Verify return code: 0 (ok)` | 证书链校验通过 |
| `Verify return code: 10 (certificate has expired)` | 证书过期 |
| `Verify return code: 20 (unable to get local issuer certificate)` | 缺中间证书 |
| `Verify return code: 62 (hostname mismatch)` | 域名与证书 SAN 不匹配 |
| `Protocol : TLSv1.3` | 协商到的协议版本 |
| `Server certificate` 后的一串 `s:` / `i:` | Subject / Issuer |

## 二、只取证书关键信息

```bash
# 从远端直接取证书
openssl s_client -connect example.com:443 -servername example.com </dev/null 2>/dev/null \
  | openssl x509 -noout -subject -issuer -dates

# 看本地证书文件
openssl x509 -in cert.pem -noout -text          # 全量信息（含 SAN、Key Usage）
openssl x509 -in cert.pem -noout -dates         # notBefore / notAfter
openssl x509 -in cert.pem -noout -subject -issuer
openssl x509 -in cert.pem -noout -ext subjectAltName   # 证书覆盖哪些域名
```

到期时间脚本化检查：

```bash
exp=$(openssl x509 -in cert.pem -noout -enddate | cut -d= -f2)
echo "$exp"
date -d "$exp" +%s        # 转时间戳，便于和当前时间比较
```

## 三、校验证书链与主机名

```bash
# 用指定 CA 链校验
openssl verify -CAfile ca-bundle.pem cert.pem

# 校验主机名（OpenSSL 1.1+）
openssl verify -CAfile ca-bundle.pem -verify_hostname example.com cert.pem

# 抓取服务端完整链后本地校验
openssl s_client -connect example.com:443 -servername example.com -showcerts </dev/null \
  > /tmp/handshake.txt
```

> 生产最常见的问题不是“证书本身错”，而是**中间证书没配全**：浏览器能自动补链，`curl`、Java、Python 不一定，表现为部分客户端报 `unable to get local issuer certificate`。

## 四、协议、SNI 与 HTTP/2 探测

```bash
# 指定 TLS 版本（验证是否还开着重启不安全的旧协议）
openssl s_client -connect example.com:443 -servername example.com -tls1_2
openssl s_client -connect example.com:443 -servername example.com -tls1_3

# 看 ALPN 是否协商到 h2
openssl s_client -connect example.com:443 -servername example.com -alpn h2

# 只握手不发送 HTTP
openssl s_client -connect 10.0.0.10:443 -servername example.com -brief
```

## 五、HTTPS 端到端检查组合

```bash
curl -vI https://example.com                  # 看 DNS、连接、TLS、响应头
curl -kI https://example.com                  # 跳过校验（只用于判断服务是否活着）
curl --resolve example.com:443:203.0.113.10 https://example.com   # 绕过 DNS 直连指定 IP
openssl s_client -connect example.com:443 -servername example.com -brief </dev/null
```

判断顺序：DNS 能解析 → TCP 443 能连 → TLS 握手成功 → 证书校验通过 → HTTP 返回码正常。

## 六、常见报错与根因

| 现象 | 根因 | 处理 |
|---|---|---|
| `unable to get local issuer certificate` | 服务端没发中间证书，或客户端 CA 库旧 | 服务端补全 `ssl_certificate` 链；客户端更新 `ca-certificates` |
| `certificate has expired` | 证书过期 | 续签并 reload；检查定时续期任务 |
| `hostname mismatch` | 访问域名不在 SAN 里 | 证书补 SAN，或用正确域名访问 |
| `wrong version number` | 用 HTTPS 打了 HTTP 端口（或反之） | 确认端口与协议 |
| `sslv3 alert handshake failure` | 协议/加密套件不兼容 | 对齐客户端与服务端的 TLS 版本、cipher |
| `no peer certificate available` | 服务端没配证书或 SNI 未命中 | 检查虚拟主机证书配置 |
| `self-signed certificate` | 自签名证书 | 测试环境可 `-k`，生产换正式证书 |

## 七、官方文档与相关

- OpenSSL 官方文档：https://docs.openssl.org/3.0/
- s_client：https://docs.openssl.org/3.0/man1/openssl-s_client/
- x509：https://docs.openssl.org/3.0/man1/openssl-x509/
- verify：https://docs.openssl.org/3.0/man1/openssl-verify/
- CA/Browser 证书规范（了解 SAN、有效期要求）：https://cabforum.org/
- 速查页：[网络命令速查](../network-commands#tls-与证书)
- HTTP 测试：[curl](./curl)
- 证书过期排障案例：[TLS 证书过期](/cases/t-tls-cert-expired)
