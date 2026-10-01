---
title: 安全加固
description: Linux 基础加固：账号策略、防火墙、SELinux、SSH 加固、SSL/TLS 证书、VPN、chrony 时间同步
category: Linux
difficulty: 中级
---
# 安全加固

::: tip 本篇定位
建立**纵深防御**的安全意识，掌握 Linux 基础加固：账号与密码策略、防火墙、**SELinux**、**SSH 加固**、SSL/TLS 证书、VPN 方案和 **chrony 时间同步**。
:::

## 一、安全加固总览

安全不是靠某一个"银弹"，而是**纵深防御（Defense in Depth）**——多层措施叠加，一层被突破还有下一层。

### 1.1 加固清单

| 方向 | 措施 |
|---|---|
| 最小化安装 | 只装必要的软件包，减少攻击面 |
| 收敛服务/端口 | 关闭不用的服务，只监听/开放必要端口 |
| 账号策略 | 最小权限、禁用无用账号、强密码策略、限制 sudo |
| 及时补丁 | 定期更新系统和软件，修复已知漏洞 |
| 防火墙 | 默认拒绝，只放行必要流量 |
| SSH 加固 | 密钥登录、禁 root、改端口 |
| 访问控制 | 启用 SELinux/AppArmor 等强制访问控制 |
| 加密传输 | 敏感服务用 HTTPS/TLS |
| 日志审计 | 开启日志、定期审查登录和异常 |
| 数据备份 | 可恢复是最后的安全底线 |

### 1.2 密码策略

```bash
# 密码复杂度（RHEL 用 pwquality，Debian 用 libpam-pwquality）
# /etc/security/pwquality.conf
minlen = 12            # 最小长度
dcredit = -1           # 至少 1 个数字
ucredit = -1           # 至少 1 个大写
lcredit = -1           # 至少 1 个小写
ocredit = -1           # 至少 1 个特殊字符

# 密码有效期 /etc/login.defs
PASS_MAX_DAYS   90     # 最长使用天数
PASS_MIN_DAYS   1
PASS_WARN_AGE   7
chage -l 用户名          # 查看某用户密码策略
```

### 1.3 补丁更新

```bash
# RHEL/Rocky
sudo dnf update --security     # 只更新安全补丁
# Debian/Ubuntu
sudo apt update && sudo apt upgrade
```

> 生产环境更新前先在测试环境验证，重要更新安排在业务低峰，并保留快照/回滚能力。

---

## 二、防火墙

防火墙在网络层做访问控制，原则是**默认拒绝、只放行必要流量**。

| 工具 | 发行版 | 说明 |
|---|---|---|
| iptables | 通用（传统） | 功能强大，规则较底层 |
| nftables | 通用（新一代） | iptables 的继任者，语法更统一 |
| firewalld | RHEL/CentOS/Rocky | 基于 zone 的动态管理，底层 nftables |
| ufw | Debian/Ubuntu | 简单易用（uncomplicated firewall） |

```bash
# firewalld（RHEL）
sudo firewall-cmd --get-default-zone
sudo firewall-cmd --add-service=ssh --permanent
sudo firewall-cmd --reload

# ufw（Ubuntu）
sudo ufw default deny incoming
sudo ufw allow 22022/tcp
sudo ufw enable
```

iptables/nftables 的完整表链、规则和 NAT 详见独立文章 [防火墙 iptables](/guide/linux-security-iptables)。

::: warning 云服务器还要看"安全组"
阿里云/腾讯云等在宿主机网络层还有**安全组（云防火墙）**，相当于机器外面的一层防火墙。即使系统内放行，安全组没开端口也访问不了；两边都要配置。
:::

---

## 三、SELinux

### 3.1 背景：MAC 强制访问控制

- 传统权限（rwx、属主）是 **DAC（自主访问控制）**，root 几乎无所不能，进程被攻破就能为所欲为；
- **SELinux（Security-Enhanced Linux）** 是 **MAC（强制访问控制）**，由 NSA 贡献，给每个进程和文件打上**安全标签**，即使 root 操作，不符合策略也会被拒绝；
- **RHEL/Rocky/CentOS 默认开启且 Enforcing**；Debian/Ubuntu 默认用 **AppArmor**（另一种 MAC），SELinux 默认不装。

### 3.2 三种模式

| 模式 | 含义 |
|---|---|
| **enforcing** | 强制：违反策略的操作被**拒绝**并记录 |
| **permissive** | 宽容：只记录警告、**不拦截**（调试用） |
| **disabled** | 关闭 |

```bash
getenforce                      # 查看当前模式
sestatus                        # 详细状态

sudo setenforce 0               # 临时切 permissive（0），重启失效
sudo setenforce 1               # 临时切 enforcing（1）
```

永久模式改 `/etc/selinux/config`（**需重启**）：

```ini
SELINUX=enforcing        # enforcing / permissive / disabled
```

::: warning 不要一遇到问题就关 SELinux
生产中**不建议直接 disabled**。正确做法是排查并修正上下文/布尔值；临时调试可先切 permissive，定位后再回 enforcing。
:::

### 3.3 安全上下文（Security Context）

格式：`用户:角色:类型:级别`，运维最关注**类型（Type，以 _t 结尾）**。

```bash
ls -Z /var/www/html              # 查看文件上下文（httpd_sys_content_t）
ps -eZ | grep nginx             # 查看进程域（httpd_t / nginx_t）
id -Z                            # 当前用户上下文
```

**修正上下文：**

```bash
# 临时修改（chcon）
sudo chcon -t httpd_sys_content_t /var/www/html/index.html

# 永久修改（推荐，写入策略，restorecon 可恢复）
sudo semanage fcontext -a -t httpd_sys_content_t "/data/web(/.*)?"
sudo restorecon -Rv /data/web        # 按策略重新打标签
```

> 典型问题：把网站根目录改到非标准路径（如 /data/web），文件默认是 `default_t`，httpd 无权读取报 403。用 `semanage fcontext + restorecon` 修正即可。

### 3.4 布尔值（Booleans）

布尔值是策略里可开关的功能项：

```bash
getsebool -a                          # 列出所有
sudo setsebool -P httpd_can_network_connect on   # -P 永久生效（允许 httpd 访问外网）
semanage boolean -l | grep httpd      # 含说明
```

常用 httpd 布尔：`httpd_can_network_connect`（连数据库/外网）、`httpd_enable_homedirs`（用户家目录页面）、`httpd_unified`。

### 3.5 端口与排错

```bash
# 让服务使用非标准端口（如 httpd 用 8080）
sudo semanage port -l | grep http_port_t
sudo semanage port -a -t http_port_t -p tcp 8080
```

**排查 SELinux 拒绝：**

```bash
sudo ausearch -m avc -ts recent              # 查拒绝日志
sudo journalctl -t setroubleshoot            # 看诊断建议（需 setroubleshoot）
sudo sealert -a /var/log/audit/audit.log      # 给出原因和修复命令
```

::: details Debian/Ubuntu 的 AppArmor
Debian 系默认用 AppArmor，按"配置文件 + 路径"做访问控制：
```bash
sudo aa-status
sudo aa-complain /usr/bin/xxx     # 宽容模式
```
思想与 SELinux 类似，都是 MAC，掌握其一即可类比。
:::

---

## 四、SSH 加固

SSH 是服务器最常暴露、最被重点扫描爆破的服务，必须加固。配置文件 `/etc/ssh/sshd_config`，改完 `systemctl restart sshd`。

### 4.1 核心加固项

```ini
# 1. 禁止 root 直接登录
PermitRootLogin no

# 2. 密钥登录、关闭密码登录
PubkeyAuthentication yes
PasswordAuthentication no
PermitEmptyPasswords no

# 3. 改非标准高端口（减少自动化扫描，端口需在安全组/防火墙放行）
Port 22022

# 4. 限制可登录用户
AllowUsers zlmggg
# AllowGroups sshusers

# 5. 其他
MaxAuthTries 3              # 最大认证尝试次数
LoginGraceTime 30           # 认证宽限时间
X11Forwarding no            # 不需要就关
# ClientAliveInterval 300   # 空闲超时
# ClientAliveCountMax 2
```

```bash
sudo sshd -t                 # 改完先检查语法，避免配置错误起不来
sudo systemctl restart sshd
```

### 4.2 密钥登录流程

```bash
# 客户端生成密钥（ed25519 更短更安全）
ssh-keygen -t ed25519
ssh-copy-id -p 22022 zlmggg@服务器IP      # 把公钥推到服务器 ~/.ssh/authorized_keys
ssh -p 22022 zlmggg@服务器IP             # 验证密钥能登录后，再关密码登录
```

::: danger 别把自己关在外面
关闭密码登录、改端口、禁 root 之前，**务必保留一个已登录的会话别动**，另开新窗口验证密钥能正常登录，确认无误后再关闭旧会话。否则配置有误将无法远程登录，只能走云控制台 VNC 救援。
:::

> 完整的 SSH 密钥、MobaXterm 配置、sudo 用户创建步骤，见部署文档和 [用户与权限](/guide/linux-users)。

---

## 五、SSL/TLS 证书

### 5.1 证书原理（简要）

- **非对称加密**有公钥/私钥：公钥可公开、私钥保密；
- **CA（证书颁发机构）** 用自己的根证书给网站签发证书，浏览器/系统内置了受信任 CA 的根证书；
- 访问 HTTPS 网站时，服务器出示证书，客户端验证它由受信任 CA 签发、域名匹配且未过期，形成**信任链**，随后协商密钥进行加密通信。

### 5.2 自签名证书（内网/测试）

自签名证书不被公网信任（浏览器报警），只适合内网和测试：

```bash
# 生成私钥 + 自签名证书（x509，365 天）
openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout server.key -out server.crt -days 365 \
  -subj "/CN=10.0.0.13"
```

### 5.3 Let's Encrypt 免费证书（公网推荐）

**Let's Encrypt** 提供免费、受信任的证书，有效期 **90 天**（短期证书更安全），用 **acme.sh** 等工具申请并自动续期：

```bash
# acme.sh 容器方式指定 Let's Encrypt（默认 CA 可能是 ZeroSSL）
docker run --rm -v /data/acme:/acme.sh neilpang/acme.sh \
  --set-default-ca --server letsencrypt

# 申请（webroot/standalone/nginx 等方式，需域名已解析、80 可访问）
# 安装证书到指定目录并配置 reload 命令，acme.sh 会自动加 cron 续期
```

::: tip 证书与备案
国内服务器在备案完成前，80/443 域名访问会被拦截，证书的 HTTP 验证也可能受影响；可等备案通过后再申请，或用 DNS 验证方式。
:::

### 5.4 HTTPS 配置要点

- 用 HTTP/2、配置现代 TLS 版本（禁用旧的 SSLv3/TLS 1.0/1.1）；
- 配置 HSTS（强制 HTTPS）；
- 证书、私钥权限保护好（私钥泄露等于身份可被冒充）；
- 定期检查证书有效期和自动续期是否正常。

> OpenSSL 完整命令、自建 CA、PKI 体系可扩展学习；SSL 配置参考 Mozilla SSL Configuration Generator：https://ssl-config.mozilla.org/

---

## 六、VPN

### 6.1 应用场景

VPN（虚拟专用网络）让你在公网中建立加密通道，**安全地接入内网**——比如在家通过公网访问公司/家里服务器内网的服务，而不必把它们直接暴露到公网。

### 6.2 常见方案

| 方案 | 特点 |
|---|---|
| **WireGuard** | 现代、代码精简、配置简单、性能好，内核集成，**首选学习** |
| **OpenVPN** | 成熟老牌、跨平台、资料多，配置相对复杂 |
| IPsec/IKEv2 | 标准化，常用于站点到站点、企业/移动设备 |
| Tailscale | 基于 WireGuard 的零信任组网，开箱即用、NAT 穿透好 |

### 6.3 思路对比

- **传统 VPN**：接入后"进入"内网，可访问内网资源（网络层）；
- **零信任（Zero Trust）**：不默认信任内网，每次访问都认证、按需授权（如 Tailscale、Cloudflare Tunnel）；
- 对个人小服务器，**WireGuard/Tailscale** 简单够用；把 SSH 等管理端口只对 VPN 内网开放，能大幅减少公网暴露。

::: details Tailscale 作为备选
Tailscale 基于 WireGuard，设备登录账号即自动组网，能穿透 NAT、无需公网端口，适合家用 IP 经常变化的场景；缺点是依赖其协调服务（有自建 Headscale 方案）。
:::

---

## 七、时间同步

### 7.1 为什么时间必须准确

- **日志关联**：多台机器排查，时间不一致无法对齐事件；
- **认证/证书**：Kerberos 对时间偏差敏感（通常要求 5 分钟内），证书判断有效期；
- **集群一致性**：数据库、分布式系统依赖时间协调；
- 计划任务、交易时序等。

### 7.2 工具选型

| 工具 | 说明 |
|---|---|
| **chrony** | 现代 NTP 实现，同步快、对不稳定网络友好，**RHEL 8+ 默认**，推荐 |
| ntpd | 传统 NTP 守护进程 |
| systemd-timesyncd | systemd 自带的轻量客户端，Ubuntu Server 常用，只做客户端 |

### 7.3 chrony 配置

配置文件 `/etc/chrony/chrony.conf`（Ubuntu）或 `/etc/chrony.conf`（RHEL）：

```ini
# 上游时间服务器（用国内源更快）
server ntp.aliyun.com iburst
server cn.pool.ntp.org iburst
# makestep：偏差大时直接步进校准
makestep 1.0 3
# 允许哪些内网客户端同步（做服务器时）
# allow 10.0.0.0/24
# 本机没网时仍可作为时间源
# local stratum 10
```

```bash
sudo systemctl enable --now chronyd
chronyc sources -v          # 查看上游源（^* 表示已同步）
chronyc tracking           # 查看同步状态/偏差
```

### 7.4 timedatectl

```bash
timedatectl                          # 查看时间、时区、NTP 状态
sudo timedatectl set-timezone Asia/Shanghai
sudo timedatectl set-ntp true        # 开启网络时间同步
```

### 7.5 自建时间服务器

在内网一台能连公网的机器上跑 chrony，配置 `allow 内网网段` 和 `local stratum`，其他内网机器把 server 指向它，实现内网统一时间源，避免每台都连公网。

> 官方文档：https://chrony.tuxfamily.org/documentation.html

---

## 面试自测

1. 什么是纵深防御？列举至少 5 项基础加固措施。
2. Linux 防火墙有哪些常见工具？默认策略应该是什么？
3. SELinux 三种模式的区别？enforcing 和 permissive 有何不同？
4. SELinux 的安全上下文是什么？改了网站根目录导致 403 怎么解决？
5. SELinux 布尔值是什么？如何让 httpd 连接外部数据库？
6. 如何排查 SELinux 导致的拒绝？为什么不建议直接关闭 SELinux？
7. SSH 加固有哪些核心措施？密钥登录的流程？
8. 修改 SSH 配置时如何防止把自己关在外面？
9. 证书/CA 的信任链原理？Let's Encrypt 证书有效期多久、如何续期？
10. 自签名证书和 CA 签发证书的区别、各自适用场景？
11. VPN 是干什么的？WireGuard、OpenVPN、Tailscale 各有什么特点？
12. 时间不准确会导致哪些问题？chrony 如何查看同步状态？

## 相关速查

- [防火墙 iptables](/guide/linux-security-iptables)
- [用户与权限](/guide/linux-users)
- [网络命令速查](/reference/network-commands)
- [Linux 命令速查](/reference/linux-commands)
