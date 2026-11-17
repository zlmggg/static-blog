# 命令实操题

::: tip 本篇定位
覆盖现场/笔试高频的日志统计、实时过滤、批量查找和跨机批量操作命令，每条命令都拆开讲。
:::

## 高频面试题

### Q1：统计 Nginx 日志的 PV、UV、Top IP、状态码分布？

**我的答案：**

Nginx 默认访问日志每行格式大概是 `IP - - [时间] "请求" 状态码 字节 ...`，我用 awk 切字段来统计。假设日志是 `/var/log/nginx/access.log`，IP 在第 1 列、状态码在第 9 列。

**PV（总访问量）**就是日志总行数：

```bash
wc -l /var/log/nginx/access.log
```

**访问量 Top10 IP**，这是最常考的一条，我拆开讲：

```bash
awk '{print $1}' /var/log/nginx/access.log | sort | uniq -c | sort -rn | head -n 10
```

逐段解释：`awk '{print $1}'` 把每行第一列（客户端 IP）抽出来；`sort` 先排序，让相同 IP 挨在一起；`uniq -c` 去重并在前面**统计每个 IP 出现次数**；`sort -rn` 按次数**数字倒序**排；`head -n 10` 取前 10。想算 UV（独立 IP 数）就把 `uniq -c` 换成 `sort -u | wc -l`。

**状态码分布**，看 200/404/502 各有多少：

```bash
awk '{print $9}' /var/log/nginx/access.log | sort | uniq -c | sort -rn
```

思路一模一样，只是抽第 9 列状态码。

**只看今天某时段、或只看 5xx**：

```bash
grep '30/Sep/2026' /var/log/nginx/access.log | awk '{print $9}' | grep -E '^5' | wc -l
```

解释：先 `grep` 出 9 月 30 日的行，再抽状态码，`grep -E '^5'` 筛出以 5 开头的 5xx，最后数行数。

我总结个口诀：**awk 抽列 → sort 相邻 → uniq -c 计数 → sort -rn 排序 → head 取前 N**，日志统计万变不离其宗。

---

### Q2：实时查看和过滤日志怎么做？

**我的答案：**

**实时跟日志**用 `tail -f`：

```bash
tail -f /var/log/nginx/access.log
```

加 `-n 200` 先看最后 200 行再跟。**边跟边过滤**就接 grep：

```bash
tail -f /var/log/nginx/access.log | grep -E '502|504'
```

`-E` 是扩展正则，一次匹配 502 和 504。想同时看上下文就 `grep -C 5 'error'`，`-C 5` 是匹配行前后各 5 行。

**查过去某段时间**不用 tail，用 grep 直接过滤时间段：

```bash
grep '30/Sep/2026:14:' /var/log/nginx/access.log
```

**systemd 管的服务**用 journalctl，比翻文件方便：

```bash
journalctl -u nginx -f              # 实时跟 nginx 服务日志
journalctl -u nginx --since "10 minutes ago"   # 最近 10 分钟
journalctl -u nginx -p err         # 只看 error 级别以上
```

**K8s 里看 Pod 日志**：

```bash
kubectl logs <pod-name> -f                    # 实时跟
kubectl logs <pod-name> --previous            # 容器崩溃前的上一个日志
kubectl logs <pod-name> -c <container>        # 多容器 Pod 指定容器
```

我现场排障的习惯是：先 `tail -f | grep` 盯着复现，复现到一条就拿关键字去 Kibana 搜全量，比在文件里盲翻快。

---

### Q3：批量查找和处理文件怎么做？

**我的答案：**

**按名字找文件**用 find：

```bash
find /var/log -name "*.log" -type f
```

`/var/log` 是查找起点，`-name` 按文件名（支持通配符），`-type f` 只要文件。按大小找（比如大于 100M 的大日志）：

```bash
find /var/log -type f -size +100M
```

**找到后批量处理**有两种接法。第一种 `find -exec`：

```bash
find /var/log -name "*.log" -mtime +30 -exec rm -f {} \;
```

解释：`-mtime +30` 是 30 天前改过的文件，`-exec ... {} \;` 对每个找到的文件执行删除，`{}` 代表找到的文件名。这就是个经典的"清理 30 天前日志"。

第二种更常用 `xargs`，把 find 的结果管道传给后面：

```bash
find /var/log -name "*.log" -mtime +30 -print0 | xargs -0 rm -f
```

`-print0`/`-0` 用空字符分隔文件名，防止文件名带空格被拆错。xargs 的好处是能控制并发和复用，比如批量打包：

```bash
find /data/backup -name "*.sql" -print0 | xargs -0 tar czf backup.tar.gz
```

**批量改配置**我一般先 `grep -rl "old_str" /etc/app/` 找出哪些文件含旧值，确认后再用 sed 批量替换：

```bash
grep -rl "192.168.1.10" /etc/app/ | xargs sed -i 's/192.168.1.10/10.0.0.5/g'
```

`sed -i` 直接改文件，`g` 全行替换。**生产上我一定会先不带 `-i` 跑一遍看替换结果，或者先备份，绝不在生产直接盲改。**

---

### Q4：跨多台机器批量执行命令怎么做？

**我的答案：**

**最简单的 for 循环**，靠 SSH 批量跑：

```bash
for ip in 10.0.0.{1..10}; do
  ssh root@$ip "hostname && uptime"
done
```

解释：`{1..10}` 是大展开，循环出 1 到 10 十个 IP；每台 ssh 过去跑 `hostname` 和 `uptime`。批量杀进程、批量看负载都这么干。想等结果就加 `< /dev/null` 防止交互卡住。

**要更稳就用 while 读 IP 列表文件**：

```bash
while read ip; do
  ssh -o ConnectTimeout=5 root@$ip "uptime"
done < hosts.txt
```

`-o ConnectTimeout=5` 是某台连不上别一直卡着。

**但正经生产我用 Ansible ad-hoc**，不用写剧本，一行命令管一组机器：

```bash
ansible web -m shell -a "uptime" -f 20
```

解释：`web` 是 inventory 里的主机组，`-m shell` 用 shell 模块，`-a` 是要执行的命令，`-f 20` 并发 20 台。批量装包：`ansible web -m yum -a "name=nginx state=latest"`；批量改服务：`ansible web -m service -a "name=nginx state=restarted"`。

我会对比着说：临时一次性操作用 for 循环或 ad-hoc，**重复要做、要幂等、要留痕的配置，一定要写成 Ansible playbook 而不是 shell 循环**——这也是 SRE 和"会写脚本"的区别。

---

## 相关链接

- [相关文档](/reference/linux-commands)
- [日志排查](/guide/linux-log)
