---
category: 容器
difficulty: 初级
date: 2026-09-25
description: "Docker 报 No swap limit support 时，说明内核未开启 cgroup swap accounting，导致容器 swap 限制不生效。本文给出 GRUB 参数、重启验证、cgroup v2 差异与常见坑。"
---
# Docker 提示 “No swap limit support” 怎么处理

## 现象

装好 Docker 后执行 `docker info`，末尾出现：

```bash
$ docker info
...
WARNING: No swap limit support
```

这不是 Docker 起不来，而是内核没有开启 **cgroup swap accounting**，导致 Docker 无法对容器做 swap 限制。容器照常能跑，但 `--memory-swap` 这类参数不会按预期生效。

## 环境

- 系统：Ubuntu 22.04（cgroup v1）
- Docker：24.x
- 内核启动参数里没有 `swapaccount=1`

> cgroup v2 环境下内存和 swap 由 `memory.swap.max` 控制，通常不会再出现这条警告；先确认自己用的是 v1 还是 v2。

## 根因

Docker 限制容器内存依赖 cgroup。cgroup v1 的 memory 子系统要额外打开 swap accounting，内核启动参数必须带：

```text
swapaccount=1
```

如果 `/proc/cmdline` 里没有这个参数，Docker 只能限制物理内存，不能准确统计/限制 swap，于是给出 `No swap limit support` 警告。

先确认：

```bash
cat /proc/cmdline | tr ' ' '\n' | grep swapaccount
# 没有输出 = 没开
```

再确认 cgroup 版本：

```bash
stat -fc %T /sys/fs/cgroup
# cgroup2fs = v2；tmpfs = v1
```

## 解决步骤

### 1. 修改 GRUB 启动参数

Debian/Ubuntu 编辑 `/etc/default/grub`：

```bash
sudo cp /etc/default/grub /etc/default/grub.bak
sudo vim /etc/default/grub
```

找到 `GRUB_CMDLINE_LINUX`，把 `swapaccount=1` 追加进去（保留原有参数）：

```bash
GRUB_CMDLINE_LINUX="net.ifnames=0 biosdevname=0 swapaccount=1"
```

如果原来这一行是空的，就直接写：

```bash
GRUB_CMDLINE_LINUX="swapaccount=1"
```

不要改 `GRUB_CMDLINE_LINUX_DEFAULT` 里的 `quiet splash` 之类，两个变量会一起进内核命令行；把 swapaccount 放 `GRUB_CMDLINE_LINUX` 更清晰。

### 2. 重新生成 GRUB 配置

```bash
# Debian / Ubuntu
sudo update-grub

# RHEL / Rocky / CentOS
sudo grub2-mkconfig -o /boot/grub2/grub.cfg
# UEFI 系统可能是：
sudo grub2-mkconfig -o /boot/efi/EFI/rocky/grub.cfg
```

RHEL 系先用 `grub2-editenv list` 或 `cat /boot/grub2/grub.cfg | grep swapaccount` 确认新参数写进去了。

### 3. 重启并验证

```bash
sudo reboot
```

重启后：

```bash
cat /proc/cmdline | tr ' ' '\n' | grep swapaccount
# swapaccount=1

docker info | grep -i swap
# 不再出现 WARNING: No swap limit support
```

### 4. 验证 swap 限制是否生效

```bash
docker run --rm -it --memory=256m --memory-swap=512m alpine sh
```

进入容器后查看 cgroup 限制（cgroup v1）：

```bash
cat /sys/fs/cgroup/memory/memory.limit_in_bytes
cat /sys/fs/cgroup/memory/memory.memsw.limit_in_bytes
```

`memory.memsw.limit_in_bytes` 能读到值，说明 swap accounting 已经生效。

## 验证清单

- [ ] `/proc/cmdline` 含 `swapaccount=1`
- [ ] `docker info` 不再报 `No swap limit support`
- [ ] `docker run --memory --memory-swap` 能正常启动
- [ ] 容器内 cgroup 的 `memory.memsw.limit_in_bytes` 与参数一致

## 复盘与预防

1. **这条警告不是“Docker 装坏了”**：它只影响 swap 限制能力，不影响容器基本运行；但生产上如果有内存兜底策略，建议开启。
2. **改 GRUB 前先备份**：`/etc/default/grub` 改错会导致开机参数异常，先 `cp` 备份，改完 `update-grub` 再重启。
3. **别在生产高峰重启**：开启 swapaccount 需要重启内核参数，安排维护窗口。
4. **cgroup v2 不要照抄**：先看 `stat -fc %T /sys/fs/cgroup`，v2 下没有 `swapaccount` 这个开关，乱加参数没有意义。
5. **swap 不是万能兜底**：开启 swap 限制后仍要监控容器内存和节点 swap 使用，避免节点因 swap 抖动导致整体变慢。

## 相关

- Docker 命令速查：[Docker 命令速查](/reference/docker-commands)
- 容器问答：[容器与 Kubernetes 问题](/guide/container#常见问题-faq)
- 内核参数：[sysctl 与 ulimit](/reference/linux-commands)
