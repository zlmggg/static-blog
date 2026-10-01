# Linux 命令速查

> 按功能聚合的命令速查表，忘了命令直接来这里复制。
> 用法：右侧「本页目录」可快速跳到对应分类；也可直接 `Ctrl+K` 搜索命令名。
> 说明：命令默认通用；RHEL 系（CentOS/Rocky）与 Debian 系（Ubuntu）有差异处会单独标注。

## 文件与目录

| 命令 | 说明 | 示例 |
|---|---|---|
| [`pwd`](./cmd/cd-pwd) | 显示当前所在目录 | [`pwd`](./cmd/cd-pwd) |
| [`ls`](./cmd/ls) | 列出目录内容 | `ls -alh`（a 含隐藏、l 详情、h 可读大小） |
| [`cd`](./cmd/cd-pwd) | 切换目录 | `cd /etc`；`cd ~` 回家；`cd -` 上一个目录 |
| [`mkdir`](./cmd/mkdir) | 创建目录 | `mkdir -p a/b/c`（p 递归创建） |
| [`touch`](./cmd/touch) | 创建空文件 / 更新时间戳 | `touch test.txt` |
| [`cp`](./cmd/cp) | 复制 | `cp -r src dst`（r 递归复制目录） |
| [`mv`](./cmd/mv) | 移动 / 重命名 | `mv old new` |
| [`rm`](./cmd/rm) | 删除 | `rm -rf dir`（r 递归、f 强制，慎用） |
| [`ln`](./cmd/ln) | 建立链接 | `ln -s 源 链接名`（s 软链接） |
| [`stat`](./cmd/stat) | 查看文件详细元信息 | `stat file` |
| [`tree`](./cmd/tree) | 树状显示目录 | `tree -L 2`（L 层数） |

## 文件查看与编辑

| 命令 | 说明 | 示例 |
|---|---|---|
| [`cat`](./cmd/cat) | 查看整个文件 | `cat file` |
| [`less`](./cmd/less-more) | 分页查看（推荐，可搜索） | `less file`，按 `/` 搜索、`q` 退出 |
| [`head`](./cmd/head) | 看开头 | `head -n 20 file` |
| [`tail`](./cmd/tail) | 看结尾 | `tail -f file`（f 实时跟踪，看日志常用） |
| `vim` | 编辑器 | `vim file`（i 编辑、Esc 后 `:wq` 保存退出） |
| [`wc`](./cmd/wc) | 统计行/词/字节 | `wc -l file`（l 行数） |
| [`sort`](./cmd/sort) | 排序 | `sort file`；`sort -nr` 数字倒序 |
| [`uniq`](./cmd/uniq) | 去重（常配合 sort） | `sort file \| uniq -c`（c 计数） |

## 管道、重定向与查找

| 命令 / 符号 | 说明 | 示例 |
|---|---|---|
| [`\|`](./cmd/redirect-tee) | 管道：前一个的输出给后一个 | `ps aux \| grep nginx` |
| [`>`](./cmd/redirect-tee) [`>>`](./cmd/redirect-tee) | 重定向：覆盖 / 追加 | `echo hi > a.txt`；`echo x >> a.txt` |
| [`2>`](./cmd/redirect-tee) | 错误输出重定向 | `cmd 2> err.log`；`cmd > all 2>&1` |
| [`tee`](./cmd/redirect-tee) | 同时输出到屏幕和文件 | `cmd \| tee out.log` |
| [`xargs`](./cmd/xargs) | 把输入转为命令参数 | `find . -name "*.log" \| xargs rm` |
| [`find`](./cmd/find) | 按条件查找文件 | 见下表 |
| [`locate`](./cmd/locate-which-whereis) | 从数据库快速定位（需 updatedb） | `locate nginx.conf` |
| [`which`](./cmd/locate-which-whereis) [`whereis`](./cmd/locate-which-whereis) | 查命令路径 | `which python3` |

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

> 完整深入用法见 [Shell 编程指南](/guide/linux-shell) 与各专题，这里只列最常用形式。

| 命令 | 说明 | 示例 |
|---|---|---|
| [`grep`](./cmd/grep) | 文本搜索 | `grep -rn "error" /var/log`（r 递归、n 行号） |
| [`grep -E`](./cmd/grep) | 扩展正则（等同 egrep） | `grep -E "a\|b" file` |
| [`grep -v`](./cmd/grep) | 反向匹配（排除） | `ps aux \| grep -v grep` |
| [`sed`](./cmd/sed) | 流编辑 | `sed -i 's/old/new/g' file`（i 原地替换） |
| [`sed -n`](./cmd/sed) | 打印指定行 | `sed -n '10,20p' file` |
| [`awk`](./cmd/awk) | 列处理 | `awk -F: '{print $1}' /etc/passwd`（F 分隔符） |
| [`awk`](./cmd/awk) | 按条件过滤 | `awk '$3>1000' file` |

## 用户与权限

| 命令 | 说明 | 示例 |
|---|---|---|
| [`whoami`](./cmd/user-mgmt) [`id`](./cmd/user-mgmt) | 当前用户 / 用户ID组信息 | `id username` |
| [`useradd`](./cmd/user-mgmt) | 新建用户 | `useradd -m -s /bin/bash user` |
| [`userdel`](./cmd/user-mgmt) | 删除用户 | `userdel -r user`（r 删家目录） |
| [`usermod`](./cmd/user-mgmt) | 修改用户 | `usermod -aG docker user`（aG 追加附加组） |
| [`passwd`](./cmd/user-mgmt) | 改密码 | `passwd username` |
| [`groupadd`](./cmd/user-mgmt) | 新建组 | `groupadd dev` |
| [`chmod`](./cmd/chmod) | 改权限 | `chmod 755 file`；`chmod +x script.sh` |
| [`chown`](./cmd/chown) | 改属主属组 | `chown user:group file`；`chown -R user dir` |
| [`setfacl`](./cmd/setfacl) | 设置 ACL 细粒度权限 | `setfacl -m u:user:rwx file` |
| [`sudo`](./cmd/sudo-su) | 以管理员身份执行 | `sudo systemctl restart nginx` |
| [`su`](./cmd/sudo-su) | 切换用户 | `su - user` |

**权限数字速记：** r=4，w=2，x=1；如 `755` = rwxr-xr-x。

## 进程查看

| 命令 | 说明 | 示例 |
|---|---|---|
| [`ps`](./cmd/ps) | 进程快照 | `ps aux`；`ps -ef` |
| [`top`](./cmd/top) | 实时进程/CPU/内存 | [`top`](./cmd/top)（按 P 按CPU、M 按内存排序，q 退出） |
| [`htop`](./cmd/top) | 增强版 top（需安装） | [`htop`](./cmd/top) |
| [`pstree`](./cmd/process-find) | 树状显示进程 | `pstree -p`（p 显示PID） |
| [`pgrep`](./cmd/process-find) | 按名称查 PID | `pgrep nginx` |
| [`pidof`](./cmd/process-find) | 查程序 PID | `pidof sshd` |
| `uptime` | 运行时长 + 负载 | `uptime`（看 load average） |
| `w` `who` | 当前登录用户及操作 | `w` |
| [`lsof`](./cmd/lsof) | 进程打开的文件/端口 | 见下表 |
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
| [`kill`](./cmd/process-signal) | 发信号给进程 | `kill PID`；`kill -9 PID`（强制） |
| [`killall`](./cmd/process-signal) | 按名称杀进程 | `killall nginx` |
| [`pkill`](./cmd/process-signal) | 按名称/模式杀 | `pkill -f "python app"` |
| [`jobs`](./cmd/job-control) | 查看后台任务 | `jobs -l` |
| [`fg`](./cmd/job-control) [`bg`](./cmd/job-control) | 调到前台 / 后台运行 | `fg %1` |
| [`nohup`](./cmd/job-control) | 退出终端后继续运行 | `nohup ./run.sh &` |
| [`nice`](./cmd/job-control) [`renice`](./cmd/job-control) | 设置/调整优先级 | `renice -n 10 -p PID` |

**kill 信号：** `15` SIGTERM 优雅终止（默认）；`9` SIGKILL 强制；`1` SIGHUP 重载配置。

## 内存与性能

| 命令 | 说明 | 示例 |
|---|---|---|
| [`free`](./cmd/free) | 内存使用 | `free -h`（h 可读单位） |
| [`vmstat`](./cmd/vmstat) | 虚拟内存/CPU/IO 综合 | `vmstat 2`（每2秒刷新） |
| [`mpstat`](./cmd/mpstat-sar) | 各 CPU 核统计 | `mpstat -P ALL 1` |
| [`iostat`](./cmd/iostat-iotop) | 磁盘 IO 统计 | `iostat -xz 1` |
| [`iotop`](./cmd/iostat-iotop) | 按进程看 IO（需安装） | `iotop -o` |
| [`sar`](./cmd/mpstat-sar) | 历史活动数据 | `sar -u 1 3`（CPU） |
| `slabtop` | 内核 slab 缓存 | `slabtop -o` |

## 磁盘空间

| 命令 | 说明 | 示例 |
|---|---|---|
| [`df`](./cmd/df) | 文件系统空间 | `df -h`（空间）；`df -i`（inode） |
| [`du`](./cmd/du) | 目录占用大小 | `du -sh *`（s 汇总、h 可读） |
| [`lsblk`](./cmd/lsblk-blkid) | 列出块设备 | `lsblk -f`（f 显示文件系统/UUID） |
| [`blkid`](./cmd/lsblk-blkid) | 查看设备 UUID/类型 | `sudo blkid` |

## 内核与资源限制

| 命令 | 说明 | 示例 |
|---|---|---|
| [`sysctl`](./cmd/sysctl-ulimit) | 查看/设置内核参数 | `sysctl -a`；`sysctl -w net.ipv4.ip_forward=1` |
| [`ulimit`](./cmd/sysctl-ulimit) | 用户资源限制 | `ulimit -a`（查看全部）；`ulimit -n 65535` |
| [`dmesg`](./cmd/dmesg-uname) | 内核环形缓冲日志 | `dmesg -T`（T 显示时间）；`dmesg \| grep -i oom` |
| [`uname`](./cmd/dmesg-uname) | 系统/内核信息 | `uname -a`；`uname -r` |
| [`lsmod`](./cmd/dmesg-uname) [`modprobe`](./cmd/dmesg-uname) | 内核模块 | [`lsmod`](./cmd/dmesg-uname)；`modprobe 模块名` |

## 时间与任务

| 命令 | 说明 | 示例 |
|---|---|---|
| [`date`](./cmd/date) | 查看/设置时间 | `date "+%F %T"`；`date -s "2026-09-24 10:00:00"` |
| [`timedatectl`](./cmd/time-sync) | systemd 时间管理 | `timedatectl set-timezone Asia/Shanghai` |
| [`crontab`](./cmd/crontab) | 定时任务 | `crontab -e`（编辑）、`crontab -l`（查看） |
| [`ntpq`](./cmd/time-sync) [`chronyc`](./cmd/time-sync) | 时间同步状态 | `chronyc sources` |

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

## 其他实用

| 命令 | 说明 | 示例 |
|---|---|---|
| [`watch`](./cmd/watch) | 周期执行并全屏刷新 | `watch -n 1 'ls -l'`（n 秒数） |
| [`history`](./cmd/history-alias) | 历史命令 | `history \| grep docker`；`!100` 重跑第100条 |
| [`alias`](./cmd/history-alias) | 命令别名 | `alias ll='ls -alh'` |
| [`echo`](./cmd/echo-env-export) | 输出文本/变量 | `echo $PATH` |
| [`env`](./cmd/echo-env-export) [`export`](./cmd/echo-env-export) | 环境变量 | `export http_proxy=http://127.0.0.1:7890` |
| [`tar`](./cmd/tar) | 打包压缩 | `tar -zxvf a.tar.gz`（解压）；`tar -zcvf a.tar.gz dir` |
| [`zip`](./cmd/zip-unzip) [`unzip`](./cmd/zip-unzip) | 压缩/解压 | `unzip file.zip`；`zip -r out.zip dir` |
