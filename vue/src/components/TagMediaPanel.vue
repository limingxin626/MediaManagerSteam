<template>
  <div class="flex flex-col w-72 shrink-0 border-l border-[var(--border-color)] min-h-0">
    <!-- Header -->
    <div class="px-4 py-3 border-b border-[var(--border-color)] shrink-0">
      <div class="flex items-center gap-2">
        <svg class="w-4 h-4 text-[var(--color-primary-500)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M7 7h.01M7 3h5a1.99 1.99 0 011.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.99 1.99 0 013 12V7a4 4 0 014-4z" />
        </svg>
        <span class="text-sm font-semibold text-gray-900 dark:text-white truncate">
          {{ tagName || '全部媒体' }}
        </span>
        <span v-if="items.length > 0" class="ml-auto text-xs text-gray-400">{{ items.length }}{{ hasMore ? '+' : '' }}</span>
      </div>
    </div>

    <!-- Body -->
    <div ref="scrollEl" class="flex-1 min-h-0 overflow-y-auto p-2">
      <!-- Empty -->
      <div v-if="!loading && items.length === 0" class="h-full flex items-center justify-center py-20">
        <p class="text-sm text-gray-400">暂无媒体</p>
      </div>

      <!-- Grid -->
      <div v-else class="grid grid-cols-3 gap-1">
        <div v-for="(media, index) in items" :key="`${media.id}-${media.source_message_id}-${index}`"
          class="group relative aspect-square overflow-hidden rounded-md cursor-pointer bg-gray-100 dark:bg-white/5 hover:opacity-90 transition-opacity"
          @click="$emit('preview', { items, index })"
          @contextmenu.prevent="openMenu($event, media)">
          <img :src="resolveThumb(media)" class="w-full h-full object-cover" loading="lazy" />
          <div v-if="media.mime_type && media.mime_type.startsWith('video')"
            class="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div class="w-7 h-7 bg-black/40 rounded-full flex items-center justify-center border border-white/30">
              <svg class="w-3.5 h-3.5 text-white ml-0.5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z" />
              </svg>
            </div>
          </div>
          <div v-if="media.duration_ms"
            class="absolute bottom-0.5 right-0.5 bg-black/70 text-white text-[10px] px-1 py-0.5 rounded">
            {{ formatDuration(media.duration_ms) }}
          </div>
        </div>
      </div>

      <!-- Loading spinner -->
      <div v-if="loading" class="text-center py-4">
        <div class="inline-block animate-spin rounded-full h-5 w-5 border-t-2 border-b-2 border-[var(--color-primary-500)]"></div>
      </div>

      <!-- Bottom sentinel for infinite scroll -->
      <div ref="sentinel" class="h-1"></div>
    </div>

    <!-- Context menu -->
    <div v-if="menu.open"
      class="fixed z-[60] min-w-[9rem] bg-[var(--bg-card)] border border-[var(--border-color)] rounded-lg shadow-xl py-1"
      :style="{ top: `${menu.y}px`, left: `${menu.x}px` }">
      <button
        class="w-full text-left px-3 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-white/10 transition-colors flex items-center gap-2"
        @click="jumpToMessage">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
        </svg>
        跳转到消息
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, onMounted, onUnmounted, nextTick } from 'vue'
import type { MessageMediaItem, CursorResponse } from '../types'
import { api } from '../composables/useApi'
import { resolveThumb, formatDuration } from '../utils/media'

const props = defineProps<{
  tagId: number | null
  tagName?: string
}>()

const emit = defineEmits<{
  (e: 'preview', payload: { items: MessageMediaItem[]; index: number }): void
  (e: 'jump', messageId: number): void
}>()

const items = ref<MessageMediaItem[]>([])
const loading = ref(false)
const hasMore = ref(false)
const nextCursor = ref<string | null>(null)

const scrollEl = ref<HTMLElement | null>(null)
const sentinel = ref<HTMLElement | null>(null)
let observer: IntersectionObserver | null = null

const fetchPage = async (reset = false) => {
  if (loading.value) return
  if (!reset && !hasMore.value) return

  loading.value = true
  const tagAtRequest = props.tagId
  try {
    const data = await api.get<CursorResponse<MessageMediaItem>>('/media/feed', {
      tag_id: props.tagId ?? undefined,  // null = 全部（无标签过滤）
      limit: 40,
      cursor: reset ? undefined : nextCursor.value,
    })
    // tag 在请求期间被切换则丢弃结果
    if (props.tagId !== tagAtRequest) return
    if (reset) {
      items.value = data.items
    } else {
      items.value.push(...data.items)
    }
    nextCursor.value = data.next_cursor
    hasMore.value = data.has_more
  } catch {
    // silent
  } finally {
    if (props.tagId === tagAtRequest) loading.value = false
  }
}

const reload = () => {
  items.value = []
  nextCursor.value = null
  hasMore.value = false
  fetchPage(true)
}

watch(() => props.tagId, () => {
  closeMenu()
  reload()
})

onMounted(() => {
  observer = new IntersectionObserver((entries) => {
    if (entries[0]?.isIntersecting && hasMore.value && !loading.value) {
      fetchPage()
    }
  }, { root: scrollEl.value, rootMargin: '200px' })
  if (sentinel.value) observer.observe(sentinel.value)
  reload()
  document.addEventListener('click', closeMenu)
})

onUnmounted(() => {
  observer?.disconnect()
  observer = null
  document.removeEventListener('click', closeMenu)
})

// --- Context menu (right-click) ---
const menu = reactive<{ open: boolean; x: number; y: number; media: MessageMediaItem | null }>({
  open: false, x: 0, y: 0, media: null,
})

const openMenu = (e: MouseEvent, media: MessageMediaItem) => {
  menu.media = media
  menu.x = e.clientX
  menu.y = e.clientY
  menu.open = true
  nextTick(() => {
    // 防止溢出屏幕右/下边缘
    const pad = 8
    if (menu.x + 160 > window.innerWidth) menu.x = window.innerWidth - 160 - pad
    if (menu.y + 80 > window.innerHeight) menu.y = window.innerHeight - 80 - pad
  })
}

const closeMenu = () => {
  menu.open = false
}

const jumpToMessage = () => {
  const mid = menu.media?.source_message_id
  closeMenu()
  if (mid != null) emit('jump', mid)
}
</script>
