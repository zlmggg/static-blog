# docker network 详解：容器网络 ls / create / connect / disconnect / inspect / rm

> 本文是 [Docker 命令速查](../docker-commands#网络) 中 `docker network` 各子命令的从 0 到 1 详解，本篇一次讲清 `ls`、`create`、`connect`、`disconnect`、`inspect`、`rm`。
> 目标：把每个子命令的选项讲清楚，多看几遍后，你在服务器上敲 `docker network <子命令> --help` 就知道该用哪个选项。
> 环境依据：Docker Engine 28.x（docker CLI 28.x），默认 bridge 网络为 `docker0`，containerd 默认运行时；本沙箱未安装 docker，选项与输出据 [Docker 官方命令参考](https://docs.docker.com/reference/cli/docker/network/ls/) 核实，示例输出为示意。

## 一、命令是干什么的

容器要联网，就得接在某个"网络"上。`docker network` 这组命令管理这些虚拟网络：

- `docker network ls`：列出 Docker 知道的所有网络；
- `docker network create`：新建一个网络（最常用的是自定义 bridge）；
- `docker network connect`：把一个**已经在跑**的容器接入某个网络；
- `docker network disconnect`：把容器从某网络拔掉；
- `docker network inspect`：看某网络的详情（网段、网关、接了哪些容器）；
- `docker network rm`：删除网络（上面不能有容器）。

> 类比：网络是小区，容器是住户。`ls` 是看有几个小区；`create` 是新开一个小区；`connect/disconnect` 是让住户搬入/搬出；`inspect` 是查小区规划图；`rm` 是拆小区。

### Docker 的四种内置网络模式

| 驱动 | 含义 | 什么时候用 |
|---|---|---|
| `bridge` | 默认桥接网络，容器通过 veth 接 docker0/NAT 出网 | 单机多容器互通，最常用 |
| `host` | 容器直接共用宿主机网络栈，**没有网络隔离**，端口直接用宿主机的 | 性能敏感、不需要端口映射时 |
| `none` | 容器完全没有网卡 | 跑不需要网络的离线任务 |
| `container` | 容器共享**另一个容器**的网络栈 | 两个进程必须用 localhost 互通时 |

> 关键区别：**默认 bridge（docker0）没有容器名 DNS**，容器之间只能靠 IP 互访；**用户自建的 bridge 网络自带 DNS**，容器之间可以直接用容器名当域名访问。这就是为什么生产都自己 `docker network create`。

## 二、命令语法

```bash
docker network ls       [选项]
docker network create    [选项] 网络名
docker network connect   [选项] 网络 容器
docker network disconnect [选项] 网络 容器
docker network inspect   [选项] 网络 [网络...]
docker network rm        网络 [网络...]
```

## 三、选项全表

### 1. docker network ls

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-f`，`--filter` | 按条件过滤 | 如 `driver=bridge`、`type=custom` |
| `--format` | Go 模板自定义列 | 只要名字和驱动 |
| `-q`，`--quiet` | 只输出网络 ID | 脚本批量删 |
| `--no-trunc` | 不截断 ID | 看完整 ID |

常用过滤器：`driver=bridge`、`name=xxx`、`type=builtin/custom`、`scope=local/swarm`、`label=...`。

### 2. docker network create

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-d`，`--driver` | 网络驱动，默认 `bridge` | 单机用 bridge，跨机 overlay |
| `--subnet` | 指定网段 CIDR | 如 `172.20.0.0/16` |
| `--gateway` | 指定网关 IP | 不指定 Docker 自动选 |
| `--ip-range` | 从这个子段里分配容器 IP | 自定义 IP 池 |
| `--internal` | 隔离网络，禁止出外网 | 纯内部服务 |
| `--ipv6` | 启用 IPv6 | 需要 v6 时 |
| `--attachable` | 允许手动容器接入 overlay | Swarm 场景 |
| `--label` | 打标签 | 批量管理 |
| `-o`，`--opt` | 驱动专属参数 | 如 MTU、网桥名 |

### 3. docker network connect

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `--alias` | 在该网络里给容器起别名 | 用别的名字解析到它 |
| `--ip` / `--ip6` | 指定固定 IP | 想要固定地址 |
| `--link` | 老版链接到别的容器 | 新项目用 DNS 替代 |

### 4. docker network disconnect

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-f`，`--force` | 强制断开 | 容器不配合时 |

### 5. docker network inspect

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-f`，`--format` | Go 模板抠字段 | 只要某段信息 |
| `-v`，`--verbose` | 详细输出（含容器信息） | 诊断时 |

### 6. docker network rm

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-f`，`--force` | 网络不存在也不报错 | 脚本里容错 |

## 四、由浅入深的典型示例

### 示例 1：列出所有网络

```bash
docker network ls
```

输出（示意，据 Docker 官方文档）：

```text
NETWORK ID     NAME      DRIVER    SCOPE
7fca4eb8c647  bridge    bridge    local
9f904ee27bf5  none      null      local
cf03ee007fb4  host      host      local
```

> 装好 Docker 默认就有 `bridge`、`none`、`host` 三个内置网络，删不掉。

### 示例 2：自建一个自定义 bridge 网络

```bash
docker network create mynet
```

输出（示意）：

```text
cb79f45948d87e389e12013fa4d969689ed2c3316985dd832a43aaec9a0fe394
```

> 不写 `-d` 默认就是 bridge。之后 `docker run --network=mynet` 起的容器都接进这个网络。

### 示例 3：自定义网段和网关

```bash
docker network create \
  --driver bridge \
  --subnet 172.28.0.0/16 \
  --gateway 172.28.0.1 \
  mybr0
```

> 不指定 subnet 时 Docker 自动挑一个不冲突的网段；想固定地址段就手动指定。

### 示例 4：起容器时就接进网络（`--network`）

```bash
docker run -d --name web --network mynet nginx:alpine
docker run --rm --network mynet busybox:latest ping -c 2 web
```

输出（示意）：

```text
PING web (172.18.0.2): 56 data bytes
64 bytes from 172.18.0.2: seq=0 ttl=64 time=0.073 ms
```

> 注意：这里直接用容器名 `web` 当主机名就 ping 通了——这就是自定义 bridge 的 DNS 魔法，默认 docker0 做不到。

### 示例 5：把已在跑的容器接进网络（`connect`）

```bash
docker network connect mynet web
```

> 容器启动时没接 mynet，后来想让它加入，用 connect；不用重启容器。

### 示例 6：接入时起个别名、指定固定 IP

```bash
docker network connect --alias db --ip 172.18.0.10 mynet web
```

> 同网络里其他容器可以用 `db` 这个名字访问它。

### 示例 7：把容器从网络拔掉（`disconnect`）

```bash
docker network disconnect mynet web
```

> 容器必须在运行才能 disconnect。

### 示例 8：看网络详情（`inspect`）

```bash
docker network inspect mynet
```

输出（示意，JSON）：

```json
[
  {
    "Name": "mynet",
    "Driver": "bridge",
    "IPAM": { "Config": [{ "Subnet": "172.18.0.0/16" }] },
    "Containers": {
      "4bed76d3ad42...": { "Name": "web", "IPv4Address": "172.18.0.2/16" }
    }
  }
]
```

> 重点看 `Containers` 段：这个网络里现在接了哪些容器、各自什么 IP。

### 示例 9：删除网络

```bash
docker network rm mynet
```

> 网络上还有容器时删不掉，得先 disconnect 或停删容器。

### 示例 10：批量删所有自定义网络

```bash
docker network rm $(docker network ls --filter type=custom -q)
```

> `type=custom` 只列自建网络，不动内置的 bridge/host/none。

## 五、`-p` 端口映射的原理（重点）

新手问得最多：`docker run -p 8080:80` 到底做了什么？

1. Docker 在宿主机上起一个 `docker-proxy` 进程监听 `0.0.0.0:8080`；
2. 同时在宿主机 iptables/nftables 里加一条 DNAT 规则：访问宿主机 8080 的包，转发到容器 80 端口；
3. 容器在 bridge 网络里有个内部 IP（如 172.18.0.2），容器间互访走 docker0 网桥，**不经过 -p**。

所以：

- `-p` 只解决"宿主机外部怎么访问容器"；
- 容器之间互相访问，直接用 `容器名:容器端口`（同自定义网络），**不需要 -p**；
- `--network=host` 时容器和宿主机共享网络栈，`-p` 无效（容器直接绑宿主机端口）。

## 六、高频组合速记

| 命令 | 用途 |
|---|---|
| `docker network ls` | 看有哪些网络 |
| `docker network create mynet` | 建自定义 bridge |
| `docker run --network mynet ...` | 起容器就接进去 |
| `docker network connect mynet 容器` | 运行中容器加入网络 |
| `docker network disconnect mynet 容器` | 拔出 |
| `docker network inspect mynet` | 看网段和已接容器 |
| `docker network rm mynet` | 删网络 |

## 七、RHEL 系与 Debian 系差异

- 命令两系一致；
- **防火墙**：RHEL 系 firewalld 默认可能拦 Docker 映射端口，需要 `firewall-cmd` 放行或让 Docker 管理 NAT 规则；Debian 系默认 ufw 较少干扰；
- **iptables vs nftables**：RHEL 9+、新 Debian 默认 nftables，Docker 28 已支持，规则写入方式不同但用户无感知；
- **`--internal` 网络**：两系行为一致，都是断开外网 only 内网互通。

## 八、新手易错点

1. **默认 bridge 没有 DNS**：在默认 `bridge` 网络里，容器间只能用 IP 互访，用容器名解析不通。要名字互通就自建网络。
2. **网络上有容器时删不掉**：`docker network rm` 报错就先 `docker network disconnect` 或停容器。
3. **一个容器能接多个网络**：容器可以同时挂在 bridge 和别的网络上，相当于双网卡。
4. **`--network=host` 下 `-p` 无效**：容器直接用宿主机端口，再写 `-p 8080:80` 没意义甚至报错。
5. **`none` 网络的容器上不了网**：不是没配网关，是真的没网卡，别当 bug 查。
6. **overlay 网络要 Swarm**：跨主机的 overlay 网络得先 `docker swarm init`，单机 `create -d overlay` 建了也跨不了机。
7. **IP 会变**：容器重启后默认 DHCP 可能换 IP，别在代码里写死容器 IP；要固定 IP 用 `--ip` 或自定义网络别名。

## 九、相关命令与文档

- 速查页：[Docker 命令速查](../docker-commands#网络)
- 起容器接网络：`docker run --network`（详解见 [run](./run)）
- 看容器 IP：`docker inspect`（详解见 [ps-inspect](./ps-inspect)）
- 数据持久化：`docker volume`（详解见 [volume](./volume)）
- 原理与实战：[Docker 实战手册](../../guide/container-docker)
- 官方参考：https://docs.docker.com/reference/cli/docker/network/ls/
