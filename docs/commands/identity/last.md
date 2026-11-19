---
title: "last / lastlog / lastb · 登录审计"
description: "last 成功登录历史、lastb 失败登录（暴破排查）、lastlog 各用户最后登录、who 当前在线。安全审计与入侵排查中文详解。"
---

# last / lastlog / lastb · 登录审计

> 命令手册 · [用户与权限](/commands/identity/) ｜ 频率：偶尔用
> 谁什么时候登过、从哪来、有没有人暴力破解——安全审计和入侵排查靠这三个。

## 一句话用途

查成功/失败登录历史，发现异常登录与暴力破解。

## 高频场景速查

```bash
last                     # 成功登录历史（读 /var/log/wtmp）
last -n 20               # 最近20条
last rocky               # 某用户的登录
last -i                  # 显示 IP 而非主机名
lastb                    # 失败登录（读 /var/log/btmp，需 root）
lastb -n 50              # 最近50次失败（看暴破）
lastlog                  # 每个用户最后登录时间
lastlog -u rocky         # 某用户
```

## 参数详解

| 命令/参数 | 含义 |
|---|---|
| `last -n N` | 最近 N 条 |
| `last -i` | 显示 IP |
| `last -x` | 含关机/运行级别变化 |
| `last -f 文件` | 读指定日志（轮转的旧 wtmp） |
| `lastb` | 失败登录 |
| `lastlog -t 天数` | 最近 N 天内登录的 |
| `lastlog -b 天数` | N 天前还没登录的（僵尸账号） |

## 运维实战

**排查暴力破解**：`lastb | awk '{print $3}' | sort | uniq -c | sort -rn | head` 统计失败登录来源 IP，集中的就是暴破源，封它（[iptables](/commands/network/iptables)/fail2ban）。
**找僵尸账号**：`lastlog -b 90` 列 90 天没登录的账号，评估禁用。
**入侵溯源**：`last -i` 看异常时间/异常 IP 的成功登录。

::: tip 易错点
lastb 需 root（btmp 权限 600）。wtmp/btmp 会轮转，查更早的用 `last -f /var/log/wtmp-xxx`。攻击者可能清日志，重要审计应外发 syslog。
:::

## 相关命令

[id/whoami/w](./id-whoami) · [chage](./chage) · [auditctl](./audit) · [iptables](/commands/network/iptables)

## 官方文档

- last：<https://man7.org/linux/man-pages/man1/last.1.html>
- lastlog：<https://man7.org/linux/man-pages/man8/lastlog.8.html>