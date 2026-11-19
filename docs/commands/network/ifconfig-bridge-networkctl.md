---
title: "ifconfig / bridge / networkctl · 接口与桥接"
description: "ifconfig 旧接口配置（已被 ip 取代）、bridge 看网桥/FDB、networkctl 看 systemd-networkd。容器/虚拟化网络基础，中文详解。"
---

# ifconfig / bridge / networkctl · 接口与桥接

> 命令手册 · [网络](/commands/network/) ｜ 频率：很少用
> ifconfig 是老工具（认得即可，配置用 ip）；bridge 看网桥转发表，容器/虚机网络常打交道；networkctl 管 systemd-networkd。

## 一句话用途

查看/配置网络接口与网桥（旧工具与桥接专用）。

## 高频场景速查

```bash
ifconfig                     # 看接口（旧，= ip addr）
ifconfig eth0                # 看某接口
sudo ifconfig eth0 up/down   # 启停接口（= ip link set）
bridge link                  # 看网桥端口
bridge fdb show              # 看转发表（MAC→端口）
bridge vlan show             # 看 VLAN
networkctl                   # systemd-networkd 接口状态
networkctl status eth0       # 某接口详情
```

## ifconfig → ip 对照

| ifconfig | ip 替代 |
|---|---|
| `ifconfig` | `ip addr` |
| `ifconfig eth0 up` | `ip link set eth0 up` |
| `ifconfig eth0 10.0.0.11/24` | `ip addr add 10.0.0.11/24 dev eth0` |
| `ifconfig eth0 mtu 9000` | `ip link set eth0 mtu 9000` |

## bridge（容器/虚机网络）

Docker/KVM 用网桥连通容器/虚机与外部：

```bash
bridge fdb show br docker0       # docker0 网桥的 MAC 表
ip link show type bridge         # 看所有网桥
brctl show                       # 旧工具（bridge-utils）
```

## 运维实战

**容器网络排查**：`bridge fdb show` 看容器 MAC 学到没，`ip link` 看 veth 对端。
**虚机网络**：KVM 网桥 br0 上 `bridge link` 看 tap 设备绑定。
**老系统应急**：没 ip 命令时用 ifconfig 临时配 IP。

::: tip 优先用 ip
ifconfig（net-tools）已停止维护，新系统默认不装。ip（iproute2）功能更全、默认有。认得 ifconfig 输出即可，配置统一用 ip/nmcli。
:::

## 相关命令

[ip](./ip-addr-link) · [nmcli](./nmcli) · [ethtool](./ethtool) · [Docker 网络](/services/container/docker/03-功能)

## 官方文档

- ifconfig：<https://man7.org/linux/man-pages/man8/ifconfig.8.html>
- bridge：<https://man7.org/linux/man-pages/man8/bridge.8.html>
- networkctl：<https://www.freedesktop.org/software/systemd/man/latest/networkctl.html>