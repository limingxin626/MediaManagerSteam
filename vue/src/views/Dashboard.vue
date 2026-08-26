<template>
  <div class="h-full overflow-y-auto pb-8">
    <div class="max-w-7xl w-full mx-auto px-4 pt-6 space-y-4">
      <nav class="grid grid-cols-4 gap-3 md:hidden" aria-label="主页导航">
        <RouterLink
          v-for="item in homeNavigationItems"
          :key="item.path"
          :to="item.path"
          class="flex min-w-0 flex-col items-center gap-2 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] px-2 py-3 text-[var(--text-secondary)] shadow-[var(--shadow-sm)] transition-colors hover:bg-[var(--bg-secondary)] hover:text-[var(--color-primary-600)]"
        >
          <svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
            <path :d="item.icon" />
          </svg>
          <span class="w-full truncate text-center text-xs font-medium">{{ item.label }}</span>
        </RouterLink>
      </nav>

      <HeatmapCard />

      <IssueBoard />
    </div>
  </div>
</template>

<script setup lang="ts">
import HeatmapCard from '../components/dashboard/HeatmapCard.vue'
import IssueBoard from '../components/dashboard/IssueBoard.vue'
import { navigationItems } from '../config/navigation'

defineOptions({ name: 'Dashboard' })

const homeNavigationItems = navigationItems.filter(item => item.path !== '/')
</script>
