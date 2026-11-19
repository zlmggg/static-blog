---
title: "for / while / until · 循环"
description: "for 遍历列表与 C 风格、while 读文件与条件循环、until、break/continue、循环里改变量的子 shell 陷阱。中文详解。"
---

# for / while / until · 循环

> 命令手册 · [Shell 与脚本](/commands/shell/) ｜ 主题页
> 批量做事：遍历主机列表、逐行读文件、重试到成功。循环里变量改不动是最常见的坑。

## 一句话用途

重复执行：遍历一批对象、逐行处理文件、满足条件前一直重试。

## for

```bash
for ip in 10.0.0.11 10.0.0.12 10.0.0.13; do
  ssh rocky@$ip 'uptime'
done

for f in /var/log/*.log; do          # 通配展开
  gzip "$f"
done

for ((i=0; i<5; i++)); do            # C 风格
  echo "$i"
done

for ip in $(cat hosts.txt); do ...   # 命令替换取列表
```

## while / until

```bash
while IFS= read -r line; do          # 逐行读文件（标准写法）
  echo "$line"
done < hosts.txt

while ! curl -sf http://app/health; do   # 重试到成功
  sleep 2
done

until [ -f /tmp/ready ]; do sleep 1; done   # 条件为假时循环
```

`break` 跳出循环，`continue` 跳过本次。

## 子 shell 陷阱（重点）

```bash
count=0
cat hosts.txt | while read -r line; do
  count=$((count+1))      # 管道右侧是子 shell，改的是副本
done
echo "$count"             # 仍是 0！

# 正确：用重定向而非管道
count=0
while read -r line; do
  count=$((count+1))
done < hosts.txt
echo "$count"             # 正确累加
```

::: danger 管道里的变量改不动
`cmd | while ...` 的 while 在子 shell 跑，里面对变量的修改循环外看不到。要累加/收集结果，用 `while ... done < file` 或进程替换 `while ... done < <(cmd)`。
:::

## 运维实战

**批量巡检**：for 遍历主机 ssh 执行（规范场景用 [Ansible](/services/cicd/ansible)）。
**等服务就绪**：`until curl -sf health; do sleep 2; done` 部署后等健康检查通过再继续。

## 相关主题

[变量](./variables) · [test/if](./test-if-case) · [函数](./functions) · [重定向](./redirect-pipe)

## 官方文档

- Bash 循环：<https://www.gnu.org/software/bash/manual/html_node/Looping-Constructs.html>