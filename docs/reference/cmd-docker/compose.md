# docker compose 命令详解：一条命令管起一整组容器

> 本文是 [Docker 命令速查](../docker-commands#docker-compose) 中 `docker compose` 的从 0 到 1 详解，本篇一次讲清 `up`、`down`、`ps`、`logs`、`build`、`restart`、`exec`、`run`、`config`、`pull`，以及 `compose.yaml` 的核心字段。
> 目标：把每个子命令的常用选项和 compose.yaml 写法讲清楚，多看几遍后，你在项目目录里敲 `docker compose <子命令> --help` 就知道该用哪个选项。
> 环境依据：**Docker Compose v2**（`docker compose` 插件形式，不是旧版 `docker-compose` 独立二进制），随 Docker Engine 28.x 一起安装；本沙箱未安装 docker，选项与配置据 [Docker 官方 compose 参考](https://docs.docker.com/reference/cli/docker/compose/) 核实，示例输出为示意。

## 一、命令是干什么的

实际项目一般不止一个容器：Web 应用 + 数据库 + 缓存 + 反向代理。手动一个个 `docker run` 又长又容易错。Compose 让你把这一组容器的定义写在一个 `compose.yaml` 文件里，然后：

- `docker compose up -d`：照着 yaml 把所有服务一次性拉起来；
- `docker compose down`：把这一组全停掉删掉；
- `docker compose logs`：同时看所有服务的日志；
- `docker compose exec web sh`：进到某个服务的容器里；
- 等等。

> 类比：`docker run` 是一个一个手动装机；`docker compose` 是拿一张"装机清单"（compose.yaml），一条命令把一整个机房的机器都开好。

> **重要**：2026 年的写法是 `docker compose`（中间空格，插件子命令），不是老的 `docker-compose`（中间横杠，独立 Python 脚本）。两版 yaml 大部分兼容，但老命令已被官方废弃。

## 二、命令语法

```bash
docker compose [-f compose.yaml] [-p 项目名] <子命令> [选项] [服务名...]
```

- `-f`：指定 compose 文件路径（默认在当前目录找 `compose.yaml` 或 `docker-compose.yaml`）；
- `-p`：项目名（默认用目录名）；
- 后面跟子命令和可选的服务名（只对某几个服务操作）。

## 三、compose.yaml 核心字段

一个最小可用的 compose.yaml：

```yaml
services:
  web:
    image: nginx:alpine
    ports:
      - "8080:80"
    volumes:
      - ./html:/usr/share/nginx/html
    environment:
      - NGINX_PORT=80
    depends_on:
      - db

  db:
    image: mysql:8.4
    environment:
      MYSQL_ROOT_PASSWORD: example
    volumes:
      - db-data:/var/lib/mysql

volumes:
  db-data:
```

逐字段解释：

| 字段 | 含义 |
|---|---|
| `services:` | 下面每个顶级 key 是一个服务（一个容器） |
| `image:` | 用哪个镜像；和 `build:` 二选一或都写 |
| `build:` | 不写 image 时，从这个目录的 Dockerfile 构建 |
| `ports:` | 端口映射，`"宿主机:容器"` |
| `volumes:` | 挂载；`./路径:/容器路径` 是 bind，`名字:/容器路径` 是命名卷 |
| `environment:` | 环境变量，列表或字典写法都行 |
| `depends_on:` | 先起依赖的服务再起我（只保证启动顺序，不等它"就绪"） |
| `volumes:`（顶级） | 声明命名卷，供上面 services 引用 |

## 四、常用子命令

### 1. docker compose up（创建并启动）

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-d`，`--detach` | 后台跑，不占当前终端 | 日常起服务（极常用） |
| `--build` | 启动前先重新构建镜像 | 改了代码后 |
| `--force-recreate` | 不管配置变没变都重建容器 | 怀疑容器状态脏了 |
| `--no-deps` | 不启动依赖的服务 | 单独重启某一个 |
| `--scale 服务=N` | 把某服务扩到 N 个实例 | 简易水平扩容 |
| `--wait` | 等服务都 healthy 再返回 | CI 里等就绪 |
| `--remove-orphans` | 清掉 yaml 里没定义的"孤儿"容器 | 清理残留 |

### 2. docker compose down（停止并删除）

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-v`，`--volumes` | 连命名卷和匿名卷一起删 | **会删数据库数据，慎加** |
| `--rmi local\|all` | 同时删镜像 | 彻底清理 |
| `--remove-orphans` | 删孤儿容器 | 配合清理 |
| `-t`，`--timeout` | 停止超时秒数 | 优雅关闭需要更久 |

> 默认 `down` 删容器和网络，**保留命名卷**（保护数据）；加 `-v` 才删卷。

### 3. 其它子命令速查

| 子命令 | 作用 |
|---|---|
| `docker compose ps` | 看本项目起了哪些容器 |
| `docker compose logs [-f] [服务]` | 看日志，`-f` 跟踪 |
| `docker compose build` | 只构建服务镜像（不启动） |
| `docker compose restart [服务]` | 重启服务 |
| `docker compose stop` / `start` | 停止 / 启动（不删容器） |
| `docker compose exec 服务 命令` | 进运行中的服务容器跑命令 |
| `docker compose run 服务 命令` | 起一个一次性临时容器跑命令 |
| `docker compose config` | 校验并打印合并后的最终 yaml |
| `docker compose pull` | 拉所有服务的镜像 |
| `docker compose top` | 看各服务容器里的进程 |

## 五、由浅入深的典型示例

### 示例 1：在项目目录一键起所有服务

```bash
docker compose up -d
```

输出（示意）：

```text
[+] Running 4/4
 ✔ Network myapp_default    Created
 ✔ Container myapp-db-1      Started
 ✔ Container myapp-web-1     Started
```

> `-d` 后台跑。不加 `-d` 会前台占着终端，Ctrl+C 会停掉所有服务。

### 示例 2：改了代码后重建并启动

```bash
docker compose up -d --build
```

> `--build` 会先重新 build 有 `build:` 段的服务，再用新镜像起容器。

### 示例 3：只看某服务日志并跟踪

```bash
docker compose logs -f web
```

> 不加服务名就是所有服务混在一起打，每行前面带服务名前缀。

### 示例 4：进 web 服务的容器

```bash
docker compose exec web sh
```

> 等价于 `docker exec -it <web容器> sh`，但不用记容器名。

### 示例 5：跑一个一次性命令（`run`）

```bash
docker compose run --rm web python manage.py migrate
```

> 起一个新的临时容器跑迁移命令，跑完 `--rm` 自动删掉。和 `exec` 的区别：`exec` 是进**正在跑**的容器，`run` 是**新起一个**。

### 示例 6：校验 yaml 写得对不对

```bash
docker compose config
```

> 会把 `-f` 叠加、环境变量替换后的最终 yaml 打出来，写错字段能立刻发现。

### 示例 7：停掉并删除（保留数据卷）

```bash
docker compose down
```

> 容器和网络删了，`db-data` 卷保留，下次 `up` 数据还在。

### 示例 8：彻底清理（连数据库数据一起删）

```bash
docker compose down -v
```

> **危险**：`-v` 会把 `db-data` 命名卷也删掉，数据库没了。只在你确定不要数据时用。

### 示例 9：只重启某一个服务

```bash
docker compose restart web
```

> 不动 db，只重启 web。

### 示例 10：拉最新镜像

```bash
docker compose pull
```

> 把 yaml 里所有 service 的镜像重新拉一遍。

## 六、高频组合速记

| 命令 | 用途 |
|---|---|
| `docker compose up -d` | 后台起全套服务（**最常用**） |
| `docker compose up -d --build` | 改完代码重建并起 |
| `docker compose down` | 停删容器网络（留数据） |
| `docker compose logs -f` | 跟全部日志 |
| `docker compose ps` | 看项目容器状态 |
| `docker compose exec web sh` | 进 web 容器 |
| `docker compose restart web` | 重启单个服务 |
| `docker compose config` | 校验 yaml |

## 七、RHEL 系与 Debian 系差异

- 命令两系一致；
- **安装**：两系装 `docker-ce` 都会带 `docker-compose-plugin` 包，装完直接 `docker compose` 可用；老教程里 `apt install docker-compose` 装的是 v1，已废弃；
- **yml/yaml 格式**：两系都认 `compose.yaml`（新）和 `docker-compose.yaml`（老名字）；
- **路径挂载**：RHEL 系 SELinux 下 bind mount 可能要加 `:z`，Debian 系不用（见 [volume](./volume) 差异段）。

## 八、新手易错点

1. **是 `docker compose`（空格）不是 `docker-compose`（横杠）**：2026 年 v2 是插件；老横杠命令是 v1，已停止维护。
2. **`depends_on` 只保证启动顺序，不等就绪**：db 容器"启动了"不代表 MySQL 已经能接受连接。Web 刚起来连不上 db 是常见坑，要加健康检查或在代码里重试。
3. **`down -v` 删数据库数据**：和 `docker system prune --volumes` 一样危险，敲之前想清楚。
4. **`up` 不加 `-d` 会前台占终端**：想后台跑一定要 `-d`。
5. **改了 yaml 里的端口/环境变量要 `up` 才生效**：Compose 检测到配置变化会自动重建容器；没重建就 `docker compose up -d` 一下。
6. **`docker compose run` vs `exec`**：`run` 起新临时容器，`exec` 进已有容器。跑迁移用 `run`，进排障用 `exec`。
7. **项目名默认是目录名**：换个目录放同一份 yaml 会起另一套容器，别以为串了；用 `-p` 显式指定项目名。
8. **bind mount 的相对路径相对 compose 文件位置**：`./html` 是相对 compose.yaml 所在目录，不是你当前 shell 的目录。

## 九、相关命令与文档

- 速查页：[Docker 命令速查](../docker-commands#docker-compose)
- 单容器起停：`docker run/stop/rm`（详解见 [run](./run) / [lifecycle](./lifecycle)）
- 进容器：`docker exec`（详解见 [exec](./exec)）
- 看日志：`docker logs`（详解见 [logs](./logs)）
- 数据卷：`docker volume`（详解见 [volume](./volume)）
- 一键清理：`docker system prune`（详解见 [system-prune](./system-prune)）
- 原理与实战：[Docker 实战手册](../../guide/container-docker)
- 官方参考：https://docs.docker.com/reference/cli/docker/compose/
