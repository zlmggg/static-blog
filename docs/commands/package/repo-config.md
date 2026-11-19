---
title: "仓库配置 · 换源与内网源"
description: "RHEL 系 .repo 与 Debian 系 sources 配置、换国内镜像源、搭内网 yum/apt 源、仓库优先级与 GPG 校验。运维加速与离线环境必备。"
---

# 仓库配置 · 换源与内网源

> 命令手册 · [软件包管理](/commands/package/) ｜ 频率：偶尔用
> 包从哪下载由仓库配置决定。默认官方源国内慢，换镜像源加速；内网离线环境要自建源。

## 一句话用途

告诉包管理器"去哪个地址下载包"，换源加速、内网自建源都靠它。

## RHEL 系（.repo）

`/etc/yum.repos.d/*.repo`，一个仓库一段：

```ini
[aliyun-base]
name=Aliyun Base
baseurl=https://mirrors.aliyun.com/rockylinux/9/BaseOS/x86_64/os/
enabled=1
gpgcheck=1
gpgkey=https://mirrors.aliyun.com/rockylinux/RPM-GPG-KEY-Rocky-9
```

```bash
sudo dnf clean all && sudo dnf makecache    # 换源后刷新
dnf repolist                                # 看启用的仓库
```

- `enabled=1` 启用，`gpgcheck=1` 校验签名（生产别关）。
- `priority`（需 dnf-plugins-core）数字越小优先级越高，防第三方源覆盖官方包。

## Debian 系（sources）

Ubuntu 24.04 用 deb822 格式 `/etc/apt/sources.list.d/ubuntu.sources`：

```text
Types: deb
URIs: https://mirrors.aliyun.com/ubuntu/
Suites: noble noble-updates noble-security
Components: main restricted universe multiverse
Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg
```

旧格式 `/etc/apt/sources.list`：`deb https://mirrors.aliyun.com/ubuntu/ noble main`。改完 `sudo apt update`。

## 内网自建源

- **RHEL**：把 RPM 放目录，`createrepo_c /path` 生成元数据，HTTP 暴露，客户端 baseurl 指向它。
- **Debian**：`dpkg-scanpackages . /dev/null | gzip > Packages.gz`，或用 apt-mirror 同步官方源。

## 常见坑

| 现象 | 原因 | 解法 |
|---|---|---|
| 换源不生效 | 没清缓存 | dnf clean all / apt update |
| GPG 校验失败 | key 没导入 | 导入对应 gpgkey |
| 404 | 版本代号写错 | 核对 rocky 9 / noble |
| 第三方包覆盖官方 | 没设优先级 | 配 priority |

## 相关命令

[dnf/yum](./dnf-yum) · [apt](./apt) · [rpm/dpkg](./rpm-dpkg)

## 官方文档

- DNF 仓库：<https://dnf.readthedocs.io/en/latest/conf_ref.html#repo-options>
- Ubuntu 源：<https://ubuntu.com/server/docs/package-management>