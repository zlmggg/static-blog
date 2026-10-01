<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useData, useRoute } from 'vitepress'

// 文章页 h1 上方的元信息条：分类 chip + 难度色标 + 日期 + 阅读时长
// 字段来自 frontmatter：category / difficulty(初级|中级|高级) / date(YYYY-MM-DD)
const { frontmatter, isDark } = useData()
const route = useRoute()

const fm = computed<Record<string, any>>(() => frontmatter.value || {})

// category / difficulty / date 三者全缺时整个组件不渲染（聚合页/索引页因此无空条）
const hasAny = computed(
  () => !!(fm.value.category || fm.value.difficulty || fm.value.date)
)

// frontmatter.date 会被 VitePress 解析成 Date 对象，统一格式化为 YYYY-MM-DD
const dateStr = computed(() => {
  const d = fm.value.date
  if (!d) return ''
  if (d instanceof Date) {
    const p = (n: number) => String(n).padStart(2, '0')
    return `${d.getUTCFullYear()}-${p(d.getUTCMonth() + 1)}-${p(d.getUTCDate())}`
  }
  return String(d).slice(0, 10)
})

// 难度色标：初级 绿 / 中级 黄 / 高级 红（深色用亮色、浅色用加深档，淡底）
const DIFF_STYLE: Record<
  string,
  { colorLight: string; colorDark: string; bg: string; border: string }
> = {
  初级: { colorLight: '#047857', colorDark: '#34d399', bg: 'rgba(52, 211, 153, 0.14)', border: 'rgba(52, 211, 153, 0.45)' },
  中级: { colorLight: '#b45309', colorDark: '#fbbf24', bg: 'rgba(251, 191, 36, 0.16)', border: 'rgba(251, 191, 36, 0.45)' },
  高级: { colorLight: '#dc2626', colorDark: '#f87171', bg: 'rgba(248, 113, 113, 0.14)', border: 'rgba(248, 113, 113, 0.45)' }
}
// 深色模式下难度文字用更亮一档

const minutes = ref(1)

function calcReading() {
  // 读取正文（.vp-doc）纯文本；CJK 按 ~380 字/分钟、其余（含代码）按 ~300 字符/分钟
  const root = document.querySelector('.vp-doc')
  if (!root) return
  const text = root.textContent || ''
  const cjk = (text.match(/[一-鿿　-〿＀-￯]/g) || []).length
  const other = text.replace(/[一-鿿　-〿＀-￯\s]/g, '').length
  minutes.value = Math.max(1, Math.ceil(cjk / 380 + other / 300))
}

onMounted(() => {
  calcReading()
})

// 路由切换后正文 DOM 会整体替换，等下一帧重新统计
watch(
  () => route.path,
  () => {
    setTimeout(calcReading, 250)
  }
)
</script>

<template>
  <div v-if="hasAny" class="vp-metabar">
    <span v-if="fm.category" class="chip chip-cat">{{ fm.category }}</span>
    <span
      v-if="fm.difficulty && DIFF_STYLE[fm.difficulty]"
      class="chip chip-diff"
      :style="{
        color: isDark ? DIFF_STYLE[fm.difficulty].colorDark : DIFF_STYLE[fm.difficulty].colorLight,
        background: DIFF_STYLE[fm.difficulty].bg,
        borderColor: DIFF_STYLE[fm.difficulty].border
      }"
    >
      {{ fm.difficulty }}
    </span>
    <span v-if="dateStr" class="meta-date">{{ dateStr }}</span>
    <span v-if="dateStr" class="meta-sep">·</span>
    <span class="meta-read">阅读约 {{ minutes }} 分钟</span>
  </div>
</template>

<style scoped>
.vp-metabar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  margin: 4px 0 18px;
  font-size: 13px;
}
.chip {
  display: inline-flex;
  align-items: center;
  padding: 3px 11px;
  border-radius: 999px;
  font-size: 12.5px;
  font-weight: 500;
  line-height: 1.5;
}
.chip-cat {
  color: var(--vp-c-brand-1);
  background: color-mix(in srgb, var(--vp-c-brand-1) 12%, transparent);
  border: 1px solid color-mix(in srgb, var(--vp-c-brand-1) 35%, transparent);
}
.chip-diff {
  border: 1px solid transparent;
}
.meta-date {
  font-family: var(--vp-font-family-mono);
  font-size: 12.5px;
  color: var(--vp-c-text-3, var(--vp-c-text-2));
}
.meta-sep {
  color: var(--vp-c-text-3, var(--vp-c-text-2));
  opacity: 0.6;
}
.meta-read {
  color: var(--vp-c-text-2);
}
</style>
