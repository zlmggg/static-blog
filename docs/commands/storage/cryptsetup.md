---
title: "cryptsetup · LUKS 磁盘加密"
description: "cryptsetup LUKS 加密分区、luksFormat/open/close、密钥槽管理、fstab crypttab 自动解锁。静态数据加密，中文详解。"
---

# cryptsetup · LUKS 磁盘加密

> 命令手册 · [磁盘与存储](/commands/storage/) ｜ 频率：很少用
> 笔记本/敏感数据盘要加密，防丢盘泄密。LUKS 是 Linux 标准磁盘加密，cryptsetup 管理。

## 一句话用途

创建和管理 LUKS 加密卷（静态数据加密）。

## 高频场景速查

```bash
sudo cryptsetup luksFormat /dev/sdb1       # 初始化加密（设密码，会清盘）
sudo cryptsetup open /dev/sdb1 cryptdata   # 解锁，映射到 /dev/mapper/cryptdata
sudo mkfs.xfs /dev/mapper/cryptdata        # 在映射设备上格式化
sudo mount /dev/mapper/cryptdata /data
sudo cryptsetup close cryptdata            # 关闭（锁定）
sudo cryptsetup luksDump /dev/sdb1         # 看密钥槽/头信息
sudo cryptsetup luksAddKey /dev/sdb1       # 加备用密码
```

## 自动解锁（crypttab）

```text
# /etc/crypttab
cryptdata  UUID=xxxx  /root/keyfile  luks
# /etc/fstab
/dev/mapper/cryptdata  /data  xfs  defaults,nofail  0 0
```

keyfile 避免开机输密码（但 keyfile 本身要保护，或绑 TPM）。

## 运维实战

**敏感数据盘加密**：luksFormat→open→mkfs→mount，盘丢了没密码读不出。
**多密码**：luksAddKey 加管理员备用密码（最多8槽）。
**性能**：现代 CPU 有 AES-NI，加密开销小（`grep aes /proc/cpuinfo` 确认）。

::: danger 密码丢了数据没了
LUKS 无后门，密码/密钥丢失数据不可恢复。luksAddKey 设备用密码，header 备份（luksHeaderBackup）防头损坏。
:::

## 相关命令

[mkfs](./mkfs) · [mount/fstab](./mount-umount) · [lsblk](./lsblk-blkid-findmnt) · [openssl](/commands/devtools/openssl)

## 官方文档

- cryptsetup：<https://gitlab.com/cryptsetup/cryptsetup>
- man：<https://man7.org/linux/man-pages/man8/cryptsetup.8.html>