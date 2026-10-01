# Docker

::: tip 本篇定位
覆盖镜像/容器、Dockerfile、卷、网络、底层原理和资源限制。
:::

## 高频面试题

### Q1：Docker 网络模式？

**我的答案：**

结论：Docker 有五种网络模式，常用的是 **bridge、host、none、container**，再加上自定义 bridge。

第一，**bridge（默认）**。每个容器在 docker0 网桥（一般是 172.17.0.0/16）上拿到一个独立 IP，容器之间通过 NAT 出去访问外网。外部要访问容器，必须 `-p 8080:80` 做端口映射，本质是 iptables DNAT。单机容器之间互通没问题，但跨主机就麻烦，而且默认 bridge 不支持容器名 DNS 解析。

第二，**host**。容器直接共享宿主机网络命名空间，没有独立网卡，容器里监听 80 就是宿主机的 80。网络性能最好（没有 NAT 开销），但端口会打架，谁先占谁用。性能敏感、端口不冲突的任务型容器用。

第三，**none**。容器有自己的 net namespace，但不配置任何网卡，只有 lo 回环。完全隔离，适合安全计算、临时任务。

第四，**container**。新容器不创建自己的网络，而是复用另一个已有容器的网络命名空间。两个容器共享同一个 IP 和端口空间，sidecar 模式（比如 Istio 代理）就这么玩。

第五，**自定义 bridge 网络**。生产推荐：`docker network create mynet`，容器加入 `mynet` 后，**可以直接用容器名互相 DNS 解析**（默认 bridge 不行），还能做更细的隔离。微服务单机部署基本都这么搞。

跨主机容器通信要靠 Overlay 网络（Swarm 自带、或 Calico/Flannel），单机 bridge 解决不了。

---

### Q2：Docker 底层原理？

**我的答案：**

结论：Docker 容器不是虚拟机，本质是**宿主机上一个被 namespace 隔离、被 cgroup 限制、用 rootfs 装了独立文件系统的普通进程**。三个核心技术：

第一，**Linux Namespace 做隔离**。容器看起来像一台独立机器，是因为它有自己一套 namespace：`PID`（独立进程树，容器里 1 号进程是你的应用）、`NET`（独立网卡/路由表）、`IPC`、`MNT`（独立挂载点）、`UTS`（独立 hostname）、`USER`（用户映射）。隔离了这些，进程就以为自己独占一个系统。

第二，**Cgroup 做资源限制**。namespace 只隔离"看不见"，不限制"用多少"。cgroup 负责限制这个组进程能用多少 CPU、内存、磁盘 IO、进程数。`docker run --cpus=1.5 -m 512m` 就是在配 cgroup。容器内存超了，OOM Killer 就出来杀进程。

第三，**rootfs + Overlay2 做文件系统**。镜像一层层叠起来，底层是只读的（`docker image inspect` 能看到多层 layer），容器启动时在最上面挂一层可写层（upperdir）。用的是 OverlayFS：lowerdir 是各层只读镜像，upperdir 是容器可写层，mergeddir 是联合视图。你改一个文件，Copy-on-Write 把它从底层复制到 upperdir 再改，不影响镜像层。这就是为什么镜像能多层复用、容器启动快。

所以镜像本质是一堆只读 layer + 一个 json 配置，容器就是"镜像 layer 联合挂载 + namespace 起进程 + cgroup 限资源"。

---

### Q3：镜像如何优化体积？

**我的答案：**

结论：镜像优化三板斧——**选小基础镜像、多阶段构建、减少层数并清理缓存**。

第一，**基础镜像选小的**。能跑 Alpine 就别跑 CentOS/Debian，`alpine` 才 5MB 左右；跑 Go/Rust 这种静态编译语言直接用 `scratch`（空镜像）或 `distroless`，十几 MB 搞定。别用 `latest` 标签，固定版本号。

第二，**多阶段构建**。这是最有效的手段。Dockerfile 写两个阶段：第一阶段用 `golang:1.22` 这种大镜像编译出二进制；第二阶段 `FROM alpine`，把第一阶段编译产物 `COPY --from=0 /build/app /app` 进去。最终镜像里只有二进制和运行时依赖，编译工具链全部留在第一阶段，不带进最终镜像。Java 项目也这么玩，Maven 编译阶段和 JRE 运行阶段分开。

第三，**合并 RUN 并清理缓存**。每写一个 `RUN` 就多一层，所以 `apt-get install`、`yum install`、`pip install` 这种，要把安装、清理缓存、删临时文件写在同一个 RUN 里，用 `&&` 连起来：

```dockerfile
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*
```

不删 `/var/lib/apt/lists/*`，apt 的索引就留在镜像层里，白占几百 MB。

第四，**写 `.dockerignore`**，把 `.git`、`node_modules`、本地配置文件、`*.log` 排除掉，别让它们进构建上下文。

第五，**用 `.dockerignore` 排敏感文件**，构建上下文传得也快。

优化完用 `docker history <镜像>` 看每一层多大，找胖的那层；`docker images` 对比优化前后体积。

---

### Q4：容器异常如何排查？

**我的答案：**

结论：容器挂了按"**状态 → 日志 → 进程 → 配置 → 资源**"五步查。

第一步，看状态。`docker ps -a`，重点看 STATUS 列：`Exited (137) 10 minutes ago` 是被 OOM 杀的（137=128+9 SIGKILL）；`Exited (1)` 是应用自己报错退出；`Restarting` 一直在重启说明启动就崩。

第二步，看日志。`docker logs <容器>` 看标准输出；`docker logs --tail 200 -f <容器>` 实时跟踪。`--since 10m` 看最近 10 分钟。应用日志如果写在容器内文件里，要挂 volume 出来，不然容器删了日志就没了。

第三步，进容器看。`docker exec -it <容器> sh`（Alpine 没 bash）。如果容器根本起不来、exec 不进去，用 `docker run --entrypoint=sh <镜像>` 起一个临时容器挂同样的卷和网络进去查。

第四步，看配置。`docker inspect <容器>`，重点看 `State`（退出码、OOMKilled、Error）、`Mounts`（卷挂对没）、`NetworkSettings`（IP、端口映射）、`HostConfig`（资源限制、重启策略）。

第五步，查资源。`docker stats` 实时看每个容器 CPU/内存/网络；`docker update` 动态调限制。OOM 了就看 `dmesg | tail`，调大 `-m` 或者优化应用内存。

常见坑：镜像里没装 `sh`/`curl`/`ss` 这些工具（distroless 镜像常见），exec 进去啥都干不了，这时候要靠 sidecar 临时调试容器，或者把镜像换成带 shell 的 debug 版。容器一直 CrashLoopBackOff，八成是配置文件/环境变量/挂载不对，先看日志里第一行报错，别瞎猜。

---

## 相关链接

- [相关文档](/reference/docker-commands)
