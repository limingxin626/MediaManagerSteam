<template>
  <header class="window-drag fixed inset-x-0 top-0 z-[100] flex h-9 select-none items-center border-b border-[var(--border-color)] bg-[var(--sidebar-bg)] pr-[140px] text-[var(--text-secondary)]">
    <div class="flex min-w-0 items-center gap-2.5 px-3">
      <div class="grid h-[18px] w-[18px] place-items-center rounded-[4px] bg-[var(--color-primary-600)] text-[10px] font-semibold text-white">M</div>
      <span class="truncate text-xs font-medium tracking-[0.01em]">Media Manager</span>
    </div>
  </header>
</template>

<script setup lang="ts">
import { watch } from 'vue'
import { useTheme } from '../composables/useTheme'

const { theme } = useTheme()
watch(theme, value => window.electronAPI?.setTitleBarTheme(value === 'dark'), { immediate: true })
</script>
