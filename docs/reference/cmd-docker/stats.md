# docker stats 命令详解：实时看每个容器吃了多少 CPU/内存/网络

> 本文是 [Docker 命令速查](../docker-commands#进入与日志) 中 `docker stats` 的从 0 到 1 详解。
> 目标：把 `docker stats --help` 里的每个选项和每一列含义讲清楚，多看几遍后，你在服务器上敲 `docker stats --help` 就知道该用哪个选项。
> 环境依据：Docker Engine 28.x（docker CLI 28.x），cgroup v2、containerd 默认运行时；本沙箱未安装 docker，列含义与输出据 [Docker 官方命令参考](https://docs.docker.com/reference/cli/docker/container/stats/) 核实，示例输出为示意。

## 一、命令是干什么的

`docker stats` 像一个"容器版 top"：实时刷新每个运行中容器的资源占用——CPU 百分比、内存用量/上限、网络收发、磁盘块读写、进程/线程数。用来一眼看出**哪个容器在吃资源、哪个快超内存限制**。

- 不带参数：所有运行中容器，每秒刷新一次；
- 跟容器名：只看指定几个；
- `--no-stream`：只取一次快照就退出（适合脚本）。

> 类比：宿主机上 `top` 看整机进程，`docker stats` 就是按容器聚合后的 top，让你不用进容器就知道谁在捣乱。

## 二、命令语法

```bash
docker stats [选项] [容器...]
```

- `[选项]`：控制是否流式、输出格式；
- `[容器...]`：可选，指定看哪几个容器名/ID；不写就看全部运行中容器。
- 已停止的容器传了也**没有数据**（显示 0B/0B）。

## 三、选项全表（对照 `docker stats --help`）

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-a`，`--all` | 显示所有容器（含已停止） | 想看全量（停止的会显示 0） |
| `--no-stream` | 不流式，只取第一次快照就退出 | 脚本里采集一次数据 |
| `--no-trunc` | 不截断输出 | 字段太长被截时 |
| `--format` | 用 Go 模板自定义输出列 | 只想要 CPU 和内存，或输出 JSON |

### 输出每一列含义（Linux）

| 列名 | 含义 |
|---|---|
| `CONTAINER ID` / `NAME` | 容器 ID 和名字 |
| `CPU %` | 该容器用掉的 CPU 占整机 CPU 的百分比 |
| `MEM USAGE / LIMIT` | 当前实际用的内存 / 允许用的上限 |
| `MEM %` | 内存用量占上限的百分比 |
| `NET I/O` | 容器网络接口收/发的总流量（下面是收、上面是发） |
| `BLOCK I/O` | 对宿主机块设备读/写的总量 |
| `PIDS` | 容器创建的进程和内核线程总数 |

> 官方说明：Linux 上 CLI 报的 `MEM USAGE` 是**减去 cache** 后的用量（cgroup v2 下取 `inactive_file`），不是裸 cgroup 内存数；`PIDS` 里线程数很多但 `ps` 看到的进程很少，往往是程序在狂开线程。

## 四、由浅入深的典型示例

### 示例 1：看所有运行中容器（默认流式）

```bash
docker stats
```

输出（示意，据 Docker 官方文档）：

```text
CONTAINER ID   NAME              CPU %     MEM USAGE / LIMIT   MEM %     NET I/O          BLOCK I/O      PIDS
b95a83497c91   awesome_brattain  0.28%     5.629MiB / 1.952GiB 0.28%     916B / 0B        147kB / 0B     9
67b2525d8ad1   foobar            0.00%     1.727MiB / 1.952GiB 0.09%     2.48kB / 0B    4.11MB / 0B    2
```

> 每秒刷新，按 `Ctrl+C` 退出。

### 示例 2：只看指定容器

```bash
docker stats awesome_brattain 67b2525d8ad1
```

> 跟几个容器名/ID 就只监控这几个，排除干扰。

### 示例 3：取一次快照就退出（`--no-stream`）

```bash
docker stats --no-stream
```

输出（示意）：

```text
CONTAINER ID   NAME      CPU %     MEM USAGE / LIMIT   MEM %     NET I/O        BLOCK I/O   PIDS
ed37317fbf42  nginx     0.03%     2.352MiB / 982.5MiB 0.24%     539kB / 606kB  0B / 13.3kB 2
```

> 适合写监控脚本，定时跑一次采集数据。

### 示例 4：输出 JSON（`--format`）

```bash
docker stats nginx --no-stream --format "{{ json . }}"
```

输出（示意）：

```text
{"BlockIO":"0B / 13.3kB","CPUPerc":"0.03%","Container":"nginx","ID":"ed37317fbf42","MemPerc":"0.24%","MemUsage":"2.352MiB / 982.5MiB","Name":"nginx","NetIO":"539kB / 606kB","PIDs":"2"}
```

> 方便程序解析。

### 示例 5：自定义只显示容器、CPU、内存

```bash
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

输出（示意）：

```text
CONTAINER         CPU %     MEM USAGE / LIMIT
fervent_panini    0.00%     56KiB / 15.57GiB
5acfcb1b4fd1     0.07%     32.86MiB / 15.57GiB
```

> 可用模板变量：`.Container` `.Name` `.ID` `.CPUPerc` `.MemUsage` `.NetIO` `.BlockIO` `.MemPerc` `.PIDs`。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `docker stats` | 实时看所有容器资源（**最常用**） |
| `docker stats 容器名` | 只盯某几个容器 |
| `docker stats --no-stream` | 脚本里取一次快照 |
| `docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"` | 精简列 |
| `docker stats -a` | 连停止的也列出来 |

## 六、RHEL 系与 Debian 系差异

- 命令两系一致；
- **存储驱动差异**：RHEL 系历史上用过 `devicemapper`，现代 Docker Engine 28.x 两系都默认 `overlay2`/`overlayfs`（containerd snapshotter），`BLOCK I/O` 列读数口径一致；
- **cgroup 版本**：两系新系统（RHEL 9+、Ubuntu 22.04+）都是 cgroup v2，内存统计口径同上；老系统 cgroup v1 的 cache 统计字段名不同，但 CLI 已帮你换算好，用户不用关心。

## 七、新手易错点

1. **不加 `--no-stream` 会一直刷新**：以为卡死了，其实是在流式刷，Ctrl+C 退出。
2. **`MEM USAGE` 不是裸 RSS**：它已经扣掉了 page cache，别和 `free` 命令直接比；想看原始 cgroup 内存用 `docker inspect`。
3. **没设内存上限时 LIMIT 是整机内存**：不写 `-m` 的容器，LIMIT 显示宿主机总内存，`MEM %` 分母很大。
4. **停止的容器没数据**：传了停止容器名也只显示 0B/0B，别误以为它在跑。
5. **`NET I/O` 是累计值不是速率**：它是从启动到现在的总量，要看速率得自己隔两次采样相减。
6. **PIDS 高不一定有问题**：多线程程序（Java、Go）PIDS 本来就大；只有 PIDS 暴涨伴随内存涨才要警惕内存泄漏/线程泄漏。
7. **这是只读命令**：不会动容器，放心看。

## 八、相关命令与文档

- 速查页：[Docker 命令速查](../docker-commands#进入与日志)
- 看容器详情：`docker inspect`（详解见 [ps-inspect](./ps-inspect)）
- 限制资源：`docker run --cpus/-m`（详解见 [run](./run)）
- 看日志：`docker logs`（详解见 [logs](./logs)）
- 原理与实战：[Docker 实战手册](../../guide/container-docker)
- 官方参考：https://docs.docker.com/reference/cli/docker/container/stats/
