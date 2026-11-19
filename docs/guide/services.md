---
title: "服务部署"
description: "本页聚合 常见服务的部署与运维：Web 服务（Nginx / Apache / Tomcat）、DNS 域名服务、文件共享服务。"
---
# 服务部署

> 本页聚合 **常见服务的部署与运维**：Web 服务（Nginx / Apache / Tomcat）、DNS 域名服务、文件共享服务。

## 文章索引

### Web 服务

::: idx

| 文章 | 解决什么问题 | 状态 |
|---|---|---|
| [Nginx 实战](/services/web/nginx/01-理论) | 安装、虚拟主机、反向代理、负载均衡、SSL/HTTP2、调优 | ✅ 已完成 |
| [Apache 与 Tomcat](#合并资料) | HTTP 协议、Apache 虚拟主机/认证、Tomcat、JVM/GC | ✅ 已完成 |

:::

### DNS 域名服务

::: idx

| 文章 | 解决什么问题 | 状态 |
|---|---|---|
| [DNS 域名解析](#合并资料) | DNS 原理/记录、BIND 部署、正反解析、主从、分离解析 | ✅ 已完成 |

:::

### 文件共享

::: idx

| 文章 | 解决什么问题 | 状态 |
|---|---|---|
| [文件共享服务](#合并资料) | NFS、Samba、vsftpd 部署与权限 | ✅ 已完成 |

:::

### 负载均衡与高可用

::: idx

| 文章 | 解决什么问题 | 状态 |
|---|---|---|
| [LVS 与 Keepalived](/services/web/lvs-keepalived) | LVS DR/NAT 模式、ipvsadm、Keepalived VIP 四层负载高可用 | ✅ 已完成 |

:::

## 命令速查

- 服务管理、端口查看：[Linux 命令速查](/reference/linux-commands)
- HTTP 测试（curl）、端口连通（nc）：[网络命令速查](/reference/network-commands)

<!-- merged-guide-material:start -->
## 合并资料

> 原先单独成页的同主题内容已收进本页；默认折叠，点开看原页全文。

<details>
<summary><strong>DNS 域名解析 — DNS 层级与递归迭代、记录类型、BIND（RHEL named / Debian bind9）正反向解析、主从复制、view 分离、转发缓存、dig/nslookup/host 排障</strong></summary>

::: tip 本篇定位
理解 DNS **域名层级、递归/迭代解析、各类记录**，用 BIND 搭建**正向/反向解析、主从复制、view 分离、转发缓存**，并用 **dig/nslookup/host** 排障。
:::

#### 先建立全局观：域名是怎么变成 IP 的

```
你输入 www.sersec.com
   → 本地 DNS（递归解析器）
   → 问根"."（返回 .com 顶级域地址）
   → 问 .com（返回 sersec.com 权威服务器地址）
   → 问 sersec.com 权威（返回 www 的 IP）
   → 本地 DNS 缓存结果并返回给你
```

- **递归查询**：你把问题交给本地 DNS，由它负责问到底、返回最终答案；
- **迭代查询**：本地 DNS 依次向根、顶级域、权威服务器询问，每级返回"你去问下一个"。

DNS 主要用 **UDP 53**（快）；区域传输和超大响应用 **TCP 53**。

---

#### 一、DNS 基础

##### 1.1 域名层级

```
        . （根域 root）
       / \
    .com .cn ...        顶级域 TLD
     |
  sersec.com            二级域（可注册的主体）
     |
  www.sersec.com        子域/主机
```

##### 1.2 记录类型

| 记录 | 作用 | 例子 |
|---|---|---|
| **A** | 域名 → IPv4 | www → 203.0.113.10 |
| AAAA | 域名 → IPv6 | |
| **CNAME** | 域名别名 → 另一域名 | cdn → xxx.com |
| **MX** | 邮件服务器（带优先级） | |
| **NS** | 指定该域的权威 DNS 服务器 | |
| **PTR** | IP → 域名（反向解析） | |
| **SOA** | 起始授权，区域主服务器/管理员/序列号/计时 | 每个区域开头 |
| TXT | 文本（SPF、域名验证） | |
| SRV | 服务记录 | |
| CAA | 限定可签发证书的 CA | |

---

#### 二、BIND 安装

##### 2.1 RHEL/Rocky（服务名 named）

```bash
sudo dnf install -y bind bind-utils
sudo systemctl enable --now named
# 主配置 /etc/named.conf；区域文件 /var/named/
```

##### 2.2 Debian/Ubuntu（服务名 bind9）

```bash
sudo apt install -y bind9 bind9utils dnsutils
sudo systemctl enable --now bind9
# /etc/bind/named.conf、named.conf.options、named.conf.local；区域 /etc/bind/
```

##### 2.3 配置结构

- 主配置：监听、允许查询、转发、包含区域；
- 区域文件：具体记录。

RHEL `/etc/named.conf` 关键：

```conf
options {
    listen-on port 53 { any; };
    allow-query     { any; };
    recursion yes;
};
zone "sersec.com" IN {
    type master;
    file "sersec.com.zone";
    allow-update { none; };
};
```

Debian 在 `named.conf.local` 写 zone，options 写在 `named.conf.options`。

---

#### 三、正向解析

##### 3.1 区域文件

RHEL：`/var/named/sersec.com.zone`（Debian：`/etc/bind/db.sersec.com`）：

```conf
$TTL 86400
@   IN  SOA   ns.sersec.com. admin.sersec.com. (
            2026092801 ; Serial  序列号（每次修改 +1）
            3600       ; Refresh
            1800       ; Retry
            604800     ; Expire
            86400 )    ; Minimum TTL
    IN  NS    ns.sersec.com.
    IN  MX 10 mail.sersec.com.
ns  IN  A     203.0.113.10
www IN  A     203.0.113.10
mail IN A     203.0.113.10
cdn IN  CNAME www.sersec.com.
```

##### 3.2 验证

```bash
# RHEL
named-checkconf
named-checkzone sersec.com /var/named/sersec.com.zone
sudo systemctl reload named

# Debian
sudo named-checkzone sersec.com /etc/bind/db.sersec.com
sudo systemctl reload bind9
```

::: warning 最常见错误
- 完整域名（FQDN）结尾**漏了点 `.`**，会被自动补成相对名；
- 改了记录**没加 Serial**，从库不更新；
- 区域文件属主/权限不对（RHEL 应为 root 或 named，按发行版要求）。
:::

---

#### 四、反向解析

##### 4.1 区域声明

```conf
# 网段 203.0.113.0/24，反向域写反：113.0.203.in-addr.arpa
zone "113.0.203.in-addr.arpa" IN {
    type master;
    file "113.0.203.zone";
};
```

##### 4.2 反向区域文件

`/var/named/113.0.203.zone`：

```conf
$TTL 86400
@ IN SOA ns.sersec.com. admin.sersec.com. (
      2026092801 3600 1800 604800 86400 )
  IN NS ns.sersec.com.
10 IN PTR www.sersec.com.      -- 203.0.113.10
```

```bash
named-checkzone 113.0.203.in-addr.arpa /var/named/113.0.203.zone
```

反向解析常用于邮件服务器信誉、日志反查。

---

#### 五、主从复制

主从通过**区域传输**同步：全量 **AXFR**、增量 **IXFR**；主库 Serial 增大后通知（NOTIFY）从库拉取。

**主库：**

```conf
zone "sersec.com" IN {
    type master;
    file "sersec.com.zone";
    allow-transfer { 10.0.0.14; };   -- 只允许从库
    also-notify    { 10.0.0.14; };
};
```

**从库（10.0.0.14）：**

```conf
zone "sersec.com" IN {
    type slave;
    masters { 10.0.0.13; };
    file "slaves/sersec.com.zone";    -- 存可写目录
};
```

::: danger 安全
`allow-transfer` 必须限制为从库 IP，若配成 `any`，任何人都能 axfr 拉走你整个域的所有记录（信息泄露，也是常见扫描点）。
:::

---

#### 六、view 分离解析

让**内网和外网**对同一域名解析到不同结果（如 www 内网→内网 IP、外网→公网 IP）。

```conf
view "internal" {
    match-clients { 10.0.0.0/8; localhost; };
    zone "sersec.com" IN {
        type master;
        file "sersec-internal.zone";
    };
};

view "external" {
    match-clients { any; };
    zone "sersec.com" IN {
        type master;
        file "sersec-external.zone";
    };
};
```

> 使用 view 后，所有 zone 都必须放进某个 view，不能有游离在 view 外的 zone。

---

#### 七、转发与缓存

本机不解析、把请求转给上游 DNS（如公共/云厂商 DNS）：

```conf
options {
    forwarders { 223.5.5.5; 223.6.6.6; };   -- 阿里
    forward first;     -- first: 先转发，失败再自己迭代；only: 只转发
};
```

转发可针对特定域（zone forward），缓存能减少重复查询、加快解析。

---

#### 八、客户端工具与排障

##### 8.1 dig（最常用）

```bash
dig www.sersec.com                  # 完整输出
dig @10.0.0.13 www.sersec.com       # 指定 DNS 服务器
dig -t MX sersec.com                # 指定记录类型
dig -x 203.0.113.10               # 反向解析
dig www.sersec.com +short           # 只看结果
dig www.sersec.com +trace           # 跟踪完整迭代路径
```

输出关注：`status: NOERROR`、`ANSWER SECTION`、TTL。

##### 8.2 nslookup / host

```bash
nslookup www.sersec.com 10.0.0.13
host www.sersec.com
```

##### 8.3 常见问题

| 现象 | 方向 |
|---|---|
| 解析不到 | 服务状态、UDP/TCP 53、allow-query、区域配置 |
| 改记录不生效 | Serial 没加、缓存 TTL 未到、没 reload |
| 从库不同步 | allow-transfer、NOTIFY、网络、Serial |
| SERVFAIL | 看日志，区域文件/语法错误、上游不可达 |

---

#### 本章自测

1. 描述一次完整的域名解析过程，递归和迭代的区别？
2. A、CNAME、MX、NS、PTR、SOA 记录分别做什么？
3. 区域文件里 Serial 的作用？为什么改记录要加序列号？
4. 主从 DNS 如何同步？AXFR 和 IXFR？allow-transfer 为什么不能 any？
5. view 分离解析解决什么问题？
6. dig -x、+trace、@服务器分别怎么用？

#### 相关速查

- [Linux 命令速查](/reference/linux-commands)
- BIND 文档（ISC）：https://bind9.readthedocs.io/
- dig 手册：https://man7.org/linux/man-pages/man1/dig.1.html

</details>

<details>
<summary><strong>文件共享服务 — NFS（exports 选项/exportfs/autofs）、Samba（smb.conf/smbpasswd/跨平台客户端）、vsftpd（主动被动/chroot/虚拟用户）部署与方案选型</strong></summary>

::: tip 本篇定位
掌握三种文件共享方案：**NFS**（Linux 之间）、**Samba**（跨 Windows/Linux）、**vsftpd**（FTP），理解原理、完整配置、权限映射与客户端挂载，并会选型。
:::

#### 先建立全局观：按"和谁共享"选方案

| 方案 | 协议 | 主要场景 |
|---|---|---|
| NFS | NFS/RPC，端口 2049 | **Linux ↔ Linux** 共享目录 |
| Samba | SMB/CIFS | **Windows ↔ Linux**、跨平台文件和打印共享 |
| FTP/vsftpd | FTP，端口 21 | 文件上传下载（明文，建议 SFTP/FTPS） |

---

#### 一、NFS

##### 1.1 原理

NFS（Network File System）让客户机把远程目录**挂载**成本地目录使用。它依赖 **RPC（rpcbind）** 做端口映射，数据端口 2049。

##### 1.2 安装

```bash
# 服务端
sudo dnf install -y nfs-utils rpcbind        # RHEL
sudo apt install -y nfs-kernel-server        # Debian

sudo mkdir -p /data/share
sudo chown -R nobody:nobody /data/share
```

##### 1.3 配置 /etc/exports

```conf
# 格式：共享目录  允许主机(选项)
/data/share  10.0.0.0/24(rw,sync,no_root_squash,no_subtree_check)
/data/ro     *(ro,sync)
```

常用选项：

| 选项 | 含义 |
|---|---|
| rw / ro | 读写 / 只读 |
| sync / async | 同步写（安全，推荐）/ 异步（快） |
| root_squash（默认） | 客户端 root 映射为匿名（安全） |
| no_root_squash | 保留 root 权限（危险，按需） |
| all_squash | 所有用户都映射为匿名 |
| anonuid / anongid | 指定匿名映射的 uid/gid |
| no_subtree_check | 不检查子目录（减少问题） |

##### 1.4 发布

```bash
sudo exportfs -r        # 重新加载 exports
sudo exportfs -v        # 查看生效的共享
sudo systemctl enable --now nfs-server rpcbind   # Debian: nfs-kernel-server
```

##### 1.5 客户端挂载

```bash
sudo dnf install -y nfs-utils        # Debian: nfs-common
showmount -e 10.0.0.13               # 查看服务端共享列表
sudo mkdir -p /mnt/share
sudo mount -t nfs 10.0.0.13:/data/share /mnt/share
df -h
```

##### 1.6 开机挂载与自动挂载

```conf
# /etc/fstab
10.0.0.13:/data/share  /mnt/share  nfs  defaults,_netdev  0 0
```

大量/按需挂载用 **autofs**（访问时才挂载、空闲自动卸载），配置 auto.master + 映射文件。

::: warning 权限两层都要对
NFS 同时受 **exports 选项**和**服务端文件系统权限**约束。挂载后写不进去，先查服务端目录属主/权限、是否被 root_squash、uid 是否一致。
:::

---

#### 二、Samba

##### 2.1 原理

Samba 实现 SMB/CIFS 协议，让 Linux 与 Windows 之间共享文件、打印机，支持域认证。

##### 2.2 安装

```bash
sudo dnf install -y samba samba-client        # RHEL
sudo apt install -y samba samba-client        # Debian
sudo mkdir -p /data/smbshare
```

##### 2.3 配置 /etc/samba/smb.conf

```conf
[global]
        workgroup = WORKGROUP
        security = user
        map to guest = Bad User

[share]
        comment = Shared Data
        path = /data/smbshare
        browseable = yes
        writable = yes
        valid users = smbuser
        create mask = 0664
        directory mask = 0775
```

##### 2.4 创建 Samba 用户

Samba 用户必须先是系统用户，再单独设 Samba 密码（独立于系统密码）：

```bash
sudo useradd -s /sbin/nologin smbuser
sudo smbpasswd -a smbuser        # 设置 Samba 密码
sudo pdbedit -L                  # 列出 Samba 用户
sudo systemctl enable --now smb nmb     # Debian: smbd nmbd
testparm                         # 检查配置语法
```

##### 2.5 客户端

```bash
# Linux
smbclient -L //10.0.0.13 -U smbuser
smbclient //10.0.0.13/share -U smbuser

# 挂载
sudo mount -t cifs -o username=smbuser //10.0.0.13/share /mnt/smb
# /etc/fstab 加 cifs 凭据文件（credentials，权限 600）
```

Windows：资源管理器输入 `\\10.0.0.13\share`，输入 Samba 账号密码。

---

#### 三、vsftpd

##### 3.1 主动与被动模式

| 模式 | 数据连接 |
|---|---|
| 主动 PORT | 服务器用 **20** 主动连客户端（客户端有防火墙时易失败） |
| **被动 PASV** | 客户端连服务器的高端口（NAT/防火墙环境常用，需放行端口范围） |

控制连接端口 **21**。

##### 3.2 安装

```bash
sudo dnf install -y vsftpd       # RHEL
sudo apt install -y vsftpd       # Debian
```

##### 3.3 关键配置 /etc/vsftpd/vsftpd.conf

```conf
anonymous_enable=NO
local_enable=YES
write_enable=YES
local_umask=022
chroot_local_user=YES            # 锁定用户在自己家目录
allow_writeable_chroot=YES       # chroot 目录可写时需要
pasv_min_port=30000
pasv_max_port=31000             # 被动端口范围（防火墙/安全组放行）
```

```bash
sudo systemctl enable --now vsftpd
```

##### 3.4 虚拟用户（更安全）

用独立的虚拟账号文件（PAM + Berkeley DB 或 guest 用户映射），虚拟用户不对应真实系统登录账号，泄露风险更小。

::: danger FTP 是明文协议
FTP 传输内容和密码都不加密，公网易被嗅探。安全需求请用 **SFTP（基于 SSH）** 或 **FTPS（FTP over TLS，vsftpd 支持 ssl_enable）**。
:::

---

#### 四、方案对比与选型

| 维度 | NFS | Samba | FTP/SFTP |
|---|---|---|---|
| 跨平台 | Linux 为主 | Windows/Linux 都好 | 任意（客户端即可） |
| 挂载使用 | 支持，像本地盘 | 支持 | 一般上传下载 |
| 性能 | 高（局域网） | 中 | 中 |
| 安全 | 靠权限/选项 | 用户认证 | SFTP/FTPS 才安全 |
| 典型 | Linux 集群共享存储 | 办公/混合环境 | 文件分发、运维传输 |

---

#### 本章自测

1. NFS 的 root_squash 和 no_root_squash 有什么区别？
2. NFS 挂载后无法写入，从哪些方面排查？
3. Samba 用户和系统用户是什么关系？smbpasswd -a 做什么？
4. FTP 主动和被动模式的区别？为什么 NAT 环境常用被动？
5. 为什么不建议公网用明文 FTP？替代方案？
6. NFS、Samba、SFTP 分别适合什么场景？

#### 相关速查

- [Linux 命令速查](/reference/linux-commands)
- NFS（Linux 文档）：https://nfs.sourceforge.net/nfs-howto/
- Samba 文档：https://www.samba.org/samba/docs/
- vsftpd：https://security.appspot.com/vsftpd.html（需科学上网）；国内平替：https://cloud.tencent.com/document/product/1207/47638

</details>

<details>
<summary><strong>Apache 与 Tomcat — HTTP 协议方法状态码 Cookie/Session/JWT、Apache（httpd/apache2）MPM/虚拟主机/htaccess、Tomcat 安装部署/server.xml/WAR、JVM 内存 GC 与调优</strong></summary>

::: tip 本篇定位
理解 **HTTP 协议**，会部署配置 **Apache**（httpd/apache2），会安装 **Tomcat** 部署 Java Web（WAR、server.xml、manager），并掌握 **JVM 内存结构、GC 与基础调优**。
:::

---

#### 一、HTTP 协议

HTTP 是浏览器/客户端与 Web 服务器之间的**应用层、无状态**协议（基于 TCP）。

##### 1.1 请求方法

| 方法 | 语义 |
|---|---|
| GET | 获取资源（参数在 URL，幂等） |
| POST | 提交数据（参数在 body） |
| PUT | 更新/替换资源 |
| DELETE | 删除资源 |
| HEAD | 只要响应头 |
| PATCH | 部分更新 |

##### 1.2 状态码

| 段 | 含义 | 常见 |
|---|---|---|
| 2xx | 成功 | 200 OK |
| 3xx | 重定向 | 301 永久、302 临时、304 Not Modified（缓存） |
| 4xx | 客户端错误 | 400 参数、401 未认证、403 禁止、404 不存在 |
| 5xx | 服务端错误 | 500 内部错误、502 网关、503 不可用、504 网关超时 |

##### 1.3 请求/响应头

常见 Header：Host、Content-Type、Content-Length、User-Agent、Referer、Authorization、Cache-Control、Set-Cookie。

##### 1.4 Cookie、Session 与 JWT

HTTP 无状态，需要维持登录态：

| 方案 | 原理 | 特点 |
|---|---|---|
| Cookie | 服务器下发、浏览器每次自动携带 | 存客户端，有大小限制 |
| Session | 服务端存状态，靠 Cookie 里的 session id 关联 | 服务端存，多机要共享 session |
| JWT | 服务端签发签名 token（Header.Payload.Signature），客户端携带 | 无状态、可跨服务，签发后难即时作废 |

---

#### 二、Apache 安装

Apache HTTP Server（httpd）是老牌 Web 服务器。

##### 2.1 RHEL/Rocky（服务名 httpd）

```bash
sudo dnf install -y httpd
sudo systemctl enable --now httpd
# 配置 /etc/httpd/conf/httpd.conf、conf.d/；站点 /var/www/html；日志 /var/log/httpd/
```

##### 2.2 Debian/Ubuntu（服务名 apache2）

```bash
sudo apt install -y apache2
sudo systemctl enable --now apache2
# /etc/apache2/；站点 /var/www/html；日志 /var/log/apache2/
```

##### 2.3 MPM 工作模式

| MPM | 模型 | 特点 |
|---|---|---|
| prefork | 多进程、每进程一个请求、无线程 | 稳定、兼容非线程安全模块（如老 PHP），内存占用高 |
| worker | 多进程 + 每进程多线程 | 内存省、并发较好 |
| event | 类似 worker，优化 keep-alive | **默认推荐** |

RHEL 编辑 `/etc/httpd/conf.modules.d/` 选择；Debian `a2dismod mpm_prefork && a2enmod mpm_event`。

---

#### 三、Apache 配置

##### 3.1 虚拟主机

Debian（站点配置 + 启用）：

```bash
sudo cp /etc/apache2/sites-available/000-default.conf /etc/apache2/sites-available/a.com.conf
```

```apache
<VirtualHost *:80>
    ServerName www.a.com
    DocumentRoot /data/www/a
    ErrorLog ${APACHE_LOG_DIR}/a_error.log
    CustomLog ${APACHE_LOG_DIR}/a_access.log combined
</VirtualHost>
```

```bash
sudo a2ensite a.com.conf
sudo systemctl reload apache2
```

RHEL 在 `/etc/httpd/conf.d/a.conf` 写 VirtualHost。

##### 3.2 目录访问控制

```apache
<Directory /data/www/a>
    Require all granted
    Options -Indexes +FollowSymLinks
    AllowOverride All        # 允许 .htaccess（None 性能更好）
</Directory>
```

##### 3.3 .htaccess 与认证

`.htaccess` 可在不改主配置的情况下做目录级控制（重写、认证、缓存），但每次请求读取、有性能开销，能用主配置就用主配置。

基础认证：

```bash
htpasswd -c /etc/apache2/.htpasswd tom
```

```apache
<Directory /data/www/private>
    AuthType Basic
    AuthName "Private"
    AuthUserFile /etc/apache2/.htpasswd
    Require valid-user
</Directory>
```

##### 3.4 常用模块命令（Debian）

```bash
a2enmod rewrite ssl headers expires     # 启用模块
a2dismod ...
a2ensite / a2dissite
apache2ctl configtest                   # 检查配置
```

---

#### 四、Tomcat 安装

Tomcat 是 Java 的 Servlet/JSP 容器，运行 Java Web 应用。

##### 4.1 先装 JDK

```bash
sudo dnf install -y java-17-openjdk java-17-openjdk-devel     # RHEL
sudo apt install -y openjdk-17-jdk                            # Debian
java -version
# JDK LTS：8、11、17、21；新框架（Spring Boot 3）需 17+
```

##### 4.2 二进制安装

```bash
# https://tomcat.apache.org/ 下载 Tomcat 10（注意包名变化，见下）
tar -xzf apache-tomcat-10.1.34.tar.gz -C /usr/local/
ln -s /usr/local/apache-tomcat-10.1.34 /usr/local/tomcat

/usr/local/tomcat/bin/startup.sh        # 启动
/usr/local/tomcat/bin/shutdown.sh       # 停止
# 访问 http://IP:8080
```

##### 4.3 Docker

```bash
docker run -d --name tomcat -p 8080:8080 tomcat:10.1.34-jdk17
```

##### 4.4 Tomcat 目录

| 目录 | 内容 |
|---|---|
| bin | 启动/停止脚本 |
| conf | server.xml、web.xml、tomcat-users.xml |
| lib | 依赖 jar |
| webapps | 应用部署目录（放 WAR 自动解压） |
| logs | 日志（catalina.out） |
| work / temp | 编译 JSP、临时文件 |

##### 4.5 端口（server.xml）

| 端口 | 用途 |
|---|---|
| 8080 | HTTP 访问 |
| 8005 | Shutdown 关闭端口 |
| 8009 | AJP（与 Apache httpd 联动，新版默认禁用） |

::: warning Tomcat 版本与包名
**Tomcat 10+ 把 `javax.*` 改成了 `jakarta.*`**。老的基于 javax 的 WAR 部署到 Tomcat 10 会报错，这类老应用应使用 **Tomcat 9**；新开发用 Tomcat 10/11。
:::

---

#### 五、Tomcat 部署与配置

##### 5.1 部署 WAR

```bash
cp app.war /usr/local/tomcat/webapps/ROOT.war   # ROOT 作为根应用
# 或放到 webapps/app，访问 /app/；Tomcat 自动解压部署
```

##### 5.2 manager 管理后台

`conf/tomcat-users.xml` 加角色和用户：

```xml
<role rolename="manager-gui"/>
<user username="admin" password="Admin@123" roles="manager-gui"/>
```

manager 默认只允许本机/需配 RemoteAddrValve 放行，生产务必改强密码或不启用。

##### 5.3 与 Nginx/Apache 配合

生产通常由 Nginx 处理静态、HTTPS，动态请求反代到 Tomcat 8080，Tomcat 只监听本机。

---

#### 六、JVM 基础

##### 6.1 运行时内存结构

| 区域 | 说明 | 是否线程共享 |
|---|---|---|
| 堆 Heap | 对象实例，GC 主战场（新生代 Eden/S0/S1 + 老年代） | 共享 |
| 方法区/元空间 Metaspace | 类信息、常量（JDK8+ 在本地内存） | 共享 |
| 虚拟机栈 | 方法栈帧（局部变量、操作数栈） | 私有 |
| 程序计数器 | 当前执行位置 | 私有 |
| 本地方法栈 | native 方法 | 私有 |

##### 6.2 GC 与判定

- 对象是否回收靠**可达性分析**（从 GC Roots 出发不可达即回收）；
- GC 类型：Minor GC（新生代）、Major/Full GC（老年代/整堆）。

##### 6.3 垃圾收集器

| 收集器 | 特点 |
|---|---|
| Serial / Serial Old | 单线程，小内存/客户端 |
| Parallel Scavenge | 吞吐量优先（JDK8 默认之一） |
| CMS | 低停顿，已废弃（JDK14 移除） |
| **G1** | 分区、可预测停顿，**JDK9+ 默认** |
| ZGC / Shenandoah | 超低停顿、大堆 |

##### 6.4 常用 JVM 参数

```bash
-Xms512m -Xmx512m                 # 堆初始/最大（生产常设相同，避免动态扩缩）
-Xss512k                          # 线程栈大小
-XX:MetaspaceSize=128m
-XX:+UseG1GC                      # 使用 G1
-XX:MaxGCPauseMillis=200
# Tomcat 可写在 bin/setenv.sh 的 JAVA_OPTS/CATALINA_OPTS
```

##### 6.5 排查工具

| 工具 | 用途 |
|---|---|
| jps | 查看 Java 进程 |
| jstat -gcutil pid 1000 | 看 GC/各区使用 |
| jmap -dump:format=b,file=h.hprof pid | 堆转储（分析内存泄漏） |
| jstack pid | 线程栈（分析死锁、CPU 高） |
| jconsole / VisualVM / Arthas | 可视化 / 在线诊断（Arthas 强大） |

---

#### 本章自测

1. 401、403、502、504 分别是什么含义？
2. Cookie、Session、JWT 的区别？多台服务器 Session 怎么处理？
3. Apache 的 prefork/worker/event 有什么区别？
4. Tomcat 8080、8005、8009 端口分别做什么？
5. 为什么老 WAR 放到 Tomcat 10 会报错？
6. JVM 堆和栈、元空间分别存什么？
7. Minor GC 和 Full GC 的区别？G1 有什么特点？
8. CPU 飙高/内存泄漏分别用什么工具、怎么定位？

#### 相关速查

- [Linux 命令速查](/reference/linux-commands)
- HTTP 标准（MDN）：https://developer.mozilla.org/zh-CN/docs/Web/HTTP
- Apache 文档：https://httpd.apache.org/docs/
- Tomcat 文档：https://tomcat.apache.org/tomcat-10.1-doc/
- JVM 调优（Oracle）：https://docs.oracle.com/en/java/javase/17/docs/specs/man/java.html

</details>

<!-- merged-guide-material:end -->
