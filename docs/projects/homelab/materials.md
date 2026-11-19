# 资料清单

> 这套项目要下载什么、用什么版本、仓库里的文件从哪拿。**密码不进入站点**，统一写 `【实验密码】`，实际值放本地密码库。

## 一、要下载的件

| 用途 | 资料 | 版本 | 地址 |
|---|---|---|---|
| PVE 安装 | Proxmox VE ISO | 9.2-1 | <https://www.proxmox.com/en/downloads> |
| 写 U 盘 | Rufus / balenaEtcher | 任意 | <https://rufus.ie> |
| 内存测试 | memtest86+（可选） | 任意 | <https://www.memtest.org> |
| 堡垒机 | JumpServer 安装脚本 | v3.10.0 | <https://resource.fit2cloud.com/jumpserver/jumpserver/release/v3.10.0/quick_start.sh> |
| 对象存储 | MinIO server | latest | <https://dl.min.io/server/minio/release/linux-amd64/minio> |
| 对象存储 | mc 客户端 | latest | <https://dl.min.io/client/mc/release/linux-amd64/mc> |
| 搜索 / 日志 | Elasticsearch | 7.17.x | <https://artifacts.elastic.co/packages/7.x/apt> |
| 搜索 / 日志 | Kibana | 7.17.x | <https://artifacts.elastic.co/packages/7.x/apt> |
| 中间件 | nacos-server 镜像 | v2.3.2 | `docker pull nacos/nacos-server:v2.3.2` |
| 日志 | Logstash / Filebeat | 7.17.x | <https://artifacts.elastic.co/packages/7.x/apt> |
| 业务 | RuoYi-Cloud 源码 | v3.6.5 | <https://gitee.com/y_project/RuoYi-Cloud> |
| 运行时 | Temurin JDK 8 | 8u4xx | <https://mirrors.tuna.tsinghua.edu.cn/Adoptium/8/jdk/x64/linux/> |
| 运行时 | Node.js | 16.x | <https://deb.nodesource.com/setup_16.x> |
| 驱动 | mysql-connector-j | 8.0.33 | `https://maven.aliyun.com/repository/public/com/mysql/mysql-connector-j/8.0.33/mysql-connector-j-8.0.33.jar` |
| K8s | kubeadm / kubelet / kubectl | v1.30 | <https://pkgs.k8s.io/core:/stable:/v1.30/deb/> |
| K8s | flannel 清单 | latest | <https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml> |
| 业务 | mall-swarm 源码 | master | <https://gitee.com/macrozheng/mall-swarm> |

> 国内加速：apt 用 USTC / 清华镜像；npm 用 `registry.npmmirror.com`；pip 用清华 PyPI；Maven 用阿里云；Docker 镜像加速按所在网络配置。

## 二、仓库文件

这些文件随项目放在 `/ops-project/files/` 下，可以直接下载：

| 文件 | 用途 |
|---|---|
| <a href="/ops-project/files/02-PVE准备/make-ubuntu2404-template.sh" download><code>make-ubuntu2404-template.sh</code></a> | 生成 Ubuntu 24.04 模板 9000 |
| <a href="/ops-project/files/02-PVE准备/ubuntu-2404-vendor.yaml" download><code>ubuntu-2404-vendor.yaml</code></a> | 模板 cloud-init 配置 |
| <a href="/ops-project/files/02-PVE准备/create-lab-vm.sh" download><code>create-lab-vm.sh</code></a> | 按 VMID 批量建机 |
| <a href="/ops-project/files/02-PVE准备/eip-apply.sh" download><code>eip-apply.sh</code></a> | EIP 1:1 NAT 应用 |
| <a href="/ops-project/files/02-PVE准备/eip.service" download><code>eip.service</code></a> | 开机自动应用 EIP |
| <a href="/ops-project/files/02-PVE准备/thin-alert.sh" download><code>thin-alert.sh</code></a> | thin 池 80% / 90% 告警 |
| <a href="/ops-project/files/02-PVE准备/thin-alert.service" download><code>thin-alert.service</code></a> | 告警 oneshot 单元 |
| <a href="/ops-project/files/02-PVE准备/thin-alert.timer" download><code>thin-alert.timer</code></a> | 每 5 分钟触发 |
| <a href="/ops-project/files/03-集群部署/p0-node-init.sh" download><code>p0-node-init.sh</code></a> | P0 节点初始化 |
| <a href="/ops-project/files/03-集群部署/keepalived-lvs.conf" download><code>keepalived-lvs.conf</code></a> | LVS-DR + keepalived 模板 |
| <a href="/ops-project/files/03-集群部署/demo-app.py" download><code>demo-app.py</code></a> | 最小链路占位应用 |
| <a href="/ops-project/files/04-工具与自检/ansible/inventory.ini" download><code>ansible/inventory.ini</code></a> | Ansible inventory、cfg、group_vars |

## 三、账号与密码

- 账号统一用 `ubuntu`、`admin`、`ry`、`nacos`、`repl`、`mall` 这类实验账号。
- 所有密码在站点里都显示为 `【实验密码】`；按各篇实操在实验环境里自行设置，存到本地密码库。
- 不要把实验密码提交到公开仓库，也不要用生产密码做实验。

## 四、离线包建议

现场网络不稳时，先在 Windows 下好，再 scp 进 PVE：

```powershell
# 在 Windows PowerShell 里执行
scp ".\ops-project-files\proxmox-ve_9.2-1.iso" root@192.168.10.30:/var/lib/vz/template/iso/
```

优先级：PVE ISO → RuoYi 源码 + JDK8 + Node16 → ES / Kibana / Logstash（06、08）→ Nacos / MinIO / RabbitMQ 镜像。
