---
title: "apt · Debian/Ubuntu 包管理"
description: "apt 安装卸载更新、查包查文件归属、仓库与源配置、锁版本、清缓存。--help 参数按频率中文分级，含换源实战。"
---

# apt · Debian/Ubuntu 包管理

> 命令手册 · [软件包管理](/commands/package/) ｜ 频率：每天用
> Debian/Ubuntu 的包管理器。apt 是面向交互的前端（底层 apt-get/dpkg）。RHEL 系用 [dnf/yum](./dnf-yum)。

## 一句话用途

装软件、卸软件、更新、查依赖、管源——Ubuntu 装环境的起点。

## 高频场景速查

```bash
sudo apt update                      # 刷新包索引（装前必跑）
sudo apt install -y nginx            # 装包
sudo apt remove -y nginx             # 卸载（留配置）
sudo apt purge -y nginx              # 卸载并删配置
sudo apt upgrade -y                  # 更新已装包
sudo apt search keyword              # 搜包
sudo apt show nginx                  # 包详情
apt list --installed                 # 已装列表
sudo apt autoremove                  # 清无用依赖
```

## 参数详解（按频率分级）

### 每天用

| 命令 | 含义 |
|---|---|
| `update` | 刷新索引（不升级包） |
| `install -y` | 安装 |
| `remove` / `purge` | 卸载 / 连配置删 |
| `upgrade` | 升级已装包 |
| `search` / `show` | 搜 / 看详情 |

### 偶尔用

| 命令/参数 | 含义 |
|---|---|
| `full-upgrade` | 升级并处理依赖变更（可删包） |
| `--reinstall install` | 重装 |
| `apt-mark hold nginx` | 锁版本 |
| `apt-file search bin/ifconfig` | 查文件归属（需装 apt-file） |
| `download nginx` | 只下载 .deb |
| `clean` / `autoclean` | 清下载缓存 |

### 很少用

| 命令 | 含义 |
|---|---|
| `source nginx` | 下源码包 |
| `build-dep nginx` | 装编译依赖 |
| `--no-install-recommends` | 不装推荐包（精简） |

::: tip 易错点
`apt update` 只刷索引不升级，`apt upgrade` 才升级——两步别混。`remove` 留配置、`purge` 删配置。换源后必须 `apt update` 才生效。
:::

## 运维实战

**换阿里云源**（Ubuntu 24.04 用 deb822 格式 `/etc/apt/sources.list.d/ubuntu.sources`，把 URI 改成 `https://mirrors.aliyun.com/ubuntu/`），然后 `sudo apt update`。

**离线装包**：有网机 `apt download nginx`（含依赖用 `apt-get download $(apt-cache depends --recurse nginx)`），拷到内网 `sudo dpkg -i *.deb`。

## 相关命令

[dpkg](./rpm-dpkg) · [仓库配置](./repo-config) · [apt-file 查归属](./repoquery-apt-file) · [dnf/yum](./dnf-yum)

## 官方文档

- apt：<https://manpages.ubuntu.com/manpages/noble/en/man8/apt.8.html>
- sources.list：<https://manpages.ubuntu.com/manpages/noble/en/man5/sources.list.5.html>