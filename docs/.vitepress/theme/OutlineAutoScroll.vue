<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'

/**
 * 右侧大纲自动滚动
 * ------------------------------------------------------------
 * 问题：VitePress 内置的 useActiveAnchor 只给激活标题加 .active 类、
 * 移动左侧指示条，从不滚动大纲容器。而 .aside-container 是
 * position:fixed + 100vh + 滚动条隐藏，文章标题一多，
 * 激活项跑到可视区外后既不自动滚、也几乎没法手动滚。
 *
 * 方案：用 MutationObserver 监听激活项的 class 变化，
 * 把新激活项滚动到大纲可视范围内。
 * 观察 body 而非大纲节点：路由切换时大纲 DOM 会被整体替换，
 * 观察 body 可避免每次路由变化后重新绑定；回调里只做一次
 * querySelector + 引用比较，开销可忽略。
 */
let observer: MutationObserver | null = null
let lastLink: Element | null = null

function scrollToActive() {
  const container = document.querySelector<HTMLElement>('.aside-container')
  if (!container) return

  // 路由已切换：旧大纲 DOM 被替换，重置滚动位置
  if (lastLink && !lastLink.isConnected) {
    container.scrollTop = 0
    lastLink = null
    return
  }

  const link = document.querySelector<HTMLElement>('.VPDocAsideOutline a.active')
  if (!link || link === lastLink) return
  lastLink = link

  const linkRect = link.getBoundingClientRect()
  const cRect = container.getBoundingClientRect()
  const margin = 56 // 上下缓冲：进入缓冲区才开始滚动，避免每次高亮都晃动

  const outOfView =
    linkRect.top < cRect.top + margin || linkRect.bottom > cRect.bottom - margin
  if (!outOfView) return

  // 把激活项滚到容器偏上 1/3 处，阅读动线更自然
  const target =
    container.scrollTop + (linkRect.top - cRect.top) - container.clientHeight / 3
  container.scrollTo({ top: Math.max(0, target), behavior: 'smooth' })
}

onMounted(() => {
  observer = new MutationObserver(scrollToActive)
  observer.observe(document.body, {
    subtree: true,
    attributes: true,
    attributeFilter: ['class']
  })
  // 首次进入若带锚点，也校正一次
  requestAnimationFrame(scrollToActive)
})

onUnmounted(() => observer?.disconnect())
</script>

<template>
  <!-- 无 UI，仅挂载行为 -->
</template>
