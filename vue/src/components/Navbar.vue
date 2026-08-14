<template>
  <aside class="app-sidebar hidden w-[52px] shrink-0 flex-col border-r border-[var(--border-color)] bg-[var(--sidebar-bg)] md:flex">
    <nav class="flex flex-1 flex-col items-center gap-1 py-2" aria-label="主导航">
      <router-link v-for="item in navigationItems" :key="item.path" :to="item.path"
        class="activity-item" :class="{ 'activity-item--active': isNavigationActive(route.path, item.path) }" :title="item.label" :aria-label="item.label">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round"><path :d="item.icon" /></svg>
      </router-link>
    </nav>
    <button class="activity-item mx-auto mb-2" :title="theme === 'light' ? '深色模式' : '浅色模式'" @click="toggleTheme">
      <svg v-if="theme === 'light'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.65"><path d="M20 15.2A8.5 8.5 0 0 1 8.8 4 8.5 8.5 0 1 0 20 15.2Z" /></svg>
      <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.65"><circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M4.9 4.9l1.4 1.4m11.4 11.4 1.4 1.4m0-14.2-1.4 1.4M6.3 17.7l-1.4 1.4"/></svg>
    </button>
  </aside>
</template>
<script setup lang="ts">
import { useRoute } from 'vue-router'
import { navigationItems, isNavigationActive } from '../config/navigation'
import { useTheme } from '../composables/useTheme'
const route = useRoute()
const { theme, toggleTheme } = useTheme()
</script>
<style scoped>
.activity-item { position: relative; display: grid; width: 44px; height: 44px; place-items: center; color: var(--text-muted); transition: color 100ms ease, background-color 100ms ease; }
.activity-item:hover { color: var(--text-primary); background: rgba(127,127,127,.09); }
.activity-item svg { width: 23px; height: 23px; }
.activity-item--active { color: var(--text-primary); }
.activity-item--active::before { content: ''; position: absolute; left: 0; top: 8px; bottom: 8px; width: 2px; border-radius: 0 2px 2px 0; background: var(--color-primary-500); }
</style>
