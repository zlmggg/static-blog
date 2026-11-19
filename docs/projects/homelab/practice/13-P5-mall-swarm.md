# 13 · P5：mall-swarm（真实业务场景）

> # 🧠 记忆点
>
> **这一篇是"若依全流程跑通之后"的加餐。**
> 顺序不能反：先用若依把 Nacos / 网关 / 主从 / 哨兵 / MinIO / ES 全部跑顺，
> 再用 mall-swarm 补"真实电商业务"（商品搜索、图片存储、订单消息、多模块编译）。
>
> 如果若依还没跑通就上 mall-swarm，你会同时面对"中间件没通"和"业务本身复杂"两类问题，排错会崩溃。

| 项目 | 内容 |
|---|---|
| **所属阶段** | P5（加分项） |
| **前置条件** | P4 完成；若依已在 K8s 里能登录 |
| **预计耗时** | 1–2 天（第一次） |
| **完成标志** | mall-admin 前端能登录、商品列表能搜、图片能上传 |
| **下一步** | 无（这是最后一块） |

---

## 一、为什么要上 mall-swarm

若依是"**管理系统脚手架**"：菜单、权限、字典、代码生成——它把**中间件**用起来了，但**业务**很薄。

mall-swarm 是"**电商业务系统**"：商品、订单、购物车、搜索、支付——它把**业务链路**用起来了。

| 对比项 | 若依 RuoYi-Cloud | mall-swarm |
|---|---|---|
| 定位 | 后台管理脚手架 | 电商业务系统 |
| 服务数 | 4（gateway/auth/system/file） | 6–7（gateway/auth/admin/portal/search/monitor） |
| 用 ES 的方式 | 旁路（Logstash 同步） | **业务原生**（商品搜索走 ES） |
| 用对象存储 | 文件服务（MinIO） | **商品图片**（OSS/MinIO） |
| 用消息队列 | 无 | **RabbitMQ**（订单超时取消） |
| 前端 | Vue admin | Vue admin + uni-app（H5） |
| 适合验证 | 权限、配置中心、文件 | **搜索、异步、多模块、读写分离** |

> 一句话：**若依让你证明"我会搭"，mall-swarm 让你证明"我搭的东西能跑真业务"。**

---

## 二、版本怎么选（先定这个，后面全跟着变）

mall-swarm 有两个分支：

| 分支 | 技术栈 | JDK | 适合 |
|---|---|---|---|
| `master` | Spring Cloud 2023/2025 + Spring Boot 3.2/3.5 + Sa-Token | **17** | 新，但要重新装 JDK17 |
| `dev-v2` | Spring Cloud 2021 + Spring Boot 2.7 + OAuth2 | **8** | 复用你已有的 JDK8 |

**推荐 `master` + JDK17**：Ubuntu 24.04 仓库直接有 `openjdk-17-jdk`，比折腾 JDK8 省事；而且你已有 Nacos 2.3、ES 7.17，都能对上。

> 具体版本号、模块端口以你 clone 下来那一刻的 `README.md` 和 `pom.xml` 为准——**第一次启动后把实际端口记录到本文档第十节**。

---

## 三、新增的组件（相对若依）

| 组件 | 怎么来 | 放哪 |
|---|---|---|
| JDK 17 | `apt install openjdk-17-jdk` | 5 台 K8s + 构建机 |
| RabbitMQ | Docker `rabbitmq:3-management` | app-green-02（133） |
| mall 数据库 | `mall.sql`（源码 `document/sql/`） | mysql-01 |
| ES 索引 | `mall_search` | 已有的 ES 集群 |
| Nacos 配置 | 源码 `config/` 目录下的 yml | 导入 `ry-config` 之外新建 `mall-config` 命名空间 |

> RabbitMQ 不上新 VM，用 Docker 跑在 133 上，端口 5672/15672。
> 如果要"消息队列也高可用"，那得再加 2 台——那是 P5.5 的事，先不做。

---

## 本步需要的资料

| 类型 | 名称 | 从哪来 |
|---|---|---|
| 下载 | mall-swarm 源码（**master** 分支） | gitee.com/macrozheng/mall-swarm |
| 下载 | OpenJDK **17** | apt |
| 下载 | `rabbitmq:3-management` 镜像 | docker hub |
| 数据 | `mall.sql` | 源码 `document/sql/` |

> 总表（含版本、下载地址、账号规则）见 [`00-资料清单.md`](/projects/homelab/materials)。

---

## 四、执行骨架（9 步）

### 步骤 1 · 装 JDK17 和 RabbitMQ

```bash
# 在 app-green-02 上执行（ubuntu）
sudo apt install -y openjdk-17-jdk
java -version

sudo apt install -y docker.io
sudo systemctl enable --now docker
sudo docker run -d --name rabbitmq --restart always \
  -p 5672:5672 -p 15672:15672 \
  -e RABBITMQ_DEFAULT_USER=admin \
  -e RABBITMQ_DEFAULT_PASS='【实验密码】' \
  rabbitmq:3-management
```

**验收**：`java -version` 显示 17；浏览器（走隧道或 EIP）`http://10.0.0.133:15672` 能登录。

### 步骤 2 · 建库导入

```bash
# 在 mysql-01 上执行（ubuntu）
sudo mysql <<'SQL'
CREATE DATABASE IF NOT EXISTS mall DEFAULT CHARSET utf8mb4;
CREATE USER IF NOT EXISTS 'mall'@'10.0.0.%' IDENTIFIED BY '【实验密码】';
GRANT ALL PRIVILEGES ON mall.* TO 'mall'@'10.0.0.%';
FLUSH PRIVILEGES;
SQL
sudo mysql mall < /tmp/mall.sql
```

**验收**：`USE mall; SHOW TABLES;` 有 `pms_product`、`oms_order` 等表。

### 步骤 3 · 拉源码并编译

```bash
# 在 app-green-02 上执行（ubuntu）
cd /opt
sudo git clone --depth 1 https://gitee.com/macrozheng/mall-swarm.git
sudo chown -R ubuntu:ubuntu mall-swarm
cd mall-swarm
mvn -q clean package -DskipTests
```

**验收**：各模块 `target/*.jar` 生成。

### 步骤 4 · 导入 Nacos 配置

源码里的 `config/` 目录是"要导进 Nacos 的配置"：

1. Nacos 控制台 → 命名空间 → 新建，**ID 填 `mall-config`**
2. `配置管理` → 导入 → 选 `config/` 下的 yml（逐个或打包导入）
3. 把里面的 MySQL / Redis / ES / RabbitMQ 地址改成你的 IP

**验收**：`mall-config` 命名空间下能看到 `mall-admin-dev.yml` 等配置。

### 步骤 5 · 起服务

按依赖顺序起：`mall-gateway` → `mall-auth` → `mall-admin` / `mall-portal` / `mall-search`。

```bash
# 在 app-green-02 上执行（ubuntu）—— 示例：mall-admin
nohup java -Xms256m -Xmx512m -jar mall-admin/target/*.jar \
  --spring.profiles.active=dev > /tmp/mall-admin.log 2>&1 &
```

**验收**：Nacos 服务列表出现 5 个 `mall-*` 服务。

### 步骤 6 · 建 ES 索引

```bash
# 在 bastion 上执行（ubuntu）
curl -s -XPUT "http://10.0.0.180:9200/mall_search" -H 'Content-Type: application/json' -d '
{"settings":{"number_of_shards":3,"number_of_replicas":1}}'
```

然后在 mall-admin 后台点"商品 → 导入 ES"（或调 `/esProduct/importAll` 接口）。

**验收**：`curl 10.0.0.180:9200/mall_search/_count` 有数据。

### 步骤 7 · 前端

- `mall-admin-web`（Vue）：单独 clone，`npm install && npm run build` → 放 Nginx
- `mall-app-web`（uni-app）：H5 模式构建 → 也能放 Nginx，手机浏览器打开

**验收**：浏览器登录 mall-admin，能看商品列表。

### 步骤 8 · 图片走 MinIO

mall 的 OSS 配置支持 MinIO（在 `mall-config` 的配置里改 `oss` 段，指向 `http://10.0.0.170:9000` + 桶 `mall`）。

**验收**：后台上传商品图，MinIO 桶里能看到对象。

### 步骤 9 · 收尾

- 把实际端口、镜像名、Nacos 命名空间记录到本文档
- 给 mall 相关 Pod/进程加监控（Prometheus 的 `node_exporter` 已覆盖主机层）

---

## 五、和若依的取舍（方案说明）

- **若依**：先把 Nacos 集群、MySQL 主从、Redis 哨兵、MinIO、ES 旁路跑顺，验证的是中间件和运维链路。
- **mall-swarm**：再跑真实电商链路，商品搜索走 ES、图片走 MinIO、订单走 RabbitMQ，验证的是业务链路。
- 两者解决的是不同问题，不是替代关系；先若依后 mall，是为了把中间件问题与业务问题分开定位。

---

## 六、风险与待确认（**第一次做之前先看**）

| 风险 | 说明 | 应对 |
|---|---|---|
| 版本漂移 | master 分支一直在升级（SC2023→2025、SB3.2→3.5） | 以 clone 下来的 `pom.xml` 为准，别照抄网上旧教程 |
| 端口不确定 | 各模块端口在 `application.yml` 里 | 第一次启动后 `ss -lntp` 记录，填回本文档 |
| 配置导入麻烦 | `config/` 下 yml 多，手动导易漏 | 用 Nacos 的"导入"功能整包导 |
| ES 版本 | mall 要求 ES 7.x（你已有 7.17） | 不用动 |
| 内存 | 6 个 JVM × 512M ≈ 3G + RabbitMQ 500M | 133 只有 3G，可能不够；建议把 mall 服务分散到 220/221 或先用 2 个模块试 |

> **建议**：第一次只起 `gateway + auth + admin` 三个，跑通再补 `portal`/`search`。别一上来全启。

---

## 七、完成标志

- [ ] `mall-admin` 能登录，商品列表有数据
- [ ] 商品搜索走 ES，能搜到
- [ ] 商品图片在 MinIO 里
- [ ] RabbitMQ 管理界面能看到队列
- [ ] 实际端口/版本已记录到本文档

**到这一步，整个实验环境就闭环了：从一台裸机到能跑真实业务的微服务集群。**
