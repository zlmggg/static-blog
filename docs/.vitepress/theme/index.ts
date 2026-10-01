// 自定义主题入口：继承 VitePress 默认主题，挂载自定义 Layout 与全局组件
// 文档：https://vitepress.dev/zh/guide/extending-default-theme
import DefaultTheme from 'vitepress/theme'
import './custom.css'
import Layout from './Layout.vue'
import Home from './components/Home.vue'
import Mermaid from './Mermaid.vue'

export default {
  extends: DefaultTheme,
  // 用自定义 Layout（全局背景 bg-fx、圆形涟漪主题切换、doc-before MetaBar、页脚）
  Layout,
  enhanceApp({ app }) {
    // 全局注册 Mermaid（markdown fence 手动转组件用）与首页 Home 组件
    app.component('Mermaid', Mermaid)
    app.component('Home', Home)
  }
}
