---
title: 文件共享服务
description: NFS（exports 选项/exportfs/autofs）、Samba（smb.conf/smbpasswd/跨平台客户端）、vsftpd（主动被动/chroot/虚拟用户）部署与方案选型
---

# 文件共享服务

::: tip 本篇定位
掌握三种文件共享方案：**NFS**（Linux 之间）、**Samba**（跨 Windows/Linux）、**vsftpd**（FTP），理解原理、完整配置、权限映射与客户端挂载，并会选型。
:::

## 先建立全局观：按"和谁共享"选方案

| 方案 | 协议 | 主要场景 |
|---|---|---|
| NFS | NFS/RPC，端口 2049 | **Linux ↔ Linux** 共享目录 |
| Samba | SMB/CIFS | **Windows ↔ Linux**、跨平台文件和打印共享 |
| FTP/vsftpd | FTP，端口 21 | 文件上传下载（明文，建议 SFTP/FTPS） |

---

## 一、NFS

### 1.1 原理

NFS（Network File System）让客户机把远程目录**挂载**成本地目录使用。它依赖 **RPC（rpcbind）** 做端口映射，数据端口 2049。

### 1.2 安装

```bash
# 服务端
sudo dnf install -y nfs-utils rpcbind        # RHEL
sudo apt install -y nfs-kernel-server        # Debian

sudo mkdir -p /data/share
sudo chown -R nobody:nobody /data/share
```

### 1.3 配置 /etc/exports

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

### 1.4 发布

```bash
sudo exportfs -r        # 重新加载 exports
sudo exportfs -v        # 查看生效的共享
sudo systemctl enable --now nfs-server rpcbind   # Debian: nfs-kernel-server
```

### 1.5 客户端挂载

```bash
sudo dnf install -y nfs-utils        # Debian: nfs-common
showmount -e 10.0.0.13               # 查看服务端共享列表
sudo mkdir -p /mnt/share
sudo mount -t nfs 10.0.0.13:/data/share /mnt/share
df -h
```

### 1.6 开机挂载与自动挂载

```conf
# /etc/fstab
10.0.0.13:/data/share  /mnt/share  nfs  defaults,_netdev  0 0
```

大量/按需挂载用 **autofs**（访问时才挂载、空闲自动卸载），配置 auto.master + 映射文件。

::: warning 权限两层都要对
NFS 同时受 **exports 选项**和**服务端文件系统权限**约束。挂载后写不进去，先查服务端目录属主/权限、是否被 root_squash、uid 是否一致。
:::

---

## 二、Samba

### 2.1 原理

Samba 实现 SMB/CIFS 协议，让 Linux 与 Windows 之间共享文件、打印机，支持域认证。

### 2.2 安装

```bash
sudo dnf install -y samba samba-client        # RHEL
sudo apt install -y samba samba-client        # Debian
sudo mkdir -p /data/smbshare
```

### 2.3 配置 /etc/samba/smb.conf

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

### 2.4 创建 Samba 用户

Samba 用户必须先是系统用户，再单独设 Samba 密码（独立于系统密码）：

```bash
sudo useradd -s /sbin/nologin smbuser
sudo smbpasswd -a smbuser        # 设置 Samba 密码
sudo pdbedit -L                  # 列出 Samba 用户
sudo systemctl enable --now smb nmb     # Debian: smbd nmbd
testparm                         # 检查配置语法
```

### 2.5 客户端

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

## 三、vsftpd

### 3.1 主动与被动模式

| 模式 | 数据连接 |
|---|---|
| 主动 PORT | 服务器用 **20** 主动连客户端（客户端有防火墙时易失败） |
| **被动 PASV** | 客户端连服务器的高端口（NAT/防火墙环境常用，需放行端口范围） |

控制连接端口 **21**。

### 3.2 安装

```bash
sudo dnf install -y vsftpd       # RHEL
sudo apt install -y vsftpd       # Debian
```

### 3.3 关键配置 /etc/vsftpd/vsftpd.conf

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

### 3.4 虚拟用户（更安全）

用独立的虚拟账号文件（PAM + Berkeley DB 或 guest 用户映射），虚拟用户不对应真实系统登录账号，泄露风险更小。

::: danger FTP 是明文协议
FTP 传输内容和密码都不加密，公网易被嗅探。安全需求请用 **SFTP（基于 SSH）** 或 **FTPS（FTP over TLS，vsftpd 支持 ssl_enable）**。
:::

---

## 四、方案对比与选型

| 维度 | NFS | Samba | FTP/SFTP |
|---|---|---|---|
| 跨平台 | Linux 为主 | Windows/Linux 都好 | 任意（客户端即可） |
| 挂载使用 | 支持，像本地盘 | 支持 | 一般上传下载 |
| 性能 | 高（局域网） | 中 | 中 |
| 安全 | 靠权限/选项 | 用户认证 | SFTP/FTPS 才安全 |
| 典型 | Linux 集群共享存储 | 办公/混合环境 | 文件分发、运维传输 |

---

## 面试自测

1. NFS 的 root_squash 和 no_root_squash 有什么区别？
2. NFS 挂载后无法写入，从哪些方面排查？
3. Samba 用户和系统用户是什么关系？smbpasswd -a 做什么？
4. FTP 主动和被动模式的区别？为什么 NAT 环境常用被动？
5. 为什么不建议公网用明文 FTP？替代方案？
6. NFS、Samba、SFTP 分别适合什么场景？

## 相关速查

- [Linux 命令速查](/reference/linux-commands)
- NFS（Linux 文档）：https://nfs.sourceforge.net/nfs-howto/
- Samba 文档：https://www.samba.org/samba/docs/
- vsftpd：https://security.appspot.com/vsftpd.html
