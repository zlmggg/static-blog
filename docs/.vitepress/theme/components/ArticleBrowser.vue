<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Article, Level } from '../data/types'

/**
 * ArticleBrowser —— 聚合页文章浏览器（逐字复刻内容页小样「索引页」）
 * 用法（md 中）：<ArticleBrowser :articles="articles" />
 */
const props = withDefaults(
  defineProps<{
    /** 文章列表（必填） */
    articles: Article[]
    /** 搜索框占位文案 */
    placeholder?: string
    /** 分组展示顺序；缺省按 articles 中首次出现顺序 */
    groupOrder?: string[]
    /** 分组是否默认折叠 */
    defaultCollapsed?: boolean
  }>(),
  {
    placeholder: '搜索标题、标签、描述…',
    groupOrder: () => [],
    defaultCollapsed: false
  }
)

/* ---------- 搜索 & 难度筛选 ---------- */
const kw = ref('')
const diff = ref<'all' | Level>('all')

/** 仅当存在带 lvl 的文章时才渲染难度 tabs */
const hasLvl = computed(() => props.articles.some((a) => a.lvl))

const DIFF_TABS: { key: 'all' | Level; label: string }[] = [
  { key: 'all', label: '全部' },
  { key: 'easy', label: '初级' },
  { key: 'mid', label: '中级' },
  { key: 'hard', label: '高级' }
]

/** 行内难度徽章单字（tabs 用全称，逐字照小样） */
const lvlLabel: Record<Level, string> = { easy: '初', mid: '中', hard: '高' }

/* ---------- 分组顺序与折叠 ---------- */
const order = computed<string[]>(() => {
  if (props.groupOrder && props.groupOrder.length) return props.groupOrder
  const seen: string[] = []
  for (const a of props.articles) if (!seen.includes(a.group)) seen.push(a.group)
  return seen
})

const collapsed = ref<Set<string>>(
  new Set(props.defaultCollapsed ? order.value : [])
)
function toggleGroup(name: string) {
  const next = new Set(collapsed.value)
  if (next.has(name)) next.delete(name)
  else next.add(name)
  collapsed.value = next
}

/* ---------- 过滤逻辑 ---------- */
const filtered = computed(() => {
  const k = kw.value.trim().toLowerCase()
  return props.articles.filter((a) => {
    if (diff.value !== 'all' && a.lvl !== diff.value) return false
    if (!k) return true
    const hay = `${a.group} ${a.title} ${a.sub ?? ''} ${(a.tags ?? []).join(' ')}`.toLowerCase()
    return hay.includes(k)
  })
})

/** 过滤后分组：空组整个隐藏 */
const groups = computed(() =>
  order.value
    .map((name) => ({
      name,
      items: filtered.value.filter((a) => a.group === name)
    }))
    .filter((g) => g.items.length > 0)
)

const empty = computed(() => filtered.value.length === 0)
</script>

<template>
  <div class="ab-browser">
    <!-- 工具栏：实时搜索 + 难度 tabs（仅有 lvl 数据时渲染） -->
    <div class="idx-toolbar">
      <div class="idx-search">
        <svg
          width="17"
          height="17"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
        >
          <circle cx="11" cy="11" r="7" />
          <path d="m21 21-4.3-4.3" />
        </svg>
        <input v-model="kw" type="text" :placeholder="placeholder" />
      </div>
      <div v-if="hasLvl" class="filter-tabs">
        <button
          v-for="t in DIFF_TABS"
          :key="t.key"
          class="ftab"
          :class="{ active: diff === t.key }"
          @click="diff = t.key"
        >
          {{ t.label }}
        </button>
      </div>
    </div>

    <!-- 可折叠分组 -->
    <div
      v-for="g in groups"
      :key="g.name"
      class="idx-group"
      :class="{ collapsed: collapsed.has(g.name) }"
    >
      <div class="g-head" @click="toggleGroup(g.name)">
        <h2>{{ g.name }}</h2>
        <span class="count">{{ g.items.length }} 篇</span>
        <span class="care">
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2.2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="m6 9 6 6 6-6" />
          </svg>
        </span>
      </div>
      <div class="g-body art-list">
        <a v-for="a in g.items" :key="a.link" class="art-row" :href="a.link">
          <div class="art-main">
            <div class="art-title">{{ a.title }}</div>
            <div v-if="a.sub" class="art-sub">{{ a.sub }}</div>
          </div>
          <div v-if="a.tags && a.tags.length" class="art-tags">
            <span v-for="t in a.tags" :key="t" class="tag">{{ t }}</span>
          </div>
          <span v-if="a.lvl" class="lvl" :class="a.lvl">{{ lvlLabel[a.lvl] }}</span>
          <span v-if="a.date" class="art-date">{{ a.date }}</span>
          <span class="arrow">
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2.2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path d="M5 12h14M13 6l6 6-6 6" />
            </svg>
          </span>
        </a>
      </div>
    </div>

    <!-- 空态 -->
    <div v-if="empty" class="empty-hint">没有匹配的文章，换个关键词或筛选条件试试。</div>
  </div>
</template>

<style scoped>
/* 设计 token 自包含（复刻小样 --surface/--border/--text/--muted，深浅色各自一份） */
.ab-browser {
  --surface: rgba(255, 255, 255, 0.035);
  --border: rgba(255, 255, 255, 0.09);
  --text: #ececf3;
  --muted: #9a9ab0;
}
html:not(.dark) .ab-browser {
  --surface: rgba(255, 255, 255, 0.78);
  --border: rgba(30, 35, 70, 0.09);
  --text: #181b28;
  --muted: #585e76;
}

/* 工具栏 */
.idx-toolbar {
  display: flex;
  gap: 14px;
  margin: 30px 0 10px;
  align-items: center;
  flex-wrap: wrap;
}
.idx-search {
  flex: 1;
  min-width: 250px;
  display: flex;
  align-items: center;
  gap: 11px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 11px 16px;
  color: var(--muted);
}
.idx-search:focus-within {
  border-color: var(--brand-1);
}
.idx-search input {
  flex: 1;
  background: none;
  border: none;
  outline: none;
  color: var(--text);
  font-size: 14px;
  font-family: inherit;
}
.idx-search input::placeholder {
  color: var(--muted);
}
.filter-tabs {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
}
.ftab {
  padding: 8px 15px;
  border-radius: 9px;
  font-size: 13px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--muted);
  cursor: pointer;
  transition: 0.2s;
  font-family: inherit;
}
.ftab:hover {
  background: var(--surface);
  color: var(--text);
}
.ftab.active {
  background: color-mix(in srgb, var(--brand-1) 16%, transparent);
  color: var(--brand-1);
  border-color: color-mix(in srgb, var(--brand-1) 32%, transparent);
}

/* 分组 */
.idx-group {
  margin-top: 26px;
}
.g-head {
  display: flex;
  align-items: center;
  gap: 11px;
  cursor: pointer;
  user-select: none;
  margin-bottom: 4px;
}
.g-head h2 {
  font-size: 19px;
  font-weight: 600;
  margin: 0;
  line-height: 1.3;
}
.g-head .count {
  font-size: 12px;
  color: var(--muted);
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 2px 11px;
  background: var(--surface);
}
.g-head .care {
  margin-left: auto;
  transition: 0.25s;
  color: var(--muted);
  display: inline-flex;
}
.idx-group.collapsed .g-body {
  display: none;
}
.idx-group.collapsed .care {
  transform: rotate(-90deg);
}

/* 文章行 */
.art-list {
  display: flex;
  flex-direction: column;
}
.art-row {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 13px 15px;
  border-radius: 12px;
  cursor: pointer;
  border: 1px solid transparent;
  transition: 0.2s;
  color: inherit;
  text-decoration: none;
  margin: 0;
}
.art-row:hover {
  background: var(--surface);
  border-color: var(--border);
}
.art-main {
  flex: 1;
  min-width: 0;
}
.art-title {
  font-size: 15px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 9px;
  flex-wrap: wrap;
}
.art-sub {
  margin-top: 4px;
  font-size: 13px;
  color: var(--muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.art-tags {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
  flex-wrap: wrap;
  justify-content: flex-end;
  max-width: 250px;
}
.tag {
  font-size: 11.5px;
  color: var(--muted);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 2px 8px;
}
.lvl {
  font-size: 11.5px;
  font-weight: 600;
  border-radius: 6px;
  padding: 2px 10px;
  flex-shrink: 0;
}
.lvl.easy {
  color: #34d399;
  background: rgba(52, 211, 153, 0.12);
}
.lvl.mid {
  color: #fbbf24;
  background: rgba(251, 191, 36, 0.12);
}
.lvl.hard {
  color: #f87171;
  background: rgba(248, 113, 113, 0.14);
}
.art-date {
  font-size: 12px;
  color: var(--muted);
  font-family: var(--vp-font-family-mono, monospace);
  flex-shrink: 0;
  width: 86px;
  text-align: right;
}
.art-row .arrow {
  color: var(--muted);
  flex-shrink: 0;
  transition: 0.2s;
  display: inline-flex;
}
.art-row:hover .arrow {
  color: var(--brand-1);
  transform: translateX(3px);
}
.empty-hint {
  padding: 48px 10px;
  text-align: center;
  color: var(--muted);
  font-size: 14px;
}

/* 响应式（逐字照小样 ≤820：隐藏 tags、date 自适应） */
@media (max-width: 820px) {
  .art-tags {
    display: none;
  }
  .art-date {
    width: auto;
  }
}
</style>
