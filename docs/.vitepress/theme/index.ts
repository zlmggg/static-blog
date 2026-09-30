// 自定义主题入口：先继承 VitePress 默认主题，再引入自定义样式
// 文档：https://vitepress.dev/zh/guide/extending-default-theme
import DefaultTheme from 'vitepress/theme'
import { h } from 'vue'
import './custom.css'
import OutlineAutoScroll from './OutlineAutoScroll.vue'
import Mermaid from './Mermaid.vue'

export default {
  extends: DefaultTheme,
  // 全局注册 Mermaid 组件
  enhanceApp({ app }) {
    app.component('Mermaid', Mermaid)
  },
  Layout: () =>
    h(DefaultTheme.Layout, null, {
      // 大纲自动滚动（原有，保留）
      'aside-outline-after': () => h(OutlineAutoScroll),
      // 全站底部：构建说明 + 版权 + 备案号，同一行
      'layout-bottom': () =>
        h('div', { class: 'site-footer' }, [
          h('span', { class: 'footer-item' }, '基于 VitePress 构建'),
          h('span', { class: 'footer-item' }, 'Copyright © 2026 sresec.com'),
          h(
            'a',
            {
              class: 'footer-item',
              href: 'https://beian.miit.gov.cn/',
              target: '_blank',
              rel: 'noopener noreferrer'
            },
            '黑ICP备2026011822号'
          )
        ])
    })
}
