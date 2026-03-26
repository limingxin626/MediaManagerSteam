<template>
  <div class="min-h-screen transition-colors">
    <!-- Fixed Header -->
    <div class="fixed top-0 left-0 md:left-64 right-0 z-50 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 shadow-sm">
      <div class="w-full px-4 sm:px-6 lg:px-8 py-3 flex items-center gap-3">
        <h2 class="text-xl font-bold text-gray-900 dark:text-white shrink-0">媒体</h2>
        <!-- Type Filter -->
        <div class="flex gap-2">
          <button
            v-for="opt in typeOptions"
            :key="opt.value"
            @click="setType(opt.value)"
            :class="[
              'px-3 py-1.5 rounded-full text-sm transition-colors',
              selectedType === opt.value
                ? 'bg-pink-600 text-white'
                : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
            ]"
          >{{ opt.label }}</button>
        </div>
        <!-- Starred Filter -->
        <button
          @click="toggleStarredFilter"
          class="p-1.5 rounded-lg transition-colors"
          :class="starredFilter
            ? 'text-yellow-400 bg-yellow-50 dark:bg-yellow-900/20'
            : 'text-gray-400 hover:text-yellow-400 bg-gray-100 dark:bg-gray-800'"
          title="仅看收藏"
        >
          <svg class="w-5 h-5" :fill="starredFilter ? 'currentColor' : 'none'" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Grid -->
    <div class="pt-16 px-1 sm:px-2">
      <div class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 xl:grid-cols-8 gap-1">
        <div
          v-for="item in items"
          :key="item.id"
          class="group aspect-square overflow-hidden relative rounded cursor-pointer hover:opacity-90 transition-opacity bg-gray-900"
          @click="openPreview(item)"
        >
          <img
            :src="resolveUrl(item.thumb_url)"
            :alt="String(item.id)"
            class="w-full h-full object-cover"
            loading="lazy"
          />
          <!-- Video icon -->
          <div v-if="isVideo(item.mime_type)" class="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div class="w-8 h-8 bg-black/40 rounded-full flex items-center justify-center border border-white/30">
              <svg class="w-4 h-4 text-white ml-0.5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z"/>
              </svg>
            </div>
          </div>
          <!-- Duration -->
          <div v-if="item.duration" class="absolute bottom-1 right-1 bg-black/70 text-white text-xs px-1.5 py-0.5 rounded">
            {{ formatDuration(item.duration) }}
          </div>
          <!-- Star toggle -->
          <button
            @click.stop="toggleStar(item, $event)"
            class="absolute top-1 right-1 p-1 rounded-full transition-all"
            :class="item.starred
              ? 'text-yellow-400'
              : 'text-white/70 hover:text-yellow-400 opacity-0 group-hover:opacity-100'"
          >
            <svg class="w-4 h-4" :fill="item.starred ? 'currentColor' : 'none'" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="flex justify-center py-8">
        <div class="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-pink-500"></div>
      </div>

      <!-- End -->
      <div v-if="!loading && !hasMore && items.length > 0" class="text-center py-8 text-sm text-gray-500 dark:text-gray-400">
        已经到底了
      </div>

      <!-- Empty -->
      <div v-if="!loading && items.length === 0" class="flex flex-col items-center justify-center py-24 text-gray-500 dark:text-gray-400">
        <svg class="w-12 h-12 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
        </svg>
        <p class="text-sm">暂无媒体</p>
      </div>

      <!-- Scroll sentinel -->
      <div ref="sentinel" class="h-1"></div>
    </div>

    <!-- Media Preview -->
    <MediaPreview
      :is-open="previewOpen"
      :items="previewItems"
      :start-index="previewStartIndex"
      :starred-ids="mediaStarredIds"
      @close="previewOpen = false"
      @toggle-star="handlePreviewToggleStar"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import MediaPreview from '../components/MediaPreview.vue'
import type { Media, CursorResponse } from '../types'
import { api, useInfiniteScroll } from '../composables/useApi'
import { isVideo, formatDuration, resolveUrl } from '../utils/media'
import { useToast } from '../composables/useToast'

defineOptions({ name: 'Media' })

const toast = useToast()

const typeOptions = [
  { value: '', label: '全部' },
  { value: 'video', label: '视频' },
  { value: 'image', label: '图片' },
]

const selectedType = ref('')
const starredFilter = ref(false)
const sentinel = ref<HTMLElement | null>(null)

const previewOpen = ref(false)
const previewItems = ref<any[]>([])
const previewStartIndex = ref(0)

const { items, loading, hasMore, reset, setupObserver } = useInfiniteScroll<Media>({
  fetchFn: ({ cursor, limit }) => api.get<CursorResponse<Media>>('/media', {
    cursor,
    limit,
    starred: starredFilter.value || undefined,
  }),
  sentinel,
  limit: 40,
})

const setType = (type: string) => {
  selectedType.value = type
  // type filter not yet supported by backend cursor API — reset and load
  reset()
}

const toggleStarredFilter = () => {
  starredFilter.value = !starredFilter.value
  reset()
}

const toggleStar = async (item: Media, event: Event) => {
  event.stopPropagation()
  try {
    await api.put(`/media/${item.id}/starred?starred=${!item.starred}`)
    item.starred = !item.starred
  } catch {
    toast.error('操作失败')
  }
}

const openPreview = (item: Media) => {
  const idx = items.value.findIndex(m => m.id === item.id)
  previewItems.value = items.value.map((m: Media) => ({
    id: m.id,
    file_path: m.file_path,
    mime_type: m.mime_type,
    duration: m.duration
  }))
  previewStartIndex.value = idx >= 0 ? idx : 0
  previewOpen.value = true
}

const mediaStarredIds = computed(() => {
  const s = new Set<number>()
  for (const m of items.value) {
    if (m.starred) s.add(m.id)
  }
  return s
})

const handlePreviewToggleStar = async (mediaId: number) => {
  const item = items.value.find(m => m.id === mediaId)
  if (item) {
    await toggleStar(item, new Event('click'))
  }
}

onMounted(() => {
  reset()
  setupObserver()
})
</script>
