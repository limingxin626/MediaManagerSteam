<template>
  <div class="flex h-full min-h-0 bg-[var(--bg-primary)] text-[var(--text-primary)]">
    <button v-if="mobileTagsOpen" class="fixed inset-0 z-30 bg-black/25 md:hidden" aria-label="关闭标签筛选" @click="mobileTagsOpen = false"></button>
    <aside class="fixed inset-y-0 left-0 z-40 w-48 shrink-0 flex-col border-r border-[var(--border-color)] bg-[var(--sidebar-bg)] md:static md:z-auto md:flex" :class="mobileTagsOpen ? 'flex' : 'hidden'">
      <div class="flex h-10 shrink-0 items-center justify-between border-b border-[var(--border-color)] px-4">
        <span class="text-xs font-semibold text-[var(--color-primary-600)] dark:text-[var(--color-primary-500)]">标签</span>
        <button class="text-[var(--text-muted)] md:hidden" title="关闭" @click="mobileTagsOpen = false">
          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 6l12 12M18 6 6 18" /></svg>
        </button>
      </div>
      <div class="min-h-0 flex-1 overflow-y-auto px-2 py-3">
        <button
          class="mb-0.5 flex w-full items-center justify-between rounded-lg px-3 py-2 text-left text-sm transition-colors"
          :class="selectedTagId === null ? activeFilterClass : inactiveFilterClass"
          @click="selectTag(null)"
        >
          <span>全部</span>
        </button>
        <button
          v-for="tag in tags"
          :key="tag.id"
          class="mb-0.5 flex w-full items-center justify-between rounded-lg px-3 py-2 text-left text-sm transition-colors"
          :class="selectedTagId === tag.id ? activeFilterClass : inactiveFilterClass"
          @click="selectTag(tag.id)"
        >
          <span class="truncate">{{ tag.name }}</span>
          <span class="ml-2 shrink-0 text-xs tabular-nums text-[var(--text-muted)]">{{ tag.folder_count }}</span>
        </button>
      </div>
    </aside>

    <main class="flex min-w-0 flex-1">
      <div class="relative flex min-w-0 flex-1 flex-col">
      <header class="shrink-0 border-b border-[var(--border-color)] bg-[var(--bg-card)]">
        <div class="mx-auto flex w-full max-w-6xl items-center justify-between gap-3 px-4 py-3 pr-10 sm:px-6 lg:px-8">
          <button class="grid h-8 w-8 shrink-0 place-items-center rounded-[var(--radius-sm)] text-[var(--text-muted)] hover:bg-[var(--bg-secondary)] md:hidden" title="标签筛选" @click="mobileTagsOpen = true">
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 6h16M7 12h10M10 18h4" /></svg>
          </button>
          <div class="flex shrink-0 items-center gap-2">
            <select
              v-if="viewMode === 'grid'"
              v-model="gridMode"
              class="h-8 rounded-[var(--radius-sm)] border border-[var(--border-color)] bg-[var(--bg-secondary)] px-2 text-xs text-[var(--text-secondary)] sm:hidden"
              aria-label="Grid 模式"
              @change="persistGridMode"
            >
              <option value="mosaic">拼图</option>
              <option value="fanart">Fanart</option>
              <option value="poster">Poster</option>
            </select>
            <div v-if="viewMode === 'grid'" class="hidden rounded-[var(--radius-sm)] bg-[var(--bg-secondary)] p-0.5 sm:flex" aria-label="Grid 模式">
              <button
                v-for="option in gridModeOptions"
                :key="option.value"
                class="h-7 rounded-[5px] px-2 text-xs transition-colors"
                :class="gridMode === option.value ? viewActiveClass : viewInactiveClass"
                @click="setGridMode(option.value)"
              >
                {{ option.label }}
              </button>
            </div>
            <button
              class="grid h-8 w-8 place-items-center rounded-[var(--radius-sm)] text-[var(--text-muted)] transition-colors hover:bg-[var(--bg-secondary)] hover:text-[var(--color-primary-600)] disabled:opacity-50"
              :disabled="loading"
              title="刷新"
              @click="refresh"
            >
              <svg class="h-4 w-4" :class="{ 'animate-spin': loading }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M20 7v5h-5M4 17v-5h5M6.1 8.2A7 7 0 0 1 18.5 7M17.9 15.8A7 7 0 0 1 5.5 17" /></svg>
            </button>
            <div class="flex rounded-[var(--radius-sm)] bg-[var(--bg-secondary)] p-0.5" aria-label="目录视图">
              <button
                class="grid h-7 w-8 place-items-center rounded-[5px] transition-colors"
                :class="viewMode === 'grid' ? viewActiveClass : viewInactiveClass"
                title="Grid"
                @click="setViewMode('grid')"
              >
                <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h6v6h-6z" /></svg>
              </button>
              <button
                class="grid h-7 w-8 place-items-center rounded-[5px] transition-colors"
                :class="viewMode === 'feed' ? viewActiveClass : viewInactiveClass"
                title="Feed"
                @click="setViewMode('feed')"
              >
                <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M5 6h14M5 12h14M5 18h14" /></svg>
              </button>
            </div>
          </div>
        </div>
      </header>

      <div ref="scrollContainer" class="relative min-h-0 flex-1 overflow-y-auto">
        <div class="mx-auto w-full px-4 py-4 pb-6 sm:px-6 lg:px-8">
          <div v-if="loading && !folders.length" class="mx-auto grid max-w-7xl grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
            <div v-for="index in 8" :key="index" class="animate-pulse overflow-hidden rounded-lg border border-[var(--border-color)] bg-[var(--bg-card)]">
              <div class="bg-[var(--bg-secondary)]" :class="gridPreviewSizeClass"></div>
              <div class="h-10 px-3 py-2.5">
                <div class="h-4 w-2/3 rounded bg-[var(--bg-secondary)]"></div>
              </div>
            </div>
          </div>
          <div v-else-if="error && !folders.length" class="py-20 text-center">
            <p class="text-sm text-red-500">{{ error }}</p>
            <button class="mt-3 text-sm text-[var(--color-primary-600)]" @click="refresh">重试</button>
          </div>
          <div v-else-if="!folders.length" class="flex flex-col items-center py-20 text-center">
            <span class="grid h-14 w-14 place-items-center rounded-lg bg-[var(--bg-secondary)] text-[var(--text-muted)]">
              <svg class="h-7 w-7" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M3.5 6.5h6l2 2h9v10h-17z" /></svg>
            </span>
            <h2 class="mt-4 text-sm font-medium">暂无目录</h2>
          </div>

          <div v-if="viewMode === 'grid' && folders.length" class="mx-auto grid max-w-7xl grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
            <article
              v-for="folder in folders"
              :key="folder.id"
              :data-folder-id="folder.id"
              class="group flex min-w-0 cursor-pointer flex-col overflow-hidden rounded-lg border border-[var(--border-color)] bg-[var(--bg-card)] shadow-[var(--shadow-sm)] transition-shadow hover:shadow-[var(--shadow-md)]"
              @click="openFolder(folder.id)"
            >
              <div
                class="grid shrink-0 gap-0.5 overflow-hidden bg-[var(--bg-secondary)]"
                :class="[gridPreviewSizeClass, previewGridClass(folderGridFiles(folder).length)]"
              >
                <div
                  v-for="file in folderGridFiles(folder)"
                  :key="file.id"
                  class="group/media relative min-h-0 min-w-0 overflow-hidden"
                >
                  <img v-if="resolveThumb(file)" :src="resolveThumb(file)" :alt="file.name" class="h-full w-full object-cover transition-transform duration-200 group-hover/media:scale-[1.03]" loading="lazy" />
                  <MediaPlaceholder v-else />
                  <VideoBadge v-if="file.media_type === 'VIDEO'" />
                </div>
                <div v-if="!folderGridFiles(folder).length" class="col-span-2 grid h-full place-items-center text-amber-600/70 dark:text-amber-400/70">
                  <svg class="h-12 w-12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.3"><path d="M3.5 6.5h6l2 2h9v10h-17z" /></svg>
                </div>
              </div>
              <div class="h-10 shrink-0 px-3 py-2.5">
                <h2 class="truncate text-sm font-semibold leading-5">{{ folder.name }}</h2>
              </div>
            </article>
          </div>

          <div v-else-if="folders.length" class="mx-auto flex max-w-6xl flex-col gap-4">
            <article
              v-for="folder in folders"
              :key="folder.id"
              :data-folder-id="folder.id"
              class="overflow-hidden rounded-lg border border-[var(--border-color)] bg-[var(--bg-card)] shadow-[var(--shadow-sm)]"
            >
              <button class="flex w-full items-center gap-3 px-4 py-3 text-left hover:bg-[var(--bg-secondary)]" @click="openFolder(folder.id)">
                <span class="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-amber-500/12 text-amber-600 dark:text-amber-400">
                  <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M3.5 6.5h6l2 2h9v10h-17z" /></svg>
                </span>
                <span class="min-w-0 flex-1">
                  <span class="block truncate text-sm font-semibold">{{ folder.name }}</span>
                  <span class="mt-0.5 block truncate text-xs text-[var(--text-muted)]">{{ folderPath(folder) }}</span>
                </span>
                <span class="shrink-0 text-xs text-[var(--text-muted)]">{{ folder.media_count }} 个媒体</span>
                <svg class="h-4 w-4 shrink-0 text-[var(--text-muted)]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="m9 5 7 7-7 7" /></svg>
              </button>
              <div v-if="folderPreviews(folder).length" class="grid grid-cols-4 gap-0.5 border-t border-[var(--border-color)] bg-[var(--bg-secondary)] sm:grid-cols-6">
                <button
                  v-for="(file, index) in folderPreviews(folder)"
                  :key="file.id"
                  class="group/media relative aspect-square overflow-hidden"
                  @click="openPreview(folderPreviews(folder), index)"
                >
                  <img v-if="resolveThumb(file)" :src="resolveThumb(file)" :alt="file.name" class="h-full w-full object-cover transition-transform duration-200 group-hover/media:scale-[1.03]" loading="lazy" />
                  <MediaPlaceholder v-else />
                  <VideoBadge v-if="file.media_type === 'VIDEO'" />
                </button>
              </div>
              <div v-if="folderTags(folder).length" class="flex gap-1 overflow-hidden px-4 py-2">
                <span v-for="tag in folderTags(folder)" :key="tag.id" class="tag-chip shrink-0">{{ tag.name }}</span>
              </div>
            </article>
          </div>

          <div v-if="loading && folders.length" class="py-6 text-center">
            <div class="inline-block h-6 w-6 animate-spin rounded-full border-2 border-[var(--border-color)] border-t-[var(--color-primary-500)]"></div>
          </div>
          <div v-else-if="!hasMore && folders.length" class="py-8 text-center">
            <p class="text-xs text-[var(--text-muted)]">已经到底了</p>
          </div>
        </div>
      </div>

      </div>
    </main>

    <MediaPreview :is-open="previewOpen" :items="previewItems" :start-index="previewIndex" @close="previewOpen = false" @toggle-star="handleMediaStarChanged" @media-deleted="handleMediaChanged" @media-rotated="handleMediaChanged" @media-replaced="handleMediaChanged" />
  </div>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, nextTick, onActivated, onDeactivated, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import MediaPreview from '../components/MediaPreview.vue'
import { api } from '../composables/useApi'
import type { Folder, FolderTagCount, MessageMediaItem, RepositoryFile } from '../types'
import { resolveThumb } from '../utils/media'

defineOptions({ name: 'Folder' })

interface FolderCursorResponse {
  items: Folder[]
  next_cursor: number | null
  has_more: boolean
}

const MediaPlaceholder = defineComponent({
  setup: () => () => h('div', { class: 'grid h-full w-full place-items-center text-[var(--text-muted)]' }, [
    h('svg', { class: 'h-8 w-8', viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '1.4' }, [
      h('path', { d: 'M4 5h16v14H4zM7 15l3-3 2 2 2-2 3 3' }),
    ]),
  ]),
})

const VideoBadge = defineComponent({
  setup: () => () => h('span', { class: 'absolute left-2 top-2 grid h-7 w-7 place-items-center rounded-full bg-black/55 text-white' }, [
    h('svg', { class: 'h-3.5 w-3.5', viewBox: '0 0 24 24', fill: 'currentColor' }, [h('path', { d: 'm8 5 11 7-11 7z' })]),
  ]),
})

const folders = ref<Folder[]>([])
const tags = ref<FolderTagCount[]>([])
const selectedTagId = ref<number | null>(null)
const nextCursor = ref<number | null>(null)
const hasMore = ref(false)
const loading = ref(false)
const error = ref('')
const viewMode = ref<'grid' | 'feed'>('grid')
const gridMode = ref<GridMode>('mosaic')
const mobileTagsOpen = ref(false)
const scrollContainer = ref<HTMLElement | null>(null)
const previewOpen = ref(false)
const previewItems = ref<MessageMediaItem[]>([])
const previewIndex = ref(0)
const router = useRouter()
let infiniteScrollObserver: IntersectionObserver | null = null
let savedScrollTop = 0

const PREFETCH_DISTANCE = 10
type GridMode = 'mosaic' | 'fanart' | 'poster'

const gridModeOptions: { value: GridMode; label: string }[] = [
  { value: 'mosaic', label: '拼图' },
  { value: 'fanart', label: 'Fanart' },
  { value: 'poster', label: 'Poster' },
]

const activeFilterClass = 'bg-[var(--color-accent-soft)] text-[var(--color-primary-600)] dark:text-[var(--color-primary-500)] font-medium'
const inactiveFilterClass = 'text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)]'
const viewActiveClass = 'bg-[var(--bg-card)] text-[var(--color-primary-600)] shadow-[var(--shadow-sm)]'
const viewInactiveClass = 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'
const gridPreviewSizeClass = computed(() => {
  if (gridMode.value === 'poster') return 'aspect-[376/535]'
  if (gridMode.value === 'fanart') return 'aspect-[800/535]'
  return 'h-44'
})

function folderPath(folder: Folder) {
  if (!folder.primary_repo_id) return '位置不可用'
  return `${folder.primary_repo_id}/${folder.primary_folder_path || ''}`.replace(/\/$/, '')
}

function folderPreviews(folder: Folder) {
  return folder.preview_files ?? []
}

function folderGridFiles(folder: Folder) {
  const previews = folderPreviews(folder)
  if (gridMode.value === 'mosaic') return previews
  const cover = gridMode.value === 'fanart' ? folder.fanart_file : folder.poster_file
  return cover ? [cover] : previews.slice(0, 1)
}

function folderTags(folder: Folder) {
  return folder.tags ?? []
}

function previewGridClass(count: number) {
  if (count <= 1) return 'grid-cols-1'
  return 'grid-cols-2'
}

function mapPreviewFiles(files: RepositoryFile[]) {
  return files.filter(file => file.media_id !== null).map(file => ({
    id: file.media_id!, repo_id: file.repo_id, file_path: file.file_path,
    file_url: file.file_url, thumb_url: file.thumb_url,
    local_file_path: file.local_file_path, local_thumb_path: file.local_thumb_path,
    mime_type: file.mime_type, width: file.width, height: file.height,
    duration_ms: file.duration_ms, starred: file.starred, tags: [],
  } as unknown as MessageMediaItem))
}

async function loadTags() {
  try { tags.value = await api.get<FolderTagCount[]>('/folders/tags') }
  catch { tags.value = [] }
}

async function loadFolders(reset = false) {
  if (loading.value) return
  loading.value = true
  error.value = ''
  try {
    const data = await api.get<FolderCursorResponse>('/folders', {
      cursor: reset ? undefined : nextCursor.value,
      limit: 40,
      tag_id: selectedTagId.value,
    })
    folders.value = reset ? data.items : [...folders.value, ...data.items]
    nextCursor.value = data.next_cursor
    hasMore.value = data.has_more
  } catch (caught: any) {
    error.value = caught?.message || '加载目录失败'
  } finally {
    loading.value = false
    await nextTick()
    bindInfiniteScrollTarget()
  }
}

async function refresh() {
  scrollContainer.value?.scrollTo({ top: 0 })
  await Promise.all([loadTags(), loadFolders(true)])
}

async function selectTag(tagId: number | null) {
  if (selectedTagId.value === tagId) return
  selectedTagId.value = tagId
  mobileTagsOpen.value = false
  scrollContainer.value?.scrollTo({ top: 0 })
  await loadFolders(true)
}

function setupInfiniteScroll() {
  infiniteScrollObserver?.disconnect()
  const root = scrollContainer.value
  if (!root) return
  infiniteScrollObserver = new IntersectionObserver(entries => {
    if (entries[0]?.isIntersecting && !loading.value && hasMore.value) loadFolders()
  }, { root })
  bindInfiniteScrollTarget()
}

function bindInfiniteScrollTarget() {
  const root = scrollContainer.value
  if (!root || !infiniteScrollObserver) return
  const cards = root.querySelectorAll<HTMLElement>('[data-folder-id]')
  infiniteScrollObserver.disconnect()
  if (!cards.length || !hasMore.value) return
  const targetIndex = Math.max(0, cards.length - 1 - PREFETCH_DISTANCE)
  infiniteScrollObserver.observe(cards[targetIndex]!)
}

function setViewMode(mode: 'grid' | 'feed') {
  viewMode.value = mode
  localStorage.setItem('folder_view', mode)
  nextTick(bindInfiniteScrollTarget)
}

function setGridMode(mode: GridMode) {
  gridMode.value = mode
  persistGridMode()
}

function persistGridMode() {
  localStorage.setItem('folder_grid_mode', gridMode.value)
}

function openPreview(files: RepositoryFile[], index: number) {
  const materialized = files.filter(file => file.media_id !== null)
  const selected = files[index]
  const mappedIndex = materialized.findIndex(file => file.id === selected?.id)
  if (mappedIndex < 0) return
  previewItems.value = mapPreviewFiles(materialized)
  previewIndex.value = mappedIndex
  previewOpen.value = true
}

function openFolder(folderId: number) {
  savedScrollTop = scrollContainer.value?.scrollTop ?? 0
  router.push({ name: 'FolderDetail', params: { id: folderId } })
}

function handleMediaStarChanged(mediaId: number) {
  const starred = previewItems.value.find(item => item.id === mediaId)?.starred
  if (starred === undefined) return
  for (const folder of folders.value) {
    for (const file of folder.preview_files ?? []) {
      if (file.media_id === mediaId) file.starred = starred
    }
    if (folder.fanart_file?.media_id === mediaId) folder.fanart_file.starred = starred
    if (folder.poster_file?.media_id === mediaId) folder.poster_file.starred = starred
  }
}

async function handleMediaChanged() {
  await loadFolders(true)
}

onMounted(async () => {
  const saved = localStorage.getItem('folder_view')
  const savedGridMode = localStorage.getItem('folder_grid_mode')
  viewMode.value = saved === 'feed' ? 'feed' : 'grid'
  gridMode.value = savedGridMode === 'fanart' || savedGridMode === 'poster' ? savedGridMode : 'mosaic'
  await refresh()
  setupInfiniteScroll()
})

onActivated(() => {
  nextTick(() => {
    scrollContainer.value?.scrollTo({ top: savedScrollTop })
    setupInfiniteScroll()
  })
})

onDeactivated(() => {
  savedScrollTop = scrollContainer.value?.scrollTop ?? savedScrollTop
  infiniteScrollObserver?.disconnect()
})

onUnmounted(() => infiniteScrollObserver?.disconnect())
</script>
