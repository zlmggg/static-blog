import { defineConfig } from 'vitepress'
import container from 'markdown-it-container'

// 站点常量：canonical / Open Graph 统一用同一套，避免每页手写
const SITE_URL = 'https://www.sresec.com'
const SITE_NAME = '禾光知寒'
const DEFAULT_DESCRIPTION = '一个 SRE 的成长档案与随时可查的运维手册：命令速查、服务部署与排障训练'

// 文档：https://vitepress.dev/zh/reference/site-config

// 【单站方案】技术问答并入各领域指南末尾的「常见问题 FAQ」，
// 求职、简历、HR、谈薪类个人内容不上公开站；站点不区分公开/私有构建。

export default defineConfig({
  // 站点语言：设置为中文后，界面内置文案会自动使用中文
  lang: 'zh-CN',

  // 站点标题（显示在顶部导航最左侧，也是浏览器标签页标题后缀）
  title: '禾光知寒',
  description: '一个 SRE 的成长档案与随时可查的运维手册：命令速查、服务部署与排障训练',

  // 实验项目附件是 public 下的静态文件，不是文档页；只忽略这一组静态下载链接
  ignoreDeadLinks: [/^\/ops-project\/files\//],

  // 本地搜索索引（125 页约 2MB，仅打开搜索框时异步加载）与 Mermaid 都已按需拆分，
  // 调高打包体积警告阈值到 6000，消除这个无害的 chunk size 警告
  vite: {
    build: {
      chunkSizeWarningLimit: 6000
    }
  },

  // 页面底部显示最后更新时间（取 Git 提交时间）
  lastUpdated: true,

  // 站点地图：构建时自动生成 sitemap.xml，帮助搜索引擎收录整站
  sitemap: {
    hostname: 'https://www.sresec.com'
  },

  // 浏览器标签页图标（favicon），与导航栏 Logo 共用同一张 SVG
  // 字体：拉丁字体自托管见 /fonts/fonts.css，中文直接用系统字体（无第三方字体依赖）
  head: [
    ['meta', { name: 'keywords', content: 'SRE,运维,Linux命令,Docker,Kubernetes,K8s,命令速查,排障,监控告警' }],
    ['link', { rel: 'icon', type: 'image/svg+xml', href: '/logo.svg' }],
    // RSS 订阅源自动发现（浏览器/阅读器可提示订阅）
    [
      'link',
      { rel: 'alternate', type: 'application/rss+xml', title: '禾光知寒', href: '/feed.xml' }
    ],
    // 拉丁字体自托管（Space Grotesk / JetBrains Mono）；中文用系统字体
    ['link', { rel: 'stylesheet', href: '/fonts/fonts.css' }]
  ],

  // 每页注入 canonical / Open Graph / Twitter 卡片，便于搜索引擎和分享卡片识别
  transformHead({ pageData }: any) {
    const rel = String(pageData.relativePath || '')
      .replace(/\.md$/, '')
      .replace(/(^|\/)index$/, '$1')
    const path = rel === 'index' ? '' : rel
    const canonical = `${SITE_URL}/${path}`
    const title = pageData.title
      ? String(pageData.title).includes(SITE_NAME)
        ? pageData.title
        : `${pageData.title} · ${SITE_NAME}`
      : SITE_NAME
    const description = pageData.description || DEFAULT_DESCRIPTION
    const isHome = pageData.relativePath === 'index.md'
    return [
      ['link', { rel: 'canonical', href: canonical }],
      ['meta', { property: 'og:type', content: isHome ? 'website' : 'article' }],
      ['meta', { property: 'og:site_name', content: SITE_NAME }],
      ['meta', { property: 'og:title', content: title }],
      ['meta', { property: 'og:description', content: description }],
      ['meta', { property: 'og:url', content: canonical }],
      ['meta', { property: 'og:locale', content: 'zh_CN' }],
      ['meta', { name: 'twitter:card', content: 'summary' }],
      ['meta', { name: 'twitter:title', content: title }],
      ['meta', { name: 'twitter:description', content: description }]
    ]
  },

  // 默认跟随操作系统主题（prefers-color-scheme）：
  //   appearance: true  → 系统深色则深色、系统浅色则浅色；用户手动切换后记住选择
  //   appearance: 'dark' → 强制深色（V2 行为，V3 已弃用）
  appearance: true,

  // Markdown 解析增强
  markdown: {

    // theme: {
    //   light: 'github-light-default',
    //   dark: 'github-dark-default'
    // },

    // 语言别名：笔记里用 ```conf 标记的配置文件（如 BIND named.conf），
    // 别名到 nginx 语法高亮（二者都是「语句 { 指令 值; }」结构），
    // 消除 "language 'conf' is not loaded" 警告；以后再写 conf 也自动生效。
    languageAlias: {
      conf: 'nginx',
      fstab: 'nginx',
      // 以下语言 Shiki 2.5 未内置对应语法，别名到最接近的已内置语法，消除 "not loaded" 警告：
      jinja2: 'jinja',   // Helm/Nginx 等 Jinja 风格模板
      promql: 'sql',     // PromQL 查询
      logql: 'sql',      // Loki LogQL 查询
      traceql: 'sql',    // Tempo TraceQL 查询
      cron: 'bash',      // crontab 定时任务行
      crontab: 'bash',   // 部分笔记围栏用 crontab，统一别名消除 not loaded 警告
      tmux: 'bash'       // tmux 配置/命令片段按 shell 高亮
    },
    config: (md: any) => {
      // 自定义容器 ::: idx：包裹聚合页「文章索引表」，配合 CSS 固定状态列宽度
      md.use(container, 'idx', {
        render(tokens: any, idx: number) {
          return tokens[idx].nesting === 1 ? '<div class="idx-table">\n' : '</div>\n'
        }
      })

      // 命令手册聚合表：紧凑排版容器（行高与间距收紧，第一列按内容自适应）
      md.use(container, 'cmd', {
        render(tokens: any, idx: number) {
          return tokens[idx].nesting === 1 ? '<div class="cmd-table">\n' : '</div>\n'
        }
      })

      // —— Mermaid：把 ```mermaid 代码块转成 <Mermaid> 组件，由组件在浏览器端渲染 ——
      // 手动集成而非用 vitepress-plugin-mermaid（该插件的 withMermaid 在 VitePress 1.6 会白屏）。
      const defaultFence = md.renderer.rules.fence
      md.renderer.rules.fence = (tokens: any, idx: number, options: any, env: any, self: any) => {
        const token = tokens[idx]
        if (token.info.trim() === 'mermaid') {
          // 源码 base64 编码后传入（base64 只含字母数字和 +/=，放进属性不会破坏 HTML）
          const b64 = Buffer.from(token.content, 'utf-8').toString('base64')
          return `<div class="mermaid-wrapper"><Mermaid b64="${b64}"></Mermaid></div>\n`
        }
        return defaultFence
          ? defaultFence(tokens, idx, options, env, self)
          : self.renderToken(tokens, idx, options)
      }
      // 行内代码里出现 {{ }}（如 Docker Go template、Helm 模板语法）时，
      // 会被 Vue 当成插值表达式导致构建失败，给这类 <code> 自动加 v-pre。
      const defaultRule = md.renderer.rules.code_inline
      md.renderer.rules.code_inline = (tokens: any, idx: number, options: any, env: any, self: any) => {
        const content: string = tokens[idx].content
        if (content.includes('{{')) {
          return `<code v-pre>${md.utils.escapeHtml(content)}</code>`
        }
        return defaultRule
          ? defaultRule(tokens, idx, options, env, self)
          : `<code>${md.utils.escapeHtml(content)}</code>`
      }
    }
  },

  themeConfig: {
    // 顶部导航最左侧站点标题前面的 Logo（紫渐变圆角方块 SVG）
    logo: '/logo.svg',

    // —— 顶部导航 ——
    nav: [
      { text: '首页', link: '/' },
      { text: '命令手册', link: '/commands/', activeMatch: '/commands/' },
      { text: '服务详解', link: '/services/', activeMatch: '/services/' },
      { text: '部署方案', link: '/deploy/', activeMatch: '/deploy/' },
      { text: '故障与排障', link: '/cases/', activeMatch: '/cases/' },
      {
        text: '我的项目',
        activeMatch: '/projects/',
        items: [
          { text: '项目总览', link: '/projects/' },
          { text: '禾光知寒站点', link: '/projects/site-blog' },
          { text: '阿里云部署', link: '/projects/aliyun-deploy' },
          { text: '项目架构', link: '/projects/homelab' }
        ]
      },
      { text: '关于', link: '/about' }
    ],

    // —— 左侧导航：全局精简侧边栏，只列「开始 / 速查 / 聚合页 / 案例」入口 ——
    // 详细文章不在侧边栏展开，通过各聚合页 + 全文搜索（Ctrl+K）进入。
    sidebar: [
      {
        text: '开始',
        collapsed: false,
        items: [
          { text: '关于本站', link: '/about' }
        ]
      },
      {
        text: '命令手册',
        collapsed: false,
        items: [
          { text: '命令手册总览', link: '/commands/' },
          { text: '文件与文本', link: '/commands/basic/' },
          { text: '用户与权限', link: '/commands/identity/' },
          { text: '进程与系统', link: '/commands/system/' },
          { text: '磁盘与存储', link: '/commands/storage/' },
          { text: '网络', link: '/commands/network/' },
          { text: '排障观测', link: '/commands/observe/' },
          { text: '软件包管理', link: '/commands/package/' },
          { text: 'Shell 与脚本', link: '/commands/shell/' },
          { text: '开发与效率', link: '/commands/devtools/' }
        ]
      },
      {
        text: '服务详解',
        collapsed: false,
        items: [
          { text: '服务全景', link: '/services/' },
          {
            text: '接入与网络',
            collapsed: true,
            items: [
              { text: '分组导读', link: '/services/web/' },
              {
                text: 'Nginx',
                collapsed: true,
                items: [
                  { text: '01 服务理论', link: '/services/web/nginx/01-理论' },
                  { text: '02 部署方案', link: '/services/web/nginx/02-部署' },
                  { text: '03 功能详解', link: '/services/web/nginx/03-功能' },
                  { text: '04 实战参考', link: '/services/web/nginx/04-实战' }
                ]
              },
              { text: 'LVS + Keepalived', link: '/services/web/lvs-keepalived' },
              { text: 'HAProxy', link: '/services/web/haproxy' },
              { text: 'DNS（Bind）', link: '/services/web/dns' }
            ]
          },
          {
            text: '数据库与缓存',
            collapsed: true,
            items: [
              { text: '分组导读', link: '/services/database/' },
              {
                text: 'MySQL',
                collapsed: true,
                items: [
                  { text: '01 服务理论', link: '/services/database/mysql/01-理论' },
                  { text: '02 部署方案', link: '/services/database/mysql/02-部署' },
                  { text: '03 功能详解', link: '/services/database/mysql/03-功能' },
                  { text: '04 实战参考', link: '/services/database/mysql/04-实战' }
                ]
              },
              {
                text: 'Redis',
                collapsed: true,
                items: [
                  { text: '01 服务理论', link: '/services/database/redis/01-理论' },
                  { text: '02 部署方案', link: '/services/database/redis/02-部署' },
                  { text: '03 功能详解', link: '/services/database/redis/03-功能' },
                  { text: '04 实战参考', link: '/services/database/redis/04-实战' }
                ]
              }
            ]
          },
          {
            text: '中间件',
            collapsed: true,
            items: [
              { text: '分组导读', link: '/services/middleware/' },
              { text: 'Nacos', link: '/services/middleware/nacos' },
              { text: 'Kafka', link: '/services/middleware/kafka' },
              { text: 'RabbitMQ', link: '/services/middleware/rabbitmq' }
            ]
          },
          {
            text: '容器与编排',
            collapsed: true,
            items: [
              { text: '分组导读', link: '/services/container/' },
              {
                text: 'Docker',
                collapsed: true,
                items: [
                  { text: '01 服务理论', link: '/services/container/docker/01-理论' },
                  { text: '02 部署方案', link: '/services/container/docker/02-部署' },
                  { text: '03 功能详解', link: '/services/container/docker/03-功能' },
                  { text: '04 实战参考', link: '/services/container/docker/04-实战' }
                ]
              },
              { text: 'Docker Compose', link: '/services/container/compose' },
              {
                text: 'Kubernetes',
                collapsed: true,
                items: [
                  { text: '01 服务理论', link: '/services/container/kubernetes/01-理论' },
                  { text: '02 部署方案', link: '/services/container/kubernetes/02-部署' },
                  { text: '03 功能详解', link: '/services/container/kubernetes/03-功能' },
                  { text: '04 实战参考', link: '/services/container/kubernetes/04-实战' }
                ]
              },
              { text: 'Helm', link: '/services/container/helm' },
              { text: 'Harbor', link: '/services/container/harbor' }
            ]
          },
          {
            text: '存储与搜索',
            collapsed: true,
            items: [
              { text: '分组导读', link: '/services/storage-search/' },
              { text: 'MinIO', link: '/services/storage-search/minio' },
              {
                text: 'Elasticsearch',
                collapsed: true,
                items: [
                  { text: '01 服务理论', link: '/services/storage-search/elasticsearch/01-理论' },
                  { text: '02 部署方案', link: '/services/storage-search/elasticsearch/02-部署' },
                  { text: '03 功能详解', link: '/services/storage-search/elasticsearch/03-功能' },
                  { text: '04 实战参考', link: '/services/storage-search/elasticsearch/04-实战' }
                ]
              }
            ]
          },
          {
            text: 'CI/CD 与自动化',
            collapsed: true,
            items: [
              { text: '分组导读', link: '/services/cicd/' },
              { text: 'GitLab', link: '/services/cicd/gitlab' },
              {
                text: 'Jenkins',
                collapsed: true,
                items: [
                  { text: '01 服务理论', link: '/services/cicd/jenkins/01-理论' },
                  { text: '02 部署方案', link: '/services/cicd/jenkins/02-部署' },
                  { text: '03 功能详解', link: '/services/cicd/jenkins/03-功能' },
                  { text: '04 实战参考', link: '/services/cicd/jenkins/04-实战' }
                ]
              },
              { text: 'Ansible', link: '/services/cicd/ansible' }
            ]
          },
          {
            text: '监控与日志',
            collapsed: true,
            items: [
              { text: '分组导读', link: '/services/observability/' },
              {
                text: 'Prometheus',
                collapsed: true,
                items: [
                  { text: '01 服务理论', link: '/services/observability/prometheus/01-理论' },
                  { text: '02 部署方案', link: '/services/observability/prometheus/02-部署' },
                  { text: '03 功能详解', link: '/services/observability/prometheus/03-功能' },
                  { text: '04 实战参考', link: '/services/observability/prometheus/04-实战' }
                ]
              },
              { text: 'Grafana', link: '/services/observability/grafana' },
              { text: 'Alertmanager', link: '/services/observability/alertmanager' },
              { text: 'ELK 日志平台', link: '/services/observability/elk' }
            ]
          }
        ]
      },
      {
        text: '部署方案',
        collapsed: false,
        items: [
          { text: '部署形态矩阵', link: '/deploy/' },
          { text: '接入层高可用', link: '/deploy/stacks/lb-ha' },
          { text: 'MySQL 主从读写分离', link: '/deploy/stacks/mysql-ha' },
          { text: 'Redis 哨兵集群', link: '/deploy/stacks/redis-sentinel' },
          { text: 'CI/CD 流水线', link: '/deploy/stacks/cicd-pipeline' },
          { text: '监控告警栈', link: '/deploy/stacks/monitor-stack' },
          { text: '日志链路', link: '/deploy/stacks/log-stack' }
        ]
      },
      {
        text: '我的项目',
        collapsed: false,
        items: [
          { text: '项目总览', link: '/projects/' },
          { text: '禾光知寒站点', link: '/projects/site-blog' },
          { text: '阿里云部署', link: '/projects/aliyun-deploy' },
          { text: '项目架构', link: '/projects/homelab' },
          {
            text: '10-实操',
            collapsed: true,
            items: [
              { text: '10-实操总览', link: '/projects/homelab/practice/' },
              { text: '资料清单', link: '/projects/homelab/materials' },
              { text: 'D0 装机与 PVE 初始化', link: '/projects/homelab/practice/01-D0-装机与PVE初始化' },
              { text: 'D1-P0 管理平面', link: '/projects/homelab/practice/02-D1-P0管理平面' },
              { text: 'D1-P1 最小链路', link: '/projects/homelab/practice/03-D1-P1最小链路' },
              { text: 'D1-P1.5 堡垒机', link: '/projects/homelab/practice/04-D1-P15堡垒机' },
              { text: 'D2-P2-1 数据层高可用', link: '/projects/homelab/practice/05-D2-P2-1数据层高可用' },
              { text: 'D2-P2-2 对象存储与搜索', link: '/projects/homelab/practice/06-D2-P2-2对象存储与搜索' },
              { text: 'D2-P2-3 蓝绿发布', link: '/projects/homelab/practice/07-D2-P2-3蓝绿发布' },
              { text: 'P3-0 中间件 Nacos 与日志', link: '/projects/homelab/practice/08-P3-0中间件Nacos与日志' },
              { text: 'P3-1 若依与 MinIO', link: '/projects/homelab/practice/09-P3-1若依部署与MinIO' },
              { text: 'P3-2 若依接入 ES', link: '/projects/homelab/practice/10-P3-2若依接入ES' },
              { text: 'P3-3 若依蓝绿发布', link: '/projects/homelab/practice/11-P3-3若依蓝绿发布' },
              { text: 'P4 K8s 迁移', link: '/projects/homelab/practice/12-P4-K8s迁移' },
              { text: 'P5 mall-swarm', link: '/projects/homelab/practice/13-P5-mall-swarm' }
            ]
          }
        ]
      },
      {
        text: '故障与排障',
        collapsed: false,
        items: [
          { text: '排障记录（聚合）', link: '/cases/' }
        ]
      },
      {
        text: '运维手记',
        collapsed: true,
        items: [
          { text: '运维手记', link: '/guide/blog' },
          { text: '职业发展与行业思考', link: '/guide/career' }
        ]
      }
    ],

    // —— 右侧「大纲」：自动提取当前文章的标题 ——
    outline: {
      level: [2, 3],
      label: '本页目录'
    },

    // 上一页 / 下一页按钮文案
    docFooter: {
      prev: '上一页',
      next: '下一页'
    },

    lastUpdatedText: '最后更新',
    returnToTopLabel: '回到顶部',
    sidebarMenuLabel: '菜单',
    darkModeSwitchLabel: '主题',
    lightModeSwitchTitle: '切换到浅色模式',
    darkModeSwitchTitle: '切换到深色模式',

    // —— 本地全文搜索（纯前端，无需服务端）——
    search: {
      provider: 'local',
      options: {
        translations: {
          button: {
            buttonText: '搜索文档',
            buttonAriaLabel: '搜索文档'
          },
          modal: {
            noResultsText: '无法找到相关结果',
            resetButtonTitle: '清除查询条件',
            footer: {
              selectText: '选择',
              navigateText: '切换',
              closeText: '关闭'
            }
          }
        }
      }
    },

    // 页脚
    // footer: {
    //   message: '基于 VitePress 构建',
    //   copyright: 'Copyright © 2026 sresec.com'
    // }
  }
})
