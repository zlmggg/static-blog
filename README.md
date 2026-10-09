<div align="center">

# 禾光知寒 · SRE Notes

**一个基于 VitePress 的个人 SRE 运维知识库 —— 操作指南 · 命令速查 · 排障训练 · 面试整理**

[在线站点](https://www.sresec.com) · [快速开始](#-快速开始) · [代码结构](#-代码结构与功能说明) · [自定义站点](#-自定义改成你自己的站) · [部署上线](#-部署上线)

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![VitePress](https://img.shields.io/badge/VitePress-1.6-64a36b.svg)
![Node](https://img.shields.io/badge/node-%3E%3D18-339933.svg)

</div>

---

## 简介

禾光知寒（SRE Notes）是一个用 [VitePress](https://vitepress.dev/zh/) 构建的个人运维知识库，Markdown 驱动、构建为纯静态站点，通过 Docker + Nginx 部署。

内容覆盖 Linux 运维、服务部署、监控告警、日常排障、容器与云原生（Docker / Kubernetes）、自动化与 IaC、DevOps 与平台工程等方向。

> 建这个库的初衷，是让自己遇到问题时能快速搜到、快速回忆处理方法；也希望这些能直接抄走的方案，帮到同样在路上的运维同学。

## ✨ 特性

- **开箱即用的知识库结构**：操作指南 / 命令速查 / 排障训练场 / 面试专区四大板块，导航与目录已规划好；
- **命令速查**：Linux / 网络 / Docker / kubectl / Git / 云原生，按命令拆成独立页面，翻到即用；
- **排障训练场**：50 个典型故障场景，按「现象 → 定位 → 根因 → 解决」编排，练可复用的排查套路；
- **文章元信息条**：分类、难度（初级 / 中级 / 高级）、日期，以及自动估算的阅读时长；
- **Mermaid 图表**：浏览器端渲染架构图 / 流程图 / 时序图，自动跟随深浅色主题；
- **本地全文搜索**：`Ctrl + K` 纯前端搜索，无需服务端；
- **深色护眼主题**：玻璃态导航、终端风格首页、深浅色一键切换；
- **纯静态 + Docker 部署**：一份 Dockerfile，一条命令上线。

## 🧱 目录结构

```text
.
├─ docs/                            # 站点内容（VitePress 的 srcDir）
│  ├─ .vitepress/
│  │  ├─ config.mts                 # ⭐ 站点配置：导航 / 侧边栏 / Markdown 增强
│  │  └─ theme/                     # 自定义主题（组件与样式，功能见下节）
│  │     ├─ index.ts                # 主题入口：注册组件、挂载 Layout
│  │     ├─ custom.css              # ⭐ 全局样式 / 配色 / 玻璃态变量
│  │     ├─ Layout.vue              # ⭐ 全局布局中枢
│  │     ├─ Mermaid.vue             # Mermaid 图表渲染组件
│  │     └─ components/
│  │        ├─ Home.vue              # ⭐ 首页（首屏 + 项目 + 分类）
│  │        ├─ MetaBar.vue           # 文章元信息条
│  │        └─ ThemeToggle.vue       # 主题切换按钮
│  ├─ index.md                      # 首页入口（挂载 <Home />）
│  ├─ about.md                      # 关于页
│  ├─ roadmap.md                    # 学习路线
│  ├─ guide/                        # 操作指南（聚合页 + 系列文章）
│  ├─ reference/                    # 命令速查（速查页 + cmd-* 详解）
│  ├─ cases/                        # 排障训练场（t-* 案例 + 排障记录）
│  ├─ projects/                     # 我的项目（项目总览 + 项目文章）
│  ├─ interview/                    # 面试专区
│  └─ public/                       # 静态资源（logo / fonts 字体 / 插图）
├─ scripts/
│  └─ gen-feed.mjs                  # 构建后生成 RSS 订阅源
├─ deploy/                          # 部署示例（Dockerfile / compose / nginx）
├─ .github/workflows/build.yml       # CI：push / PR 自动构建
├─ FILES.md                         # 英文文件名 ↔ 中文标题对照表
└─ package.json
```

## 🧩 代码结构与功能说明

这一节讲清楚每个组件、脚本、配置文件分别负责什么，方便你快速定位「想改某个效果，该动哪个文件」。

### 1. 主题入口 `theme/index.ts`

- 继承 VitePress 默认主题，挂载自定义 `Layout`；
- 全局注册两个组件：`Mermaid`（图表）、`Home`（首页）；
- 引入全局样式 `custom.css`。

### 2. 全局布局中枢 `theme/Layout.vue`

全站级逻辑都在这里，分四块：

| 功能区 | 作用 |
|---|---|
| 主题切换 `provide('toggle-appearance')` | 从点击位置**圆形涟漪扩散**切换深浅色（View Transitions API）；浏览器不支持时直接切换 |
| 右侧大纲自动滚动 | 监听大纲激活项变化，把当前标题自动滚进可视区；切换路由时重置 |
| 复制按钮增强 | 给代码块复制按钮注入「复制 / ✓ 已复制」文字；用 MutationObserver 应对 SPA 路由切换后出现的新按钮 |
| 插槽挂载 | `#layout-top` 全局背景、`#doc-before` 元信息条、`#nav-bar-content-after` 主题按钮、`#layout-bottom` 页脚 |

页脚内容（构建说明 / 版权 / 备案号）在这个文件的 `#layout-bottom` 插槽里。

### 3. 首页组件 `theme/components/Home.vue`（改动最频繁的文件）

**`<script>` 里的数据与逻辑：**

| 区块 | 作用 |
|---|---|
| `STATS` | 构建时用 `import.meta.glob` 自动扫描 md 统计（技术文档 / 命令详解 / 排障案例 / 知识专题），**无需手改数字** |
| 终端动画 | `SCRIPTS` 是终端演示数据；`typeCmd` 打字机、`addOut` 彩色输出、`runTerm` 循环播放；系统开启「减少动态效果」时用 `staticTerm` 静态展示 |
| `FEATS` | 第二屏 9 个内容分类数据（标题 / 描述 / 图标 / 跳转） |
| `PROJECTS` | 「我的项目」3 张卡片数据 |
| `showHint` + 滚动监听 | 向下箭头：页面一旦滚动（超过 8px）立即淡出，回顶部重现 |
| `animateCount` | 统计数字进入视口时从 0 滚动到目标值 |
| `go()` / `openSearch()` | 卡片跳转路由 / 触发搜索框 |

**`<template>` 结构（从上到下）：**

- `.first-screen`（首屏，占满一屏）：Hero（徽标 / 大标题 / 描述 / 按钮 + 右侧终端）→ 统计条 → 首屏搜索框 → 向下箭头；
- `.projects`：我的项目三卡片；
- `#features`：9 个分类的紧凑列表。

**`<style>`（非 scoped）：** 全部以 `.home-root` 作命名空间，**只作用于首页、不污染其他页面**；开头定义深色 / 浅色两套 token（背景、卡片、边框、终端配色），后面是各模块样式与响应式断点。

### 4. 文章元信息条 `theme/components/MetaBar.vue`

- 读取文章 frontmatter 的 `category` / `difficulty` / `date`，显示在 H1 上方；
- 三者全缺时组件不渲染（聚合页、索引页因此不会出现空条）；
- 难度色标：初级绿 / 中级黄 / 高级红；
- **阅读时长自动估算**：中文约 380 字/分钟、代码等约 300 字符/分钟；切换路由后重新统计。

### 5. 主题切换按钮 `theme/components/ThemeToggle.vue`

- 调用 Layout 注入的切换方法；
- 内含太阳 / 月亮两套 SVG 图标。

### 6. Mermaid 图表 `theme/Mermaid.vue`

- 只在浏览器端**动态 `import('mermaid')`、且只加载一次**（不进首屏、不影响构建）；
- 所有图的初始化 + 渲染进入**全局串行队列**，杜绝多图并发竞态；
- 在离屏临时容器中渲染，避免临时节点残留到页面；
- 失败自动重试一次；切换深浅色后防抖重绘；
- 大图自适应：不超出容器，超高图（如竖向流程图）限高 80vh，再宽可横向滚动。

### 7. 全局样式 `theme/custom.css`

按注释分成若干块，想调对应效果直接定位：

| 注释块 | 控制的内容 |
|---|---|
| 字体与设计 token | 字体栈、品牌色 `--brand-*`、圆角 `--radius` |
| 全局背景 | `.bg-fx`：网格 + 三团光晕（深色 / 浅色分别设置） |
| 玻璃态变量 | 导航、卡片、搜索弹窗共用的玻璃态参数 |
| 导航 / 侧边栏 / 大纲 | 三栏宽度、间距、对齐 |
| 正文排版 | 标题、段落、列表、引用 |
| 表格 | HeroUI 风格圆角表格、`idx` 索引表、悬停高亮 |
| 代码块 | `--cb-body/head/border/blur` 变量、标题栏、tabs、复制按钮 |
| 自定义容器 | callout、提示块 |
| 滚动条 | 全站滚动条样式 |
| 响应式 | 窄屏 / 移动端适配 |

### 8. 站点配置 `.vitepress/config.mts`

| 配置块 | 作用 |
|---|---|
| 基础信息 | `lang` / `title` / `description` |
| `vite` | `chunkSizeWarningLimit` 打包体积警告阈值 |
| `lastUpdated` / `sitemap` | 页底最后更新时间（取 Git 提交）、自动生成站点地图 |
| `head` | favicon、RSS 自动发现、字体样式表 |
| `appearance` | 默认深色主题 |
| `markdown.languageAlias` | 把 conf / promql / cron 等别名到已内置语法，消除高亮警告 |
| `markdown.config` | 注册 `idx` 容器；把 ` ```mermaid ` 转成 `<Mermaid>` 组件；给含 `{{ }}` 的行内代码加 `v-pre` |
| `themeConfig` | logo、顶部 `nav`、左侧 `sidebar`、右侧 `outline`、搜索、各类中文文案 |

### 9. RSS 生成脚本 `scripts/gen-feed.mjs`

- 在 `vitepress build` 之后自动运行（已挂在 `package.json` 的 build 命令里）；
- 扫描带 frontmatter `date` 的文章（排障案例、项目文章，以及将来补了日期的指南；自动排除聚合页），按日期倒序取最新 20 篇，生成 `feed.xml`。

### 10. 部署文件 `deploy/`

| 文件 | 作用 |
|---|---|
| `Dockerfile` | 多阶段构建：Node 阶段编译站点 → Nginx 阶段托管静态产物 |
| `docker-compose.yml` | 一条命令构建并运行容器（映射 8080 端口） |
| `nginx.conf` | 静态站配置：安全响应头、gzip、带 hash 资源长缓存、路由回退 |

### 11. 持续集成 `.github/workflows/build.yml`

- 推送到 GitHub 的 master/main（或发起 PR）时，自动安装依赖并构建；构建过程会顺带检查死链。项目目前主要托管在 Gitee，此配置在同步到 GitHub 后自动生效。

## 🚀 快速开始

环境要求：[Node.js](https://nodejs.org/) **18 或更高版本**。

```bash
# 1. 安装依赖（国内可加 --registry=https://registry.npmmirror.com）
npm install

# 2. 启动本地开发服务器
npm run dev
```

浏览器打开终端提示的地址（默认 `http://localhost:5173`），修改内容会实时热更新。

其他命令：

```bash
npm run build     # 构建静态产物到 docs/.vitepress/dist
npm run preview   # 本地预览构建产物
```

## 🎨 自定义（改成你自己的站）

**1. 站点信息** —— `docs/.vitepress/config.mts`

| 配置项 | 作用 |
|---|---|
| `title` | 站点名称（导航最左侧、浏览器标签页标题） |
| `description` | 站点描述（利于 SEO） |
| `head` | favicon、字体等 |
| `themeConfig.logo` | 导航栏 Logo |
| `themeConfig.nav` | 顶部导航 |
| `themeConfig.sidebar` | 左侧导航 |

**2. 配色与玻璃态** —— `docs/.vitepress/theme/custom.css`

顶部 `:root`（浅色）与 `.dark`（深色）里是主题 CSS 变量；背景光晕、玻璃态、代码块、表格的透明度都在这里调整，注释里有说明。

**3. Logo 与插图** —— `docs/public/`

- `logo.svg`：站点 Logo（导航 + favicon 共用）；
- `hero-ops.png`：首页插图。

**4. 内容**

`docs/guide/`、`reference/`、`cases/`、`interview/` 下是示例文章，可直接修改或删除。文件名建议用英文（URL 更专业），与中文标题的对照见 [FILES.md](FILES.md)。

**写一篇新文章**：在对应板块新建 `.md`，顶部可加 frontmatter：

```yaml
---
category: Linux          # 分类，显示为元信息条
difficulty: 初级          # 难度：初级 / 中级 / 高级
date: 2020-11-03         # 日期（可选，格式 YYYY-MM-DD）
---
```

阅读时长由 `MetaBar` 组件根据正文长度自动估算，无需手写。

## 📦 部署上线

### 方式一：Docker（推荐）

`deploy/` 目录提供了多阶段构建的 Dockerfile，在**项目根目录**执行：

```bash
# 构建镜像
docker build -f deploy/Dockerfile -t sre-notes .

# 运行（访问 http://localhost:8080）
docker run -d -p 8080:80 --name sre-notes sre-notes
```

或使用 docker-compose：

```bash
docker compose -f deploy/docker-compose.yml up -d --build
```

### 方式二：静态托管

构建产物位于 `docs/.vitepress/dist`，把整个目录上传到任意静态服务器、对象存储或 Pages 服务即可。Nginx 配置示例见 [`deploy/nginx.conf`](deploy/nginx.conf)。

## 🤝 致谢

- [VitePress](https://vitepress.dev/zh/)：本站的构建框架；
- 内容编写与技术排障由 [豆包 Doubao](https://www.doubao.com) 辅助完成。

## 📄 License

基于 [MIT License](LICENSE) 开源，欢迎自由使用与修改。
