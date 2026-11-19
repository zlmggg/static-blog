---
title: "系统解析配置 · hosts/resolv.conf/nsswitch"
description: "/etc/hosts 静态映射、/etc/resolv.conf DNS 服务器、/etc/nsswitch.conf 解析顺序、systemd-resolved。排「解析走哪条路」，中文详解。"
---

# 系统解析配置 · hosts/resolv.conf/nsswitch

> 命令手册 · [网络](/commands/network/) ｜ 主题页
> 程序解析域名走哪条路、问哪个 DNS、hosts 优先生效吗——由这几个配置文件决定。

## 一句话用途

理解并配置系统名称解析的顺序与 DNS 服务器。

## 三个关键文件

### /etc/hosts（静态映射）

```text
127.0.0.1   localhost
10.0.0.11   db01 db01.example.com
10.0.0.12   redis01
```

优先级通常最高（nsswitch 里 files 在前）。内网无 DNS 时用 hosts 互相解析。

### /etc/resolv.conf（DNS 服务器）

```text
nameserver 10.0.0.2
nameserver 223.5.5.5
search example.com
options timeout:2 attempts:2
```

- `nameserver`：DNS 服务器（最多3个，按序问）。
- `search`：短名补全的搜索域。
- 常被 NetworkManager/systemd-resolved/cloud-init 覆盖，手改可能失效。

### /etc/nsswitch.conf（解析顺序）

```text
hosts: files dns myhostname
passwd: files sss
```

`hosts: files dns` 表示先查 hosts 再查 DNS。getent 走这里，dig 不走。

## systemd-resolved

```bash
resolvectl status                  # 看每网卡 DNS 与域
cat /etc/resolv.conf               # 可能指向 127.0.0.53（resolved  stub）
sudo resolvectl dns eth0 10.0.0.2  # 设某网卡 DNS
```

resolved 监听 127.0.0.53，resolv.conf 指向它，它再按网卡转发到真实 DNS。

## 运维实战

**内网互解析**：无 DNS 时各机 /etc/hosts 写全集群映射（或用 [DNS 服务](/services/web/dns)/Ansible 统一分发）。
**排解析慢**：resolv.conf 第一个 nameserver 不通会等超时才问第二个，调 options timeout。
**手改被覆盖**：用 nmcli 设 DNS（[nmcli](./nmcli)）而非手改 resolv.conf。

## 相关命令

[dig](./dig) · [nslookup/host/getent](./nslookup-host) · [nmcli](./nmcli) · [DNS 服务](/services/web/dns)

## 官方文档

- resolv.conf：<https://man7.org/linux/man-pages/man5/resolv.conf.5.html>
- nsswitch：<https://man7.org/linux/man-pages/man5/nsswitch.conf.5.html>
- resolved：<https://www.freedesktop.org/software/systemd/man/latest/systemd-resolved.service.html>