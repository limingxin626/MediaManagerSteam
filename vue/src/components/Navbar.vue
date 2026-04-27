<template>
  <aside class="fixed left-0 top-0 bottom-0 w-16 z-50 bg-[var(--sidebar-bg)] transition-colors hidden md:flex flex-col border-r border-[var(--border-color)]">
    <div class="flex items-center justify-center h-16">
      <svg class="w-6 h-6 text-gray-800 dark:text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
      </svg>
    </div>

    <nav class="flex-1 py-4 overflow-y-auto">
      <div class="space-y-1 px-2">
        <router-link
          to="/"
          class="flex items-center justify-center p-3 rounded-lg text-gray-500 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-purple-900/30 hover:text-gray-900 dark:hover:text-white transition-colors"
          active-class="bg-[var(--color-primary-600)] text-white dark:text-white"
          title="主页"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
          </svg>
        </router-link>
        <router-link
          to="/messages"
          class="flex items-center justify-center p-3 rounded-lg text-gray-500 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-purple-900/30 hover:text-gray-900 dark:hover:text-white transition-colors"
          active-class="bg-[var(--color-primary-600)] text-white dark:text-white"
          title="消息"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
          </svg>
        </router-link>
        <router-link
          to="/media"
          class="flex items-center justify-center p-3 rounded-lg text-gray-500 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-purple-900/30 hover:text-gray-900 dark:hover:text-white transition-colors"
          active-class="bg-[var(--color-primary-600)] text-white dark:text-white"
          title="媒体"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
        </router-link>
        <router-link
          to="/admin"
          class="flex items-center justify-center p-3 rounded-lg text-gray-500 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-purple-900/30 hover:text-gray-900 dark:hover:text-white transition-colors"
          active-class="bg-[var(--color-primary-600)] text-white dark:text-white"
          title="管理"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </router-link>
      </div>
    </nav>

    <div class="p-2">
      <button
        @click="toggleTheme"
        class="w-full flex items-center justify-center p-3 rounded-lg text-gray-500 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-purple-900/30 hover:text-gray-900 dark:hover:text-white transition-colors"
        :title="theme === 'light' ? '深色模式' : '浅色模式'"
      >
        <svg v-if="theme === 'light'" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
        </svg>
        <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
        </svg>
      </button>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { useTheme } from '../composables/useTheme'

const { theme, toggleTheme } = useTheme()
</script>
