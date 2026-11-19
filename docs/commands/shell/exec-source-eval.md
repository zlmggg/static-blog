---
title: "exec / source / eval · 执行方式"
description: "source 与 bash 执行的区别（当前 shell vs 子进程）、exec 替换进程与重定向、eval 二次解析及其安全风险。中文详解。"
---

# exec / source / eval · 执行方式

> 命令手册 · [Shell 与脚本](/commands/shell/) ｜ 主题页
> 同一个脚本，`source` 和 `bash` 跑效果不同；exec 能替换当前进程；eval 强大但危险。搞懂执行方式少踩坑。

## 一句话用途

控制脚本/命令在哪个进程里跑、是否替换当前 shell、是否二次解析字符串。

## source vs bash（重点）

```bash
source env.sh        # 在当前 shell 执行，变量/函数留在当前环境
. env.sh             # 等价 source（POSIX 写法）
bash env.sh          # 开子进程执行，变量不影响当前 shell
./env.sh             # 同 bash（需执行权限+shebang）
```

::: tip 为什么 source 激活环境
`source venv/bin/activate` 用 source 是因为要改**当前 shell** 的 PATH；用 bash 跑改的是子进程，退出就没了。加载环境变量配置同理用 source。
:::

## exec

```bash
exec nginx -g 'daemon off;'    # 用 nginx 替换当前 shell 进程（容器入口常用）
exec > logfile 2>&1            # 重定向当前 shell 后续所有输出
exec 3< file                   # 打开文件描述符 3
```

exec 不创建新进程，直接**替换**当前进程映像。容器 ENTRYPOINT 用 exec 让应用成为 PID 1，正确接收信号。

## eval（慎用）

```bash
cmd='echo hello'
eval "$cmd"          # 把字符串当命令二次解析执行
```

eval 对字符串做二次展开后执行。强大但**极危险**——若字符串含用户输入，等于命令注入。

::: danger eval 的安全风险
`eval "echo $user_input"` 当 user_input 是 `; rm -rf /` 会执行删除。绝大多数场景用数组 + `"${arr[@]}"` 或直接执行替代 eval，别拼接字符串 eval。
:::

## 运维实战

**加载配置**：`source /etc/profile.d/app.sh` 让环境变量在当前会话生效。
**容器入口**：`exec "$@"` 让 CMD 进程替换 shell，正确收 SIGTERM 优雅退出。
**脚本日志全收**：开头 `exec > >(tee -a run.log) 2>&1` 后续输出全进日志。

## 相关主题

[变量](./variables) · [重定向](./redirect-pipe) · [函数](./functions) · [健壮性](./robust)

## 官方文档

- Bash 内建：<https://www.gnu.org/software/bash/manual/html_node/Bourne-Shell-Builtins.html>