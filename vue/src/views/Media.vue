<template>
  <div class="h-screen flex flex-col transition-colors">
    <!-- Fixed Header -->
    <div class="shrink-0 border-b border-[var(--border-color)] shadow-sm">
      <div class="w-full mx-auto px-4 sm:px-6 lg:px-8 py-3">
        <div class="flex items-center gap-3 max-w-4xl mx-auto">
        <h2 class="text-lg font-bold text-gray-900 dark:text-white shrink-0">媒体</h2>
        <!-- Type Filter -->
        <div class="flex gap-2">
          <button
            v-for="opt in typeOptions"
            :key="opt.value"
            @click="setType(opt.value)"
            :class="[
              'px-3 py-1.5 rounded-full text-sm transition-colors',
              selectedType === opt.value
                ? 'bg-[var(--color-primary-600)] text-white'
                : 'bg-gray-100 dark:bg-white/10 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-white/20'
            ]"
          >{{ opt.label }}</button>
        </div>
        <!-- Starred Filter -->
        <button
          @click="toggleStarredFilter"
          class="p-1.5 rounded-lg transition-colors"
          :class="starredFilter
            ? 'text-yellow-400 bg-yellow-900/20'
            : 'text-gray-400 hover:text-yellow-400 bg-gray-100 dark:bg-white/10'
          "
          title="仅看收藏"
        >
          <svg class="w-5 h-5" :fill="starredFilter ? 'currentColor' : 'none'" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
          </svg>
        </button>
        </div>
      </div>
    </div>

    <!-- Scrollable Content Area -->
    <div ref="scrollContainer" class="flex-1 overflow-y-auto min-h-0 relative" @scroll="onScroll">
      <div class="py-4 px-1 sm:px-2 max-w-4xl mx-auto">
        <!-- Top sentinel for loading newer content -->
        <div ref="topSentinel" class="h-1"></div>

        <!-- Loading before (newer) -->
        <div v-if="loadingBefore" class="flex justify-center py-4">
          <div class="animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-[var(--color-primary-500)]"></div>
        </div>

        <div class="grid grid-cols-3 sm:grid-cols-4 gap-1">
          <template v-for="(item, idx) in items" :key="item.id">
            <!-- Month separator -->
            <div v-if="shouldShowSeparator(idx)" class="col-span-3 sm:col-span-4 py-2" :class="idx > 0 ? 'mt-2' : ''">
              <span class="text-sm font-medium text-gray-500 dark:text-gray-400">{{ getMonthLabel(item) }}</span>
            </div>
            <!-- Media item -->
            <div
              class="group aspect-square overflow-hidden relative rounded cursor-pointer transition-transform duration-200 hover:scale-[1.03] bg-gray-200 dark:bg-gray-900"
              :data-created="item.created_at"
              @click="openPreview(item)"
            >
              <img
                :src="resolveUrl(item.thumb_url)"
                :alt="String(item.id)"
                class="w-full h-full object-cover"
                loading="lazy"
              />
              <div class="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors duration-200 pointer-events-none"></div>
              <!-- Video icon -->
              <div v-if="isVideo(item.mime_type)" class="absolute inset-0 flex items-center justify-center pointer-events-none">
                <div class="w-8 h-8 bg-black/40 rounded-full flex items-center justify-center border border-white/30">
                  <svg class="w-4 h-4 text-white ml-0.5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M8 5v14l11-7z"/>
                  </svg>
                </div>
              </div>
              <!-- Duration -->
              <div v-if="item.duration_ms" class="absolute bottom-1 right-1 bg-black/70 text-white text-xs px-1.5 py-0.5 rounded">
                {{ formatDuration(item.duration_ms) }}
              </div>
              <!-- Star toggle -->
              <button
                @click.stop="starWithBounce(item)"
                class="absolute top-1 right-1 p-1 rounded-full transition-all"
                :class="item.starred
                  ? 'text-yellow-400'
                  : 'text-white/70 hover:text-yellow-400 opacity-0 group-hover:opacity-100'
                "
              >
                <svg class="w-4 h-4" :class="{ 'star-bounce': mediaBounceId === item.id }" :fill="item.starred ? 'currentColor' : 'none'" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                </svg>
              </button>
            </div>
          </template>
        </div>

        <!-- Loading -->
        <div v-if="loading" class="flex justify-center py-8">
          <div class="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-[var(--color-primary-500)]"></div>
        </div>

        <!-- End -->
        <div v-if="!loading && !hasMore && items.length > 0" class="text-center py-8 text-sm text-gray-400">
          已经到底了
        </div>

        <!-- Empty -->
        <div v-if="!loading && items.length === 0" class="flex flex-col items-center justify-center py-20">
          <div class="relative w-24 h-24 mb-4">
            <div class="absolute inset-0 rounded-2xl bg-[var(--color-primary-500)]/10 rotate-6"></div>
            <div class="absolute inset-0 rounded-2xl bg-[var(--color-primary-500)]/5 -rotate-3"></div>
            <div class="absolute inset-0 flex items-center justify-center">
              <svg class="w-10 h-10 text-[var(--color-primary-500)]/40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
            </div>
          </div>
          <h3 class="text-sm font-medium text-[var(--text-primary)]">暂无媒体</h3>
          <p class="mt-1 text-sm text-[var(--text-muted)]">还没有任何媒体内容</p>
        </div>

        <!-- Scroll sentinel (bottom, for loading older) -->
        <div ref="sentinel" class="h-1"></div>
      </div>

      <!-- Timeline Bar -->
      <TimelineBar
        v-if="timeline.length"
        :timeline="timeline"
        :current-year="currentYear"
        :current-month="currentMonth"
        :compact="isCompact"
        @jump="handleTimelineJump"
      />

      <!-- Back to Latest -->
      <button
        v-if="isJumped"
        @click="backToLatest"
        class="fixed bottom-20 right-4 z-30 flex items-center gap-1.5 px-3 py-2 rounded-full bg-[var(--color-primary-600)] text-white text-sm shadow-lg hover:bg-[var(--color-primary-700)] transition-colors"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7"/>
        </svg>
        回到最新
      </button>
    </div>

    <!-- Media Preview -->
    <MediaPreview
      :is-open="previewOpen"
      :items="previewItems"
      :start-index="previewStartIndex"
      @close="previewOpen = false"
      @toggle-star="handlePreviewToggleStar"
      @media-deleted="handleMediaDeleted"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted, onUnmounted, watch } from 'vue'
import MediaPreview from '../components/MediaPreview.vue'
import TimelineBar from '../components/TimelineBar.vue'
import type { TimelineEntry } from '../components/TimelineBar.vue'
import type { Media, CursorResponse } from '../types'
import { api, useInfiniteScroll } from '../composables/useApi'
import { isVideo, formatDuration, resolveUrl, toggleMediaStar } from '../utils/media'

defineOptions({ name: 'Media' })

const typeOptions = [
  { value: '', label: '全部' },
  { value: 'video', label: '视频' },
  { value: 'image', label: '图片' },
]

const selectedType = ref('')
const starredFilter = ref(false)
const sentinel = ref<HTMLElement | null>(null)
const topSentinel = ref<HTMLElement | null>(null)
const scrollContainer = ref<HTMLElement | null>(null)
const isCompact = ref(window.innerWidth < 768)

const previewOpen = ref(false)
const previewItems = ref<any[]>([])
const previewStartIndex = ref(0)
const mediaBounceId = ref<number | null>(null)
function starWithBounce(item: Media) {
  mediaBounceId.value = item.id
  setTimeout(() => mediaBounceId.value = null, 300)
  toggleMediaStar(item)
}

// --- Downward (older) infinite scroll via composable ---
const { items, loading, hasMore, reset, jumpToCursor, setupObserver } = useInfiniteScroll<Media>({
  fetchFn: ({ cursor, limit }) => api.get<CursorResponse<Media>>('/media', {
    cursor,
    limit,
    starred: starredFilter.value || undefined,
    type: selectedType.value || undefined,
  }),
  sentinel,
  limit: 40,
})

// --- Upward (newer) loading state ---
const prevCursor = ref<string | null>(null)
const hasMoreBefore = ref(false)
const loadingBefore = ref(false)
const isJumped = ref(false)
let topObserver: IntersectionObserver | null = null

function mediaParams() {
  return {
    starred: starredFilter.value || undefined,
    type: selectedType.value || undefined,
  }
}

async function loadBefore() {
  if (loadingBefore.value || !hasMoreBefore.value || !prevCursor.value) return

  loadingBefore.value = true
  try {
    const data = await api.get<CursorResponse<Media>>('/media', {
      cursor: prevCursor.value,
      direction: 'forward',
      limit: 40,
      ...mediaParams(),
    })

    const container = scrollContainer.value
    const prevScrollTop = container?.scrollTop ?? 0
    const prevHeight = container?.scrollHeight ?? 0

    // forward returns ASC order (oldest first), reverse to DESC (newest first) then prepend
    const newItems = data.items.reverse()
    items.value = [...newItems, ...items.value]

    hasMoreBefore.value = data.has_more
    if (data.has_more && newItems.length) {
      // newItems[0] is the newest after reverse — use it as next forward cursor
      prevCursor.value = `${newItems[0].created_at}|${newItems[0].id}`
    } else {
      prevCursor.value = null
      hasMoreBefore.value = false
      isJumped.value = false
    }

    await nextTick()
    if (container) {
      const scrollDelta = container.scrollHeight - prevHeight
      container.scrollTo({ top: prevScrollTop + scrollDelta, behavior: 'auto' })
    }
  } finally {
    loadingBefore.value = false
  }
}

function setupTopObserver() {
  teardownTopObserver()
  const root = scrollContainer.value
  topObserver = new IntersectionObserver(
    (entries) => {
      if (entries[0]?.isIntersecting && !loadingBefore.value && hasMoreBefore.value && root && root.scrollTop > 0) {
        loadBefore()
      }
    },
    { root, rootMargin: '200px' },
  )
  if (topSentinel.value) topObserver.observe(topSentinel.value)
}

function teardownTopObserver() {
  topObserver?.disconnect()
  topObserver = null
}

function resetBidirectionalState() {
  prevCursor.value = null
  hasMoreBefore.value = false
  loadingBefore.value = false
  isJumped.value = false
}

// --- Timeline ---
const timeline = ref<TimelineEntry[]>([])
const currentYear = ref(new Date().getFullYear())
const currentMonth = ref(new Date().getMonth() + 1)

async function loadTimeline() {
  timeline.value = await api.get<TimelineEntry[]>('/media/timeline', {
    ...mediaParams(),
  })
  if (timeline.value.length) {
    currentYear.value = timeline.value[0].year
    currentMonth.value = timeline.value[0].month
  }
}

async function handleTimelineJump(entry: TimelineEntry) {
  const nextMonth = entry.month === 12
    ? `${entry.year + 1}-01-01T00:00:00`
    : `${entry.year}-${String(entry.month + 1).padStart(2, '0')}-01T00:00:00`
  const cursor = `${nextMonth}|999999999`

  // Use composable's jumpToCursor — it clears items, sets cursor, loads DESC
  await jumpToCursor(cursor)

  // After load, set up upward (newer) cursor from the first item
  if (items.value.length) {
    const first = items.value[0]
    prevCursor.value = `${first.created_at}|${first.id}`
    hasMoreBefore.value = true
    isJumped.value = true
  }

  currentYear.value = entry.year
  currentMonth.value = entry.month
}

// --- Month separators ---
function getYearMonth(item: Media): string {
  if (!item.created_at) return ''
  return item.created_at.substring(0, 7)
}

function shouldShowSeparator(idx: number): boolean {
  if (idx === 0) return true
  return getYearMonth(items.value[idx]) !== getYearMonth(items.value[idx - 1])
}

function getMonthLabel(item: Media): string {
  if (!item.created_at) return ''
  const d = new Date(item.created_at)
  return `${d.getFullYear()}年${d.getMonth() + 1}月`
}

// --- Scroll sync ---
function onScroll() {
  const container = scrollContainer.value
  if (!container) return
  const gridItems = container.querySelectorAll<HTMLElement>('[data-created]')
  for (const el of gridItems) {
    const rect = el.getBoundingClientRect()
    if (rect.top >= 0) {
      const created = el.dataset.created
      if (created) {
        const d = new Date(created)
        currentYear.value = d.getFullYear()
        currentMonth.value = d.getMonth() + 1
      }
      break
    }
  }
}

// --- Filters ---
const setType = (type: string) => {
  selectedType.value = type
  resetBidirectionalState()
  reset()
}

const toggleStarredFilter = () => {
  starredFilter.value = !starredFilter.value
  resetBidirectionalState()
  reset()
}

const backToLatest = () => {
  resetBidirectionalState()
  reset()
  scrollContainer.value?.scrollTo({ top: 0, behavior: 'auto' })
}

watch([selectedType, starredFilter], () => {
  loadTimeline()
})

const handlePreviewToggleStar = async (mediaId: number) => {
  const item = items.value.find(m => m.id === mediaId)
  if (item) await toggleMediaStar(item)
}

const handleMediaDeleted = (mediaId: number) => {
  const idx = items.value.findIndex(m => m.id === mediaId)
  if (idx !== -1) items.value.splice(idx, 1)
}

const openPreview = (item: Media) => {
  const idx = items.value.findIndex(m => m.id === item.id)
  if (idx === -1) return

  const totalItems = 20
  const half = Math.floor(totalItems / 2)

  let start = idx - half
  let end = idx + half

  if (start < 0) {
    end += Math.abs(start)
    start = 0
  }
  if (end >= items.value.length) {
    start -= (end - items.value.length + 1)
    end = items.value.length - 1
  }

  start = Math.max(0, start)

  const selectedItems = items.value.slice(start, end + 1)
  previewItems.value = selectedItems.map((m: Media) => ({
    id: m.id,
    file_path: m.file_path,
    mime_type: m.mime_type,
    duration_ms: m.duration_ms,
    thumb_url: m.thumb_url,
    starred: m.starred
  }))

  previewStartIndex.value = idx - start
  previewOpen.value = true
}

onMounted(() => {
  reset()
  setupObserver()
  setupTopObserver()
  loadTimeline()
})

onUnmounted(() => {
  teardownTopObserver()
})
</script>
