---
category: 容器
difficulty: 中级
date: 2022-09-02
---

# Docker 存储驱动 overlay2 与磁盘打满（2022-09-02）

## 现象

节点磁盘告警使用率到 95%，但 `docker system df` 发现镜像/容器占用和实际不符。新建容器时报错：

```text
docker: Error response from daemon: write /var/lib/docker/overlay2/.../merged: no space left on device.
```

但 `df -h` 根分区明明还有空间——**inode 或镜像层堆积**的问题。

## 环境

| 组件 | 版本 |
|---|---|
| 操作系统 | Ubuntu 20.04.4 LTS（ext4 数据盘） |
| Docker | 20.10.18 |
| 存储驱动 | overlay2 |
| 数据目录 | `/var/lib/docker`（根分区） |

## 定位过程

### 1. 先看 Docker 视角的磁盘占用

```bash
docker system df
docker system df -v     # 详细版，看每个镜像/容器/卷占多少
```

输出：

```text
Images:   共 80 个，可 reclaim 12GB
Containers: 共 30 个，其中 12 个已 Exited
Local Volumes: 50 个
Build Cache: 8GB
```

发现堆积了大量**停止的容器**、**悬空镜像（dangling）** 和 **build cache**。

### 2. 看宿主机真实磁盘与 inode

```bash
df -h          # 块空间
df -i          # inode 空间（海量小文件会撑爆 inode）
du -sh /var/lib/docker/*
```

本次 `df -h` 显示根分区 95%，`df -i` inode 才用 30%——是真的块空间满。

### 3. 定位是 overlay2 哪一层占的

```bash
# overlay2 目录下找最大的层
du -sh /var/lib/docker/overlay2/* | sort -h | tail -10

# 看哪个容器在写大量可写层（容器内部产生大文件）
docker ps -q | xargs -I{} docker inspect --format \
  '{{.Name}} {{json .GraphDriver.Data}}' {} | head
```

发现某个跑了 30 天的日志容器，可写层里堆了 8GB 没轮转的日志（json-file 日志没配 max-size）。

### 4. 确认存储驱动是否正确

```bash
docker info | grep -i "Storage Driver"
# 应为 overlay2
```

```text
Storage Driver: overlay2
Backing Filesystem: extfs
```

> 如果这里显示 `devicemapper`（老版本默认），那本身就慢且费空间，应迁到 overlay2。现代内核（>=4.0）+ ext4/xfs 都该用 overlay2。

## 根因

| 层级 | 说明 |
|---|---|
| 直接原因 | 长期不清理，悬空镜像/停止容器/build cache 堆积 + 容器日志未轮转写爆可写层 |
| 存储原因 | overlay2 多层叠加，删除大文件后如果还有层引用，空间不释放 |
| 配置原因 | daemon.json 没配日志轮转，单个容器日志无限增长 |

## 解决步骤

### 止血

1. 立刻清理悬空资源（安全，不影响运行中容器）：

```bash
# 删已停止的容器、悬空镜像、无用网络、build cache
docker system prune -f
# 连没用的镜像一起删（小心：会删掉没在用的镜像，需要时重新 pull）
docker system prune -a -f --volumes   # 评估后再用

# 只清 build cache
docker builder prune -a -f
```

2. 那个写爆日志的容器，先 truncate 它的日志文件止血（不重启容器）：

```bash
# 找到容器日志文件
CID=$(docker ps -q --filter name=bad-logger)
LOG=$(docker inspect --format='{{.LogPath}}' $CID)
truncate -s 0 "$LOG"
```

### 根治

1. daemon.json 全局配日志轮转，避免单容器日志爆炸：

```json
{
  "log-driver": "json-file",
  "log-opts": { "max-size": "100m", "max-file": "3" }
}
```

> 改完需重启 docker，旧容器要重建才生效（log-opts 是容器创建时固定的）。

2. 数据目录迁到独立大盘（参考 [dockerd 启动失败](/cases/t-docker-daemon-fail.md) 里的 data-root 迁移）。

3. 定期清理任务（cron 每周跑一次 prune）：

```cron
0 3 * * 0 /usr/bin/docker system prune -f --filter "until=168h"
```

## 验证与预防

```bash
df -h /var/lib/docker        # 使用率回落
docker system df             # reclaimable 空间归零
```

- 监控：对 docker 数据盘使用率、inode 配告警（>80%）。
- 规范：所有容器必须配日志轮转；定期 prune；大文件写入用 volume 而非容器可写层。
- 选型：overlay2 是默认推荐，不要用 devicemapper/aufs。

## 相关

- 命令速查：[Docker 命令速查](/reference/docker-commands) ｜ [Linux 命令速查](/reference/linux-commands)
- 同组短文：[dockerd 启动失败](/cases/t-docker-daemon-fail) ｜ [容器网络不通](/cases/t-docker-network-bridge) ｜ [镜像拉取失败](/cases/t-docker-image-pull-fail)
