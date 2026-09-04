<template>
  <div class="fixed inset-0 z-[95] flex flex-col bg-[var(--bg-primary)]">
    <div v-if="loading" class="grid flex-1 place-items-center">
      <div class="h-8 w-8 animate-spin rounded-full border-2 border-[var(--border-color)] border-t-[var(--color-primary-500)]"></div>
    </div>

    <template v-else-if="folder">
      <header class="z-20 shrink-0 border-b border-[var(--border-color)] bg-[var(--bg-card)]/95 backdrop-blur">
        <div class="mx-auto flex h-14 w-full max-w-[1600px] items-center gap-3 px-3 sm:px-6 lg:px-8 xl:px-10">
          <button class="grid h-9 w-9 shrink-0 place-items-center rounded-[var(--radius-md)] text-[var(--text-secondary)] transition-colors hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)]" title="返回目录 (Esc)" @click="close">
            <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 19 3 12l7-7M3 12h18" /></svg>
          </button>
          <div class="min-w-0 flex-1">
            <h1 class="truncate text-sm font-semibold text-[var(--text-primary)] sm:text-base">{{ folder.name }}</h1>
            <p class="truncate text-xs text-[var(--text-muted)]">{{ folderPath }}</p>
          </div>
          <button v-if="isElectron" class="flex h-9 shrink-0 items-center justify-center gap-2 rounded-[var(--radius-md)] border border-[var(--border-color)] bg-[var(--bg-card)] px-3 text-sm font-medium text-[var(--text-secondary)] transition-colors hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)] disabled:cursor-not-allowed disabled:opacity-50" :disabled="!primaryLocation?.local_path" title="在系统文件管理器中打开" @click="openFolderPath">
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3.5 6.5h6l2 2h9v10h-17z" /></svg>
            <span class="hidden sm:inline">打开文件夹</span>
          </button>
          <input ref="uploadInput" class="hidden" type="file" multiple accept="video/mp4,image/jpeg,image/png,image/gif" @change="uploadFiles" />
          <button class="flex h-9 shrink-0 items-center justify-center gap-2 rounded-[var(--radius-md)] bg-[var(--color-primary-600)] px-3 text-sm font-medium text-white transition-colors hover:bg-[var(--color-primary-700)] disabled:opacity-50" :disabled="uploading" @click="uploadInput?.click()">
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 16V4m0 0-4 4m4-4 4 4M5 15v4h14v-4" /></svg>
            <span class="hidden sm:inline">{{ uploading ? '上传中' : '上传文件' }}</span>
          </button>
        </div>
      </header>

      <div ref="scrollContainer" class="min-h-0 flex-1 overflow-y-auto">
        <main class="mx-auto w-full max-w-[1760px] space-y-8 px-4 py-6 sm:px-6 lg:space-y-10 lg:px-8 lg:py-8 xl:px-10">
          <section class="mx-auto grid w-full items-start overflow-hidden rounded-[var(--radius-lg)] border border-[var(--border-color)] bg-[var(--bg-card)] shadow-[var(--shadow-md)] lg:max-w-[56.25rem] lg:grid-cols-[800fr_376fr] xl:max-w-[62.5rem]">
          <button
            v-if="featuredVideo"
            class="group relative block aspect-video w-full overflow-hidden bg-black text-left"
            @click="openPreview(featuredVideo)"
          >
            <img
              v-if="resolveThumb(featuredVideo)"
              :src="resolveThumb(featuredVideo)"
              :alt="featuredVideo.name"
              class="h-full w-full object-cover transition-transform duration-300 group-hover:scale-[1.01]"
            />
            <div v-else class="grid h-full w-full place-items-center text-white/65">
              <svg class="h-12 w-12" viewBox="0 0 24 24" fill="currentColor"><path d="m8 5 11 7-11 7z" /></svg>
            </div>
          </button>
          <button
            v-else-if="fanartFile"
            class="group relative block w-full overflow-hidden text-left"
            @click="openPreview(fanartFile)"
          >
            <img
              v-if="fanartUrl"
              :src="fanartUrl"
              :alt="fanartFile.name"
              class="block h-auto w-full transition-transform duration-300 group-hover:scale-[1.01]"
              @error="handleFanartError"
            />
            <div v-else class="grid h-full w-full place-items-center text-[var(--text-muted)]">
              <svg class="h-12 w-12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M4 5h16v14H4zM7 15l3-3 2 2 2-2 3 3" /></svg>
            </div>
          </button>

          <aside class="w-full overflow-hidden border-t border-[var(--border-color)] bg-[var(--bg-card)] lg:border-l lg:border-t-0">
            <div class="border-b border-[var(--border-color)] p-5">
              <h2 class="truncate text-base font-semibold text-[var(--text-primary)]">{{ folder.name }}</h2>
              <p class="mt-1 break-all text-xs leading-5 text-[var(--text-muted)]">{{ folderPath }}</p>
            </div>

            <div class="border-b border-[var(--border-color)] p-5">
              <h2 class="mb-3 text-xs font-semibold uppercase text-[var(--text-secondary)]">标签</h2>
              <div v-if="folder.tags.length" class="flex flex-wrap gap-2">
                <span v-for="tag in folder.tags" :key="tag.id" class="tag-chip">#{{ tag.name }}</span>
              </div>
              <p v-else class="text-sm text-[var(--text-muted)]">暂无标签</p>
            </div>

            <div class="p-5">
              <h2 class="mb-3 text-xs font-semibold uppercase text-[var(--text-secondary)]">基本信息</h2>
              <div class="space-y-2.5 text-sm">
                <div class="flex items-center justify-between gap-3">
                  <span class="text-[var(--text-muted)]">Kind</span>
                  <span class="inline-flex min-w-0 items-center gap-1.5">
                    <span class="truncate">{{ folderKindLabel }}</span>
                    <code class="rounded bg-[var(--bg-secondary)] px-1.5 py-0.5 text-[11px] text-[var(--text-secondary)]">{{ folder.kind }}</code>
                  </span>
                </div>
                <div class="flex justify-between gap-3"><span class="text-[var(--text-muted)]">媒体数量</span><span>{{ folder.media_count }}</span></div>
                <div v-if="folder.entries.length" class="flex justify-between gap-3"><span class="text-[var(--text-muted)]">内容条目</span><span>{{ folder.entries.length }}</span></div>
                <div v-if="folder.gallery.length" class="flex justify-between gap-3"><span class="text-[var(--text-muted)]">图集图片</span><span>{{ folder.gallery.length }}</span></div>
                <div v-if="folder.extras.length" class="flex justify-between gap-3"><span class="text-[var(--text-muted)]">附加内容</span><span>{{ folder.extras.length }}</span></div>
                <div v-if="folder.unclassified.length" class="flex justify-between gap-3"><span class="text-[var(--text-muted)]">未分类</span><span class="text-amber-500">{{ folder.unclassified.length }}</span></div>
                <div class="flex justify-between gap-3"><span class="text-[var(--text-muted)]">位置数量</span><span>{{ folder.location_count }}</span></div>
                <div v-if="folder.collection_name" class="flex justify-between gap-3"><span class="text-[var(--text-muted)]">合集</span><span class="truncate">{{ folder.collection_name }}</span></div>
                <div v-if="folder.issue_title" class="flex justify-between gap-3"><span class="text-[var(--text-muted)]">Issue</span><span class="truncate">{{ folder.issue_title }}</span></div>
              </div>
            </div>
          </aside>
          </section>

          <section v-if="folderPreviews.length" class="overflow-hidden rounded-[var(--radius-lg)] border border-[var(--border-color)] bg-[var(--bg-card)] shadow-[var(--shadow-sm)]">
            <div class="flex h-12 items-center justify-between border-b border-[var(--border-color)] px-4 sm:px-5">
              <div class="flex items-center gap-2">
                <h2 class="text-sm font-semibold text-[var(--text-primary)]">Preview</h2>
                <span class="rounded-full bg-[var(--color-accent-soft)] px-2 py-0.5 text-[11px] font-medium text-[var(--color-primary-600)]">章节</span>
              </div>
              <span class="text-xs tabular-nums text-[var(--text-muted)]">{{ folderPreviews.length }} 项</span>
            </div>
            <div class="grid grid-cols-2 gap-3 p-3 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6">
              <button
                v-for="preview in folderPreviews"
                :key="preview.id"
                class="group relative aspect-square overflow-hidden rounded-[var(--radius-md)] text-left"
                @click="openFolderPreview(preview)"
              >
                <img v-if="resolveThumb(preview)" :src="resolveThumb(preview)" :alt="preview.name" class="h-full w-full object-contain transition-transform duration-200 group-hover:scale-[1.03]" loading="lazy" />
                <div v-else class="grid h-full w-full place-items-center text-[var(--text-muted)]">
                  <svg class="h-8 w-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M4 5h16v14H4zM7 15l3-3 2 2 2-2 3 3" /></svg>
                </div>
                <span v-if="preview.frame_ms !== null" class="absolute right-2 top-2 rounded-full bg-black/60 px-2 py-0.5 text-[10px] tabular-nums text-white/90 backdrop-blur">{{ formatFrameTime(preview.frame_ms) }}</span>
              </button>
            </div>
          </section>

          <article v-for="group in mediaGroups" :key="group.title" class="min-w-0">
            <div class="flex h-12 items-center justify-between">
              <h2 class="text-sm font-semibold text-[var(--text-primary)]">{{ group.title }}</h2>
              <div class="flex items-center gap-3">
                <span class="text-xs tabular-nums text-[var(--text-muted)]">{{ group.files.length }} 项</span>
                <button class="flex h-7 items-center gap-1.5 rounded-[var(--radius-sm)] border border-[var(--border-color)] bg-[var(--bg-secondary)] px-2 text-xs font-medium text-[var(--text-secondary)] transition-colors hover:text-[var(--text-primary)]" :title="mediaFit === 'cover' ? '当前：填充裁切，点击切换为完整显示' : '当前：完整显示，点击切换为填充裁切'" @click="toggleMediaFit">
                  <svg v-if="mediaFit === 'cover'" class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M8 3H3v5M16 3h5v5M8 21H3v-5M16 21h5v-5" /></svg>
                  <svg v-else class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M9 4H4v5M15 4h5v5M9 20H4v-5M15 20h5v-5" /><path d="M8 8h8v8H8z" /></svg>
                  {{ mediaFit === 'cover' ? 'Cover' : 'Contain' }}
                </button>
              </div>
            </div>
            <div class="grid grid-cols-2 gap-x-5 gap-y-7 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6">
              <button
                v-for="file in group.files"
                :key="file.id"
                class="group min-w-0 text-left"
                @click="openPreview(file)"
              >
                <div class="relative aspect-square overflow-hidden">
                  <img
                    v-if="resolveThumb(file)"
                    :src="resolveThumb(file)"
                    :alt="file.name"
                    class="h-full w-full transition-transform duration-200 group-hover:scale-[1.03]"
                    :class="mediaFit === 'cover' ? 'object-cover' : 'object-contain'"
                    loading="lazy"
                  />
                  <div v-else class="grid h-full w-full place-items-center text-[var(--text-muted)]">
                    <svg class="h-8 w-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M4 5h16v14H4zM7 15l3-3 2 2 2-2 3 3" /></svg>
                  </div>
                </div>
                <span class="mt-2.5 block truncate px-1 text-center text-xs text-[var(--text-secondary)] group-hover:text-[var(--text-primary)]" :title="file.name">{{ file.name }}</span>
              </button>
            </div>
          </article>
          <div v-if="!mediaGroups.length" class="grid min-h-72 place-items-center px-6 text-center text-sm text-[var(--text-muted)]">
            暂无媒体
          </div>
        </main>
      </div>
    </template>

    <div v-else class="grid flex-1 place-items-center px-6 text-center">
      <div>
        <p class="text-sm text-red-500">{{ error || '目录不存在' }}</p>
        <button class="mt-4 text-sm text-[var(--color-primary-600)]" @click="close">返回目录</button>
      </div>
    </div>

    <MediaPreview :is-open="previewOpen" :items="previewItems" :start-index="previewIndex" :all-tags="allTags" @close="previewOpen = false" @toggle-star="handleMediaStarChanged" @media-deleted="handleMediaDeleted" @media-rotated="refreshFolder" @media-replaced="refreshFolder" />
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import MediaPreview from '../components/MediaPreview.vue'
import { api } from '../composables/useApi'
import { useToast } from '../composables/useToast'
import type { FolderDetail, FolderPreview, MessageMediaItem, RepositoryFile, TagWithCount } from '../types'
import { IS_ELECTRON } from '../utils/constants'
import { resolveMediaUrl, resolveThumb } from '../utils/media'

const props = defineProps<{ folderId: number }>()
const router = useRouter()
const toast = useToast()
const folder = ref<FolderDetail | null>(null)
const loading = ref(true)
const error = ref('')
const uploading = ref(false)
const uploadInput = ref<HTMLInputElement | null>(null)
const scrollContainer = ref<HTMLElement | null>(null)
const previewOpen = ref(false)
const previewItems = ref<MessageMediaItem[]>([])
const previewIndex = ref(0)
const allTags = ref<TagWithCount[]>([])
const fanartFallback = ref(false)
const mediaFit = ref<'cover' | 'contain'>('cover')
let loadRequest = 0
const isElectron = IS_ELECTRON

const fanartFile = computed(() => folder.value?.artwork.fanart ?? null)
const posterFile = computed(() => folder.value?.artwork.poster ?? null)
const folderPreviews = computed(() => folder.value?.previews ?? [])
const primaryLocation = computed(() => folder.value?.locations.find(location => location.role === 'PRIMARY') ?? null)
const primaryFolderId = computed(() => primaryLocation.value?.id ?? null)
const allMediaFiles = computed(() => {
  const unique = new Map<number, RepositoryFile>()
  for (const file of folder.value?.files ?? []) {
    if (file.media_id === null) continue
    const existing = unique.get(file.media_id)
    if (!existing || (file.folder_id === primaryFolderId.value && existing.folder_id !== primaryFolderId.value)) {
      unique.set(file.media_id, file)
    }
  }
  return [...unique.values()]
})
const mediaFiles = computed(() => {
  const artworkMediaIds = new Set(
    [
      fanartFile.value?.media_id,
      posterFile.value?.media_id,
      ...folderPreviews.value.map(preview => preview.id),
    ].filter((id): id is number => id !== null && id !== undefined),
  )
  return allMediaFiles.value.filter(file => (
    !artworkMediaIds.has(file.media_id!)
  ))
})
const videoFiles = computed(() => mediaFiles.value.filter(file => file.media_type === 'VIDEO'))
const featuredVideo = computed(() => videoFiles.value.length === 1 ? videoFiles.value[0] : null)
const mediaGroups = computed(() => [
  { title: '视频', files: featuredVideo.value ? [] : videoFiles.value },
  { title: folder.value?.kind === 'gallery' ? '图集' : '图片', files: mediaFiles.value.filter(file => file.media_type === 'IMAGE') },
].filter(group => group.files.length))
const folderKindLabel = computed(() => ({
  movie: '电影', multi_part: '多部内容', series: '剧集', gallery: '图集', video: '单视频', mixed: '混合媒体', unknown: '未分类',
}[folder.value?.kind ?? 'unknown']))
const fanartUrl = computed(() => {
  if (!fanartFile.value) return ''
  return fanartFallback.value
    ? resolveThumb(fanartFile.value)
    : resolveMediaUrl(fanartFile.value) || resolveThumb(fanartFile.value)
})
const folderPath = computed(() => {
  if (!folder.value?.primary_repo_id) return '位置不可用'
  return `${folder.value.primary_repo_id}/${folder.value.primary_folder_path || ''}`.replace(/\/$/, '')
})

function mapPreviewFiles(files: RepositoryFile[]) {
  return files.map(file => ({
    id: file.media_id!, repo_id: file.repo_id, file_path: file.file_path,
    file_url: file.file_url, thumb_url: file.thumb_url,
    local_file_path: file.local_file_path, local_thumb_path: file.local_thumb_path,
    mime_type: file.mime_type, width: file.width, height: file.height,
    duration_ms: file.duration_ms, starred: file.starred,
  } as unknown as MessageMediaItem))
}

async function fetchFolder(showLoading: boolean) {
  const request = ++loadRequest
  if (showLoading) loading.value = true
  error.value = ''
  fanartFallback.value = false
  try {
    const result = await api.get<FolderDetail>(`/folders/${props.folderId}`)
    if (request === loadRequest) folder.value = result
  } catch (caught: any) {
    if (request === loadRequest) {
      folder.value = null
      error.value = caught?.message || '加载目录失败'
    }
  } finally {
    if (request === loadRequest && showLoading) loading.value = false
  }
}

function loadFolder() {
  return fetchFolder(true)
}

function refreshFolder() {
  return fetchFolder(false)
}

async function fetchTags() {
  try {
    allTags.value = await api.get<TagWithCount[]>('/tags')
  } catch {
    allTags.value = []
  }
}

function mapFolderPreviews(previews: FolderPreview[]) {
  return previews.map(preview => ({
    id: preview.id, repo_id: preview.repo_id, file_path: preview.file_path,
    file_url: preview.file_url, thumb_url: preview.thumb_url,
    local_file_path: preview.local_file_path, local_thumb_path: preview.local_thumb_path,
    mime_type: preview.mime_type, width: preview.width, height: preview.height,
    duration_ms: preview.duration_ms, starred: preview.starred,
  } as unknown as MessageMediaItem))
}

function formatFrameTime(frameMs: number) {
  const totalSeconds = Math.floor(frameMs / 1000)
  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const seconds = totalSeconds % 60
  return hours > 0
    ? `${hours}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
    : `${minutes}:${String(seconds).padStart(2, '0')}`
}

function openPreview(file: RepositoryFile) {
  previewItems.value = mapPreviewFiles(allMediaFiles.value)
  previewIndex.value = allMediaFiles.value.findIndex(item => item.media_id === file.media_id)
  if (previewIndex.value < 0) return
  previewOpen.value = true
}

function openFolderPreview(preview: FolderPreview) {
  previewItems.value = mapFolderPreviews(folderPreviews.value)
  previewIndex.value = folderPreviews.value.findIndex(item => item.id === preview.id)
  if (previewIndex.value < 0) return
  previewOpen.value = true
}

function handleMediaStarChanged(mediaId: number) {
  const starred = previewItems.value.find(item => item.id === mediaId)?.starred
  if (starred === undefined || !folder.value) return
  for (const file of folder.value.files) {
    if (file.media_id === mediaId) file.starred = starred
  }
  for (const preview of folder.value.previews) {
    if (preview.id === mediaId) preview.starred = starred
  }
}

async function handleMediaDeleted(mediaId: number) {
  const scrollTop = scrollContainer.value?.scrollTop ?? 0
  previewItems.value = previewItems.value.filter(item => item.id !== mediaId)
  await refreshFolder()
  await nextTick()
  scrollContainer.value?.scrollTo({ top: scrollTop })
}

function handleFanartError() {
  if (!fanartFallback.value) fanartFallback.value = true
}

function toggleMediaFit() {
  mediaFit.value = mediaFit.value === 'cover' ? 'contain' : 'cover'
  localStorage.setItem('folder_detail_media_fit', mediaFit.value)
}

async function openFolderPath() {
  const path = primaryLocation.value?.local_path
  if (!path || !window.electronAPI?.openPath) {
    toast.error('文件夹位置不可用')
    return
  }
  try {
    const errorMessage = await window.electronAPI.openPath(path)
    if (errorMessage) toast.error(`无法打开文件夹：${errorMessage}`)
  } catch (caught: any) {
    toast.error(caught?.message || '无法打开文件夹')
  }
}

function close() {
  if (window.history.length > 1) router.back()
  else router.replace('/folders')
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key !== 'Escape' || previewOpen.value) return
  event.preventDefault()
  close()
}

async function uploadFiles(event: Event) {
  const input = event.target as HTMLInputElement
  const files = Array.from(input.files ?? [])
  if (!files.length || uploading.value) return
  uploading.value = true
  try {
    for (const file of files) {
      const form = new FormData()
      form.append('file', file)
      await api.post(`/folders/${props.folderId}/files`, form)
    }
    toast.success(`已上传 ${files.length} 个文件`)
    await loadFolder()
  } catch (caught: any) {
    toast.error(caught?.message || '上传失败')
  } finally {
    uploading.value = false
    input.value = ''
  }
}

onMounted(() => {
  mediaFit.value = localStorage.getItem('folder_detail_media_fit') === 'contain' ? 'contain' : 'cover'
  fetchTags()
  window.addEventListener('keydown', handleKeydown)
})

watch(() => props.folderId, loadFolder, { immediate: true })

onUnmounted(() => {
  loadRequest++
  window.removeEventListener('keydown', handleKeydown)
})
</script>
