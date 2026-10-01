---
category: Linux
difficulty: 中级
date: 2021-03-14
---

# 时间不同步导致 TLS/JWT/Kerberos 鉴权失败（2021-03-14）

## 现象

一台新上线的服务器，调用内部 HTTPS 接口报证书错误：

```
curl: (60) SSL certificate problem: certificate is not yet valid
```

JWT 鉴权一直返回 401：

```
{"code":401,"message":"Token expired"}
```

但后端日志里明明 token 刚签发 1 秒。Kerberos/AD 域认证也失败：

```
kinit: Client 'user@EXAMPLE.COM' not found in Kerberos database while getting initial credentials
```

更奇怪的是，这台机器的日志时间比其他服务器慢了 8 分钟。

## 环境

- 发行版：Ubuntu 20.04.2 LTS
- 内核：`5.4.0-70-generic`
- 时间同步软件：chrony 3.5-6ubuntu
- 业务：内部微服务互调，用 JWT + mTLS

## 定位过程

### 1. 先看本机时间对不对

```bash
date
# Sun Mar 14 09:52:31 UTC 2021
timedatectl
#               Local time: Sun 2021-03-14 09:52:31 UTC
#           Universal time: Sun 2021-03-14 09:52:31 UTC
#                 RTC time: Sun 2021-03-14 09:52:30
#                Time zone: Etc/UTC (UTC, +0000)
# System clock synchronized: no
#              NTP service: inactive
```

`System clock synchronized: no`，NTP 没开。和其他机器对一下时间差 8 分钟。

### 2. 看 chrony 同步状态

```bash
chronyc tracking
# Reference ID    : 00000000 ()
# Stratum         : 0
# Ref time (UTC)  : Thu Jan  1 00:00:00 1970
# System time     : 8 seconds slow of NTP time
# Last offset     : +0.000000000 seconds
# RMS offset      : 0.000000000 seconds
```

`Reference ID : 0` 表示一台上游都没同步上。

```bash
chronyc sources
#  ^* 表示已同步的源
#  没有任何 ^*，全是 ^? 表示不可达
```

### 3. 验证时间差导致的 TLS 报错

```bash
openssl s_client -connect api.internal:443 -servername api.internal </dev/null 2>/dev/null | openssl x509 -noout -dates
# notBefore=Mar 14 09:50:00 2021 GMT
# notAfter=Jun 14 09:50:00 2021 GMT
```

本机时间是 09:52，证书 09:50 才生效，本机时间如果慢了 8 分钟（显示 09:44），就会落在 notBefore 之前，报 "certificate is not yet valid"。

### 4. JWT 为什么也失败

JWT 里有 `iat`（签发时间）和 `exp`（过期时间）。鉴权服务器签发时用的是正确时间（比如 10:00:00），这台服务器收到请求时自己时间是 09:52:00，校验 `exp > now` 时发现 `now < iat`，直接判过期。

## 根因

新机器装系统时没选对时区，也没开 NTP，主板 RTC 电池电量低导致时间飘。8 分钟的时差让所有依赖时间的鉴权（TLS 证书有效期校验、JWT 时间戳、Kerberos 票据）全部失效。

## 解决步骤

### 1. 临时止血：手动对时

```bash
# 立刻把时间改成正确的（从一台正常机器拿时间）
date -s "2021-03-14 10:00:00"

# 把系统时间写入硬件 RTC，防止重启又飘
hwclock --systohc
```

### 2. 彻底修复：开启 chrony

`/etc/chrony/chrony.conf`（Ubuntu）：

```
server ntp.aliyun.com iburst
server cn.ntp.org.cn iburst
driftfile /var/lib/chrony/chrony.drift
makestep 1.0 3
rtcsync
```

CentOS 配置文件在 `/etc/chrony.conf`，格式一样。

启动并设置开机自启：

```bash
systemctl enable --now chronyd
```

确认同步成功：

```bash
chronyc sources
# ^* ntp.aliyun.com ...
chronyc tracking
# System clock synchronized: yes
```

### 3. 设对时区

```bash
timedatectl set-timezone Asia/Shanghai
timedatectl
#   Time zone: Asia/Shanghai (CST, +0800)
```

## 验证与预防

- 所有服务器 `chronyc tracking` 显示 `Leap status : Normal`，偏移 < 50ms。
- 监控补：`chronyc tracking` 的系统时间偏移、`timedatectl` 的 synchronized 状态。
- 告警阈值：时间偏移 > 1 秒就告警（TLS/JWT 一般容忍 30~60 秒，1 秒已经很危险）。
- 新机器装机脚本里必须包含：`timedatectl set-timezone` + `systemctl enable --now chronyd`。
- 不要用 `ntpd`，现在主流发行版默认都是 `chronyd`。

## 相关

- 命令速查：[Linux 命令速查](/reference/linux-commands)
- 网络方向：[DNS 解析失败](/cases/t-dns-resolution-fail)
- 服务方向：[HTTPS 证书过期/链不全](/cases/t-tls-cert-expired)
- 巡检清单：[运维巡检清单](/reference/ops-checklists)
