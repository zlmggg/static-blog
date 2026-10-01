# 系统基础与启动流程

::: tip 本篇定位
覆盖发行版区别、开机流程、systemd 和系统初始化优化。
:::

## 高频面试题

### Q1：描述 Linux 开机启动流程？

**我的答案：**

我习惯按"从按下电源到登录"这条线分五步讲，每步出问题都能对上排查点。

第一步**固件自检**：按电源后先跑 BIOS 或 UEFI，做加电自检（POST），初始化 CPU、内存、键盘这些硬件，然后按启动顺序找可引导磁盘。UEFI 相比老 BIOS 支持 GPT 大盘和图形化启动菜单。

第二步**引导加载器**：从磁盘的引导记录拉 GRUB2。BIOS 模式读 MBR 前 512 字节，UEFI 模式读 EFI 分区里的 `grubx64.efi`。GRUB 会让你选内核，然后把内核镜像和 initramfs 加载进内存。

第三步**内核与 initramfs**：内核解压运行，先靠 initramfs（一个小的临时根文件系统）里的驱动，把磁盘控制器、LVM、软RAID 这些模块加载起来，再挂载真正的根分区 `/`，最后切到根分区上。

第四步**systemd 接管**：根挂好后启动 1 号进程 systemd（PID 永远是 1，所有进程的祖先）。它不直接按脚本顺序跑，而是按 target 来拉起服务——`multi-user.target` 对应字符界面多用户，`graphical.target` 再往上加图形界面。常用 `systemctl get-default` 看默认目标，`systemctl set-default multi-user.target` 修改。

第五步**登录**：启动 getty，弹出登录提示符，进入可操作状态。

排障上我会对应：起不来先看是卡在哪一步——屏幕没字是固件/硬件问题，GRUB 进不去是引导问题，内核 panic 看 initramfs/磁盘，服务起不来就 `systemctl status xxx` 看日志。

---

### Q2：RHEL 系与 Debian 系的主要区别？

**我的答案：**

这俩是我最常打交道的两大派，区别我按五个方面对比着说。

第一**包管理**：RHEL 系（RHEL/Rocky/Alma/CentOS）用 `rpm` 包格式，命令是 `dnf`（老版本是 `yum`），装包 `dnf install nginx`，查包 `dnf provides */nginx`；Debian 系（Ubuntu/Debian）用 `deb` 包，命令是 `apt`，装包 `apt install nginx`，更新前要先 `apt update` 刷新索引。

第二**防火墙**：RHEL 系默认 firewalld，用 `firewall-cmd --add-service=http --permanent` 加规则；Debian 系一般用 ufw，`ufw allow 80/tcp`，底层都是 netfilter。

第三**安全模块**：RHEL 系默认开 SELinux，这是新手最容易踩的坑——服务起不来常常是 SELinux 拦的，用 `getenforce` 看状态；Debian 系默认是 AppArmor，管控思路不同。

第四**网络配置**：RHEL 系老版写 `/etc/sysconfig/network-scripts/`，新版用 NetworkManager 的 `nmcli`；Ubuntu 用 netplan 写 YAML。

第五**版本策略**：RHEL 系追求稳定保守，一个大版本支持 10 年，适合生产；Ubuntu 两年一个 LTS，更新更激进，桌面和云生态用得多。

工作中我以 RHEL 系为主线，遇到 Ubuntu 我会单独注意它防火墙是 ufw、没 SELinux、网络配置用 netplan 这三点差异。

---

### Q3：系统安装后的基础优化？

**我的答案：**

新机器装好系统，我按一套固定清单做初始化，保证它能安全、稳定地上生产。

第一**配软件源和时间**：先把默认源换成内网或国内镜像，`dnf makecache`（或 `apt update`）；时间必须准，装 chrony 做时间同步，`timedatectl set-timezone Asia/Shanghai` 设时区——集群里时间不对，证书和日志全乱。

第二**SSH 加固**：禁止 root 直接密码登录，先建普通用户并加入 wheel/sudo 组，再 `PermitRootLogin no`、改默认端口、用密钥登录关掉密码登录。

第三**建普通用户、给 sudo**：日常不用 root 干活，`useradd -m ops`、`usermod -aG wheel ops`，再配 sudo 权限，所有操作可审计。

第四**防火墙和 SELinux 按需开**：firewalld 默认只放必要端口；SELinux 我不建议直接关，先 `getenforce` 确认是 enforcing，业务跑通后再按需调策略，关了等于少一层防护。

第五**资源限制和内核参数**：改 `/etc/security/limits.conf` 调 ulimit（打开文件数调到 65535，不然高并发会 Too many open files）；按业务调 `/etc/sysctl.conf`，比如 `vm.overcommit_memory`、文件描述符上限，改完 `sysctl -p` 生效。

这套做完，新机器才算从"能装完"到"能上岗"。

---

## 相关链接

- [相关文档](/guide/linux-install)
