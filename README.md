<div align="center">

# 禾光知寒 · SRE Notes

**一个基于 VitePress 的个人 SRE 运维知识库 —— 操作指南 · 命令速查 · 排障训练 · 面试整理**

[在线站点](https://www.sresec.com) · [快速开始](#-快速开始) · [自定义站点](#-自定义改成你自己的站) · [部署上线](#-部署上线)

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
├─ docs/                        # 站点内容（VitePress 的 srcDir）
│  ├─ .vitepress/
│  │  ├─ config.mts             # ⭐ 站点配置：标题 / 导航 / 侧边栏
│  │  └─ theme/                 # 自定义主题（样式与组件）
│  │     ├─ custom.css          # ⭐ 全局样式 / 配色 / 玻璃态变量
│  │     ├─ Layout.vue          # 自定义布局（背景、元信息条、页脚）
│  │     ├─ Mermaid.vue         # Mermaid 浏览器端渲染组件
│  │     └─ components/
│  │        ├─ Home.vue          # 首页（终端 Hero）
│  │        ├─ MetaBar.vue       # 文章元信息条
│  │        └─ ThemeToggle.vue   # 主题切换按钮
│  ├─ index.md                  # 首页入口（挂载 <Home />）
│  ├─ about.md                  # 关于页
│  ├─ roadmap.md                # 学习路线
│  ├─ guide/                    # 操作指南（聚合页 + 系列文章）
│  ├─ reference/                # 命令速查（聚合长文档 + cmd-* 拆分页）
│  ├─ cases/                    # 排障训练场（t-* 案例 + 排障记录）
│  ├─ interview/                # 面试专区
│  └─ public/                   # 静态资源（logo / 插图 / diagrams）
├─ deploy/                      # 部署示例（Dockerfile / compose / nginx）
├─ FILES.md                     # 英文文件名 ↔ 中文标题对照表
└─ package.json
```

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
