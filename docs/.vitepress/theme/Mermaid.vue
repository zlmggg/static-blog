<script setup>
// Mermaid 渲染组件：
// - 只在浏览器端（onMounted）动态 import mermaid，避免 SSR/构建阶段加载导致白屏；
// - mermaid 源码以 base64 传入（base64 无特殊字符，放进属性安全），组件做 UTF-8 解码；
// - 跟随站点深/浅色主题切换自动重绘。
import { ref, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps({ b64: { type: String, required: true } })
const container = ref(null)
let observer = null

// UTF-8 安全的 base64 解码（mermaid 源码含中文，atob 默认会乱码）
function decode(b64) {
  const bin = atob(b64)
  const bytes = Uint8Array.from(bin, (c) => c.charCodeAt(0))
  return new TextDecoder().decode(bytes)
}

async function render() {
  if (!container.value) return
  const code = decode(props.b64)
  const mermaid = (await import('mermaid')).default
  const isDark = document.documentElement.classList.contains('dark')
  mermaid.initialize({
    startOnLoad: false,
    securityLevel: 'loose',
    theme: isDark ? 'dark' : 'default'
  })
  const id = 'mmd-' + Math.random().toString(36).slice(2, 10)
  try {
    const { svg } = await mermaid.render(id, code)
    container.value.innerHTML = svg
  } catch (e) {
    // 语法出错时退回显示源码，方便定位，不留白
    container.value.innerHTML =
      '<pre style="white-space:pre-wrap;text-align:left">' +
      code.replace(/[<>&]/g, (c) => ({ '<': '&lt;', '>': '&gt;', '&': '&amp;' }[c])) +
      '</pre>'
  }
}

onMounted(() => {
  render()
  // 监听 <html> 的 class（深色/浅色切换），变化后重绘
  observer = new MutationObserver(() => render())
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })
})

onBeforeUnmount(() => observer && observer.disconnect())
</script>

<template>
  <div ref="container" class="mermaid-diagram"></div>
</template>

<style scoped>
.mermaid-diagram {
  margin: 1.5rem 0;
  display: flex;
  justify-content: center;
}
.mermaid-diagram :deep(svg) {
  max-width: 100%;
  height: auto;
}
</style>
