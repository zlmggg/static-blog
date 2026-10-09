---
category: 监控
difficulty: 初级
---

# Prometheus 实战 02：部署 Prometheus 服务端

> **Prometheus 实战系列（共 10 篇）**
> ← 上一篇 [Prometheus 实战 01](./monitor-prometheus-01-intro) ｜ 下一篇 [Prometheus 实战 03](./monitor-prometheus-03-exporters-grafana) →
> [返回监控索引](./monitor)

## 阶段二：部署 Prometheus 监控系统

### 阶段目标

- 完成监控服务器的初始化（国内软件源、时间同步、防火墙规划）；
- 用 5 种方式之一把 Prometheus 跑起来（重点掌握**二进制**和 **Docker/Compose**）；
- 看懂并会改 Prometheus 主配置文件；
- 完成 Node Exporter、Grafana、Pushgateway 的部署与对接，最终看到主机监控大屏、能用 Pushgateway 上报自定义指标。

本阶段是全书最重要的上机阶段，请在监控服务器 `monitor`（示例 10.0.0.10）上操作。

---

### 2.0 监控服务器初始化

#### 2.0.1 把系统软件源换成国内源

官方软件源服务器在国外，装软件又慢又容易断。先换成阿里云源（也可以换成清华源，两者二选一即可）。

**操作目录与用户**：以下命令需要 root 权限。先切到 root：

```bash
sudo -i
```

`sudo -i` 会加载 root 的环境变量、直接进入 root 的家目录，提示符变成 `root@...`。后续凡是看到"用 root 操作"，都指这种状态。输入 `exit` 可退回普通用户。

**Ubuntu 22.04（源文件是 /etc/apt/sources.list）**，先备份再替换：

```bash
cp /etc/apt/sources.list /etc/apt/sources.list.bak
sed -i 's@//.*archive.ubuntu.com@//mirrors.aliyun.com@g' /etc/apt/sources.list
sed -i 's@//.*security.ubuntu.com@//mirrors.aliyun.com@g' /etc/apt/sources.list
```

参数解释：`cp 源 目标` 是复制备份；`sed -i` 表示直接修改文件；`s@旧@新@g` 表示把文件里所有旧文本替换成新文本，`@` 只是分隔符（用 `/` 也行，但网址里 `/` 多，用 `@` 看得清楚）。

**Ubuntu 24.04（源文件改成了 DEB822 格式：/etc/apt/sources.list.d/ubuntu.sources）**：

```bash
cp /etc/apt/sources.list.d/ubuntu.sources /etc/apt/sources.list.d/ubuntu.sources.bak
sed -i 's@//archive.ubuntu.com@//mirrors.aliyun.com@g' /etc/apt/sources.list.d/ubuntu.sources
sed -i 's@//security.ubuntu.com@//mirrors.aliyun.com@g' /etc/apt/sources.list.d/ubuntu.sources
```

**想用清华源**：把上面命令里的 `mirrors.aliyun.com` 换成 `mirrors.tuna.tsinghua.edu.cn` 即可。

刷新软件包索引：

```bash
apt update
```

预期输出（最后两行类似即可）：

```text
Get:7 https://mirrors.aliyun.com/ubuntu noble InRelease [267 kB]
Reading package lists... Done
Building dependency tree... Done
All packages are up to date.
```

如果看到 `Hit:`、`Get:` 都是 `mirrors.aliyun.com`，说明换源成功。

#### 2.0.2 安装必备小工具

精简安装的系统常常连 `wget`、`tar` 都没有，先装上：

```bash
apt -y install wget curl tar gzip vim bash-completion lsof
```

参数解释：`-y` 表示所有询问都自动回答 yes；后面一串是要装的包名——`wget`/`curl` 下载用、`tar`/`gzip` 解压用、`vim` 编辑器、`lsof` 查端口占用。

验证：

```bash
wget --version | head -1
curl --version | head -1
```

预期输出：

```text
GNU Wget 1.21.4 built on linux-gnu.
curl 8.5.0 (x86_64-pc-linux-gnu) ...
```

#### 2.0.3 设置主机名、时区、时间同步

**主机名**（监控服务器就叫 monitor）：

```bash
hostnamectl set-hostname monitor
bash
```

`bash` 是重新加载一次 shell，让提示符立刻显示新主机名。

**时区**（很多默认是 UTC，日志时间会差 8 小时）：

```bash
timedatectl set-timezone Asia/Shanghai
timedatectl
```

预期输出关键两行：

```text
               Local time: Mon 2026-09-28 11:30:00 CST
           Universal time: Mon 2026-09-28 03:30:00 UTC
                 Time zone: Asia/Shanghai (CST, +0800)
```

**时间同步**：监控数据对时间戳很敏感，机器时间不准会导致 Grafana 图错位、告警延迟。

```bash
apt -y install chrony
systemctl enable --now chrony
systemctl is-active chrony
```

预期输出：`active`。查看同步状态：

```bash
chronyc sources | head -5
```

看到以 `^` 开头、带 IP 或域名的时间服务器列表即正常。

#### 2.0.4 防火墙规划

监控集群要用到一批端口，先心里有数（**先别急着一刀切关防火墙**，按表放行更安全）：

| 端口 | 组件 | 谁需要访问 |
| --- | --- | --- |
| 9090 | Prometheus | 运维浏览器、Grafana、联邦上级 |
| 9093 | Alertmanager | 运维浏览器、Prometheus |
| 3000 | Grafana | 运维浏览器 |
| 9091 | Pushgateway | 业务脚本、Prometheus |
| 9115 | Blackbox Exporter | Prometheus |
| 9100 | Node Exporter | Prometheus |

Ubuntu 默认防火墙是 `ufw`，默认不启用。如果启用了，按端口放行：

```bash
ufw allow 9090/tcp
ufw allow 9093/tcp
ufw allow 3000/tcp
ufw allow 9091/tcp
ufw allow 9115/tcp
ufw allow 9100/tcp
ufw --force enable
ufw status
```

参数解释：`allow 端口/tcp` 放行 TCP；`--force enable` 跳过确认直接启用。

RHEL/Rocky 系用 `firewalld`，对应命令（以 9090 为例，其余端口照做）：

```bash
firewall-cmd --add-port=9090/tcp --permanent
firewall-cmd --reload
```

::: warning
如果是云服务器（阿里云/腾讯云/AWS 等），除了机器内部防火墙，还要在**云控制台的"安全组"**里放行这些端口，两处都通才能访问。
:::

---

### 2.1 部署 Prometheus

#### 2.1.1 五种部署方式对比

| 方式 | 适合场景 | 本手册建议 |
| --- | --- | --- |
| apt/yum 包安装 | 快速体验 | Ubuntu 仓库版本偏旧，生产不推荐 |
| 二进制安装 | 生产环境（虚拟机/物理机） | **重点掌握，生产首选** |
| Docker 启动 | 快速容器化部署 | 容器环境推荐 |
| Docker Compose | 一整套组件编排 | **组件多时最省心，重点掌握** |
| Ansible 批量部署 | 几十上百台机器批量装 | 了解，给链接 |
| Kubernetes | K8s 集群 | 阶段十一专门讲 |

#### 2.1.2 方法一：Ubuntu apt 包安装（体验用）

直接安装：

```bash
apt -y install prometheus
systemctl status prometheus --no-pager
```

预期输出关键行：

```text
● prometheus.service - Monitoring system and time series database
     Loaded: loaded (/lib/systemd/system/prometheus.service; enabled)
     Active: active (running) since ...
```

安装包还会顺带装上 Node Exporter：

```bash
systemctl status prometheus-node-exporter --no-pager
ss -ntlp | grep -E '9090|9100'
```

预期输出：

```text
LISTEN 0 4096 *:9090 *:*
LISTEN 0 4096 *:9100 *:*
```

::: warning
Ubuntu 24.04 仓库里的 Prometheus 是 2.45.x，22.04 更是 2.31.x，**都不是当前稳定版 3.x**。生产环境请用下面的二进制或容器方式安装指定版本，不要直接用仓库版本。卸载体验版用：`apt -y purge prometheus prometheus-node-exporter`。
:::

**RHEL/Rocky/CentOS 的 yum 仓库**：系统默认不带 Prometheus 源，需要配置 packagecloud 仓库（服务器在国外）：

```ini
[prometheus]
name=prometheus
baseurl=https://packagecloud.io/prometheus-rpm/release/el/$releasever/$basearch
repo_gpgcheck=1
enabled=1
gpgkey=https://packagecloud.io/prometheus-rpm/release/gpgkey
gpgcheck=1
```

把上面内容保存为 `/etc/yum.repos.d/prometheus.repo`，再执行 `yum makecache && yum -y install prometheus`。由于源在国外，RHEL 系同样更推荐二进制方式。

#### 2.1.3 方法二：二进制安装（生产推荐）

**第 1 步：下载二进制包**

操作目录：`/usr/local`；用户：root。

```bash
cd /usr/local
wget https://github.com/prometheus/prometheus/releases/download/v3.15.0/prometheus-3.15.0.linux-amd64.tar.gz
```

参数解释：安装包来自官方 GitHub Releases，文件名中 `3.15.0` 是版本、`linux-amd64` 表示 Linux 64 位系统。

**国内下载加速（GitHub 慢时用）**：在原链接前加 GitHub 代理前缀，例如：

```text
https://ghproxy.net/https://github.com/prometheus/prometheus/releases/download/v3.15.0/prometheus-3.15.0.linux-amd64.tar.gz
```

代理地址可能变动，一个不能用就换另一个（如 `https://gh-proxy.com/`、`https://ghfast.top/`）；也可以在能访问的机器下载后用 scp 拷到服务器。

**第 2 步：解压并建立软链接**

```bash
tar xf prometheus-3.15.0.linux-amd64.tar.gz
ln -s prometheus-3.15.0.linux-amd64 prometheus
cd prometheus
ls -l
```

参数解释：`tar xf 包名` 中 `x` 是解开（extract）、`f` 指定文件；`ln -s 真实目录 软链接名` 建立软链接——以后升级只换软链接指向，路径永远是 `/usr/local/prometheus`。

预期输出：

```text
drwxr-xr-x 2 1001 127 4096 Sep 24 00:00 console_libraries
drwxr-xr-x 2 1001 127 4096 Sep 24 00:00 consoles
-rw-r--r-- 1 1001 127 11357 Sep 24 00:00 LICENSE
-rw-r--r-- 1 1001 127  3773 Sep 24 00:00 NOTICE
-rwxr-xr-x 1 1001 127  ... prometheus
-rw-r--r-- 1 1001 127   934 Sep 24 00:00 prometheus.yml
-rwxr-xr-x 1 1001 127  ... promtool
```

两个可执行文件：`prometheus` 是服务主程序；`promtool` 是配置检查、调试工具。它们是 Go 编译的**静态链接**程序（`ldd prometheus` 会显示"不是动态可执行文件"），不依赖系统库，拷到哪都能跑。

**第 3 步：规范目录结构**

```bash
mkdir -p bin conf data
mv prometheus promtool bin/
mv prometheus.yml conf/
```

目录规划：`bin/` 放程序，`conf/` 放配置，`data/` 放时序数据。

**第 4 步：创建专用运行用户**

```bash
useradd -r -s /usr/sbin/nologin prometheus
chown -R prometheus:prometheus /usr/local/prometheus/
```

参数解释：`useradd -r` 创建系统用户（UID 较小、不可登录）；`-s /usr/sbin/nologin` 禁止该用户登录 Shell——服务程序用独立用户跑，即使被攻破也拿不到 Shell，是安全规范。`chown -R 用户:组 路径` 递归修改属主，让服务用户能读写自己的目录。

**第 5 步：配置 PATH 环境变量（可选，方便敲命令）**

```bash
cat > /etc/profile.d/prometheus.sh <<'EOF'
export PROMETHEUS_HOME=/usr/local/prometheus
export PATH=${PROMETHEUS_HOME}/bin:$PATH
EOF
source /etc/profile.d/prometheus.sh
promtool --version
```

预期输出（类似）：

```text
promtool, version 3.15.0 (branch: HEAD, revision: ...)
  build user:       ...
  build date:       ...
```

**第 6 步：检查自带配置文件**

```bash
grep -Ev '^ *#|^$' /usr/local/prometheus/conf/prometheus.yml
```

`grep -Ev '^ *#|^$'` 表示过滤掉注释行和空行，只看有效配置。预期输出：

```text
global:
  scrape_interval: 15s
  evaluation_interval: 15s
alerting:
  alertmanagers:
    - static_configs:
        - targets:
rule_files:
scrape_configs:
  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]
```

用 promtool 检查语法：

```bash
promtool check config /usr/local/prometheus/conf/prometheus.yml
```

预期输出：

```text
Checking /usr/local/prometheus/conf/prometheus.yml
  SUCCESS: 0 rule files found
```

**第 7 步：创建 systemd 服务文件**

用编辑器创建 `/etc/systemd/system/prometheus.service`（推荐用 vim；不会用 vim 也可以直接用下面的整块写入方式）：

```bash
cat > /etc/systemd/system/prometheus.service <<'EOF'
[Unit]
Description=Prometheus Server
Documentation=https://prometheus.io/docs/introduction/overview/
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=prometheus
Group=prometheus
WorkingDirectory=/usr/local/prometheus/
ExecStart=/usr/local/prometheus/bin/prometheus \
  --config.file=/usr/local/prometheus/conf/prometheus.yml \
  --storage.tsdb.path=/usr/local/prometheus/data \
  --storage.tsdb.retention.time=15d \
  --web.listen-address=0.0.0.0:9090 \
  --web.enable-lifecycle
ExecReload=/bin/kill -HUP $MAINPID
Restart=on-failure
RestartSec=5
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF
```

关键参数逐个解释：

| 参数 | 作用 |
| --- | --- |
| `After=network-online.target` | 等网络就绪后再启动 |
| `User/Group` | 用 prometheus 身份运行 |
| `--config.file` | 指定主配置文件路径 |
| `--storage.tsdb.path` | 时序数据存放目录 |
| `--storage.tsdb.retention.time=15d` | 数据保留 15 天，过期自动删；企业常用 15～30 天 |
| `--web.listen-address=0.0.0.0:9090` | 监听所有网卡的 9090（只写 127.0.0.1 外部访问不到） |
| `--web.enable-lifecycle` | 允许通过 HTTP 接口热加载/关闭，**有被远程关闭的安全风险**；不需要可删掉，改用 `systemctl reload` |
| `ExecReload` | 执行 reload 时给主进程发 HUP 信号 |
| `Restart=on-failure` | 进程异常退出自动拉起 |
| `LimitNOFILE=65535` | 提高文件描述符上限，目标多了必须调 |

::: warning
生产环境两条红线：① 数据目录建议挂独立磁盘/分区，防止监控数据把系统根分区写满；② 安全要求高时不要开 `--web.enable-lifecycle`，热加载改用 `systemctl reload prometheus`。
:::

**第 8 步：启动并设置开机自启**

```bash
systemctl daemon-reload
systemctl enable --now prometheus
ss -lntp | grep 9090
```

`systemctl daemon-reload` 让 systemd 重新读取服务文件；`enable --now` 表示同时设开机自启并立即启动。预期输出：

```text
LISTEN 0 4096 0.0.0.0:9090 0.0.0.0:* users:(("prometheus",pid=1234,fd=10))
```

**第 9 步：验证**

```bash
curl http://localhost:9090/-/healthy
curl http://localhost:9090/-/ready
```

预期输出：

```text
Prometheus Server is Healthy.
Prometheus Server is Ready.
```

浏览器访问（把 IP 换成你的监控服务器地址）：

```text
http://【监控服务器IP】:9090
```

能看到 Prometheus 自带界面即成功。

#### 2.1.4 认识 Prometheus 自带界面

顶部四个一级菜单：

| 菜单 | 功能 |
| --- | --- |
| **Alerts** | 查看告警规则与当前告警状态（阶段五用） |
| **Graph** | 默认首页：写 PromQL 表达式、出表格和简单图表 |
| **Status** | 系统状态（见下表） |
| **Help** | 官方帮助链接 |

Status 下拉子菜单：

| 子菜单 | 能看到什么 |
| --- | --- |
| Runtime & Build Information | 版本、Go 版本、主机资源等运行信息 |
| Command-Line Flags | 启动时实际生效的命令行参数 |
| Configuration | 当前加载的完整配置文件内容 |
| Rules | 已加载的记录规则、告警规则 |
| **Targets** | 所有监控目标及其 UP/DOWN 状态（最常用） |
| Service Discovery | 服务发现的过程与结果（阶段六用） |

Graph 页面用法：在输入框选/填一个指标名（如 `scrape_duration_seconds`）→ 点 **Execute** → 下方 Table 标签看数值、Graph 标签看曲线。注意：自带界面的图表刷新后表达式就没了、也不能保存大屏，所以才需要 Grafana。

#### 2.1.5 管理 API（自动化常用）

| 接口 | 方法 | 作用 | 是否需要 lifecycle |
| --- | --- | --- | --- |
| `/-/healthy` | GET | 健康检查，始终返回 200 | 否 |
| `/-/ready` | GET | 是否准备好响应查询 | 否 |
| `/-/reload` | POST/PUT | 热加载配置文件 | **是** |
| `/-/quit` | POST/PUT | 关闭服务 | **是** |

热加载配置（开了 lifecycle）：

```bash
curl -X POST http://localhost:9090/-/reload
```

没开 lifecycle 也能用 systemd 热加载（效果相同，更安全）：

```bash
systemctl reload prometheus
```

如果没开 lifecycle 却调用接口，会返回：

```text
Lifecycle API is not enabled.
```

远程关闭（演示，生产勿用）：

```bash
curl -X POST http://localhost:9090/-/quit
```

预期输出：`Requesting termination... Goodbye!`

#### 2.1.6 方法三：Docker 方式安装

**第 1 步：安装 Docker（用国内源）**

```bash
apt -y install ca-certificates curl gnupg
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://mirrors.aliyun.com/docker-ce/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.gpg] https://mirrors.aliyun.com/docker-ce/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" > /etc/apt/sources.list.d/docker.list
apt update
apt -y install docker-ce docker-ce-cli containerd.io
systemctl enable --now docker
docker --version
```

参数解释：官方 Docker 源是 `download.docker.com`，换成 `mirrors.aliyun.com/docker-ce` 即可；`$(... VERSION_CODENAME)` 会自动取系统代号（jammy/noble）。

RHEL 系：把 repo 地址换成 `https://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo`，下载后放到 `/etc/yum.repos.d/`，再 `yum -y install docker-ce`。

**第 2 步：配置容器镜像加速**

Docker Hub 在国内拉取常超时，配置加速器：

```bash
mkdir -p /etc/docker
cat > /etc/docker/daemon.json <<'EOF'
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://docker.1panel.live",
    "https://hub.rat.dev"
  ],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "3"
  }
}
EOF
systemctl daemon-reload
systemctl restart docker
docker info | grep -A5 'Registry Mirrors'
```

参数解释：`registry-mirrors` 是 Docker Hub 的镜像加速地址，配多个会依次尝试；`log-opts` 限制容器日志单个 100MB、最多 3 个，防止日志撑爆磁盘（阶段常见坑）。

::: warning
公共加速器地址变动频繁，若某个失效，删掉即可，保留能用的；也可在 DaoCloud、1Panel 等官网查最新地址。拉取私有/国外镜像失败时，优先怀疑加速器问题。
:::

**第 3 步：启动 Prometheus 容器**

最简启动（只用默认配置，适合验证镜像）：

```bash
docker run -d --name prometheus -p 9090:9090 prom/prometheus:v3.15.0
```

参数解释：`-d` 后台运行；`--name` 容器名；`-p 宿主机端口:容器端口` 做端口映射；镜像 tag **必须写明确版本 v3.15.0，不要用 latest**。

生产推荐写法（挂载配置文件 + 数据持久化）。先在宿主机准备目录和配置：

```bash
mkdir -p /data/prometheus /etc/prometheus
docker cp prometheus:/etc/prometheus/prometheus.yml /etc/prometheus/prometheus.yml
docker rm -f prometheus
docker run -d \
  --name prometheus \
  --restart=always \
  -p 9090:9090 \
  -v /etc/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml \
  -v prometheus_data:/prometheus \
  prom/prometheus:v3.15.0 \
  --config.file=/etc/prometheus/prometheus.yml \
  --storage.tsdb.path=/prometheus \
  --storage.tsdb.retention.time=15d
```

参数解释：`--restart=always` 容器退出/开机都自动重启（生产必设）；`-v 文件:文件` 是绑定挂载，把宿主机配置挂进容器；`-v prometheus_data:/prometheus` 是命名卷，数据由 Docker 管理、持久保存；镜像名后面的内容会覆盖默认启动参数。

验证：

```bash
docker ps
curl http://localhost:9090/-/healthy
```

预期输出：容器列表里 prometheus 为 `Up`，健康检查返回 `Prometheus Server is Healthy.`。

#### 2.1.7 方法四：Docker Compose 编排

**第 1 步：安装 compose 插件**

```bash
apt -y install docker-compose-plugin
docker compose version
```

预期输出：`Docker Compose version v2.xx.x`。

**第 2 步：编写只含 Prometheus 的编排文件**

创建项目目录：

```bash
mkdir -p /opt/monitoring/prometheus
cd /opt/monitoring
```

把配置文件放好：

```bash
cp /etc/prometheus/prometheus.yml /opt/monitoring/prometheus/prometheus.yml
```

创建 `/opt/monitoring/docker-compose.yml`：

```yaml
services:
  prometheus:
    image: prom/prometheus:v3.15.0
    container_name: prometheus
    restart: always
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=15d'
      - '--web.enable-lifecycle'

volumes:
  prometheus_data:
```

**第 3 步：启动**

```bash
docker compose up -d
docker compose ps
```

参数解释：`up -d` 按编排文件后台创建并启动所有服务；`ps` 查看编排内服务状态。预期输出：prometheus 行 `running`，端口 `0.0.0.0:9090->9090/tcp`。

后续本阶段每加一个组件（Node Exporter、Grafana、Pushgateway），都会往这个 compose 文件里追加，最后形成一套完整编排。

#### 2.1.8 方法五：Ansible 批量部署（了解）

机器数量多时，用官方 Ansible 角色批量安装，角色仓库：

```text
https://github.com/prometheus-community/ansible
```

Prometheus 角色说明页：

```text
https://prometheus-community.github.io/ansible/branch/main/prometheus_role.html
```

用法概要：安装 ansible（`apt -y install ansible`）→ 在 playbook 中引用 `prometheus.prometheus.prometheus` 角色并设置 `prometheus_version: "3.15.0"` 等变量 → 对主机清单执行 `ansible-playbook`。初学者先掌握二进制和 Compose，工作中真有批量需求再学 Ansible。

---

### 2.2 主配置文件详解

#### 2.2.1 四大核心配置段

文件路径：二进制安装为 `/usr/local/prometheus/conf/prometheus.yml`；容器为挂载的 `/etc/prometheus/prometheus.yml`。

| 配置段 | 作用 |
| --- | --- |
| `global` | 全局默认值：采集间隔、规则评估间隔、外部标签等 |
| `alerting` | Alertmanager 的地址与连接方式 |
| `rule_files` | 规则文件列表（记录规则、告警规则，阶段五用） |
| `scrape_configs` | **最核心**：定义一个个 job 以及如何抓取 |

`global` 段两个关键值：

```yaml
global:
  scrape_interval: 15s       # 全局抓取间隔，默认 1 分钟
  evaluation_interval: 15s   # 规则评估间隔，默认 1 分钟
  # scrape_timeout 默认 10s，且不能超过 scrape_interval
```

#### 2.2.2 其他可选配置（眼熟即可，用到再查）

- 通用扩展：`tls_config`、`static_config`、`relabel_configs`、`metric_relabel_configs`、`alert_relabel_configs`、`alertmanager_config`、`remote_write`、`remote_read`；
- 服务发现集成：`file_sd_configs`、`dns_sd_configs`、`consul_sd_configs`、`kubernetes_sd_configs`、`ec2_sd_configs`、`openstack_sd_configs`、`azure_sd_configs`、`gce_sd_configs` 等。

#### 2.2.3 scrape_configs 写法

一个 job 的标准写法：

```yaml
scrape_configs:
  - job_name: '示例任务'
    metrics_path: /metrics      # 抓取路径，默认就是 /metrics，可省略
    scheme: http                # 协议 http/https，默认 http，可省略
    static_configs:
      - targets: ['10.0.0.11:9100', '10.0.0.12:9100']
        labels:
          env: 'prod'
          idc: 'chengdu'
```

参数解释：

| 参数 | 作用 |
| --- | --- |
| `job_name` | 任务名，会成为每条序列的 `job` 标签 |
| `metrics_path` | 抓取的网页路径 |
| `scheme` | 用 http 还是 https |
| `static_configs.targets` | 静态目标列表，每个 `IP:端口` 是一个 instance |
| `static_configs.labels` | 给该组所有目标额外附加的自定义标签 |

改完任何配置，固定两步：

```bash
promtool check config /usr/local/prometheus/conf/prometheus.yml
systemctl reload prometheus
```

::: warning
YAML 格式两条铁律：① **缩进只能用空格、不能用 Tab**，同级对齐（一般缩进 2 个空格）；② 冒号后面要有空格。缩进错了会报 `yaml: line X: did not find expected key`。改完一定先 promtool 检查再 reload。
:::

---
