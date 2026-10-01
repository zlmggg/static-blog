---
title: Apache 与 Tomcat
description: HTTP 协议方法状态码 Cookie/Session/JWT、Apache（httpd/apache2）MPM/虚拟主机/htaccess、Tomcat 安装部署/server.xml/WAR、JVM 内存 GC 与调优
category: 服务
difficulty: 中级
---
# Apache 与 Tomcat

::: tip 本篇定位
理解 **HTTP 协议**，会部署配置 **Apache**（httpd/apache2），会安装 **Tomcat** 部署 Java Web（WAR、server.xml、manager），并掌握 **JVM 内存结构、GC 与基础调优**。
:::

---

## 一、HTTP 协议

HTTP 是浏览器/客户端与 Web 服务器之间的**应用层、无状态**协议（基于 TCP）。

### 1.1 请求方法

| 方法 | 语义 |
|---|---|
| GET | 获取资源（参数在 URL，幂等） |
| POST | 提交数据（参数在 body） |
| PUT | 更新/替换资源 |
| DELETE | 删除资源 |
| HEAD | 只要响应头 |
| PATCH | 部分更新 |

### 1.2 状态码

| 段 | 含义 | 常见 |
|---|---|---|
| 2xx | 成功 | 200 OK |
| 3xx | 重定向 | 301 永久、302 临时、304 Not Modified（缓存） |
| 4xx | 客户端错误 | 400 参数、401 未认证、403 禁止、404 不存在 |
| 5xx | 服务端错误 | 500 内部错误、502 网关、503 不可用、504 网关超时 |

### 1.3 请求/响应头

常见 Header：Host、Content-Type、Content-Length、User-Agent、Referer、Authorization、Cache-Control、Set-Cookie。

### 1.4 Cookie、Session 与 JWT

HTTP 无状态，需要维持登录态：

| 方案 | 原理 | 特点 |
|---|---|---|
| Cookie | 服务器下发、浏览器每次自动携带 | 存客户端，有大小限制 |
| Session | 服务端存状态，靠 Cookie 里的 session id 关联 | 服务端存，多机要共享 session |
| JWT | 服务端签发签名 token（Header.Payload.Signature），客户端携带 | 无状态、可跨服务，签发后难即时作废 |

---

## 二、Apache 安装

Apache HTTP Server（httpd）是老牌 Web 服务器。

### 2.1 RHEL/Rocky（服务名 httpd）

```bash
sudo dnf install -y httpd
sudo systemctl enable --now httpd
# 配置 /etc/httpd/conf/httpd.conf、conf.d/；站点 /var/www/html；日志 /var/log/httpd/
```

### 2.2 Debian/Ubuntu（服务名 apache2）

```bash
sudo apt install -y apache2
sudo systemctl enable --now apache2
# /etc/apache2/；站点 /var/www/html；日志 /var/log/apache2/
```

### 2.3 MPM 工作模式

| MPM | 模型 | 特点 |
|---|---|---|
| prefork | 多进程、每进程一个请求、无线程 | 稳定、兼容非线程安全模块（如老 PHP），内存占用高 |
| worker | 多进程 + 每进程多线程 | 内存省、并发较好 |
| event | 类似 worker，优化 keep-alive | **默认推荐** |

RHEL 编辑 `/etc/httpd/conf.modules.d/` 选择；Debian `a2dismod mpm_prefork && a2enmod mpm_event`。

---

## 三、Apache 配置

### 3.1 虚拟主机

Debian（站点配置 + 启用）：

```bash
sudo cp /etc/apache2/sites-available/000-default.conf /etc/apache2/sites-available/a.com.conf
```

```apache
<VirtualHost *:80>
    ServerName www.a.com
    DocumentRoot /data/www/a
    ErrorLog ${APACHE_LOG_DIR}/a_error.log
    CustomLog ${APACHE_LOG_DIR}/a_access.log combined
</VirtualHost>
```

```bash
sudo a2ensite a.com.conf
sudo systemctl reload apache2
```

RHEL 在 `/etc/httpd/conf.d/a.conf` 写 VirtualHost。

### 3.2 目录访问控制

```apache
<Directory /data/www/a>
    Require all granted
    Options -Indexes +FollowSymLinks
    AllowOverride All        # 允许 .htaccess（None 性能更好）
</Directory>
```

### 3.3 .htaccess 与认证

`.htaccess` 可在不改主配置的情况下做目录级控制（重写、认证、缓存），但每次请求读取、有性能开销，能用主配置就用主配置。

基础认证：

```bash
htpasswd -c /etc/apache2/.htpasswd tom
```

```apache
<Directory /data/www/private>
    AuthType Basic
    AuthName "Private"
    AuthUserFile /etc/apache2/.htpasswd
    Require valid-user
</Directory>
```

### 3.4 常用模块命令（Debian）

```bash
a2enmod rewrite ssl headers expires     # 启用模块
a2dismod ...
a2ensite / a2dissite
apache2ctl configtest                   # 检查配置
```

---

## 四、Tomcat 安装

Tomcat 是 Java 的 Servlet/JSP 容器，运行 Java Web 应用。

### 4.1 先装 JDK

```bash
sudo dnf install -y java-17-openjdk java-17-openjdk-devel     # RHEL
sudo apt install -y openjdk-17-jdk                            # Debian
java -version
# JDK LTS：8、11、17、21；新框架（Spring Boot 3）需 17+
```

### 4.2 二进制安装

```bash
# https://tomcat.apache.org/ 下载 Tomcat 10（注意包名变化，见下）
tar -xzf apache-tomcat-10.1.34.tar.gz -C /usr/local/
ln -s /usr/local/apache-tomcat-10.1.34 /usr/local/tomcat

/usr/local/tomcat/bin/startup.sh        # 启动
/usr/local/tomcat/bin/shutdown.sh       # 停止
# 访问 http://IP:8080
```

### 4.3 Docker

```bash
docker run -d --name tomcat -p 8080:8080 tomcat:10.1.34-jdk17
```

### 4.4 Tomcat 目录

| 目录 | 内容 |
|---|---|
| bin | 启动/停止脚本 |
| conf | server.xml、web.xml、tomcat-users.xml |
| lib | 依赖 jar |
| webapps | 应用部署目录（放 WAR 自动解压） |
| logs | 日志（catalina.out） |
| work / temp | 编译 JSP、临时文件 |

### 4.5 端口（server.xml）

| 端口 | 用途 |
|---|---|
| 8080 | HTTP 访问 |
| 8005 | Shutdown 关闭端口 |
| 8009 | AJP（与 Apache httpd 联动，新版默认禁用） |

::: warning Tomcat 版本与包名
**Tomcat 10+ 把 `javax.*` 改成了 `jakarta.*`**。老的基于 javax 的 WAR 部署到 Tomcat 10 会报错，这类老应用应使用 **Tomcat 9**；新开发用 Tomcat 10/11。
:::

---

## 五、Tomcat 部署与配置

### 5.1 部署 WAR

```bash
cp app.war /usr/local/tomcat/webapps/ROOT.war   # ROOT 作为根应用
# 或放到 webapps/app，访问 /app/；Tomcat 自动解压部署
```

### 5.2 manager 管理后台

`conf/tomcat-users.xml` 加角色和用户：

```xml
<role rolename="manager-gui"/>
<user username="admin" password="Admin@123" roles="manager-gui"/>
```

manager 默认只允许本机/需配 RemoteAddrValve 放行，生产务必改强密码或不启用。

### 5.3 与 Nginx/Apache 配合

生产通常由 Nginx 处理静态、HTTPS，动态请求反代到 Tomcat 8080，Tomcat 只监听本机。

---

## 六、JVM 基础

### 6.1 运行时内存结构

| 区域 | 说明 | 是否线程共享 |
|---|---|---|
| 堆 Heap | 对象实例，GC 主战场（新生代 Eden/S0/S1 + 老年代） | 共享 |
| 方法区/元空间 Metaspace | 类信息、常量（JDK8+ 在本地内存） | 共享 |
| 虚拟机栈 | 方法栈帧（局部变量、操作数栈） | 私有 |
| 程序计数器 | 当前执行位置 | 私有 |
| 本地方法栈 | native 方法 | 私有 |

### 6.2 GC 与判定

- 对象是否回收靠**可达性分析**（从 GC Roots 出发不可达即回收）；
- GC 类型：Minor GC（新生代）、Major/Full GC（老年代/整堆）。

### 6.3 垃圾收集器

| 收集器 | 特点 |
|---|---|
| Serial / Serial Old | 单线程，小内存/客户端 |
| Parallel Scavenge | 吞吐量优先（JDK8 默认之一） |
| CMS | 低停顿，已废弃（JDK14 移除） |
| **G1** | 分区、可预测停顿，**JDK9+ 默认** |
| ZGC / Shenandoah | 超低停顿、大堆 |

### 6.4 常用 JVM 参数

```bash
-Xms512m -Xmx512m                 # 堆初始/最大（生产常设相同，避免动态扩缩）
-Xss512k                          # 线程栈大小
-XX:MetaspaceSize=128m
-XX:+UseG1GC                      # 使用 G1
-XX:MaxGCPauseMillis=200
# Tomcat 可写在 bin/setenv.sh 的 JAVA_OPTS/CATALINA_OPTS
```

### 6.5 排查工具

| 工具 | 用途 |
|---|---|
| jps | 查看 Java 进程 |
| jstat -gcutil pid 1000 | 看 GC/各区使用 |
| jmap -dump:format=b,file=h.hprof pid | 堆转储（分析内存泄漏） |
| jstack pid | 线程栈（分析死锁、CPU 高） |
| jconsole / VisualVM / Arthas | 可视化 / 在线诊断（Arthas 强大） |

---

## 面试自测

1. 401、403、502、504 分别是什么含义？
2. Cookie、Session、JWT 的区别？多台服务器 Session 怎么处理？
3. Apache 的 prefork/worker/event 有什么区别？
4. Tomcat 8080、8005、8009 端口分别做什么？
5. 为什么老 WAR 放到 Tomcat 10 会报错？
6. JVM 堆和栈、元空间分别存什么？
7. Minor GC 和 Full GC 的区别？G1 有什么特点？
8. CPU 飙高/内存泄漏分别用什么工具、怎么定位？

## 相关速查

- [Linux 命令速查](/reference/linux-commands)
- HTTP 标准（MDN）：https://developer.mozilla.org/zh-CN/docs/Web/HTTP
- Apache 文档：https://httpd.apache.org/docs/
- Tomcat 文档：https://tomcat.apache.org/tomcat-10.1-doc/
- JVM 调优（Oracle）：https://docs.oracle.com/en/java/javase/17/docs/specs/man/java.html
