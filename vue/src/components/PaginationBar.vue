<template>
  <div v-if="totalItems > 0" :class="[isSplitView ? 'left-[24%]' : 'left-1/2', 'fixed bottom-6 transform -translate-x-1/2 z-40']">
    <div class="bg-white/80 dark:bg-gray-800/80 backdrop-blur-lg rounded-full shadow-xl border border-gray-200 dark:border-gray-700 px-6 py-3 flex items-center gap-4">
      <div class="text-sm text-gray-500 dark:text-gray-400">
        {{ (currentPage - 1) * pageSize + 1 }} - {{ Math.min(currentPage * pageSize, totalItems) }} / {{ totalItems }}
      </div>
      <button
        @click="$emit('first')"
        :disabled="currentPage === 1"
        class="px-4 py-2 rounded-full border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
        title="第一页"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
        </svg>
      </button>
      <button
        @click="$emit('prev')"
        :disabled="currentPage === 1"
        class="px-4 py-2 rounded-full border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
        title="上一页"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <div class="flex items-center gap-1">
        <span class="px-4 py-2 rounded-full bg-indigo-100 dark:bg-indigo-900 text-indigo-700 dark:text-indigo-400 font-medium">{{ currentPage }}</span>
        <span class="text-sm text-gray-500 dark:text-gray-400">/</span>
        <span class="text-sm text-gray-500 dark:text-gray-400">{{ totalPages }}</span>
      </div>
      <button
        @click="$emit('next')"
        :disabled="currentPage === totalPages"
        class="px-4 py-2 rounded-full border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
        title="下一页"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
        </svg>
      </button>
      <button
        @click="$emit('last')"
        :disabled="currentPage === totalPages"
        class="px-4 py-2 rounded-full border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
        title="最后一页"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 5l7 7-7 7M5 5l7 7-7 7" />
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  currentPage: number
  totalPages: number
  totalItems: number
  pageSize: number
  isSplitView?: boolean
}>()

defineEmits<{
  first: []
  prev: []
  next: []
  last: []
}>()
</script>
