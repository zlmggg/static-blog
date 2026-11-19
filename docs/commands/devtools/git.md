---
title: "git · 版本协作底座"
description: "git 日常提交分支远程、查看历史与差异、撤销与回退、暂存 stash、标签。--help 参数按频率中文分级。工作流详解在 CI/CD 服务页。"
---

# git · 版本协作底座

> 命令手册 · [开发与效率](/commands/devtools/) ｜ 频率：每天用
> Git 是版本协作工具（不是常驻服务），命令放本组；GitLab/Jenkins 工作流详解在 [CI/CD 服务页](/services/cicd/gitlab)。

## 一句话用途

管代码版本：提交、分支、合并、推远程、看历史、撤销回退。

## 高频场景速查

```bash
git status                           # 看当前改动
git add -A && git commit -m "说明"    # 暂存+提交
git push origin main                 # 推远程
git pull --rebase                    # 拉取并变基（历史更干净）
git switch -c feature/x              # 建并切分支
git log --oneline -10                # 看最近10条
git diff                             # 看未暂存改动
git stash / git stash pop            # 临时收起/恢复改动
```

## 参数详解（按频率分级）

### 每天用

| 命令 | 含义 |
|---|---|
| `status` / `diff` | 看改动 |
| `add` / `commit -m` | 暂存 / 提交 |
| `push` / `pull` | 推 / 拉 |
| `switch` / `branch` | 切分支 / 列分支 |
| `log --oneline` | 简洁历史 |
| `merge` | 合并分支 |

### 偶尔用

| 命令 | 含义 |
|---|---|
| `reset --soft HEAD~1` | 撤销上次提交保留改动 |
| `reset --hard HEAD~1` | 彻底丢弃上次提交（高危） |
| `revert <commit>` | 生成反向提交（安全回退已推送的） |
| `restore 文件` | 丢弃工作区改动 |
| `stash` / `stash pop` | 暂存现场 |
| `tag -a v1.0 -m` | 打标签 |
| `cherry-pick <commit>` | 摘某提交到当前分支 |

### 很少用

| 命令 | 含义 |
|---|---|
| `rebase -i` | 交互式整理历史 |
| `reflog` | 看所有 HEAD 变动（救误删） |
| `bisect` | 二分定位引入 bug 的提交 |
| `blame 文件` | 看每行谁改的 |

::: danger reset --hard 与 revert 的区别
已推送到远程的提交要回退用 `revert`（生成反向提交，不改历史）；`reset --hard` 改写历史，强推会坑队友。误删分支/提交先 `git reflog` 找回。
:::

## 运维实战

**改错提交信息**：`git commit --amend -m "新说明"`（未推送时）。
**拉取冲突**：`git pull --rebase` 后解冲突 `git add` + `git rebase --continue`。
**临时切分支救火**：`git stash` 收起当前 → 切分支修 → 回来 `git stash pop`。

## 相关命令

[ssh-keygen](./ssh-keygen) 配 Git SSH 密钥 · [GitLab CI](/services/cicd/gitlab) · [diff/patch](/commands/basic/)

## 官方文档

- Git：<https://git-scm.com/doc>
- Pro Git 中文：<https://git-scm.com/book/zh/v2>