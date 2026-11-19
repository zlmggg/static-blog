# 08 · P3-0：中间件（Nacos 集群 + 日志链路）

| 项目 | 内容 |
|---|---|
| **所属阶段** | P3（第三天） |
| **前置条件** | P2 全部完成；app-blue/green 四台可用 |
| **预计耗时** | 60 分钟 |
| **完成标志** | Nacos 控制台显示 **3 个节点**；Kibana 里能按主机名搜到 syslog |
| **下一步** | `09-P3-1若依部署与MinIO.md` |

**这一步不放新 VM，复用 app 组四台：**

| VM | IP | 跑什么 |
|---|---|---|
| app-blue-01 | 10.0.0.130 | nacos-1 + gateway（09 再装） |
| app-blue-02 | 10.0.0.131 | nacos-2 + auth（09） |
| app-green-01 | 10.0.0.132 | nacos-3 + system（09） |
| app-green-02 | 10.0.0.133 | 构建机 + job/file（09） |

> Nacos 三个节点都用 Docker 跑（`--network host`），P4 再迁进 K8s。

---

## 本步需要的资料

| 类型 | 名称 | 从哪来 |
|---|---|---|
| 下载 | `nacos/nacos-server:v2.3.2` 镜像 | docker pull |
| 下载 | Logstash / Filebeat **7.17** | artifacts.elastic.co |
| 账号 | MySQL `nacos` / `【实验密码】` | 本步创建 |
| 前置 | ES 集群 green | 06 的产物 |

> 总表（含版本、下载地址、账号规则）见 [`00-资料清单.md`](/projects/homelab/materials)。

---

## 步骤 0 · 开始前检查（3 分钟）

**在哪台**：bastion（ubuntu）
**目的**：确认四台 app 可用、内存够
**开始前**：P2 验收通过

**操作**：

```bash
# 在 bastion 上执行（ubuntu）
cd ~/ansible
ansible app -m shell -a 'free -m | awk "/Mem:/{print \$4}"'
```

**应该看到**：四台各返回一个数字，**每台 ≥ 1500**（MB）。

**失败怎么办**：
- 某台可用内存 < 1000 → 上面还有 Flask 的 edu-app 在跑，`systemctl stop edu-app`（07 的占位应用可以停了）

---

## 步骤 1 · 三台装 Docker（10 分钟）

**在哪台**：130 / 131 / 132
**目的**：用 Docker 跑 Nacos，省去装 JDK 和调参
**开始前**：步骤 0 通过

**操作**：

```bash
# 在 bastion 上执行（ubuntu）—— 三台一起装
ansible app_blue,app_green -m shell -a \
  'apt-get install -y docker.io >/dev/null && systemctl enable --now docker && docker --version' \
  --become --limit '10.0.0.130,10.0.0.131,10.0.0.132'
```

**应该看到**：三行 `Docker version 24.x`。

拉一下镜像（三台都要，比较慢）：

```bash
# 在 bastion 上执行（ubuntu）
ansible app_blue,app_green -m shell -a 'docker pull nacos/nacos-server:v2.3.2' \
  --become --limit '10.0.0.130,10.0.0.131,10.0.0.132'
```

**应该看到**：`Status: Downloaded newer image for nacos/nacos-server:v2.3.2`。

**失败怎么办**：
- `docker pull` 卡住 → 配镜像加速器：`/etc/docker/daemon.json` 加 `{"registry-mirrors":["https://你的加速器"]}`，`systemctl restart docker`
- `apt` 装不上 → 换 apt 源

---

## 步骤 2 · MySQL 建 Nacos 库（10 分钟）

**在哪台**：mysql-01（150）
**目的**：Nacos 集群模式必须用外部数据库
**开始前**：步骤 1 能拉到镜像

**操作**：

1. 从镜像里取出建表脚本（在 app-blue-01 上执行）：

```bash
# 在 app-blue-01 上执行（ubuntu）
sudo docker run --rm --entrypoint cat nacos/nacos-server:v2.3.2 \
  /home/nacos/conf/mysql-schema.sql > /tmp/nacos-schema.sql
wc -l /tmp/nacos-schema.sql
```

**应该看到**：几百行（文件非空）。

2. 传到 mysql-01 并导入：

```bash
# 在 bastion 上执行（ubuntu）
scp ubuntu@10.0.0.130:/tmp/nacos-schema.sql /tmp/
scp /tmp/nacos-schema.sql ubuntu@10.0.0.150:/tmp/

ssh ubuntu@10.0.0.150 "sudo mysql <<'SQL'
CREATE DATABASE IF NOT EXISTS nacos_config DEFAULT CHARSET utf8mb4;
CREATE USER IF NOT EXISTS 'nacos'@'10.0.0.%' IDENTIFIED BY '【实验密码】';
GRANT ALL PRIVILEGES ON nacos_config.* TO 'nacos'@'10.0.0.%';
FLUSH PRIVILEGES;
SQL"
```

```bash
# 在 mysql-01 上执行（ubuntu）
sudo mysql nacos_config < /tmp/nacos-schema.sql
sudo mysql -e "USE nacos_config; SHOW TABLES;" | head
```

**应该看到**：`config_info`、`users`、`roles` 等表。

**失败怎么办**：
- `docker run ... cat` 报文件不存在 → `docker run --rm --entrypoint ls nacos/nacos-server:v2.3.2 /home/nacos/conf` 找实际文件名
- 导入报语法错 → 文件被截断，重取一次

---

## 步骤 3 · 起 3 个 Nacos（15 分钟）

**在哪台**：130 / 131 / 132
**目的**：组成 3 节点集群
**开始前**：步骤 2 的库表已建好

**操作**：

```bash
# 在 bastion 上执行（ubuntu）—— 三台的命令只有 IP 不同，用 ansible 一次下发
ansible app_blue,app_green -m shell -a \
  'docker rm -f nacos 2>/dev/null; \
   docker run -d --name nacos --restart always --network host \
     -e MODE=cluster \
     -e NACOS_SERVERS="10.0.0.130:8848 10.0.0.131:8848 10.0.0.132:8848" \
     -e SPRING_DATASOURCE_PLATFORM=mysql \
     -e MYSQL_SERVICE_HOST=10.0.0.150 \
     -e MYSQL_SERVICE_DB_NAME=nacos_config \
     -e MYSQL_SERVICE_USER=nacos \
     -e MYSQL_SERVICE_PASSWORD=【实验密码】 \
     -e NACOS_AUTH_ENABLE=false \
     -e JVM_XMS=512m -e JVM_XMX=512m -e JVM_XMN=256m \
     nacos/nacos-server:v2.3.2' \
  --become --limit '10.0.0.130,10.0.0.131,10.0.0.132'
```

**应该看到**：三行容器 ID。

等 30 秒，看健康状态：

```bash
# 在 bastion 上执行（ubuntu）
for ip in 10.0.0.130 10.0.0.131 10.0.0.132; do
  echo -n "$ip: "; curl -s http://$ip:8848/nacos/v1/console/health/readiness; echo
done
```

**应该看到**：三行 `UP`。

**失败怎么办**：
- 一直起不来 → `docker logs nacos --tail 50`，多半是连不上 MySQL
- `Connection refused` 到 3306 → 确认 mysql-01 的 `bind-address` 是 0.0.0.0
- 内存不够被 OOM → `docker stats --no-stream`，把 JVM_XMX 降到 384m

---

## 步骤 4 · 验证 Nacos 集群（5 分钟）

**在哪台**：Windows 浏览器
**目的**：确认三节点互相注册成功

**操作**：

1. 浏览器打开 **<http://192.168.10.130:8848/nacos>**（走 EIP，130 没有 EIP —— 改用管理通道：**<http://10.0.0.130:8848/nacos>** 不行，浏览器不在内网）。

> 130 没有 EIP。用 SSH 隧道最稳：在 Windows PowerShell 执行
> `ssh -L 8848:10.0.0.130:8848 root@192.168.10.30`
> 然后浏览器打开 <http://127.0.0.1:8848/nacos>

2. 登录（未开鉴权，直接进）→ 左侧 `集群管理` → `节点列表`

**应该看到**：3 个节点，`状态` 都是 UP。

3. 建一个测试配置：`配置管理` → `配置列表` → `+`，Data ID `test.yml`，Group `DEFAULT_GROUP`，内容 `hello: world`，发布。

```bash
# 在 bastion 上执行（ubuntu）—— 用 API 验证配置能读到
curl -s "http://10.0.0.130:8848/nacos/v1/cs/configs?dataId=test.yml&group=DEFAULT_GROUP"
```

**应该看到**：`hello: world`。

**失败怎么办**：
- 只有 1 个节点 → `docker logs nacos | grep -i "cluster"`，看 cluster.conf 是否生成
- 控制台打不开 → 换隧道端口，或直接 `curl` 验证

---

## 步骤 5 · Logstash（10 分钟）

**在哪台**：es-03（182）
**目的**：接收 Filebeat 的日志，写进 ES
**开始前**：06 的 ES 集群是 green

**操作**：

```bash
# 在 bastion 上执行（ubuntu）
ssh ubuntu@10.0.0.182
```

```bash
# 在 es-03 上执行（ubuntu）
sudo apt install -y logstash

sudo tee /etc/logstash/conf.d/lab.conf >/dev/null <<'EOF'
input {
  beats { port => 5044 }
}

output {
  elasticsearch {
    hosts => ["http://10.0.0.180:9200", "http://10.0.0.181:9200", "http://10.0.0.182:9200"]
    index => "lab-logs-%{+YYYY.MM.dd}"
    manage_template => false
  }
}
EOF

sudo systemctl enable --now logstash
sleep 20
sudo systemctl is-active logstash
ss -lntp | grep 5044
```

**应该看到**：`active`；`0.0.0.0:5044` 在监听。

**失败怎么办**：
- `active` 但 5044 没起 → `sudo journalctl -u logstash -n 50`，配置语法错会明确报行号
- 内存不够 → `free -m`，Logstash 默认吃 1G，`/etc/logstash/jvm.options` 改 `-Xms512m -Xmx512m`

---

## 步骤 6 · Filebeat 全量采集（10 分钟）

**在哪台**：bastion（下发）+ 所有 VM
**目的**：把每台的 syslog/auth.log 收上来
**开始前**：步骤 5 的 5044 在监听

**操作**：

1. 在 bastion 上准备配置文件：

```bash
# 在 bastion 上执行（ubuntu）
cat > ~/filebeat.yml <<'EOF'
filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - /var/log/syslog
      - /var/log/auth.log

output.logstash:
  hosts: ["10.0.0.182:5044"]

logging.level: warning
EOF
```

2. 所有机器装 Filebeat（走 Elastic 7.x 源）：

```bash
# 在 bastion 上执行（ubuntu）
ansible all -m shell -a \
  'curl -s https://artifacts.elastic.co/GPG-KEY-elasticsearch | gpg --dearmor -o /usr/share/keyrings/elastic.gpg; \
   echo "deb [signed-by=/usr/share/keyrings/elastic.gpg] https://artifacts.elastic.co/packages/7.x/apt stable main" > /etc/apt/sources.list.d/elastic-7.x.list; \
   apt-get update -qq && apt-get install -y filebeat >/dev/null && filebeat version' \
  --become
```

**应该看到**：每台一行 `filebeat version 7.17.x`。

3. 下发配置并启动：

```bash
# 在 bastion 上执行（ubuntu）
ansible all -m copy -a "src=/home/ubuntu/filebeat.yml dest=/etc/filebeat/filebeat.yml" --become
ansible all -m shell -a "systemctl enable --now filebeat && systemctl restart filebeat" --become
```

**应该看到**：全部 `changed`，没有 `FAILED`。

**失败怎么办**：
- 某台装不上 → `ansible <host> -m shell -a 'apt-get update' --become -vvv` 看报错
- filebeat 起不来 → `journalctl -u filebeat -n 30`，多半是 yml 缩进

---

## 步骤 7 · Kibana 看日志（5 分钟）

**在哪台**：Windows 浏览器
**目的**：确认日志真的进了 ES

**操作**：

1. 浏览器 <http://192.168.10.191:5601> → 左侧 `Stack Management` → `Index Patterns` → `Create index pattern` → 输入 `lab-logs-*` → 时间字段选 `@timestamp` → 创建。
2. 左侧 `Discover`，右上时间选 `Last 15 minutes`。

**应该看到**：一条条日志，字段里有 `agent.hostname`（哪台机器）、`message`。

验证 ES 里也有索引：

```bash
# 在 bastion 上执行（ubuntu）
curl -s "http://10.0.0.180:9200/_cat/indices/lab-logs-*?v"
```

**应该看到**：`lab-logs-2026.11.16` 之类，`docs.count` 大于 0。

**失败怎么办**：
- Kibana 里没数据 → 先看 ES 有没有索引；没有就 `journalctl -u logstash -n 30` 看有没有收到 beats
- 有索引但 Kibana 看不到 → 时间范围选错了

---

## P3-0 验收清单

- [ ] 三台 Nacos 的 readiness 都是 `UP`
- [ ] Nacos 控制台"节点列表"显示 3 个节点
- [ ] 能发布并读取一个测试配置
- [ ] Logstash `active`，5044 在监听
- [ ] 所有 VM 的 filebeat 都是 `active`
- [ ] Kibana 能按 `agent.hostname` 搜到日志
- [ ] ES 里有 `lab-logs-*` 索引且 docs.count > 0

**全部打勾后** → 进入 `09-P3-1若依部署与MinIO.md`。
