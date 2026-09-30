---
title: 日志管理
description: /var/log 日志、journalctl、journal 持久化与清理、rsyslog 集中日志、logrotate 轮转、dmesg 与 auditd
---

# 日志管理

::: tip 本篇定位
搞清楚 `/var/log` 下各类日志的用途，熟练使用 **journalctl** 查看和过滤 systemd 日志、配置 journal 持久化与清理；掌握 **rsyslog**（含集中日志服务器）和 **logrotate** 日志轮转，并了解 dmesg、auditd。
:::

## 一、日志概览

### 1.1 为什么需要日志

日志记录系统和服务运行过程中发生的事件（时间、来源、事件内容、严重程度），是**排障、审计、安全分析**的第一手资料。飞机有黑匣子，系统的"黑匣子"就是日志。

### 1.2 两套日志体系

现代 systemd 系统中，日志通常存两份：

| 体系 | 守护进程 | 存储形式 | 查看工具 |
|---|---|---|---|
| 传统日志 | **rsyslogd** | **文本文件**，落在 `/var/log/` | `cat`、`tail`、`grep` |
| systemd 日志 | **systemd-journald** | **二进制结构化**数据 | `journalctl` |

应用/内核的日志先由 journald 收集，rsyslog 再根据规则把其中一部分转成文本写入 `/var/log`。

### 1.3 /var/log 常见日志

| 日志文件 | RHEL/Rocky | Debian/Ubuntu | 内容 |
|---|---|---|---|
| 系统主日志 | `messages` | `syslog` | 综合的系统、服务运行信息（最常看） |
| 认证日志 | `secure` | `auth.log` | 登录、sudo、账号认证相关（安全排查） |
| 内核日志 | — | `kern.log` | 内核产生的消息 |
| 启动日志 | `boot.log` | boot.log | 系统启动过程 |
| 计划任务 | `cron` | — | crond/at 执行记录 |
| 邮件 | `maillog` | `mail.log` | 邮件服务 |
| 包管理 | `dnf.rpm.log`/yum.log | `dpkg.log`、apt/history.log | 软件安装记录 |
| 审计 | `audit/audit.log` | audit/audit.log | auditd 审计 |

**二进制的登录记录（不能直接 cat，用专门命令）：**

| 文件 | 命令 | 内容 |
|---|---|---|
| `/var/log/wtmp` | `last` | 成功登录记录 |
| `/var/log/btmp` | `lastb`（需 root） | 失败登录记录（爆破排查） |
| `/var/log/lastlog` | `lastlog` | 每个用户最近一次登录 |

```bash
last | head            # 最近登录
lastb | head           # 失败登录（排查 SSH 爆破）
lastlog                # 各用户最后登录
```

---

## 二、systemd-journald

`journalctl` 是查看 systemd 日志的工具，日志是结构化的二进制数据，支持强大的过滤。

### 2.1 基本查看

```bash
journalctl             # 列出所有日志（进入 less，G 到末尾、q 退出）
journalctl -e          # 直接跳到末尾
journalctl -n 20       # 只看最后 20 条（类似 tail -n）
journalctl -f          # 实时跟踪（类似 tail -f）
journalctl -r          # 倒序（最新在前）
```

### 2.2 按服务/程序过滤（最常用）

```bash
journalctl -u nginx.service          # 某服务的日志
journalctl -u nginx -u php-fpm       # 同时看多个服务
journalctl /usr/sbin/sshd            # 按可执行程序路径
journalctl -u nginx -f               # 跟踪某服务
```

### 2.3 按本次启动过滤

journal 会区分每次开机的日志：

```bash
journalctl -b                 # 本次开机以来的日志（排障常用，排除历史干扰）
journalctl -b -1              # 上一次开机的日志（排查上次为什么崩溃/关机）
journalctl --list-boots       # 列出所有可查的启动（编号、起止时间）
journalctl -b <启动ID>         # 查看指定那次启动
```

### 2.4 按时间过滤

```bash
journalctl --since "2026-09-27 09:00"
journalctl --until "2026-09-27 18:00"
journalctl -S yesterday              # 昨天到现在（--since）
journalctl --since "1 hour ago"
journalctl --since "2026-09-27" --until "2026-09-28"
```

时间支持 `YYYY-MM-DD HH:MM:SS`、`now`、`yesterday/today/tomorrow`、`"N minutes/hours/days ago"`。

### 2.5 按级别过滤

`-p` 按优先级（priority）过滤，只显示该级别及更严重的：

| 编号 | 级别 | 含义 |
|---|---|---|
| 0 | emerg | 系统不可用 |
| 1 | alert | 必须立即处理 |
| 2 | crit | 严重情况 |
| 3 | err | 错误 |
| 4 | warning | 警告 |
| 5 | notice | 一般但需注意 |
| 6 | info | 常规信息（默认） |
| 7 | debug | 调试信息 |

```bash
journalctl -p err            # 只看错误及以上
journalctl -p warning -b     # 本次开机的警告及以上
```

### 2.6 按字段与其他过滤

```bash
journalctl _PID=1234         # 某进程
journalctl _UID=0            # 某 UID（root）
journalctl _COMM=sshd        # 按进程名
journalctl -k                # 只看内核日志（等同 dmesg）
journalctl --disk-usage      # journal 占了多少磁盘
journalctl -o json-pretty    # 输出格式（见下）
```

**输出格式 `-o`：**

| 格式 | 说明 |
|---|---|
| short（默认） | 类 syslog 文本 |
| short-precise | 时间精确到微秒 |
| short-iso | ISO 8601 时间 |
| json / json-pretty | JSON（单行/美化，便于程序处理） |
| cat | 只显示消息本身，无元数据 |
| verbose | 显示所有字段 |

```bash
journalctl -u nginx -o json-pretty      # 结构化输出
journalctl -u nginx --no-pager          # 不进分页器，直接全部输出
```

::: tip 排障常用组合
```bash
journalctl -u nginx -b -p err           # 本次开机 nginx 的错误
journalctl -xe                          # 最近的错误及解释（-x 附加帮助文本）
```
:::

---

## 三、journal 持久化与清理

### 3.1 默认行为的差异

| 系统 | 默认存储 | 重启后 |
|---|---|---|
| **Debian/Ubuntu** | 持久化在 `/var/log/journal/` | 历史保留 |
| **RHEL/Rocky/CentOS** | 默认存 `/run/log/journal/`（内存/tmpfs） | **重启即丢失** |

### 3.2 开启持久化

编辑 `/etc/systemd/journald.conf`，设置 `Storage=persistent`：

```bash
sudo mkdir -p /var/log/journal
sudo systemd-tmpfiles --create --prefix /var/log/journal   # 确保权限
sudo vim /etc/systemd/journald.conf
```

```ini
[Journal]
Storage=persistent
#SystemMaxUse=500M        # journal 最多占用磁盘
#MaxRetentionSec=1month   # 日志最长保留时间
```

```bash
sudo systemctl restart systemd-journald
journalctl --list-boots          # 之后能看到多次启动记录
```

::: details Storage 取值
- `volatile`：只存 `/run/log/journal`（内存，重启丢）；
- `persistent`：存 `/var/log/journal`（磁盘，持久）；
- `auto`（默认）：有 `/var/log/journal` 目录就持久化，否则内存；
- `none`：不存任何数据。
:::

### 3.3 清理 journal

journal 会自动按配置限额清理，也可手动回收空间：

```bash
journalctl --disk-usage                       # 先看占用

sudo journalctl --vacuum-size=200M            # 只保留到 200M
sudo journalctl --vacuum-time=7d              # 删除 7 天前的
sudo journalctl --vacuum-files=10             # 只保留 10 个 journal 文件
```

自动限额在 `journald.conf`：`SystemMaxUse`（总占用）、`SystemKeepFree`（保留空闲）、`MaxRetentionSec`（保留时长）。

---

## 四、rsyslog

### 4.1 rsyslog 概念

rsyslog 是传统的日志服务，基于 syslog 协议，把日志按**设施（facility）+ 优先级（priority）**分类，再根据规则写到文件或转发。

**facility 设施（日志来源分类）：**

| 设施 | 来源 |
|---|---|
| auth / authpriv | 认证、安全（authpriv 权限更严） |
| cron | 计划任务 |
| daemon | 守护进程 |
| kern | 内核 |
| mail | 邮件 |
| user | 用户级 |
| local0–local7 | 本地自定义（可给应用专用） |

**priority 优先级**（从高到低）：`emerg > alert > crit > err > warning > notice > info > debug`。

### 4.2 配置文件

| 文件 | 作用 |
|---|---|
| `/etc/rsyslog.conf` | 主配置 |
| `/etc/rsyslog.d/*.conf` | 分片配置（推荐，服务包投放于此） |

主配置分三部分：`#### GLOBAL DIRECTIVES ####`（全局）、`#### MODULES ####`（模块）、`#### RULES ####`（规则）。

**规则 RULE 格式：`facility.priority    动作`**

```bash
# RHEL 默认规则示例
*.info;mail.none;authpriv.none;cron.none    /var/log/messages   # 除 mail/authpriv/cron 外的 info 以上
authpriv.*                                   /var/log/secure     # 认证全部
mail.*                                       -/var/log/maillog   # - 表示不立即同步磁盘
cron.*                                       /var/log/cron
*.emerg                                      :omusrmsg:*         # 紧急消息发给所有登录用户
```

- `*.info`：所有设施的 info 及以上；
- `mail.none`：排除 mail（none 表示不记录）；
- 分号 `;` 组合多个选择器；
- 文件路径前的 `-` 表示缓冲写入、不每次 fsync（性能优先）。

### 4.3 自定义应用日志（示例）

给 sshd 单独记录（sshd 用 local6/authpriv）。以自定义应用 local6 为例：

```bash
# /etc/rsyslog.d/sshd.conf
local6.*    /var/log/sshd.log
```

```bash
sudo systemctl restart rsyslog
logger -p local6.info "hello sshd"        # 模拟写入测试
tail /var/log/sshd.log
```

::: warning 文件权限导致无法创建
新版本 rsyslog 下，日志文件可能因权限无法自动创建。可手动预建并设置属主：
```bash
sudo touch /var/log/sshd.log
sudo chown syslog:adm /var/log/sshd.log    # Ubuntu；RHEL 属主 root:root
sudo systemctl restart rsyslog
```
:::

### 4.4 集中日志服务器

多台机器时，把日志集中到一台 log-server 统一存储和检索。

**服务端（log-server，10.0.0.13）：** 在 `/etc/rsyslog.conf` 启用接收模块（默认注释）：

```ini
# UDP（快、不保证可靠，默认 514）
module(load="imudp")
input(type="imudp" port="514")
# TCP（可靠，推荐）
module(load="imtcp")
input(type="imtcp" port="514")
```

```bash
sudo systemctl restart rsyslog
ss -tunlp | grep 514          # 确认监听
```

**客户端：** 把日志转发到服务器（`@` UDP、`@@` TCP）：

```bash
# /etc/rsyslog.d/remote.conf
*.info    @@10.0.0.13:514      # TCP 转发
# *.info   @10.0.0.13:514      # UDP 转发
```

```bash
sudo systemctl restart rsyslog
logger "this msg from client"   # 测试，服务端 /var/log/messages 可见
```

::: tip rsyslog vs ELK
- **rsyslog**：单机或少量机器的集中日志，简单轻量；
- **ELK/Loki**：大规模分布式集群，支持强大的检索、聚合、可视化，但资源开销大。
:::

> 官方文档：https://www.rsyslog.com/doc/

---

## 五、logrotate 轮转

### 5.1 为什么需要轮转

日志一直写同一个文件会越来越大，占满磁盘、难以查看和备份。**logrotate** 定期把旧日志切割、压缩、删除，使日志保持在可控大小。

### 5.2 配置文件

| 文件 | 作用 |
|---|---|
| `/etc/logrotate.conf` | 主配置（全局默认） |
| `/etc/logrotate.d/<服务>` | 各服务单独规则（apt、nginx、rsyslog 等） |

主配置默认：

```bash
weekly              # 默认每周轮转
rotate 4            # 保留 4 份，超出删除
create              # 轮转后生成新的空文件
dateext             # 用日期做后缀
#compress           # 是否压缩（默认注释）
include /etc/logrotate.d
```

### 5.3 规则块语法

```bash
/var/log/nginx/*.log {
    daily                  # 每天
    rotate 14              # 保留 14 份
    missingok              # 日志不存在也不报错
    notifempty             # 空文件不轮转
    compress               # gzip 压缩
    delaycompress          # 最近一次先不压（配合 compress，下次才压）
    create 0640 www-data adm   # 新文件权限 属主 属组
    sharedscripts          # 多个日志只执行一次脚本
    postrotate
        [ -f /var/run/nginx.pid ] && kill -USR1 `cat /var/run/nginx.pid`
    endscript
}
```

**常用指令：**

| 指令 | 含义 |
|---|---|
| daily / weekly / monthly | 轮转周期 |
| size 100M | 按大小轮转（到 100M 就切，可与周期并用） |
| rotate N | 保留份数 |
| compress / delaycompress | 压缩 / 延迟压缩 |
| dateext | 日期后缀（默认 .1 .2 编号） |
| missingok / notifempty | 不存在不报错 / 空文件不转 |
| create 模式 属主 属组 | 新建空文件 |
| copytruncate | 复制当前日志后直接清空原文件（见下） |
| su 用户 组 | 轮转操作使用的身份（权限场景） |
| prerotate/postrotate | 轮转前/后执行的脚本 |

::: warning create 与 copytruncate 的区别
- **create**：把原日志改名，再新建同名空文件，需应用重新打开文件（多数守护进程配合 postrotate 发信号）；
- **copytruncate**：先复制原日志、再把原文件截断清空，**应用无需重启/重开**，适合不支持重新打开日志的程序；但复制和截断之间可能丢失少量日志。
:::

### 5.4 手动执行与调试

```bash
sudo logrotate -d /etc/logrotate.d/nginx      # debug：只演示会做什么，不真执行
sudo logrotate -f /etc/logrotate.d/nginx      # force：强制立即轮转一次（测试用）
```

logrotate 本身不是守护进程，由 **systemd timer（logrotate.timer）或 `/etc/cron.daily/logrotate`** 每天触发一次：

```bash
systemctl list-timers | grep logrotate
```

> 配置手册：`man logrotate.conf`，命令手册：`man logrotate`。

---

## 六、dmesg 与 auditd

### 6.1 dmesg：内核环形缓冲区

`dmesg` 显示内核的环形缓冲区日志（硬件识别、驱动加载、内核报错、OOM）：

```bash
dmesg                       # 内核日志
dmesg -T                    # 显示人类可读时间
dmesg | grep -i error       # 过滤错误
dmesg | grep -i oom         # 排查 OOM
journalctl -k               # 等价（systemd 系统）
```

### 6.2 auditd：审计（了解）

**auditd** 是 Linux 审计守护进程，按规则记录安全相关事件（谁访问了某文件、执行了某命令、修改了配置），日志在 `/var/log/audit/audit.log`：

```bash
sudo systemctl status auditd
sudo ausearch -m avc -ts recent        # 查 SELinux 拒绝
sudo aureport                          # 审计报告
```

auditd 偏安全合规场景，普通排障用 journalctl/rsyslog 即可。

---

## 面试自测

1. /var/log/messages（syslog）和 secure（auth.log）分别记录什么？
2. wtmp、btmp、lastlog 是什么？分别用哪个命令查看？
3. journalctl 如何按服务、按本次启动、按时间、按级别过滤？
4. journalctl -b、-b -1、--list-boots 的用途？
5. RHEL 系和 Ubuntu 系 journal 默认持久化行为有何差异？如何开启持久化？
6. journal 如何清理？vacuum-size/time/files 分别什么意思？
7. rsyslog 的 facility 和 priority 各是什么？
8. rsyslog 规则 `*.info;mail.none ... /var/log/messages` 是什么意思？
9. 如何搭建 rsyslog 集中日志服务器？@ 和 @@ 的区别？
10. logrotate 的作用？daily/rotate/compress/delaycompress 分别干什么？
11. create 和 copytruncate 的区别和各自适用场景？
12. dmesg 看什么？auditd 是干什么的？

## 相关速查

- [Linux 命令速查](/reference/linux-commands)
- [进程与服务管理](/guide/linux-process)
