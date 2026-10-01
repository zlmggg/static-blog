---
category: 监控
difficulty: 中级
---

# JumpServer 堡垒机实战

::: tip 本篇定位
部署开源堡垒机 JumpServer，实现资产集中纳管、统一登录入口、访问授权控制和操作全程审计。本篇以 v4.10.17 LTS 为例（容器化部署），并说明 v5.0.0 的情况。
:::

## 一、堡垒机概述

### 1.1 跳板机与堡垒机

- **跳板机**：一台作为统一入口的服务器，运维人员先登录跳板机、再跳到内网其他机器。它解决了"入口统一"，但**无法控制和审计登录后的操作行为**，一旦跳板机被攻破，内网门户大开。
- **堡垒机**：在跳板机基础上，增加了身份认证、访问授权、操作控制和全程审计，能记录"谁、在什么时间、对哪台资产、做了什么"，是运维安全管控的核心设施。

### 1.2 4A 理念

堡垒机的核心能力常概括为 4A：

| 能力 | 含义 |
|---|---|
| Authentication（认证） | 确认"你是谁"，支持密码、MFA 多因子、统一身份源 |
| Account（账号） | 集中管理登录账号，并托管资产上的系统账号与密码 |
| Authorization（授权） | 控制"你能访问哪些资产、用哪个账号、能做什么动作" |
| Audit（审计） | 对登录、命令、文件传输、操作录像进行记录和回放 |

### 1.3 JumpServer 简介与组件

JumpServer 是开源堡垒机（GPL v2.0），使用 Python/Django 开发，符合 4A，提供 Web Terminal，支持 SSH、Telnet、RDP、VNC、数据库、K8s 等多种资产，支持分布式、跨机房部署。

各组件分工：

| 组件 | 职责 |
|---|---|
| Core | 核心组件，Django 提供 API、认证、调度，其他组件依赖它启动 |
| Koko | 提供 SSH/Telnet 字符型（Linux/Unix）资产连接 |
| Lion | 提供 Windows RDP 等图形资产连接（基于 Guacamole） |
| Chen | 提供数据库资产连接 |
| Web | 前端 Nginx，对外提供 Web 页面 |
| PostgreSQL / Redis | 数据存储与缓存，默认以容器方式一起部署 |

![JumpServer 组件架构：运维人员经 Web 前端访问 Core，Core 依赖 PostgreSQL、Redis，并通过 Koko、Lion、Chen 分别连接 Linux、Windows、数据库资产](/diagrams/jumpserver-01.svg)

### 1.4 版本选择

- **v5.0.0**：2026-09-17 发布的最新大版本，主打全新原生客户端和内置 AI；但属于大版本的首个（.0）版本，刚发布不久，生产采用通常会先观察一段时间。
- **v4.10.17 LTS**：成熟的长期支持版本，文档和实践丰富、稳定。

::: tip 学习和生产建议
学习或生产部署，建议先用 **v4.10.17 LTS**，等 v5 经过几个小版本打磨后再升级。想用最新版时，只需把下文命令里的版本号替换为 `v5.0.0`，安装流程一致。官方对 v4 早期版本也建议先升到最新 v4.10.x LTS 再升 v5。
:::

## 二、部署 JumpServer

### 2.1 环境要求

官方建议配置为 **4 核 CPU / 8 GB 内存 / 100 GB 磁盘**（因为要同时运行 Core、Koko、Lion、Chen、PostgreSQL、Redis 等多个容器）。小规格机器（如 2 核 2 GB）可以用于学习体验，但会比较吃紧，建议关闭暂时不用的组件、加 swap。操作系统支持主流 Debian/RedHat 系发行版，内核建议 4.0 以上。

### 2.2 前置条件

JumpServer 基于 Docker 部署，先安装 Docker 和 Compose 插件：

```bash
# 安装 Docker（以 Ubuntu 为例）
apt update
apt install -y docker.io docker-compose-plugin
systemctl enable --now docker
docker version
docker compose version
```

### 2.3 下载安装器并安装

```bash
cd /opt
wget https://github.com/jumpserver/installer/releases/download/v4.10.17/jumpserver-installer-v4.10.17.tar.gz
tar -xf jumpserver-installer-v4.10.17.tar.gz
cd jumpserver-installer-v4.10.17
```

::: tip GitHub 下载慢
安装器和后续镜像都在 GitHub/Docker Hub，直连慢时可使用加速代理下载，或在本机下载后上传到服务器 `/opt`；镜像拉取慢可配置 Docker 镜像加速器。
:::

执行安装（交互式）：

```bash
./jmsctl.sh install
```

安装过程会依次询问，一般可直接回车使用默认值：

- 是否自动配置防火墙；
- 是否安装内置 PostgreSQL 和 Redis（学习环境选是，用容器自建）；
- 各服务端口（Web 默认 80、SSH 默认 2222）；
- `SECRET_KEY` 和 `BOOTSTRAP_TOKEN`（留空则自动生成）；
- 是否完成后启动。

安装完成后启动全部服务：

```bash
./jmsctl.sh start
docker ps
```

正常会看到 `jms_core`、`jms_koko`、`jms_lion`、`jms_chen`、`jms_web`、`jms_postgresql`、`jms_redis` 等容器处于 Up 状态。

### 2.4 首次登录

浏览器访问 `http://服务器IP`（若改过 Web 端口则带端口）：

- 用户名：`admin`
- 密码：`ChangeMe`（v4 默认；v3 为 admin/admin）

首次登录强制修改密码，且不能使用原密码。改完用新密码重新登录。

也可以通过 SSH 连接 JumpServer 的 2222 端口：

```bash
ssh -p 2222 admin@服务器IP
```

::: tip jmsctl 常用命令
`./jmsctl.sh start|stop|restart` 启停、`./jmsctl.sh status` 状态、`./jmsctl.sh uninstall` 卸载、`./jmsctl.sh upgrade` 升级、`./jmsctl.sh help` 查看全部。配置文件在 `/opt/jumpserver/config/config.txt`，改端口等需先 stop、改完再 start。
:::

### 2.5 配置文件与默认端口

统一配置文件为 `/opt/jumpserver/config/config.txt`，常用配置项：

| 配置项 | 含义 | 默认值 |
|---|---|---|
| `HTTP_PORT` / `HTTPS_PORT` | Web 访问端口 | 80 / 443 |
| `SSH_PORT` | SSH/SFTP 资产连接端口 | 2222 |
| `SECRET_KEY` | 数据加密密钥，生产务必自定义并妥善保存 | 安装时生成 |
| `BOOTSTRAP_TOKEN` | 各组件向 Core 注册用的令牌 | 安装时生成 |
| `DB_*` | 数据库连接（内置 PostgreSQL） | 容器自建 |
| `REDIS_*` | Redis 连接 | 容器自建 |

::: warning SECRET_KEY 不要随意变更
SECRET_KEY 用于加密数据库中保存的资产密码，改动会导致已保存的密码无法解密。重装或迁移时要保持 SECRET_KEY、BOOTSTRAP_TOKEN 与原环境一致。
:::

### 2.6 备份、升级与卸载

- **备份**：核心是数据库和配置。用 `./jmsctl.sh backup_db` 备份数据库，并备份 `/opt/jumpserver/config/config.txt`、安装目录下的密钥文件；
- **升级**：下载新版安装器，在新版目录执行 `./jmsctl.sh upgrade`，升级前先备份数据库；
- **卸载**：`./jmsctl.sh uninstall` 会停止并删除容器，按提示选择是否保留数据卷（数据库）。

## 三、用户与资产

JumpServer 里有三类容易混淆的"用户"，先理清：

![三类用户与资产的关系：登录用户经授权规则访问资产，资产关联特权账号用于管理，登录用户连接时使用资产上的普通系统账号](/diagrams/jumpserver-02.svg)

1. **登录用户**：人用来登录 JumpServer 的账号，在 JumpServer 中创建（如 wang、admin）。
2. **特权账号（旧称管理用户）**：资产上具有 root/Administrator 或 sudo ALL 权限的账号，JumpServer 用它来采集资产信息、推送创建普通账号。
3. **普通系统账号（旧称系统用户）**：登录用户连接资产时实际使用的业务账号，一般不给管理权限。

### 3.1 创建登录用户与用户组

JumpServer 登录用户有三种角色：系统管理员、普通用户、系统审计员。

- 在 **用户管理 → 用户** 中创建用户（如 wang），邮箱不能重复；
- 在 **用户组** 中创建组（如 development），把用户加入组，便于按组批量授权；
- 可对用户启用/禁用、重置 MFA。

### 3.2 多因子认证（MFA）

在用户设置中开启 MFA 后，登录时除了账号密码，还要输入手机验证器（如 Google Authenticator）生成的动态码，安全性更高。管理员可在用户列表中为用户开启，用户首次登录时扫码绑定。

### 3.3 通过账号模板创建系统账号

新版推荐在 **账号管理 → 账号模板** 中统一创建特权账号和普通账号模板，不必为每台资产重复配置：

- **特权账号模板**：填 root（或管理员）用户名和密码/密钥，用于资产采集和管理；
- **普通账号模板**：可设置用户名、密文策略（随机生成或指定），授权后 JumpServer 会自动在资产上创建该账号。

::: tip 生产实践
企业里通常已用自动化工具在所有服务器上统一创建好系统账号（UID、命名一致），JumpServer 直接引用即可；学习环境可让 JumpServer 通过特权账号自动创建普通账号。
:::

### 3.4 创建资产与节点

- 在 **资产管理 → 资产** 中创建资产，选择类型（主机/网络设备/数据库等），填 IP、管理端口，选择管理账号（特权账号）并测试可连接；
- 用**节点（树状分组）**对资产分类，如按"生产/测试""机房/业务线"组织；子节点资产可继承节点上的授权。

### 3.5 测试资产与账号改密

- **测试连通**：资产详情里用特权账号测试，JumpServer 会通过它登录资产、采集主机名、硬件等信息；测试失败多为网络不通、账号无 sudo 权限或密钥未配置；
- **账号收集**：可让 JumpServer 通过特权账号扫描资产上已存在的系统账号并纳管；
- **批量改密**：支持对纳管的账号定期轮换密码（随机生成并密文保存），避免长期使用固定密码；
- 资产信息变更后可手动刷新，保证与实际一致。

## 四、授权与访问

### 4.1 创建资产授权规则

在 **权限管理 → 资产授权** 中新建规则，把"用户/用户组"和"资产/节点"以及"可使用的系统账号"绑定：

- 选择被授权的用户或用户组；
- 选择资产或节点（节点内资产自动继承）；
- 选择可使用的系统账号（普通账号）；
- 勾选协议（SSH、SFTP 用于登录和文件传输）；
- 可设置授权的生效时间段。

规则生效后，普通账号会被自动推送到对应资产。

### 4.2 Web 终端访问

普通用户登录后，在资产列表里选择有权限的主机，点击连接即可在浏览器中打开 Web Terminal 操作；也可点页面上的 Web 终端图标。文件上传下载通过 Web 界面或 SFTP 完成。

### 4.3 SSH 与文件传输

除了浏览器，还能用本地终端直连 JumpServer 的 2222 端口，再选择资产：

```bash
ssh -p 2222 登录用户@服务器IP
```

文件传输可用 SFTP 工具（如 FileZilla）连接 2222 端口进行上传下载。

### 4.4 数据库资产

数据库作为一类资产纳管：先在账号模板中创建数据库账号，在资产中添加数据库（填主机、端口、类型），授权规则中针对具体数据库资产授权（数据库授权不支持只按节点），之后即可在 Web 端或通过 SSH 连接数据库。

### 4.5 登录限制与连接令牌

- 在系统设置里可限制用户登录的来源 IP、设置会话超时时间，长时间无操作自动断开；
- 支持为用户或资产生成有时效的**连接令牌**，用于临时授权或免登录快速连接；
- 用户可在个人设置查看自己的授权资产、修改密码和 MFA；
- 管理员可随时禁用某个登录用户，立即阻断其访问。

## 五、会话审计

### 5.1 在线与历史会话

- **会话管理 → 在线会话**：查看当前正在进行的连接和实时执行的命令，管理员可**强制中断（踢出）**用户会话；
- **历史会话**：查看过去所有连接记录，支持在线回放操作录像、查看每条命令，也可下载录像离线播放（离线播放需用官方 VideoPlayer）。

### 5.2 命令历史与审计

在历史会话中可查看该会话执行过的全部命令，配合系统审计员角色，由专人负责审计录像和高危操作。审计员账号默认只看审计内容、不参与运维，实现职责分离。

### 5.3 命令过滤器

命令过滤器用于禁止执行危险命令，防止误操作或恶意行为：

1. 在 **命令过滤 → 命令组** 中定义要管控的命令（如 `rm -rf /`、`shutdown`、`mkfs` 等）；
2. 创建命令过滤规则，指定哪些用户/系统账号、在哪些资产上应用，设置动作（允许/拒绝/复核）和优先级；
3. 将过滤器绑定到系统账号；
4. 用户执行命令时按优先级逐条匹配：命中允许则放行，命中拒绝则禁止，都未命中则默认允许。

::: tip 复核动作
除允许、拒绝外，规则动作还可设为"复核"：用户执行该命令时需提交申请，管理员审批通过后才放行，适用于高危但确有需要的操作。
:::

### 5.4 分布式多节点部署

当资产数量大或跨机房时，JumpServer 支持分布式：在额外节点上只部署 Koko、Lion、Chen 等接入组件，通过 `BOOTSTRAP_TOKEN` 注册到同一个 Core 和数据库，由 Core 统一调度。这样可把连接、录像的负载分散到多个节点，不同机房就近接入。安装新节点时在安装向导中选择对应组件、填写主 Core 地址和相同的 BOOTSTRAP_TOKEN 即可。学习环境单机部署即可。

## 面试自测

1. 跳板机和堡垒机有什么区别？跳板机存在什么安全短板？
2. 堡垒机的 4A 分别指什么？各自解决什么问题？
3. JumpServer 中 Core、Koko、Lion、Chen 各负责连接哪类资产？
4. JumpServer 依赖哪些数据库/缓存？默认是怎么部署的？
5. v5.0.0 和 v4.10.17 LTS 该怎么选？为什么生产不急于追大版本的 .0 版本？
6. JumpServer 官方推荐的硬件配置？小内存机器学习要注意什么？
7. 说清 JumpServer 里三类"用户"（登录用户、特权账号、普通系统账号）的区别和作用。
8. 特权账号为什么必须是 root/管理员权限？它被用来做什么？
9. 什么是账号模板？为什么推荐用它而不是逐台资产创建账号？
10. 用户组和节点分别用于解决什么问题？
11. MFA 是什么？开启后登录流程有什么变化？
12. 一台新 Linux 主机要纳管进 JumpServer，完整步骤是什么？
13. 资产授权规则包含哪几个要素？节点授权有什么继承特性？
14. 用户通过哪几种方式访问资产？SSH 直连用哪个端口？
15. 文件上传下载通过什么协议、哪个端口？
16. 数据库资产的授权有什么注意事项？
17. 在线会话管理能做哪些操作？如何踢出一个正在进行的会话？
18. 历史会话的审计包含哪些内容？离线看录像需要什么？
19. 为什么要设置系统审计员角色、与运维角色分离？
20. 命令过滤器的工作流程是怎样的？匹配不到规则时默认放行还是拒绝？
21. 为什么说堡垒机是运维安全合规（等保）中的重要设施？

## 相关速查

- 命令速查：[Linux 命令速查](/reference/linux-commands)、[Docker 命令速查](/reference/docker-commands)
- 官方资源：
  - JumpServer 官网：https://www.jumpserver.org/
  - 官方文档（v4）：https://docs.jumpserver.org/zh/v4/
  - 快速入门：https://docs.jumpserver.org/zh/v4/quick_start/
  - 环境要求：https://docs.jumpserver.org/zh/v4/installation/setup_linux_standalone/requirements/
  - jmsctl 命令：https://docs.jumpserver.org/zh/v4/installation/jmsctl_sh/
  - 反向代理：https://docs.jumpserver.org/zh/v4/installation/proxy/
  - GitHub 主仓库：https://github.com/jumpserver/jumpserver
  - Installer 下载：https://github.com/jumpserver/installer/releases
  - v5 发布说明：https://www.jumpserver.com/blog/introducing-jumpserver-v5
  - 录像播放器：https://github.com/jumpserver/VideoPlayer/releases
