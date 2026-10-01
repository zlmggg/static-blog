# Shell 编程与文本处理

::: tip 本篇定位
覆盖 Shell 语法和 grep/awk/sed、find 等文本处理。
:::

## 高频面试题

### Q1：grep、awk、sed 各自擅长？

**我的答案：**

这三个是文本处理三剑客，我按"各管一段"来记：grep 管**找行**，awk 管**按列处理**，sed 管**编辑替换**。

**grep** 是行过滤器，作用是"从一堆文本里把符合条件的行筛出来"，不做修改。常用参数：`-i` 忽略大小写、`-v` 反选（排除匹配行）、`-r` 递归目录、`-n` 显示行号、`-E` 用扩展正则。比如 `grep -rn "error" /var/log/` 找出日志里所有 error 行。

**awk** 是按列处理的语言，适合"每行是一条记录、用空格或分隔符分成几列"的场景。它能取列、做统计、按条件过滤。比如 `awk '{print $1}'` 取第一列，`-F:` 指定冒号分隔（处理 /etc/passwd 特别好用）。

**sed** 是流编辑器，适合"按规则批量替换或删行"，最常用就是替换：`sed 's/旧/新/g'`。比如 `sed -i 's/192.168.1.10/10.0.0.5/g' nginx.conf` 直接改文件里的 IP。`-i` 是原地修改，不加 `-i` 只打印结果不改文件。

一句话分工：**要找用 grep，要算列用 awk，要改文本用 sed**，实战里经常仨串起来用——grep 先过滤，awk 再取列统计，sed 最后替换。

---

### Q2：awk 如何统计列总和/出现次数？

**我的答案：**

awk 的精髓就是它的"三段式"和数组统计，我用两个例子说清楚。

**统计某列总和**：它有 BEGIN、主体、END 三个块。BEGIN 是处理前跑一次（初始化），主体是每行跑一次，END 是全部读完跑一次（输出汇总）。比如统计 /tmp/data 里第二列的总和：

```bash
awk '{sum += $2} END {print "总和=" sum}' /tmp/data
```

这里 sum 每行累加第二列 `$2`，最后 END 打印总和。

**统计某个字段出现次数**：用数组当计数器，key 就是要统计的内容。比如统计 /etc/passwd 里每种 shell 出现多少次（用 `-F:` 指定冒号分隔，第 7 列是 shell）：

```bash
awk -F: '{cnt[$7]++} END {for (s in cnt) print s, cnt[s]}' /etc/passwd
```

原理是：每读一行，就把 `cnt[这个shell]` 加 1，遇到相同 shell 自动累加；END 里遍历这个数组，把每种 shell 和它的次数打出来。这就是 awk 做分组计数的经典套路。

再比如统计第 1 列等于某个值时第 3 列的和：`awk '$1=="web" {sum+=$3} END{print sum}'`。核心就记三点：`-F` 定分隔符、`数组[key]++` 做计数、`END` 出结果。

---

### Q3：统计日志中访问最高的 IP？

**我的答案：**

这是 awk/sort/uniq 组合的经典题，套路是"取 IP → 计数 → 排序 → 取前 N"。假设是 Nginx access.log，IP 在第一列：

```bash
awk '{print $1}' /var/log/nginx/access.log | sort | uniq -c | sort -rn | head -10
```

我一步步解释这条管道。第一截 `awk '{print $1}'` 把每行的 IP 单独取出来，一行一个。第二截 `sort` 先排序——uniq 只能合并相邻的重复行，所以前面必须先 sort，否则一样的 IP 不挨着就统计不到，这是新手最容易漏的一步。第三截 `uniq -c` 把相邻重复行合并并在前面打出出现次数。第四截 `sort -rn` 按出现次数**数字倒序**排（`-r` 倒序、`-n` 按数值）。最后 `head -10` 取前 10 个。

输出大概长这样：

```
   1523 1.2.3.4     ← 访问最多的 IP
    860 5.6.7.8
    210 9.10.11.12
```

如果日志格式复杂、IP 不在第一列，可以先用 grep 过滤，比如只统计 404 请求里的 IP：`grep ' 404 ' access.log | awk '{print $1}' | sort | uniq -c | sort -rn | head`。整个套路——取列、sort、uniq -c、sort -rn——记熟，统计 Top N 的题都能套。

---

### Q4：find 常用用法？

**我的答案：**

find 是按条件找文件再批量处理的工具，我按"找什么、怎么处理"两类记。

**按条件找（常用条件）：**

```bash
find /etc -name "*.conf"                 # 按名字找，-iname 忽略大小写
find /var -type f -size +100M            # 找大于 100M 的普通文件
find /home -type d -name "logs"          # -type d 只找目录，f 是文件
find /var/log -mtime -7                   # 7 天内被修改过的文件（+7 是 7 天前）
```

参数要点：`-name` 按文件名、`-type f/d` 按类型、`-size` 按大小（+大于 -小于）、`-mtime` 按修改时间（天）。

**找到之后批量处理（-exec）：**

```bash
find /var/log -name "*.log" -mtime +30 -exec rm -f {} \;
# 找出 30 天前的日志并删除，{} 代表找到的每个文件，\; 结尾

find /tmp -name "*.tmp" -exec ls -lh {} \;     # 先看下找到啥再删，保险
```

生产上有两个好习惯：一是**删之前先用 `-exec ls -lh {} \;` 预览一遍**，确认找的是对的再换 `rm`，别上来就删；二是清老日志用 `-mtime +N` 按时间删，这是日志轮转的手工做法。

我个人常用来排查的一条：`find / -name "*.pid" -mmin -60` 找最近一小时变动的文件。find 的核心就是"先把条件写准，再用 -exec 批量动作"。

---

## 相关链接

- [相关文档](/reference/linux-commands)
