---
title: "shellcheck / bash -n · 静态检查"
description: "shellcheck 静态扫描脚本隐患（未引号变量/子shell/废弃写法）、bash -n 语法检查、bash -x 调试跟踪、set -x。脚本质量保障中文详解。"
---

# shellcheck / bash -n · 静态检查

> 命令手册 · [Shell 与脚本](/commands/shell/) ｜ 主题页
> 脚本写完先体检：shellcheck 扫隐患、bash -n 查语法、bash -x 跟踪执行。少踩坑靠它们。

## 一句话用途

不运行就发现脚本里的语法错误和常见隐患，运行时跟踪每一步定位问题。

## 高频场景速查

```bash
shellcheck deploy.sh             # 静态扫描（强烈推荐）
shellcheck -S warning deploy.sh  # 只看 warning 以上
bash -n deploy.sh                # 只查语法不执行
bash -x deploy.sh                # 跟踪执行（打印每条命令）
bash -x deploy.sh 2> trace.log   # 跟踪日志存文件
```

## shellcheck 常见告警

| 代码 | 含义 | 修法 |
|---|---|---|
| SC2086 | 变量没加引号 | `"$var"` |
| SC2046 | 命令替换没引号 | `"$(cmd)"` |
| SC2162 | read 没 -r | `read -r` |
| SC2034 | 变量定义了没用 | 删或用 |
| SC2155 | 声明+赋值掩盖退出码 | 分两行 |

```bash
# 局部忽略某条告警
# shellcheck disable=SC2086
echo $intentionally_unquoted
```

## 调试跟踪

```bash
set -x            # 脚本内开启跟踪（打印展开后的命令）
... 可疑段 ...
set +x            # 关闭

# 或只跟踪某函数
func() { set -x; ...; set +x; }
```

`bash -x` 输出前缀 `+`，显示变量展开后的真实命令——定位"变量值不对"最直观。

## 运维实战

**CI 里卡脚本质量**：流水线加 `shellcheck *.sh`，告警即失败，逼着写规范。
**排"脚本跑飞了"**：`bash -x` 看实际执行的命令和变量值，比瞪眼读代码快。

::: tip 易错点
`bash -n` 只查语法，查不出逻辑隐患（未引号变量等），那要靠 shellcheck。两者配合用。
:::

## 相关主题

[健壮性 set/trap](./robust) · [变量](./variables) · [重定向](./redirect-pipe)

## 官方文档

- ShellCheck：<https://www.shellcheck.net/>
- ShellCheck wiki：<https://github.com/koalaman/shellcheck/wiki>