---
title: "ncdu 命令详解：交互式磁盘占用分析"
description: "本文是 Linux 命令速查 中磁盘排查的补充；ncdu（NCurses Disk Usage）用 TUI 交互式浏览目录占用，比 du -sh * 逐层猜目录快得多。 目标：磁盘满了能快速找到“到底是哪个目录、哪类文件”吃掉的，并能把扫描结果导出后离线分析。"
---
# ncdu 命令详解：交互式磁盘占用分析

> 本文是 [Linux 命令速查](../linux-commands#磁盘空间) 中磁盘排查的补充；`ncdu`（NCurses Disk Usage）用 TUI 交互式浏览目录占用，比 `du -sh *` 逐层猜目录快得多。
> 目标：磁盘满了能快速找到“到底是哪个目录、哪类文件”吃掉的，并能把扫描结果导出后离线分析。

## 一、它解决什么问题

`du` 只能一行行输出，目录一多就要反复 `du -sh * | sort -h` 往下钻；`ncdu` 把结果做成可交互界面：

- 按大小排序，直接看到最大的目录/文件；
- 回车进入子目录，左箭头返回上级；
- 支持按名称、大小、 apparent size 排序；
- 可以标记并删除文件（生产环境慎用）；
- 支持导出扫描结果，在本地打开分析，不用在生产机上长时间停留。

## 二、安装

```bash
# RHEL / Rocky / CentOS
sudo dnf install -y ncdu

# Debian / Ubuntu
sudo apt update && sudo apt install -y ncdu
```

确认版本：

```bash
ncdu --version
```

## 三、最常用命令

```bash
# 扫描 /var，默认按实际磁盘占用排序
sudo ncdu /var

# 只扫当前文件系统，不跨挂载点（排查根分区必加）
sudo ncdu -x /

# 扫描时不进入 /proc、/sys 等内核文件系统
sudo ncdu --exclude-kernfs -x /

# 导出扫描结果，之后在本地打开
sudo ncdu -o /tmp/scan.json /

# 读取之前导出的结果（只读浏览）
ncdu -f /tmp/scan.json
```

`-x` 很重要：不加会跨到 NFS、容器 overlay、备份盘等挂载点，扫描慢，而且统计的不是你以为的那个分区。

## 四、界面按键

进入界面后：

| 按键 | 作用 |
|---|---|
| `↑` / `↓` | 上下移动 |
| `→` / `Enter` | 进入选中的目录 |
| `←` | 返回上级 |
| `n` | 按名称排序 |
| `s` | 按大小排序 |
| `a` | 切换 apparent size（表观大小，不按块对齐） |
| `g` | 切换百分比/图形显示 |
| `d` | 删除选中项（会二次确认，生产慎用） |
| `?` | 帮助 |
| `q` | 退出 |

`apparent size` 和实际占用不是一回事：稀疏文件、压缩文件、硬链接、块对齐都会让两者不同。排查“`df` 满了但 `du` 对不上”时，先用默认实际占用，再切 `a` 对比。

## 五、典型排查场景

### 1. 根分区满了，先定位大目录

```bash
sudo ncdu -x /
```

进入 `/` 后看第一屏最大的目录，回车逐层下钻：`/var` → `/var/log` → `/var/lib/docker`。不要一上来就 `find / -size +1G`，全盘 find 更慢，而且会被大量小文件拖死。

### 2. 只看某个业务目录

```bash
sudo ncdu -x /data
```

### 3. 生产机不方便长期操作：导出后本地看

```bash
# 生产机
sudo ncdu -o /tmp/scan.json -x /

# 拉到本地
scp ops@server:/tmp/scan.json ./

# 本地打开
ncdu -f scan.json
```

导出文件是 JSON，也可以直接 `jq` 处理，但 `ncdu -f` 浏览最直观。

### 4. 排除已知的大目录

```bash
sudo ncdu -x --exclude=/data/backup --exclude='*/cache/*' /
```

`--exclude` 可以用通配符；排除规则按路径匹配，不确定时先小范围试。

### 5. 容器宿主机的 `/var/lib/docker`

```bash
sudo ncdu -x /var/lib/docker
```

常见占用：`overlay2`（镜像层和容器可写层）、`containers`（日志）、`volumes`（卷）。不要直接删 `overlay2` 目录，清理要走 `docker system prune`、`docker image prune` 等命令，否则容易把运行中的容器搞坏。

## 六、ncdu 和 du 怎么选

| 场景 | 用哪个 |
|---|---|
| 脚本里统计目录大小 | `du -sh` / `du -sb` |
| 交互式逐层排查 | `ncdu` |
| 按修改时间、属主、类型筛选 | `find` |
| 查已删除但被进程占用的大文件 | `lsof +L1` / `lsof | grep deleted` |

`ncdu` 不显示“已删除但仍被进程打开”的文件，这类空间要配合 `lsof` 查：

```bash
sudo lsof +L1
sudo lsof | grep deleted
```

## 七、常见坑

1. **不加 `-x` 扫到别的挂载点**：统计结果和 `df` 对不上，根分区排查一定加 `-x`。
2. **用 root 扫全盘很慢**：先扫最可疑的顶层目录，再逐层下钻；不要无脑 `ncdu /`。
3. **`d` 删除很危险**：生产环境只用它看，删除走变更流程；误删后恢复成本很高。
4. **硬链接重复计算**：同一文件多个硬链接时，`du`/`ncdu` 的统计口径要看版本和选项，别拿两个工具的数字直接对账。
5. **稀疏文件**：`du` 按实际块算，`ls -l` 按表观大小算，数据库、虚拟磁盘镜像常见，别误判。
6. **扫描时 IO 高**：大目录扫描会读元数据，生产高峰期先 `nice -n 19 ionice -c3 ncdu ...` 降优先级。

## 官方文档

- [ncdu 官方手册](https://dev.yorhel.nl/ncdu/man)
- [ncdu 项目主页](https://dev.yorhel.nl/ncdu)
