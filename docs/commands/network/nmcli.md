---
title: "nmcli · NetworkManager 网络配置"
description: "nmcli 配静态 IP/DNS/网关、看连接与设备、启停连接、配 bond/vlan。RHEL 系网络配置主力，中文详解。"
---

# nmcli · NetworkManager 网络配置

> 命令手册 · [网络](/commands/network/) ｜ 频率：偶尔用
> RHEL/Rocky 用 NetworkManager 管网络，nmcli 是它的命令行。配静态 IP、改 DNS、看连接状态都靠它。

## 一句话用途

配置和管理网络连接：IP/DNS/网关、启停连接、查看设备状态。

## 高频场景速查

```bash
nmcli device status                  # 设备状态
nmcli connection show                # 所有连接
nmcli connection show "ens192"       # 某连接详情
sudo nmcli connection modify "ens192" ipv4.addresses 10.0.0.11/24
sudo nmcli connection modify "ens192" ipv4.gateway 10.0.0.1
sudo nmcli connection modify "ens192" ipv4.dns "10.0.0.2 223.5.5.5"
sudo nmcli connection modify "ens192" ipv4.method manual    # 静态
sudo nmcli connection up "ens192"    # 重启连接生效
sudo nmcli connection modify "ens192" ipv4.method auto      # DHCP
nmcli networking off/on              # 总开关
```

## 关键概念

- **device**：物理/虚拟网卡（ens192/eth0）。
- **connection**：配置profile，绑到 device。一个设备可有多 profile。
- **ipv4.method**：manual（静态）/auto（DHCP）。
- 改完要 `connection up` 或 `device reapply` 生效。

## 运维实战

**配静态 IP**：modify addresses/gateway/dns + method manual + up。
**加多个 IP**：`+ipv4.addresses 10.0.0.12/24`（+ 追加）。
**配 DNS 搜索域**：`ipv4.dns-search example.com`。
**远程改网络防失联**：用 `nmcli` 而非直接改文件，改错可控制台救；或先加临时 IP 测试。

::: tip 易错点
nmcli 改的是 NetworkManager 配置，别同时手改 /etc/sysconfig/network-scripts 或 systemd-networkd，会冲突。云主机网络多由 cloud-init 管，改前确认。
:::

## 相关命令

[ip](./ip-addr-link) · [ifconfig/bridge](./ifconfig-bridge-networkctl) · [resolvectl](./nslookup-host) · [ethtool](./ethtool)

## 官方文档

- nmcli：<https://networkmanager.dev/docs/api/latest/nmcli.html>
- NetworkManager：<https://networkmanager.dev/>