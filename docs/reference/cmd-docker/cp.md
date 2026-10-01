# docker cp 命令详解：容器和宿主机之间互相拷文件

> 本文是 [Docker 命令速查](../docker-commands#进入与日志) 中 `docker cp` 的从 0 到 1 详解。
> 目标：把 `docker cp --help` 里的每个选项讲清楚，多看几遍后，你在服务器上敲 `docker cp --help` 就知道该用哪个选项。
> 环境依据：Docker Engine 28.x（docker CLI 28.x），containerd 默认运行时；本沙箱未安装 docker，选项与输出据 [Docker 官方命令参考](https://docs.docker.com/reference/cli/docker/container/cp/) 核实，示例输出为示意。

## 一、命令是干什么的

`docker cp` 在**容器文件系统和宿主机文件系统之间**拷文件/目录：

- 从容器拷出来：`docker cp 容器:/路径 宿主机路径`；
- 拷进容器：`docker cp 宿主机路径 容器:/路径`。

它像一个"双向 SCP"，不用真的进容器，就能把容器里的配置/日志捞出来，或者把宿主机的文件喂进去。

> 类比：`docker cp` 就像 U 台拷贝——容器是另一台电脑，你用 U 盘把文件在两边倒腾。容器不管在跑还是停了，都能 cp。

## 二、命令语法

```bash
# 从容器拷到宿主机
docker cp [选项] 容器:SRC_PATH DEST_PATH
# 从宿主机拷到容器
docker cp [选项] SRC_PATH 容器:DEST_PATH
```

- 冒号 `:` 是"容器名和容器内路径"的分隔符；
- 容器路径相对容器根 `/`，开头的 `/` 写不写都行；
- 宿主机路径可以是绝对或相对（相对当前目录）。

## 三、选项全表（对照 `docker cp --help`）

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-a`，`--archive` | 保留所有 UID/GID 元信息 | 拷进去时想保持文件属主一致 |
| `-L`，`--follow-link` | 跟随源路径里的软链接 | 拷贝链接指向的真实文件而不是链接本身 |
| `-q`，`--quiet` | 不打进度 | 脚本里安静拷 |

## 四、由浅入深的典型示例

### 示例 1：把宿主机文件拷进容器

```bash
docker cp ./some_file web:/work
```

> 把当前目录的 `some_file` 拷到 `web` 容器的 `/work` 目录下。

### 示例 2：把容器里的日志拷到宿主机

```bash
docker cp web:/var/logs/ /tmp/app_logs
```

> 把容器里整个 `/var/logs` 目录拷到宿主机 `/tmp/app_logs`。注意末尾斜杠：拷目录内容。

### 示例 3：拷单个文件出来

```bash
docker cp web:/etc/nginx/nginx.conf ./nginx.conf.bak
```

> 把容器里 nginx 配置拉到当前目录备份，改完再拷回去。

### 示例 4：拷回去覆盖容器内文件

```bash
docker cp ./nginx.conf web:/etc/nginx/nginx.conf
```

> 改完配置拷回容器，然后 `docker exec web nginx -s reload` 生效。

### 示例 5：连权限属主一起拷（`-a`）

```bash
docker cp -a ./data web:/app/data
```

> 默认拷进容器的文件属主是 root；加 `-a` 保留源文件的 UID/GID。

### 示例 6：拷软链接指向的真实文件（`-L`）

```bash
docker cp -L web:/app/current ./current
```

> 如果 `/app/current` 是个软链接，不加 `-L` 拷出来的是个坏链接；加 `-L` 拷的是它指向的真实内容。

### 示例 7：流式拷贝（配合 tar）

```bash
docker cp web:/var/logs/app.log - | tar x -O | grep "ERROR"
```

> 把容器里的文件以 tar 流打到 stdout，管道里直接 grep，不落本地文件。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `docker cp 容器:/路径 ./本地` | 从容器拷出来 |
| `docker cp ./本地 容器:/路径` | 拷进容器 |
| `docker cp 容器:/dir ./本地dir` | 拷整个目录 |
| `docker cp -a 源 容器:目标` | 保留属主 |

## 六、RHEL 系与 Debian 系差异

- 命令两系一致；
- **SELinux**：RHEL 系下拷进容器的文件可能带宿主机 SELinux 标签，容器进程读不了；必要时进容器后 `chcon` 或重新挂载带 `:z`。Debian 系无此问题。

## 七、新手易错点

1. **冒号别写反**：`docker cp web:/etc ./bak` 是"容器→本地"；`docker cp ./bak web:/etc` 是"本地→容器"。写反了会报"没有那个文件"。
2. **容器路径开头的 `/` 可写可不写**：`web:etc/nginx.conf` 和 `web:/etc/nginx.conf` 等价。
3. **目标目录不存在不会自动建父目录**：`docker cp file web:/a/b/` 里 `/a/b` 不存在会报错，先 `docker exec` 建好。
4. **容器停了也能 cp**：`docker cp` 对 Exited 容器同样有效，这正是它用来抢救日志的场景。
5. **`/proc`、`/sys`、`/dev` 下的文件拷不出来**：这些是虚拟文件系统，要用 `docker exec ... tar` 绕（官方文档里有写法）。
6. **大目录拷贝较慢**：`docker cp` 本质是打 tar 再解开，拷几百 MB 以上的目录不如直接挂 volume/bind mount。
7. **cp 进去的文件要重启或 reload 才生效**：拷了新配置进去，进程不会自动重读，记得 reload/restart。

## 八、相关命令与文档

- 速查页：[Docker 命令速查](../docker-commands#进入与日志)
- 进容器执行命令：`docker exec`（详解见 [exec](./exec)）
- 数据持久化：`docker volume`（详解见 [volume](./volume)）
- 起容器：`docker run -v`（详解见 [run](./run)）
- 原理与实战：[Docker 实战手册](../../guide/container-docker)
- 官方参考：https://docs.docker.com/reference/cli/docker/container/cp/
