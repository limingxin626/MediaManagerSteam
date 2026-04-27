<template>
  <div class="fixed bottom-6 left-1/2 transform -translate-x-1/2 z-50 md:hidden">
    <nav class="bg-white/80 dark:bg-gray-800/80 backdrop-blur-lg rounded-full shadow-xl border border-gray-200 dark:border-gray-700 px-4 py-2 flex items-center gap-6">
      <button
        v-for="item in navItems"
        :key="item.path"
        @click="navigateTo(item.path)"
        :class="[
          'flex flex-col items-center justify-center gap-1 px-4 py-3 rounded-full transition-all',
          isActive(item.path) ? 'bg-[var(--color-primary-500)]/15 text-[var(--color-primary-600)]' : 'text-gray-600 dark:text-gray-400 hover:text-[var(--color-primary-600)]'
        ]"
      >
        <svg :class="['w-5 h-5']" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path :stroke-linecap="'round'" :stroke-linejoin="'round'" :stroke-width="'2'" :d="item.icon" />
        </svg>
        <span class="text-xs font-medium">{{ item.label }}</span>
      </button>
    </nav>
  </div>
</template>

<script setup lang="ts">
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

const navItems = [
  {
    path: '/',
    label: '主页',
    icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6'
  },
  {
    path: '/messages',
    label: '消息',
    icon: 'M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10'
  },
  {
    path: '/media',
    label: '媒体',
    icon: 'M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z'
  },
  {
    path: '/admin',
    label: '管理',
    icon: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065zM15 12a3 3 0 11-6 0 3 3 0 016 0z'
  }
]

const navigateTo = (path: string) => {
  router.push(path)
}

const isActive = (path: string) => {
  return route.path === path
}
</script>

<style scoped>
/* 额外的样式可以在这里添加 */
</style>