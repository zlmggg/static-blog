# crontab 命令详解：配置定时任务

> 本文是 [Linux 命令速查](../linux-commands#时间与定时) 中 `crontab` 的从 0 到 1 详解。
> 目标：把 `crontab -e/-l/-r/-u` 和"分 时 日 月 周"五段格式讲清楚，多看几遍后，你在服务器上敲 `crontab -e` 就知道怎么写定时任务。
> 环境依据：cronie/cron 包（Ubuntu 22.04 用 cron 包；RHEL/CentOS/Rocky 用 cronie，命令用法一致）。

## 一、命令是干什么的

`crontab`（cron table）用来管理**定时任务表**：让系统在指定的时间（如每天凌晨 3 点、每 5 分钟）自动执行某个命令或脚本。备份、日志切割、定时报表都靠它。

- `crontab -e`：**编辑**当前用户的定时任务（最常用）；
- `crontab -l`：**列出**当前用户已有的定时任务；
- `crontab -r`：**删除**整个定时任务表（危险）；
- `crontab -u 用户`：以 root 身份操作**别的用户**的任务表。

> 类比：`crontab` 像一个"闹钟+日程表"，你写一行"几点几分干什么"，cron 守护进程到点自动帮你按一下。

## 二、命令语法

```bash
crontab [-u 用户] 文件          # 用文件替换当前任务表
crontab [-u 用户] [-i] { -e | -l | -r }
```

- `-e`：打开编辑器编辑任务表；
- `-l`：打印任务表到屏幕；
- `-r`：删除整张任务表；
- `-i`：配合 `-r`，删除前先询问；
- `-u 用户`：root 才能用，操作用户的表。

最简单的用法：

```bash
crontab -e
```

## 三、任务格式（核心：五段时间）

打开 `crontab -e` 后，每行一个任务：

```text
分  时  日  月  周   要执行的命令
```

| 位置 | 含义 | 取值 |
|---|---|---|
| 第 1 段 | **分钟** | 0~59 |
| 第 2 段 | **小时** | 0~23 |
| 第 3 段 | **日** | 1~31 |
| 第 4 段 | **月** | 1~12 |
| 第 5 段 | **星期** | 0~7（0 和 7 都是周日） |

特殊符号：

| 符号 | 含义 | 例子 |
|---|---|---|
| `*` | 每一个 | `*` 在分时位 = 每分钟/每小时 |
| `,` | 列表 | `1,3,5` |
| `-` | 范围 | `1-5` |
| `/n` | 每隔 n | `*/5` = 每隔 5 单位 |

常见写法示例：

| 表达式 | 含义 |
|---|---|
| `* * * * *` | 每分钟 |
| `*/5 * * * *` | 每 5 分钟 |
| `0 * * * *` | 每小时整点 |
| `0 2 * * *` | 每天凌晨 2 点 |
| `0 3 * * 0` | 每周日凌晨 3 点 |
| `30 1 * * 1-5` | 工作日凌晨 1:30 |
| `0 0 1 * *` | 每月 1 号零点 |

> 两个环境变量常用：`SHELL=/bin/bash`、`MAILTO=you@example.com`（把输出 mailed 给你）。命令里的路径建议写**绝对路径**，因为 cron 的 `PATH` 很精简。

## 四、由浅入深的典型示例

### 示例 1：列出当前用户的定时任务

```bash
crontab -l
```

```text
no crontab for user
```

> 还没配过任务时会提示 no crontab。

### 示例 2：编辑定时任务

```bash
crontab -e
```

在打开的编辑器里加一行（每天凌晨 2 点备份）：

```text
0 2 * * * /usr/bin/rsync -a /data/ /backup/  >> /var/log/backup.log 2>&1
```

保存退出后，cron 会自动安装这张表。

> 要点：
> - 命令用绝对路径；
> - `>> log 2>&1` 把输出和错误都追加到日志，避免它把结果寄到你邮箱；
> - 写完可以 `crontab -l` 确认。

### 示例 3：每 5 分钟执行一次健康检查

```text
*/5 * * * * /opt/scripts/healthcheck.sh >/dev/null 2>&1
```

> `>/dev/null 2>&1` 表示丢弃所有输出（脚本自己已经记日志时）。

### 示例 4：工作日凌晨 1:30 跑报表

```text
30 1 * * 1-5 /opt/scripts/report.sh
```

> `1-5` 是周一到周五。

### 示例 5：root 查看/编辑某个用户的任务

```bash
sudo crontab -u www-data -l
sudo crontab -u www-data -e
```

> root 才能用 `-u`，普通用户只能改自己的表。

### 示例 6：删除前先询问（防误删）

```bash
crontab -r -i
```

```text
crontab: really delete user's crontab? (y/n)
```

> 不加 `-i` 的 `crontab -r` 会**直接清空整张表**，没有后悔药，养成加 `-i` 的习惯。

### 示例 7：系统级定时目录（不用 crontab -e）

除了用户自己的 crontab，系统还提供一批"放进去就执行"的目录：

```text
/etc/cron.hourly/
/etc/cron.daily/
/etc/cron.weekly/
/etc/cron.monthly/
/etc/crontab
/etc/cron.d/
```

把可执行脚本丢进 `/etc/cron.daily/`，系统每天自动跑；`/etc/crontab` 和 `/etc/cron.d/*` 比用户表多一列"以哪个用户身份执行"：

```text
# /etc/crontab 的格式（多一个 user 列）
25 1 * * * root /usr/bin/rsnapshot daily
```

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `crontab -e` | 编辑定时任务（**最常用**） |
| `crontab -l` | 查看已有任务 |
| `crontab -r -i` | 谨慎删除整张表 |
| `sudo crontab -u 用户 -e` | 改指定用户的任务 |
| `*/5 * * * * 命令` | 每 5 分钟 |
| `0 2 * * * 命令` | 每天凌晨 2 点 |

## 六、RHEL 系与 Debian 系差异

- **包名**：Ubuntu/Debian 是 `cron`（服务名 `cron`）；RHEL/CentOS/Rocky 是 `cronie`（服务名 `crond`）。命令 `crontab` 本身完全一样。
- 系统级目录两系都有 `/etc/crontab`、`/etc/cron.d/`、`/etc/cron.{hourly,daily,weekly,monthly}`，用法一致。
- 服务管理：Debian `systemctl status cron`；RHEL `systemctl status crond`。
- RHEL 还有 `/etc/cron.allow`、`/etc/cron.deny` 控制谁能用 cron；Debian 用 `/etc/cron.allow`/`/etc/cron.deny`，机制相同。

## 七、新手易错点

1. **五段是"分 时 日 月 周"，不是"分 时 日 月 年"**：cron 没有"年"这一段，写 6 段会出错。
2. **日和周是"或"关系**：`0 0 1 * 0` 表示"每月 1 号**或**每周日"都执行，不是"既是 1 号又是周日"。
3. **命令路径要用绝对路径**：cron 的 `PATH` 极简，直接写 `python` 可能找不到；写成 `/usr/bin/python3`。
4. **不重定向输出会一直发邮件**：cron 会把命令输出邮寄给本地用户，长期不处理会堆邮件/`/var/spool/mail`。
5. **`crontab -r` 直接清空**：没有回收站，务必加 `-i` 或先 `crontab -l > backup.txt` 备份。
6. **时区要对**：cron 按系统时区跑（`timedatectl` 设定），服务器时区错了任务时间就全错。
7. **`%` 在 crontab 里有特殊含义**：命令里的 `%` 要转义成 `\%`，或在脚本里用日期命令生成。

## 八、相关命令与文档

- 速查页：[Linux 命令速查](../linux-commands#时间与定时)
- 时间显示/计算：`date`（详解见 [date](./date)）
- 时区与 NTP：`timedatectl`（详解见 [time-sync](./time-sync)）
- cron 原理与更多玩法：见 [Linux 定时任务专题](../../guide/linux-cron)
