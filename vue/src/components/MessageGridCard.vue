<template>
  <div ref="cardRef"
    class="group relative flex flex-col h-80 bg-[var(--bg-card)] rounded-[var(--radius-lg)] shadow-[var(--shadow-sm)] border border-[var(--border-color)] overflow-hidden hover:shadow-[var(--shadow-md)] transition-shadow duration-200 cursor-pointer"
    :class="{ 'animate-in': isVisible, 'opacity-0': !isVisible, 'ring-2 ring-[var(--color-primary-500)] border-transparent': props.selected }"
    @click="handleClick">

    <!-- Selection checkbox (merge mode) -->
    <div v-if="props.selectable" @click.stop="emit('toggle-select', props.message.id)"
      class="absolute top-2 left-2 z-10 w-6 h-6 rounded-md border-2 flex items-center justify-center transition-colors" :class="props.selected
        ? 'bg-[var(--color-primary-600)] border-[var(--color-primary-600)] text-white'
        : 'bg-black/30 border-white/70 hover:border-white'">
      <svg v-if="props.selected" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
      </svg>
    </div>

    <!-- Cover (仅有媒体时占固定高) -->
    <div v-if="cover"
      class="relative bg-gray-100 dark:bg-gray-800 overflow-hidden"
      :class="message.text ? 'h-40 shrink-0' : 'flex-1 min-h-0'">
      <img :src="resolveThumb(cover)" alt="cover"
        class="w-full h-full object-cover transition-transform duration-200 group-hover:scale-105" />
      <div class="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors duration-200 pointer-events-none"></div>
      <template v-if="isVideo(cover.mime_type)">
        <div class="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div class="w-10 h-10 bg-black/50 rounded-full flex items-center justify-center backdrop-blur-sm border border-white/20">
            <svg class="w-5 h-5 text-white ml-0.5" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z" /></svg>
          </div>
        </div>
      </template>
      <div v-if="cover.duration_ms"
        class="absolute bottom-1.5 left-1.5 bg-black/70 text-white text-[10px] px-1.5 py-0.5 rounded backdrop-blur-sm font-medium">
        {{ formatDuration(cover.duration_ms) }}
      </div>
      <div v-if="extraMediaCount > 0"
        class="absolute top-1.5 right-1.5 bg-black/60 text-white text-[10px] px-1.5 py-0.5 rounded-full backdrop-blur-sm font-medium">
        +{{ extraMediaCount }}
      </div>
    </div>

    <!-- Body -->
    <div class="flex flex-col min-h-0 p-3" :class="message.text || !cover ? 'flex-1' : 'shrink-0'">
      <!-- Text excerpt (fills remaining space; 无图时铺满整卡显示更多行) -->
      <div v-if="message.text"
        class="markdown-body markdown-body--compact text-[var(--text-secondary)] flex-1 min-h-0 overflow-hidden mb-2">
        <div v-html="renderedText"></div>
      </div>
      <!-- 无图无文字：留占位图标 + spacer -->
      <div v-else-if="!cover" class="flex-1 min-h-0 flex items-center justify-center">
        <svg class="w-8 h-8 text-[var(--text-muted)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
            d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
      </div>

      <!-- Tags -->
      <div v-if="messageTags.length > 0" class="flex items-center gap-1 flex-nowrap overflow-hidden mb-2">
        <span v-for="tag in visibleTags" :key="tag.id" class="tag-chip shrink-0">{{ tag.name }}</span>
        <span v-if="hiddenTagCount > 0" class="text-[10px] text-[var(--text-muted)] shrink-0">+{{ hiddenTagCount }}</span>
      </div>

      <!-- Meta row -->
      <div class="flex items-center justify-between gap-2 pt-1 text-[10px] text-[var(--text-muted)]">
        <span class="truncate">{{ formatDate(message.created_at) }}</span>
        <span v-if="message.media_count > 0" class="inline-flex items-center gap-0.5 tabular-nums shrink-0">
          <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          {{ message.media_count }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import type { Message, MessageMediaItem, TagItem } from '../types'
import { isVideo, formatDuration, resolveThumb } from '../utils/media'
import { renderMarkdown } from '../utils/markdown'
import { formatRelativeTime } from '../utils/date'

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
  'toggle-select': [id: number]
}>()

const cardRef = ref<HTMLElement | null>(null)
const isVisible = ref(false)
let observer: IntersectionObserver | null = null

onMounted(() => {
  if (cardRef.value) {
    observer = new IntersectionObserver(
      ([entry]) => {
        if (entry?.isIntersecting) {
          isVisible.value = true
          observer?.disconnect()
        }
      },
      { rootMargin: '50px' }
    )
    observer.observe(cardRef.value)
  }
})

onUnmounted(() => {
  observer?.disconnect()
})

const cover = computed<MessageMediaItem | null>(() => props.mediaItems?.[0] ?? null)

const extraMediaCount = computed(() => {
  const n = props.mediaItems?.length ?? 0
  return Math.max(0, n - 1)
})

const messageTags = computed(() => props.tags || [])

const MAX_TAGS = 3
const visibleTags = computed(() => messageTags.value.slice(0, MAX_TAGS))
const hiddenTagCount = computed(() => Math.max(0, messageTags.value.length - MAX_TAGS))

const renderedText = computed(() => {
  if (!props.message.text) return ''
  return renderMarkdown(props.message.text)
})

const formatDate = formatRelativeTime

const handleClick = () => {
  emit('click', props.message.id)
}
</script>
