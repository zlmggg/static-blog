<script setup>
// Mermaid 渲染组件（修复多图并发竞态、主题切换重绘、临时节点污染 body、大图自适应）：
// - 只在浏览器端动态 import mermaid（避免 SSR/构建白屏）；
// - 模块只加载一次；initialize + render 全部进入全局串行队列，杜绝并发竞态；
// - render 使用离屏临时容器，避免 Mermaid 把临时/错误节点残留到 <body>（消除"一红一白"）；
// - 失败自动延迟重试一次；主题切换防抖重绘，且只采用最新一次结果；
// - useMaxWidth 让图按容器宽度自适应，外层可横向滚动兜底。
import { ref, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps({ b64: { type: String, required: true } })
const container = ref(null)
let observer = null
let disposed = false
let renderSeq = 0

// UTF-8 安全的 base64 解码（源码含中文，atob 会乱码）
function decode(b64) {
  const bin = atob(b64)
  const bytes = Uint8Array.from(bin, (c) => c.charCodeAt(0))
  return new TextDecoder().decode(bytes)
}

// 各图统一配置：useMaxWidth 让 SVG 不超出容器
function baseConfig(dark) {
  return {
    startOnLoad: false,
    securityLevel: 'loose',
    theme: dark ? 'dark' : 'default',
    flowchart: { useMaxWidth: true, htmlLabels: true },
    sequence: { useMaxWidth: true },
    gantt: { useMaxWidth: true },
    class: { useMaxWidth: true },
    state: { useMaxWidth: true },
    er: { useMaxWidth: true },
    journey: { useMaxWidth: true },
    pie: { useMaxWidth: true }
  }
}

// 模块单例：mermaid 只动态加载一次
let mermaidPromise = null
function getMermaid() {
  if (!mermaidPromise) {
    mermaidPromise = (async () => (await import('mermaid')).default)()
  }
  return mermaidPromise
}

// 全局串行队列：所有组件的 initialize + render 排队执行，避免并发
let queueTail = Promise.resolve()
function enqueue(task) {
  const run = queueTail.then(() => task())
  queueTail = run.then(
    () => {},
    () => {}
  )
  return run
}

// 离屏临时挂载点（给 Mermaid 测量/临时插入，不污染可见页面）
function makeHost() {
  const host = document.createElement('div')
  host.style.cssText =
    'position:absolute;top:0;left:-99999px;width:1200px;visibility:hidden;'
  document.body.appendChild(host)
  return host
}

// 单次尝试：建 host → 队列内 initialize + render → 移除 host，返回 svg
async function attemptOnce(mermaid, code) {
  const host = makeHost()
  const id = 'mmd-' + Math.random().toString(36).slice(2, 10)
  try {
    const svg = await enqueue(async () => {
      const dark = document.documentElement.classList.contains('dark')
      mermaid.initialize(baseConfig(dark))
      const result = await mermaid.render(id, code, host)
      return result.svg
    })
    return svg
  } finally {
    host.remove()
  }
}

function showSource(code) {
  if (disposed || !container.value) return
  container.value.innerHTML =
    '<pre style="white-space:pre-wrap;text-align:left">' +
    code.replace(/[<>&]/g, (c) => ({ '<': '&lt;', '>': '&gt;', '&': '&amp;' }[c])) +
    '</pre>'
}

async function draw() {
  const seq = ++renderSeq
  const code = decode(props.b64)
  const mermaid = await getMermaid()
  if (disposed) return

  let svg
  try {
    svg = await attemptOnce(mermaid, code)
  } catch (e1) {
    // 瞬时/竞态错误：稍等整体重试一次
    await new Promise((r) => setTimeout(r, 160))
    if (disposed || seq !== renderSeq) return
    try {
      svg = await attemptOnce(mermaid, code)
    } catch (e2) {
      if (!disposed && seq === renderSeq) showSource(code)
      return
    }
  }
  if (disposed || seq !== renderSeq) return
  container.value.innerHTML = svg
}

// 主题切换：防抖后重绘
let themeTimer = null
function scheduleDraw() {
  clearTimeout(themeTimer)
  themeTimer = setTimeout(() => draw(), 120)
}

onMounted(() => {
  draw()
  observer = new MutationObserver(scheduleDraw)
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })
})

onBeforeUnmount(() => {
  disposed = true
  clearTimeout(themeTimer)
  observer && observer.disconnect()
})
</script>

<template>
  <div class="mermaid-wrapper">
    <div ref="container" class="mermaid-diagram"></div>
  </div>
</template>

<style scoped>
.mermaid-wrapper {
  margin: 1.5rem 0;
  max-width: 100%;
  overflow-x: auto; /* 超大图兜底：横向滚动而非裁切 */
}
.mermaid-diagram {
  display: flex;
  justify-content: center;
  min-width: 0;
}
.mermaid-diagram :deep(svg) {
  max-width: 100%;
  /* 纵向兜底：超高的竖向流程图（如 roadmap 八阶段）最高占 80% 视口高度，
     保证一屏内可见；配合 viewBox + preserveAspectRatio(meet) 等比缩放并居中，
     宽图受 max-width 约束、高图受 max-height 约束，二者都不溢出。 */
  max-height: 80vh;
  height: auto;
  display: block;
  margin: 0 auto;
}
</style>
