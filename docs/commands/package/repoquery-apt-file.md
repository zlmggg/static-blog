---
title: "repoquery / apt-file · 查依赖与文件归属"
description: "dnf repoquery 查依赖/被依赖/包文件，apt-file 查未安装包的文件归属。排「缺哪个包/谁依赖它」必备，参数中文分级。"
---

# repoquery / apt-file · 查依赖与文件归属

> 命令手册 · [软件包管理](/commands/package/) ｜ 频率：偶尔用
> 不装包就能查"它依赖谁、谁依赖它、包里有哪些文件"。排依赖问题和找文件归属用。

## 一句话用途

装包前看清依赖关系，缺命令时反查该装哪个包。

## 高频场景速查

```bash
# RHEL 系（dnf repoquery，需 dnf-plugins-core）
dnf repoquery --requires nginx           # nginx 依赖哪些包
dnf repoquery --whatrequires openssl     # 谁依赖 openssl
dnf repoquery -l nginx                   # nginx 包的文件列表（未装也能查）
dnf repoquery --resolve --requires nginx # 递归解析全部依赖

# Debian 系
sudo apt install apt-file && sudo apt-file update
apt-file search bin/ifconfig             # 查文件属于哪个包（含未装）
apt-file list nginx                      # 包的文件列表
apt-cache depends nginx                  # 依赖
apt-cache rdepends nginx                 # 被依赖
```

## 参数详解

### 偶尔用

| 命令 | 含义 |
|---|---|
| `repoquery --requires` | 查依赖 |
| `repoquery --whatrequires` | 查被依赖（卸载前必看） |
| `repoquery -l` | 包文件列表 |
| `apt-file search` | 文件归属（含未装包） |
| `apt-cache depends/rdepends` | 依赖/被依赖 |

::: tip 易错点
`rpm -qf` 只能查**已装**文件归属；`apt-file`/`repoquery -l` 能查**未装**包。卸载某包前先 `--whatrequires` 看谁依赖它，避免连带删掉关键服务。
:::

## 运维实战

**"编译报缺 libssl.so，装哪个包？"**：`dnf provides */libssl.so*` 或 `apt-file search libssl.so` → openssl-devel / libssl-dev。

**"能卸 openssl 吗？"**：`dnf repoquery --whatrequires openssl` 看一堆包依赖它，别卸。

## 相关命令

[dnf/yum](./dnf-yum) · [apt](./apt) · [rpm/dpkg](./rpm-dpkg) · [ldconfig](./ldconfig)

## 官方文档

- repoquery：<https://dnf.readthedocs.io/en/latest/command_ref.html#repoquery-command>
- apt-file：<https://manpages.debian.org/bookworm/apt-file/apt-file.1.en.html>