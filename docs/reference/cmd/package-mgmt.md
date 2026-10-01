# apt 与 dnf/yum 命令详解：Debian 系与 RHEL 系的包管理

> 本文是 [Linux 命令速查](../linux-commands#软件包管理) 中 `apt`、`dnf`/`yum` 的从 0 到 1 详解。
> 目标：把 Debian 系（apt）和 RHEL 系（dnf/yum）的安装、卸载、搜索、更新命令对照讲清楚，多看几遍后，你在不同发行版上都能装包。
> 环境依据：`apt` 2.4.14（Ubuntu 22.04 自带，Debian/Ubuntu 系）；`dnf`/`yum` 属 RPM 系包管理器（RHEL 8+/CentOS/Rocky 默认用 dnf，yum 是其软链；本机沙箱未安装，选项依据 dnf 官方 man）。

## 一、命令是干什么的

Linux 装软件本质是"从软件仓库下载包并解到系统里"。两大阵营命令不同：

- **Debian/Ubuntu 系**：用 **apt**（底层是 `dpkg`，包后缀 `.deb`）。Ubuntu、Debian、Mint 等。
- **RHEL/CentOS/Rocky/Fedora 系**：用 **dnf**（RHEL 8 起替代老的 `yum`，底层是 `rpm`，包后缀 `.rpm`）。命令上 `yum` 和 `dnf` 基本通用。

> 类比：apt 和 dnf 都是"应用商店的命令行版"，只是 Debian 系管 `.deb`、RHEL 系管 `.rpm`，两者仓库不通用。

核心动作对应关系：

| 动作 | Debian 系（apt） | RHEL 系（dnf/yum） |
|---|---|---|
| 刷新仓库列表 | `apt update` | `dnf check-update`（或 `dnf makecache`） |
| 安装包 | `apt install 包` | `dnf install 包` |
| 卸载包 | `apt remove 包` | `dnf remove 包` |
| 卸载并清依赖 | `apt autoremove` | `dnf autoremove` |
| 搜索包 | `apt search 关键词` | `dnf search 关键词` |
| 看包信息 | `apt show 包` | `dnf info 包` |
| 升级全部 | `apt upgrade` | `dnf upgrade` |
| 列出已装 | `apt list --installed` | `dnf list installed` |
| 查命令属于哪个包 | `dpkg -S 文件` | `dnf provides 文件` |

## 二、命令语法

```bash
# apt（Debian 系）
apt [选项] 子命令 [包名]...

# dnf（RHEL 系，yum 同语法）
dnf [选项] 子命令 [包名]...
```

- 日常交互推荐直接用 `apt`（而不是老的 `apt-get`/`apt-cache`），输出更友好；
- 安装/卸载/升级一般要加 `sudo`。

## 三、选项全表（对照 `apt --help` 与 dnf man）

### 1. apt 常用子命令（Debian 系）

| 子命令 | 中文含义 | 什么场景用 |
|---|---|---|
| `update` | 刷新可用包列表 | 装包前先跑（**最常用**） |
| `install 包` | 安装包 | 装软件 |
| `reinstall 包` | 重新安装 | 包损坏时 |
| `remove 包` | 卸载包（保留配置） | 卸载软件 |
| `purge 包` | 卸载并删配置 | 彻底卸载 |
| `autoremove` | 自动清理不再需要的依赖 | 定期跑 |
| `upgrade` | 升级所有已装包 | 系统更新 |
| `full-upgrade` | 升级（可处理依赖变化） | 大版本升级 |
| `search 关键词` | 按描述搜索包 | 不知道包名时 |
| `show 包` | 显示包详情 | 看包大小、版本 |
| `list` | 列出包（`--installed`/`--upgradable`） | 看已装/可升级 |
| `edit-sources` | 编辑软件源列表 | 换源时 |

### 2. dnf 常用子命令（RHEL 系，yum 通用）

| 子命令 | 中文含义 | 什么场景用 |
|---|---|---|
| `install 包` | 安装包 | 装软件 |
| `remove 包` | 卸载包 | 卸载 |
| `autoremove` | 清理无用依赖 | 定期跑 |
| `search 关键词` | 搜索包 | 找包 |
| `info 包` | 包详情 | 看包信息 |
| `list` | 列包（`installed`/`available`/`upgrades`） | 看已装/可升级 |
| `upgrade` | 升级所有包 | 系统更新 |
| `check-update` | 检查有无可升级（不安装） | 脚本里判断 |
| `repolist` | 列出已启用的仓库 | 看源配置 |
| `provides 文件` | 查某个文件属于哪个包 | 命令找不到时 |
| `clean all` | 清理缓存 | 缓存出问题时 |
| `makecache` | 生成仓库缓存 | 首次/换源后 |

## 四、由浅入深的典型示例

### 示例 1：Debian 系——装包前先更新列表

```bash
sudo apt update
sudo apt install -y nginx
```

```text
Reading package lists... Done
Building dependency tree... Done
The following NEW packages will be installed: nginx
...
```

> `apt update` 是刷新"有哪些版本可装"的清单；`-y` 表示自动确认 yes，脚本里常用。生产建议去掉 `-y` 先看一眼要装啥。

### 示例 2：Debian 系——搜索一个不知道名字的包

```bash
apt search mysql server
```

> 不知道确切包名时，用关键词搜，从描述里挑。

### 示例 3：Debian 系——卸载并清理

```bash
sudo apt remove nginx
sudo apt autoremove
```

> `remove` 删程序、`autoremove` 把当初为依赖而装、现在没人要的包清掉。

### 示例 4：Debian 系——升级全部

```bash
sudo apt update
sudo apt upgrade
```

> 先 `update` 再 `upgrade`，是日常安全更新的标准两步。

### 示例 5：RHEL 系——安装软件（dnf）

```bash
sudo dnf install -y nginx
```

示意输出（依据 dnf 官方文档，非本机实跑）：

```text
Last metadata expiration check: 0:12:33 ago.
Dependencies resolved.
=====================================================================
 Package        Arch   Version         Repository        Size
=====================================================================
Installing:
 nginx          x86_64 1:1.20.1.el8    @System           ...
Complete!
```

> RHEL 8 起 `yum` 命令被 `dnf` 取代，但 `yum` 仍是 dnf 的软链，老命令 `yum install` 也能跑。

### 示例 6：RHEL 系——搜索与查详情

```bash
dnf search nginx
dnf info nginx
```

> 和 apt 的 search/show 对应。

### 示例 7：RHEL 系——查命令属于哪个包

```bash
dnf provides /usr/bin/vim
```

示意输出：

```text
vim-enhanced-2:8.0.637-20.el8.x86_64 : A Vim...
Repo        : @System
Matched from:
Filename    : /usr/bin/vim
```

> 报错"command not found"但知道文件路径时，用 `provides` 反查该装哪个包。Debian 系对应 `dpkg -S /usr/bin/vim`。

### 示例 8：RHEL 系——看仓库列表

```bash
dnf repolist
```

> 列出 enabled 的 repo（baseos、appstream、epel 等）。第三方源（如 epel）没装好时装不到包。

### 示例 9：RHEL 系——升级全部

```bash
sudo dnf upgrade --refresh
```

> `--refresh` 先刷新元数据再升级。

## 五、高频组合速记

```bash
# Debian/Ubuntu 系
sudo apt update                 # 刷新列表
sudo apt install -y 包           # 安装
sudo apt remove 包               # 卸载
sudo apt autoremove             # 清依赖
sudo apt upgrade                # 升级全部
apt search 关键词               # 搜索
dpkg -S /usr/bin/文件           # 查文件属于哪个包

# RHEL/CentOS/Rocky 系
sudo dnf install -y 包          # 安装（yum install 同）
sudo dnf remove 包               # 卸载
sudo dnf autoremove             # 清依赖
sudo dnf upgrade                # 升级全部
dnf search 关键词               # 搜索
dnf provides /usr/bin/文件      # 反查文件
dnf repolist                    # 看仓库
```

## 六、RHEL 系与 Debian 系差异（总结）

- **包格式**：Debian 系 `.deb`（底层 dpkg）；RHEL 系 `.rpm`（底层 rpm）。
- **包管理器**：Debian 用 `apt`；RHEL 8+ 用 `dnf`（老版本用 `yum`）。
- **仓库配置**：Debian 系在 `/etc/apt/sources.list` 和 `/etc/apt/sources.list.d/`；RHEL 系在 `/etc/yum.repos.d/*.repo`。
- **第三方源**：Debian 常加 PPA；RHEL 常加 EPEL、Remi 等 repo。
- **服务管理**：都用 systemd（`systemctl`），与包管理器无关。

## 七、新手易错点

1. **装包前不 `apt update`**：会报"找不到包"或装到旧版本，先刷新列表。
2. **`apt upgrade` 和 `apt dist-upgrade` 分不清**：日常安全更新用 `upgrade`；要处理"必须卸掉某包才能升级"时用 `full-upgrade`/`dist-upgrade`。
3. **RHEL 上用 `yum` 还是 `dnf`**：RHEL 8+ 两者等价（yum 是 dnf 软链），但新脚本建议写 `dnf`。
4. **不知道包名就乱试**：先用 `search` 搜，或用 `provides` 反查，不要瞎猜包名。
5. **`apt remove` 不删配置**：想彻底清干净用 `apt purge`；`autoremove` 定期跑能省不少磁盘。
6. **随意加第三方源**：陌生源可能带恶意包或依赖冲突，生产环境只加可信源。
7. **容器里装包**：容器镜像层是只读的，装包会写在可写层；想永久固化应改 Dockerfile。

## 八、相关命令与文档

- 速查页：[Linux 命令速查](../linux-commands#软件包管理)
- 打包压缩：`tar`（详解见 [tar](./tar)）
- 看磁盘空间：`df`（详解见 [df](./df)）、`du`（详解见 [du](./du)）
- 系统初始化与软件安装思路：见 [Linux 安装专题](../../guide/linux-install)
