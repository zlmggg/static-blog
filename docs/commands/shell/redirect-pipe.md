---
title: "重定向与管道 · 数据流向"
description: "标准输入输出错误、> >> 2>&1 &>、管道 |、tee、here-doc/here-string、进程替换。搞懂 2>&1 顺序与管道退出码。中文详解。"
---

# 重定向与管道 · 数据流向

> 命令手册 · [Shell 与脚本](/commands/shell/) ｜ 主题页
> 命令的输入输出往哪走。重定向改文件、管道接命令。`2>&1` 的顺序和管道退出码是最常踩的坑。

## 一句话用途

把命令的输出存文件、把错误一起收、把上一个命令的输出喂给下一个。

## 三个标准流

| 流 | 编号 | 默认去向 |
|---|---|---|
| stdin 标准输入 | 0 | 键盘 |
| stdout 标准输出 | 1 | 屏幕 |
| stderr 标准错误 | 2 | 屏幕 |

## 重定向

```bash
cmd > out.txt            # stdout 覆盖写文件
cmd >> out.txt           # stdout 追加
cmd 2> err.txt           # stderr 写文件
cmd > all.txt 2>&1       # stdout+stderr 都进 all.txt（顺序重要！）
cmd &> all.txt           # 同上简写（bash）
cmd < in.txt             # 从文件读 stdin
cmd 2>/dev/null          # 丢弃错误
```

::: danger 2>&1 的顺序
`cmd > all.txt 2>&1` 对：先把 1 指向文件，再把 2 指向 1 当前所指（文件）。
`cmd 2>&1 > all.txt` 错：先把 2 指向 1 当前所指（屏幕），再把 1 指向文件——错误仍打屏幕。
:::

## 管道与 tee

```bash
cmd1 | cmd2              # cmd1 的 stdout 接 cmd2 的 stdin
cmd | tee out.txt        # 既上屏又存文件
cmd | tee -a out.txt     # 追加
```

### 管道退出码（重点）

`cmd1 | cmd2` 默认返回 **cmd2** 的退出码，cmd1 失败被掩盖。脚本里要 `set -o pipefail`，任一环节失败整条管道就算失败（见 [健壮性](./robust)）。

## here-doc / here-string / 进程替换

```bash
cat <<EOF                # here-doc 多行输入
hello $name
EOF

cat <<'EOF'              # 单引号 EOF 不展开变量
literal $name
EOF

grep err <<< "$line"     # here-string 单行

diff <(sort a) <(sort b) # 进程替换，把命令输出当文件
```

## 运维实战

**日志既看又存**：`./deploy.sh 2>&1 | tee deploy.log`。
**只要错误**：`cmd 2>err.log 1>/dev/null`。
**比较两命令输出**：`diff <(ssh h1 'rpm -qa') <(ssh h2 'rpm -qa')` 看两台包差异。

## 相关主题

[变量](./variables) · [exec/source/eval](./exec-source-eval) · [set -euo pipefail](./robust) · [tee/xargs](/commands/basic/)

## 官方文档

- Bash 重定向：<https://www.gnu.org/software/bash/manual/html_node/Redirections.html>