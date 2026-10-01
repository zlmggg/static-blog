<script setup lang="ts">
import { inject } from 'vue'

// 由 Layout.vue provide('toggle-appearance') 注入：带圆形涟漪的深浅色切换
const toggle = inject<(e: MouseEvent) => void>('toggle-appearance')
</script>

<template>
  <button
    class="theme-btn theme-toggle-btn"
    title="切换深浅色"
    aria-label="切换深浅色"
    @click="toggle?.($event)"
  >
    <svg
      class="sun"
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="2"
      stroke-linecap="round"
    >
      <circle cx="12" cy="12" r="4" />
      <path
        d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"
      />
    </svg>
    <svg
      class="moon"
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
    >
      <path d="M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8z" />
    </svg>
  </button>
</template>
