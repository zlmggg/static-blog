---
title: "Linux 命令速查"
description: "按功能聚合的命令速查表，忘了命令直接来这里复制。 用法：右侧「本页目录」可快速跳到对应分类；也可直接 Ctrl+K 搜索命令名。 说明：命令默认通用；RHEL 系（CentOS/Rocky）与 Debian 系（Ubuntu）有差异处会单独标注。"
---
# Linux 命令速查

> 按功能聚合的命令速查表，忘了命令直接来这里复制。
> 用法：右侧「本页目录」可快速跳到对应分类；也可直接 `Ctrl+K` 搜索命令名。
> 说明：命令默认通用；RHEL 系（CentOS/Rocky）与 Debian 系（Ubuntu）有差异处会单独标注。

## 文件与目录

| 命令 | 说明 | 示例 |
|---|---|---|
| [`pwd`](/commands/basic/cd-pwd) | 显示当前所在目录 | [`pwd`](/commands/basic/cd-pwd) |
| [`ls`](/commands/basic/ls) | 列出目录内容 | `ls -alh`（a 含隐藏、l 详情、h 可读大小） |
| [`cd`](/commands/basic/cd-pwd) | 切换目录 | `cd /etc`；`cd ~` 回家；`cd -` 上一个目录 |
| `mkdir` | 创建目录 | `mkdir -p a/b/c`（p 递归创建） |
| `touch` | 创建空文件 / 更新时间戳 | `touch test.txt` |
| [`cp`](/commands/basic/cp) | 复制 | `cp -r src dst`（r 递归复制目录） |
| [`mv`](/commands/basic/mv) | 移动 / 重命名 | `mv old new` |
| [`rm`](/commands/basic/rm) | 删除 | `rm -rf dir`（r 递归、f 强制，慎用） |
| `ln` | 建立链接 | `ln -s 源 链接名`（s 软链接） |
| `stat` | 查看文件详细元信息 | `stat file` |
| `tree` | 树状显示目录 | `tree -L 2`（L 层数） |

## 文件查看与编辑

| 命令 | 说明 | 示例 |
|---|---|---|
| `cat` | 查看整个文件 | `cat file` |
| `less` | 分页查看（推荐，可搜索） | `less file`，按 `/` 搜索、`q` 退出 |
| `head` | 看开头 | `head -n 20 file` |
| [`tail`](/commands/basic/tail) | 看结尾 | `tail -f file`（f 实时跟踪，看日志常用） |
| `vim` | 编辑器 | `vim file`（i 编辑、Esc 后 `:wq` 保存退出） |
| `wc` | 统计行/词/字节 | `wc -l file`（l 行数） |
| `sort` | 排序 | `sort file`；`sort -nr` 数字倒序 |
| `uniq` | 去重（常配合 sort） | `sort file \| uniq -c`（c 计数） |

## 管道、重定向与查找

| 命令 / 符号 | 说明 | 示例 |
|---|---|---|
| `\|` | 管道：前一个的输出给后一个 | `ps aux \| grep nginx` |
| `>` `>>` | 重定向：覆盖 / 追加 | `echo hi > a.txt`；`echo x >> a.txt` |
| `2>` | 错误输出重定向 | `cmd 2> err.log`；`cmd > all 2>&1` |
| `tee` | 同时输出到屏幕和文件 | `cmd \| tee out.log` |
| `xargs` | 把输入转为命令参数 | `find . -name "*.log" \| xargs rm` |
| [`find`](/commands/basic/find) | 按条件查找文件 | 见下表 |
| `locate` | 从数据库快速定位（需 updatedb） | `locate nginx.conf` |
| `which` `whereis` | 查命令路径 | `which python3` |

**find 常用：**

```bash
find / -name "*.conf"              # 按名称
find . -type f -size +100M         # 类型f文件、大于100M
find . -mtime -7                   # 7天内修改过
find . -user root                  # 属主是root
find . -type f -name "*.log" -delete   # 查找并删除
find . -type f -exec ls -l {} \;   # 对结果执行命令
```

## 文本三剑客（速查）

> 完整深入用法见 [Shell 编程指南](/guide/linux#合并资料) 与各专题，这里只列最常用形式。

| 命令 | 说明 | 示例 |
|---|---|---|
| [`grep`](/commands/basic/grep) | 文本搜索 | `grep -rn "error" /var/log`（r 递归、n 行号） |
| [`grep -E`](/commands/basic/grep) | 扩展正则（等同 egrep） | `grep -E "a\|b" file` |
| [`grep -v`](/commands/basic/grep) | 反向匹配（排除） | `ps aux \| grep -v grep` |
| [`sed`](/commands/basic/sed) | 流编辑 | `sed -i 's/old/new/g' file`（i 原地替换） |
| [`sed -n`](/commands/basic/sed) | 打印指定行 | `sed -n '10,20p' file` |
| [`awk`](/commands/basic/awk) | 列处理 | `awk -F: '{print $1}' /etc/passwd`（F 分隔符） |
| [`awk`](/commands/basic/awk) | 按条件过滤 | `awk '$3>1000' file` |

## 用户与权限

| 命令 | 说明 | 示例 |
|---|---|---|
| `whoami` `id` | 当前用户 / 用户ID组信息 | `id username` |
| `useradd` | 新建用户 | `useradd -m -s /bin/bash user` |
| `userdel` | 删除用户 | `userdel -r user`（r 删家目录） |
| `usermod` | 修改用户 | `usermod -aG docker user`（aG 追加附加组） |
| `passwd` | 改密码 | `passwd username` |
| `groupadd` | 新建组 | `groupadd dev` |
| [`chmod`](/commands/identity/chmod) | 改权限 | `chmod 755 file`；`chmod +x script.sh` |
| `chown` | 改属主属组 | `chown user:group file`；`chown -R user dir` |
| `setfacl` | 设置 ACL 细粒度权限 | `setfacl -m u:user:rwx file` |
| `sudo` | 以管理员身份执行 | `sudo systemctl restart nginx` |
| `su` | 切换用户 | `su - user` |

**权限数字速记：** r=4，w=2，x=1；如 `755` = rwxr-xr-x。

## 进程查看

| 命令 | 说明 | 示例 |
|---|---|---|
| [`ps`](/commands/system/ps) | 进程快照 | `ps aux`；`ps -ef` |
| [`top`](/commands/system/top) | 实时进程/CPU/内存 | [`top`](/commands/system/top)（按 P 按CPU、M 按内存排序，q 退出） |
| [`htop`](/commands/system/top) | 增强版 top（需安装） | [`htop`](/commands/system/top) |
| `pstree` | 树状显示进程 | `pstree -p`（p 显示PID） |
| `pgrep` | 按名称查 PID | `pgrep nginx` |
| `pidof` | 查程序 PID | `pidof sshd` |
| `uptime` | 运行时长 + 负载 | `uptime`（看 load average） |
| `w` `who` | 当前登录用户及操作 | `w` |
| [`lsof`](/commands/observe/lsof) | 进程打开的文件/端口 | 见下表 |
| `fuser` | 查文件/端口占用进程 | `fuser -v 80/tcp` |

**lsof 常用：**

```bash
lsof -i :80                # 查80端口被谁占用
lsof -i tcp                # 所有TCP连接
lsof -p 1234               # 查PID 1234打开的文件
lsof -u user               # 某用户打开的文件
lsof -i -n -P              # n不解析主机名、P不解析端口名（更快）
```

## 进程控制

| 命令 | 说明 | 示例 |
|---|---|---|
| `kill` | 发信号给进程 | `kill PID`；`kill -9 PID`（强制） |
| `killall` | 按名称杀进程 | `killall nginx` |
| `pkill` | 按名称/模式杀 | `pkill -f "python app"` |
| `jobs` | 查看后台任务 | `jobs -l` |
| `fg` `bg` | 调到前台 / 后台运行 | `fg %1` |
| `nohup` | 退出终端后继续运行 | `nohup ./run.sh &` |
| `nice` `renice` | 设置/调整优先级 | `renice -n 10 -p PID` |

**kill 信号：** `15` SIGTERM 优雅终止（默认）；`9` SIGKILL 强制；`1` SIGHUP 重载配置。

## 终端复用与长任务

| 命令 | 说明 | 示例 |
|---|---|---|
| `tmux` | 会话保持、分屏、多窗口 | `tmux new -s ops`；`tmux a -t ops` |
| `screen` | 老牌终端复用，老系统常见 | `screen -S ops`；`screen -r ops` |

> SSH 断线后任务不丢，长排查、长时间备份、多人看同一会话时用。完整按键与配置见 tmux 与 screen 详解。

## 内存与性能

| 命令 | 说明 | 示例 |
|---|---|---|
| `free` | 内存使用 | `free -h`（h 可读单位） |
| `vmstat` | 虚拟内存/CPU/IO 综合 | `vmstat 2`（每2秒刷新） |
| `mpstat` | 各 CPU 核统计 | `mpstat -P ALL 1` |
| `iostat` | 磁盘 IO 统计 | `iostat -xz 1` |
| `iotop` | 按进程看 IO（需安装） | `iotop -o` |
| `sar` | 历史活动数据 | `sar -u 1 3`（CPU） |
| `slabtop` | 内核 slab 缓存 | `slabtop -o` |
| [`strace`](/commands/observe/strace) | 跟踪系统调用、定位卡顿/报错 | `strace -f -tt -T -p PID` |
| [`perf`](/commands/observe/perf) | CPU 热点、调度与性能采样 | `perf top -g`；`perf record -F 99 -g -p PID` |

## 磁盘空间

| 命令 | 说明 | 示例 |
|---|---|---|
| [`df`](/commands/storage/df) | 文件系统空间 | `df -h`（空间）；`df -i`（inode） |
| [`du`](/commands/storage/du) | 目录占用大小 | `du -sh *`（s 汇总、h 可读） |
| `ncdu` | 交互式磁盘占用分析 | `sudo ncdu -x /`（不跨挂载点） |
| [`smartctl`](/commands/storage/smartctl) | 磁盘 SMART 健康与坏道预警 | `sudo smartctl -H /dev/sda`；`-a /dev/nvme0` |
| `lsblk` | 列出块设备 | `lsblk -f`（f 显示文件系统/UUID） |
| `blkid` | 查看设备 UUID/类型 | `sudo blkid` |

## 内核与资源限制

| 命令 | 说明 | 示例 |
|---|---|---|
| `sysctl` | 查看/设置内核参数 | `sysctl -a`；`sysctl -w net.ipv4.ip_forward=1` |
| `ulimit` | 用户资源限制 | `ulimit -a`（查看全部）；`ulimit -n 65535` |
| `dmesg` | 内核环形缓冲日志 | `dmesg -T`（T 显示时间）；`dmesg \| grep -i oom` |
| `uname` | 系统/内核信息 | `uname -a`；`uname -r` |
| `lsmod` `modprobe` | 内核模块 | `lsmod`；`modprobe 模块名` |

## 时间与任务

| 命令 | 说明 | 示例 |
|---|---|---|
| `date` | 查看/设置时间 | `date "+%F %T"`；`date -s "2026-09-24 10:00:00"` |
| `timedatectl` | systemd 时间管理 | `timedatectl set-timezone Asia/Shanghai` |
| [`crontab`](/commands/system/crontab) | 定时任务 | `crontab -e`（编辑）、`crontab -l`（查看） |
| `ntpq` `chronyc` | 时间同步状态 | `chronyc sources` |

**crontab 格式：** `分 时 日 月 周 命令`，如 `*/5 * * * * /opt/check.sh`。

## 包管理（RHEL vs Debian）

::: code-group

```bash [Debian/Ubuntu]
apt update                    # 更新软件源索引
apt install -y 包名           # 安装
apt remove 包名               # 卸载
apt search 关键词             # 搜索
dpkg -i 包.deb                # 安装本地deb
```

```bash [RHEL/CentOS]
yum install -y 包名           # 安装（旧）
dnf install -y 包名           # 安装（新版）
yum remove 包名               # 卸载
yum search 关键词             # 搜索
rpm -ivh 包.rpm               # 安装本地rpm
```

:::

> 包管理完整用法（仓库优先级、版本锁定、离线安装、rpm/dpkg 查询）：见 包管理详解。

## 服务与日志 systemd

> 服务起不来、开机不自启、日志找不到，先看这一节。完整 unit/日志用法见 [systemctl 与 journalctl 详解](/commands/system/systemctl-journalctl)。

| 命令 | 说明 | 示例 |
|---|---|---|
| [`systemctl status 服务`](/commands/system/systemctl-journalctl) | 状态、主 PID、最近日志 | `systemctl status nginx` |
| [`systemctl start/stop/restart 服务`](/commands/system/systemctl-journalctl) | 启动/停止/重启 | `systemctl restart nginx` |
| [`systemctl reload 服务`](/commands/system/systemctl-journalctl) | 重载配置（不中断连接） | `systemctl reload nginx` |
| [`systemctl enable --now 服务`](/commands/system/systemctl-journalctl) | 设为开机自启并立即启动 | `systemctl enable --now nginx` |
| [`systemctl disable 服务`](/commands/system/systemctl-journalctl) | 取消开机自启 | `systemctl disable nginx` |
| [`systemctl --failed`](/commands/system/systemctl-journalctl) | 只看失败的服务 | 巡检常用 |
| [`systemctl daemon-reload`](/commands/system/systemctl-journalctl) | 改完 unit 文件后重载 | 新增/修改 service 后必做 |
| [`journalctl -u 服务 -f`](/commands/system/systemctl-journalctl) | 实时看服务日志 | `journalctl -u nginx -f` |
| [`journalctl -u 服务 --since "10 minutes ago"`](/commands/system/systemctl-journalctl) | 按时间看日志 | 排查最近一次重启 |
| [`journalctl -p err -b`](/commands/system/systemctl-journalctl) | 本次开机的 error 及以上 | 快速找根因 |
| [`journalctl --disk-usage`](/commands/system/systemctl-journalctl) | 日志占用磁盘 | 清理前先看 |
| [`logrotate`](/commands/storage/logrotate) | 日志轮转、压缩与清理 | `logrotate -d /etc/logrotate.d/nginx`（干跑） |

## 远程登录与传输 SSH rsync

> 登录、免密、端口转发、传文件。密钥体系与加固见 [Linux 安全指南](/guide/linux-security)；完整选项见 [SSH 与 rsync 详解](/commands/network/ssh-rsync)。

| 命令 | 说明 | 示例 |
|---|---|---|
| [`ssh 用户@主机`](/commands/network/ssh-rsync) | 登录远程主机 | `ssh ops@203.0.113.10` |
| [`ssh -p 端口 用户@主机`](/commands/network/ssh-rsync) | 指定 SSH 端口 | `ssh -p 2222 ops@host` |
| [`ssh -J 跳板机 用户@内网`](/commands/network/ssh-rsync) | 经跳板机连接 | `ssh -J bastion ops@10.0.0.12` |
| [`ssh-keygen -t ed25519`](/commands/network/ssh-rsync) | 生成密钥对 | `ssh-keygen -t ed25519 -C "ops"` |
| [`ssh-copy-id 用户@主机`](/commands/network/ssh-rsync) | 下发公钥实现免密 | `ssh-copy-id ops@host` |
| [`ssh -L 本地:目标:端口`](/commands/network/ssh-rsync) | 本地端口转发 | `ssh -L 8080:127.0.0.1:80 ops@host` |
| [`scp 文件 用户@主机:/路径`](/commands/network/ssh-rsync) | 简单复制文件 | `scp a.tar.gz ops@host:/tmp/` |
| [`rsync -avz 源/ 用户@主机:/目标/`](/commands/network/ssh-rsync) | 增量同步（推荐） | 尾部斜杠决定是否同步目录本身 |
| [`rsync -avz --delete --dry-run`](/commands/network/ssh-rsync) | 先演练删除再同步 | 防止误删目标文件 |

## 网络与防火墙

| 命令 | 说明 | 示例 |
|---|---|---|
| [`ethtool`](/commands/network/ethtool) | 网卡速率/双工/丢包/光模块 | `ethtool eth0`；`ethtool -S eth0` |
| [`iptables`](/commands/network/iptables) | 主机防火墙规则与持久化 | `iptables -L -n -v --line-numbers` |
| [`firewall-cmd`](/reference/network-commands) | firewalld 端口/服务/富规则 | `firewall-cmd --permanent --add-service=https` |

> 远程改防火墙前先放行 SSH，并保留一个已登录会话；Docker 环境优先改 `DOCKER-USER` 链。

## 其他实用

| 命令 | 说明 | 示例 |
|---|---|---|
| `watch` | 周期执行并全屏刷新 | `watch -n 1 'ls -l'`（n 秒数） |
| `history` | 历史命令 | `history \| grep docker`；`!100` 重跑第100条 |
| `alias` | 命令别名 | `alias ll='ls -alh'` |
| `echo` | 输出文本/变量 | `echo $PATH` |
| `env` `export` | 环境变量 | `export http_proxy=http://127.0.0.1:7890` |
| [`tar`](/commands/basic/tar) | 打包压缩 | `tar -zxvf a.tar.gz`（解压）；`tar -zcvf a.tar.gz dir` |
| `zip` `unzip` | 压缩/解压 | `unzip file.zip`；`zip -r out.zip dir` |

<!-- merged-command-pitfalls:start -->
## 命令坑点索引

> 原先逐条拆开的单命令详解已合并到本手册；下面只保留每条命令最容易踩的坑，完整选项和示例不再单独成页。
> 需要看某条命令的完整用法时，先在上方速查表找到它，再看本节对应行。

| 命令 | 最容易踩的坑 | 官方文档 |
|---|---|---|
| `apt 与 dnf/yum` | 装包前不 apt update：会报"找不到包"或装到旧版本，先刷新列表。 | [官方](https://manpages.debian.org/bookworm/apt/apt.8.en.html) |
| `cat` | 大文件别直接 cat：几百 MB 的日志直接 cat 会瞬间刷爆终端、找不回头，改用 less 或 head/tail。 | [官方](https://www.gnu.org/software/coreutils/manual/) |
| `chown` | 改属主要 root：普通用户 chown 别人的文件会报 Operation not permitted，记得加 sudo。 | [官方](https://www.gnu.org/software/coreutils/manual/) |
| `date` | 格式串有空格必须加引号：date +%Y-%m-%d %H:%M:%S 不加引号会报错或只取第一段。 | [官方](https://www.gnu.org/software/coreutils/manual/) |
| `dmesg、uname 与 lsmod/modprobe` | dmesg 不加 -T 时间是开机秒数：[ 0.000000] 是开机后的秒数，不是时钟时间，加 -T 才是日期。 | — |
| `echo、env 与 export` | VAR=值 不 export，子进程读不到：这是最经典的坑。 | [官方](https://www.gnu.org/software/bash/manual/html_node/Bourne-Shell-Builtins.html) |
| `free` | 把 free 列当成"还能用的内存"：这是最常见的误判。 | [官方](https://man7.org/linux/man-pages/man1/free.1.html) |
| `head` | head 默认只看 10 行：不是整个文件，想看全部用 cat 或 less。 | [官方](https://www.gnu.org/software/coreutils/manual/) |
| `history 与 alias` | alias 只对当前 shell 生效：新开终端就没了；要永久用写进 ~/.bashrc 并 source ~/.bashrc。 | [官方](https://www.gnu.org/software/bash/manual/html_node/Bash-History-Builtins.html) |
| `iostat 与 iotop` | iostat 第一行是开机以来平均：判断当前瓶颈要看后面实时行，或加 -y 跳过第一行。 | — |
| `jobs、fg、bg、nohup、nice、renice` | & 只是后台，断 SSH 还是会死：要断了 SSH 还活着，必须 nohup ... &。 | [官方](https://www.gnu.org/software/bash/manual/html_node/Job-Control.html) |
| `kill、killall、pkill` | 别上来就 kill -9：先 kill -15 等几秒，不行再 kill -9。 | [官方](https://man7.org/linux/man-pages/man1/kill.1.html) |
| `less 与 more` | 进去后出不来很慌：永远记住按 q 退出，不是 Ctrl+C（虽然也能退，但 q 才是正道）。 | [官方](https://man7.org/linux/man-pages/man1/less.1.html) |
| `ln` | 忘了 -s：默认建的是硬链接，很多人本意是软链接却建错了。 | [官方](https://www.gnu.org/software/coreutils/manual/) |
| `locate / which / whereis` | locate 查不到刚建的文件：它查的是定时更新的数据库，新文件要等 updatedb 跑完（或手动 sudo updatedb）才能查到。 | [官方](https://man7.org/linux/man-pages/man1/locate.1.html) |
| `lsblk 与 blkid` | lsblk 看到的 NAME 带缩进树：缩进表示从属关系，不是名字的一部分。 | [官方](https://man7.org/linux/man-pages/man8/lsblk.8.html) |
| `mkdir` | 建多级目录忘记 -p：报 No such file or directory，几乎是每个新手都会踩一次的坑。 | [官方](https://www.gnu.org/software/coreutils/manual/) |
| `mpstat 与 sar` | Ubuntu 上 sar 报"没数据"：不是命令坏了，是没启用采集；先确认 /var/log/sa/ 下有没有 saDD 文件。 | — |
| `ncdu` | 不加 -x 扫到别的挂载点：统计结果和 df 对不上，根分区排查一定加 -x。 | [官方](https://dev.yorhel.nl/ncdu/man) |
| `pstree、pgrep、pidof` | pgrep 默认只匹配进程名，不匹配参数：要按命令行关键字找记得加 -f。 | [官方](https://man7.org/linux/man-pages/man1/pgrep.1.html) |
| `setfacl 与 getfacl` | ls -l 看不到完整 ACL：设了 ACL 后，权限位最后会多一个 +（如 -rw-r--r--+），但具体规则要 getfacl 才看得到。 | [官方](https://man7.org/linux/man-pages/man1/setfacl.1.html) |
| `sort` | 排数字忘了 -n：最常见的坑，导致 10 排在 2 前面。 | [官方](https://www.gnu.org/software/coreutils/manual/) |
| `stat` | 分不清三个时间：atime（读过没）、mtime（内容改没改）、ctime（权限/属主改没改）；改内容会动 mtime 和 ctime。 | [官方](https://www.gnu.org/software/coreutils/manual/) |
| `sudo 与 su` | su 和 su - 不一样：没有横杠不切环境，很多变量、PATH 还是旧的，导致「切了 root 但命令找不到」。 | [官方](https://www.sudo.ws/docs/man/sudo.man/) |
| `sysctl 与 ulimit` | sysctl -w 改完重启就没了：必须写进 /etc/sysctl.d/*.conf 并 sysctl --system 才永久。 | [官方](https://man7.org/linux/man-pages/man8/sysctl.8.html) |
| `timedatectl、chronyc 与 ntpq` | 容器里 timedatectl 报错：容器通常没有 systemd 作为 PID 1，timedatectl 连不上 bus；容器时间一般跟随宿主机，不用自己对。 | — |
| `tmux 与 screen` | 前缀键按法不对：Ctrl-b 是“按下再松开”，不是按住不放和 c 一起按。 | [官方](https://man7.org/linux/man-pages/man1/tmux.1.html) |
| `touch` | touch 建的是空文件：它不会写入任何内容，文件大小为 0。 | [官方](https://www.gnu.org/software/coreutils/manual/) |
| `tree` | 没装会报 command not found：先 apt install tree / yum install tree。 | [官方](https://man7.org/linux/man-pages/man1/tree.1.html) |
| `uniq` | uniq 不排序，只去相邻重复：这是头号坑。 | [官方](https://www.gnu.org/software/coreutils/manual/) |
| `useradd、usermod、userdel、passwd、groupadd、id、whoami` | usermod -G 不加 -a 会清空原有附加组：这是最高频事故。 | [官方](https://man7.org/linux/man-pages/man8/useradd.8.html) |
| `vmstat` | 盯着第一行平均值看：第一行是开机以来的平均，掩盖了当前抖动；一定要看第二行及以后的实时增量。 | [官方](https://man7.org/linux/man-pages/man8/vmstat.8.html) |
| `watch` | 带管道/引号的命令没加引号：watch ls -l \| wc -l 会被解析成"watch 跑 ls -l，然后管道给 wc -l"，不是你想要的；要写成 watch 'ls -l \| wc -l'。 | [官方](https://man7.org/linux/man-pages/man1/watch.1.html) |
| `wc` | wc -l 数的是换行符个数：如果文件最后一行没有换行符，那行不会被计入行数，可能差 1。 | [官方](https://www.gnu.org/software/coreutils/manual/) |
| `xargs` | 带空格文件名必须 -print0 \| xargs -0：否则文件名被空格拆碎，命令就错了。 | [官方](https://www.gnu.org/software/findutils/manual/html_mono/find.html) |
| `zip 与 unzip` | 打包忘了 -r：只会压空目录壳，子目录里的文件没进去。 | [官方](https://infozip.sourceforge.net/) |
| `重定向与管道` | > 会先清空文件：命令 > 文件 如果命令就是读这个文件本身，会先把文件清空！ | [官方](https://www.gnu.org/software/bash/manual/html_node/Redirections.html) |

<!-- merged-command-pitfalls:end -->

## 相关问答

- 系统操作类问题：[Linux 系统操作问题](/guide/linux#常见问题-faq)
- 网络连通类问题：[网络与连通性问题](/guide/linux-network#常见问题-faq)

## 官方文档

- GNU Coreutils 手册（ls/cp/df/du 等）：https://www.gnu.org/software/coreutils/manual/
- man-pages（Linux 命令手册）：https://man7.org/linux/man-pages/
- systemd / systemctl：https://www.freedesktop.org/software/systemd/man/latest/systemctl.html
- journalctl：https://www.freedesktop.org/software/systemd/man/latest/journalctl.html
- OpenSSH：https://www.openssh.com/manual.html
- rsync：https://rsync.samba.org/documentation.html
