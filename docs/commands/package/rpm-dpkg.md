---
title: "rpm / dpkg · 底层包查询"
description: "rpm/dpkg 查包内容、验文件完整性、查文件归属、解包不安装。--help 参数按频率中文分级，排「这个文件哪个包装的」必备。"
---

# rpm / dpkg · 底层包查询

> 命令手册 · [软件包管理](/commands/package/) ｜ 频率：偶尔用
> dnf/apt 的底层包工具。日常装包用 [dnf](./dnf-yum)/[apt](./apt)，rpm/dpkg 用来**查包内容、验完整性、反查文件归属**。

## 一句话用途

不联网也能查"装了哪个版本、这个文件属于哪个包、包里的文件有没有被改过"。

## 高频场景速查

```bash
# RHEL 系
rpm -qa | grep nginx                 # 查已装包
rpm -qi nginx                        # 包详情
rpm -ql nginx                        # 包安装的所有文件
rpm -qf /usr/sbin/nginx              # 反查文件属于哪个包
rpm -V nginx                         # 校验文件是否被改（输出空=没改）

# Debian 系
dpkg -l | grep nginx                 # 查已装包
dpkg -s nginx                        # 包详情
dpkg -L nginx                        # 包安装的文件
dpkg -S /usr/sbin/nginx              # 反查文件归属
sudo dpkg -i pkg.deb                 # 本地装 .deb
dpkg -c pkg.deb                      # 看 .deb 内容（不装）
```

## 参数详解（按频率分级）

### 偶尔用

| rpm | dpkg | 含义 |
|---|---|---|
| `-qa` | `-l` | 列已装包 |
| `-qi` | `-s` | 包详情 |
| `-ql` | `-L` | 包的文件列表 |
| `-qf` | `-S` | 文件归属反查 |
| `-V` | `--verify` | 校验文件完整性 |
| `-ivh` | `-i` | 本地装包 |
| `-e` | `-r` | 卸载 |

### 很少用

| rpm | dpkg | 含义 |
|---|---|---|
| `-qp xxx.rpm` | `-c xxx.deb` | 查未安装的包文件 |
| `--nodeps` | `--force-depends` | 忽略依赖（高危，慎用） |
| `-U` | — | 升级安装 |

::: tip 易错点
`rpm -V` 输出 `S.5....T.` 表示文件大小/MD5/修改时间变了——配置被改过或文件损坏，排障时很有用。`--nodeps` 强装会破坏依赖关系，除非明确知道后果否则别用。
:::

## 运维实战

**"ifconfig 命令没有，装哪个包？"**：`dnf provides */ifconfig` 或 `yum whatprovides */ifconfig` 反查（net-tools）。已装的文件用 `rpm -qf $(which ifconfig)`。

**怀疑配置文件被改**：`rpm -V nginx` 看哪些文件偏离了包原始状态。

## 相关命令

[dnf/yum](./dnf-yum) · [apt](./apt) · [repoquery/apt-file](./repoquery-apt-file)

## 官方文档

- rpm：<https://rpm.org/documentation.html>
- dpkg：<https://manpages.debian.org/bookworm/dpkg/dpkg.1.en.html>