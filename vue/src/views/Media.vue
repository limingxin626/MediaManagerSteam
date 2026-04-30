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
    <div class="flex-1 min-h-0 relative">
    <div ref="scrollContainer" class="absolute inset-0 overflow-y-auto media-scroll" @scroll="vg.onScroll">
      <div ref="measureEl" class="relative max-w-4xl mx-auto px-1 sm:px-2 py-4" :style="{ height: vg.totalHeight.value + 'px' }">

        <!-- Month headers -->
        <div
          v-for="b in vg.buckets.value"
          :key="'h-' + b.key"
          class="absolute left-0 right-0 px-1 sm:px-2 py-2"
          :style="{ top: b.headerOffset + 'px', height: vg.monthHeaderH.value + 'px' }"
        >
          <span class="text-sm font-medium text-gray-500 dark:text-gray-400">{{ b.year }}年{{ b.month }}月</span>
        </div>

        <!-- Cells (placeholder + loaded) -->
        <template v-for="b in vg.buckets.value" :key="'g-' + b.key">
          <div
            v-for="i in b.count"
            :key="b.key + '-' + (i - 1)"
            :style="cellStyle(b, i - 1)"
            class="absolute rounded overflow-hidden bg-gray-200 dark:bg-gray-900"
          >
            <template v-if="vg.loadedItem(b, i - 1) as Media | undefined">
              <div
                class="group w-full h-full relative cursor-pointer transition-transform duration-200 hover:scale-[1.03]"
                @click="openPreview(b.key, i - 1)"
              >
                <img
                  :src="resolveUrl((vg.loadedItem(b, i - 1) as Media).thumb_url)"
                  :alt="String((vg.loadedItem(b, i - 1) as Media).id)"
                  class="w-full h-full object-cover"
                  loading="lazy"
                />
                <div class="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors duration-200 pointer-events-none"></div>
                <div v-if="isVideo((vg.loadedItem(b, i - 1) as Media).mime_type)" class="absolute inset-0 flex items-center justify-center pointer-events-none">
                  <div class="w-8 h-8 bg-black/40 rounded-full flex items-center justify-center border border-white/30">
                    <svg class="w-4 h-4 text-white ml-0.5" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M8 5v14l11-7z"/>
                    </svg>
                  </div>
                </div>
                <div v-if="(vg.loadedItem(b, i - 1) as Media).duration_ms" class="absolute bottom-1 right-1 bg-black/70 text-white text-xs px-1.5 py-0.5 rounded">
                  {{ formatDuration((vg.loadedItem(b, i - 1) as Media).duration_ms!) }}
                </div>
                <button
                  @click.stop="starWithBounce(vg.loadedItem(b, i - 1) as Media)"
                  class="absolute top-1 right-1 p-1 rounded-full transition-all"
                  :class="(vg.loadedItem(b, i - 1) as Media).starred
                    ? 'text-yellow-400'
                    : 'text-white/70 hover:text-yellow-400 opacity-0 group-hover:opacity-100'
                  "
                >
                  <svg class="w-4 h-4" :class="{ 'star-bounce': mediaBounceId === (vg.loadedItem(b, i - 1) as Media).id }" :fill="(vg.loadedItem(b, i - 1) as Media).starred ? 'currentColor' : 'none'" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                  </svg>
                </button>
              </div>
            </template>
          </div>
        </template>

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
        v-if="vg.timeline.value.length"
        :timeline="vg.timeline.value"
        :min-date="timelineMinDate"
        :max-date="timelineMaxDate"
        :current-date="vg.currentDate.value"
        @jump="handleDateScrubberJump"
        @jump-final="handleDateScrubberJumpFinal"
      />
    </div>

      <!-- Back to Latest -->
      <button
        v-if="showBackToLatest"
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
      @media-rotated="handleMediaRotated"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import MediaPreview from '../components/MediaPreview.vue'
import DateScrubber from '../components/DateScrubber.vue'
import FilterSidebar from '../components/FilterSidebar.vue'
import type { Media, TagWithCount, Actor } from '../types'
import { api } from '../composables/useApi'
import { useVirtualGrid, type BucketLayout } from '../composables/useVirtualGrid'
import { isVideo, formatDuration, resolveUrl, toggleMediaStar } from '../utils/media'

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

// --- Layout helpers ---
function cellStyle(b: BucketLayout, idx: number) {
  const p = vg.itemPosition(b, idx)
  return {
    top: p.top + 'px',
    left: p.left + 'px',
    width: p.size + 'px',
    height: p.size + 'px',
  }
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

// --- Back to latest ---
const showBackToLatest = computed(
  () => vg.scrollTop.value > vg.viewportH.value * 2,
)
function backToLatest() {
  scrollContainer.value?.scrollTo({ top: 0, behavior: 'auto' })
}

// --- Preview ---
function openPreview(bucketKey: string, idx: number) {
  const item = vg.cache.value.get(bucketKey)?.items[idx]
  if (!item) return

  // Gather siblings: ±10 from same bucket's loaded items
  const entry = vg.cache.value.get(bucketKey)!
  const totalItems = 20
  const half = Math.floor(totalItems / 2)
  let start = Math.max(0, idx - half)
  let end = Math.min(entry.items.length - 1, idx + half)
  if (end - start < totalItems - 1) {
    if (start === 0) end = Math.min(entry.items.length - 1, totalItems - 1)
    else if (end === entry.items.length - 1) start = Math.max(0, end - (totalItems - 1))
  }

  const slice = entry.items.slice(start, end + 1)
  previewItems.value = slice.map((m: Media) => ({
    id: m.id,
    file_path: m.file_path,
    mime_type: m.mime_type,
    duration_ms: m.duration_ms,
    thumb_url: m.thumb_url,
    starred: m.starred,
  }))
  previewStartIndex.value = idx - start
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

<style scoped>
.media-scroll { scrollbar-width: none; }
.media-scroll::-webkit-scrollbar { display: none; }
</style>
