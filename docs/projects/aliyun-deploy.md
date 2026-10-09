---
category: 项目
difficulty: 中级
date: 2026-10-09
---

# 阿里云个人站点部署与运维

> 在一台阿里云 ECS 上，从挂数据盘开始，用 Docker Compose 把 Nginx 站点和监控跑起来，并完成基础加固。

## 一、背景 / 目标

一台新的阿里云 ECS（主机名 `hg-blog`），系统盘空间有限。目标：

- 加一块数据盘，把站点、配置、日志、容器编排都放到数据盘，和系统盘隔离；
- 用 Docker Compose 管理 Nginx 与监控，配置即代码、可重建；
- 主机做最小化加固，监控不暴露公网。

## 二、环境 / 目录规划

数据盘（20G，`/dev/vdb1`）挂载到 `/data`，统一目录：

```text
/data
├─ compose/docker-compose.yml   # 容器编排
├─ nginx/
│  ├─ conf.d/                   # Nginx 站点配置（www.conf 等）
│  ├─ snippets/                 # 可复用配置片段
│  └─ auth/                     # Basic Auth 密码文件（已逐步弃用）
├─ certs/                       # TLS 证书
├─ www/                         # 主站静态文件（容器只读挂载）
├─ private/                     # 原私有站内容（已弃用）
└─ logs/nginx/                  # Nginx 日志
```

## 三、容器编排（Docker Compose）

两个服务，网络隔离：

| 容器 | 镜像 | 端口 | 说明 |
|---|---|---|---|
| `edge-nginx` | `nginx:alpine` | 80 / 443 | 边缘 Web，配置 / 站点 / 证书全部只读挂载 |
| `netdata` | `netdata/netdata` | `127.0.0.1:19999` | 只绑本地回环，用 SSH 隧道访问，不暴露公网 |

```bash
# 本地隧道访问监控（在自己电脑执行）
ssh -p 22022 -L 19999:127.0.0.1:19999 zlmggg@<服务器IP>
# 然后浏览器打开 http://localhost:19999
```

## 四、主机加固

- **SSH**：端口改为 `22022`，禁用密码登录、只用 ed25519 密钥。
- **监控最小暴露**：Netdata 只监听回环，靠 SSH 隧道访问。
- **Nginx**：隐藏版本号（`server_tokens off`），拦截 `.git/.env/备份压缩包` 等敏感路径，80 跳 443。
- **容器资源**：给容器设 `mem_limit`，`restart: always` 保证开机自启。

## 五、踩过的坑

- **Docker swap 限制不生效**：`docker info` 报 `No swap limit support`，需在内核启动参数加 `swapaccount=1` 后重启。详见 [这篇记录](/cases/t-docker-swap)。
- **地域 IP 白名单误伤爬虫**：曾用「境外 IP 一律拦截 + Basic Auth」，结果误伤 Bing / Google 爬虫，影响收录 → 移除白名单和密码，改为只按扫描特征拦截。

## 六、成果 / 复盘

- 站点与监控容器化运行，配置和内容都在数据盘，重建 / 迁移只需备份 `/data` 与 Compose 文件。
- 待补：Nginx 安全响应头（HSTS、X-Content-Type-Options）、静态资源 immutable 缓存、基于访问日志的分析（GoAccess）。

## 七、相关链接

- 站点本身：[禾光知寒站点](./site-blog)
- 线上：[https://www.sresec.com](https://www.sresec.com)
