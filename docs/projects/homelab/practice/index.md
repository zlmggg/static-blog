# 10-实操：部署上线 13 项

> 本目录是项目的主输出：从 PVE 底座开始，按 D0 → P5 的顺序把整套架构部署上线。每一篇都按“在哪台 / 目的 / 开始前 / 操作 / 应该看到 / 失败怎么办 / 验收”组织，可以独立照着执行。
>
> 架构说明见 [项目架构](/projects/homelab)；版本、地址和附件见 [资料清单](/projects/homelab/materials)。

## 一、13 项总表

| 步 | 阶段 | 这一步建什么 | 架构落点 | 做完后的业务结果 | 文档 | 预计 |
|---|---|---|---|---|---|---|
| 1 | D0 | PVE 底座、私网、EIP、模板 9000 | 虚拟化与网络底座 | 能克隆 VM，后续所有节点有统一模板 | [01-D0-装机与PVE初始化](/projects/homelab/practice/01-D0-装机与PVE初始化) | 2.5h |
| 2 | P0 | bastion、DNS、Ansible 三节点 | 管理面 | 机器可批量初始化、内网域名可解析 | [02-D1-P0管理平面](/projects/homelab/practice/02-D1-P0管理平面) | 40min |
| 3 | P1 | LVS、Nginx、App、MySQL、Redis、Prometheus、Grafana | 最小业务链路 | Windows 能打开 VIP 页面，请求能走到数据库 | [03-D1-P1最小链路](/projects/homelab/practice/03-D1-P1最小链路) | 2–3h |
| 4 | P1.5 | JumpServer | 运维审计入口 | 人能通过堡垒机登录，操作有录像 | [04-D1-P15堡垒机](/projects/homelab/practice/04-D1-P15堡垒机) | 40–60min |
| 5 | P2-1 | MySQL 一主两从、Redis 三哨兵 | 数据高可用 | 数据库复制可验证，缓存可自动选主 | [05-D2-P2-1数据层高可用](/projects/homelab/practice/05-D2-P2-1数据层高可用) | 90min |
| 6 | P2-2 | MinIO 3 节点 6 盘、ES 3 节点 | 对象存储与搜索 | 文件能存对象，日志/搜索有索引 | [06-D2-P2-2对象存储与搜索](/projects/homelab/practice/06-D2-P2-2对象存储与搜索) | 90min |
| 7 | P2-3 | Nginx upstream 蓝绿 | 发布机制 | 能在 blue/green 之间切流并回滚 | [07-D2-P2-3蓝绿发布](/projects/homelab/practice/07-D2-P2-3蓝绿发布) | 60min |
| 8 | P3-0 | Nacos 3 节点、Filebeat/Logstash | 注册配置与日志 | 微服务能注册，日志能进 ES | [08-P3-0中间件Nacos与日志](/projects/homelab/practice/08-P3-0中间件Nacos与日志) | 60min |
| 9 | P3-1 | 若依微服务、MinIO 文件后端 | 真实业务应用 | 若依登录、头像上传落 MinIO | [09-P3-1若依部署与MinIO](/projects/homelab/practice/09-P3-1若依部署与MinIO) | 2h |
| 10 | P3-2 | 若依接入 ES | 业务搜索 | 课程/内容搜索走 ES | [10-P3-2若依接入ES](/projects/homelab/practice/10-P3-2若依接入ES) | 60min |
| 11 | P3-3 | 若依网关级蓝绿 | 业务发布 | 若依能在 VIP 上切版本、回滚 | [11-P3-3若依蓝绿发布](/projects/homelab/practice/11-P3-3若依蓝绿发布) | 45min |
| 12 | P4 | K8s 5 节点、Nacos StatefulSet、若依服务 | 部分上 K8s | Nacos 和若依服务跑在 K8s，VIP 仍可用 | [12-P4-K8s迁移](/projects/homelab/practice/12-P4-K8s迁移) | 3–4h |
| 13 | P5 | mall-swarm 电商链路 | 真实业务扩展 | 商品搜索、图片、订单消息跑通 | [13-P5-mall-swarm](/projects/homelab/practice/13-P5-mall-swarm) | 1–2 天 |

## 二、按架构阶段理解

- **D0：底座**。先把虚拟化、私网、EIP、模板做对；后面所有节点都从这个模板克隆。
- **P0：管理面**。bastion 做 DNS 和 Ansible 主控，另外两台做备控/执行；先让机器能被统一管理。
- **P1：最小业务闭环**。只做“VIP → Nginx → App → MySQL/Redis”，目标是先让页面打开，不追求完整高可用。
- **P1.5：审计入口**。JumpServer 负责人对机器的登录、授权和录像；和 bastion 的机器入口分开。
- **P2：数据与发布机制**。MySQL 主从、Redis 哨兵、MinIO、ES、蓝绿 upstream 在这一阶段补齐。
- **P3：真实业务**。Nacos、若依、MinIO 文件、ES 搜索、网关蓝绿，把“能打开页面”升级成“能运行业务”。
- **P4：部分上 K8s**。只迁 Nacos 和若依服务，数据层继续留在 VM；不把所有组件塞进 K8s。
- **P5：真实电商链路**。mall-swarm 补商品、订单、搜索、消息，验证更复杂的业务形态。

## 三、做之前先看

- [项目架构](/projects/homelab)：先理解六层、三条流和节点结构，再动手。
- [资料清单](/projects/homelab/materials)：版本、下载地址、仓库附件、账号规则。
- 每篇实操开头的“前置条件”必须满足，再进入下一步。

## 四、两条顺序提醒

> **P4 之前必须先确认“要做 K8s 迁移业务”**，把 Docker 里的 Nacos 和若依服务迁进 K8s，不要直接开写。
>
> **P5 放在若依之后**：先用若依把中间件和业务链路跑顺，再上 mall-swarm 补真实业务场景，顺序不能反。
