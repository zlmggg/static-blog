---
title: "env / export · 环境变量"
description: "env 看/临时设环境变量、export 导出、PATH 管理、env -i 干净环境、变量作用域。排「命令找不到/变量没生效」，中文详解。"
---

# env / export · 环境变量

> 命令手册 · [进程与系统](/commands/system/) ｜ 频率：偶尔用
> 命令找不到（PATH 不对）、脚本变量没生效（没 export）、服务环境不一致——都和环境变量有关。

## 一句话用途

查看、设置、导出环境变量，管理 PATH，给子进程传递环境。

## 高频场景速查

```bash
env                          # 看所有环境变量
echo $PATH                   # 看 PATH
export PATH="$PATH:/opt/bin" # 追加 PATH（当前 shell）
export APP_ENV=prod          # 导出变量（子进程可见）
env APP_ENV=prod ./app       # 仅本次命令带某变量
env -i ./app                 # 干净环境运行（排除干扰）
printenv APP_ENV             # 看单个变量
unset APP_ENV                # 删除变量
```

## 关键概念

- **shell 变量 vs 环境变量**：`VAR=x` 只是 shell 变量，子进程看不到；`export VAR=x` 才成为环境变量传给子进程。
- **PATH**：命令搜索路径，冒号分隔。命令找不到先查 PATH 含不含其目录。
- **作用域**：export 只对当前 shell 及子进程生效，永久要写 ~/.bashrc 或 /etc/profile.d/。

::: tip 排"command not found"
先 `which cmd` / `echo $PATH`。装了但找不到，多半 PATH 没含安装目录（如 /usr/local/bin、~/.local/bin）。cron 里 PATH 极简，脚本要用绝对路径。
:::

## 运维实战

**给服务注入配置**：systemd service 里 `Environment=APP_ENV=prod` 或 EnvironmentFile。
**临时切环境跑**：`env DATABASE_URL=... ./migrate.sh` 不污染当前 shell。
**排环境差异**：`env -i bash --noprofile --norc` 起干净 shell 对比，定位是哪个变量作怪。

## 相关命令

[变量](/commands/shell/variables) · [which/whereis](./which-whereis) · [exec/source](/commands/shell/exec-source-eval) · [systemctl](./systemctl-journalctl)

## 官方文档

- env：<https://man7.org/linux/man-pages/man1/env.1.html>
- Bash 环境：<https://www.gnu.org/software/bash/manual/html_node/Environment.html>