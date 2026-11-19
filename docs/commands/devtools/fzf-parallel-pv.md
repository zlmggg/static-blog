---
title: "fzf / parallel / pv · 效率工具"
description: "fzf 模糊查找历史与文件、parallel 并行批量执行、pv 看管道进度。提升运维操作效率，参数中文分级。"
---

# fzf / parallel / pv · 效率工具

> 命令手册 · [开发与效率](/commands/devtools/) ｜ 频率：偶尔用
> 三个提效小工具：fzf 模糊搜、parallel 并行跑、pv 看进度。用熟了操作快很多。

## 一句话用途

模糊查找命令历史/文件、把批量任务并行化、给管道加进度条。

## 高频场景速查

```bash
# fzf（装后 Ctrl+R 模糊搜历史）
history | fzf                          # 模糊找历史命令
vim $(fzf)                             # 模糊选文件打开
kubectl get pods | fzf                 # 模糊选 pod

# parallel 并行
cat hosts.txt | parallel -j 4 ssh {} 'uptime'      # 4路并行查 uptime
parallel gzip ::: *.log                            # 并行压缩

# pv 进度
pv bigfile.sql | mysql db                          # 看导入进度
tar cf - /data | pv | gzip > data.tar.gz           # 看打包流量
```

## 参数详解

### fzf

| 参数 | 含义 |
|---|---|
| `--multi` / `-m` | 多选 |
| `--preview 'cat {}'` | 预览选中项 |
| `--query 词` | 初始过滤词 |
| Ctrl+R / Ctrl+T | 历史 / 文件（绑定后） |

### parallel

| 参数 | 含义 |
|---|---|
| `-j N` | 并行 N 路 |
| `{}` | 替换为输入项 |
| `:::` | 后跟参数列表 |
| `--bar` | 进度条 |

### pv

| 参数 | 含义 |
|---|---|
| `pv 文件` | 显示流速/进度/ETA |
| `-s 大小` | 已知总量时显示百分比 |

::: tip 易错点
parallel 并行 ssh 要确认目标机已免密（[ssh-keygen](./ssh-keygen)），否则卡在密码交互。并行数别开太大压垮目标或本机。
:::

## 运维实战

**批量巡检提速**：`cat hosts | parallel -j 8 ssh {} 'df -h /'` 比 for 循环串行快几倍。多机规范操作仍推荐 [Ansible](/services/cicd/ansible)。
**大文件导入看进度**：`pv dump.sql | mysql db` 不再盲目等待。

## 相关命令

[xargs](/commands/basic/) 串行管道 · [ssh-keygen](./ssh-keygen) · [Ansible](/services/cicd/ansible) · [watch](./watch-timeout-time)

## 官方文档

- fzf：<https://github.com/junegunn/fzf>
- GNU parallel：<https://www.gnu.org/software/parallel/>
- pv：<https://man7.org/linux/man-pages/man1/pv.1.html>