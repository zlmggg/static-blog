---
category: 容器
difficulty: 中级
date: 2021-05-17
---

# dockerd 启动失败排查（2021-05-17）

## 现象

改完 `/etc/docker/daemon.json` 后重启 Docker，`systemctl restart docker` 一直卡住失败：

```text
Job for docker.service failed because the control process exited with error code.
See "systemctl status docker.service" and "journalctl -xe" for details.
```

`systemctl status docker` 显示：

```text
docker.service: Start request repeated too quickly.
Failed with result 'exit-code'.
```

## 环境

| 组件 | 版本 |
|---|---|
| 操作系统 | CentOS 7.9（内核 3.10.0-1160） |
| Docker | 20.10.6（CE） |
| 运行时 | containerd 1.4.4 |
| 改动 | 刚把数据根目录 `data-root` 从 `/var/lib/docker` 迁到 `/data/docker` |

## 定位过程

### 1. 先看 systemd 到底报什么

```bash
systemctl status docker.service --no-pager
journalctl -u docker.service --no-pager -n 80
```

### 2. 前台手动跑 dockerd，直接看错误

systemd 吞掉的错误，前台跑会直接打出来：

```bash
dockerd
```

本次输出：

```text
unable to configure the Docker daemon with file /etc/docker/daemon.json:
  invalid character ':' after top-level value
```

是 **daemon.json 语法错误**（多了个逗号/漏了括号）。先校验 JSON：

```bash
python3 -m json.tool /etc/docker/daemon.json
# 会指出具体哪一行哪个字符出错
```

### 3. 常见启动失败原因对照表

排障时按这个表逐个过：

| 现象（dockerd 前台报错关键词） | 原因 | 解法 |
|---|---|---|
| `invalid character` | daemon.json 语法错 | `json.tool` 校验，修逗号/括号 |
| `failed to start daemon: error creating overlay` | 存储驱动不支持 | 检查内核/`storage-driver` 配置 |
| `starting containerd` / `connection timed out` | containerd 没起来 | `systemctl status containerd` |
| `listen tcp ...: bind: address already in use` | 2375 端口被占 | `ss -tlnp | grep 2375` |
| `mkdir /data/docker: permission denied` | 数据盘目录权限 | `chmod`/挂载点没挂上 |
| `graph driver` 迁移后起不来 | 旧数据与新 driver 不兼容 | 不要混用，先清空或迁移数据 |

### 4. 本次实际问题：数据根目录迁移

除了 JSON 语法，本次迁移 `data-root` 还踩了坑——新盘 `/data` 没挂好：

```bash
# 确认新目录真的在目标盘上、且属主正确
df -h /data/docker
ls -ld /data/docker
# 如果 df 显示 /data 还在根分区，说明盘没 mount 上
mount | grep /data
```

## 根因

| 层级 | 说明 |
|---|---|
| 直接原因 | 改 daemon.json 时手误留下非法 JSON 字符，dockerd 解析配置失败直接退出 |
| 叠加因素 | 数据根目录迁移目标盘未正确挂载 |

## 解决步骤

### 止血

1. 先恢复一份"已知能用"的 daemon.json，让 docker 先起来：

```bash
# 备份坏配置
mv /etc/docker/daemon.json /etc/docker/daemon.json.bad
# 写最小可用配置
cat > /etc/docker/daemon.json <<'EOF'
{
  "log-driver": "json-file",
  "log-opts": { "max-size": "100m", "max-file": "3" }
}
EOF
systemctl daemon-reload
systemctl start docker
```

2. 确认 docker 起来后，再逐步加回需要的配置项，每次改完 `systemctl restart docker` 验证。

### 根治

1. 正确迁移数据根目录（这次要做对）：

```bash
# 1. 停 docker
systemctl stop docker

# 2. 确保新盘挂载
mkfs.xfs /dev/sdb          # 首次
mount /dev/sdb /data

# 3. 迁移旧数据
rsync -aX /var/lib/docker/ /data/docker/

# 4. 改配置
cat > /etc/docker/daemon.json <<'EOF'
{
  "data-root": "/data/docker",
  "storage-driver": "overlay2"
}
EOF

# 5. 重新加载并启动
systemctl daemon-reload
systemctl start docker

# 6. 验证数据根目录已生效
docker info | grep "Docker Root Dir"
# 应显示 /data/docker
```

2. 养成习惯：改 daemon.json 后先 `python3 -m json.tool` 校验再重启。

## 验证与预防

```bash
docker info                    # 无 Warning，Docker Root Dir 正确
docker run --rm hello-world    # 能正常跑容器
```

- 规范：改配置前备份；JSON 先校验；迁移数据目录先停服务再 rsync。
- 监控：docker 存活监控，systemd 配 `restart=on-failure`。

## 相关

- 命令速查：[Docker 命令速查](/reference/docker-commands) ｜ [Linux 命令速查](/reference/linux-commands)
- 同组短文：[存储驱动 overlay2 问题](/cases/t-docker-storage-driver) ｜ [容器网络不通](/cases/t-docker-network-bridge) ｜ [镜像拉取失败](/cases/t-docker-image-pull-fail)
