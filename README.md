<div align="center">

# 禾光知寒 · SRE Notes

**一个基于 VitePress 的个人 SRE 运维知识库 —— 命令手册 · 服务详解 · 部署方案 · 排障记录**

[在线站点](https://www.sresec.com) · [快速开始](#-快速开始) · [内容结构](#-内容结构-v4) · [代码结构](#-代码结构与功能说明) · [部署上线](#-部署上线)

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![VitePress](https://img.shields.io/badge/VitePress-1.6-64a36b.svg)
![Node](https://img.shields.io/badge/node-%3E%3D18-339933.svg)
![Version](https://img.shields.io/badge/version-V4-2563EB.svg)

</div>

---

## 简介

禾光知寒（SRE Notes）是一个用 [VitePress](https://vitepress.dev/zh/) 构建的个人运维知识库，Markdown 驱动、构建为纯静态站点，通过 Docker + Nginx 部署。

**V4 是一次完整重构**：从"零散文章合集"收敛为「命令手册 · 服务详解 · 部署方案」三大可检索体系，保留「排障记录」与「我的项目」两条实践线。内容以可查、可抄、可复现为标准，不是概念科普。

> 建这个库的初衷，是让自己遇到问题时能快速搜到、快速回忆处理方法；也希望这些能直接抄走的方案，帮到同样在路上的运维同学。

## ✨ 特性

- **命令手册（OS 级 9 组）**：文本与文件、用户与权限、系统与进程、磁盘与存储、网络、观测排障、包管理、Shell、开发工具，230+ 条命令。每条含中文详解、常用参数、易错点，降低英文 `--help` 阅读门槛；
- **服务详解（7 组 22 个服务）**：接入与网络 / 数据库与缓存 / 中间件 / 容器与编排 / 存储与搜索 / CI-CD 与自动化 / 监控与日志。大服务统一「理论 → 部署 → 功能 → 实战」四段：理论讲原理与请求生命周期，功能与实战的每条规则都配「为什么」；
- **部署方案**：先给形态矩阵（单机 / 主备 / 集群 / 容器）与选型依据，再给 6 套可直接落地的组合（LB 高可用、MySQL 主从、Redis 哨兵、CI/CD 流水线、监控栈、日志栈）；
- **排障记录**：单页聚合索引，按分类列出编号记录（`L/N/S/M/R/D/K/SEC-序号`），点详情看完整「现象 → 定位 → 根因 → 验证」链路，统一编号不用日期；
- **我的项目**：真实落地的项目架构与实操记录，技能与项目互证；
- **Mermaid 图表**：浏览器端动态加载、跟随深浅色主题，不进首屏包；
- **本地全文搜索**：`Ctrl + K` 纯前端搜索（MiniSearch），无需服务端；
- **深色护眼主题**：玻璃态导航、终端风格首页、深浅色一键切换；
- **纯静态 + 容器化部署**：多阶段 Dockerfile 构建，版本目录 + 原子软链发布，可回滚。

## 🧱 内容结构（V4）

```text
docs/
├─ commands/            # 命令手册：9 组 OS 级命令
│  ├─ basic/            # 文本与文件
│  ├─ identity/         # 用户与权限
│  ├─ system/           # 系统与进程
│  ├─ storage/          # 磁盘与存储
│  ├─ network/          # 网络
│  ├─ observe/          # 观测与排障
│  ├─ package/          # 包管理
│  ├─ shell/            # Shell 编程
│  └─ devtools/         # 开发工具
├─ services/            # 服务详解：7 组 22 个服务
│  ├─ web/              # 接入与网络（Nginx / LVS+Keepalived / HAProxy / DNS）
│  ├─ database/         # 数据库与缓存（MySQL / Redis）
│  ├─ middleware/       # 中间件（Nacos / Kafka / RabbitMQ）
│  ├─ container/        # 容器与编排（Docker / Compose / K8s / Helm / Harbor）
│  ├─ storage-search/   # 存储与搜索（MinIO / Elasticsearch）
│  ├─ cicd/             # CI/CD 与自动化（GitLab / Jenkins / Ansible）
│  └─ observability/    # 监控与日志（Prometheus / Grafana / Alertmanager / ELK）
├─ deploy/              # 部署方案：形态矩阵 + 6 套组合
├─ cases/               # 排障记录：聚合索引 + 编号详情子页
├─ projects/            # 我的项目：架构、实操、资料
├─ guide/               # 运维手记：博客 / 职业 / 进阶
└─ reference/           # 旧版速查页（保留兼容，逐步并入命令手册）
```

## 🧩 代码结构与功能说明

这一节讲清楚每个组件、脚本、配置文件分别负责什么，方便定位「想改某个效果，该动哪个文件」。

### 1. 主题入口 `theme/index.ts`

- 继承 VitePress 默认主题，挂载自定义 `Layout`；
- 全局注册两个组件：`Mermaid`（图表）、`Home`（首页）；
- 引入全局样式 `custom.css`。

### 2. 全局布局中枢 `theme/Layout.vue`

| 功能区 | 作用 |
|---|---|
| 主题切换 `provide('toggle-appearance')` | 从点击位置**圆形涟漪扩散**切换深浅色（View Transitions API）；浏览器不支持时直接切换 |
| 右侧大纲自动滚动 | 监听大纲激活项变化，把当前标题滚进可视区；切换路由时重置 |
| 复制按钮增强 | 给代码块复制按钮注入「复制 / ✓ 已复制」；用 MutationObserver 应对 SPA 路由切换后的新按钮 |
| 插槽挂载 | `#layout-top` 全局背景、`#doc-before` 元信息条、`#nav-bar-content-after` 主题按钮、`#layout-bottom` 页脚 |

页脚内容（构建说明 / 版权 / 备案号）在这个文件的 `#layout-bottom` 插槽里。

### 3. 首页组件 `theme/components/Home.vue`（改动最频繁）

**`<script>` 数据与逻辑：**

| 区块 | 作用 |
|---|---|
| `STATS` | 构建时用 `import.meta.glob` 自动扫描 md 统计（技术文档 / 命令详解 / 排障案例 / 知识专题），无需手改数字 |
| 终端动画 | `SCRIPTS` 是演示数据；`typeCmd` 打字机、`addOut` 彩色输出、`runTerm` 循环播放；系统开启「减少动态效果」时用静态展示 |
| `FEATS` | 第二屏内容分类数据（标题 / 描述 / 图标 / 跳转） |
| `PROJECTS` | 「我的项目」卡片数据 |
| `animateCount` | 统计数字进入视口时从 0 滚动到目标值 |
| `go()` / `openSearch()` | 卡片跳转路由 / 触发搜索框 |

**`<template>` 结构（从上到下）：**

- `.first-screen`（首屏）：Hero（徽标 / 标题 / 描述 / 按钮 + 终端）→ 统计条 → 搜索框 → 向下箭头；
- `.projects`：我的项目卡片；
- `#features`：内容分类列表。

**`<style>`（非 scoped）：** 全部以 `.home-root` 作命名空间，只作用于首页。

### 4. 文章元信息条 `theme/components/MetaBar.vue`

- 读取 frontmatter 的 `category` / `difficulty` / `date`，显示在 H1 上方；
- 三者全缺时组件不渲染（聚合页、索引页因此不出现空条）；
- 难度色标：初级绿 / 中级黄 / 高级红；
- **阅读时长自动估算**：中文约 380 字/分钟、代码等约 300 字符/分钟。

### 5. 主题切换按钮 `theme/components/ThemeToggle.vue`

调用 Layout 注入的切换方法，内含太阳 / 月亮两套 SVG。

### 6. Mermaid 图表 `theme/Mermaid.vue`

- 只在浏览器端**动态 `import('mermaid')`、且只加载一次**（不进首屏、不影响构建）；
- 初始化与渲染进入**全局串行队列**，杜绝多图并发竞态；
- 离屏容器渲染，避免临时节点残留；失败重试一次；切换深浅色后防抖重绘；
- 大图自适应，超高图限高 80vh，超宽可横向滚动。

### 7. 全局样式 `theme/custom.css`

| 注释块 | 控制的内容 |
|---|---|
| 字体与设计 token | 字体栈、品牌色 `--brand-*`、圆角 |
| 全局背景 | `.bg-fx`：网格 + 三团光晕（深浅色分别设置） |
| 玻璃态变量 | 导航、卡片、搜索弹窗共用参数 |
| 导航 / 侧边栏 / 大纲 | 三栏宽度、间距、对齐 |
| 正文排版 | 标题、段落、列表、引用 |
| 表格 | 圆角表格、`idx` 索引表、悬停高亮 |
| 代码块 | `--cb-body/head/border/blur`、标题栏、tabs、复制按钮 |
| 自定义容器 | callout、提示块 |
| 滚动条 / 响应式 | 全站滚动条、窄屏与移动端适配 |

### 8. 站点配置 `.vitepress/config.mts`

| 配置块 | 作用 |
|---|---|
| 基础信息 | `lang` / `title` / `description` |
| `vite` | `chunkSizeWarningLimit` 打包体积阈值 |
| `lastUpdated` / `sitemap` | 页脚最后更新时间（取 Git 提交）、自动生成站点地图 |
| `head` | favicon、RSS 自动发现、字体样式表 |
| `appearance` | 默认深色主题 |
| `markdown.languageAlias` | 把 conf / promql / cron 等别名到内置语法 |
| `markdown.config` | 注册 `idx` 容器；` ```mermaid ` 转成 `<Mermaid>`；含 `{{ }}` 的行内代码加 `v-pre` |
| `themeConfig` | logo、顶部 `nav`、左侧 `sidebar`（服务详解按 7 组折叠）、右侧 `outline`、搜索、中文文案 |

### 9. RSS 生成脚本 `scripts/gen-feed.mjs`

- 在 `vitepress build` 之后自动运行（挂在 `package.json` 的 build 命令里）；
- 扫描带 frontmatter `date` 的文章（项目文章与指南，自动排除聚合页），按日期倒序取最新 20 篇生成 `feed.xml`；
- 排障记录按 V4 规范**用编号不用日期**，因此不进按日期排序的订阅源。

### 10. 部署文件 `deploy/`

| 文件 | 作用 |
|---|---|
| `Dockerfile` | 多阶段构建：Node 阶段编译站点 → Nginx 阶段托管静态产物 |
| `docker-compose.yml` | 一条命令构建并运行容器（映射 8080 端口） |
| `nginx.conf` | 静态站配置：安全响应头、gzip、带 hash 资源长缓存、路由回退 |
| `云服务器部署现状核对-20261115.md` | 线上服务器只读核对记录（架构、权限、备份、待修项） |

## 🚀 快速开始

环境要求：[Node.js](https://nodejs.org/) **18 或更高版本**。

```bash
# 1. 安装依赖（国内可加 --registry=https://registry.npmmirror.com）
npm install

# 2. 启动本地开发服务器
npm run dev

# 3. 构建静态产物 / 本地预览
npm run build
npm run preview
```

构建产物在 `docs/.vitepress/dist`。

## 🎨 自定义（改成你自己的站）

**1. 站点信息** —— `docs/.vitepress/config.mts`

| 配置项 | 作用 |
|---|---|
| `title` | 站点名称（导航最左、标签页标题） |
| `description` | 站点描述（利于 SEO） |
| `themeConfig.logo` | 导航栏 Logo |
| `themeConfig.nav` | 顶部导航 |
| `themeConfig.sidebar` | 左侧导航（服务详解已按 7 组折叠） |

**2. 配色与玻璃态** —— `docs/.vitepress/theme/custom.css`

顶部 `:root`（浅色）与 `.dark`（深色）是主题 CSS 变量；背景光晕、玻璃态、代码块、表格的透明度都在这里，注释有说明。

**3. Logo 与插图** —— `docs/public/`

- `logo.svg`：站点 Logo（导航 + favicon 共用）；
- `hero-ops.png`：首页插图。

**4. 内容**

按 V4 结构往 `commands/`、`services/`、`deploy/`、`cases/`、`projects/` 对应分组新建 `.md`。文件名用英文（URL 更专业），与中文标题的对照见 [FILES.md](FILES.md)。

**写一篇新文章**：在对应板块新建 `.md`，顶部可加 frontmatter：

```yaml
---
category: Linux          # 分类，显示为元信息条
difficulty: 初级          # 难度：初级 / 中级 / 高级
date: 2026-11-20         # 日期（可选，项目/指南文章用于 RSS；排障记录用编号不用日期）
---
```

阅读时长由 `MetaBar` 根据正文长度自动估算，无需手写。

**新增服务页**：复制四段模板（`01-理论` / `02-部署` / `03-功能` / `04-实战`），再在 `config.mts` 的服务分组里加条目。深度标准是「理论讲原理与请求生命周期，规则配为什么」。

## 📦 部署上线

### 方式一：Docker（推荐）

在**项目根目录**执行：

```bash
docker build -f deploy/Dockerfile -t sre-notes .
docker run -d -p 8080:80 --name sre-notes sre-notes
```

或 docker-compose：

```bash
docker compose -f deploy/docker-compose.yml up -d --build
```

### 方式二：静态托管

把 `docs/.vitepress/dist` 整个目录上传到任意静态服务器、对象存储或 Pages 服务。Nginx 配置示例见 [`deploy/nginx.conf`](deploy/nginx.conf)。

### 方式三：版本目录 + 原子切换（本站线上做法）

```bash
# 本地构建并打包
npm run build && tar czf dist.tar.gz -C docs/.vitepress/dist .
scp -P 22022 -i ~/.ssh/sersec_ed25519 dist.tar.gz zlmggg@<服务器IP>:~/

# 服务器：解压成新版本目录 → 接统计软链 → 原子切换 current → 保留最近 5 版
sudo /data/deploy.sh /home/zlmggg/dist.tar.gz
sudo /data/rollback.sh     # 回滚到上一版本
```

## 🤝 致谢

- [VitePress](https://vitepress.dev/zh/)：本站的构建框架；
- 内容编写与技术排障由 [豆包 Doubao](https://www.doubao.com) 辅助完成。

## 📄 License

基于 [MIT License](LICENSE) 开源，欢迎自由使用与修改。
