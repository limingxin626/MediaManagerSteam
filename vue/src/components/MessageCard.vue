<template>
  <div
    class="group bg-(--color-card-bg) rounded-xl shadow-sm border border-white/10 overflow-hidden hover:shadow-lg transition-all duration-200 cursor-pointer"
    :class="{ 'ring-2 ring-indigo-500 border-indigo-500': props.selected }"
    @click="handleClick"
  >
    <div class="p-4">
      <!-- Actor Info -->
      <div class="flex items-center justify-between mb-3">
        <div class="flex items-center gap-3">
          <!-- Selection checkbox -->
          <div
            v-if="props.selectable"
            @click.stop="emit('toggle-select', props.message.id)"
            class="shrink-0 w-6 h-6 rounded-md border-2 flex items-center justify-center transition-colors"
            :class="props.selected
              ? 'bg-indigo-600 border-indigo-600 text-white'
              : 'border-gray-600 hover:border-indigo-400'"
          >
            <svg v-if="props.selected" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <div class="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-semibold">
            {{ actorInitial }}
          </div>
          <div class="flex-1 min-w-0">
            <h3 class="text-sm font-semibold text-white truncate">
              {{ message.actor_name || '未知' }}
            </h3>
            <p class="text-xs text-gray-400">
              {{ formatDate(message.created_at) }}
            </p>
          </div>
        </div>
        <div class="flex items-center gap-1">
          <button
            @click.stop="handleToggleStar"
            class="p-1.5 rounded-lg transition-colors"
            :class="props.message.starred
              ? 'text-yellow-400 hover:text-yellow-500'
              : 'text-gray-400 hover:text-yellow-400 opacity-0 group-hover:opacity-100'"
            :title="props.message.starred ? '取消收藏' : '收藏'"
          >
            <svg class="w-4 h-4" :fill="props.message.starred ? 'currentColor' : 'none'" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
            </svg>
          </button>
          <button
            @click.stop="handleDelete"
            class="p-1.5 text-gray-400 hover:text-red-500 rounded-lg hover:bg-red-900/20 transition-colors opacity-0 group-hover:opacity-100"
            title="删除消息"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Unified Media Preview -->
      <div v-if="mediaPreviewItems.length > 0" class="relative rounded-xl overflow-hidden mb-2">
        <div
          class="grid gap-0.5"
          :class="mediaGridClass"
        >
          <div
            v-for="(item, index) in mediaPreviewItems"
            :key="item.id"
            class="relative overflow-hidden bg-gray-800 cursor-pointer"
            :class="mediaItemClass(index)"
            @click.stop="handleMediaClick(index)"
          >
            <img
              :src="resolveUrl(item.thumb_url)"
              :alt="`Media ${index + 1}`"
              class="w-full h-full object-cover transition-transform duration-200 hover:scale-105"
            />

            <!-- Video overlay -->
            <div v-if="isVideo(item.mime_type)" class="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div class="w-10 h-10 bg-black/50 rounded-full flex items-center justify-center backdrop-blur-sm border border-white/20">
                <svg class="w-5 h-5 text-white ml-0.5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M8 5v14l11-7z"/>
                </svg>
              </div>
            </div>

            <!-- Duration badge -->
            <div v-if="item.duration" class="absolute bottom-1.5 left-1.5 bg-black/70 text-white text-[10px] px-1.5 py-0.5 rounded backdrop-blur-sm font-medium">
              {{ formatDuration(item.duration) }}
            </div>

            <!-- Menu Button -->
            <div class="absolute top-1.5 right-1.5">
              <button
                @click.stop="toggleMenu(index)"
                class="w-6 h-6 bg-black/50 hover:bg-black/80 text-white rounded-full flex items-center justify-center backdrop-blur-sm transition-colors opacity-0 group-hover:opacity-100"
                :class="{ 'opacity-100!': activeMenuIndex === index }"
              >
                <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"/>
                </svg>
              </button>

              <div v-if="activeMenuIndex === index" class="absolute top-8 right-0 bg-gray-800 rounded-lg shadow-lg border border-white/10 py-1 min-w-[140px] z-10">
                <button
                  @click.stop="findMessagesByMedia(item.id)"
                  class="w-full px-4 py-2 text-left text-sm text-gray-300 hover:bg-white/10 transition-colors"
                >
                  查找所有message
                </button>
              </div>
            </div>

            <!-- "More" overlay on last item -->
            <div
              v-if="index === mediaPreviewItems.length - 1 && remainingCount > 0"
              class="absolute inset-0 bg-black/50 flex items-center justify-center pointer-events-none"
            >
              <span class="text-white text-2xl font-semibold">+{{ remainingCount }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Message Text -->
      <div v-if="message.text" class="mb-2">
        <p class="text-sm text-gray-300 whitespace-pre-line line-clamp-4">{{ message.text }}</p>
      </div>

      <!-- Tags & Media count row -->
      <div v-if="messageTags.length > 0 || message.media_count > 0" class="flex items-center gap-2 mt-2 flex-wrap">
        <span
          v-for="tag in messageTags"
          :key="tag.id"
          class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-indigo-900/30 text-indigo-300"
        >
          {{ tag.name }}
        </span>
        <span v-if="message.media_count > 0" class="inline-flex items-center gap-1 text-xs text-gray-500 ml-auto">
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          {{ message.media_count }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Message, MessageMediaItem, TagItem } from '../types'
import { isVideo, formatDuration, resolveUrl } from '../utils/media'

interface Props {
  message: Message
  mediaItems?: MessageMediaItem[]
  tags?: TagItem[]
  selectable?: boolean
  selected?: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  click: [id: number]
  'media-click': [mediaIndex: number]
  delete: [id: number]
  'find-messages-by-media': [mediaId: number]
  'toggle-select': [id: number]
  'toggle-star': [id: number]
}>()

const maxPreviewItems = 9
const activeMenuIndex = ref<number | null>(null)

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

const remainingCount = computed(() => {
  if (!props.mediaItems) return 0
  return Math.max(0, props.mediaItems.length - maxPreviewItems)
})

// Telegram-style grid: 1→full, 2→2col, 3→left big + right 2 small, 4→2x2, 5+→3col
const mediaGridClass = computed(() => {
  const count = mediaPreviewItems.value.length
  if (count === 1) return 'grid-cols-1'
  if (count === 2) return 'grid-cols-2'
  if (count === 3) return 'grid-cols-3 grid-rows-2'
  if (count === 4) return 'grid-cols-2'
  return 'grid-cols-3'
})

const mediaItemClass = (index: number) => {
  const count = mediaPreviewItems.value.length
  if (count === 1) return 'aspect-video'
  if (count === 3 && index === 0) return 'col-span-2 row-span-2'
  if (count === 3) return 'aspect-square'
  return 'aspect-square'
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

const handleMediaClick = (index: number) => {
  emit('media-click', index)
}

const handleDelete = () => {
  emit('delete', props.message.id)
}

const handleToggleStar = () => {
  emit('toggle-star', props.message.id)
}

const toggleMenu = (index: number) => {
  if (activeMenuIndex.value === index) {
    activeMenuIndex.value = null
  } else {
    activeMenuIndex.value = index
  }
}

const findMessagesByMedia = (mediaId: number) => {
  activeMenuIndex.value = null
  emit('find-messages-by-media', mediaId)
}
</script>
