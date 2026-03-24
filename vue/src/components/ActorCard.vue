<template>
  <div 
    class="bg-[var(--color-card-bg)] rounded-xl shadow-sm border border-gray-700 overflow-hidden hover:shadow-lg transition-all hover:scale-[1.02] duration-200 cursor-pointer flex flex-col"
    @click="$emit('click', actor.id)"
  >

    <!-- Thumbnail -->
    <div class="bg-gray-100 dark:bg-gray-700 overflow-hidden aspect-[3/4]">
      <img 
        :src="`file:///E:/AskTao/data/actor_cover/${actor.id}.webp`" 
        :alt="actor.name" 
        class="w-full h-full object-cover"
      />
    </div>

    <div class="p-4 mt-auto">
      <!-- Card Header -->
      <div class="flex justify-between items-start mb-4">
        <div>
          <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-1 truncate">{{ actor.name }}</h3>
        </div>
      </div>

      <!-- Card Content -->
      <div class="flex items-center gap-4 mb-3">
        <div class="flex items-start flex-1">
          <svg class="w-5 h-5 text-gray-400 mt-0.5 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
          <div>
            <p class="text-xs text-gray-500 dark:text-gray-400 mb-0.5">分类</p>
            <p class="text-sm text-gray-900 dark:text-gray-100">{{ actor.category }}</p>
          </div>
        </div>

        <div class="flex items-start flex-1">
          <svg class="w-5 h-5 text-gray-400 mt-0.5 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
          </svg>
          <div>
            <p class="text-xs text-gray-500 dark:text-gray-400 mb-0.5">评分</p>
            <p class="text-sm text-gray-900 dark:text-gray-100">{{ (actor.score || 0).toFixed(1) }}</p>
          </div>
        </div>
      </div>

      <!-- Download Status -->
      <div class="flex items-center gap-2 mb-3">
        <svg class="w-5 h-5 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
        </svg>
        <div>
          <p class="text-xs text-gray-500 dark:text-gray-400 mb-0.5">下载状态</p>
          <p 
            class="text-sm font-medium"
            :class="{
              'text-gray-600 dark:text-gray-300': actor.download_status === '未下载',
              'text-yellow-600 dark:text-yellow-400': actor.download_status === '非原档',
              'text-green-600 dark:text-green-400': actor.download_status === '原档'
            }"
          >
            {{ actor.download_status || '未下载' }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Actor } from '../types'
import { API_BASE_URL } from '../utils/constants'

interface Props {
  actor: Actor
}

defineProps<Props>()

defineEmits<{
  click: [id: number]
  edit: [actor: Actor]
  delete: [id: number]
}>()


</script>
