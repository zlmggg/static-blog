---
title: "firewall-cmd · firewalld 防火墙"
description: "firewalld 区域/服务/端口管理、--permanent 持久化、rich rule 富规则、放行与拦截。RHEL 系默认防火墙，中文详解。"
---

# firewall-cmd · firewalld 防火墙

> 命令手册 · [网络](/commands/network/) ｜ 频率：偶尔用
> RHEL/Rocky 默认用 firewalld（不是直接 iptables）。按区域(zone)管规则，放行服务/端口用 firewall-cmd。

## 一句话用途

管理 firewalld 防火墙：放行/拦截端口与服务，按区域控制。

## 高频场景速查

```bash
sudo firewall-cmd --state                    # 运行状态
sudo firewall-cmd --list-all                 # 当前区域全部规则
sudo firewall-cmd --get-active-zones         # 活跃区域
sudo firewall-cmd --add-service=http --permanent        # 放行 http
sudo firewall-cmd --add-port=8080/tcp --permanent       # 放行端口
sudo firewall-cmd --remove-port=8080/tcp --permanent    # 移除
sudo firewall-cmd --reload                   # 重载使 permanent 生效
sudo firewall-cmd --add-service=https        # 临时放行（重启失效）
```

## 关键概念

- **zone（区域）**：信任级别（public/internal/trusted/drop），网卡绑定到区域。
- **--permanent**：写持久配置，**必须 --reload 才生效**；不加则临时（reload/重启失效）。
- **service vs port**：service 是预定义端口集（http=80），port 直接指定。

::: danger permanent 与 reload
`--add-port=... --permanent` 只是写配置，不 --reload 不生效。反过来不加 --permanent 立即生效但重启丢。生产两步：--permanent 加规则 + --reload。
:::

## 富规则（精细控制）

```bash
# 只允许某 IP 访问 3306
sudo firewall-cmd --permanent --add-rich-rule='rule family=ipv4 source address=10.0.0.5 port port=3306 protocol=tcp accept'
# 拒绝某网段
sudo firewall-cmd --permanent --add-rich-rule='rule family=ipv4 source address=192.168.1.0/24 drop'
sudo firewall-cmd --reload
```

## 运维实战

**部署后放行端口**：`--add-port=应用端口/tcp --permanent && --reload`。
**数据库只对内网**：rich rule 限定源 IP，不对公网开放 3306/6379。
**排"端口不通"**：先 `--list-all` 看放行没，再 [ss](./ss) 看监听没，再 [nc](./nc-socat-telnet) 测。

## 相关命令

[iptables](./iptables) · [nft](./nft) · [ufw](./ufw) · [ss](./ss) · [SELinux](/commands/identity/selinux)

## 官方文档

- firewalld：<https://firewalld.org/documentation/>
- firewall-cmd：<https://firewalld.org/documentation/man-pages/firewall-cmd.html>