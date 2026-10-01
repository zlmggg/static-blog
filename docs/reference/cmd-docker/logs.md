# docker logs 命令详解：查看容器里程序打印的日志

> 本文是 [Docker 命令速查](../docker-commands#进入与日志) 中 `docker logs` 的从 0 到 1 详解。
> 目标：把 `docker logs --help` 里的每个选项讲清楚，多看几遍后，你在服务器上敲 `docker logs --help` 就知道该用哪个选项。
> 环境依据：Docker Engine 28.x（docker CLI 28.x），日志驱动默认 `json-file`，容器运行时默认为 containerd；本沙箱未安装 docker，选项与输出据 [Docker 官方命令参考](https://docs.docker.com/reference/cli/docker/container/logs/) 核实，示例输出为示意。

## 一、命令是干什么的

`docker logs` 用来取某个容器往 **stdout/stderr** 打出来的日志。容器里的程序一般不写本地文件，而是直接往标准输出打印；Docker 把这些输出收集起来，`docker logs` 就是把它们翻出来给你看。

- 不带选项：把容器从启动到现在的日志全打出来；
- `-f`：像 `tail -f` 一样**跟着实时刷**；
- `--tail`：只看最后多少行；
- `--since/--until`：按时间范围截取。

> 类比：`docker logs` 就像在服务器上对一个进程做 `tail -f /var/log/xxx.log`，只不过日志文件由 Docker 替你管了，不用你去找路径。

## 二、命令语法

```bash
docker logs [选项] 容器
```

- `[选项]`：控制看多少、跟不跟、带不带时间戳；
- `容器`：必填，容器名或 ID；一次只能看一个容器。

## 三、选项全表（对照 `docker logs --help`）

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-f`，`--follow` | 实时跟踪新日志 | 服务出问题边跑边看（极常用） |
| `-n`，`--tail` | 只看最后 N 行（默认 `all`） | 日志几万行，不想全翻时 |
| `-t`，`--timestamps` | 每行前面打印 RFC3339 时间戳 | 想知道每条日志几点打的 |
| `--since` | 只看某个时间点之后的日志 | 如 `30m`（30 分钟前）或 `2026-09-30T10:00:00` |
| `--until` | 只看某个时间点之前的日志 | 配合 `--since` 圈定一个时间窗 |
| `--details` | 显示日志附带的额外属性（环境变量、标签等） | 排障时想看 log-opt 注入的细节 |

> 说明：`docker logs` 只能拿到容器写到 stdout/stderr 的内容。如果程序自己写日志到容器内文件（如 `/var/log/nginx/access.log`），`docker logs` 是看不到的，得 `docker exec` 进去读文件。

## 四、由浅入深的典型示例

### 示例 1：一次性看全部历史日志

```bash
docker logs web
```

输出（示意）：

```text
/docker-entrypoint.sh: /docker-entrypoint.d/ is not empty, will attempt to perform configuration
/docker-entrypoint.sh: Looking for shell scripts in /docker-entrypoint.d/
/docker-entrypoint.sh: Launching /docker-entrypoint.d/10-listen-on-ipv6-by-default.sh
...
2026/09/30 10:00:00 [notice] 1#1: start worker processes
```

> 日志多的时候会刷屏，配合 `--tail` 或 `grep` 更好用。

### 示例 2：实时跟踪日志（`-f`，最常用）

```bash
docker logs -f web
```

> 会停在那不停刷新日志，按 `Ctrl+C` 退出（注意：Ctrl+C 只是退出日志跟踪，**不会停容器**）。

### 示例 3：只看最后 100 行再跟踪（`--tail`）

```bash
docker logs -f --tail 100 web
```

> 先倒回最后 100 行，再从那里开始实时刷。线上排障基本就是这条。

### 示例 4：每行带时间戳（`-t`）

```bash
docker logs -t web
```

输出（示意）：

```text
2026-09-30T10:00:00.123456789Z [notice] 1#1: start worker processes
2026-09-30T10:00:01.987654321Z 127.0.0.1 - - [30/Sep/2026:10:00:01 +0000] "GET / HTTP/1.1" 200 612
```

> 时间戳是 RFC3339Nano 格式，纳秒位会补零对齐。

### 示例 5：只看最近 30 分钟的日志（`--since`）

```bash
docker logs --since 30m web
```

> `--since` 支持相对时长（`30m`、`2h`、`1h30m`），也支持 RFC3339 时间点 `2026-09-30T09:00:00`。

### 示例 6：圈定时间窗（`--since` + `--until`）

```bash
docker logs --since 2026-09-30T09:00:00 --until 2026-09-30T10:00:00 web
```

输出（示意，据官方文档）：

```text
Tue 30 Sep 2026 09:00:01 UTC
Tue 30 Sep 2026 09:00:02 UTC
...
Tue 30 Sep 2026 09:59:58 UTC
```

> 常用于复盘某个时间段发生的故障。`--since` 可以和 `-f`、`--tail` 组合。

### 示例 7：只看错误日志（管道 grep）

```bash
docker logs web 2>&1 | grep -i error
```

> `docker logs` 的 stdout 和 stderr 可能分开，`2>&1` 合并后再 grep。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `docker logs -f 容器` | 实时跟日志（**最常用**） |
| `docker logs -f --tail 100 容器` | 看最后 100 行并跟踪 |
| `docker logs --tail 50 容器` | 只看最后 50 行 |
| `docker logs -t 容器` | 带时间戳 |
| `docker logs --since 30m 容器` | 最近 30 分钟 |
| `docker logs 容器 \| grep error` | 过滤错误 |

## 六、RHEL 系与 Debian 系差异

- 命令两系一致；
- **日志驱动**：默认都是 `json-file`，日志存在 `/var/lib/docker/containers/<容器ID>/<容器ID>-json.log`；RHEL 系若用 `journald` 日志驱动，日志会进 systemd journal，可用 `journalctl -u docker` 看；
- **日志切割**：json-file 默认**不自动切割**，跑久了单个日志文件能涨到几十 GB。生产环境建议在 `/etc/docker/daemon.json` 配 `log-opts`（`max-size`、`max-file`），两系配置方式相同。

## 七、新手易错点

1. **`docker logs` 看不到程序写到容器内文件的日志**：它只收 stdout/stderr。程序若写 `/var/log/app.log`，得 `docker exec` 进去读。
2. **`-f` 后按 Ctrl+C 不停容器**：只是退出跟踪。想停容器用 `docker stop`。
3. **日志文件会无限涨**：不配置 `max-size`，磁盘可能被日志吃光（这是 Docker 宿主机常见故障）。
4. **`--tail` 传负数或非整数会被当成 all**：别写 `--tail -100`，Docker 不接受。
5. **停止的容器也能看日志**：`docker logs` 对 Exited 状态的容器照样有效，这正好用来复盘它为什么挂的。
6. **时间戳时区**：不带 `Z` 或时区偏移时用客户端本地时区；跨时区排障要写全 RFC3339 带时区。
7. **多容器别同时 `-f`**：看一组服务的日志用 `docker compose logs -f`（见 [compose](./compose)），它会自动加服务名前缀。

## 八、相关命令与文档

- 速查页：[Docker 命令速查](../docker-commands#进入与日志)
- 进容器读文件日志：`docker exec`（详解见 [exec](./exec)）
- 看容器资源占用：`docker stats`（详解见 [stats](./stats)）
- 看容器详情：`docker inspect`（详解见 [ps-inspect](./ps-inspect)）
- 多服务日志：`docker compose logs`（详解见 [compose](./compose)）
- 原理与实战：[Docker 实战手册](../../guide/container-docker)
- 官方参考：https://docs.docker.com/reference/cli/docker/container/logs/
