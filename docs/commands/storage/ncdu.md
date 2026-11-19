---
title: "ncdu · 交互式磁盘占用"
description: "ncdu 交互浏览目录占用、排序/进入/删除，比 du 直观找大文件。磁盘满了快速定位，中文详解。"
---

# ncdu · 交互式磁盘占用

> 命令手册 · [磁盘与存储](/commands/storage/) ｜ 频率：偶尔用
> du 输出一堆数字难看，ncdu 交互式浏览：方向键进目录、按大小排序、直接删。找"谁占满了磁盘"最快。

## 一句话用途

交互式浏览目录磁盘占用，快速定位大文件/大目录。

## 高频场景速查

```bash
ncdu /                     # 从根浏览（需装 ncdu）
ncdu /var                  # 看 /var
ncdu -x /                  # 不跨文件系统（排除挂载）
ncdu -o scan.txt /         # 导出扫描结果
ncdu -f scan.txt           # 读已扫描结果（离线看）
```

## 界面按键

| 键 | 作用 |
|---|---|
| `↑/↓` | 选择 |
| `→/Enter` | 进入目录 |
| `←` | 返回上级 |
| `n` | 按名排序 |
| `s` | 按大小排序 |
| `d` | 删除选中（慎用） |
| `g` | 切换图形/百分比 |
| `q` | 退出 |

## ncdu vs du

| | du | ncdu |
|---|---|---|
| 输出 | 文本列表 | 交互浏览 |
| 找大目录 | 排序看 | 直观进入 |
| 远程慢盘 | 每次重扫 | -o 导出离线看 |

## 运维实战

**磁盘满了定位**：`ncdu -x /` 从根逐层进入，揪出占空间的目录（常见 /var/log、/tmp、容器 overlay）。
**远程慢盘**：`ncdu -o /tmp/scan.txt /data` 扫一次导出，慢慢分析不用重扫。
**配合 du**：脚本里用 `du -xh --max-depth=1 | sort -rh | head`（[du](./du)），交互用 ncdu。

::: tip 易错点
ncdu 的 d 删除是真删（进回收站？不，直接删），生产慎用。-x 不跨文件系统避免扫到 NFS/其他挂载卡住。
:::

## 相关命令

[du](./du) · [df](./df) · [logrotate](./logrotate) · [find](/commands/basic/find)

## 官方文档

- ncdu：<https://dev.yorhel.nl/ncdu>
- man：<https://man7.org/linux/man-pages/man1/ncdu.1.html>