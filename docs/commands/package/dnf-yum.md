---
title: "dnf / yum · RHEL 系包管理"
description: "dnf/yum 安装卸载更新、查包查依赖、仓库管理、锁版本、清缓存、离线下载。--help 参数按使用频率中文分级，含换源与内网源实战。"
---

# dnf / yum · RHEL 系包管理

> 命令手册 · [软件包管理](/commands/package/) ｜ 频率：每天用
> RHEL/Rocky/CentOS/Fedora 的包管理器。yum 是旧称，RHEL 8+ 底层已是 dnf（命令兼容）。Debian/Ubuntu 用 [apt](./apt)。

## 一句话用途

装软件、卸软件、更新、查依赖、管仓库——运维装环境的起点。

## 高频场景速查（复制即用）

```bash
sudo dnf install -y nginx              # 装包（-y 免确认）
sudo dnf remove -y nginx               # 卸载
sudo dnf update -y                     # 更新全部
sudo dnf search keyword                # 搜包
sudo dnf info nginx                    # 看包详情
sudo dnf list installed                # 已装列表
sudo dnf provides */ifconfig           # 查某文件属于哪个包
sudo dnf clean all                     # 清缓存
```

## 参数详解（按频率分级）

### 每天用

| 命令/参数 | 含义 |
|---|---|
| `install -y` | 安装，-y 自动确认 |
| `remove` | 卸载（保留配置） |
| `update` / `upgrade` | 更新包 |
| `search` | 按名/描述搜 |
| `info` | 包版本/大小/依赖 |
| `provides */文件名` | 反查文件归属（缺命令时找包） |

### 偶尔用

| 命令/参数 | 含义 |
|---|---|
| `reinstall` | 重装（修复损坏文件） |
| `downgrade` | 降级到旧版 |
| `history` / `history undo N` | 看/回滚事务 |
| `groupinstall "Development Tools"` | 装包组 |
| `--downloadonly --downloaddir=./` | 只下载不装（离线用） |
| `versionlock add nginx` | 锁版本防误更新 |

### 很少用

| 命令/参数 | 含义 |
|---|---|
| `autoremove` | 清不再被依赖的包 |
| `distro-sync` | 对齐仓库版本 |
| `--enablerepo=xxx` | 临时启用某仓库 |
| `--disablerepo=* --enablerepo=local` | 只用内网源 |

::: tip 易错点
`remove` 不会删配置文件（/etc 下保留），要彻底清用 `dnf remove` 后手动删配置。`update` 可能升内核，生产先 `versionlock` 锁住关键包。
:::

## 运维实战

**换阿里云源**（加速）：

```bash
sudo sed -i 's|^mirrorlist=|#mirrorlist=|g; s|^#baseurl=http://mirror.centos.org|baseurl=https://mirrors.aliyun.com|g' /etc/yum.repos.d/*.repo
sudo dnf clean all && sudo dnf makecache
```

**离线装包**：有网机 `dnf install --downloadonly --downloaddir=./pkgs nginx`，拷到内网 `sudo dnf localinstall ./pkgs/*.rpm`。

## 相关命令

[rpm](./rpm-dpkg) 查包内容 · [仓库配置](./repo-config) · [apt](./apt)（Debian 系） · [make/gcc](./make-gcc) 源码编译

## 官方文档

- DNF：<https://dnf.readthedocs.io/en/latest/>
- DNF 命令参考：<https://dnf.readthedocs.io/en/latest/command_ref.html>