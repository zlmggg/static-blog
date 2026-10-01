---
category: 容器
difficulty: 初级
---

# Docker 容器化应用快速入门

::: tip 本篇定位：掌握容器原理、镜像构建、存储网络、Compose 多服务编排、仓库管理、资源限制、运维。
:::

## Docker 概述

`Docker` 是**容器化平台**，基于 Linux 内核的 `Namespace（隔离）`、`Cgroups（资源限制）`、`UnionFS（联合文件系统）`实现。<br>
简单一句话：**把应用 + 依赖 + 配置打包成一个轻量、可移植的容器，一处打包，到处运行。**

><small>区分与虚拟机的区别：</small>
>- <small>**虚拟机**：完整操作系统内核，体积大，启动分钟级。</small>
>- <small>**Docker 容器**：共享宿主机内核，只打包应用和库，MB 级别，秒级启动。</small>

### 核心概念

- 镜像（Image）：只读模板，是创建容器的模板。比如 `nginx:alpine`，包含 nginx 程序、依赖。镜像不能运行。<br>
- 容器（Container）：运行中的镜像实例。比如 `nginx:alpine` 运行的容器。<br>
- 仓库（Registry）：存储镜像的中心仓库。比如 Docker Hub、Harbor。<br>
- 网络（Network）：容器之间的通信。比如 bridge、host、none、container。<br>
- 端口映射（Port Mapping）：将容器端口映射到宿主机端口。比如 `80:80`，将容器端口 80 映射到宿主机端口 80。<br>
- 卷（Volume）：持久化存储容器数据的目录。比如 `/app`。<br>
- 绑定挂载（Bind Mount）：将宿主机目录挂载到容器目录。比如 `/app:/app`。<br>
- 环境变量：在容器运行时设置的环境变量。比如 `PORT=80`。<br>    

### 核心优势

- ✅ **环境一致**：开发、测试、生产环境完全相同，解决 “在我电脑能跑，线上不行”
- ✅ **轻量高效**：共享宿主机内核，占用资源远低于虚拟机，秒启动
- ✅ **快速部署**：镜像分发，一键拉起服务
- ✅ **隔离性**：容器之间进程、网络、文件系统互相隔离
- ✅ **版本管理**：镜像支持版本标签，方便回滚

### 使用场景

1. 开发环境标准化（团队统一环境）
2. 微服务打包部署（K8s 底层就是容器）
3. 持续集成 / CI/CD（Jenkins + Docker）
4. 测试环境快速创建销毁
5. 单机多应用隔离（数据库、中间件、网站分开容器）

### 简单工作流

1. 编写 Dockerfile → `docker build` 构建镜像
2. 本地保存镜像，或 push 到镜像仓库
3. 在目标机器拉取镜像 `docker pull`
4. `docker run` 创建并启动容器，对外提供服务

### 命令速记

```bash
# 拉取镜像
docker pull nginx:1.25-alpine
# 查看本地镜像
docker images
# 查看镜像历史
docker history nginx:1.25-alpine
# 后台运行容器，端口映射 80:80 -d 后台运行
# --name 容器名称
# -p 宫主机端口:容器端口
# -v 宫主机目录:容器目录
docker run -d --name mynginx -p 80:80 -v /app:/app nginx:1.25-alpine
# 进入容器
docker exec -it mynginx /bin/bash
# 查看容器状态
docker inspect mynginx
# 查看容器环境变量
docker inspect -f '{{.Config.Env}}' mynginx
# 查看容器挂载的卷
docker inspect -f '{{.Mounts}}' mynginx
# 查看容器网络
docker inspect -f '{{.NetworkSettings}}' mynginx
# 查看容器端口映射
docker inspect -f '{{.NetworkSettings.Ports}}' mynginx
# 查看容器命令
docker inspect -f '{{.Config.Cmd}}' mynginx
# 查看运行容器
docker ps -a
# 查看容器日志
docker logs mynginx
# 启动容器
docker start mynginx
# 停止容器
docker stop mynginx
# 重启容器
docker restart mynginx
# 删除容器
docker rm mynginx
# 删除镜像
docker rmi nginx:alpine:1.25
```

## 安装

### Docker 版本管理

核心区分：**Docker Engine（容器引擎，Linux 生产环境用）** vs **Docker Desktop（Windows/mac 开发桌面工具，内置 Engine+GUI+K8s）**
底层开源项目叫 **Moby**，Docker Engine 基于 Moby 编译打包。

#### 版本号命名历史变迁

1. **早期版本（2017-03 之前）：1.x 序列**
`0.x ~ 1.13.1`，语义化版本，如 `1.12.6`、`1.13.1`。

> 
> 1.13.1 是最后一个 1.x 版本。

2. **2017.03 ~ 2020：YY.MM 时间化版本（CE/EE 时代）**
从 `17.03` 开始，格式：**年。月**，后缀是补丁号，例 `19.03.15`（2019 年 3 月发布，第 15 次补丁）

- CE：Community Edition 社区免费版
  - Stable：季度稳定版，维护周期 4 个月
  - Edge：月度尝鲜版，维护很短，生产不推荐
- EE：Enterprise Edition 企业付费版，同版本号，维护 1 年，带官方支持、安全加固、认证镜像等

> 
> 注意：**2020 年后 EE 产品线停产，不再单独发布 EE**，现在企业付费是 Docker Desktop 订阅。

3. **2021 之后：恢复纯主版本号（20.10 → 21,22,23,24,25,26,27,28,29）**
格式：`主.次.补丁`，例如 `20.10.24`、`25.0.5`、`29.0.0`。

### Docker 安装和删除

- 官方文档 : <small>https://docs.docker.com/engine/install/<br></small>
- 阿里云文档: <small>https://developer.aliyun.com/mirror/docker-ce?spm=a2c6h.13651102.0.0.29a91b11NTKyP9</small>    

#### Debian/Ubuntu RHEL 系包安装
::: code-group

```bash [Debian/Ubuntu]
sudo apt-get update
sudo apt-get -y install apt-transport-https ca-certificates curl software-properties-common
# step 2: 安装GPG证书
curl -fsSL https://mirrors.aliyun.com/docker-ce/linux/ubuntu/gpg | sudo apt-key 
add -
# Step 3: 写入软件源信息
sudo add-apt-repository "deb [arch=amd64] https://mirrors.aliyun.com/docker-ce/linux/ubuntu $(lsb_release -cs) stable"
# Step 4: 更新并安装Docker-CE
sudo apt-get -y update
sudo apt-get -y install docker-ce

# Step 5: 删除 Docker
apt purge docker-ce docker-ce-cli containerd.io runc
rm -rf /var/lib/docker

```

```bash [RHEL 系]
# step 1: 安装必要的一些系统工具
sudo yum install -y yum-utils
# Step 2: 添加软件源信息
yum-config-manager --add-repo https://mirrors.aliyun.com/dockerce/linux/centos/docker-ce.repo
# Step 3: 安装Docker
sudo yum install docker-ce docker-ce-cli containerd.io docker-buildx-plugin 
docker-compose-plugin
# Step 4: 开启Docker服务
sudo service docker start

# 注意：
# 官方软件源默认启用了最新的软件，您可以通过编辑软件源的方式获取各个版本的软件包。例如官方并没有
# 将测试版本的软件源置为可用，您可以通过以下方式开启。同理可以开启各种测试版本等。
# vim /etc/yum.repos.d/docker-ce.repo
#   将[docker-ce-test]下方的enabled=0修改为enabled=1
#
# 安装指定版本的Docker-CE:
# Step 1: 查找Docker-CE的版本:
# yum list docker-ce.x86_64 --showduplicates | sort -r
#   Loading mirror speeds from cached hostfile
#   Loaded plugins: branch, fastestmirror, langpacks
#   docker-ce.x86_64           17.03.1.ce-1.el7.centos           docker-ce-stable
#   docker-ce.x86_64           17.03.1.ce-1.el7.centos           @docker-ce-stable
#   docker-ce.x86_64           17.03.0.ce-1.el7.centos           docker-ce-stable
#   Available Packages
# Step2: 安装指定版本的Docker-CE: (VERSION例如上面的17.03.0.ce.1-1.el7.centos)
# sudo yum -y install docker-ce-[VERSION]
```

:::

#### Linux 二进制离线安装

本方法适用于无法上网或无法通过包安装方式安装的主机上安装docker

**安装文档：**

- <small>https://docs.docker.com/engine/install/binaries/<br></small>
- <small>https://docs.docker.com/install/linux/docker-ce/binaries/<br></small>

**二进制安装下载路径：**

- <small>https://download.docker.com/linux/<br></small>
- <small>https://download.docker.com/linux/static/stable/<br></small>
- <small>https://mirrors.aliyun.com/docker-ce/linux/static/stable/x86_64/<br></small>



::: code-group

```bash [Debian/Ubuntu]
# step 1: 下载二进制包  注意：版本请自行确定
wget https://download.docker.com/linux/static/stable/amd64/docker-ce-20.10.24-0~ubuntu-20.04.1.tar.gz
# step 2: 解压二进制包
tar -zxvf docker-ce-20.10.24-0~ubuntu-20.04.1.tar.gz
# step 3: 安装二进制包
cp docker/* /usr/local/bin/
# step 4: 启动 Docker 服务
dockerd &>/dev/null
# step 5: 验证安装
docker version
# step 6: 运行测试容器
docker run hello-world
# step 7: 查看进程树
pstree -p
```

:::

**创建 Docker service 文件**

```bash
cat > /lib/systemd/system/docker.service <<-EOF
[Unit]
Description=Docker Application Container Engine
Documentation=https://docs.docker.com
After=network-online.target firewalld.service
Wants=network-online.target
[Service]
Type=notify
# the default is not to use systemd for cgroups because the delegate issues still
ExecStart=/usr/local/bin/dockerd -H unix://var/run/docker.sock
ExecReload=/bin/kill -s HUP \$MAINPID
LimitNOFILE=infinity
LimitNPROC=infinity
LimitCORE=infinity
TimeoutStartSec=0
Delegate=yes
KillMode=process
Restart=on-failure
StartLimitBurst=3
StartLimitInterval=60s
[Install]
WantedBy=multi-user.target
EOF
# 重新加载 systemd 配置
systemctl daemon-reload
# 启用 Docker 服务
systemctl enable --now docker

```

**自动补全[可选]**
::: code-group

```bash [Debian/Ubuntu]
# For Bash Completion
curl -L https://raw.githubusercontent.com/docker/cli/master/contrib/completion/bash/docker -o /etc/bash_completion.d/docker.sh
# 检查是否成功
wc -l /etc/bash_completion.d/docker.sh
# For Zsh users
curl -L https://raw.githubusercontent.com/docker/cli/master/contrib/completion/zsh/_docker -o /usr/local/share/zsh/site-functions/_docker 
# 安装 bash-completion 包
apt install -y bash-completion
```

:::

### 官方通用安装Docker脚本

从Docker官方下载通用安装脚本
<front color=red> 注意： 此脚本当前不支持 Rocky Linux</front>

```bash
# 如果是 Rocky Linux，修改os-release文件如下，即可支持安装Docker
sudo vim /etc/os-release    
# 将ID=rocky 修改为 ID=centos
# step 1: 下载脚本
curl -fsSL https://get.docker.com -o get-docker.sh
# step 2: 执行脚本
sudo sh get-docker.sh
```

### Docker 组成和配置

```mermaid
flowchart LR
    A[Docker client] --> B[Docker Engine<br/>dockerd]
    B --> C[Containerd]
    C --> D[containerd-shim]
    D --> E[runc]
    E --> F[container]
```

环境配置文件：

- `/etc/sysconfig/docker-network`
- `/etc/sysconfig/docker-storage`
- `/etc/sysconfig/docker`

Unit File: `/lib/systemd/system/docker.service`

docker-ce 配置文件: `/etc/docker/daemon.json`

::: code-group

```json [国内镜像加速]
{
     "registry-mirrors": [  
        "https://docker.m.daocloud.io",
        "https://docker.1panel.live",
        "https://docker.1ms.run",
        "https://docker.xuanyuan.me"
   ]
}
```

:::

Docker Registry配置文件: `/etc/docker/registry.json`

**ubuntu 查看Docker相关文件**
::: code-group

```bash [服务端相关文件]
dpkg -L docker-ce
/.
/etc
/etc/default
/etc/default/docker
/etc/init
/etc/init/docker.conf
/etc/init.d
/etc/init.d/docker
/lib
/lib/systemd
/lib/systemd/system
/lib/systemd/system/docker.service
/lib/systemd/system/docker.socket
/usr
/usr/bin
/usr/bin/docker-init
/usr/bin/docker-proxy
/usr/bin/dockerd
/usr/share
/usr/share/doc
/usr/share/doc/docker-ce
/usr/share/doc/docker-ce/README.md
/usr/share/doc/docker-ce/changelog.Debian.gz
/var
/var/lib
/var/lib/docker-engine
/var/lib/docker-engine/distribution_based_engine.json
```
```bash [客户端相关文件]
dpkg -L docker-ce-cli
/.
/usr
/usr/bin
/usr/bin/docker
/usr/libexec
/usr/libexec/docker
/usr/libexec/docker/cli-plugins
/usr/libexec/docker/cli-plugins/docker-app
/usr/libexec/docker/cli-plugins/docker-buildx
/usr/share
/usr/share/bash-completion
/usr/share/bash-completion/completions
/usr/share/bash-completion/completions/docker
/usr/share/doc
/usr/share/doc/docker-ce-cli
/usr/share/doc/docker-ce-cli/changelog.Debian.gz
/usr/share/fish
/usr/share/fish/vendor_completions.d
/usr/share/fish/vendor_completions.d/docker.fish
/usr/share/man
/usr/share/man/man1
/usr/share/man/man1/docker-wait.1.gz
/usr/share/man/man1/docker.1.gz
/usr/share/man/man5
/usr/share/man/man5/Dockerfile.5.gz
/usr/share/man/man5/docker-config-json.5.gz
/usr/share/man/man8
/usr/share/man/man8/dockerd.8.gz
/usr/share/zsh
/usr/share/zsh/vendor-completions
/usr/share/zsh/vendor-completions/_docker
```

:::

### Docker 命令帮助 [🐳](/reference/docker-commands)

**docker 命令格式**

```bash
docker [OPTIONS] COMMAND
# COMMAND 分为
Management Commands  # 指定管理的资源对象类型,较新的命令用法,将命令按资源类型进行分类,方便使用
Commands             # 对不同资源操作的命令不分类,使用容易产生混乱
```
docker 命令有很多子命令，可以用下面方法查看帮助

```bash
#docker 命令帮助
man docker 
docker
docker  --help
#docker 子命令帮助
man docker-COMMAND
docker COMMAND --help```
```

官方文档:

- <small>https://docs.docker.com/reference/</small>
- <small>https://docs.docker.com/engine/reference/commandline/cli/</small>

### Docker 相关信息和优化配置

**查看Docker版本信息**

```bash
docker version      # 显示Docker Client 版本信息与 Docker Engine 版本信息
docker -version     # 显示Docker Client 版本信息
```

**查看 docker 详解信息**

```bash
docker info      # 显示Docker Engine 信息,包括版本、系统信息、容器数量、镜像数量、存储驱动、网络驱动、日志驱动等

Client:
 Debug Mode: false                  #client 端是否开启 debug
Server:
 Containers: 2                      #当前主机运行的容器总数
 Running: 0                         #有几个容器是正在运行的
 Paused: 0                          #有几个容器是暂停的
 Stopped: 2                         #有几个容器是停止的
 Images: 4                          #当前服务器的镜像数
 Server Version: 19.03.5            #服务端版本
 Storage Driver: overlay2           #正在使用的存储引擎
 Backing Filesystem: extfs          #后端文件系统，即服务器的磁盘文件系统
 Supports d_type: true              #是否支持 d_type
 Native Overlay Diff: true          #是否支持差异数据存储
 Logging Driver: json-file          #日志类型,每个容器的标准输出以日志存放在
                                    #/var/lib/docker/containers/<CONTAINER ID>/<CONTAINER ID>-json.log 
 Cgroup Driver: cgroupfs            #Cgroups 类型    
 Plugins:                           #插件
 Volume: local                      #卷
 Network: bridge host ipvlan macvlan null overlay       # overlay 跨主机通信
 Log: awslogs fluentd gcplogs gelf journald json-file local logentries splunk 
syslog                              #日志类型
 Swarm: inactive                    #是否支持 swarm
 Runtimes: runc                     #已安装的容器运行时
 Default Runtime: runc              #默认使用的容器运行时
 Init Binary: docker-init           #初始化容器的守护进程，即 pid 为 1 的进程
 containerd version: b34a5c8af56e510852c35414db4c1f4fa6172339     #版本
 runc version: 3e425f80a8c931f88e6d94a8c831b9d5aa481657           #runc版本
 init version: fec3683                                            #init 版本
 Security Options:                                                #安全选项
 apparmor                           #安全模块，https://docs.docker.com/engine/security/apparmor/
 seccomp                            #安全计算模块，即制容器操作，https://docs.docker.com/engine/security/seccomp/
   Profile: default                     #默认的配置文件
 Kernel Version: 4.15.0-29-generic      #宿主机内核版本
 Operating System: Ubuntu 18.04.1 LTS   #宿主机操作系统
 OSType: linux                          #宿主机操作系统类型
 Architecture: x86_64                   #宿主机架构
 CPUs: 1                                #宿主机 CPU 数量
 Total Memory: 962MiB                   #宿主机总内存
 Name: ubuntu1804.magedu.com            #宿主机 hostname
 ID: IZHJ:WPIN:BRMC:XQUI:VVVR:UVGK:NZBM:YQXT:JDWB:33RS:45V7:SQWJ    #宿主机 ID
 Docker Root Dir: /var/lib/docker           #宿主机关于docker数据的保存目录,建议使用独立SSD的磁盘,保证性能和空间
 Debug Mode: false                          #server 端是否开启 debug
 Registry: https://index.docker.io/v1/      #仓库路径
 Labels:
 Experimental: false                        #是否测试版
 Insecure Registries:
  127.0.0.0/8 :                             #非安全的镜像仓库
 Registry Mirrors:
 https://si7y70hh.mirror.aliyuncs.com/       #镜像仓库
 Live Restore Enabled: false                 #是否开启活动重启 (重启docker-daemon 不关闭容器 )
WARNING: No swap limit support               #系统警告信息 (没有开启 swap 资源限制 )
```

解决方法请参考 ➡ [解决SWAP报警提示](/cases/t-docker-swap.md)

### 查看 docker0 网卡

在docker安装启动之后，默认会生成一个名称为docker0的网卡并且默认IP地址为172.17.0.1的网卡。

```bash
ip a | grep docker0

4: docker0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP 
group default 
   link/ether 0X:00:d3:26:ed:4e brd ff:ff:ff:ff:ff:ff
   inet 172.17.0.1/16 brd 172.17.255.255 scope global docker0
       valid_lft forever preferred_lft forever
   inet6 fe80::42:d3ff:fe26:ed4e/64 scope link 
       valid_lft forever preferred_lft forever
route -n

Kernel IP routing table

Destination     Gateway         Genmask         Flags Metric Ref   Use Iface
0.0.0.0         10.0.0.2        0.0.0.0         UG    100    0        0 eth0
10.0.0.0        0.0.0.0         255.255.255.0   U     100    0        0 eth0
172.17.0.0      0.0.0.0         255.255.0.0     U     0      0        0 docker0
```

### Docker 存储引擎

官方文档关于存储引擎的相关文档：<br>
[Docker 存储引擎](https://docs.docker.com/storage/storagedriver/) <br>
[选择存储引擎](https://docs.docker.com/engine/storage/drivers/select-storage-driver/)

修改存储引擎参考文档：<br>
[修改存储引擎](https://docs.docker.com/storage/storagedriver/overlayfs-driver/)<br>

Docker官方推荐首选存储引擎为overlay2

devicemapper存在使用空间方面存在限制，虽然可以通过配置解决，当前官方依然推荐使用overlay2

**基于Overlay文件系统实现联合文件系统挂载**

```bash
# 查看是否支持overlay2存储引擎的挂载点
# 如果支持overlay2存储引擎，会显示overlay2的挂载点
# 如果不支持overlay2存储引擎，会显示devicemapper的挂载点
grep -i overlay /boot/config-6.8.0-31-generic

CONFIG_EFI_CUSTOM_SSDT_OVERLAYS=y
CONFIG_OVERLAY_FS=m
# CONFIG_OVERLAY_FS_REDIRECT_DIR is not set
CONFIG_OVERLAY_FS_REDIRECT_ALWAYS_FOLLOW=y
# CONFIG_OVERLAY_FS_INDEX is not set
CONFIG_OVERLAY_FS_XINO_AUTO=y
# CONFIG_OVERLAY_FS_METACOPY is not set
# CONFIG_OVERLAY_FS_DEBUG is not set

# 加载overlay内核模块
modinfo -d overlay      # Overlay filesystem
modinfo -n overlay      # /lib/modules/6.8.0-31-generic/kernel/fs/overlayfs/overlay.ko.zst
lsmod | grep overlay    # overlay               212992  2

# 如果没有，可以执行下面加载模块
modprobe overlayfs
mkdir -p /data/overlay/{lower1,lower2,merged,upper,work} 
echo lower1 file f1 > /data/overlay/lower1/f1
echo lower1 file f2 > /data/overlay/lower1/f2
echo lower2 file f1 > /data/overlay/lower2/f1
echo lower2 file f3 > /data/overlay/lower2/f3
tree /data/overlay/
/data/overlay/
├── lower1
│   ├── f1
│   └── f2
├── lower2
│   ├── f1
│   └── f3
├── merged
├── upper
└── work
6 directories, 4 files
cd /data/overlay/
[root@ubuntu2404 overlay]#tree
.
├── lower1
│   ├── f1
│   └── f2
├── lower2
│   ├── f1
│   └── f3
├── merged
├── upper
└── work
6 directories, 4 files

#挂载
[root@ubuntu2404 overlay]#mount -t overlay overlay -o 
lowerdir=./lower2:./lower1,upperdir=./upper,workdir=./work ./merged
#验证
[root@ubuntu2404 overlay]#tree ./merged/
./merged/
├── f1
├── f2
└── f3
1 directory, 3 files

[root@ubuntu2404 overlay]#cat ./merged/f1 
lower2 file f1
[root@ubuntu2404 overlay]#cat ./merged/f2
lower1 file f2
[root@ubuntu2404 overlay]#cat ./merged/f3
lower2 file f3
[root@ubuntu2404 overlay]#echo merged file f4 > merged/f4
[root@ubuntu2404 overlay]#ls upper/
f4
[root@ubuntu2404 overlay]#cat upper/f4
merged file f4
[root@ubuntu2404 overlay]#cat merged/f1 
lower2 file f1
[root@ubuntu2404 overlay]#echo merged file f1 > merged/f1
[root@ubuntu2404 overlay]#ls upper/
f1 f4
[root@ubuntu2404 overlay]#cat upper/f1
merged file f1
```

### Docker 配置和优化

官方文档关于配置和优化的相关文档：<br>
[配置和优化](https://docs.docker.com/reference/cli/dockerd/#daemon-configuration-file)  

注意：这种方式只对新建的容器有效的，之前的容器不生效

**支持官方仓库和私有仓库镜像下载**

```bash
cat /etc/docker/daemon.json
{
    "registry-mirrors": [  
        "https://docker.m.daocloud.io",
        "https://docker.1panel.live",
        "https://docker.1ms.run",
        "https://docker.xuanyuan.me"
   ],
    "insecure-registries": ["example.com"]
}
#只支持docker官方镜像下载，不支持私有仓库镜像下载
```

**Docker 优化**

```bash
vim /etc/docker/daemon.json
{
"registry-mirrors": [   
    "https://registry.docker-cn.com",
    "http://hub-mirror.c.163.com",
    "https://docker.mirrors.ustc.edu.cn",
    "https://si7y70hh.mirror.aliyuncs.com/"
 ],
#开启远程:https://docs.docker.com/config/daemon/remote-access/ 
#方法1:docker.service文件中ExecStart=/usr/bin/dockerd -H tcp://0.0.0.0:2375 -H fd:// 
#方法2: 注意:需要删除/lib/systemd/system/docker.service文件中的-H fd:// 两种冲突
"hosts": ["unix:///var/run/docker.sock", "tcp://0.0.0.0:2375"],
"insecure-registries": ["harbor.magedu.com"],
"exec-opts": ["native.cgroupdriver=systemd"],
  "data-root": "/data/docker",                  #方法1:指定docker数据目录,方法2：
ExecStart=/usr/bin/dockerd --data-root=/data/docker
#"graph": "/data/docker",#旧版写法，指定docker数据目录,新版24.0.0不支持
"max-concurrent-downloads": 10, 
"max-concurrent-uploads": 5,    
"log-opts": {
   "max-size": "300m",   #指定容器日志文件的最大值
   "max-file": "2"       #指定容器日志文件的个数，循环写入日志文件，即一个日志满，会写入第二
个文件
 },
"live-restore": true,   #docker.service重启，不影响容器的运行
  "proxies": {           #代理 https://docs.docker.com/network/proxy/
   "default": {
     "httpProxy": "http://proxy.example.com:3128",
     "httpsProxy": "https://proxy.example.com:3129",
     "noProxy": "*.test.example.com,.example.org,127.0.0.0/8"
   }
   "tcp://docker-daemon1.example.com": {
     "noProxy": "*.internal.example.net"
   }
 }
}
systemctl daemon-reload && systemctl restart docker.service

```

**Docker 实现代理功能**

```bash
#无法直接下载指定镜像
docker pull registry.k8s.io/ingress-nginx/controller:v1.7.1
Error response from daemon: Head "https://us-west2-docker.pkg.dev/v2/k8s-artifacts-prod/images/ingress-nginx/controller/manifests/v1.7.1": dial tcp 142.251.170.82:443: connect: connection refused
#先安装科学上网软件，开启局域网连接略
mkdir -p /etc/systemd/system/docker.service.d
cat >> /etc/systemd/system/docker.service.d/http-proxy.conf 
<<EOF
[Service]
Environment="HTTP_PROXY=http://${PROXY_SERVER_IP}:${PROXY_PORT}/"
Environment="HTTPS_PROXY=http://${PROXY_SERVER_IP}:${PROXY_PORT}/"
Environment="NO_PROXY=127.0.0.0/8,172.17.0.0/16,10.0.0.0/24,10.244.0.0/16,192.16
8.0.0/16,magedu.com,cluster.local"
EOF
systemctl daemon-reload && systemctl restart docker.service
#重新拉取成功
docker pull registry.k8s.io/ingress-nginx/controller:v1.7.1 
```

**Containerd 实现代理功能**

```bash
mkdir -p /etc/systemd/system/containerd.service.d
cat >> /etc/systemd/system/containerd.service.d/http-proxy.conf <<EOF
[Service]
Environment="HTTP_PROXY=http://${PROXY_SERVER_IP}:${PROXY_PORT}/"
Environment="HTTPS_PROXY=http://${PROXY_SERVER_IP}:${PROXY_PORT}/"
Environment="NO_PROXY=127.0.0.0/8,172.17.0.0/16,10.0.0.0/24,10.244.0.0/16,192.16
8.0.0/16,magedu.com,cluster.local"
EOF
systemctl daemon-reload && systemctl restart 
containerd.service
```
**开启远程连接**

```bash
#在docker服务端主机开启远程网络连接功能
vim /lib/systemd/system/docker.service 
[Service]
.....
ExecStart=/usr/local/bin/dockerd -H unix://var/run/docker.sock -H 
tcp://0.0.0.0:2375
.......
systemctl daemon-reload
systemctl restart docker.service
#确认端口打开
ss -ntlp|grep dockerd
LISTEN 0      4096               *:2375           *:*   users:(("dockerd",pid=1937,fd=3))
docker info
.......
  127.0.0.0/8
 Live Restore Enabled: false
 Product License: Community Engine
#显示下面提示
WARNING: API is accessible on http://0.0.0.0:2375 without encryption.
         Access to the remote API is equivalent to root access on the host. 
Refer
         to the 'Docker daemon attack surface' section in the documentation for
         more information: https://docs.docker.com/go/attack-surface/

#在另一台docker客户端主机远程连接服务器
docker -H <docker服务器IP>:2375 version
Client: Docker Engine - Community
 Version:           24.0.6  #本机docker客户端的版本
......
Server: Docker Engine - Community
 Engine:
 Version:          24.0.7  #此处可以看到远程docker服务器的版本,和客户端版本不同
```

**通过ssh 协议远程连接**

```bash
ssh-keygen
ssh-copy-id 10.0.0.100
docker -H ssh://root@10.0.0.100 version
Client: Docker Engine - Community
 Version:           26.1.3
 API version:       1.45
 Go version:       go1.21.10
 Git commit:       b72abbb
 Built:             Thu May 16 08:33:29 2024
 OS/Arch:           linux/amd64
 Context:           default
Server: Docker Engine - Community
 Engine:
 Version:          26.1.4
 API version:      1.45 (minimum version 1.24)
 Go version:       go1.21.11
 Git commit:       de5c9cf
 Built:           Wed Jun  5 11:28:57 2024
 OS/Arch:         linux/amd64
 Experimental:     false
 containerd:
 Version:          1.6.33
 GitCommit:       d2d58213f83a351ca8f528a95fbd145f5654e957
 runc:
 Version:          1.1.12
 GitCommit:       v1.1.12-0-g51d5e94
 docker-init:
 Version:          0.19.0
 GitCommit:       de40ad0

ssh 10.0.0.100 docker images
REPOSITORY                       TAG           IMAGE ID       CREATED         
SIZE
harbor.magedu.com/library/ubuntu    22.04         67c845845b7d   5 months ago   77.9MB
172.24.0.253/library/rockylinux   8.9-minimal   f63d8d2889fd   11 months ago   93.3MB
```

## Docker 镜像（Image）管理

### Docker 镜像介绍

Docker 镜像是容器的**静态只读模板**，打包了应用程序运行所需的全部内容：业务代码、运行时环境、依赖库、配置文件、环境变量、启动命令等。镜像启动后就成为一个容器，二者的关系可以类比为「程序安装包」与「运行中的程序」。

**核心特性**

1. **只读性**：镜像本身不可修改，只能通过重新构建生成新镜像；容器运行时的所有修改都发生在顶部的可写层，不会改动镜像本身。
2. **分层存储**：基于联合文件系统（UnionFS）实现多层叠加，是镜像最核心的设计。
3. **可复用共享**：不同镜像可以共用相同的底层镜像，极大节省磁盘和传输成本。
4. **可移植性**：一次构建，可在任意安装了 Docker 的环境中运行，环境完全一致。
5. **版本化管理**：通过标签（Tag）区分不同版本 / 变体，支持版本回滚。

**核心原理：分层文件系统**

**联合文件系统（UnionFS）**

UnionFS 是一种轻量级文件系统，它可以将多个独立的目录（层）挂载到同一个目录下，对外呈现为一个完整的文件系统。

Docker 镜像就是由一层层这样的只读文件系统叠加而成：

- 最底层是基础镜像（如 `ubuntu`、`alpine`）
- 往上每一层对应一次文件系统变更（安装软件、复制文件等）
- 上层优先级高于下层，同名文件会被上层覆盖

**镜像层与容器层**

- **镜像层**：全部只读，每一层对应 Dockerfile 中一条会修改文件系统的指令（`RUN`/`COPY`/`ADD`）；`ENV`/`CMD`/`EXPOSE` 等指令仅修改元数据，不新增文件层。
- **容器层**：容器启动时，会在镜像最顶层添加**唯一一层可写层**；容器内所有文件修改、新增、删除都只作用于这一层，删除容器时可写层一并销毁，镜像本身不受影响

**分层设计的优势**

- **节省磁盘**：100 个基于 Ubuntu 的应用镜像，只需存储 1 份 Ubuntu 基础层。
- **加速构建**：未修改的层直接复用缓存，无需重复执行。
- **加速传输**：拉取 / 推送镜像时，只传输本地不存在的层。

示例：

```bash
docker pull nginx 
Using default tag: latest
latest: Pulling from library/nginx
8ec398bc0356: Pull complete 
a53c868fbde7: Pull complete 
79daf9dd140d: Pull complete
Digest: sha256:70821e443be75ea38bdf52a974fd2271babd5875b2b1964f05025981c75a6717
Status: Downloaded newer image for nginx:latest
docker.io/library/nginx:latest

#查看镜像分层历史
docker history nginx
IMAGE           CREATED        CREATED BY                                    SIZE     COMMENT
0901fa9da894    9 days ago    /bin/sh -c #(nop) CMD ["nginx" "-g" "daemon…   0B                  
<missing>       9 days ago    /bin/sh -c #(nop) STOPSIGNAL SIGTERM           0B                  
<missing>       9 days ago    /bin/sh -c #(nop) EXPOSE 80                    0B                  
<missing>       9 days ago    /bin/sh -c #(nop) ENTRYPOINT ["/docker-entr…   0B                  
<missing>       9 days ago    /bin/sh -c #(nop) COPY file:0fd5fca330dcd6a7…  1.04kB             
<missing>       9 days ago    /bin/sh -c #(nop) COPY file:1d0a4127e78a26c1…  1.96kB             
<missing>       9 days ago    /bin/sh -c #(nop) COPY file:e7e183879c35719c…  1.2kB              
<missing>       9 days ago    /bin/sh -c set -x     && addgroup --system -…  63.3MB             
......
```

**镜像的命名与标识**

```bash
[仓库地址/]仓库名[:标签]
```

- **仓库地址**：私有仓库时填写，如 `registry.example.com/`；官方 Docker Hub 可省略。
- **仓库名**：镜像的名称，官方镜像直接为名称（如 `nginx`），第三方镜像为 `用户名/仓库名`（如 `bitnami/nginx`）。
- **标签（Tag）**：版本 / 变体标识，不写默认使用 `latest`。

> ⚠️ 注意：`latest` 只是默认标签，不代表「最新稳定版」，生产环境必须指定明确版本号。

示例：

- `nginx:latest`：官方最新稳定版
- `bitnami/nginx:8.9-minimal`：第三方最新稳定版
- `harbor.magedu.com/library/ubuntu:22.04`：私有仓库 22.04 版本

**唯一标识：镜像 ID 与摘要**

- **镜像 ID**：本地生成的短哈希，仅在当前宿主机唯一，用于快速操作。
- **镜像摘要（Digest）**：基于镜像内容计算的全局唯一哈希，内容不变则摘要不变；生产环境中用于精确锁定镜像版本，避免标签被覆盖导致的不一致。

**常见镜像分类与变体**

按来源划分

- **官方镜像**：Docker 官方认证维护，安全、更新及时，如 `ubuntu`、`mysql`、`python`、`redis`。
- **第三方镜像**：社区、厂商或个人发布，如 `bitnami` 系列、`elastic/logstash`。
- **自建镜像**：企业 / 个人通过 Dockerfile 定制构建，用于业务应用。

主流标签变体对比

以官方镜像为例，同一软件通常提供多个变体，适配不同场景：

| 变体标签              | 核心特点                                                     | 适用场景                     |
| --------------------- | ------------------------------------------------------------ | ---------------------------- |
| `alpine`              | 基于 Alpine Linux，体积极小（几 MB~ 几十 MB），使用 musl libc | 生产部署、追求轻量化         |
| `slim`                | 精简版，移除非必要工具，体积小于标准版                       | 平衡功能与体积               |
| `bullseye`/`bookworm` | 基于对应版本 Debian，完整 glibc 环境                         | 兼容性要求高的业务           |
| `latest`              | 默认标签，内容随官方更新而变化                               | 本地测试，**不推荐生产使用** |

镜像仓库 Registry

统一保存镜像而且是多个不同镜像版本的地方，叫做镜像仓库
Docker hub: docker官方的公共仓库，已经保存了大量的常用镜像，可以方便大家直接使用
阿里云，网易等第三方镜像的公共仓库
Image registry: docker 官方提供的私有仓库部署工具，无web管理界面，目前使用较少
Harbor: vmware 提供的自带web界面自带认证功能的镜像私有仓库，目前有很多公司使用

镜像的地址格式

```bash
nginx = docker.io/library/nginx:latest
nginx:latest
nginx:1.20.0
docker.io/library/nginx:1.20.0
docker.io/library/alpine
registry.cn-hangzhou.aliyuncs.com/wangxiaochun/busybox:v1.0
harbor.magedu.com/project/centos:7.2.1511
172.20.0.100/project/centos: latest
```

### 镜像搜索

**官方网站进行镜像的搜索:**

```bash
http://hub.docker.com
http://dockerhub.com
https://hub-stage.docker.com/ 
```

**第三方仓库**

```bash
https://quay.io/              # 红帽公司维护
https://registry.k8s.io       # kubernetes 仓库
http://cr.console.aliyun.com  # 阿里云仓库
```

执行docker search命令进行搜索，例如：

```bash
Usage: docker search [OPTIONS] TERM
Options:
  -f, --filter filter   Filter output based on conditions provided
      --format string   Pretty-print search using a Go template
      --limit int       Max number of search results (default 25)
      --no-trunc        Don't truncate output
说明:  
OFFICIAL: 官方
AUTOMATED: 使用第三方docker服务来帮助编译镜像，可以在互联网上面直接拉取到镜像，减少了繁琐的编译过程
```

示例：

```bash
docker search centos
NAME                               DESCRIPTION      STARS               OFFICIAL           AUTOMATED
centos                             The official build of CentOS.        5786               [OK]            
ansible/centos7-ansible           Ansible on Centos7                    126                [OK]
jdeathe/centos-ssh                 OpenSSH / Supervisor / EPEL/IUS/SCL  114                [OK]
consol/centos-xfce-vnc             Centos container with "headless"...  108                [OK]
centos/mysql-57-centos7           MySQL 5.7 SQL database server         67                     
imagine10255/centos6-lnmp-php56   centos6-lnmp-php56                    57                 [OK]
tutum/centos                       Simple CentOS docker image with SSH  44  
......                               
```
选择性的查找镜像

```bash
#搜索点赞100个以上的镜像
#旧语法
docker search -s 100 centos
#新语法
docker search --filter=stars=100 centos
```
Alpine 镜像

Alpine 操作系统是一个面向安全的轻型 Linux 发行版。它不同于通常 Linux 发行版，Alpine 采用了musl libc 和 busybox 以减小系统的体积和运行时资源消耗，但功能上比 busybox 又完善的多，因此得到开源社区越来越多的青睐。在保持瘦身的同时，Alpine 还提供了自己的包管理工具 apk，可以通过 https://pkgs.alpinelinux.org/packages 网站上查询包信息，也可以直接通过 apk 命令直接查询和安装各种软件。

- Alpine 官网: https://www.alpinelinux.org/
- Alpine 官方仓库: https://github.com/alpinelinux
- Alpine 官方镜像: https://hub.docker.com/_/alpine/
- Alpine 官方镜像仓库: https://github.com/gliderlabs/docker-alpine
- Alpine 阿里云的镜像仓库: https://mirrors.aliyun.com/alpine/

alpine 管理软件

```bash
/ # cat /etc/apk/repositories
https://dl-cdn.alpinelinux.org/alpine/v3.15/main
https://dl-cdn.alpinelinux.org/alpine/v3.15/community

#修改源替换成国内源
sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/' /etc/apk/repositories
sed -i 's/dl-cdn.alpinelinux.org/mirrors.tuna.tsinghua.edu.cn/' /etc/apk/repositories 
sed -i 's/dl-cdn.alpinelinux.org/mirrors.ustc.edu.cn/' /etc/apk/repositories

#更新源
apk update  #相当于 apt update

#安装软件
apk add vim #相当于 apt install vim

#删除软件
apk del openssh openntp vim #相当于 apt remove openssh 
#安装常见软件
apk update && apk --no-cache add bash curl telnet  wget net-tools pstree zip unzip 

#安装常用编译工具
apk update && apk --no-cache add gcc make curl zip unzip net-tools pstree wget libgcc libc-dev libcurl libc-utils pcre-dev zlib-dev libnfs pcre pcre2 libevent libevent-dev iproute2

#修改时区
apk update && apk --no-cache add tzdata && ln -s /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && echo "Asia/Shanghai" > /etc/timezone

apk add nginx
apk info nginx
apk manifest nginx
ls -l /bin
```

Debian(ubuntu)系统建议安装的基础包

在很多软件官方提供的镜像都使用的是Debian(ubuntu)的系统,比如:nginx,tomcat,mysql,httpd 等,但镜像内缺少很多常用的调试工具.当需要进入容器内进行调试管理时,可以安装以下常用工具包

```bash
# apt update             # 安装软件前需要先更新索引
# apt install procps  #提供top,ps,free等命令
# apt install psmisc  #提供pstree,killall等命令
# apt install iputils-ping  #提供ping命令
# apt install net-tools  #提供netstat网络工具等
```

### 镜像下载

从 docker 仓库将镜像下载到本地，命令格式如下:

```bash
ddocker pull [OPTIONS] NAME[:TAG|@DIGEST]
Options:
  -a, --all-tags               Download all tagged images in the repository
      --disable-content-trust   Skip image verification (default true)
      --platform string         Set platform if server is multi-platform capable
  -q, --quiet                   Suppress verbose output
NAME: 是镜像名,格式:仓库服务器:端口/项目名称/镜像名称，仓库服务器:端口/项目名称/可以省略，默认docker.io/library/
TAG: 即版本号,如果不指定:TAG,则下载最新版镜像,即latest
```

```bash
# 下载最新版镜像
docker pull nginx

# 下载镜像指定版本
docker pull nginx:1.19-alpine
```

hello world 镜像

```bash
docker pull hello-world
Using default tag: latest               #默认下载最新版本
latest: Pulling from library/hello-world
1b930d010525: Pull complete             #分层下载
Digest: sha256:9572f7cdcee8591948c2963463447a53466950b3fc15a247fcad1917ca215a2f 
#摘要
Status: Downloaded newer image for hello-world:latest
docker.io/library/hello-world:latest    #下载的完整地址

```

默认镜像下载保存的路径:

```bash
#29.X版本以后路径
/var/lib/docker/containerd/daemon
#旧版路径
/var/lib/docker/overlay2/镜像ID
```

> 注意: 镜像下载完成后，会自动解压缩，比官网显示的可能会大很多，如: centos8.1.1911下载时只有70MB，下载完后显示237MB

示例：从docker官网下载镜像

```bash
docker pull hello-world
docker pull alpine
docker pull busybox
docker pull nginx    
docker pull centos
docker pull centos:centos7.7.1908
docker pull docker.io/library/mysql:5.7.30
docker pull mysql:5.6.47
```

下载镜像 alpine,busybox等镜像,查看下载的存放目录

```bash
ls /var/lib/docker/overlay2/l
du -sh /var/lib/docker/overlay2
8.0K /var/lib/docker/overlay2

ls /var/lib/docker/overlay2/l
docker pull hello-world
docker pull alpine:3.11.3
3.11.3: Pulling from library/alpine
c9b1b535fdd9: Pull complete 
Digest: sha256:ab00606a42621fb68f2ed6ad3c88be54397f981a7b70a79db3d1172b11c4367d
Status: Downloaded newer image for alpine:3.11.3
docker.io/library/alpine:3.11.3

docker pull busybox
Using default tag: latest
latest: Pulling from library/busybox
bdbbaa22dec6: Pull complete 
Digest: sha256:6915be4043561d64e0ab0f8f098dc2ac48e077fe23f488ac24b665166898115a
Status: Downloaded newer image for busybox:latest
docker.io/library/busybox:latest

docker pull centos:centos8.1.1911
centos8.1.1911: Pulling from library/centos
1234567890abcdef: Pull complete 
Digest: sha256:1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
Status: Downloaded newer image for centos:centos8.1.1911
docker.io/library/centos:centos8.1.1911
centos8.1.1911: Pulling from library/centos
8a29a15cefae: Pull complete 
Digest: sha256:fe8d824220415eed5477b63addf40fb06c3b049404242b31982106ac204f6700
Status: Downloaded newer image for centos:centos8.1.1911
docker.io/library/centos:centos8.1.1911

du -sh /var/lib/docker/overlay2/*
5.9M /var/lib/docker/overlay2/1802616f4c8e0a0b52c839431b6faa8ac21f4bd831548dcbd46943d3f60061fa
16K  /var/lib/docker/overlay2/5773b92e1351da5e589d0573d9f22d1ec3be1e0e98edbfcddba4b830f12c7be2
1.3M /var/lib/docker/overlay2/de31641b8d2207de7f08eabb5240474a1aaccfef08b6034dcee02b9623f8d9dc
252M /var/lib/docker/overlay2/f41df336075611f9e358e5eaf2ebd5089920a90ba68760cdec8da03edff362f7
20K  /var/lib/docker/overlay2/l

docker images 
REPOSITORY         TAG                 IMAGE ID           CREATED            SIZE
alpine             3.11.3             e7d92cdc71fe        7 days ago         5.59MB
centos             centos8.1.1911     470671670cac        7 days ago         237MB
busybox            latest             6d5fcfe5ff17        4 weeks ago        1.22MB
hello-world        latest             fce289e99eb9        12 months ago      1.84kB
```






















### 镜像加速和配置优化

**为什么需要加速器**：默认 `docker pull` 直连 Docker Hub（registry-1.docker.io），国内经常超时、TLS 握手失败。registry mirror 相当于在 Docker 守护进程前面挂一个"国内中转站"：pull 时 Docker 先问镜像站要，中转站没有再回源 Docker Hub，对用户透明。

配置文件 `/etc/docker/daemon.json`（Docker Engine 29.x，2026 年当前稳定线）完整示例：

```json
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://docker.1panel.live",
    "https://docker.1ms.run"
  ],
  "insecure-registries": [
    "harbor.internal.local:80"
  ],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "3"
  },
  "exec-opts": ["native.cgroupdriver=systemd"],
  "data-root": "/var/lib/docker",
  "live-restore": true,
  "max-concurrent-downloads": 10
}
```

改完必须重载生效：

```bash
sudo systemctl daemon-reload
sudo systemctl restart docker
docker info | grep -A 5 "Registry Mirrors"
```

**2024 年后国内加速器现状（务必知道）**：

- 2024 年中起，大厂公共加速器批量关停或限流：USTC（`docker.mirrors.ustc.edu.cn`）、网易（`hub-mirror.c.163.com`）已停止公共服务；阿里云个人加速器（`xxxx.mirror.aliyuncs.com`）官方公告已停止同步最新镜像，拉 `latest` 可能拿到旧层。
- 现在能用的基本是社区维护的中转站（`docker.m.daocloud.io`、`docker.1panel.live`、`docker.1ms.run`、`hub.rat.dev` 等），特点是**随时可能挂、有白名单/限流、不保证镜像新鲜**，只能当开发环境的尽力而为。
- 云厂商内网镜像站只在自家 VPC 内可用：腾讯云 `https://mirror.ccs.tencentyun.com`（仅腾讯云服务器内网）、阿里云内网域名同理，出了云就不通。

**生产可用的替代思路**：

1. **自建 Harbor proxy cache（推荐）**：Harbor 自带代理缓存项目，把 docker.io / gcr.io / quay.io 缓存到内网，全公司共享，稳定可控，见后文"Docker 仓库管理"。
2. **镜像名前缀替换**：不改 daemon，直接把镜像名写成中转站前缀，如 `docker pull docker.m.daocloud.io/library/nginx:1.27`，pull 下来后 `docker tag` 回原名。
3. **离线导入**：见本节末尾"拉取不可描述的镜像"。

::: warning 不要把公共加速器写死进生产配置
公共加速器随时可能失效。生产环境 pull 失败时第一反应是 `docker info` 看 mirrors 是否还通；更稳妥的做法是所有镜像一律经内网 Harbor 分发，加速器只给开发机用。
:::

### 查看本地镜像

```bash
docker images
# 等价于
docker image ls
```

典型输出：

```
REPOSITORY    TAG       IMAGE ID       CREATED        SIZE
nginx         1.27      6f59c5d4d6dc    2 weeks ago     192MB
mysql         8.4       908200b0b1a4    3 weeks ago     780MB
<none>        <none>    a1b2c3d4e5f6    5 days ago      120MB   ← dangling 悬空镜像
```

各列含义：

| 列 | 含义 |
|---|---|
| REPOSITORY | 镜像仓库名（去掉仓库地址前缀的短名） |
| TAG | 标签；`<none>` 表示没打标签 |
| IMAGE ID | 镜像唯一 ID（SHA256 前 12 位）；`--no-trunc` 看完整 |
| CREATED | 镜像**构建时间**（不是你 pull 下来的时间） |
| SIZE | 镜像展开后的逻辑大小；层有共享，实际占盘比这个小 |

常用过滤：

```bash
docker images nginx                      # 只看 nginx 仓库
docker images "nginx:1.27"               # 指定 tag
docker images -f "dangling=true"         # 只看悬空镜像
docker images -f "before=nginx:1.27"     # 某镜像之前构建的
docker images -q                         # 只输出 IMAGE ID，常配合批量删除
```

### 镜像导出

把本地镜像打成 tar 包，用于离线拷贝：

```bash
docker save -o nginx-1.27.tar nginx:1.27
# gzip 压缩省空间（不写 -o，输出走 stdout）
docker save nginx:1.27 | gzip > nginx-1.27.tar.gz
# 一次导出多个镜像到同一个包
docker save -o web-images.tar nginx:1.27 redis:7.4
```

导出的是镜像的所有层和元数据，**镜像名和 tag 会原样保留**，load 回来后 `docker images` 里名字不变。

### 镜像导入

```bash
docker load -i nginx-1.27.tar
# gzip 包可直接 load（Docker 自动识别压缩）
docker load -i nginx-1.27.tar.gz
```

典型输出：

```
Loaded image: nginx:1.27
```

`docker load` 与 `docker import` 的区别：

- `docker load`：加载 `docker save` 导出的镜像包，**保留历史层和 tag**，用于镜像搬家。
- `docker import`：把一个 rootfs 目录/压缩包导入成镜像，**不保留历史层**，常用于从虚拟机磁盘模板做基础镜像。

### 镜像删除

```bash
docker rmi nginx:1.27            # 按 名字:tag 删
docker rmi 6f59c5d4d6dc          # 按 IMAGE ID 删
```

**删除规则**：

- 一个镜像可能被多个 tag 指向，`docker rmi 名字:tag` 只是摘掉那个标签；标签摘光了才真正删层。
- 正在被容器使用的镜像删不掉，报错形如：
  `conflict: unable to delete ... (must be forced): image is being used by stopped container xxx`

处理办法：

```bash
docker ps -a | grep nginx          # 找到用这个镜像的容器
docker rm -f <容器ID>              # 删掉容器后再 rmi
# 非必要不要用：docker rmi -f <ID>（强删会把引用它的容器写层搞坏）
```

### 清理`dangling`状态镜像

`dangling`（悬空）镜像就是 `<none>:<none>`：你重新 build 同名镜像后，旧 tag 被摘走但层没人要了，就变成悬空垃圾。

```bash
# 列出悬空镜像
docker images -f "dangling=true"
# 只清理悬空镜像（安全，不会删任何有名字的镜像）
docker image prune
# 连"没有任何容器引用"的镜像一起删（确认后再用）
docker image prune -a
```

可加 `--filter "until=24h"` 只删超过 24 小时的，`-f` 跳过交互确认。生产上 `prune -a` 前务必确认后面要用的镜像不是还没 pull 的——删了得重新下载。

### 镜像打标签

```bash
docker tag 原镜像:原tag 仓库地址/项目名/镜像名:新tag
# 例：把本地 nginx:1.27 打上 Harbor 私有仓库标签
docker tag nginx:1.27 harbor.internal.local:80/library/nginx:1.27
```

**推送前提**：

1. tag 里的仓库地址前缀决定 push 到哪，必须和实际仓库一致；
2. 先 `docker login harbor.internal.local:80` 登录；
3. 再 `docker push harbor.internal.local:80/library/nginx:1.27`。

`docker tag` **不复制镜像层**，只是给同一个 IMAGE ID 多起一个名字，秒级完成。

### 拉取不可描述的镜像

这里说的是 Docker Hub 之外、国内直连不通的镜像：`gcr.io`、`registry.k8s.io`（原 k8s.gcr.io）、`quay.io` 上的镜像。

完整离线流程：**在有网的机器上 pull 下来 → save 成 tar → 拷到内网 → load**。

```bash
# ===== 第一步：在能联网的机器上 =====
# 方式 A：官方镜像走中转站，镜像名加前缀
docker pull docker.m.daocloud.io/library/nginx:1.27
docker tag docker.m.daocloud.io/library/nginx:1.27 nginx:1.27

# 方式 B：registry.k8s.io 的镜像走对应中转前缀
# 例：registry.k8s.io/pause:3.9  →  k8s.m.daocloud.io/pause:3.9
docker pull k8s.m.daocloud.io/pause:3.9
docker tag k8s.m.daocloud.io/pause:3.9 registry.k8s.io/pause:3.9

# 打成离线包（可多个镜像一起）
docker save -o images-offline.tar nginx:1.27 registry.k8s.io/pause:3.9

# ===== 第二步：scp / 拷贝到内网目标机器 =====
scp images-offline.tar root@内网机器:/tmp/

# ===== 第三步：目标机器加载 =====
docker load -i /tmp/images-offline.tar
docker images        # 确认镜像名和 tag 都在
```

生产环境建议把这套流程固化成发布脚本，或者直接内网搭 Harbor proxy cache 统一代理。

## 镜像构建

### Dockerfile 常用指令

把"装运行环境、拷代码、暴露端口、定义启动命令"这一套手工操作写成一个文本文件 Dockerfile，`docker build` 就能自动、可重复地造出一模一样的镜像。

| 指令 | 作用 | 要点 |
|---|---|---|
| `FROM` | 指定基础镜像 | 每条 Dockerfile 的第一条指令；多阶段构建时可写多个 FROM |
| `WORKDIR` | 设置工作目录 | 后续 RUN/CMD 的相对路径都基于它；目录不存在自动建 |
| `COPY` | 拷本地文件进镜像 | 只支持 build 上下文里的文件；支持 `--chown=user:group` |
| `ADD` | 拷文件（增强版） | 会自动解压 tar、能直接下 URL；行为太隐式，**官方建议优先用 COPY** |
| `RUN` | 构建时执行命令 | 每条 RUN 生成一层；多条用 `&&` 串起来减少层数 |
| `ENV` | 环境变量 | 构建期和运行期都生效 |
| `ARG` | 构建参数 | 只在 build 时生效（`--build-arg` 传入），容器运行后不存在 |
| `EXPOSE` | 声明端口 | **只是文档作用**，不真正发布端口；发布靠 `-p` |
| `CMD` | 容器默认启动命令 | `docker run 镜像 后面的命令` 会整体覆盖它 |
| `ENTRYPOINT` | 容器入口 | 不被 run 后面的参数覆盖（除非 `--entrypoint`）；常和 CMD 配合做"固定程序+可变参数" |

CMD 与 ENTRYPOINT 的经典配合：

```dockerfile
ENTRYPOINT ["nginx"]
CMD ["-g", "daemon off;"]
# docker run my-nginx        → nginx -g "daemon off;"
# docker run my-nginx -t     → nginx -t（CMD 被替换，ENTRYPOINT 不变）
```

### 完整 Dockerfile 示例（Spring Boot 应用）

```dockerfile
# 构建阶段
FROM maven:3.9-eclipse-temurin-21 AS builder
WORKDIR /build
COPY pom.xml .
RUN mvn dependency:go-offline          # 先下依赖，充分利用层缓存
COPY src ./src
RUN mvn package -DskipTests

# 运行阶段（最终镜像）
FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
RUN addgroup -S app && adduser -S app -G app
COPY --from=builder /build/target/demo-0.0.1.jar app.jar
USER app
EXPOSE 8080
ENV JAVA_OPTS="-Xms256m -Xmx512m"
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]
```

### 构建命令

```bash
docker build -t myapp:1.0 .
# 指定 Dockerfile 路径、传构建参数、禁用缓存
docker build -f deploy/Dockerfile -t myapp:1.0 \
  --build-arg VERSION=1.0 --no-cache .
```

末尾的 `.` 是 build 上下文（context），决定了 `COPY` 能拷宿主机上哪些文件。

### 多阶段构建

上面 Dockerfile 就是多阶段：第一阶段带 Maven + JDK 全套编译工具（好几百 MB），第二阶段只把编译产物 jar 包拷进一个瘦 JRE 镜像。最终镜像可能从 800MB 瘦到 170MB。**原则：编译工具链不进最终镜像。**

### 分层缓存原理与最佳实践

镜像是一层一层叠出来的（UnionFS）。build 时 Docker 从上到下执行 Dockerfile 指令，**某一层的输入没变，就直接复用上次的缓存**；一旦某层失效，它下面所有层全部重新构建。

由此推出四条最佳实践：

1. **`.dockerignore` 必备**：排除 `.git`、`target/`、`node_modules/`、本地无关大文件，避免无关文件变动导致缓存全失效。
   ```
   .git
   target/
   node_modules/
   *.md
   ```
2. **把"变动少的"指令放上面**：先 `COPY pom.xml` 下依赖，再 `COPY src`——pom.xml 不变时依赖层一直命中缓存，改源码不用重新下 Maven 依赖。
3. **合并 RUN**：`RUN yum install -y xxx && yum clean all`，别一条 RUN 装一个包；每层都会留痕占体积。
4. **层最小化**：每个 RUN 做完顺手清理缓存（`rm -rf /var/cache/dnf/*`、`apt clean`），否则临时文件会被永久带进镜像。

## 容器的数据管理

### docker run 常用参数完整讲解

```bash
docker run -d \
  --name web01 \
  -p 8080:80 \
  -v /data/web/html:/usr/share/nginx/html \
  -e TZ=Asia/Shanghai \
  --restart=always \
  --cpus="1.0" -m="512m" \
  nginx:1.27
```

| 参数 | 作用 | 小白类比 |
|---|---|---|
| `-d` | 后台运行 | 把程序丢后台，不占着终端 |
| `-p 宿主:容器` | 端口映射 | 给容器门口装个转接分机 |
| `-v` | 挂载数据卷/目录 | 给容器开一个和宿主机共享的文件夹 |
| `-e KEY=VAL` | 环境变量 | 程序启动时读的配置开关 |
| `--name` | 容器起名 | 不起名 Docker 随机起个逗比名字 |
| `--restart` | 重启策略（no / on-failure:5 / always / unless-stopped） | 崩了要不要自动拉起来 |
| `-it` | 交互式 + 伪终端 | 想跟容器里的程序对话就加它 |
| `--rm` | 退出后自动删容器 | 一次性任务跑完就打扫干净 |

### 容器生命周期命令

```bash
docker create web01 nginx:1.27     # 建而不启
docker start web01
docker stop web01                  # 先发 SIGTERM，宽限 10s 后 SIGKILL
docker restart web01
docker pause web01 && docker unpause web01   # 冻结/解冻
docker rm web01                    # 删已停止容器；-f 连运行中的一起删
docker update --cpus=2 web01      # 运行中动态改资源限制
```

### exec / logs / cp / stats

```bash
docker exec -it web01 /bin/bash                 # 进入运行中容器（容器里得有 bash/sh）
docker exec web01 ls /etc/nginx                 # 不进入，直接跑一条命令
docker logs -f --since 10m --tail 200 web01     # 跟踪最近 200 行日志
docker stats                                   # 实时看所有容器 CPU/内存/网络
docker cp web01:/etc/nginx/nginx.conf ./        # 容器 → 宿主机拷文件
docker cp ./index.html web01:/usr/share/nginx/html/   # 宿主机 → 容器
```

### cgroup 资源限制

```bash
# 最多 1 核 CPU、512MB 内存、swap 不额外给
docker run -d --name web01 \
  --cpus="1.0" --memory="512m" --memory-swap="512m" \
  nginx:1.27
# CPU 权重（相对值，默认 1024，越大越能抢 CPU）
docker run -d --cpu-shares=2048 --name big web01 nginx:1.27
```

验证方法：

```bash
docker inspect web01 --format '{{.HostConfig.NanoCpus}} {{.HostConfig.Memory}}'
# cgroup v2（Docker 29 默认）下宿主机直接看
cat /sys/fs/cgroup/system.slice/docker-<容器ID>.scope/memory.max
cat /sys/fs/cgroup/system.slice/docker-<容器ID>.scope/cpu.max
```

**关于 `No swap limit support`**：`docker info` 出现这条 WARNING 时，`--memory-swap` 不生效，需要给内核开 `swapaccount`。本案例站内已有完整记录：[解决 SWAP 报警提示](/cases/t-docker-swap)。两种做法：

::: details Debian/Ubuntu 做法
编辑 `/etc/default/grub`，在 `GRUB_CMDLINE_LINUX` 末尾加 `swapaccount=1`：

```bash
GRUB_CMDLINE_LINUX="... swapaccount=1"
```

然后：

```bash
sudo update-grub
sudo reboot
```
:::

::: details RHEL/CentOS/Rocky 做法
编辑 `/etc/default/grub`，同样在 `GRUB_CMDLINE_LINUX` 加 `swapaccount=1`，然后重新生成 GRUB 配置：

```bash
# BIOS 机器
grub2-mkconfig -o /boot/grub2/grub.cfg
# UEFI 机器（路径按发行版略有不同）
grub2-mkconfig -o /boot/efi/EFI/rocky/grub.cfg
sudo reboot
```
:::

重启后 `docker info` 里那条 WARNING 消失即生效。

## 存储

### named volume 与 bind mount 区别

| | named volume（命名卷） | bind mount（绑定挂载） |
|---|---|---|
| 存储位置 | Docker 管理（默认 `/var/lib/docker/volumes/`） | 用户指定宿主机任意路径 |
| 谁管理 | Docker | 用户 |
| 适合 | 数据库数据目录（MySQL/PG 数据） | 开发时代码挂载、配置文件 |
| 移植性 | 强，`docker volume` 统一管理 | 弱，强依赖宿主机目录结构 |
| 权限 | Docker 帮你处理 | 自己搞定 uid/gid |

### 完整命令

```bash
# named volume
docker volume create pgdata
docker run -d -v pgdata:/var/lib/postgresql/data postgres:17
docker volume ls
docker volume inspect pgdata        # 看 Mountpoint
docker volume rm pgdata

# bind mount（:ro 只读）
docker run -d -v /opt/nginx/conf.d:/etc/nginx/conf.d:ro nginx:1.27
# 语义更清晰的等价写法
docker run -d --mount type=bind,source=/opt/nginx/conf.d,target=/etc/nginx/conf.d,readonly nginx:1.27
```

### 容器间数据共享

两个容器共享同一份数据，用一个共享 volume：

```bash
docker volume create shared
docker run -d --name app1 -v shared:/data nginx:1.27
docker run -d --name app2 -v shared:/data:ro nginx:1.27   # app2 只读挂载
```

或者用 `--volumes-from app1`，把另一个容器的所有挂载原样继承过来。

### volume 备份恢复思路

```bash
# 备份：临时起一个容器，把 volume 挂进来打 tar，输出到宿主机当前目录
docker run --rm -v pgdata:/volume -v $(pwd):/backup alpine \
  tar czf /backup/pgdata-backup.tar.gz -C /volume .

# 恢复：把 tar 解开回 volume
docker run --rm -v pgdata:/volume -v $(pwd):/backup alpine \
  tar xzf /backup/pgdata-backup.tar.gz -C /volume
```

## 网络管理

### 内置网络原理

```bash
docker network ls
```

| 驱动 | 原理 | 用途 |
|---|---|---|
| bridge（默认） | 宿主机上虚拟网桥 docker0，容器拿 172.17.x.x 内网 IP，出去靠 NAT | 默认单机容器网络 |
| host | 容器直接用宿主机网络栈，**无网络隔离**，端口直接占宿主机端口 | 性能要求极高、不需要端口隔离的场景 |
| none | 只有 lo 回环，完全没网络 | 安全敏感的计算任务 |
| container | 复用另一个容器的网络栈（sidecar 模式） | K8s Pod 内同 Pod 容器就是这个 |

### 用户自定义 bridge（推荐）

默认 bridge 里容器之间只能靠 IP 互访；**用户自建的 bridge 自带 DNS，容器名就能互相解析**：

```bash
docker network create mynet
docker run -d --name redis --network mynet redis:7.4
docker run -d --name app --network mynet -e REDIS_HOST=redis myapp:1.0
# app 容器里直接用容器名就能 ping 通
docker exec app ping -c 2 redis
```

### 端口映射 -p 四种写法

```bash
docker run -p 8080:80 ...           # 宿主机所有网卡 8080 → 容器 80
docker run -p 127.0.0.1:8080:80    # 只绑本机回环，外部访问不到
docker run -p 80:80/udp ...        # 指定协议（默认 tcp）
docker run -P ...                   # 大写：随机映射高位端口，EXPOSE 端口全暴露
```

### 容器间互联与排错

```bash
docker network inspect mynet       # 看该网络下所有容器和分配的 IP
docker exec app ip addr            # 看容器自己的网卡
docker exec app getent hosts redis  # 验证 DNS 解析
```

连不通先查三步：两个容器是不是同一个网络？容器名拼对没？目标容器里的服务监听的是 `0.0.0.0` 而不是 `127.0.0.1`？

## DockerCompose 容器单机编排

一台机器上要跑 nginx + 应用 + redis 三个容器，手动 run 十条命令很烦。Compose 就是把这一坨写进一个 YAML 文件，一条 `docker compose up -d` 全拉起来。

> Docker Engine 29 里 Compose 是官方插件（命令是 `docker compose`，带空格），老的独立二进制 `docker-compose` 已基本淘汰。

### compose.yaml 完整语法

```yaml
services:
  web:
    image: nginx:1.27
    # 或者本地构建：
    # build:
    #   context: ./web
    #   dockerfile: Dockerfile
    ports:
      - "8080:80"
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - web_html:/usr/share/nginx/html
    environment:
      - TZ=Asia/Shanghai
    depends_on:
      - app
    networks:
      - frontend
    restart: always

  app:
    build: ./app
    image: myapp:1.0
    environment:
      - REDIS_HOST=redis
    networks:
      - frontend
      - backend
    restart: always

  redis:
    image: redis:7.4
    volumes:
      - redis_data:/data
    networks:
      - backend
    restart: always

volumes:
  web_html:
  redis_data:

networks:
  frontend:
  backend:
```

### 常用命令

```bash
docker compose up -d                  # 后台启动全部
docker compose ps                     # 看状态
docker compose logs -f web            # 跟某个服务日志
docker compose exec app sh            # 进某个服务容器
docker compose down                   # 停并删容器/网络（加 -v 连 volume 一起删）
docker compose up -d --scale app=3    # app 扩到 3 个实例（注意此时 ports 不能写死）
docker compose build                  # 重新构建带 build 的服务
```

::: warning `depends_on` 不代表"对方已就绪"
`depends_on` 只控制启动顺序，**不保证对方端口已经能连上**。应用启动时连数据库失败要自己重试，不能依赖 Compose 的启动顺序。
:::

## Docker 仓库管理

Docker Hub 国内访问不稳，公司内部也不可能把镜像传到公网。**Harbor** 就是企业自建的私有镜像仓库：带 Web 界面、项目权限、镜像漏洞扫描、跨集群复制、LDAP 集成。

### 定位与架构

Harbor 本质上是在开源 OCI Distribution（registry）外面套了一层管理壳，主要组件：

- `core`（portal + api）：Web 和 API 入口
- `registry`：真正存镜像的 OCI 仓库
- `jobservice`：复制、GC 等异步任务
- `database`（PostgreSQL）：存项目、用户、权限元数据
- `redis`：缓存
- `trivy`：镜像漏洞扫描

当前稳定版 **v2.15.x**（2026 年，以 GitHub releases 最新为准）。

### 部署要点

最简方式是用官方离线安装包（自带所有镜像 tar，适合内网）：

```bash
# 从 github.com/goharbor/harbor/releases 下载 harbor-offline-installer-v2.15.x.tgz
tar xzf harbor-offline-installer-v2.15.x.tgz
cd harbor
cp harbor.yml.tmpl harbor.yml
# 编辑 harbor.yml：改 hostname、http 端口、admin 初始密码、数据盘位置
./install.sh
```

前置依赖：本机要有 Docker 和 docker compose。上 K8s 集群则用官方 Helm chart（`helm repo add harbor https://helm.goharbor.io`）。

### 完整推拉流程

```bash
# 1. 浏览器登录 Harbor Web → 新建项目（如 library，公开或私有）
# 2. 本机登录
docker login harbor.internal.local:80 -u admin
# 3. 打标签（前缀必须是 Harbor 地址/项目）
docker tag nginx:1.27 harbor.internal.local:80/library/nginx:1.27
# 4. 推送
docker push harbor.internal.local:80/library/nginx:1.27
# 5. 别的机器拉取
docker login harbor.internal.local:80
docker pull harbor.internal.local:80/library/nginx:1.27
```

### HTTP 非 HTTPS 仓库

Harbor 走纯 HTTP 内网地址时，Docker 客户端默认拒绝。在每个客户端的 `/etc/docker/daemon.json` 里加：

```json
{
  "insecure-registries": ["harbor.internal.local:80"]
}
```

然后 `sudo systemctl restart docker`。生产建议上 HTTPS（harbor.yml 里配证书），insecure 只用于纯内网测试。

### 日常运维要点

- 数据目录默认 `/data/registry`，一定要挂大盘；
- 定期在 Web 上跑"垃圾回收（GC）"，清理被删除但还占盘的镜像层；
- 开启 Trivy 漏洞扫描，可配置 block 高危镜像；
- 项目按团队划分，用机器人账号（robot account）给 CI/CD 用，别用 admin 密码到处塞。

## Docker 的资源限制

### docker system df / prune 体系

```bash
docker system df                 # 看 Docker 占盘概况（镜像/容器/卷/网络）
docker system df -v              # 明细
docker system prune              # 清停止容器、无用网络、悬空镜像（相对安全）
docker system prune -a --volumes # 连未使用的镜像和卷一起清（高危！）
```

### 日志驱动与大小轮转

容器默认日志驱动 `json-file`，容器 stdout 日志会**无限增长，是生产磁盘被写满的头号原因**。必须配大小轮转：

全局配 `/etc/docker/daemon.json`（对之后新建的所有容器生效）：

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "3"
  }
}
```

单个容器覆盖：

```bash
docker run --log-opt max-size=100m --log-opt max-file=3 ...
```

### 容器监控

```bash
docker stats                 # 实时 CPU / MEM / 网络 / IO
docker stats --no-stream     # 打一次快照
```

底层数据全部来自 cgroup，和宿主机 `/sys/fs/cgroup/` 下对应目录对得上。

### 生产常见 FAQ

| 现象 | 原因 | 解法 |
|---|---|---|
| 磁盘突然被写满 | 容器 json 日志暴涨 | 配 max-size/max-file；已发生的 `truncate -s 0 $(docker inspect -f '{{.LogPath}}' 容器名)` |
| 容器内时间慢 8 小时 | 容器默认 UTC | run 加 `-e TZ=Asia/Shanghai`，或挂 `/etc/localtime:/etc/localtime:ro` |
| 容器时间漂移 | 宿主机时钟源异常 | 确认宿主机 chronyd / systemd-timesyncd 正常；容器共享宿主内核时钟 |
| `--restart=always` 不生效 | 容器是被手动 stop 的 | `always` 无视手动 stop 也会拉起；想尊重手动停止用 `unless-stopped` |
| 误删镜像/容器 | `prune -a` 乱用 | 删除前 `docker system df -v` 看清；重要镜像提前 push 到 Harbor |
| push 报 `server gave HTTP response to HTTPS client` | Harbor 是 HTTP | 配 insecure-registries（见上节） |

## 相关速查

- [Docker 命令速查](/reference/docker-commands)
- [SWAP 报警排查案例](/cases/t-docker-swap)

### 官方文档

- Docker Engine 官方文档：https://docs.docker.com/engine/
- Dockerfile 参考：https://docs.docker.com/build/concepts/dockerfile/
- Harbor 官方文档：https://goharbor.io/docs/
- Compose 规范：https://docs.docker.com/compose/compose-file/
