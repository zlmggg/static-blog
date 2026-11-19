---
title: "auditctl / ausearch · 审计规则"
description: "auditd 审计框架、auditctl 加规则（监控文件/ syscall）、ausearch/aureport 查事件。等保合规与入侵溯源，参数中文分级。"
---

# auditctl / ausearch · 审计规则

> 命令手册 · [用户与权限](/commands/identity/) ｜ 频率：很少用
> 谁改了关键文件、谁执行了特权命令——auditd 记录到内核级审计日志，比应用日志更底层、更难篡改。

## 一句话用途

配置内核审计规则，记录"谁在何时对什么做了什么"，供合规与溯源。

## 高频场景速查

```bash
sudo systemctl enable --now auditd     # 启审计服务
sudo auditctl -l                       # 看当前规则
sudo auditctl -w /etc/passwd -p wa -k identity   # 监控 passwd 被写/改属性
sudo auditctl -w /etc/sudoers -p wa -k sudoers
sudo ausearch -k identity              # 按 key 查事件
sudo ausearch -f /etc/passwd           # 按文件查
sudo aureport --summary                # 汇总报告
```

## 参数详解

### auditctl

| 参数 | 含义 |
|---|---|
| `-w 路径` | 监控某文件/目录 |
| `-p r/w/x/a` | 触发权限（读/写/执行/属性改） |
| `-k key` | 给规则打标签（便于查） |
| `-a always,exit -S 系统调用` | 监控 syscall |
| `-l` | 列规则 |
| `-D` | 清空规则 |

### ausearch / aureport

| 命令 | 含义 |
|---|---|
| `ausearch -k key` | 按标签查 |
| `ausearch -f 文件` | 按文件查 |
| `ausearch -ts recent` | 最近事件 |
| `aureport --summary` | 汇总 |
| `aureport --auth` | 认证报告 |

## 运维实战

**等保文件完整性审计**：监控 /etc/passwd、/etc/shadow、/etc/sudoers 的写操作，规则写进 `/etc/audit/rules.d/audit.rules` 持久化。
**溯源谁改了配置**：`ausearch -f /etc/nginx/nginx.conf` 看哪个 uid/进程改的。
**监控特权命令**：`auditctl -a always,exit -F path=/usr/bin/sudo -F perm=x -k priv`。

::: tip 易错点
auditctl 临时规则重启丢失，持久化写 /etc/audit/rules.d/*.rules。审计日志在 /var/log/audit/audit.log，量大要配轮转与外发。
:::

## 相关命令

[SELinux/ausearch](./selinux) · [last](./last) · [sudo](./su-sudo) · [journalctl](/commands/system/systemctl-journalctl)

## 官方文档

- auditctl：<https://man7.org/linux/man-pages/man8/auditctl.8.html>
- RHEL 审计：<https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html/security_hardening/auditing-the-system_security-hardening>