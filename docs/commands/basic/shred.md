---
title: "shred · 安全擦除文件"
description: "shred 多次覆写防恢复、-u 覆写后删除/-n 次数/-z 补零。敏感文件销毁，SSD 局限说明，中文详解。"
---

# shred · 安全擦除文件

> 命令手册 · [文件与文本](/commands/basic/) ｜ 频率：很少用
> rm 只删目录项，数据仍可恢复。shred 多次覆写文件内容，让敏感数据难以恢复。但 SSD/日志文件系统有局限。

## 一句话用途

多次覆写文件内容以阻止恢复，可选删除。

## 高频场景速查

```bash
shred secret.txt                 # 覆写（默认3次，不删）
shred -u secret.txt              # 覆写后删除
shred -n 5 -u secret.txt         # 覆写5次后删
shred -z -u secret.txt           # 最后补一次零（掩盖覆写痕迹）
shred -v -u secret.txt           # 显示进度
```

## 参数详解

| 参数 | 含义 |
|---|---|
| `-u` | 覆写后删除文件 |
| `-n N` | 覆写次数（默认3） |
| `-z` | 最后补零 |
| `-v` | 显示进度 |
| `-f` | 强制改权限以写 |

::: danger SSD/日志文件系统局限
shred 假设原地覆写。但 SSD 磨损均衡会写到新块、ext4/xfs 日志/CoW 可能留旧副本，shred 不能保证彻底。SSD 安全擦除用 hdparm security-erase / nvme format（[nvme](/commands/storage/nvme-xfs_info-hdparm)），整盘加密（[cryptsetup](/commands/storage/cryptsetup)）后丢密钥更可靠。
:::

## 运维实战

**销毁临时密钥文件**：shred -u 用完的私钥/密码文件。
**退役机械盘**：shred 整盘（慢）或 dd 覆写，敏感场景物理销毁。
**SSD 正确做法**：加密盘丢密钥，或厂商安全擦除工具，别只靠 shred。

## 相关命令

[rm](./rm) · [dd](/commands/storage/dd) · [cryptsetup](/commands/storage/cryptsetup) · [nvme](/commands/storage/nvme-xfs_info-hdparm) · [openssl](/commands/devtools/openssl)

## 官方文档

- shred：<https://man7.org/linux/man-pages/man1/shred.1.html>