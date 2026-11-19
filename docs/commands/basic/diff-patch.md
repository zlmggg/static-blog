---
title: "diff / patch · 比较与打补丁"
description: "diff 比较文件差异、-u 统一格式/-r 递归目录、patch 应用补丁。配置变更核对与分发，中文详解。"
---

# diff / patch · 比较与打补丁

> 命令手册 · [文件与文本](/commands/basic/) ｜ 频率：偶尔用
> 改配置前后对比、生成补丁分发到多台机器——diff 找差异，patch 应用差异。

## 一句话用途

比较文件/目录差异，生成与应用补丁。

## 高频场景速查

```bash
diff old.conf new.conf               # 比较两文件
diff -u old.conf new.conf            # 统一格式（带上下文，推荐）
diff -u old.conf new.conf > fix.patch   # 生成补丁
patch old.conf < fix.patch           # 应用补丁
diff -r dir1 dir2                    # 递归比较目录
diff -q dir1 dir2                    # 只列哪些文件不同
diff -y file1 file2                  # 并排对比
```

## diff 输出格式

| 格式 | 特点 |
|---|---|
| 默认 | `<` 旧 `>` 新，简洁 |
| `-u` 统一 | 带 ± 与上下文，patch 标准 |
| `-c` 上下文 | 分块显示 |
| `-y` 并排 | 左右对照 |

## patch 应用

```bash
patch target.conf < fix.patch        # 应用
patch -p1 < fix.patch                # 去掉路径第1层（目录补丁）
patch --dry-run < fix.patch          # 预演不真改
patch -R < fix.patch                 # 反向（撤销补丁）
```

::: tip 配置变更核对
改线上配置前 `diff -u 原配置 新配置` 看清改了什么，留补丁可回滚（patch -R）。批量分发补丁比 scp 整文件更省、更可审计。
:::

## 运维实战

**核对配置改动**：diff -u 备份 当前，确认只改了预期项。
**批量打补丁**：生成 patch → Ansible 分发 → patch 应用（[Ansible](/services/cicd/ansible)）。
**目录同步核对**：diff -rq 两目录看哪些文件不一致。

## 相关命令

[cp](./cp) · [vim](./vim) · [sed](./sed) · [md5sum/sha256sum](./md5sum-sha256sum) · [Ansible](/services/cicd/ansible)

## 官方文档

- diff：<https://man7.org/linux/man-pages/man1/diff.1.html>
- patch：<https://man7.org/linux/man-pages/man1/patch.1.html>