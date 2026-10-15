<script setup lang="ts">
import { useData } from 'vitepress'
import DefaultTheme from 'vitepress/theme'
import { nextTick, onMounted, onUnmounted, provide } from 'vue'
import ThemeToggle from './components/ThemeToggle.vue'
import MetaBar from './components/MetaBar.vue'

const { isDark } = useData()

const enableTransitions = () =>
  'startViewTransition' in document &&
  window.matchMedia('(prefers-reduced-motion: no-preference)').matches

// 主题切换：从点击位置圆形涟漪扩散（View Transitions API）
provide('toggle-appearance', ({ clientX, clientY }: MouseEvent) => {
  if (!enableTransitions()) {
    isDark.value = !isDark.value
    return
  }

  const x = (100 * clientX) / innerWidth
  const y = (100 * clientY) / innerHeight
  const maxRadius =
    (100 *
      Math.hypot(
        Math.max(clientX, innerWidth - clientX),
        Math.max(clientY, innerHeight - clientY)
      )) /
    (Math.hypot(innerWidth, innerHeight) / Math.SQRT2)

  document.documentElement.style.setProperty('--switch-x', `${x}%`)
  document.documentElement.style.setProperty('--switch-y', `${y}%`)
  document.documentElement.style.setProperty('--switch-r', `${maxRadius}%`)

  document.startViewTransition(async () => {
    isDark.value = !isDark.value
    await nextTick()
  })
})

/**
 * 右侧大纲自动滚动（原 OutlineAutoScroll.vue 逻辑内联至此）
 * VitePress 内置 useActiveAnchor 只加 .active 类、不滚大纲容器；
 * 用 MutationObserver 监听激活项 class 变化，把新激活项滚进可视范围。
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
  const margin = 56

  const outOfView =
    linkRect.top < cRect.top + margin || linkRect.bottom > cRect.bottom - margin
  if (!outOfView) return

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
  requestAnimationFrame(scrollToActive)

  initCopyEnhance()
})

onUnmounted(() => {
  observer?.disconnect()
  copyObserver?.disconnect()
})

/**
 * 复制按钮原地文字增强：
 * 原生点击后给 button.copy 加 .copied（恰好 2000ms 后移除），并在左侧弹出
 * 「已复制」浮层（::before）。这里改为：按钮内注入文字，常态显示「复制图标 + 复制」，
 * 点击后按钮本身文字切到「✓ 已复制」，2 秒后随原生 .copied 移除而恢复；浮层由 CSS 隐藏。
 * VitePress 是 SPA，路由切换 / DOM 变化后新按钮需重新增强——用 MutationObserver 监听。
 */
let copyObserver: MutationObserver | null = null

function enhanceCopyButton(btn: Element) {
  const el = btn as HTMLButtonElement
  if (el.dataset.cbCopyEnhanced) return
  el.dataset.cbCopyEnhanced = '1'
  let label = el.querySelector('.cb-copy-label') as HTMLElement | null
  if (!label) {
    label = document.createElement('span')
    label.className = 'cb-copy-label'
    el.appendChild(label)
  }
  label.textContent = el.classList.contains('copied') ? '✓ 已复制' : '复制'
}

function initCopyEnhance() {
  document
    .querySelectorAll('div[class*="language-"] > button.copy')
    .forEach((btn) => enhanceCopyButton(btn))

  copyObserver?.disconnect()
  copyObserver = new MutationObserver((mutations) => {
    for (const m of mutations) {
      if (
        m.type === 'attributes' &&
        (m.target as HTMLElement).matches?.('div[class*="language-"] > button.copy')
      ) {
        const el = m.target as HTMLButtonElement
        enhanceCopyButton(el)
        const label = el.querySelector('.cb-copy-label')
        if (label) {
          label.textContent = el.classList.contains('copied') ? '✓ 已复制' : '复制'
        }
      }
      m.addedNodes.forEach((node) => {
        if (!(node instanceof HTMLElement)) return
        if (node.matches?.('div[class*="language-"] > button.copy')) {
          enhanceCopyButton(node)
        }
        node
          .querySelectorAll('div[class*="language-"] > button.copy')
          .forEach((b) => enhanceCopyButton(b))
      })
    }
  })
  copyObserver.observe(document.body, {
    subtree: true,
    childList: true,
    attributes: true,
    attributeFilter: ['class']
  })
}
</script>

<template>
  <DefaultTheme.Layout>
    <!-- 全局背景 fixed 铺满：网格 + 三团光晕（首页与内容页统一，不在这里重复挂） -->
    <template #layout-top>
      <div class="bg-fx" aria-hidden="true">
        <div class="bg-grid"></div>
        <div class="glow g1"></div>
        <div class="glow g2"></div>
        <div class="glow g3"></div>
      </div>
    </template>

    <!-- 文章页 h1 上方元信息条（分类/难度/日期/阅读时长） -->
    <template #doc-before>
      <MetaBar />
    </template>

    <!-- 圆形涟漪主题切换按钮（替换默认 VPSwitchAppearance） -->
    <template #nav-bar-content-after>
      <ThemeToggle />
    </template>

    <!-- 全站底部：构建说明 + 版权 + 备案号 -->
    <template #layout-bottom>
      <div class="site-footer">
        <span class="footer-item">基于 VitePress 构建</span>
        <span class="footer-item">Copyright © 2026 sresec.com</span>
        <a
          class="footer-item"
          href="https://beian.miit.gov.cn/"
          target="_blank"
          rel="noopener noreferrer"
        >
          黑ICP备2026011822号
        </a>
        <a
          class="footer-item footer-beian"
          href="https://beian.mps.gov.cn/#/query/webSearch?code=23022102000118"
          target="_blank"
          rel="noopener noreferrer"
        >
          <img src="/beian-police.png" alt="公安备案" />
          黑公网安备23022102000118号
        </a>
      </div>
    </template>



<style>
/* 主题切换圆形涟漪（View Transitions） */
::view-transition-old(root),
::view-transition-new(root) {
  animation: none;
  mix-blend-mode: normal;
}
::view-transition-new(root) {
  animation: switch-appearance 300ms ease-in;
}
.dark::view-transition-new(root) {
  animation: none;
}
.dark::view-transition-old(root) {
  animation: switch-appearance 300ms ease-in reverse forwards;
  z-index: 1;
}
@keyframes switch-appearance {
  from {
    clip-path: circle(0 at var(--switch-x) var(--switch-y));
  }
  to {
    clip-path: circle(var(--switch-r) at var(--switch-x) var(--switch-y));
  }
}
</style>
