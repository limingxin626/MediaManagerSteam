<template>
  <div class="h-screen flex transition-colors">
    <FilterSidebar
      :tags="tags"
      :actors="actors"
      :no-actor-count="noActorCount"
      :selected-tag-id="selectedTagId"
      :selected-actor-id="selectedActorId"
      @select-tag="selectTag"
      @select-actor="selectActor"
    />

    <!-- Main Content -->
    <div class="flex-1 flex flex-col min-w-0 relative">
    <!-- Fixed Header -->
    <div class="shrink-0 border-b border-[var(--border-color)] shadow-sm">
      <div class="w-full mx-auto px-4 sm:px-6 lg:px-8 py-3">
        <div class="flex items-center gap-3 max-w-4xl mx-auto">
        <h2 class="text-lg font-bold text-gray-900 dark:text-white shrink-0">媒体</h2>
        <!-- Refresh -->
        <button
          @click="handleRefresh"
          :disabled="refreshing"
          class="p-1.5 rounded-md transition-colors text-gray-400 hover:text-[var(--color-primary-600)] bg-gray-100 dark:bg-white/10 hover:bg-gray-200 dark:hover:bg-white/20 disabled:opacity-50 disabled:cursor-not-allowed"
          title="刷新"
        >
          <svg class="w-4 h-4" :class="{ 'animate-spin': refreshing }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
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
        <!-- Smart search -->
        <div class="relative flex-1 max-w-xs">
          <input
            v-model="searchInput"
            @keydown.enter="commitSearch"
            type="text"
            placeholder="智能搜索：sunset / 猫 / actor..."
            class="w-full px-3 py-1.5 pr-8 rounded-full text-sm bg-gray-100 dark:bg-white/10 text-gray-800 dark:text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-[var(--color-primary-500)]"
          />
          <button
            v-if="searchQuery || similarMode"
            @click="clearSmartMode"
            class="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-700 dark:hover:text-white"
            title="退出智能模式"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
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
    <div class="flex-1 min-h-0 relative">

    <!-- Smart mode grid (search / similar) -->
    <div v-if="smartActive" class="absolute inset-0 overflow-y-auto">
      <div class="w-full px-2 sm:px-4 py-4">
        <div class="flex items-center justify-between mb-3 px-1">
          <div class="text-sm text-[var(--text-muted)]">
            <span v-if="similarMode">相似于 #{{ similarMode.media_id }}</span>
            <span v-else>搜索“{{ searchQuery }}”</span>
            <span class="ml-2">共 {{ smartItems.length }} 项</span>
          </div>
          <button
            v-if="smartLoading"
            class="text-xs text-[var(--text-muted)]"
          >加载中...</button>
        </div>
        <div v-if="!smartLoading && !smartItems.length" class="py-20 text-center text-sm text-[var(--text-muted)]">
          无结果
        </div>
        <div class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 gap-1.5">
          <div
            v-for="(item, idx) in smartItems"
            :key="item.id"
            class="aspect-square rounded overflow-hidden bg-gray-200 dark:bg-gray-900"
          >
            <MediaCell
              :item="item"
              :bouncing="mediaBounceId === item.id"
              @open="openSmartPreview(idx)"
              @star="starWithBounce(item)"
            />
          </div>
        </div>
      </div>
    </div>

    <div v-show="!smartActive" ref="scrollContainer" class="absolute inset-0 overflow-y-auto scrollbar-hidden pr-[32px] md:pr-[44px]" @scroll="vg.onScroll">
      <div ref="measureEl" class="relative w-full px-1 sm:px-2 py-4" :style="{ height: vg.totalHeight.value + 'px' }">

        <!-- Month headers -->
        <div
          v-for="b in vg.visibleBuckets.value"
          :key="'h-' + b.key"
          class="absolute left-0 right-0 px-1 sm:px-2 py-2"
          :style="{ top: b.headerOffset + 'px', height: vg.monthHeaderH.value + 'px' }"
        >
          <span class="text-sm font-medium text-gray-500 dark:text-gray-400">{{ b.year }}年{{ b.month }}月</span>
        </div>

        <!-- Visible cells only (true virtualization) -->
        <div
          v-for="cell in vg.visibleCells.value"
          :key="cell.bucket.key + '-' + cell.idx"
          :style="{ top: cell.top + 'px', left: cell.left + 'px', width: cell.size + 'px', height: cell.size + 'px' }"
          class="absolute rounded overflow-hidden bg-gray-200 dark:bg-gray-900"
        >
          <template v-if="vg.loadedItem(cell.bucket, cell.idx) as Media | undefined">
            <MediaCell
              :item="(vg.loadedItem(cell.bucket, cell.idx) as Media)"
              :bouncing="mediaBounceId === (vg.loadedItem(cell.bucket, cell.idx) as Media).id"
              @open="openPreview(cell.bucket.key, cell.idx)"
              @star="starWithBounce(vg.loadedItem(cell.bucket, cell.idx) as Media)"
            />
          </template>
        </div>

        <!-- Empty -->
        <div v-if="!vg.buckets.value.length && !vg.loadingTimeline.value" class="flex flex-col items-center justify-center py-20">
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
      </div>
    </div>

      <!-- Date Scrubber -->
      <DateScrubber
        v-if="!smartActive && vg.timeline.value.length"
        :timeline="vg.timeline.value"
        :min-date="timelineMinDate"
        :max-date="timelineMaxDate"
        :current-date="vg.currentDate.value"
        @jump="handleDateScrubberJump"
        @jump-final="handleDateScrubberJumpFinal"
        @wheel="(dy) => scrollContainer?.scrollBy({ top: dy })"
      />
    </div>

    </div>

    <!-- Media Preview -->
    <MediaPreview
      :is-open="previewOpen"
      :items="previewItems"
      :start-index="previewStartIndex"
      @close="previewOpen = false"
      @toggle-star="handlePreviewToggleStar"
      @media-deleted="handleMediaDeleted"
      @media-rotated="handleMediaRotated"
      @find-similar="enterSimilarMode"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import MediaPreview from '../components/MediaPreview.vue'
import DateScrubber from '../components/DateScrubber.vue'
import FilterSidebar from '../components/FilterSidebar.vue'
import MediaCell from '../components/MediaCell.vue'
import type { Media, TagWithCount, Actor, CursorResponse } from '../types'
import { api } from '../composables/useApi'
import { useVirtualGrid } from '../composables/useVirtualGrid'
import { toggleMediaStar } from '../utils/media'
import { useToast } from '../composables/useToast'

const toast = useToast()

defineOptions({ name: 'Media' })

const typeOptions = [
  { value: '', label: '全部' },
  { value: 'video', label: '视频' },
  { value: 'image', label: '图片' },
]

const selectedType = ref('')
const starredFilter = ref(false)
const selectedTagId = ref<number | null>(null)
const selectedActorId = ref<number | null>(null)

const scrollContainer = ref<HTMLElement | null>(null)
const measureEl = ref<HTMLElement | null>(null)

const filters = computed(() => ({
  starred: starredFilter.value || undefined,
  type: selectedType.value || undefined,
  tag_id: selectedTagId.value ?? undefined,
  actor_id: selectedActorId.value ?? undefined,
}))

const vg = useVirtualGrid({
  container: scrollContainer,
  measureEl,
  filters,
})

const previewOpen = ref(false)
const previewItems = ref<any[]>([])
const previewStartIndex = ref(0)
const mediaBounceId = ref<number | null>(null)
const refreshing = ref(false)

async function handleRefresh() {
  refreshing.value = true
  try {
    vg.resetAll()
  } finally {
    refreshing.value = false
  }
}

// --- Smart mode (search / similar) ---
const searchInput = ref('')
const searchQuery = ref('')
const similarMode = ref<{ media_id: number } | null>(null)
const smartItems = ref<Media[]>([])
const smartLoading = ref(false)

const smartActive = computed(() => !!searchQuery.value || !!similarMode.value)

async function commitSearch() {
  const q = searchInput.value.trim()
  if (!q) {
    clearSmartMode()
    return
  }
  similarMode.value = null
  searchQuery.value = q
  await fetchSearch(q)
}

async function fetchSearch(q: string) {
  smartLoading.value = true
  smartItems.value = []
  try {
    const res = await api.get<CursorResponse<Media>>(
      `/smart/search?q=${encodeURIComponent(q)}&limit=50`,
    )
    smartItems.value = res.items
  } catch (e: any) {
    toast.error(e?.message || '搜索失败')
  } finally {
    smartLoading.value = false
  }
}

async function enterSimilarMode(mediaId: number) {
  searchQuery.value = ''
  searchInput.value = ''
  similarMode.value = { media_id: mediaId }
  smartLoading.value = true
  smartItems.value = []
  try {
    const res = await api.get<CursorResponse<Media>>(`/smart/similar/${mediaId}?limit=50`)
    smartItems.value = res.items
  } catch (e: any) {
    toast.error(e?.message || '加载相似媒体失败')
    similarMode.value = null
  } finally {
    smartLoading.value = false
  }
}

function clearSmartMode() {
  searchQuery.value = ''
  searchInput.value = ''
  similarMode.value = null
  smartItems.value = []
}

function openSmartPreview(idx: number) {
  const slice = smartItems.value.slice(0, smartItems.value.length)
  previewItems.value = slice.map((m) => ({
    id: m.id,
    file_path: m.file_path,
    mime_type: m.mime_type,
    duration_ms: m.duration_ms,
    thumb_url: m.thumb_url,
    thumb_path: m.thumb_path,
    starred: m.starred,
    tags: m.tags,
  }))
  previewStartIndex.value = idx
  previewOpen.value = true
}

function starWithBounce(item: Media) {
  mediaBounceId.value = item.id
  setTimeout(() => (mediaBounceId.value = null), 300)
  toggleMediaStar(item)
}

// --- Tag & Actor sidebar data ---
const tags = ref<TagWithCount[]>([])
const actors = ref<Actor[]>([])
const noActorCount = ref(0)

async function fetchTags() {
  try {
    tags.value = await api.get<TagWithCount[]>('/tags?has_media=true')
  } catch {}
}

async function fetchActors() {
  try {
    const data = await api.get<{ items: Actor[]; no_actor_count: number }>('/actors')
    actors.value = data.items
    noActorCount.value = data.no_actor_count
  } catch {}
}

function selectTag(tagId: number | null) {
  selectedTagId.value = tagId
  selectedActorId.value = null
}

function selectActor(actorId: number | null) {
  selectedActorId.value = actorId
  selectedTagId.value = null
}

function setType(type: string) {
  selectedType.value = type
}

function toggleStarredFilter() {
  starredFilter.value = !starredFilter.value
}

// --- DateScrubber ---
const timelineMinDate = computed(() => {
  const tl = vg.timeline.value
  if (!tl.length) return new Date()
  const last = tl[tl.length - 1]
  return new Date(last.year, last.month - 1, 1)
})

const timelineMaxDate = computed(() => {
  const tl = vg.timeline.value
  if (!tl.length) return new Date()
  const first = tl[0]
  return new Date(first.year, first.month, 0, 23, 59, 59)
})

function handleDateScrubberJump(date: Date) {
  vg.setDispatchPaused(true)
  vg.scrollToDate(date)
}

function handleDateScrubberJumpFinal(date: Date) {
  vg.scrollToDate(date)
  vg.setDispatchPaused(false)
  const target = vg.findBucketByDate(date)
  if (target) vg.loadBucketNow(`${target.year}-${String(target.month).padStart(2, '0')}`)
}

// --- Preview ---
function openPreview(bucketKey: string, idx: number) {
  const entry = vg.cache.value.get(bucketKey)
  if (!entry || !entry.items[idx]) return

  previewItems.value = entry.items.map((m: Media) => ({
    id: m.id,
    file_path: m.file_path,
    mime_type: m.mime_type,
    duration_ms: m.duration_ms,
    thumb_url: m.thumb_url,
    thumb_path: m.thumb_path,
    starred: m.starred,
    tags: m.tags,
  }))
  previewStartIndex.value = idx
  previewOpen.value = true
}

async function handlePreviewToggleStar(mediaId: number) {
  const found = vg.findItemBucketAndIndex(mediaId)
  if (!found) return
  const item = vg.cache.value.get(found.key)!.items[found.idx]
  await toggleMediaStar(item)
}

function handleMediaDeleted(mediaId: number) {
  vg.removeItem(mediaId)
}

function handleMediaRotated(mediaId: number) {
  const t = Date.now()
  vg.updateItem(mediaId, (m) => {
    m.thumb_url = m.thumb_url.split('?')[0] + `?t=${t}`
  })
  const pItem = previewItems.value.find((m) => m.id === mediaId)
  if (pItem) {
    pItem.thumb_url = pItem.thumb_url.split('?')[0] + `?t=${t}`
    pItem.file_path = pItem.file_path.split('?')[0] + `?t=${t}`
  }
}

onMounted(() => {
  fetchTags()
  fetchActors()
})
</script>
