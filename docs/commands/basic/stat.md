---
title: "stat · 文件元信息"
description: "stat 看 inode/权限/属主/三个时间戳/大小、-c 自定义格式、-f 看文件系统。比 ls -l 更全的元数据，中文详解。"
---

# stat · 文件元信息

> 命令手册 · [文件与文本](/commands/basic/) ｜ 频率：偶尔用
> ls -l 只看部分信息，stat 给全：inode、精确时间戳（atime/mtime/ctime）、块数、设备号。排权限/时间问题用它。

## 一句话用途

显示文件或文件系统的详细元数据。

## 高频场景速查

```bash
stat file.txt                    # 完整元信息
stat -c '%a %U %G %s %n' file    # 自定义：权限 属主 组 大小 名
stat -c '%y' file                # 只看修改时间
stat -f /data                    # 看文件系统信息（ inode 总量/空闲）
stat -L symlink                  # 跟随软链看目标
```

## 输出解读

```text
  File: file.txt
  Size: 1024       Blocks: 8     IO Block: 4096   regular file
Device: 802h/2050d Inode: 12345  Links: 1
Access: (0644/-rw-r--r--)  Uid: (1000/user)  Gid: (1000/user)
Access: 2026-11-19 ...   ← atime 访问
Modify: 2026-11-19 ...   ← mtime 内容修改
Change: 2026-11-19 ...   ← ctime 元数据变更
```

## 三个时间戳

| 时间 | 含义 | 何时变 |
|---|---|---|
| atime | 访问 | 读文件 |
| mtime | 修改 | 改内容 |
| ctime | 变更 | 改权限/属主/内容 |

## 运维实战

**排权限**：stat -c '%a %U %G' 精确看权限位与属主（[chmod](/commands/identity/chmod)）。
**查 inode**：硬链接数 Links、inode 号，理解硬链接（[ln](./ln)）。
**文件系统 inode 余量**：stat -f 看空闲 inode（[df -i](/commands/storage/df)）。
**脚本取属性**：stat -c 格式化输出便于脚本解析。

## 相关命令

[ls](./ls) · [chmod](/commands/identity/chmod) · [touch](./touch) · [ln](./ln) · [df](/commands/storage/df)

## 官方文档

- stat：<https://man7.org/linux/man-pages/man1/stat.1.html>