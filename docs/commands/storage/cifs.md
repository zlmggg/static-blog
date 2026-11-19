---
title: "mount.cifs · 挂载 Windows/SMB 共享"
description: "mount.cifs 挂 SMB/CIFS 共享、credentials 凭据文件、vers 版本、uid/gid 权限映射。跨平台文件共享，中文详解。"
---

# mount.cifs · 挂载 Windows/SMB 共享

> 命令手册 · [磁盘与存储](/commands/storage/) ｜ 频率：很少用
> 挂 Windows 共享文件夹或 Samba 服务——用 cifs（SMB 协议）。Linux 访问 Windows 文件共享的桥梁。

## 一句话用途

挂载 SMB/CIFS 网络共享（Windows 共享/Samba）。

## 高频场景速查

```bash
sudo dnf install -y cifs-utils           # 安装
sudo mount -t cifs //10.0.0.5/share /mnt \
  -o username=user,password='请替换为强密码',vers=3.0
# 推荐：凭据文件（避免密码进 history/ps）
sudo mount -t cifs //10.0.0.5/share /mnt -o credentials=/root/.smbcred,vers=3.0
# fstab 持久化
//10.0.0.5/share  /mnt  cifs  credentials=/root/.smbcred,_netdev,nofail,vers=3.0  0 0
```

## 凭据文件（安全）

```text
# /root/.smbcred（chmod 600）
username=user
password=请替换为强密码
domain=WORKGROUP
```

## 关键选项

| 选项 | 含义 |
|---|---|
| `credentials=文件` | 凭据文件（推荐） |
| `vers=3.0/2.1` | SMB 版本（新系统用3.0，1.0不安全） |
| `uid=/gid=` | 挂载后属主映射 |
| `file_mode=/dir_mode=` | 权限位 |
| `_netdev` | 等网络就绪 |
| `iocharset=utf8` | 中文文件名 |

::: warning 别用 SMB1
vers=1.0（SMB1）有严重漏洞（WannaCry 利用），默认禁用。用 vers=3.0。密码别写命令行（进 history），用 credentials 文件 chmod 600。
:::

## 运维实战

**Linux 读 Windows 共享**：mount.cifs 挂过来备份/处理。
**权限映射**：uid/gid 设成本地服务账号，file_mode=0644 让应用可读。
**排挂载失败**：确认 vers 版本匹配、防火墙放行 445、凭据正确。

## 相关命令

[mount/fstab](./mount-umount) · [NFS](./nfs) · [firewall-cmd](/commands/network/firewall-cmd) · [scp/sftp](/commands/network/scp-sftp)

## 官方文档

- mount.cifs：<https://man7.org/linux/man-pages/man8/mount.cifs.8.html>