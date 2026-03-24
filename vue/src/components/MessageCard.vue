<template>
  <div 
    class="bg-[var(--color-card-bg)] rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden hover:shadow-lg transition-all duration-200 cursor-pointer"
    @click="handleClick"
  >
    <div class="p-4">
      <!-- Actor Info -->
      <div class="flex items-center gap-3 mb-3">
        <div class="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-semibold">
          {{ actorInitial }}
        </div>
        <div class="flex-1 min-w-0">
          <h3 class="text-sm font-semibold text-gray-900 dark:text-white truncate">
            {{ message.actor_name || '未知演员' }}
          </h3>
          <p class="text-xs text-gray-500 dark:text-gray-400">
            {{ formatDate(message.created_at) }}
          </p>
        </div>
      </div>

      <!-- Media Preview -->
      <div v-if="message.media_count > 0" class="relative mb-2">
        <!-- Single Media: Natural aspect ratio with max height -->
        <div v-if="mediaPreviewItems.length === 1" class="relative inline-block">
          <img 
            :src="`file:///E:/AskTao/data/thumbs/${mediaPreviewItems[0].id}.webp`"
            :alt="`Media 1`"
            class="max-h-[500px] w-auto h-auto block"
          />
          
          <!-- Video Play Icon -->
          <div v-if="isVideo(mediaPreviewItems[0].mime_type)" class="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div class="w-10 h-10 bg-black/40 rounded-full flex items-center justify-center backdrop-blur-sm border border-white/30">
              <svg class="w-5 h-5 text-white ml-0.5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z"/>
              </svg>
            </div>
          </div>
          
          <!-- Duration Badge -->
          <div v-if="mediaPreviewItems[0].duration" class="absolute top-2 right-2 bg-black/70 text-white text-xs px-2 py-1 rounded backdrop-blur-sm">
            {{ formatDuration(mediaPreviewItems[0].duration) }}
          </div>
        </div>
        
        <!-- Multiple Media: Grid layout -->
        <div v-else class="grid gap-1" :class="mediaGridClass">
          <div 
            v-for="(item, index) in mediaPreviewItems" 
            :key="item.id"
            class="relative overflow-hidden rounded-lg bg-gray-100 dark:bg-gray-700"
            :class="mediaItemClass"
          >
            <img 
              :src="`file:///E:/AskTao/data/thumbs/${item.id}.webp`"
              :alt="`Media ${index + 1}`"
              class="w-full h-full object-cover"
            />
            
            <!-- Video Play Icon -->
            <div v-if="isVideo(item.mime_type)" class="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div class="w-10 h-10 bg-black/40 rounded-full flex items-center justify-center backdrop-blur-sm border border-white/30">
                <svg class="w-5 h-5 text-white ml-0.5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M8 5v14l11-7z"/>
                </svg>
              </div>
            </div>
            
            <!-- Duration Badge -->
            <div v-if="item.duration" class="absolute top-2 right-2 bg-black/70 text-white text-xs px-2 py-1 rounded backdrop-blur-sm">
              {{ formatDuration(item.duration) }}
            </div>
          </div>
        </div>
      </div>

      <!-- Message Text -->
      <div v-if="message.text" class="mb-3">
        <p class="text-sm text-gray-700 dark:text-gray-300 line-clamp-3">
          {{ message.text }}
        </p>
      </div>

      <!-- Tags -->
      <div v-if="messageTags.length > 0" class="flex flex-wrap gap-1.5 mt-3">
        <span 
          v-for="tag in messageTags" 
          :key="tag.id"
          class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-300"
        >
          {{ tag.name }}
        </span>
      </div>

      <!-- Media Count Badge -->
      <div v-if="message.media_count > 0" class="mt-3 flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
        <span>{{ message.media_count }} 个媒体</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Message, MessageMediaItem, TagItem } from '../types'

interface Props {
  message: Message
  mediaItems?: MessageMediaItem[]
  tags?: TagItem[]
}

const props = defineProps<Props>()

const emit = defineEmits<{
  click: [id: number]
}>()

const maxPreviewItems = 9

const actorInitial = computed(() => {
  if (!props.message.actor_name) return '?'
  return props.message.actor_name.charAt(0).toUpperCase()
})

const messageTags = computed(() => {
  return props.tags || []
})

const mediaPreviewItems = computed(() => {
  if (!props.mediaItems) return []
  return props.mediaItems.slice(0, maxPreviewItems)
})

const mediaGridClass = computed(() => {
  const count = mediaPreviewItems.value.length
  if (count === 1) return 'grid-cols-1'
  if (count === 2) return 'grid-cols-2'
  return 'grid-cols-3'
})

const mediaItemClass = computed(() => {
  const count = mediaPreviewItems.value.length
  if (count === 1) return 'max-h-[500px]'
  if (count === 2) return 'aspect-square'
  return 'aspect-square'
})

const isImage = (mimeType: string) => {
  return mimeType?.startsWith('image/')
}

const isVideo = (mimeType: string) => {
  return mimeType?.startsWith('video/')
}

const formatDuration = (duration: number | null): string => {
  if (!duration) return ''
  
  const totalSeconds = Math.round(duration)
  const hours = Math.floor(totalSeconds / 3600)
  const mins = Math.floor((totalSeconds % 3600) / 60)
  const secs = totalSeconds % 60
  
  if (hours > 0) {
    return `${hours}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  } else {
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

const handleClick = () => {
  emit('click', props.message.id)
}
</script>
