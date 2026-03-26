<template>
  <aside class="fixed left-0 top-0 bottom-0 w-64 z-50 bg-transparent transition-colors hidden md:flex flex-col">
    <div class="flex items-center justify-center h-16">
      <h1 class="text-xl font-bold text-white">系统</h1>
    </div>
    
    <nav class="flex-1 py-4 overflow-y-auto">
      <div class="space-y-1 px-3">
        <router-link
          to="/"
          class="flex items-center gap-3 px-4 py-3 rounded-lg text-gray-300 hover:bg-purple-900/30 hover:text-white transition-colors"
          active-class="bg-pink-600 text-white"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
          </svg>
          <span>消息</span>
        </router-link>
        <router-link
          to="/media"
          class="flex items-center gap-3 px-4 py-3 rounded-lg text-gray-300 hover:bg-purple-900/30 hover:text-white transition-colors"
          active-class="bg-pink-600 text-white"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
          <span>媒体</span>
        </router-link>
        <router-link
          to="/actor"
          class="flex items-center gap-3 px-4 py-3 rounded-lg text-gray-300 hover:bg-purple-900/30 hover:text-white transition-colors"
          active-class="bg-pink-600 text-white"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
          <span>演员</span>
        </router-link>
      </div>
    </nav>
    
    <div class="p-4">
      <button
        @click="toggleTheme"
        class="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-gray-300 hover:bg-purple-900/30 hover:text-white transition-colors"
        title="切换主题"
      >
        <svg v-if="theme === 'light'" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
        </svg>
        <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
        </svg>
        <span>{{ theme === 'light' ? '深色模式' : '浅色模式' }}</span>
      </button>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { useTheme } from '../composables/useTheme'

const { theme, toggleTheme } = useTheme()
</script>
