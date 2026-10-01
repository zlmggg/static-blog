---
category: 安全
difficulty: 高级
date: 2023-09-05
---

# 服务器被植入挖矿木马（2023-09-05）

## 现象

监控告警：某台公网服务器 CPU 突然 100%，但上面业务很闲。登录一看，有个陌生进程在狂吃 CPU：

```bash
top
  PID USER      %CPU   COMMAND
 8821 root      392.5  /tmp/.X11-unix/systemd-network
```

`/tmp` 下有个伪装成系统服务的二进制文件，CPU 长期跑满。

## 环境

| 组件 | 版本 |
|---|---|
| 操作系统 | Ubuntu 20.04 LTS |
| 暴露面 | 公网 IP，SSH 22 端口暴露 |
| 已知弱点 | 之前为图省事把 SSH root 密码设得很简单 |

## 定位过程

### 1. 找到可疑进程并看它在干嘛

```bash
# 找 CPU 最高的进程
top -b -n1 -o %CPU | head
ps -ef --forest | grep -v "\[" | head -30
# 看进程详细信息
ls -l /proc/8821/exe          # 进程对应的二进制文件路径
ls -l /proc/8821/cwd          # 进程工作目录
cat /proc/8821/cmdline | tr '\0' ' '
```

发现 `/tmp/.X11-unix/systemd-network` 在连一个境外矿池地址。

### 2. 查它怎么进来的：看定时任务和启动项

挖矿木马一定会留持久化后门：

```bash
# 查所有定时任务
crontab -l
ls -la /etc/cron.* /var/spool/cron/
cat /etc/crontab

# 查可疑启动项
ls -la /etc/systemd/system/ /etc/init.d/
systemctl list-units --type=service | grep -v "systemd-"

# 查最近被篡改的文件（最近 24h）
find / -mtime -1 -type f -exec ls -l {} \; 2>/dev/null | grep -vE "/proc|/sys|/var/log"
```

发现 `/etc/cron.hourly/` 下有个可疑脚本，每小时从境外 URL 下载并运行挖矿程序。

### 3. 查 SSH 爆破记录

```bash
# 看 auth.log 里的暴力破解
grep "Failed password" /var/log/auth.log | awk '{print $11}' | sort | uniq -c | sort -rn | head
# 成功登录记录
grep "Accepted" /var/log/auth.log
```

发现大量来自境外 IP 的 root 密码爆破，且有一次 `Accepted password for root from 45.xxx.xxx.xxx`——就是被爆破进来的。

### 4. 查外联

```bash
# 看这个进程连了哪些外部地址
ss -tunlp | grep 8821
# 或
lsof -p 8821 -i
```

## 根因

| 层级 | 说明 |
|---|---|
| 直接原因 | SSH root 弱密码被公网爆破成功，攻击者登录后植入挖矿木马 + cron 持久化 |
| 根本原因 | 22 端口对公网开放、允许 root 密码登录、密码复杂度低 |

## 解决步骤

### 止血

1. **立刻断网隔离**（不要直接 reboot，reboot 会丢现场证据）：

```bash
# 防火墙先封死对外挖矿外联，保留业务访问
iptables -A OUTPUT -d <矿池IP段> -j DROP
```

2. 杀掉木马进程：

```bash
kill -9 8821
# 注意：先删 cron/启动项，再杀进程，否则 cron 会立刻拉起来
rm -f /etc/cron.hourly/xxx /tmp/.X11-unix/systemd-network
```

### 根治

1. SSH 加固（最关键）：

```conf
# /etc/ssh/sshd_config
PermitRootLogin no              # 禁止 root 直接登录
PasswordAuthentication no       # 禁止密码登录，只许密钥
Port 2222                       # 改端口（可选，降低扫描）
MaxAuthTries 3
```

```bash
systemctl restart sshd
```

2. 检查并清理所有后门：

```bash
# 删可疑 cron、systemd service、SSH  authorized_keys 里陌生公钥
cat /root/.ssh/authorized_keys
# 检查所有用户的 authorized_keys
```

3. 最稳妥的做法：**备份数据后重装系统**。挖矿木马往往还装了 rootkit，手动清理很难保证干净。

## 验证与预防

```bash
# 清理后 CPU 回落
top
# 不再有异常外联
ss -tunlp
# SSH 登录日志不再有 Failed password 风暴
```

- 预防：SSH 只允许密钥登录、禁 root、改端口或用防火墙白名单；fail2ban 防爆破。
- 监控：CPU 异常告警；外联连接数告警；定期巡检 cron/启动项。
- 规范：公网服务器最小暴露面，管理端口走 VPN/堡垒机。

## 相关

- 命令速查：[Linux 命令速查](/reference/linux-commands) ｜ [网络命令速查](/reference/network-commands)
- 同组短文：[Webshell 排查处置](/cases/t-webshell-investigation) ｜ [异常外联/C2 回连](/cases/t-malicious-c2-traffic)
