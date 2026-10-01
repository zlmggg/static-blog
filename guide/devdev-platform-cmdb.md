---
category: DevOps
difficulty: 中级
---

# 自研 CMDB 与资产管理

::: tip 本篇定位
从 0 搭一套够用的 **CMDB（配置管理数据库）**：主机/应用/负责人/环境四类资产建模、ER 关系、FastAPI + SQLAlchemy + MySQL 的 CRUD 完整骨架、SSH/云 API 自动采集、Vue 列表检索、以及最容易被忽略的**数据对账**。
本篇版本：FastAPI 0.141.1、SQLAlchemy 2.0.54、Pydantic 2.13.5、MySQL 8.4、Redis 7.4、Vue 3.5.43、paramiko 5.0.0（2026-09 官网稳定版）。
:::

## 一、CMDB 是干什么的

### 1.1 小白类比：公司资产的"户口本"

CMDB 就像给机房里每台机器、每个应用上户口：这台机器叫什么、IP 多少、归谁管、跑了哪个应用、在生产还是测试环境。没有它，故障时你只能在群里问"这个域名到底指到哪台机器"。

> 类比：CMDB 不是监控（监控告诉你"现在坏没坏"），而是**资产台账**（告诉你"它是什么、归谁、和谁有关系"）。它是后面所有平台（作业发布、工单、大屏）的**数据底座**。

### 1.2 四类核心资产与关系

| 资产 | 关键字段 | 说明 |
|---|---|---|
| 主机 Host | 主机名、IP、OS、CPU/内存、环境 | 一台物理机/虚拟机/容器节点 |
| 应用 App | 应用名、语言、负责人、仓库地址 | 一个业务系统 |
| 负责人 Owner | 姓名、团队、邮箱 | 人和团队 |
| 环境 Env | 环境名（prod/staging/dev） | 同一套应用在不同环境 |

关系：**一个应用部署在多台主机上；一台主机跑多个应用；应用归一个负责人；主机属于一个环境。**

## 二、ER 关系设计

```mermaid
erDiagram
    OWNER ||--o{ APP : "负责"
    APP }o--o{ HOST : "部署在"
    ENV ||--o{ HOST : "包含"
```

中间表 `app_host` 维护应用与主机的多对多关系（一个应用多台机器、一台机器多个应用）。各表字段见下文 `models.py`。

## 三、FastAPI + SQLAlchemy 完整骨架

下面是一个**可直接运行**的最小 CMDB 后端（本地用 SQLite 跑通，生产换 MySQL）。目录结构：

```
cmdb/
├── main.py          # FastAPI 入口与路由
├── models.py        # SQLAlchemy 模型
├── schemas.py       # Pydantic 请求/响应
└── database.py      # 连接与会话
```

### 3.1 database.py：连接与会话

```python
# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# 本地开发用 SQLite；生产换成 MySQL：
# mysql+pymysql://cmdb:你的密码@127.0.0.1:3306/cmdb?charset=utf8mb4
DATABASE_URL = "sqlite:///./cmdb.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 3.2 models.py：表结构（SQLAlchemy 2.0 语法）

```python
# models.py
from sqlalchemy import String, Integer, ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base

# 应用-主机 多对多中间表
app_host = Table(
    "app_host",
    Base.metadata,
    Column("app_id", ForeignKey("app.id"), primary_key=True),
    Column("host_id", ForeignKey("host.id"), primary_key=True),
)


class Owner(Base):
    __tablename__ = "owner"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    team: Mapped[str] = mapped_column(String(64))
    email: Mapped[str] = mapped_column(String(128))
    apps: Mapped[list["App"]] = relationship(back_populates="owner")


class Env(Base):
    __tablename__ = "env"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(32), unique=True)
    hosts: Mapped[list["Host"]] = relationship(back_populates="env")


class App(Base):
    __tablename__ = "app"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True)
    repo: Mapped[str] = mapped_column(String(256), default="")
    owner_id: Mapped[int] = mapped_column(ForeignKey("owner.id"))
    owner: Mapped["Owner"] = relationship(back_populates="apps")
    hosts: Mapped[list["Host"]] = relationship(secondary=app_host, back_populates="apps")


class Host(Base):
    __tablename__ = "host"
    id: Mapped[int] = mapped_column(primary_key=True)
    hostname: Mapped[str] = mapped_column(String(128), unique=True)
    ip: Mapped[str] = mapped_column(String(64), unique=True)
    os: Mapped[str] = mapped_column(String(64), default="")
    cpu: Mapped[int] = mapped_column(Integer, default=0)
    memory_gb: Mapped[int] = mapped_column(Integer, default=0)
    env_id: Mapped[int] = mapped_column(ForeignKey("env.id"))
    env: Mapped["Env"] = relationship(back_populates="hosts")
    apps: Mapped[list["App"]] = relationship(secondary=app_host, back_populates="hosts")
```

### 3.3 schemas.py：Pydantic 校验

```python
# schemas.py
from pydantic import BaseModel


class HostIn(BaseModel):
    hostname: str
    ip: str
    os: str = ""
    cpu: int = 0
    memory_gb: int = 0
    env_id: int


class HostOut(HostIn):
    id: int

    class Config:
        from_attributes = True


class AppIn(BaseModel):
    name: str
    repo: str = ""
    owner_id: int


class AppOut(AppIn):
    id: int

    class Config:
        from_attributes = True
```

### 3.4 main.py：CRUD 路由完整骨架

```python
# main.py
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select

from database import engine, Base, get_db
import models
import schemas

Base.metadata.create_all(bind=engine)
app = FastAPI(title="CMDB 资产平台", version="0.1.0")


@app.post("/api/hosts", response_model=schemas.HostOut)
def create_host(host: schemas.HostIn, db: Session = Depends(get_db)):
    row = models.Host(**host.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@app.get("/api/hosts", response_model=list[schemas.HostOut])
def list_hosts(
    env_id: int | None = None,
    keyword: str | None = Query(None, description="按主机名/IP 模糊搜"),
    db: Session = Depends(get_db),
):
    stmt = select(models.Host)
    if env_id is not None:
        stmt = stmt.where(models.Host.env_id == env_id)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(models.Host.hostname.like(like) | models.Host.ip.like(like))
    return db.scalars(stmt.order_by(models.Host.id)).all()


@app.get("/api/hosts/{host_id}")
def get_host(host_id: int, db: Session = Depends(get_db)):
    row = db.get(models.Host, host_id)
    if not row:
        raise HTTPException(status_code=404, detail="主机不存在")
    return {"id": row.id, "hostname": row.hostname, "ip": row.ip,
            "os": row.os, "cpu": row.cpu, "memory_gb": row.memory_gb,
            "env_id": row.env_id}


@app.put("/api/hosts/{host_id}", response_model=schemas.HostOut)
def update_host(host_id: int, data: schemas.HostIn, db: Session = Depends(get_db)):
    row = db.get(models.Host, host_id)
    if not row:
        raise HTTPException(status_code=404, detail="主机不存在")
    for k, v in data.model_dump().items():
        setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return row


@app.delete("/api/hosts/{host_id}")
def delete_host(host_id: int, db: Session = Depends(get_db)):
    row = db.get(models.Host, host_id)
    if not row:
        raise HTTPException(status_code=404, detail="主机不存在")
    db.delete(row)
    db.commit()
    return {"deleted": host_id}


@app.post("/api/apps", response_model=schemas.AppOut)
def create_app(app_in: schemas.AppIn, db: Session = Depends(get_db)):
    row = models.App(**app_in.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@app.get("/api/apps/{app_id}/hosts")
def app_hosts(app_id: int, db: Session = Depends(get_db)):
    stmt = select(models.App).where(models.App.id == app_id).options(
        selectinload(models.App.hosts))
    app_row = db.scalar(stmt)
    if not app_row:
        raise HTTPException(status_code=404, detail="应用不存在")
    return [{"id": h.id, "hostname": h.hostname, "ip": h.ip} for h in app_row.hosts]
```

### 3.5 启动与验证

```bash
pip install "fastapi==0.141.1" "sqlalchemy==2.0.54" "pydantic==2.13.5" "uvicorn>=0.30"
# 生产再加：pip install "pymysql>=1.1"
uvicorn main:app --reload --port 8000

# 建一条环境（用 SQL 或再加个 env 路由），再登记主机
curl -X POST http://127.0.0.1:8000/api/hosts -H "Content-Type: application/json" \
  -d '{"hostname":"web-01","ip":"10.0.0.11","os":"Rocky 9","cpu":16,"memory_gb":64,"env_id":1}'
curl "http://127.0.0.1:8000/api/hosts?keyword=web"
# 自动文档：http://127.0.0.1:8000/docs
```

::: warning 生产用 MySQL 时
把 `DATABASE_URL` 换成 `mysql+pymysql://...`，并在 MySQL 里预先建库：`CREATE DATABASE cmdb DEFAULT CHARSET utf8mb4;`。连接池建议加 `pool_size=10, max_overflow=20`。
:::

## 四、自动采集：别让人手填

CMDB 最大的死法是"靠人录入，三天就不准"。必须自动采集：

| 采集方式 | 适用 | 采集内容 | 实现 |
|---|---|---|---|
| SSH 采集 | 自有物理机/VM | 主机名、OS、CPU/内存、网卡 | paramiko 5.0.0 跑 `hostname`/`nproc`/`free` |
| Agent | 长期纳管 | 更细的磁盘、进程 | 在每台机装一个小 agent 上报 |
| 云 API | 云上 ECS/CVM | 实例列表、规格、公网 IP | 调云厂商 OpenAPI 全量拉取 |

### 4.1 SSH 采集骨架（paramiko）

```python
# collector.py —— 从一批机器采集硬件信息，回写 CMDB
import paramiko


def collect_one(host: str, user: str, key_path: str) -> dict:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=user, key_filename=key_path, timeout=5)
    cmds = {
        "hostname": "hostname",
        "os": "cat /etc/redhat-release 2>/dev/null || uname -a",
        "cpu": "nproc",
        "memory_gb": "free -g | awk '/Mem:/{print $2}'",
    }
    out = {}
    for k, c in cmds.items():
        _in, stdout, _err = client.exec_command(c)
        out[k] = stdout.read().decode().strip()
    client.close()
    out["cpu"] = int(out["cpu"] or 0)
    out["memory_gb"] = int(out["memory_gb"] or 0)
    return out
```

采集到的数据**不要直接覆盖人工字段**，而是写进"采集快照"，和人工登记的字段做对账（见第六节）。

## 五、Vue 列表与检索前端

最小前端：一个搜索框 + 一个表格，调上面的 `/api/hosts`。

```vue
<!-- HostList.vue  Vue 3.5.43：搜索框 + 表格 -->
<template>
  <div>
    <input v-model="keyword" placeholder="按主机名/IP 搜索" @keyup.enter="load" />
    <button @click="load">查询</button>
    <table border="1">
      <thead><tr><th>主机名</th><th>IP</th><th>OS</th><th>CPU</th><th>内存G</th></tr></thead>
      <tbody>
        <tr v-for="h in hosts" :key="h.id">
          <td>{{ h.hostname }}</td><td>{{ h.ip }}</td><td>{{ h.os }}</td><td>{{ h.cpu }}</td><td>{{ h.memory_gb }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
<script setup>
import { ref } from "vue";
const hosts = ref([]), keyword = ref("");
async function load() {
  const r = await fetch(`/api/hosts?keyword=${encodeURIComponent(keyword.value)}`);
  hosts.value = await r.json();
}
load();
</script>
```

::: tip 前后端联调
开发时在 Vite 的 `vite.config.js` 配 `server.proxy` 把 `/api` 转发到 `http://127.0.0.1:8000` 避免跨域；更复杂的图表见 [工单与监控大屏](./devdev-ticket-dashboard)。
:::

## 六、数据一致性与对账

CMDB 能不能用，**90% 取决于数据准不准**，而不是功能多不多。

```mermaid
flowchart LR
    A["云API/SSH 采集"] --> S["采集快照表"]
    H["人工登记"] --> T["资产主表"]
    S --> C{"对账比对"}
    T --> C
    C -->|一致| OK["标记已对齐"]
    C -->|不一致| D["差异清单<br>邮件/钉钉通知 Owner"]
    C -->|主表有采集无| G["疑似已下线<br>标记待回收"]
```

对账规则（写一个每日跑的定时任务，见 [任务调度与 API 产品化](./devdev-scheduler-api)）：

| 差异类型 | 判定 | 处理 |
|---|---|---|
| 主表有、采集不到 | 机器可能已下线 | 标记"待回收"，通知 Owner |
| 采集到、主表没有 | 新机器没登记 | 生成"待入库"差异单 |
| CPU/内存对不上 | 规格变更 | 以采集值为准，记录变更历史 |

::: warning 生产红线
- 采集账号用**最小权限的只读账号 + SSH 密钥**，禁止用 root 密码；密钥走 [密钥管理](./devops-secrets)。
- 自动采集只写"快照"，**不直接删主表记录**——下线要走审批，防止误删真实资产。
- 所有变更（谁改了 IP、谁删了主机）写审计日志，见 [任务调度与权限审计](./devdev-scheduler-api)。
- 版本写死：`sqlalchemy==2.0.54`、`pydantic==2.13.5`，不要用 `latest`。
:::

## 七、常见问题排错

| 现象 | 原因 | 解决 |
|---|---|---|
| `no such table: host` | 没建表 | 确认 `Base.metadata.create_all(bind=engine)` 已执行 |
| MySQL 连接 `Authentication plugin` 报错 | 驱动/账号插件不兼容 | 用 pymysql 1.x，账号用 `caching_sha2_password` 或改 `mysql_native_password` |
| 中文主机名乱码 | 库/表不是 utf8mb4 | 建库指定 `CHARSET utf8mb4`，连接串加 `charset=utf8mb4` |
| 列表查询 N+1 慢 | 关联对象没预加载 | 用 `selectinload`（见 `/api/apps/{id}/hosts`） |
| 采集连不上但手动 ssh 可以 | 密钥路径/权限 | 私钥权限必须 600；确认 `key_filename` 路径 |
| 前端跨域 | 后端没开 CORS | FastAPI 加 `CORSMiddleware` 允许前端域名 |

## 相关速查

- 语言基础：[Python 运维自动化](./sre-python)
- 平台工程定位：[平台工程与 IDP](./devops-platform-engineering)
- 采集任务定时调度：[任务调度与 API 产品化](./devdev-scheduler-api)
- 云原生资源查询：[云原生命令速查](/reference/cloudnative-commands)

### 官方文档

- FastAPI 文档：https://fastapi.tiangolo.com/
- SQLAlchemy 2.0 ORM：https://docs.sqlalchemy.org/en/20/
- Pydantic 文档：https://docs.pydantic.dev/
- MySQL 8.4 文档：https://dev.mysql.com/doc/refman/8.4/en/
- paramiko 文档：https://www.paramiko.org/
- Vue 文档：https://cn.vuejs.org/
