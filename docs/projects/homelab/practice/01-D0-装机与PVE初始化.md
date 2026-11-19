# 01 · D0：装机与 PVE 初始化

| 项目 | 内容 |
|---|---|
| **所属阶段** | D0（硬件到货当天） |
| **前置条件** | 硬件到齐；Windows 能上网；路由器 DHCP 池已缩到 `192.168.10.2–.99` |
| **预计耗时** | 2.5 小时（含 10 分钟压测） |
| **完成标志** | 模板 9000 可克隆 + thin 告警已启用 + 压测通过 + 配置已备份 |
| **下一步** | `02-D1-P0管理平面.md` |

> 本文所有命令都可整段复制。每个命令块第一行标了**在哪台机器、什么用户**执行。
> 屏幕操作（BIOS、安装向导）没有命令，给的是"菜单 → 选项 → 值"对照表。

---

## 本步需要的资料

| 类型 | 名称 | 从哪来 |
|---|---|---|
| 下载 | PVE ISO **9.2-1** | proxmox.com/downloads |
| 下载 | Rufus / balenaEtcher | rufus.ie |
| 仓库 | `02-PVE准备/` 下 8 个文件 | [资料清单](/projects/homelab/materials) |
| 环境 | Windows 的 OpenSSH 客户端 | 系统"可选功能" |

> 总表（含版本、下载地址、账号规则）见 [`00-资料清单.md`](/projects/homelab/materials)。

---

## 步骤 0 · 开始前准备（15 分钟）

**目的**：清点物料、准备好 Windows 这一侧，避免装到一半发现缺东西。

**开始前**：无。

**操作**：

1. 清点物料：

| 物料 | 要求 |
|---|---|
| U 盘 | ≥8G，用来写 PVE ISO（会清空） |
| 显示器 + 键盘 | 改 BIOS、装系统必须 |
| 网线 | PVE 到 mini 交换机 |
| 十字螺丝刀 | 装机 |

2. 下载 PVE 9.2 ISO：<https://www.proxmox.com/en/downloads> → `proxmox-ve_9.2-1.iso`
3. 用 **Rufus（DD 模式）** 或 **balenaEtcher** 写入 U 盘。
4. 在 Windows 上打开 PowerShell，确认 ssh 可用：

```powershell
# 在 Windows PowerShell 里执行
ssh -V
```

**应该看到**：类似 `OpenSSH_for_Windows_9.5p1` 的版本号。

**失败怎么办**：
- 提示 `ssh 不是内部或外部命令` → Windows 设置 → 应用 → 可选功能 → 添加"OpenSSH 客户端"
- 提示找不到命令但已安装 → 关掉 PowerShell 重开一次

---

## 步骤 1 · BIOS 设置（20 分钟）

**在哪台**：物理机，开机按 `Del` 进 BIOS
**目的**：让主板认满 128G 内存、开启虚拟化、锁定内存频率
**开始前**：机器已点亮，显示器有画面

**操作**：

1. 开机狂按 `Del`，进入 BIOS 设置界面。
2. 先看 **Main** 页，记下 `BIOS Version`（例如 `4.5`），写在纸上备用。
3. 找到 **Memory Information**（可能在 Main 或 Advanced 下），确认三项：

| 项目 | 必须是 |
|---|---|
| Total Memory | **131072 MB**（=128G） |
| Memory Frequency | **1600 MHz** |
| 识别条数 | **4 条** |

4. 按下面的对照表逐项修改（菜单名可能略有差异，按关键词找）：

| 要找的关键词 | 改成 | 作用 |
|---|---|---|
| Boot Mode | **UEFI** | 用 UEFI 装系统 |
| CSM | **Disabled** | UEFI 下必须关 |
| Secure Boot | **Disabled** | 少一层变量 |
| Fast Boot | **Disabled** | 便于 U 盘启动 |
| Intel Virtualization Technology / VT-x | **Enabled** | 虚拟化必需 |
| VT-d / IOMMU | **Enabled** | 以后直通用 |
| Above 4G Decoding | **Enabled** | 大 BAR、直通 |
| SATA Mode | **AHCI** | 不要 RAID |
| Memory Frequency | **1600** | 不要 Auto |
| Restore on AC Power Loss | **Power On** | 断电恢复自动开机 |
| Fan Control | **Full Speed / Smart Fan** | 散热优先 |

5. 按 `F10` 保存并退出（选 Yes）。

**应该看到**：机器重启。

**失败怎么办**：
- 内存只认 64G → **先别装系统**，关机重插内存，单条逐槽测（见步骤 1 备注）
- 找不到某个选项 → 在 BIOS 里按 `Ctrl+F` 搜索关键词
- 改完起不来 → 进 BIOS 恢复默认（Load Optimized Defaults），只改 VT-x 和启动模式

> **内存只认一半的排查顺序**：① 关机拔电 ② 四条全部拔下重插到底 ③ 只插 1 条开机看是否认 32G ④ 换槽位再试 ⑤ 四条分别单独测试，找出坏条。

---

## 步骤 2 · 安装 PVE（30 分钟）

**在哪台**：物理机，插 U 盘启动
**目的**：把 PVE 装到 64G SATA 上（**NVMe 先别接**）
**开始前**：U 盘已写好 ISO；机箱里只接了 64G SATA

**操作**：

1. 插 U 盘，开机按 `F11`（或 `F7`/`F8`，看主板）选 U 盘启动，**选带 UEFI 的那一项**。
2. 出现 PVE 安装菜单，选 **Install Proxmox VE (Graphical)**。
3. 按屏幕顺序走：

| 屏幕 | 选什么 |
|---|---|
| EULA | 点 `I agree` |
| Target Harddisk | 选 **64G 那块 SATA**（按容量认，别选错） |
| Country / Timezone | China / Asia/Shanghai |
| Keyboard | Chinese 或 English |
| Password | 设一个你能记住的 root 密码（**记下来**） |
| Email | 随便填，如 `root@lab.local` |
| Management Interface | 你的物理网卡（如 `enp3s0`） |
| Hostname | `pve-lab.local` |
| IP | `192.168.10.30/24` |
| Gateway | `192.168.10.1` |
| DNS | `192.168.10.1` |

4. 点 **Advanced options**，改这四项（不改会用整盘）：

| 项 | 值 |
|---|---|
| hdsize | **64** |
| swapsize | **4** |
| maxroot | **48** |
| minfree | **8** |

5. 点 `Next` → `Install`，等 5–10 分钟，看到 `Installation successful` 后点 `Reboot`，**拔掉 U 盘**。

**应该看到**：重启后屏幕出现 `pve-lab login:`。

**失败怎么办**：
- U 盘启动进不去 → 回 BIOS 把 Boot Mode 改 Legacy 再试
- 装完进不了系统 → 重新插 U 盘装一次，注意 Target Harddisk 别选错
- 忘记密码 → 重装（比找回快）

---

## 步骤 3 · 首次登录、上传文件、换源（20 分钟）

**在哪台**：Windows 的浏览器 + PowerShell
**目的**：能进 PVE 后台、把脚本传上去、换成国内源
**开始前**：PVE 已重启完成，网线插在交换机上

**操作**：

1. 浏览器打开 `https://192.168.10.30:8006`，用户名 `root`，Realm 选 `Linux PAM`，密码是步骤 2 设的。
   浏览器提示证书不安全 → 点"高级" → "继续访问"。

2. 点左侧 `pve-lab` → `Shell`，打开网页终端（后面很多命令在这里敲）。

3. 在 **Windows PowerShell** 里，把 8 个文件传到 PVE（会提示输入 root 密码）：

```powershell
# 在 Windows PowerShell 里执行（路径按你的仓库位置改）
cd ".\ops-project-files\02-PVE准备"
scp eip-apply.sh eip.service thin-alert.sh thin-alert.service thin-alert.timer `
    make-ubuntu2404-template.sh ubuntu-2404-vendor.yaml create-lab-vm.sh `
    root@192.168.10.30:/root/
```

**应该看到**：8 行 `100%` 的进度，没有报错。

4. 回到 PVE 的 Web Shell，确认文件到了：

```bash
# 在 PVE 上执行（root）
ls -l /root/*.sh /root/*.service /root/*.timer /root/*.yaml
```

**应该看到**：8 个文件，大小都不为 0。

5. 换源（中科大）+ 更新：

```bash
# 在 PVE 上执行（root）
cp -a /etc/apt/sources.list.d /root/sources.list.d.bak.$(date +%F)
rm -f /etc/apt/sources.list.d/*enterprise*
rm -f /etc/apt/sources.list.d/pve-enterprise.list

cat > /etc/apt/sources.list.d/debian.sources <<'EOF'
Types: deb
URIs: https://mirrors.ustc.edu.cn/debian
Suites: trixie trixie-updates
Components: main contrib non-free non-free-firmware
Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg

Types: deb
URIs: https://mirrors.ustc.edu.cn/debian-security
Suites: trixie-security
Components: main contrib non-free non-free-firmware
Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg
EOF

cat > /etc/apt/sources.list.d/pve-no-subscription.sources <<'EOF'
Types: deb
URIs: https://mirrors.ustc.edu.cn/proxmox/debian/pve
Suites: trixie
Components: pve-no-subscription
Signed-By: /usr/share/keyrings/proxmox-archive-keyring.gpg
EOF

apt update && apt full-upgrade -y
```

6. 装常用工具：

```bash
# 在 PVE 上执行（root）
apt install -y vim htop iotop iftop ncdu tree curl wget git unzip jq lsof strace stress-ng \
  net-tools bridge-utils dnsutils lm-sensors smartmontools nvme-cli sysstat chrony bash-completion
timedatectl set-timezone Asia/Shanghai
systemctl enable --now chrony
```

**应该看到**：`apt update` 最后显示 `Reading package lists... Done`，没有 `Failed to fetch`。

**失败怎么办**：
- `Could not resolve` → DNS 填错，检查 `/etc/resolv.conf` 是否为 `192.168.10.1`
- `Key is stored in legacy trusted.gpg` 警告 → 不影响，继续
- 某个镜像 404 → 把 `mirrors.ustc.edu.cn` 换成 `mirrors.tuna.tsinghua.edu.cn`

---

## 步骤 4 · 内核参数（10 分钟 + 一次重启）

**在哪台**：PVE（root）
**目的**：开 IOMMU（以后直通要用）、关掉性能损耗大的缓解补丁
**开始前**：步骤 3 的更新已完成

**操作**：

1. 改 GRUB：

```bash
# 在 PVE 上执行（root）
cp /etc/default/grub /etc/default/grub.bak
sed -i 's/^GRUB_CMDLINE_LINUX_DEFAULT=.*/GRUB_CMDLINE_LINUX_DEFAULT="quiet intel_iommu=on iommu=pt mitigations=off"/' /etc/default/grub
update-grub
update-initramfs -u -k all
```

2. 重启：

```bash
# 在 PVE 上执行（root）
reboot
```

3. 等 1 分钟，重新打开 Web Shell，检查：

```bash
# 在 PVE 上执行（root）
dmesg | grep -e DMAR -e IOMMU | head -5
```

**应该看到**：出现 `DMAR: IOMMU enabled` 之类的行。

**失败怎么办**：
- 没有任何输出 → `cat /proc/cmdline` 看参数是否生效；没有就重做第 1 步
- 起不来 → 在 GRUB 菜单按 `e` 临时删掉参数进系统，再改回来

---

## 步骤 5 · CPU 调频与内核行为（10 分钟）

**在哪台**：PVE（root）
**目的**：CPU 跑满频、尽量不用 swap、崩溃自动重启
**开始前**：步骤 4 已重启完成

**操作**：

```bash
# 在 PVE 上执行（root）
apt install -y linux-cpupower 2>/dev/null || true
cpupower frequency-set -g performance

cat > /etc/sysctl.d/99-lab.conf <<'EOF'
net.ipv4.ip_forward = 1
vm.swappiness = 10
vm.vfs_cache_pressure = 50
kernel.panic = 10
EOF
sysctl --system
```

**应该看到**：`sysctl --system` 最后几行显示 `net.ipv4.ip_forward = 1`。

**失败怎么办**：
- `cpupower: command not found` → 跳过，不影响后续
- 提示某个参数不存在 → 忽略那一行

---

## 步骤 6 · 建私网网桥 vmbr1（15 分钟）

**在哪台**：PVE（root）
**目的**：给虚拟机一块纯内网网卡（10.0.0.0/24），出口走 NAT
**开始前**：能 `ping 223.5.5.5` 通

**操作**：

1. 先备份并确认网卡名：

```bash
# 在 PVE 上执行（root）
cp /etc/network/interfaces /root/interfaces.bak.$(date +%F)
ip -br link
```

**应该看到**：两行以上，`lo` 和你自己的网卡（如 `enp3s0`）。

2. 追加 vmbr1 配置（**整段复制**）：

```bash
# 在 PVE 上执行（root）
cat >> /etc/network/interfaces <<'EOF'

auto vmbr1
iface vmbr1 inet static
    address 10.0.0.1/24
    bridge-ports none
    bridge-stp off
    bridge-fd 0
    post-up   iptables -t nat -A POSTROUTING -s 10.0.0.0/24 -o vmbr0 -j MASQUERADE
    post-down iptables -t nat -D POSTROUTING -s 10.0.0.0/24 -o vmbr0 -j MASQUERADE
    post-up   iptables -A FORWARD -i vmbr1 -o vmbr0 -j ACCEPT
    post-down iptables -D FORWARD -i vmbr1 -o vmbr0 -j ACCEPT
    post-up   iptables -A FORWARD -i vmbr0 -o vmbr1 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
    post-down iptables -D FORWARD -i vmbr0 -o vmbr1 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
EOF

ifreload -a
ip -4 a show vmbr1
```

**应该看到**：`inet 10.0.0.1/24`。

**失败怎么办**：
- `ifreload` 报错 → `cat /etc/network/interfaces` 检查缩进（每行 4 空格）和重复段落
- 改完 SSH 断了 → 接显示器键盘，用 `cp /root/interfaces.bak.* /etc/network/interfaces` 恢复

---

## 步骤 7 · EIP 池（15 分钟）

**在哪台**：PVE（root）
**目的**：把 6 个私网地址映射成 `192.168.10.x`，让 Windows 能访问
**开始前**：步骤 6 的 vmbr1 已通，`sysctl net.ipv4.ip_forward` = 1

**操作**：

1. 创建映射文件（**这个文件默认不存在，用下面命令创建**）：

```bash
# 在 PVE 上执行（root）
cat > /etc/eip.map <<'EOF'
100     # bastion
103     # jumpserver
119     # lvs vip
191     # grafana
200     # gitlab
210     # harbor
EOF

cat /etc/eip.map
```

**应该看到**：6 行，前面是数字，后面是注释。

2. 安装脚本和服务：

```bash
# 在 PVE 上执行（root）
install -m 755 /root/eip-apply.sh /usr/local/sbin/eip-apply.sh
install -m 644 /root/eip.service   /etc/systemd/system/eip.service
systemctl daemon-reload
systemctl enable --now eip.service
systemctl status eip.service --no-pager
```

**应该看到**：`Active: active (exited)`，以及日志里 `已应用 6 条映射`。

3. 验证：

```bash
# 在 PVE 上执行（root）
iptables -t nat -L EIP-DNAT -n -v
ip -4 addr show vmbr0 | grep 192.168.10.
```

**应该看到**：6 条 DNAT 规则，以及 6 个 `/32` 地址（100/103/119/191/200/210）。

**失败怎么办**：
- 规则是 0 条 → `journalctl -u eip.service -n 30 --no-pager` 看脚本报错
- 提示 `iptables: command not found` → `apt install -y iptables`
- 地址没加上 → 确认 `/etc/eip.map` 里没有中文标点

---

## 步骤 8 · Windows 加静态路由（5 分钟）

**在哪台**：Windows（管理员 PowerShell）
**目的**：让 Windows 知道去 `10.0.0.0/24` 的包交给 PVE
**开始前**：步骤 7 完成

**操作**：

1. 右键开始菜单 → **终端(管理员)** / PowerShell(管理员)。
2. 执行：

```powershell
# 在 Windows 管理员 PowerShell 里执行
route add 10.0.0.0 mask 255.255.255.0 192.168.10.30 -p
route print -4 | Select-String "10.0.0.0"
ping 10.0.0.1
```

**应该看到**：`ping` 有回复（`来自 10.0.0.1 的回复`）。

**失败怎么办**：
- `请求超时` → 回 PVE 看 `ip -4 a show vmbr1` 是否有 `10.0.0.1`
- `需要提升权限` → 确认是"管理员"打开的窗口

---

## 步骤 9 · SSH 密钥与加固（15 分钟）

**在哪台**：PVE（root）+ Windows
**目的**：① PVE 生成"给虚拟机用"的密钥（后面建机要用）② 你从 Windows 免密登录 PVE ③ 关掉密码登录
**开始前**：步骤 8 的 ping 已通

**操作**：

### 9.1 PVE 生成给 VM 用的密钥

```bash
# 在 PVE 上执行（root）
[ -f /root/.ssh/id_ed25519 ] || ssh-keygen -t ed25519 -N "" -f /root/.ssh/id_ed25519
ls -l /root/.ssh/id_ed25519*
```

**应该看到**：`id_ed25519`（私钥）和 `id_ed25519.pub`（公钥）两个文件。
这把**公钥**后面会被 cloud-init 注入到每一台虚拟机里。

### 9.2 Windows 生成你自己的密钥

```powershell
# 在 Windows PowerShell 里执行
ssh-keygen -t ed25519 -f "$env:USERPROFILE\.ssh\id_ed25519"
```

提示 `Enter passphrase` 时：**直接回车两次**（空密码，最省事）。要设密码也行，以后每次 ssh 输一次。

**应该看到**：`Your identification has been saved...`，生成 `.ssh\id_ed25519` 和 `.pub`。

### 9.3 把 Windows 的公钥装到 PVE

```powershell
# 在 Windows PowerShell 里执行（会提示一次 root 密码）
Get-Content "$env:USERPROFILE\.ssh\id_ed25519.pub" | ssh root@192.168.10.30 "mkdir -p /root/.ssh && chmod 700 /root/.ssh && cat >> /root/.ssh/authorized_keys && chmod 600 /root/.ssh/authorized_keys"
```

**应该看到**：只提示一次密码，没有其他输出（没有报错就是成功）。

### 9.4 测试免密登录

```powershell
# 在 Windows PowerShell 里执行
ssh root@192.168.10.30 hostname
```

**应该看到**：直接返回 `pve-lab`，**不再问密码**。

### 9.5 确认免密通了，才关密码登录

```bash
# 在 PVE 上执行（root）
cat > /etc/ssh/sshd_config.d/99-lab.conf <<'EOF'
PermitRootLogin prohibit-password
PasswordAuthentication no
EOF
systemctl restart ssh
```

**应该看到**：无报错。再开一个 Windows 窗口 `ssh root@192.168.10.30` 仍能直接进。

**失败怎么办**：
- 9.4 仍要密码 → 在 PVE 上 `cat /root/.ssh/authorized_keys`，确认里面有 `ssh-ed25519 AAAA...` 开头的一行
- 9.4 报 `Permission denied (publickey)` → Windows 用的不是刚生成那把，`ssh -v root@192.168.10.30` 看它加载了哪个 key
- 关完密码后连不上 → 接显示器键盘，`rm /etc/ssh/sshd_config.d/99-lab.conf && systemctl restart ssh` 恢复

---

## 步骤 10 · 挂 NVMe 做 thin 存储（15 分钟）

**在哪台**：PVE（root）
**目的**：把 512G NVMe 做成 VM 磁盘池
**开始前**：**关机 → 接上 NVMe → 开机**（装系统时没接）

**操作**：

1. 确认盘：

```bash
# 在 PVE 上执行（root）
lsblk
```

**应该看到**：`nvme0n1`，容量约 476.9G。

2. 建卷组和 thin 池：

```bash
# 在 PVE 上执行（root）
pvcreate /dev/nvme0n1
vgcreate nvme-vg /dev/nvme0n1
lvcreate --type thin-pool -l 95%FREE --poolmetadatasize 1G -n nvme-thin nvme-vg
```

**应该看到**：`Logical volume "nvme-thin" created.`

3. 加为 PVE 存储：

```bash
# 在 PVE 上执行（root）
pvesm add lvmthin nvme-lvm --vgname nvme-vg --thinpool nvme-thin --content images,rootdir
pvesm status
```

**应该看到**：`nvme-lvm` 一行，`Status` 为 `active`，`Avail` 约 480G。

4. 把 `local` 存储改成只放 ISO/模板/片段：

```bash
# 在 PVE 上执行（root）
pvesm set local --content iso,vztmpl,snippets
pvesm status
```

**失败怎么办**：
- `pvcreate` 提示已有分区 → 确认盘是空的（`lsblk` 看有没有挂载），有就 `wipefs -a /dev/nvme0n1`
- `pvesm add` 报已存在 → 换名字，或 `pvesm remove nvme-lvm` 后重来

---

## 步骤 11 · 做模板 9000（20 分钟）

**在哪台**：PVE（root）
**目的**：做一台 Ubuntu 24.04 母版，后面所有 VM 都从它克隆
**开始前**：步骤 10 的 `nvme-lvm` 已 active

**操作**：

1. 把 cloud-init 配置放到 snippets 目录：

```bash
# 在 PVE 上执行（root）
mkdir -p /var/lib/vz/snippets
mv /root/ubuntu-2404-vendor.yaml /var/lib/vz/snippets/
ls -l /var/lib/vz/snippets/
```

2. 跑模板脚本（会下载镜像、建 VM、转模板）：

```bash
# 在 PVE 上执行（root）
bash /root/make-ubuntu2404-template.sh
```

**应该看到**：最后输出 `完成：模板 ID=9000 ...`，中间有下载进度。

3. 检查模板配置：

```bash
# 在 PVE 上执行（root）
qm config 9000
```

**应该看到**：`scsi0`、`ide2`（cloudinit）、`efidisk0`、`cicustom`、`template: 1` 都在。

**失败怎么办**：
- 下载慢/失败 → 手动下载镜像放到 `/var/lib/vz/template/iso/noble-server-cloudimg-amd64.img` 再重跑
- 提示网桥不存在 → 回步骤 6
- 提示 snippets 不存在 → 回步骤 10 第 4 小步

---

## 步骤 12 · 装 thin 池告警（10 分钟）

**在哪台**：PVE（root）
**目的**：池用到 80% 预警、90% 告警
**开始前**：步骤 10 的存储已建好

**操作**：

```bash
# 在 PVE 上执行（root）
install -m 755 /root/thin-alert.sh      /usr/local/sbin/thin-alert.sh
install -m 644 /root/thin-alert.service /root/thin-alert.timer /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now thin-alert.timer
systemctl list-timers thin-alert.timer --no-pager
```

**应该看到**：`NEXT` 一列有时间（约 5 分钟后）。

演练一次，确认告警链路通：

```bash
# 在 PVE 上执行（root）
CRIT=1 WARN=1 STATE=/tmp/thin-test.state /usr/local/sbin/thin-alert.sh
rm -f /tmp/thin-test.state
journalctl -t thin-alert -n 5 --no-pager
```

**应该看到**：`[PVE thin] nvme-vg/nvme-thin 使用率 X% —— CRIT`。

**失败怎么办**：
- 没输出 → `lvs -o lv_name,data_percent nvme-vg` 看池名对不对
- `No such file` → 服务文件名拼错，`ls /etc/systemd/system/thin-alert.*`

---

## 步骤 13 · 压测与配置固化（20 分钟）

**在哪台**：PVE（root）
**目的**：确认 150W 的 U 在 6 相供电上稳得住；把配置存一份
**开始前**：系统已全部就绪

**操作**：

1. 全核压测 10 分钟，另开一个 Shell 看温度：

```bash
# 在 PVE 上执行（root）—— 第一个窗口
stress-ng --cpu 44 --timeout 600 --metrics-brief
```

```bash
# 在 PVE 上执行（root）—— 第二个窗口（Web Shell 可以开两个标签）
watch -n2 sensors
```

2. 压测时**用手摸 VRM 散热片**（CPU 左边那排小方块上的铝片）。
3. 压测结束后看有没有硬件错误：

```bash
# 在 PVE 上执行（root）
dmesg -T | grep -i -e mce -e error | tail -20
```

4. 备份配置：

```bash
# 在 PVE 上执行（root）
tar czf /root/pve-config-$(date +%F).tgz \
  /etc/pve /etc/network/interfaces /etc/default/grub \
  /etc/apt/sources.list.d /etc/eip.map /etc/systemd/system/eip.service \
  /etc/systemd/system/thin-alert.* 2>/dev/null
ls -lh /root/pve-config-*.tgz
```

**应该看到**：压测跑满 600 秒无重启；CPU 温度 < 90℃；`dmesg` 无 MCE；备份文件几十 KB。

**失败怎么办**：
- 中途重启 → 电源/VRM/内存问题，先把 BIOS 恢复默认再测
- 温度撞 90℃ → 检查散热器扣具是否压紧、硅脂是否涂好
- VRM 烫手 → 加一个 8cm 风扇对着吹，再测一次

---

## 步骤 14 · D0 验收清单

逐条打勾，全过才算 D0 完成：

- [ ] `https://192.168.10.30:8006` 能登录
- [ ] `ip -4 a show vmbr1` 有 `10.0.0.1/24`
- [ ] `systemctl status eip.service` 是 active，`iptables -t nat -L EIP-DNAT` 有 6 条
- [ ] Windows `ping 10.0.0.1` 通
- [ ] Windows `ssh root@192.168.10.30` 免密
- [ ] `pvesm status` 里 `nvme-lvm` 是 active
- [ ] `qm config 9000` 显示 template 且配置齐全
- [ ] `systemctl list-timers thin-alert.timer` 有下次执行时间
- [ ] 压测 10 分钟通过，VRM 不烫手
- [ ] `/root/pve-config-*.tgz` 已生成

**全部打勾后** → 进入 `02-D1-P0管理平面.md`。
