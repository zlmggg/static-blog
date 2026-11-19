---
title: "NFS · 网络文件共享"
description: "NFS 服务端 exportfs//etc/exports 配置、客户端 mount.nfs/showmount、权限与 _netdev。共享存储基础，中文详解。"
---

# NFS · 网络文件共享

> 命令手册 · [磁盘与存储](/commands/storage/) ｜ 频率：偶尔用
> 多台机器共享一个目录——NFS 最经典。服务端导出目录，客户端挂载像本地一样用。

## 一句话用途

通过网络共享文件系统，多机访问同一份数据。

## 服务端配置

```bash
sudo dnf install -y nfs-utils              # RHEL
sudo systemctl enable --now nfs-server

# /etc/exports 导出目录
/data/share  10.0.0.0/24(rw,sync,no_subtree_check)

sudo exportfs -ra                          # 重新加载导出
sudo exportfs -v                           # 看当前导出
showmount -e localhost                     # 看导出列表
```

### exports 选项

| 选项 | 含义 |
|---|---|
| `rw` / `ro` | 读写 / 只读 |
| `sync` | 同步写（安全，慢） |
| `async` | 异步（快，断电可能丢） |
| `no_subtree_check` | 禁子树检查（推荐） |
| `no_root_squash` | 客户端 root 保留 root（危险） |
| `root_squash` | 客户端 root 映射为匿名（默认安全） |

## 客户端挂载

```bash
showmount -e 10.0.0.5                      # 看服务端导出
sudo mount -t nfs 10.0.0.5:/data/share /mnt
# fstab 持久化
10.0.0.5:/data/share  /mnt  nfs  defaults,_netdev,nofail  0 0
```

## 运维实战

**共享 web 静态资源**：多台 web 挂同一 NFS 存上传文件。
**K8s 持久卷**：NFS 做 PV 后端（简单场景）。
**排挂载卡死**：NFS 服务端宕机会让客户端 D 状态卡死，`umount -f -l` 强制卸，fstab 加 `soft,timeo=30` 避免硬卡。

::: danger NFS 安全
NFS 默认无强认证，靠 IP 限制。exports 限定网段、用 root_squash、防火墙只放行可信 IP。生产敏感数据用 Kerberos（sec=krb5）或换对象存储。
:::

## 相关命令

[mount/fstab](./mount-umount) · [firewall-cmd](/commands/network/firewall-cmd) · [MinIO 对象存储](/services/storage-search/minio) · [ss](/commands/network/ss)

## 官方文档

- NFS：<https://man7.org/linux/man-pages/man5/exports.5.html>
- mount.nfs：<https://man7.org/linux/man-pages/man5/nfs.5.html>