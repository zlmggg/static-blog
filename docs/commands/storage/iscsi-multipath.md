---
title: "iscsiadm / multipath · iSCSI 与多路径"
description: "iscsiadm 发现/登录 iSCSI 目标、multipath 多路径聚合冗余。SAN 存储接入，中文详解。"
---

# iscsiadm / multipath · iSCSI 与多路径

> 命令手册 · [磁盘与存储](/commands/storage/) ｜ 频率：很少用
> 企业 SAN 存储常通过 iSCSI 把远程块设备映射成本地盘。multipath 把多条路径聚合，防单链路故障。

## 一句话用途

连接 iSCSI 网络存储，配置多路径冗余。

## iSCSI 客户端

```bash
sudo dnf install -y iscsi-initiator-utils
sudo systemctl enable --now iscsid
# 发现目标
sudo iscsiadm -m discovery -t sendtargets -p 10.0.0.5
# 登录
sudo iscsiadm -m node --login
# 看会话
sudo iscsiadm -m session
lsblk                          # 出现新盘（如 sdb）
# 登出
sudo iscsiadm -m node --logout
```

## multipath 多路径

```bash
sudo dnf install -y device-mapper-multipath
sudo mpathconf --enable
sudo systemctl enable --now multipathd
sudo multipath -ll             # 看多路径设备与路径状态
```

多条物理路径到同一 LUN，multipath 聚合成 /dev/mapper/mpathX，一条断了自动切换。

## 运维实战

**接入 SAN**：discovery→login→lsblk 见新盘→（multipath 聚合）→mkfs/挂载或做 LVM。
**路径故障切换**：multipath -ll 看 failed/faulty 路径，排查交换机/网卡。
**持久化**：iscsi 节点设 automatic 启动自动登录，fstab 用 _netdev。

::: tip 易错点
iSCSI 盘 fstab 必须 _netdev（等网络），否则开机挂载失败。multipath 下用 /dev/mapper/mpathX 而非 /dev/sdX（后者是单路径）。
:::

## 相关命令

[lsblk](./lsblk-blkid-findmnt) · [lvm-create](./lvm-create) · [fstab](./fstab) · [NFS](./nfs) · [smartctl](./smartctl)

## 官方文档

- iscsiadm：<https://man7.org/linux/man-pages/man8/iscsiadm.8.html>
- multipath：<https://man7.org/linux/man-pages/man8/multipath.8.html>