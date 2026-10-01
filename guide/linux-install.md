---
category: Linux
difficulty: 初级
---

# 安装与初始环境

::: tip 本篇定位
从零装好 Linux 并完成基础配置，最终能通过 SSH 远程连接、装好常用工具。
RHEL 系（CentOS / Rocky / AlmaLinux / RHEL）与 Debian 系（Debian / Ubuntu）的差异用代码组切换。
:::

## 一、发行版选择

### 两大阵营

| 阵营 | 代表发行版 | 包管理 | 特点 |
|---|---|---|---|
| **RHEL 系** | RHEL（商业付费）、**Rocky Linux / AlmaLinux**（RHEL 兼容、免费）、CentOS Stream（RHEL 上游、滚动）、Fedora（尝鲜） | `dnf` / `yum` | 稳定、企业生产环境占比高，资料里常说的"CentOS 7/8"即此系 |
| **Debian 系** | **Debian**（极致稳定）、**Ubuntu**（桌面/云友好，基于 Debian） | `apt` | 软件包新、社区活跃、云主机默认镜像多 |

> CentOS 8 已于 2021 年底停止维护，新机器建议用 **Rocky Linux / AlmaLinux**（RHEL 兼容）或 **Ubuntu Server LTS**。

### 选择建议

- **生产服务器 / 企业运维**：Rocky/AlmaLinux 或 Ubuntu LTS（长期支持版，如 Ubuntu 22.04/24.04）。
- **学习**：两个阵营都要会，工作中常同时遇到；本地先装一个 Ubuntu 或 Rocky 即可。
- **CPU 架构**：`x86_64`（主流 PC / 服务器）；`aarch64`（ARM64，如鲲鹏、树莓派、Apple Silicon 上的 ARM 虚拟机）。用 `uname -m` 查看。

### 查看当前系统版本

```bash
cat /etc/os-release      # 发行版信息（两系通用）
uname -r                 # 内核版本
uname -m                 # CPU 架构
```

## 二、虚拟机安装

### 1. 虚拟化软件

| 软件 | 适用平台 | 说明 |
|---|---|---|
| VMware Workstation Pro | Windows | 个人现已免费，功能强，最常用 |
| VMware Fusion | macOS | Intel / Apple Silicon 均有 |
| VirtualBox | 全平台 | 免费开源 |
| Parallels Desktop | macOS（M 芯片） | ARM 虚拟机体验好（付费） |

### 2. 资源规划（新建虚拟机）

| 资源 | 最低 | 建议 |
|---|---|---|
| CPU | 1 核 | 2 核及以上 |
| 内存 | 1 GB | 2 GB（带图形界面 4 GB） |
| 磁盘 | 20 GB | 40–50 GB，选"动态分配/精简置备"（用多少占多少） |
| 网络 | — | 见下方网络模式 |

**网络模式（重点）：**

- **NAT**（默认）：虚拟机通过宿主机共享上网，可访问外网，但局域网其他机器默认访问不到它。适合只在本机学习。
- **桥接（Bridged）**：虚拟机相当于局域网里一台独立机器，拥有和宿主机同网段的 IP，**局域网其他机器（含你的电脑）能直接连它**。做服务器、想从别的设备 SSH 连接时选这个。
- **仅主机（Host-Only）**：只能和宿主机互通，不能上外网。

### 3. 安装系统

1. 下载 ISO 镜像（见各官网：[Rocky](https://rockylinux.org/download)、[AlmaLinux](https://almalinux.org/get-almalinux/)、[Ubuntu](https://ubuntu.com/download/server)、[Debian](https://www.debian.org/distrib/)）。
2. 在虚拟机设置里把 ISO 挂载到"CD/DVD"，开机。
3. 选择 **Install**（RHEL 系）或进入 Ubuntu/Debian 安装向导。
4. 安装类型选 **最小化安装（Minimal Install / Ubuntu Server）**，不装图形界面，省资源、贴近服务器。
5. 磁盘分区：新手选**自动分区（LVM）**；想手动可参考第七节。
6. 设置 **root 密码**，并创建一个普通用户（建议勾选加入管理员/ wheel/sudo 组）。
7. 安装完成后重启，用 root 或普通用户登录。

::: details 最小化安装后没有图形界面，怎么操作？
服务器本就不需要图形界面，全部用命令行操作。宿主机通过 SSH 远程连接（见第五节），在你熟悉的终端窗口里敲命令即可。
:::

## 三、安装后基础配置

### 1. 配置网络（静态 IP）

先查看网卡名称和当前 IP：

```bash
ip addr            # 简写 ip a，记下网卡名（如 ens33、eth0、enp0s3）
```

**方法一：`nmtui`（最简单，推荐新手）**

在装有 NetworkManager 的系统（RHEL 系默认、Ubuntu 桌面版）执行 `nmtui`，方向键操作：
`Edit a connection` → 选网卡 → `Edit` → 把 IPv4 改为 `Manual` → 填 Address（如 `192.168.3.210/24`）、Gateway、DNS → 勾选 `Automatically connect` → 保存退出，再执行：

```bash
nmcli connection reload
nmcli connection up ens33      # ens33 换成你的网卡名
```

**方法二：配置文件**

::: code-group
```bash [RHEL 系]
# RHEL 9 起由 NetworkManager 管理，配置在：
ls /etc/NetworkManager/system-connections/
# 也可用 nmtui 自动生成；旧版 RHEL/CentOS 7 在：
#   /etc/sysconfig/network-scripts/ifcfg-ens33
# 关键参数：BOOTPROTO=static、IPADDR、NETMASK、GATEWAY、DNS1、ONBOOT=yes
systemctl restart NetworkManager
```
```bash [Debian/Ubuntu]
# Ubuntu 18.04+ 使用 netplan：
ls /etc/netplan/                 # 形如 00-installer-config.yaml
sudo vim /etc/netplan/00-installer-config.yaml
```
```yaml [netplan 配置示例]
network:
  version: 2
  renderer: networkd
  ethernets:
    ens33:                       # 换成你的网卡名
      dhcp4: no
      addresses: [192.168.3.210/24]
      routes:
        - to: default
          via: 192.168.3.1
      nameservers:
        addresses: [223.5.5.5, 114.114.114.114]
```
```bash [应用 netplan]
sudo netplan apply
ip addr show ens33
```
:::

### 2. 主机名

```bash
hostname                                  # 查看
sudo hostnamectl set-hostname myblog      # 设置主机名为 myblog
# 设置后重新登录，提示符即变为 user@myblog
```

### 3. 时区与时间同步

```bash
timedatectl                               # 查看时间、时区、NTP 状态
sudo timedatectl set-timezone Asia/Shanghai   # 设置时区为上海
```

开启网络时间同步（NTP）：

::: code-group
```bash [RHEL 系]
# RHEL 系默认用 chrony
sudo dnf install -y chrony
sudo systemctl enable --now chronyd
chronyc sources -v          # 查看时间源，^* 表示已同步
```
```bash [Debian/Ubuntu]
# Ubuntu 默认 systemd-timesyncd，也可改装 chrony
sudo timedatectl set-ntp true
timedatectl | grep "NTP"
sudo apt install -y chrony     # （可选）改用 chrony
chronyc sources -v
```
:::

### 4. 验证网络连通

```bash
ping -c 4 www.baidu.com      # 能 ping 通说明外网 + DNS 正常
ip route                     # 查看默认网关
```

::: warning
ping 不通但 IP 能配好，优先检查：网关是否正确、DNS 是否能解析、网络模式是否选对（桥接/NAT）。
:::

## 四、配置软件源（换国内源）

新装系统默认源在国外，下载慢，换成阿里云/清华镜像。

::: code-group
```bash [RHEL 系]
# 1) 安装 EPEL 扩展源（很多工具在 EPEL 里）
sudo dnf install -y epel-release
# 2) 备份原有源
sudo mkdir -p /etc/yum.repos.d/bak
sudo mv /etc/yum.repos.d/*.repo /etc/yum.repos.d/bak/ 2>/dev/null
# 3) 下载阿里云源（以 Rocky 9 为例，其他版本去 mirrors.aliyun.com 选对应文件）
sudo curl -o /etc/yum.repos.d/Rocky.repo https://mirrors.aliyun.com/repo/Rocky9.repo
sudo curl -o /etc/yum.repos.d/epel.repo  https://mirrors.aliyun.com/repo/epel-9.repo
# 4) 重建缓存并更新
sudo dnf clean all
sudo dnf makecache
sudo dnf -y update
```
```bash [Debian/Ubuntu]
# 1) 备份
sudo cp /etc/apt/sources.list /etc/apt/sources.list.bak 2>/dev/null
# 2) 一键替换为阿里云源（Ubuntu，版本代号用 lsb_release -cs 查看，如 jammy/noble）
sudo sed -i 's@//.*archive.ubuntu.com@//mirrors.aliyun.com@g' /etc/apt/sources.list 2>/dev/null
sudo sed -i 's@//.*security.ubuntu.com@//mirrors.aliyun.com@g' /etc/apt/sources.list 2>/dev/null
#    Debian 则替换为：deb https://mirrors.aliyun.com/debian/ 版本代号 main
# 3) 更新索引并升级
sudo apt update
sudo apt -y upgrade
```
:::

> 各发行版/版本对应的源文件不同，最稳妥是到镜像站按自己版本复制：
> [阿里云镜像站](https://mirrors.aliyun.com/)、[清华大学镜像站](https://mirrors.tuna.tsinghua.edu.cn/)。
> Ubuntu 24.04 的源文件可能在 `/etc/apt/sources.list.d/ubuntu.sources`（deb822 格式），同样把域名替换为镜像站即可。

## 五、SSH 远程连接

### 1. 安装并启动 SSH 服务

::: code-group
```bash [RHEL 系]
# RHEL 系最小安装一般已带 openssh-server
sudo systemctl enable --now sshd
sudo systemctl status sshd        # active (running) 即正常
```
```bash [Debian/Ubuntu]
sudo apt update
sudo apt install -y openssh-server
sudo systemctl enable --now ssh     # 注意 Debian 系服务名是 ssh
sudo systemctl status ssh
```
:::

确认 22 端口在监听：

```bash
ss -tlnp | grep :22
```

### 2. 用终端工具连接

常用终端：Windows 自带 `ssh` / Windows Terminal、MobaXterm、Xshell、FinalShell；macOS 直接用"终端"。

```bash
ssh 用户名@服务器IP
# 例如：
ssh wiki@192.168.3.210
# 首次连接输入 yes，再输入密码
```

### 3. 配置密钥免密登录（推荐）

密码登录每次要输入且不安全，密钥登录更方便安全。

```bash
# ① 在你自己的电脑（客户端）生成密钥对，一路回车
ssh-keygen -t ed25519
# ② 把公钥上传到服务器（最简单）
ssh-copy-id wiki@192.168.3.210
# ③ 之后再 ssh 登录无需密码
ssh wiki@192.168.3.210
```

::: details 没有 ssh-copy-id 时，手动配置
```bash
# 在客户端查看公钥内容
cat ~/.ssh/id_ed25519.pub
# 登录服务器，把公钥内容追加到 authorized_keys
mkdir -p ~/.ssh && chmod 700 ~/.ssh
vim ~/.ssh/authorized_keys      # 粘贴公钥，保存
chmod 600 ~/.ssh/authorized_keys
```
:::

### 4. SSH 安全加固（可选，建议）

确认密钥能正常登录后，再编辑 `/etc/ssh/sshd_config`：

```bash
sudo vim /etc/ssh/sshd_config
```

```ini
PermitRootLogin no              # 禁止 root 直接登录（用普通用户 + sudo）
PasswordAuthentication no       # 确认密钥登录无误后，再关闭密码登录
PubkeyAuthentication yes
```

```bash
# 改完重启（RHEL 系 sshd / Debian 系 ssh）
sudo systemctl restart sshd 2>/dev/null || sudo systemctl restart ssh
```

::: warning
**务必先验证密钥能登录，再关闭密码登录**，否则可能把自己锁在外面。改配置时保留一个已登录的会话不要关，用于兜底。
:::

## 六、基础工具与帮助

### 1. 安装常用工具

::: code-group
```bash [RHEL 系]
sudo dnf install -y vim wget curl net-tools lrzsz bash-completion \
                    tree unzip telnet bind-utils
# bind-utils 提供 dig/nslookup/host；net-tools 提供 ifconfig/netstat
```
```bash [Debian/Ubuntu]
sudo apt install -y vim wget curl net-tools lrzsz bash-completion \
                    tree unzip telnet dnsutils
# dnsutils 提供 dig/nslookup/host
```
:::

| 工具 | 用途 |
|---|---|
| `vim` | 文本编辑器 |
| `wget` / `curl` | 下载 / 请求 |
| `net-tools` | `ifconfig`、`netstat`、`route`（旧命令集） |
| `iproute2` | `ip`、`ss`（新命令集，系统默认；推荐用 `ss` 替代 `netstat`、`ip a` 替代 `ifconfig`） |
| `lrzsz` | 终端里 `rz`/`sz` 上传下载小文件 |
| `bash-completion` | 命令/参数 Tab 补全 |
| `tree` | 树状显示目录 |
| `bind-utils`/`dnsutils` | `dig`、`nslookup`、`host` |

### 2. 如何获取帮助（必须学会）

```bash
man ls                # 查看命令手册（按 q 退出，/ 搜索）
man 5 passwd          # man 章节：1 普通命令，5 配置文件格式
ls --help             # 多数命令的简要帮助
info ls               # 另一种手册
```

- 记不住参数时，`命令 --help` 和 `man` 是最权威的资料。
- 软件自带文档在 `/usr/share/doc/`。

## 七、物理机安装（可选）

在真实服务器/裸机上安装，与虚拟机步骤基本一致，区别在启动介质和分区。

### 1. 制作启动 U 盘

- **Ventoy**（推荐）：装好后把多个 ISO 直接拷进 U 盘，开机选择即可，[ventoy.net](https://www.ventoy.net/cn/)。
- **Rufus**（Windows）：选择 ISO 写入 U 盘，[rufus.ie](https://rufus.ie/zh/)。
- **balenaEtcher**（跨平台/Mac）：[etcher.balena.io](https://etcher.balena.io/)。
- Linux 下可用 `dd`（危险，务必确认盘符，勿写错盘）：
  ```bash
  sudo dd if=xxx.iso of=/dev/sdX bs=4M status=progress
  ```

### 2. 从 U 盘启动

开机按启动菜单键（常见 F12 / F11 / F2 / Del，因品牌而异），选择从 U 盘启动；部分机器需先在 BIOS/UEFI 中关闭 **Secure Boot**。

### 3. 推荐分区方案（服务器）

| 挂载点 | 大小 | 说明 |
|---|---|---|
| `/boot/efi` | 200 MB–1 GB | UEFI 模式需要；Legacy 模式用 `/boot`（约 1 GB） |
| `swap` | 约等于内存（内存大可减小） | 交换分区 |
| `/` | 50 GB+ | 系统根分区 |
| `/data` | 剩余空间 | 数据单独分区（或用 LVM，便于后续扩容） |

> 生产环境建议用 **LVM** 管理系统/数据盘，后续扩容、加盘更灵活（存储相关见 [磁盘存储](./linux-storage)）。

## 相关速查

- [Linux 命令速查](/reference/linux-commands)
- [网络命令速查](/reference/network-commands)
