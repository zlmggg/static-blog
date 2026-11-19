---
title: "openssl · 证书与加密排查"
description: "openssl 查证书有效期与域名、看 CSR/私钥、验证证书链、测 TLS 连接、生成自签证书、算哈希。HTTPS 排障必备，参数中文分级。"
---

# openssl · 证书与加密排查

> 命令手册 · [开发与效率](/commands/devtools/) ｜ 频率：偶尔用
> HTTPS 证书过期、域名不匹配、链不全、TLS 握手失败——都用 openssl 查。运维证书排障的主力。

## 一句话用途

看证书内容/有效期/域名、验证证书链、测 TLS 连接、生成密钥与自签证书。

## 高频场景速查

```bash
# 看远程站点证书有效期与域名
echo | openssl s_client -connect example.com:443 -servername example.com 2>/dev/null | openssl x509 -noout -dates -subject

# 看本地证书文件
openssl x509 -in cert.crt -noout -text          # 完整信息
openssl x509 -in cert.crt -noout -dates         # 有效期
openssl x509 -in cert.crt -noout -subject -ext subjectAltName   # 域名/SAN

# 验证证书与私钥是否配对（两个 modulus 哈希应一致）
openssl x509 -noout -modulus -in cert.crt | openssl md5
openssl rsa  -noout -modulus -in key.key  | openssl md5

# 测 TLS 握手
openssl s_client -connect example.com:443 -servername example.com
```

## 参数详解（按频率分级）

### 偶尔用

| 命令 | 含义 |
|---|---|
| `x509 -noout -dates` | 证书有效期 |
| `x509 -noout -text` | 证书全部字段 |
| `s_client -connect` | 测 TLS 连接/看证书链 |
| `-servername` | 指定 SNI（多域名必需） |
| `verify -CAfile ca.crt cert.crt` | 验证证书链 |
| `req -in csr.csr -noout -text` | 看 CSR 内容 |

### 很少用

| 命令 | 含义 |
|---|---|
| `req -x509 -newkey rsa:2048 -nodes -keyout k.key -out c.crt -days 365` | 生成自签证书 |
| `genrsa -out k.key 2048` | 生成 RSA 私钥 |
| `dgst -sha256 file` | 算文件哈希 |
| `s_client -tls1_2` | 指定 TLS 版本测试 |

::: tip 易错点
多域名站点测证书**必须带 `-servername`**（SNI），否则拿到默认证书误判。证书与私钥配对看 modulus 哈希是否一致。`-nodes` 表示私钥不加密（生产慎用）。
:::

## 运维实战

**证书快过期巡检**：`echo | openssl s_client -connect host:443 -servername host 2>/dev/null | openssl x509 -noout -enddate` 脚本批量跑，提前 30 天告警。
**浏览器报证书无效**：先 `s_client` 看链是否完整（缺中间证书最常见），再核对 SAN 是否含访问域名。

## 相关命令

[curl](/commands/network/curl) 测 HTTPS · [ssh-keygen](./ssh-keygen) · [Nginx HTTPS](/services/web/nginx/04-实战)

## 官方文档

- openssl：<https://docs.openssl.org/master/>
- x509：<https://docs.openssl.org/master/man1/openssl-x509/>