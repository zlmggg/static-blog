---
title: "whois · 域名与 IP 归属"
description: "whois 查域名注册信息/到期日、IP 归属 ASN/网段、注册商。排障溯源与资产核实，中文详解。"
---

# whois · 域名与 IP 归属

> 命令手册 · [网络](/commands/network/) ｜ 频率：很少用
> 这个域名谁注册的、何时到期？这个 IP 属于哪个运营商/机房？whois 查注册与归属信息。

## 一句话用途

查询域名注册信息与 IP 地址归属（ASN/网段/组织）。

## 高频场景速查

```bash
whois example.com                # 域名注册信息
whois example.com | grep -i 'expir'   # 看到期日
whois 8.8.8.8                    # IP 归属（ASN/组织/网段）
whois -h whois.arin.net 8.8.8.8  # 指定 whois 服务器
```

## 看什么

### 域名

- Registrar：注册商。
- Creation/Expiry Date：注册/到期日。
- Name Server：权威 DNS。
- Status：状态（clientTransferProhibited 等）。

### IP

- netname/org：归属组织。
- CIDR：网段。
- ASN：自治系统号。
- country：国家。

## 运维实战

**域名到期预警**：`whois 域名 | grep -i expiry` 脚本批量查，提前续费防中断。
**攻击 IP 溯源**：`whois 攻击IP` 看归属机房/运营商，投诉/封禁参考。
**核实 CDN/云厂商**：whois IP 确认是否属于预期云厂商网段。

::: tip 易错点
whois 信息可能被隐私保护遮蔽（注册人隐藏）。IP whois 按地区分配（APNIC/ARIN/RIPE），查不到换对应服务器。到期日以注册商为准。
:::

## 相关命令

[dig](./dig) · [nslookup/host](./nslookup-host) · [nmap](./nmap) · [DNS 服务](/services/web/dns)

## 官方文档

- whois：<https://man7.org/linux/man-pages/man1/whois.1.html>