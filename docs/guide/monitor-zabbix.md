---
category: 监控
difficulty: 初级
---

# Zabbix 基础

::: tip 本篇定位
从零部署 Zabbix 7.0 LTS，完成主机添加、监控项（Item）、触发器（Trigger）和告警动作（Action）的全流程配置。学完你就能搭出一套能真正发告警的监控系统。
:::

## 简介与架构

### 一句话理解

Zabbix 是一套**企业级开源监控系统**：你想盯的每台服务器、每个服务，都派一个"探子"（Agent）上去定时采数据，数据汇总到中心（Server）存进数据库，Server 再按你设的规则判断"要不要报警"，通过邮件/钉钉/企业微信通知你。

和 Prometheus 那种"服务自己暴露指标、Server 来拉"的思路不同，Zabbix 传统上是 Agent 装在被监控机上，Server 主动去 Agent 那儿问（也支持 Agent 主动上报）。

### 各组件职责

| 组件 | 作用 | 小白类比 |
|---|---|---|
| Zabbix Server | 核心：调度采集、判断触发器、发告警 | 总部监控中心 |
| Agent2 | 装在被监控机器上的数据采集器 | 派到每台机器的探子 |
| 数据库（MySQL / PostgreSQL） | 存配置和历史监控数据 | 总部的档案室 |
| Web 前端（PHP） | 浏览器里看图、配规则、收告警 | 监控大屏和控制台 |
| Proxy（可选） | 替 Server 分管一批远端机器 | 分站站长，后面进阶篇讲 |

### 数据流向

```mermaid
flowchart LR
  A[被监控主机<br/>Agent2 :10050] -->|定时拉取指标| S[Zabbix Server<br/>:10051]
  S -->[(MySQL /<br/>PostgreSQL)]
  S --> T{触发器判断}
  T -->|异常| N[邮件/钉钉/<br/>企业微信]
  W[浏览器] <--> S
  S --> W
```

关键端口：Agent 监听 **10050**，Server 监听 **10051**，Web 是 80/443。

::: tip 版本说明
本文以 **Zabbix 7.0 LTS** 为准（2024-06 发布，完整支持到 2027-06，有限支持到 2029-06）。装之前可到官网下载页确认是否有更新的小版本：https://www.zabbix.com/cn/download 。
:::

## 部署

下面分 Server 端（数据库 + Server + Web）和 Agent 端两步走。操作系统以 Rocky/RHEL 系为主线，Debian/Ubuntu 差异单独标。

### 1. Server 端：安装软件包

::: code-group

```bash [RHEL / Rocky]
# 1. 导入官方源
rpm -Uvh https://repo.zabbix.com/zabbix/7.0/release/el/x86_64/zabbix-release-7.0-1.el.noarch.rpm
dnf clean all

# 2. 安装 Server + MySQL 库 + Web + Nginx 前端 + Agent2
dnf install -y zabbix-server-mysql zabbix-web-mysql zabbix-nginx-conf zabbix-sql-scripts zabbix-selinux-policy zabbix-agent2
```

```bash [Debian / Ubuntu]
# 1. 导入官方源（Debian 12 为例；Ubuntu 把 debian 换成 ubuntu、debian12 换成 ubuntu24.04）
wget https://repo.zabbix.com/zabbix/7.0/release/debian/pool/main/z/zabbix-release/zabbix-release_7.0-1+debian12_all.deb
dpkg -i zabbix-release_7.0-1+debian12_all.deb
apt update

# 2. 安装
apt install -y zabbix-server-mysql zabbix-frontend-php zabbix-nginx-conf zabbix-sql-scripts zabbix-agent2
```

:::

### 2. 初始化数据库

以 MariaDB/MySQL 为例（PostgreSQL 见本节末尾）：

```bash
# 登录 MySQL，建库、建用户、授权
mysql -uroot -p
```

```sql
CREATE DATABASE zabbix CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;
CREATE USER 'zabbix'@'localhost' IDENTIFIED BY 'Zabbix@2026';
GRANT ALL PRIVILEGES ON zabbix.* TO 'zabbix'@'localhost';
SET GLOBAL log_bin_trust_function_creators = 1;
EXIT;
```

导入初始表结构（**注意是导入到 zabbix 库**）：

```bash
zcat /usr/share/zabbix-sql-scripts/mysql/server.sql.gz | mysql --default-character-set=utf8mb4 -uzabbix -p zabbix
# 输入刚才设的密码 Zabbix@2026
# 导完关掉那个临时开关
mysql -uroot -p -e "SET GLOBAL log_bin_trust_function_creators = 0;"
```

::: details PostgreSQL 做法
```bash
sudo -u postgres createuser --pwprompt zabbix
sudo -u postgres createdb -O zabbix -E Unicode -T template0 zabbix
zcat /usr/share/zabbix-sql-scripts/postgresql/server.sql.gz | sudo -u postgres psql -d zabbix
```
对应安装包换成 `zabbix-server-pgsql`、`zabbix-web-pgsql`。
:::

### 3. 配置并启动 Server

```bash
# 编辑 /etc/zabbix/zabbix_server.conf，至少改这几项
#   DBPassword=Zabbix@2026
#   DBHost=localhost
vim /etc/zabbix/zabbix_server.conf
```

Nginx 前端默认监听 8080 端口、ServerName 未配置，按需要改 `/etc/zabbix/nginx.conf`（取消 `listen` 和 `server_name` 注释）。

```bash
systemctl restart zabbix-server zabbix-agent2 nginx php-fpm
# RHEL 系 php-fpm 服务名是 php-fpm；Debian 是 php8.3-fpm
systemctl enable zabbix-server zabbix-agent2 nginx php-fpm
```

验证：

```bash
systemctl status zabbix-server
# 日志在 /var/log/zabbix/zabbix_server.log，没有红色 Database 报错即正常
ss -lntp | grep -E '10051|8080'
```

### 4. Web 安装向导

浏览器打开 `http://<ServerIP>:8080/`（按你的 Nginx 配置），一路下一步：

1. **Welcome** → Next step；
2. **Check of pre-requisites**：PHP 版本、时区等，全是绿勾才继续；若 `date.timezone` 报错，编辑 `/etc/php-fpm.d/zabbix.ini`（或 `/etc/zabbix/php-fpm.conf`）设 `date.timezone = Asia/Shanghai`，重启 php-fpm；
3. **Configure DB connection**：选 MySQL，Database `zabbix`，User `zabbix`，Password 填刚才的；
4. **Zabbix server details**：Host 留 `localhost`，Port `10051`；
5. **Pre-installment** → Next → Finish。

登录默认账号：**Admin / zabbix**（注意 Admin 首字母大写），登录后立刻改密码。

### 5. Agent2 部署与配置（被监控机器上）

被监控机上同样装官方源，然后：

```bash
# RHEL
dnf install -y zabbix-agent2
# Debian
apt install -y zabbix-agent2
```

编辑 `/etc/zabbix/zabbix_agent2.conf`：

```conf
Server=10.0.0.10          # Zabbix Server 的 IP，Agent 只接受它来拉数据
ServerActive=10.0.0.10    # 主动模式上报地址
Hostname=web01             # 这台机器在 Zabbix 里叫什么（后面加主机时要一致）
```

启动：

```bash
systemctl restart zabbix-agent2
systemctl enable zabbix-agent2
ss -lntp | grep 10050      # Agent 监听 10050
```

防火墙要放行：Server 到 Agent 的 10050（被拉模式），以及 Agent 到 Server 的 10051（主动模式）。

## 主机与监控项

### 添加主机

Web 菜单：**数据采集 → 主机 → 创建主机**。

- 主机名称：`web01`（必须和 Agent 配置里的 Hostname 一致）；
- 模板：Link templates 里选 `Linux by Zabbix agent`（官方自带的 Linux 监控模板，CPU/内存/磁盘全套自带）；
- 群组：`Linux servers`；
- 接口：Add → Agent，IP 填被监控机 IP，Port `10050`。

保存后，主机列表"可用性"那一行的 **ZBX** 图标变绿，说明 Server 能连上 Agent 了。红了就去查：Agent 起没起、防火墙、Server/Agent 配置里的 IP 对不对。

### Item 与 Key

**Item（监控项）= 你要采的一个具体指标**，比如"CPU 使用率"。每个 Item 靠一个 **Key** 告诉 Agent 采什么。

几个最常用的 Key：

| Key | 采什么 | 典型值 |
|---|---|---|
| `agent.ping` | Agent 存活 | 1 = 活着 |
| `system.cpu.load` | 系统负载（1/5/15 分钟） | 0.05 |
| `vfs.fs.size[/,pused]` | 根分区已用百分比 | 45.2 |
| `system.cpu.util` | CPU 使用率 % | 12.3 |
| `vm.memory.util` | 内存使用率 % | 60.1 |
| `net.if.in[eth0]` | eth0 入站字节 | 计数器 |

可以在 Server 上手动验证 Agent 某个 Key 通不通：

```bash
zabbix_get -s web01 -p 10050 -k "system.cpu.load"
# 输出示例：0.050000
```

模板 `Linux by Zabbix agent` 已经把几十个常用 Item 配好了，一般不用自己加；自己业务指标才需要手动建 Item（进阶篇讲 UserParameter）。

## 触发器

### 它是干什么的

光有数据不报警等于没监控。**触发器（Trigger）= 给 Item 设一个阈值规则**，比如"根分区使用率 > 80% 就报警"。

### 表达式语法（7.0 新语法）

菜单：**数据采集 → 主机 → web01 → 触发器 → 创建触发器**。

经典表达式举例：

```
last(/web01/vfs.fs.size[/,pused]) > 80
```

含义：`web01` 这台主机上，最近一次根分区使用率 > 80%，触发器就变成"问题"状态。

再举几个：

```
min(/web01/system.cpu.load[,avg5]) > 4        # 5 分钟平均负载连续超 4
max(/web01/vm.memory.util) > 90               # 内存使用率峰值超 90%
last(/web01/agent.ping)=0                     # Agent 失联
```

函数速记：`last()` 最近值、`min()` 一段时间最小值、`max()` 最大值、`avg()` 平均值、`change()` 变化量。

### 告警级别分类

触发器的"严重性（Severity）"分档，从低到高：

| 级别 | 颜色 | 什么时候用 |
|---|---|---|
| 未分类 | 灰 | 记录类 |
| 信息 | 浅蓝 | 不影响业务 |
| 警告 | 黄 | 值得关注但不急 |
| 一般严重 | 橙 | 需要当天处理 |
| 严重 | 红 | 核心业务受影响 |
| 灾难 | 深红 | 全挂了，必须立刻电话叫醒人 |

## 告警动作

触发器只负责"判断出问题了"，**真正发通知靠 Action（动作）**。

### Action 配置

菜单：**告警 → 动作 → 创建动作**（7.0 里叫 Action，在 Actions 菜单下）。

1. **动作**标签：名字如"主机告警通知"；
2. **条件**：`触发器的严重性 >= 警告`，或者按主机群组过滤；
3. **操作**：发送消息给用户组（如 Zabbix Administrators），选择发送媒介（邮件/钉钉 Webhook），消息模板里可以写：

```
{HOST.NAME1} 触发告警：{TRIGGER.NAME}
当前值：{ITEM.LASTVALUE}
时间：{EVENT.DATE} {EVENT.TIME}
```

### 邮件 / 钉钉 / 企业微信通知思路

Zabbix 自带 Email 媒体类型，但钉钉、企业微信要自己配 Webhook 脚本：

- **思路**：在 `/usr/lib/zabbix/alertscripts/` 放一个脚本（如 `dingtalk.sh`），脚本里 `curl` 钉钉机器人 Webhook 地址，把消息 POST 过去；
- Zabbix 里**管理 → 媒体类型**新建一个脚本类型媒体类型，Script name 填 `dingtalk.sh`；
- 用户的"报警媒介"里选这个媒体类型，收件人填钉钉机器人 webhook 对应的手机号/标识。

```bash
# dingtalk.sh 极简示例（生产要加签名和重试）
#!/bin/bash
TO=$1
SUBJECT=$2
MESSAGE=$3
curl -s "https://oapi.dingtalk.com/robot/send?access_token=你的token" \
  -H 'Content-Type: application/json' \
  -d "{\"msgtype\":\"text\",\"text\":{\"content\":\"$SUBJECT\n$MESSAGE\"}}"
```

### 告警升级（Escalation）

同一条告警如果一段时间没人处理，自动升级通知到更高级别人。在 Action 的"操作"里配步骤：

- 步骤 1（0-5 分钟）：通知值班运维组；
- 步骤 2（5-10 分钟）：通知运维组长；
- 步骤 3（10 分钟后）：打电话/发短信给负责人。

## 验证

### 看最新数据

菜单：**监测 → 最新数据**，选主机 `web01`，能看到每个 Item 最近一次采到的值和时间曲线。有数据说明采集链路通了。

### 手动触发一次告警

最快的办法：把某个阈值临时调到当前就越界，观察告警是否真的发出来。

```bash
# 1. 找一个肯定超标的触发器，比如磁盘 > 80%
#    临时改成 last(/web01/vfs.fs.size[/,pused]) > 1（当前使用率肯定 > 1%）
# 2. 等 1 分钟左右（取决于 Item 采集间隔）
# 3. 菜单：问题 → 告警，应该能看到这条 Problem 出现
# 4. 收到邮件/钉钉后，把触发器改回 80
# 5. 问题自动恢复（OK 事件），说明整个闭环通了
```

也可以在命令行模拟：

```bash
# 用 zabbix_get 手动拉一次，确认数据本身没问题
zabbix_get -s web01 -p 10050 -k "vfs.fs.size[/,pused]"
```

::: tip 验收标准
一套可用的监控 = ① 最新数据有值 ② 触发器能变 Problem ③ 动作真的把消息发到你手机。三步都通，基础篇就算出师了。
:::

## 相关速查

- [Linux 命令速查](/reference/linux-commands)
- [Zabbix 进阶](/guide/monitor-zabbix-advanced)

### 官方文档

- Zabbix 官方文档（当前版本）：https://www.zabbix.com/documentation/current/
- Zabbix 下载页：https://www.zabbix.com/cn/download
- 发布周期与版本支持：https://www.zabbix.com/cn/life_cycle_and_release_policy
