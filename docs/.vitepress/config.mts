import { defineConfig } from 'vitepress'

// 文档：https://vitepress.dev/zh/reference/site-config
export default defineConfig({
  // 站点语言：设置为中文后，界面内置文案会自动使用中文
  lang: 'zh-CN',
  // 站点标题（显示在顶部导航最左侧，也是浏览器标签页标题后缀）
  title: '禾光知寒',
  description: '一个随时可查的 SRE 运维手册：命令速查、服务部署与故障复盘',

  // Mermaid 库体积较大，调高打包体积警告阈值，消除构建时的 chunk size 警告
  vite: {
    build: {
      chunkSizeWarningLimit: 2000
    }
  },

  // 页面底部显示最后更新时间（取 Git 提交时间）
  lastUpdated: true,

  // 浏览器标签页图标（favicon），与导航栏 Logo 共用同一张图
  head: [['link', { rel: 'icon', type: 'image/png', href: '/logo.png' }]],

  // 默认使用深色主题（用户仍可手动切换到浅色，选择会被记住）
  appearance: 'dark',

  // Markdown 解析增强
  markdown: {

    // theme: {
    //   light: 'github-light-default',
    //   dark: 'github-dark-default'
    // },

    // 语言别名：笔记里用 ```conf 标记的配置文件（如 BIND named.conf），
    // 别名到 nginx 语法高亮（二者都是「语句 { 指令 值; }」结构），
    // 消除 "language 'conf' is not loaded" 警告；以后再写 conf 也自动生效。
    languageAlias: { conf: 'nginx', fstab: 'nginx' },
    config: (md: any) => {
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
    // 顶部导航最左侧站点标题前面的 Logo
    logo: '/logo.png',

    // —— 顶部导航 ——
    nav: [
      { text: '首页', link: '/' },
      {
        text: '速查手册',
        activeMatch: '/reference/',
        items: [
          { text: 'Linux 命令速查', link: '/reference/linux-commands' },
          { text: '网络命令速查', link: '/reference/network-commands' },
          { text: 'Docker 命令速查', link: '/reference/docker-commands' },
          { text: 'kubectl 命令速查', link: '/reference/kubectl-commands' }
        ]
      },
      {
        text: '操作指南',
        activeMatch: '/guide/',
        items: [
          { text: 'Linux 系统', link: '/guide/linux' },
          { text: '服务部署', link: '/guide/services' },
          { text: '数据与中间件', link: '/guide/data' },
          { text: '监控与日志', link: '/guide/monitor' },
          { text: '容器与编排', link: '/guide/container' },
          { text: '自动化与 IaC', link: '/guide/automation' }
        ]
      },
      {
        text: '故障与排障',
        activeMatch: '/cases/',
        items: [
          { text: '故障复盘', link: '/cases/' },
          { text: '排障记录', link: '/cases/troubleshooting' }
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
          { text: '关于本站', link: '/about' },
          { text: '学习路线', link: '/roadmap' }
        ]
      },
      {
        text: '速查手册',
        collapsed: false,
        items: [
          { text: 'Linux 命令速查', link: '/reference/linux-commands' },
          { text: '网络命令速查', link: '/reference/network-commands' },
          { text: 'Docker 命令速查', link: '/reference/docker-commands' },
          { text: 'kubectl 命令速查', link: '/reference/kubectl-commands' }
        ]
      },
      {
        text: '操作指南',
        collapsed: false,
        items: [
          { text: 'Linux 系统', link: '/guide/linux' },
          { text: '服务部署', link: '/guide/services' },
          { text: '数据与中间件', link: '/guide/data' },
          { text: '监控与日志', link: '/guide/monitor' },
          { text: '容器与编排', link: '/guide/container' },
          { text: '自动化与 IaC', link: '/guide/automation' }
        ]
      },
      {
        text: '故障与排障',
        collapsed: false,
        items: [
          { text: '故障复盘', link: '/cases/' },
          { text: '排障记录', link: '/cases/troubleshooting' }
        ]
      },
      {
        text: '面试专区（私有）',
        collapsed: false,
        items: [
          { text: '面试题总览', link: '/interview/' }
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
