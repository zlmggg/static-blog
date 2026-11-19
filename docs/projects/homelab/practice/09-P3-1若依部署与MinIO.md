# 09 · P3-1：若依微服务部署 + MinIO

| 项目 | 内容 |
|---|---|
| **所属阶段** | P3（第三天） |
| **前置条件** | P3-0 完成：Nacos 3 节点 UP、日志链路通 |
| **预计耗时** | 2 小时（第一次编译+踩坑） |
| **完成标志** | 浏览器 `http://192.168.10.119` 打开若依登录页，`admin/【实验密码】` 能进；**上传头像后 MinIO 桶里有文件** |
| **下一步** | `10-P3-2若依接入ES.md` |

> **零代码改动**：MinIO 是若依 `ruoyi-file` **原生支持**的存储后端，只改 Nacos 里的配置。
> 参考：[若依官方-分布式文件](https://doc.ruoyi.vip/ruoyi-cloud/cloud/file.html)

**部署分布（复用 4 台 app）：**

| VM | 服务 | 端口 |
|---|---|---|
| app-blue-01 (130) | nacos-1 + **gateway** | 8080 |
| app-blue-02 (131) | nacos-2 + **auth** | 9200 |
| app-green-01 (132) | nacos-3 + **system** | 9201 |
| app-green-02 (133) | **file** + 构建机 | 9300 |

---

## 本步需要的资料

| 类型 | 名称 | 从哪来 |
|---|---|---|
| 下载 | RuoYi-Cloud **v3.6.5** 源码 | gitee.com/y_project/RuoYi-Cloud |
| 下载 | Temurin JDK **8** | 清华 Adoptium 镜像 |
| 下载 | Node.js **16** | deb.nodesource.com |
| 账号 | 若依默认 `admin` / `【实验密码】` | 源码 SQL 内置 |
| 前置 | Nacos 3 节点 UP | 08 的产物 |

> 总表（含版本、下载地址、账号规则）见 [`00-资料清单.md`](/projects/homelab/materials)。

---

## 步骤 0 · 准备构建机（20 分钟）

**在哪台**：app-green-02（133）
**目的**：装 JDK8、Maven、Node16，拉源码
**开始前**：P3-0 验收通过

**操作**：

1. 停掉 07 的占位应用（四台都停，8080 要留给网关）：

```bash
# 在 bastion 上执行（ubuntu）
ansible app -m shell -a 'systemctl disable --now edu-app 2>/dev/null; echo done' --become
```

2. 装 JDK8（Ubuntu 24.04 仓库没有 8，用清华镜像的 Temurin）：

```bash
# 在 app-green-02 上执行（ubuntu）
sudo apt install -y maven git unzip
mkdir -p /opt/jdk8 && cd /tmp
URL=$(curl -s https://mirrors.tuna.tsinghua.edu.cn/Adoptium/8/jdk/x64/linux/ \
  | grep -o 'OpenJDK8U-jdk_x64_linux_hotspot_[^"]*\.tar\.gz' | sort -V | tail -1)
echo "下载：$URL"
wget -q "https://mirrors.tuna.tsinghua.edu.cn/Adoptium/8/jdk/x64/linux/$URL" -O jdk8.tar.gz
sudo tar xzf jdk8.tar.gz -C /opt/jdk8 --strip-components=1
/opt/jdk8/bin/java -version
```

**应该看到**：`openjdk version "1.8.0_4xx"`。

3. 拉源码：

```bash
# 在 app-green-02 上执行（ubuntu）
cd /opt
sudo git clone -b v3.6.5 --depth 1 https://gitee.com/y_project/RuoYi-Cloud.git
sudo chown -R ubuntu:ubuntu /opt/RuoYi-Cloud
ls /opt/RuoYi-Cloud
```

**应该看到**：`ruoyi-gateway`、`ruoyi-auth`、`ruoyi-modules`、`ruoyi-ui`、`sql` 等目录。

**失败怎么办**：
- 下载 JDK 为空 → 浏览器打开镜像目录，手动找文件名替换 `URL=`
- `git clone` 失败 → 换 `https://github.com/yangzongzhuan/RuoYi-Cloud.git`

---

## 步骤 1 · 建库并导入 SQL（15 分钟）

**在哪台**：mysql-01（150）
**目的**：建若依业务库，并把 Nacos 配置种子导进 Nacos 的库
**开始前**：步骤 0 的源码已就位（`sql/` 目录里有两个脚本）

**操作**：

1. 看脚本名字：

```bash
# 在 app-green-02 上执行（ubuntu）
ls /opt/RuoYi-Cloud/sql/
```

**应该看到**：两个文件，一个是 `ry_2025xxxx.sql`（业务），一个是 `ry_config_2025xxxx.sql`（Nacos 配置）。

2. 传到 mysql-01：

```bash
# 在 bastion 上执行（ubuntu）
scp ubuntu@10.0.0.133:/opt/RuoYi-Cloud/sql/ry_2025*.sql     /tmp/ry.sql
scp ubuntu@10.0.0.133:/opt/RuoYi-Cloud/sql/ry_config_2025*.sql /tmp/ry_config.sql
scp /tmp/ry.sql /tmp/ry_config.sql ubuntu@10.0.0.150:/tmp/
```

3. 建库导入：

```bash
# 在 mysql-01 上执行（ubuntu）
sudo mysql <<'SQL'
CREATE DATABASE IF NOT EXISTS `ry-cloud` DEFAULT CHARSET utf8mb4;
CREATE USER IF NOT EXISTS 'ry'@'10.0.0.%' IDENTIFIED BY '【实验密码】';
GRANT ALL PRIVILEGES ON `ry-cloud`.* TO 'ry'@'10.0.0.%';
FLUSH PRIVILEGES;
SQL

sudo mysql ry-cloud < /tmp/ry.sql
sudo mysql nacos_config < /tmp/ry_config.sql
sudo mysql -e "USE \`ry-cloud\`; SHOW TABLES;" | head -20
sudo mysql -e "USE nacos_config; SELECT COUNT(*) FROM config_info;"
```

**应该看到**：业务表 `sys_user`、`sys_menu` 等；`config_info` 有几十条（若依的配置）。

**失败怎么办**：
- `config_info` 还是 0 → 导入错库，确认导进的是 `nacos_config`
- 表已存在报错 → SQL 是 `CREATE TABLE` 不带 IF NOT EXISTS，先 `DROP DATABASE` 重来

---

## 步骤 2 · 确认 Nacos 命名空间（5 分钟）

**在哪台**：Windows（SSH 隧道）+ 浏览器
**目的**：若依的配置在 `ry-config` 命名空间下，ID 必须完全一致
**开始前**：步骤 1 的 config_info 有数据

**操作**：

```powershell
# 在 Windows PowerShell 里执行（保持窗口不关）
ssh -L 8848:10.0.0.130:8848 root@192.168.10.30
```

浏览器打开 <http://127.0.0.1:8848/nacos> → 左侧 `命名空间`。

**应该看到**：有一个 **命名空间 ID 为 `ry-config`** 的条目。

如果没有：

1. 点 `新建命名空间`
2. **命名空间 ID 必须手动填 `ry-config`**（不要留空让它自动生成 UUID）
3. 命名空间名填 `ry-config`，保存

再回 `配置管理`，命名空间切到 `ry-config`，**应该看到几十条配置**（`ruoyi-gateway-dev.yml`、`ruoyi-auth-dev.yml`、`ruoyi-system-dev.yml`、`ruoyi-file-dev.yml` 等）。

**失败怎么办**：
- 配置列表空的 → `ry_config.sql` 没导进去，回步骤 1
- 命名空间 ID 是 UUID → 删掉重建，ID 手填 `ry-config`

---

## 步骤 3 · 编译后端（20 分钟）

**在哪台**：app-green-02（133）
**目的**：打出 4 个可执行 jar
**开始前**：步骤 0 的 JDK 和源码就位

**操作**：

```bash
# 在 app-green-02 上执行（ubuntu）
cd /opt/RuoYi-Cloud
export JAVA_HOME=/opt/jdk8
mvn -q clean package -DskipTests -T 1C
ls -lh ruoyi-gateway/target/*.jar ruoyi-auth/target/*.jar \
       ruoyi-modules/ruoyi-system/target/*.jar ruoyi-modules/ruoyi-file/target/*.jar
```

**应该看到**：4 个 jar，每个 30–80MB。

**失败怎么办**：
- `Could not resolve dependencies` → Maven 中央仓库慢，改 `~/.m2/settings.xml` 用阿里云镜像
- `invalid target release: 1.8` → JAVA_HOME 没设对，`echo $JAVA_HOME` 确认是 `/opt/jdk8`
- 内存不足被杀 → `free -m` 看，`MAVEN_OPTS="-Xmx1024m"`

---

## 步骤 4 · 部署 4 个服务（25 分钟）

**在哪台**：130 / 131 / 132 / 133
**目的**：每个 VM 跑一个服务，用 systemd 托管
**开始前**：步骤 3 的 4 个 jar 都在

**操作**：

1. 在 133 上把 jar 归位：

```bash
# 在 app-green-02 上执行（ubuntu）
sudo mkdir -p /opt/ruoyi
sudo cp /opt/RuoYi-Cloud/ruoyi-gateway/target/*.jar        /opt/ruoyi/gateway.jar
sudo cp /opt/RuoYi-Cloud/ruoyi-auth/target/*.jar           /opt/ruoyi/auth.jar
sudo cp /opt/RuoYi-Cloud/ruoyi-modules/ruoyi-system/target/*.jar /opt/ruoyi/system.jar
sudo cp /opt/RuoYi-Cloud/ruoyi-modules/ruoyi-file/target/*.jar   /opt/ruoyi/file.jar
sudo chown -R ubuntu:ubuntu /opt/ruoyi
```

2. 分发到另外三台：

```bash
# 在 app-green-02 上执行（ubuntu）
sudo mkdir -p /opt/ruoyi
scp /opt/ruoyi/gateway.jar ubuntu@10.0.0.130:/tmp/
scp /opt/ruoyi/auth.jar    ubuntu@10.0.0.131:/tmp/
scp /opt/ruoyi/system.jar  ubuntu@10.0.0.132:/tmp/
```

3. 在 **每台** 上建 systemd 单元（以 130 的 gateway 为例，其余换名字和 jar）：

```bash
# 在 app-blue-01 上执行（ubuntu）
sudo mkdir -p /opt/ruoyi
sudo mv /tmp/gateway.jar /opt/ruoyi/
sudo tee /etc/systemd/system/ruoyi-gateway.service >/dev/null <<'EOF'
[Unit]
Description=RuoYi Gateway
After=network-online.target

[Service]
User=ubuntu
WorkingDirectory=/opt/ruoyi
Environment=JAVA_HOME=/opt/jdk8
Environment=SPRING_PROFILES_ACTIVE=dev
Environment=SPRING_CLOUD_NACOS_SERVER_ADDR=10.0.0.130:8848
ExecStart=/opt/jdk8/bin/java -Xms256m -Xmx512m -jar /opt/ruoyi/gateway.jar
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable --now ruoyi-gateway
```

> 130 上还没有 JDK8！需要把 `/opt/jdk8` 从 133 拷过去，或用 ansible 下发。
> 下面的命令一次搞定：把 JDK 和 systemd 单元都推过去。

```bash
# 在 app-green-02 上执行（ubuntu）—— 把 JDK 推到另外三台
for ip in 10.0.0.130 10.0.0.131 10.0.0.132; do
  rsync -a --delete /opt/jdk8/ ubuntu@$ip:/opt/jdk8/
done
```

4. 其余三台的单元（**分别在其上执行**）：

| 在哪台 | jar | 服务名 | 端口（网关路由里已定） |
|---|---|---|---|
| 131 | auth.jar | ruoyi-auth | 9200 |
| 132 | system.jar | ruoyi-system | 9201 |
| 133 | file.jar | ruoyi-file | 9300 |

```bash
# 在 app-blue-02 上执行（ubuntu）—— auth
sudo mv /tmp/auth.jar /opt/ruoyi/
sudo tee /etc/systemd/system/ruoyi-auth.service >/dev/null <<'EOF'
[Unit]
Description=RuoYi Auth
After=network-online.target
[Service]
User=ubuntu
WorkingDirectory=/opt/ruoyi
Environment=JAVA_HOME=/opt/jdk8
Environment=SPRING_PROFILES_ACTIVE=dev
Environment=SPRING_CLOUD_NACOS_SERVER_ADDR=10.0.0.130:8848
ExecStart=/opt/jdk8/bin/java -Xms256m -Xmx512m -jar /opt/ruoyi/auth.jar
Restart=always
RestartSec=5
[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload && sudo systemctl enable --now ruoyi-auth
```

```bash
# 在 app-green-01 上执行（ubuntu）—— system
sudo mv /tmp/system.jar /opt/ruoyi/
sudo tee /etc/systemd/system/ruoyi-system.service >/dev/null <<'EOF'
[Unit]
Description=RuoYi System
After=network-online.target
[Service]
User=ubuntu
WorkingDirectory=/opt/ruoyi
Environment=JAVA_HOME=/opt/jdk8
Environment=SPRING_PROFILES_ACTIVE=dev
Environment=SPRING_CLOUD_NACOS_SERVER_ADDR=10.0.0.130:8848
ExecStart=/opt/jdk8/bin/java -Xms256m -Xmx512m -jar /opt/ruoyi/system.jar
Restart=always
RestartSec=5
[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload && sudo systemctl enable --now ruoyi-system
```

```bash
# 在 app-green-02 上执行（ubuntu）—— file（jar 已经在 /opt/ruoyi）
sudo tee /etc/systemd/system/ruoyi-file.service >/dev/null <<'EOF'
[Unit]
Description=RuoYi File
After=network-online.target
[Service]
User=ubuntu
WorkingDirectory=/opt/ruoyi
Environment=JAVA_HOME=/opt/jdk8
Environment=SPRING_PROFILES_ACTIVE=dev
Environment=SPRING_CLOUD_NACOS_SERVER_ADDR=10.0.0.130:8848
ExecStart=/opt/jdk8/bin/java -Xms256m -Xmx512m -jar /opt/ruoyi/file.jar
Restart=always
RestartSec=5
[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload && sudo systemctl enable --now ruoyi-file
```

5. 等 30 秒，在 Nacos 控制台看服务列表：

`服务管理` → `服务列表`，**应该看到** `ruoyi-gateway`、`ruoyi-auth`、`ruoyi-system`、`ruoyi-file` 四个服务，实例数都是 1。

**失败怎么办**：
- 服务没注册 → `journalctl -u ruoyi-xxx -n 50`，多半是连不上 Nacos 或数据库
- 端口冲突 → `ss -lntp | grep 8080`，edu-app 没停
- `No such file /opt/jdk8/bin/java` → rsync 没成功，重跑

---

## 步骤 5 · 编译前端并挂到 Nginx（20 分钟）

**在哪台**：133 编译 → 120/121 部署
**目的**：把若依的 Vue 前端放到你的 Nginx 上，走 VIP 访问
**开始前**：步骤 4 的服务都注册了

**操作**：

1. 装 Node 16 并编译：

```bash
# 在 app-green-02 上执行（ubuntu）
curl -fsSL https://deb.nodesource.com/setup_16.x | sudo -E bash -
sudo apt install -y nodejs
node -v

cd /opt/RuoYi-Cloud/ruoyi-ui
npm install --registry=https://registry.npmmirror.com
npm run build:prod
ls -lh dist/
```

**应该看到**：`dist/` 里有 `index.html`、`static/`。

2. 传到两台 Nginx：

```bash
# 在 app-green-02 上执行（ubuntu）
for ip in 10.0.0.120 10.0.0.121; do
  rsync -a --delete dist/ ubuntu@$ip:/tmp/ruoyi-dist/
done
```

```bash
# 在 nginx-01 上执行（ubuntu）—— 121 同样执行
sudo mkdir -p /usr/share/nginx/html/ruoyi
sudo rsync -a --delete /tmp/ruoyi-dist/ /usr/share/nginx/html/ruoyi/
sudo chown -R www-data:www-data /usr/share/nginx/html/ruoyi
```

3. 改 Nginx 配置（**替换掉 07 的 Flask 反代**）：

```bash
# 在 nginx-01 上执行（ubuntu）—— 121 同样执行
sudo rm -f /etc/nginx/conf.d/00-upstream.conf /etc/nginx/conf.d/10-server.conf
sudo tee /etc/nginx/conf.d/ruoyi.conf >/dev/null <<'EOF'
server {
    listen 80 default_server;
    server_name _;

    root /usr/share/nginx/html/ruoyi;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /prod-api/ {
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_pass http://10.0.0.130:8080/;
    }
}
EOF

sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1/
```

**应该看到**：`200`。

4. 浏览器打开 **<http://192.168.10.119>**，用 `admin` / `【实验密码】` 登录。

**应该看到**：若依后台首页，左侧菜单（系统管理、系统监控等）。

**失败怎么办**：
- 页面 404 → `try_files` 没生效，确认 `root` 指向 dist 的上一级目录
- 登录接口 404 → `curl -s -XPOST http://10.0.0.130:8080/auth/login` 试直连网关
- 登录提示"验证码错误" → 浏览器缓存，强刷
- 页面白屏 → 打开 F12 看 `/prod-api` 请求是否 404

---

## 步骤 6 · 接 MinIO（15 分钟）

**在哪台**：Nacos 控制台 + 终端
**目的**：把文件存储从本地切换到 MinIO，**只改配置**
**开始前**：步骤 5 能登录

**操作**：

1. 在 MinIO 上建桶并设为可读：

```bash
# 在 minio-01 上执行（ubuntu）
mc mb lab/ruoyi || true
mc anonymous set download lab/ruoyi
mc ls lab
```

**应该看到**：`ruoyi/` 桶。

2. 在 Nacos 里改配置：

浏览器（走隧道）<http://127.0.0.1:8848/nacos> → 命名空间 `ry-config` → 配置 `ruoyi-file-dev.yml` → 编辑。

把里面的两段改成：

```yaml
# 本地存储（注释掉）
# local:
#   path: /home/ruoyi/uploadPath
#   prefix: /statics

# MinIO
minio:
  url: http://10.0.0.170:9000
  accessKey: admin
  secretKey: 【实验密码】
  bucketName: ruoyi
```

保存并发布。

> 若依通过"哪个配置存在"来决定用哪种存储：启用 `minio` 段、注释 `local` 段即可，代码不用动。

3. 重启 file 服务让它拉新配置：

```bash
# 在 app-green-02 上执行（ubuntu）
sudo systemctl restart ruoyi-file
sleep 5
sudo journalctl -u ruoyi-file -n 20 --no-pager | grep -i minio
```

**应该看到**：没有报错（或 `Minio` 相关初始化日志）。

---

## 步骤 7 · 验证上传（5 分钟）

**在哪台**：Windows 浏览器
**目的**：证明文件真的进了 MinIO

**操作**：

1. 登录若依 → 右上角头像 → `个人中心` → `修改头像` → 上传一张图片 → 保存。

**应该看到**：头像变了，图片能显示（浏览器直接访问 `http://10.0.0.170:9000/ruoyi/...`，Windows 有 10.0.0.0/24 的路由，能通）。

2. 在 MinIO 上确认对象：

```bash
# 在 minio-01 上执行（ubuntu）
mc ls --recursive lab/ruoyi | tail
```

**应该看到**：一条 `.../2026/11/16/xxx.png` 之类的对象。

**失败怎么办**：
- 上传报 500 → `journalctl -u ruoyi-file -n 50`，多半是 accessKey/secretKey 或桶名错
- 上传成功但图片不显示 → 桶没设 `download` 策略
- `Access Denied` → MinIO 账号密码与配置不一致

---

## P3-1 验收清单

- [ ] Nacos 服务列表有 4 个 ruoyi 服务，各 1 个实例
- [ ] `http://192.168.10.119` 打开登录页，`admin/【实验密码】` 能进
- [ ] 左侧菜单能点开"系统管理 → 用户管理"，列表有数据
- [ ] 修改头像成功
- [ ] `mc ls --recursive lab/ruoyi` 能看到上传的文件
- [ ] `journalctl -u ruoyi-*` 没有持续报错

**全部打勾后** → 进入 `10-P3-2若依接入ES.md`。
