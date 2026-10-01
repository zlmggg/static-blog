---
category: Linux
difficulty: 初级
date: 2018-07-08
---

# Permission denied：属主/权限/umask/ACL 问题（2018-07-08）

## 现象

Nginx 访问 PHP 页面报 403，或者 PHP-FPM 写 session 文件失败：

```
WARNING: [pool www] child said into stderr: "Unable to write session data (files).
Please verify that the current setting of session.save_path is correct (/var/lib/php/session)"
```

手动 `curl` 报：

```
<html><head><title>403 Forbidden</title></head>
<body><center><h1>403 Forbidden</h1></center></body></html>
```

或者 SSH 登录后 `sudo` 报：

```
sudo: unable to open /var/lib/sudo/user/lecture: Permission denied
```

## 环境

- 发行版：CentOS Linux release 7.5.1804 (Core)
- 内核：`3.10.0-862.el7.x86_64`
- Nginx 1.12.2，PHP-FPM 7.1.30
- 网站根目录：`/usr/share/nginx/html/`

## 定位过程

### 1. 先看错误日志

```bash
# Nginx 错误日志
tail -20 /var/log/nginx/error.log
# 关键行：
# 2018/07/08 10:00:00 [error] 1234#0: *1 open() "/usr/share/nginx/html/index.php" failed (13: Permission denied)
```

错误码 `(13: Permission denied)` 就是权限问题。

### 2. 一层层拆路径权限

Linux 要访问一个文件，**路径上每一级目录都要有 x 权限**。用 namei 一次性看完：

```bash
namei -l /usr/share/nginx/html/index.php
# f: /usr/share/nginx/html/index.php
# drwxr-xr-x root  root  /usr
# drwxr-xr-x root  root  /usr/share
# drwxr-xr-x root  root  /usr/share/nginx
# drwxr-xr-x nginx nginx /usr/share/nginx/html
# -rw-r--r-- nginx nginx /usr/share/nginx/html/index.php
```

本例中路径每级都有 `o+x`，按理说 nginx 应该能读。那就要怀疑 SELinux 了。

### 3. 看进程实际以什么用户跑

```bash
ps -ef | grep nginx
# root      1234     1  0 ... nginx: master process
# nginx     1235  1234  0 ... nginx: worker process
# php-fpm  1236  1237  0 ... php-fpm: pool www
```

worker 进程是 `nginx` 用户，php-fpm 是 `apache` 用户（CentOS 默认）。
**Nginx 和 PHP-FPM 用户不一致**是导致跨目录读文件权限不够的常见原因。

### 4. 检查 SELinux

```bash
getenforce
# Enforcing   <- 开着的

# 看 nginx 访问这个文件时被 SELinux 拦了没
tail /var/log/audit/audit.log | grep denied
# type=AVC msg=audit(1531011600.123:456): avc:  denied  { search } for  pid=1235 comm="nginx" name="html" dev="sda2" ino=12345 scontext=system_u:system_r:httpd_t:s0 tcontext=unconfined_u:object_r:default_t:s0 tclass=dir
```

看到 `avc: denied` 就是 SELinux 在拦。

### 5. 检查 ACL

```bash
getfacl /usr/share/nginx/html/index.php
# file: index.php
# user::rw-
# user:apache:---    <- 额外加了一条 deny
# group::r--
```

## 根因

运维把网站文件 scp 上来时属主变成了 `root:root`，权限是 `600`，Nginx worker（`nginx` 用户）根本读不到。同时 SELinux 上下文因为文件是从 home 目录复制过来的，类型是 `default_t` 而不是 `httpd_sys_content_t`，被策略拦截。两层问题叠加，导致 403。

## 解决步骤

### 1. 临时止血

先确认是不是 SELinux 的问题，临时切成 Permissive 验证：

```bash
setenforce 0
# 再 curl 一次，如果通了，就是 SELinux 的问题
curl -I http://localhost/index.php
```

**不要在生产上长期关 SELinux**，验证完立刻 `setenforce 1`。

### 2. 修文件属主和权限

```bash
# 网站文件让 nginx 能读
chown -R nginx:nginx /usr/share/nginx/html/
find /usr/share/nginx/html/ -type d -exec chmod 755 {} \;
find /usr/share/nginx/html/ -type f -exec chmod 644 {} \;
```

需要 PHP-FPM 写的目录（上传、缓存、session）：

```bash
chown -R nginx:nginx /var/lib/php/session/
chmod 730 /var/lib/php/session/
```

### 3. 修 SELinux 上下文

```bash
# 把网站目录标成 httpd 可读
semanage fcontext -a -t httpd_sys_content_t "/usr/share/nginx/html(/.*)?"
restorecon -Rv /usr/share/nginx/html/

# 如果是可写目录，标成 httpd_sys_rw_content_t
semanage fcontext -a -t httpd_sys_rw_content_t "/var/lib/php/session(/.*)?"
restorecon -Rv /var/lib/php/session/
```

### 4. 检查 umask 对不对

`/etc/profile` 或 `/etc/bashrc` 里默认 umask 不要太离谱：

```bash
umask
# 0022  <- 正确，新建文件 644，目录 755
# 如果是 0077，新建文件别人都读不到
```

## 验证与预防

- `curl -I http://localhost/` 返回 200。
- PHP session 目录里能正常生成 sess_ 文件。
- 记住排权限问题的顺序：**先看 error log → namei -l 拆路径 → ps 看进程用户 → getenforce 看 SELinux → getfacl 看 ACL**。
- 部署脚本里统一用 `rsync --chown=nginx:nginx` 发布，不要 scp 完手动 chmod。

## 相关

- 命令速查：[Linux 命令速查](/reference/linux-commands)
- 服务方向：[Nginx 502 Bad Gateway](/cases/t-nginx-502)
- 服务方向：[PHP-FPM 进程池打满 502](/cases/t-phpfpm-502)
