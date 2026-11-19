---
title: "md5sum / sha256sum · 校验和"
description: "md5sum/sha256sum 算文件指纹、-c 校验清单、验证下载完整性/传输一致。sha256 更安全，中文详解。"
---

# md5sum / sha256sum · 校验和

> 命令手册 · [文件与文本](/commands/basic/) ｜ 频率：偶尔用
> 下载的文件完整吗？传输后变了吗？算个哈希指纹对比就知道。sha256 比 md5 抗碰撞，安全场景用 sha256。

## 一句话用途

计算/校验文件的哈希指纹（完整性校验）。

## 高频场景速查

```bash
sha256sum file.tar.gz            # 算 SHA256
md5sum file.tar.gz               # 算 MD5
sha256sum *.tar.gz > sums.txt    # 生成清单
sha256sum -c sums.txt            # 按清单校验
sha256sum -c sums.txt --quiet    # 只报失败
echo 'abc' | sha256sum           # 算字符串哈希
```

## 输出与校验

```text
# 生成
e3b0c442...  file.tar.gz
# 校验输出
file.tar.gz: OK
file.tar.gz: FAILED
```

## md5 vs sha256

| | MD5 | SHA256 |
|---|---|---|
| 长度 | 128位 | 256位 |
| 抗碰撞 | 已被攻破 | 安全 |
| 用途 | 快速完整性 | 安全校验/签名 |

::: tip 安全用 sha256
MD5 可被构造碰撞，不能用于防篡改/签名。验证下载完整性两者都行，安全相关（固件/证书）用 sha256。官方下载页给的校验值要对比一致。
:::

## 运维实战

**验证下载**：下载 ISO/包后 sha256sum 对比官网值，防下载损坏/被篡改。
**传输一致性**：scp 前后两端 sha256sum 对比（[scp](/commands/network/scp-sftp)）。
**批量校验**：生成 sums.txt 随文件分发，对端 -c 一键校验。
**备份完整性**：备份后算哈希存档，恢复时校验。

## 相关命令

[scp/sftp](/commands/network/scp-sftp) · [tar](./tar) · [openssl](/commands/devtools/openssl) · [split](./split) · [file](./file)

## 官方文档

- sha256sum：<https://man7.org/linux/man-pages/man1/sha256sum.1.html>
- md5sum：<https://man7.org/linux/man-pages/man1/md5sum.1.html>