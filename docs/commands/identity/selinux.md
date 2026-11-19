---
title: "SELinux · 强制访问控制"
description: "getenforce/setenforce 看与切模式、semanage 管端口/上下文、restorecon/chcon 修标签、ausearch 排拒绝。RHEL 系「权限对了还拒绝」的隐藏原因，中文详解。"
---

# SELinux · 强制访问控制

> 命令手册 · [用户与权限](/commands/identity/) ｜ 频率：偶尔用
> chmod 对了、属主对了，服务还是 Permission denied？RHEL 系多半是 SELinux 挡的。它是独立于传统权限的第二道门。

## 一句话用途

在 traditional 权限之外再加一层强制访问控制，限制进程"即使有权限也只能访问特定标签的资源"。

## 三种模式

```bash
getenforce                   # Enforcing / Permissive / Disabled
sudo setenforce 0            # 临时切 Permissive（只记录不拦）
sudo setenforce 1            # 切回 Enforcing
```

| 模式 | 行为 |
|---|---|
| Enforcing | 拦截+记录（生产默认） |
| Permissive | 只记录不拦（排障用） |
| Disabled | 完全关闭（需改配置重启） |

永久改：`/etc/selinux/config` 的 `SELINUX=`。

::: warning 别一上来就关 SELinux
遇到拒绝先 `setenforce 0` 验证是不是它，确认后**修标签/策略**再切回 1，而不是永久 Disabled。关掉等于少一道防线。
:::

## 标签与修复

每个文件/进程有 SELinux 上下文（`ls -Z` 看）。服务只能访问特定标签的文件。

```bash
ls -Z /var/www               # 看文件上下文
ps -eZ | grep nginx          # 看进程上下文
sudo restorecon -Rv /var/www # 按策略恢复默认标签（最常用）
sudo chcon -t httpd_sys_content_t /data/web   # 临时改标签
sudo semanage fcontext -a -t httpd_sys_content_t "/data/web(/.*)?"  # 永久规则
sudo restorecon -Rv /data/web
```

## 端口与布尔

```bash
sudo semanage port -a -t http_port_t -p tcp 8080   # 允许 nginx 听 8080
sudo semanage port -l | grep http                  # 看允许的端口
getsebool -a | grep httpd                          # 看布尔开关
sudo setsebool -P httpd_can_network_connect on     # 允许 nginx 反代连后端
```

## 排拒绝

```bash
sudo ausearch -m avc -ts recent        # 看最近的 SELinux 拒绝
sudo sealert -a /var/log/audit/audit.log   # 图形化分析+建议（setroubleshoot）
```

## 运维实战

**nginx 反代报权限错**：传统权限都对，是 SELinux 默认禁止 httpd 发起网络连接——`setsebool -P httpd_can_network_connect on`。
**网站放非默认目录**：/data/web 标签不对，semanage fcontext 加规则 + restorecon。
**自定义端口**：nginx 听 8080 被拒，semanage port 加 http_port_t。

## 相关命令

[chmod](./chmod) · [auditctl/ausearch](./audit) · [Nginx 实战](/services/web/nginx/04-实战) · [chattr](./chattr-lsattr)

## 官方文档

- SELinux：<https://selinuxproject.org/page/Main_Page>
- RHEL SELinux 指南：<https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html/using_selinux/index>