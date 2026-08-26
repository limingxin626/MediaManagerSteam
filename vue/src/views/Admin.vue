<template>
  <div class="h-full overflow-hidden">
    <div class="h-full max-w-7xl mx-auto px-4 py-6 flex flex-col min-h-0">
      <div class="shrink-0 flex gap-1 mb-6 border-b border-[var(--border-color)] overflow-x-auto overflow-y-hidden">
        <RouterLink
          v-for="tab in tabs"
          :key="tab.to"
          :to="tab.to"
          :class="[
            'shrink-0 px-4 py-2 text-sm font-medium border-b-2 transition-colors -mb-px',
            isActive(tab.to)
              ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400'
              : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
          ]"
        >
          {{ tab.label }}
        </RouterLink>
      </div>

      <div class="flex-1 min-h-0 overflow-y-auto">
        <RouterView />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'

const tabs = [
  { to: '/admin', label: '概览' },
  { to: '/admin/tables', label: '表浏览' },
  { to: '/admin/missing-files', label: '文件缺失' },
  { to: '/admin/duplicate-files', label: '重复文件' },
]

const route = useRoute()

function isActive(path: string) {
  return path === '/admin' ? route.path === path : route.path.startsWith(path)
}
</script>
