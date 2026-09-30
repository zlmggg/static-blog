---
title: Shell 脚本编程
description: Bash 脚本系统教程：变量、运算测试、条件循环、函数、数组、trap、调试与生产实战脚本
---

# Shell 脚本编程

::: tip 本篇定位
系统掌握 **Bash 脚本**：从 Shell 概念、变量、运算与测试，到条件、循环、函数、数组、输入输出、信号陷阱和调试，最后给出可直接改造使用的**生产实战脚本**，能独立编写自动化运维小工具。
:::

## 一、Shell 概述

### 1.1 什么是 Shell

Shell 是**命令解释器**，位于用户（应用程序）和操作系统内核之间：它把用户输入的命令解释给内核执行，再把结果返回给用户。登录后看到的命令行界面就是 Shell 提供的。

```
应用程序 → Shell → 操作系统内核 → 硬件
```

常见 Shell：

| Shell | 说明 |
|---|---|
| **bash** | GNU Bourne Again Shell，多数发行版默认，功能全 |
| sh | 早期 Bourne Shell（现代常是 bash/dash 的软链） |
| zsh | 交互体验强、补全丰富（macOS 默认） |
| dash | 轻量，Debian/Ubuntu 中 /bin/sh 常指向它 |

```bash
echo $SHELL          # 当前登录 Shell
cat /etc/shells      # 系统可用的 Shell
bash --version       # bash 版本
```

### 1.2 脚本结构与 shebang

Shell 脚本是把多条命令写进一个文本文件批量执行。第一行的 `#!` 叫 **shebang**，指定用哪个解释器执行：

```bash
#!/bin/bash
# 或 #!/usr/bin/env bash（通过 env 查找，移植性更好）
```

### 1.3 注释

```bash
# 单行注释（# 后到行尾）

: <<'EOF'
多行注释（块注释），EOF 之间都是注释
第二行
EOF
```

### 1.4 运行方式

```bash
bash script.sh          # 用 bash 解释执行，无需可执行权限
./script.sh             # 直接运行，需要可执行权限 + shebang
source script.sh        # 在当前 Shell 中执行（. script.sh），不开启子进程
```

```bash
chmod +x script.sh      # 赋予执行权限
```

::: warning source 与直接执行的区别
- `bash script.sh` / `./script.sh` 会开启**子 Shell**，脚本里设置的变量、cd 等不影响当前终端；
- `source`（`.`）在**当前 Shell** 执行，常用于加载环境变量配置（如 `source ~/.bashrc`）。
:::

### 1.5 开发规范

- 文件名见名知意，一般 `.sh` 结尾（如 `backup_mysql.sh`）；
- 脚本开头写注释：用途、作者、日期；
- 复杂逻辑加注释，缩进统一（4 空格）；
- 变量用 `${var}`、路径/变量加引号防止空格问题；
- 重要操作先判断、给出提示。

---

## 二、变量

### 2.1 定义与引用

```bash
name="tom"            # 赋值：等号两侧【不能有空格】
echo $name            # 引用
echo "${name}_log"    # 花括号明确变量边界
```

### 2.2 本地变量与环境变量

```bash
local_var=123                 # 本地变量，仅当前 Shell 有效
export GLOBAL_VAR=abc         # 环境变量，子进程可继承
env | grep GLOBAL             # 查看环境变量
```

### 2.3 特殊变量

| 变量 | 含义 |
|---|---|
| `$0` | 脚本/程序名 |
| `$1`…`$9` | 第 1…9 个位置参数 |
| `${10}` | 第 10 个参数（超过 9 用花括号） |
| `$#` | 参数个数 |
| `$@` / `$*` | 所有参数（加双引号时 `$@` 保持各参数独立，推荐） |
| `$?` | 上一条命令的退出状态（0 成功，非 0 失败） |
| `$$` | 当前 Shell/脚本 PID |
| `$!` | 最近一个后台进程的 PID |

```bash
#!/bin/bash
echo "脚本名: $0"
echo "参数个数: $#"
echo "第一个参数: $1"
echo "所有参数: $@"
```

### 2.4 只读与删除

```bash
readonly PI=3.14          # 只读，不可修改
unset name                # 删除变量
```

### 2.5 命令替换

把命令的输出赋给变量：

```bash
today=$(date +%F)         # 推荐写法
today=`date +%F`          # 旧式反引号
files=$(ls /etc)
```

### 2.6 引号区别（重要）

| 引号 | 行为 |
|---|---|
| 单引号 `'...'` | **原样输出**，变量、命令不展开 |
| 双引号 `"..."` | 变量 `$`、命令替换会展开（推荐默认用双引号） |
| 反引号 `` `...` `` | 命令替换（建议用 `$( )`） |

```bash
name=tom
echo 'hello $name'        # hello $name
echo "hello $name"        # hello tom
```

### 2.7 declare

```bash
declare -i num=10         # 整数类型
declare -r ro=abc         # 只读
declare -x export_var=1   # 导出为环境变量
declare -l/-u str         # 转小写/大写
```

---

## 三、运算与测试

### 3.1 算术运算

```bash
# $(( )) 整数运算（最常用）
a=3; b=2
echo $((a + b))          # 加
echo $((a - b))
echo $((a * b))
echo $((a / b))
echo $((a % b))          # 取余
echo $((a ** b))         # 幂
((a++))                  # 自增
((a += 5))

let "c = a + b"          # let 算术
expr $a + $b             # expr（运算符两侧需空格，老式）
echo "scale=2; 10/3" | bc   # bc 支持小数
```

### 3.2 test 与 [ ]

`test` 和 `[ ]` 等价（`[` 后、`]` 前必须有空格），用于条件判断。

**数值比较：**

| 写法 | 含义 |
|---|---|
| `-eq` / `-ne` | 等于 / 不等于 |
| `-gt` / `-ge` | 大于 / 大于等于 |
| `-lt` / `-le` | 小于 / 小于等于 |

**字符串比较：**

| 写法 | 含义 |
|---|---|
| `=` / `==` | 相等 |
| `!=` | 不等 |
| `-z "$s"` | 字符串为空（长度 0） |
| `-n "$s"` | 字符串非空 |

**文件测试：**

| 写法 | 含义 |
|---|---|
| `-e file` | 文件/目录存在 |
| `-f file` | 是普通文件 |
| `-d file` | 是目录 |
| `-r/-w/-x file` | 可读/写/执行 |
| `-s file` | 存在且非空 |
| `-L file` | 是软链接 |
| `file1 -nt/-ot file2` | 比 file2 新 / 旧 |

```bash
test -f /etc/passwd && echo "存在"
[ -d /etc ] && echo "是目录"
[ "$name" = "tom" ] && echo "匹配"
```

### 3.3 [[ ]] 进阶

`[[ ]]` 是 bash 增强，支持 `&&`、`||`、模式匹配、正则，更安全（推荐 bash 脚本使用）：

```bash
[[ -f /etc/hosts && -r /etc/hosts ]] && echo "存在且可读"
[[ "$file" == *.tar.gz ]] && echo "压缩包"
[[ "$str" =~ ^[0-9]+$ ]] && echo "是数字"      # 正则匹配
```

### 3.4 逻辑运算

```bash
[ 条件1 ] && [ 条件2 ]      # 与
[ 条件1 ] || [ 条件2 ]      # 或
! [ 条件 ]                  # 非
command1 && command2        # cmd1 成功才执行 cmd2
command1 || command2        # cmd1 失败才执行 cmd2
```

---

## 四、条件判断

### 4.1 if 语句

```bash
if 条件; then
    命令
elif 条件; then
    命令
else
    命令
fi
```

```bash
#!/bin/bash
read -p "请输入分数: " score
if [ "$score" -ge 90 ]; then
    echo "优秀"
elif [ "$score" -ge 60 ]; then
    echo "及格"
else
    echo "不及格"
fi
```

### 4.2 case 分支

适合多值匹配（模式 + `)`）：

```bash
case 变量 in
模式1)
    命令 ;;
模式2|模式3)
    命令 ;;
*)
    默认命令 ;;
esac
```

```bash
read -p "继续吗?(y/n): " ans
case "$ans" in
y|Y|yes) echo "执行" ;;
n|N|no)   echo "退出" ;;
*)        echo "无效输入" ;;
esac
```

---

## 五、循环

### 5.1 for 循环

```bash
# 遍历
for 变量 in 值1 值2 值3; do
    命令
done

for i in {1..5}; do echo $i; done
for f in /etc/*.conf; do echo "$f"; done

# C 风格
for ((i=1; i<=5; i++)); do
    echo $i
done
```

### 5.2 while 循环

```bash
while 条件; do
    命令
done

i=1
while [ "$i" -le 5 ]; do
    echo $i
    ((i++))
done
```

**逐行读取文件（处理文本常用）：**

```bash
while IFS= read -r line; do
    echo "行内容: $line"
done < /etc/hosts
```

> `IFS=` 保留行首空格，`-r` 不转义反斜杠，是读取文件行的标准写法。

### 5.3 until 循环

条件为**假**时一直执行（与 while 相反）：

```bash
until [ "$i" -gt 5 ]; do
    echo $i
    ((i++))
done
```

### 5.4 break / continue

```bash
break        # 跳出整个循环
continue     # 跳过本次，进入下一次
break 2      # 跳出外层循环（数字指定层数）
```

### 5.5 seq 与遍历

```bash
seq 1 5              # 生成 1-5
seq 1 2 10           # 从 1 步长 2 到 10
for i in $(seq 1 5); do echo $i; done
```

---

## 六、函数

### 6.1 定义

```bash
函数名() {
    命令
}

# 或
function 函数名 {
    命令
}
```

### 6.2 调用与参数

```bash
#!/bin/bash
greet() {
    echo "hello, $1"
}
greet tom          # 调用并传参，函数内 $1、$#、$@ 是函数自己的参数
```

### 6.3 返回值

```bash
add() {
    return $(( $1 + $2 ))     # return 返回【状态码】0-255
}
add 3 5; echo $?

calc() {
    echo $(( $1 * 2 ))        # 用 echo 输出实际值，$(calc) 接收
}
result=$(calc 10)
```

::: warning return 只能返回 0-255
`return` 返回的是退出状态码，不是任意数值。要返回计算结果，用 `echo`/`printf` 输出，再通过命令替换 `$(函数)` 获取。
:::

### 6.4 局部变量

```bash
test_func() {
    local x=10          # local 仅函数内有效，避免污染全局
    echo $x
}
```

### 6.5 函数库

把常用函数集中到一个库文件，用 `source` 引入：

```bash
# mylib.sh
pkg_check() { rpm -q "$1" &>/dev/null && echo "$1 已装" || echo "$1 未装"; }

# 主脚本
source ./mylib.sh
pkg_check nginx
```

---

## 七、数组

### 7.1 普通数组

```bash
arr=(a b c d)              # 定义
echo "${arr[0]}"           # 取第 0 个
echo "${arr[@]}"           # 所有元素
echo "${#arr[@]}"          # 元素个数
echo "${!arr[@]}"          # 所有索引
arr[4]=e                   # 添加/修改
unset arr[1]               # 删除元素

# 遍历
for item in "${arr[@]}"; do
    echo $item
done
```

### 7.2 关联数组（键值对）

```bash
declare -A person
person=([name]=tom [age]=20 [city]=cd)
echo "${person[name]}"
for key in "${!person[@]}"; do
    echo "$key = ${person[$key]}"
done
```

---

## 八、输入输出

### 8.1 read 交互

```bash
read name                  # 读取输入到变量
read -p "用户名: " user    # 提示信息
read -s -p "密码: " pwd    # -s 静默（输入不显示，用于密码）
read -t 5 var              # 超时时间
read -n 1 key              # 只读 1 个字符
```

### 8.2 echo / printf

```bash
echo "hello"
echo -n "不换行"
echo -e "a\tb"             # -e 解释转义符

printf "%s\t%d\n" "tom" 20  # printf 格式化（类似 C）
```

### 8.3 重定向

```bash
cmd > file        # 标准输出覆盖
cmd >> file       # 追加
cmd 2> err.log    # 标准错误
cmd > file 2>&1   # 正确和错误都写入
cmd &> file       # 同上简写
cmd 2>/dev/null   # 丢弃错误
cmd1 | cmd2       # 管道
```

---

## 九、信号与陷阱

### 9.1 trap 捕获信号

`trap` 在脚本收到指定信号时执行命令，常用于**清理临时文件、优雅退出**：

```bash
#!/bin/bash
cleanup() {
    echo "收到退出信号，清理中..."
    rm -f /tmp/tempfile
    exit 0
}
trap cleanup INT TERM        # 捕获 Ctrl+c(INT)、TERM
trap '' INT                  # 信号后空字符串表示忽略

touch /tmp/tempfile
while true; do sleep 1; done
```

### 9.2 退出钩子 EXIT

```bash
trap 'echo 脚本结束' EXIT    # 无论正常退出还是异常，都会执行
```

### 9.3 kill 信号回顾

常用信号：`1 HUP`、`2 INT(Ctrl+c)`、`9 KILL`、`15 TERM`、`20 TSTP(Ctrl+z)`、`18 CONT`、`19 STOP`，详见 [进程与服务管理](/guide/linux-process)。

---

## 十、调试

### 10.1 调试选项

```bash
bash -x script.sh       # 跟踪执行，每条命令展开后显示（最常用，+ 前缀）
bash -n script.sh       # 只检查语法错误，不执行
bash -v script.sh       # 执行前打印每一行
bash -x -e script.sh    # 遇错即停并跟踪
```

### 10.2 脚本内 set

```bash
set -x        # 开启调试跟踪
set +x        # 关闭调试
set -e        # 命令失败（非0）立即退出
set -u        # 使用未定义变量时报错
set -o pipefail   # 管道中任一命令失败整个管道算失败
```

::: tip 生产脚本推荐开头
```bash
#!/bin/bash
set -euo pipefail     # 遇错停、未定义变量报错、管道失败可感知
```
:::

### 10.3 常见错误

| 错误 | 原因 |
|---|---|
| `command not found` | 路径/拼写问题，cron 中 PATH 不全 |
| `[: missing ]` | `[` 后或 `]` 前缺空格 |
| 变量为空导致判断异常 | 变量没加双引号、未定义 |
| 赋值报错 | 等号两侧有空格 |
| 整数表达式错误 | `[ ]` 数值比较用了 `>`（应 `-gt`） |

---

## 十一、实战脚本集

### 11.1 系统巡检

```bash
#!/bin/bash
# syscheck.sh：系统健康巡检
echo "===== 主机信息 ====="
hostname; uptime
echo "===== CPU/内存 ====="
free -h
echo "===== 磁盘使用 ====="
df -h | grep -v tmpfs
echo "===== TOP5 CPU 进程 ====="
ps -eo pid,pcpu,pmem,comm --sort=-pcpu | head -6
echo "===== 监听端口 ====="
ss -tunlp | head
echo "===== 失败登录次数 ====="
lastb 2>/dev/null | wc -l
```

### 11.2 批量建用户

```bash
#!/bin/bash
# batch_user.sh：从文件批量创建用户
while IFS= read -r user; do
    id "$user" &>/dev/null && echo "$user 已存在" && continue
    useradd -m "$user"
    echo "Default@123" | passwd --stdin "$user" &>/dev/null
    echo "$user 创建成功"
done < users.txt
```

> Ubuntu 没有 `passwd --stdin`，改用 `echo "$user:Default@123" | chpasswd`。

### 11.3 定时备份

```bash
#!/bin/bash
# backup.sh：备份网站数据
set -e
SRC=/data/www
DEST=/data/backup
DATE=$(date +%F)
mkdir -p "$DEST"
tar -czf "$DEST/www_$DATE.tar.gz" "$SRC"
# 删除 7 天前的备份
find "$DEST" -name "www_*.tar.gz" -mtime +7 -delete
echo "$DATE 备份完成"
```

### 11.4 日志清理

```bash
#!/bin/bash
# log_clean.sh：清理过期日志
find /var/log/myapp -name "*.log" -mtime +30 -delete
# 清空超大当前日志
find /var/log -name "*.log" -size +500M -exec truncate -s 0 {} \;
```

### 11.5 服务状态检查

```bash
#!/bin/bash
# svc_check.sh：检查服务是否运行，异常则重启并告警
SERVICES=(nginx crond sshd)
for svc in "${SERVICES[@]}"; do
    if systemctl is-active --quiet "$svc"; then
        echo "$svc 正常"
    else
        echo "$svc 异常，尝试重启"
        systemctl restart "$svc"
        # 可加告警：curl/邮件/钉钉 webhook
    fi
done
```

---

## 面试自测

1. Shell 是什么？bash、sh、zsh、dash 有什么区别？
2. `#!/bin/bash`（shebang）的作用？
3. 运行脚本的三种方式（bash、./、source）有何区别？
4. 本地变量和环境变量的区别？如何让子进程看到变量？
5. `$? $# $@ $0 $$ $!` 分别是什么？
6. 单引号和双引号的区别？
7. 整数运算有哪些方式？如何做小数运算？
8. `[ ]` 和 `[[ ]]` 的区别？
9. `-eq/-gt` 和 `=/!=`、`-f/-d/-z` 分别用于什么比较？
10. while 如何逐行读取文件？为什么用 `IFS= read -r`？
11. 函数如何传参、如何返回数值结果？local 的作用？
12. 普通数组和关联数组怎么定义和遍历？
13. trap 是干什么的？典型使用场景？
14. `set -euo pipefail` 分别什么含义？
15. 如何调试 Shell 脚本？

## 相关速查

- [Linux 命令速查](/reference/linux-commands)
- [进程与服务管理](/guide/linux-process)
- [定时任务](/guide/linux-cron)
