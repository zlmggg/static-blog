---
title: 定时任务
description: cron 周期任务、at 一次性任务、systemd timer 的配置与注意事项
category: Linux
difficulty: 中级
---
# 定时任务

::: tip 本篇定位
掌握三类定时任务：用 **cron** 配置周期性任务、用 **at** 配置只跑一次的任务、用 **systemd timer** 做更现代的定时方案，并理解它们的环境差异和排错方法。
:::

Linux 定时任务分两种：

| 类型 | 说明 | 实现 |
|---|---|---|
| 一次性任务 | 未来某个时间点执行一次 | `at`、`batch` |
| 周期性任务 | 按时间规律重复执行 | `cron`、systemd timer |

---

## 一、crontab 基础

### 1.1 cron 服务

cron 由守护进程 **crond** 提供，系统装好后默认运行，它每分钟检查一次是否有任务到期：

```bash
systemctl status crond        # RHEL/Rocky 服务名 crond
systemctl status cron         # Debian/Ubuntu 服务名 cron
```

### 1.2 时间格式

每条 cron 任务由 **5 个时间字段 + 命令**组成：

```
  分      时      日      月      周        命令
minute  hour   day    month  weekday   command
(0-59)  (0-23) (1-31) (1-12)  (0-7)
```

::: details 星期字段的取值
星期 0 和 7 都表示周日，1=周一 … 6=周六；也可写英文 `sun,mon,...,sat`。
:::

**字段内的 4 种操作符：**

| 符号 | 含义 | 示例 |
|---|---|---|
| `*` | 该位置所有值 | `* * * * *` 每分钟 |
| `,` | 列举多个值 | `1,3,5` 第 1、3、5 |
| `-` | 范围 | `1-5` 从 1 到 5 |
| `/` | 步长/频率 | `*/5` 每隔 5 |

### 1.3 用户级任务管理

每个用户有自己的 cron 任务，用 `crontab` 命令管理：

```bash
crontab -e          # 编辑当前用户的任务（最常用）
crontab -l          # 列出当前用户的任务
crontab -r          # 删除当前用户的全部任务
crontab -i -r       # 删除前交互确认（防止误删）
crontab -u user -l  # root 查看/管理指定用户的任务
```

用户任务文件实际保存在（一般不用直接动）：

- RHEL/Rocky：`/var/spool/cron/用户名`
- Ubuntu/Debian：`/var/spool/cron/crontabs/用户名`

::: warning 用户级任务不写用户名字段
`crontab -e` 里每行就是 `5 个时间字段 + 命令`，**不要再加用户名**（加了会被当成命令的一部分导致失败）。用户名字段只在系统级 `/etc/crontab` 中出现。
:::

### 1.4 特殊关键字（简写）

cron 提供以 `@` 开头的简写：

| 关键字 | 等价表达式 | 含义 |
|---|---|---|
| `@reboot` | — | 开机启动后执行一次 |
| @yearly / @annually | `0 0 1 1 *` | 每年 1 月 1 日 0 点 |
| `@monthly` | `0 0 1 * *` | 每月 1 号 0 点 |
| `@weekly` | `0 0 * * 0` | 每周日 0 点 |
| `@daily` / @midnight | `0 0 * * *` | 每天 0 点 |
| `@hourly` | `0 * * * *` | 每小时整点 |

```bash
@reboot /opt/myapp/start.sh        # 开机后自动拉起应用
```

---

## 二、系统级 cron

需要以指定用户身份跑、或属于系统维护的任务，用系统级 cron，有三种方式。

### 2.1 /etc/crontab 主配置

```bash
cat /etc/crontab
```

```bash
SHELL=/bin/bash
PATH=/sbin:/bin:/usr/sbin:/usr/bin
MAILTO=root

# 分  时  日  月  周   用户名   命令
  *   *   *   *   *    root    /usr/bin/echo hello
```

::: tip 与用户级的关键区别
`/etc/crontab` 里在时间字段和命令之间**必须有用户名字段**（如 `root`），cron 会以该用户身份执行。
:::

### 2.2 /etc/cron.d/ 子配置

把独立的任务文件放进 `/etc/cron.d/`，格式与 `/etc/crontab` 相同（含用户名字段），适合软件包投放任务，避免改动主文件：

```bash
# /etc/cron.d/mybackup
0 2 * * * root /usr/local/bin/backup.sh
```

### 2.3 周期目录（放可执行脚本）

系统预置了一组目录，把**可执行脚本**直接放进去，就会按对应周期由 anacron/cron 调用，无需写时间表达式：

| 目录 | 执行周期 |
|---|---|
| `/etc/cron.hourly/` | 每小时 |
| `/etc/cron.daily/` | 每天 |
| `/etc/cron.weekly/` | 每周 |
| `/etc/cron.monthly/` | 每月 |

```bash
sudo cp cleanup.sh /etc/cron.daily/
sudo chmod +x /etc/cron.daily/cleanup.sh
```

> `cronie-anacron`（Debian 上是 anacron）负责保证：即使机器在预定时间关机（如笔记本、夜间关机的服务器），开机后也会补跑漏掉的 daily/weekly/monthly 任务。

### 2.4 控制谁能用 cron

通过两个文件控制（与 at 同理）：

- `/etc/cron.allow`：白名单，只有其中用户能用 cron（文件默认不存在）；
- `/etc/cron.deny`：黑名单，其中用户不能用（默认存在、内容为空，即不限制）；
- 若两个都不存在，只有 root 能用；**allow 优先级高于 deny**。

---

## 三、crontab 示例

### 3.1 常用表达式

```bash
*/5 * * * * /usr/local/bin/job.sh          # 每 5 分钟
0 * * * * /usr/local/bin/job.sh            # 每小时整点
0 2 * * * /usr/local/bin/backup.sh         # 每天 2:00
30 3 * * 0 /usr/local/bin/weekly.sh        # 每周日 3:30
0 0 1 * * /usr/local/bin/monthly.sh        # 每月 1 号 0:00
0 9-18 * * 1-5 /usr/local/bin/check.sh     # 工作日(周一到周五)9-18 点每小时
*/10 9-18 * * 1-5 /usr/local/bin/check.sh  # 工作日 9-18 点每 10 分钟
0 0 1,15 * * /usr/local/bin/semi.sh        # 每月 1 号和 15 号
```

### 3.2 实战：定时备份

```bash
crontab -e
```

```bash
# 每天凌晨 2:30 备份网站数据，日志单独记录
30 2 * * * /usr/local/bin/backup.sh >> /var/log/backup.log 2>&1
```

### 3.3 实战：清理过期日志

```bash
# 每天凌晨 4 点删除 /var/log/myapp 下 7 天前的 .log
0 4 * * * /usr/bin/find /var/log/myapp -name "*.log" -mtime +7 -delete
```

### 3.4 秒级任务

cron 最小粒度是**分钟**，做不到"每隔几秒"。变通方法是每分钟启动一个脚本，在脚本内循环：

```bash
* * * * * /usr/local/bin/every5sec.sh
```

```bash
#!/bin/bash
# every5sec.sh：在一分钟内每 5 秒执行一次
for i in {1..12}; do
    /usr/local/bin/job.sh
    sleep 5
done
```

### 3.5 在线工具

表达式拿不准时可用在线生成/校验工具（注意不要把含敏感信息的命令贴上去）：

- crontab.guru：https://crontab.guru/
- Crontab Generator：https://crontab-generator.org/

---

## 四、at 一次性任务

### 4.1 安装与服务

- **RHEL/Rocky**：默认已安装并运行 `atd`；
- **Debian/Ubuntu**：默认未安装，需先装：

```bash
sudo apt install at -y
systemctl status atd        # Ubuntu 服务名也是 atd
```

### 4.2 创建任务

进入交互式，输入要执行的命令，**按 Ctrl+D 结束**：

```bash
at 02:00                    # 今天 2:00（若已过则明天）
at 02:00 2026-09-20         # 指定年月日
at now + 5 minutes          # 5 分钟后
at now + 2 hours            # 2 小时后
at 17:00 tomorrow           # 明天 17:00
at noon                     # 中午 12:00
at midnight                 # 午夜 0 点
at teatime                   # 下午 4 点（16:00）
```

```bash
[root@rocky10 ~]# at now + 2 min
at> /usr/bin/touch /tmp/at-demo
at> <EOT>                   # 这里按 Ctrl+D
job 4 at Mon Sep 11 15:30:00 2026
```

也可以用管道直接传入（非交互）：

```bash
echo "/usr/bin/systemctl restart nginx" | at now + 10 min
```

### 4.3 查看与删除

```bash
atq                # 或 at -l：列出待执行任务及编号
at -c 4            # 查看编号 4 任务的具体内容
atrm 4             # 或 at -d 4：删除编号 4 的任务
```

### 4.4 权限控制

- `/etc/at.allow`：白名单，其中用户才能用 at；
- `/etc/at.deny`：黑名单（默认存在、为空，即不限制任何人）；
- 两文件都不存在时只有 root 能用；**allow 优先**。

### 4.5 batch：系统空闲时执行

`batch`（也是 at 包提供）在**系统负载低于阈值时**才执行任务，适合跑不在乎具体时间、但不想加重高峰负担的重活，用法同 at：

```bash
batch
at> /usr/local/bin/heavy-job.sh
at> <EOT>
```

---

## 五、systemd timer

systemd 自带定时能力，由一个 **`.timer`** 单元和它触发的 **`.service`** 单元配对组成。

### 5.1 两种触发方式

| 指令 | 含义 |
|---|---|
| `OnCalendar=` | 按日历时间（类似 cron） |
| `OnBootSec=` / `OnStartupSec=` | 距开机/启动后多久 |
| `OnUnitActiveSec=` | 距该服务上次激活后多久（周期） |
| `OnUnitInactiveSec=` | 距该服务上次停止后多久 |

### 5.2 完整示例：每 5 分钟跑一次任务

先写被触发的服务 `/etc/systemd/system/mytask.service`：

```ini
[Unit]
Description=My Periodic Task

[Service]
Type=oneshot
ExecStart=/usr/local/bin/mytask.sh
```

再写定时器 `/etc/systemd/system/mytask.timer`（**与服务同名**）：

```ini
[Unit]
Description=Run mytask every 5 minutes

[Timer]
OnBootSec=2min
OnUnitActiveSec=5min
Persistent=true

[Install]
WantedBy=timers.target
```

启用：

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now mytask.timer
systemctl list-timers                 # 查看所有定时器及下次触发时间
```

### 5.3 OnCalendar 日历表达式

```ini
[Timer]
OnCalendar=*:0/15                 # 每 15 分钟
OnCalendar=daily                  # 每天 0 点
OnCalendar=hourly                 # 每小时
OnCalendar=Mon..Fri 09:00         # 工作日 9 点
OnCalendar=*-*-1 00:00:00         # 每月 1 号 0 点
OnCalendar=Mon *-*-* 03:00:00     # 每周一 3 点
Persistent=true                   # 关机错过的，开机后补跑
```

> 语法为 `星期 年-月-日 时:分:秒`，比 cron 更直观，手册见 [systemd.time(7)](https://www.freedesktop.org/software/systemd/man/latest/systemd.time.html)、[systemd.timer(5)](https://www.freedesktop.org/software/systemd/man/latest/systemd.timer.html)。

### 5.4 与 cron 对比

| 维度 | cron | systemd timer |
|---|---|---|
| 日志 | 需自己重定向/看邮件 | 自动进 journald，`journalctl -u xxx` 直接查 |
| 错过任务 | 靠 anacron（仅 daily 等） | `Persistent=true` 原生补跑 |
| 依赖管理 | 无 | 可配合 Unit 依赖、顺序 |
| 随机延迟 | 不支持 | `RandomizedDelaySec=` 防雪崩 |
| 精度/调试 | 简单通用 | 信息更全、`list-timers` 直观 |
| 适用 | 简单、跨平台通用 | 已全面使用 systemd 的系统 |

::: tip 怎么选
- 简单的周期任务、或需要跨不同 UNIX 通用，用 **cron**，最普及；
- 想要完善日志、错过补跑、与其他服务联动，用 **systemd timer**；
- 只跑一次用 **at**。
:::

---

## 六、注意事项（cron 排错重点）

cron 任务"手动能跑、定时不跑"，90% 是下面几个原因。

### 6.1 用绝对路径

cron 的环境非常精简，`PATH` 往往只有 `/usr/bin:/bin`，你在终端能用的命令可能找不到：

```bash
# 错误：依赖 PATH
0 2 * * * backup.sh
# 正确：命令和脚本都写绝对路径
0 2 * * * /usr/local/bin/backup.sh
```

也可在任务文件顶部自定义环境：

```bash
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/bin
MAILTO=zlmggg
```

### 6.2 环境变量与交互环境不同

cron 不加载 `~/.bashrc`、`~/.bash_profile`，所以里面定义的变量、别名、conda/nvm 环境等都不生效。需要的环境在脚本内显式 `source` 或写全。

### 6.3 输出要重定向

任务有输出时，cron 默认会尝试**发本地邮件**给用户（没装邮件服务就丢失或堆积）。应显式重定向：

```bash
0 2 * * * /usr/local/bin/backup.sh >> /var/log/backup.log 2>&1   # 正常和错误都记日志
*/5 * * * * /usr/local/bin/heartbeat.sh >/dev/null 2>&1         # 丢弃所有输出
```

### 6.4 权限与脚本可执行

- 脚本要有执行权限：`chmod +x script.sh`；
- cron 以任务属主身份运行，确保该用户对脚本、日志、目标路径有权限；
- 涉及系统操作放系统级 cron 或用 root，普通任务用普通用户。

### 6.5 百分号 `%` 要转义

在 cron 命令中，未转义的 `%` 表示"换行"，其后内容被当作标准输入。需要字面 `%` 时写成 `\%`，或放进脚本里：

```bash
# date 的 +%F 中的 % 必须转义
0 2 * * * /usr/bin/tar -czf /data/bak_$(/usr/bin/date +\%F).tar.gz /data/www
```

### 6.6 看日志定位

任务没执行时查日志：

```bash
# RHEL/Rocky
sudo grep CRON /var/log/cron
# Debian/Ubuntu
sudo grep CRON /var/log/syslog
# systemd timer
journalctl -u mytask.service
```

常见日志报错：`CMD (xxx) root: 未找到命令`（路径问题）、`(root) CMDEND` 配合邮件（输出问题）。

---

## 面试自测

1. cron 时间表达式五个字段分别是什么？最小粒度是多少？
2. `*`、`,`、`-`、`/` 各代表什么？
3. 用户级 crontab 和 `/etc/crontab` 在写法上最关键的区别是什么？
4. `crontab -e/-l/-r` 分别做什么？
5. `/etc/cron.d/` 和 cron.hourly/daily 目录分别怎么用？
6. at 命令如何创建、查看、删除一次性任务？
7. cron.allow / cron.deny 的优先级和规则？
8. 如何实现"每隔几秒"的任务？
9. systemd timer 相比 cron 有哪些优势？Persistent 是干什么的？
10. 为什么脚本手动能跑、放进 cron 就不执行？怎么排查？
11. cron 里为什么要避免直接写 `%`？怎么处理？
12. @reboot 是什么场景用的？

## 相关速查

- [Linux 命令速查](/reference/linux-commands)
- [进程与服务管理](/guide/linux-process)
