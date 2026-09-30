# 排障记录

> 这里用**表格快速记录日常小问题和报错踩坑**：现象 → 关键词 → 解法。
> 一句话能说清的直接写表格；表格放不下的复杂排查，再单独开一篇短文（模板见底部）。
> 重大、影响业务的故障请写完整 [故障复盘](./)。

## 排障记录表

> 新记录加在表格最上面（倒序）。关键词尽量写全，方便以后 Ctrl+K 搜到。

| 日期 | 现象 / 报错 | 关键词 | 解法 |
|---|---|---|---|
| 2026-09-24 | SSH 连接很慢，要等十几秒 | ssh dns UseDNS 反向解析 | 改 `/etc/ssh/sshd_config` 设 `UseDNS no`，`systemctl restart sshd` |
| 2026-09-24 | df 显示有空间，但无法写入、提示 No space left | inode 满 小文件 | `df -i` 查 inode，清理海量小文件目录 |
| 2026-09-24 | 启动服务提示 Address already in use | 端口占用 | `ss -tunlp \| grep :80` 或 `lsof -i :80` 找到占用进程处理 |
| 2026-09-25 | 新装 Docker ，检查 docker info 提示 swap 相关报错 | docker swap | [详见短文](/cases/t-docker-swap.md) |

| ✏️ 待填 | | | |

## 常见排障入口速查

- 进程 / 端口 / 文件占用：[Linux 命令速查](/reference/linux-commands)
- 网络不通 / DNS / 抓包：[网络命令速查](/reference/network-commands)
- 容器异常：[Docker 命令速查](/reference/docker-commands)
- K8s 异常：[kubectl 命令速查](/reference/kubectl-commands)

## 排障短文模板（复杂问题用）

> 新建 `cases/t-简短标题.md`，复制以下结构：

```markdown
# 问题标题（YYYY-MM-DD）

## 现象（含完整报错信息）
## 环境（系统版本、相关软件版本）
## 定位过程（用了哪些命令、看到什么）
## 根因
## 解决步骤
## 相关命令（链接到速查长文档）
```
