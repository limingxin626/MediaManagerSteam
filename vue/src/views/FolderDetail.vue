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
          <input ref="uploadInput" class="hidden" type="file" multiple accept="video/mp4,image/jpeg,image/png,image/gif" @change="uploadFiles" />
          <button class="flex h-9 shrink-0 items-center justify-center gap-2 rounded-[var(--radius-md)] bg-[var(--color-primary-600)] px-3 text-sm font-medium text-white transition-colors hover:bg-[var(--color-primary-700)] disabled:opacity-50" :disabled="uploading" @click="uploadInput?.click()">
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 16V4m0 0-4 4m4-4 4 4M5 15v4h14v-4" /></svg>
            <span class="hidden sm:inline">{{ uploading ? '上传中' : '上传文件' }}</span>
          </button>
        </div>
      </header>

      <div class="min-h-0 flex-1 overflow-y-auto">
        <main class="mx-auto w-full max-w-[1600px] space-y-5 px-4 py-5 sm:px-6 lg:space-y-7 lg:px-8 lg:py-7 xl:px-10">
          <button
            v-if="fanartFile"
            class="group relative block h-[clamp(16rem,48vw,38rem)] w-full overflow-hidden rounded-[var(--radius-lg)] bg-[#181818] text-left shadow-[var(--shadow-md)]"
            @click="openPreview(fanartFile)"
          >
            <img
              v-if="fanartUrl"
              :src="fanartUrl"
              :alt="fanartFile.name"
              class="h-full w-full object-cover transition-transform duration-300 group-hover:scale-[1.01]"
              @error="handleFanartError"
            />
            <div v-else class="grid h-full w-full place-items-center text-[var(--text-muted)]">
              <svg class="h-12 w-12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M4 5h16v14H4zM7 15l3-3 2 2 2-2 3 3" /></svg>
            </div>
            <div class="pointer-events-none absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/70 via-black/25 to-transparent px-5 pb-4 pt-16 text-white sm:px-7 sm:pb-6">
              <p class="truncate text-xl font-semibold drop-shadow sm:text-2xl">{{ folder.name }}</p>
              <p class="mt-1 text-xs text-white/75">Fanart</p>
            </div>
          </button>

          <div class="grid items-start gap-5 lg:grid-cols-[minmax(0,1fr)_18rem] lg:gap-7 xl:grid-cols-[minmax(0,1fr)_20rem]">
          <article class="min-w-0 overflow-hidden rounded-[var(--radius-lg)] border border-[var(--border-color)] bg-[var(--bg-card)] shadow-[var(--shadow-sm)]">
            <div class="flex h-12 items-center justify-between border-b border-[var(--border-color)] px-4 sm:px-5">
              <h2 class="text-sm font-semibold text-[var(--text-primary)]">媒体</h2>
              <span class="text-xs tabular-nums text-[var(--text-muted)]">{{ mediaFiles.length }} 项</span>
            </div>
            <div v-if="mediaFiles.length" class="grid grid-cols-2 gap-2.5 p-2.5 sm:grid-cols-3 xl:grid-cols-4">
              <button
                v-for="file in mediaFiles"
                :key="file.id"
                class="group relative aspect-square overflow-hidden rounded-[var(--radius-md)] bg-[#181818]"
                @click="openPreview(file)"
              >
                <img
                  v-if="resolveThumb(file)"
                  :src="resolveThumb(file)"
                  :alt="file.name"
                  class="h-full w-full object-cover transition-transform duration-200 group-hover:scale-[1.03]"
                  loading="lazy"
                />
                <div v-else class="grid h-full w-full place-items-center text-[var(--text-muted)]">
                  <svg class="h-8 w-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M4 5h16v14H4zM7 15l3-3 2 2 2-2 3 3" /></svg>
                </div>
                <span v-if="file.media_type === 'VIDEO'" class="absolute left-2 top-2 grid h-8 w-8 place-items-center rounded-full bg-black/55 text-white">
                  <svg class="h-4 w-4" viewBox="0 0 24 24" fill="currentColor"><path d="m8 5 11 7-11 7z" /></svg>
                </span>
                <span class="absolute inset-x-0 bottom-0 truncate bg-black/60 px-2 py-1.5 text-left text-xs text-white">{{ file.name }}</span>
              </button>
            </div>
            <div v-else class="grid min-h-72 place-items-center px-6 text-center text-sm text-[var(--text-muted)]">
              暂无其他媒体
            </div>
          </article>

          <aside class="w-full overflow-hidden rounded-[var(--radius-lg)] border border-[var(--border-color)] bg-[var(--bg-card)] shadow-[var(--shadow-sm)] lg:sticky lg:top-5">
            <button v-if="posterFile" class="group relative mx-auto block aspect-[376/535] w-full max-w-sm overflow-hidden bg-[#181818]" @click="openPreview(posterFile)">
              <img v-if="resolveThumb(posterFile)" :src="resolveThumb(posterFile)" :alt="posterFile.name" class="h-full w-full object-cover transition-transform duration-300 group-hover:scale-[1.02]" />
              <div v-else class="grid h-full w-full place-items-center text-[var(--text-muted)]">
                <svg class="h-10 w-10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M4 5h16v14H4zM7 15l3-3 2 2 2-2 3 3" /></svg>
              </div>
              <span class="absolute bottom-3 left-3 rounded-full bg-black/60 px-2.5 py-1 text-xs text-white/90 backdrop-blur">Poster</span>
            </button>

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
                <div class="flex justify-between gap-3"><span class="text-[var(--text-muted)]">媒体数量</span><span>{{ folder.media_count }}</span></div>
                <div class="flex justify-between gap-3"><span class="text-[var(--text-muted)]">位置数量</span><span>{{ folder.location_count }}</span></div>
                <div v-if="folder.collection_name" class="flex justify-between gap-3"><span class="text-[var(--text-muted)]">合集</span><span class="truncate">{{ folder.collection_name }}</span></div>
                <div v-if="folder.issue_title" class="flex justify-between gap-3"><span class="text-[var(--text-muted)]">Issue</span><span class="truncate">{{ folder.issue_title }}</span></div>
              </div>
            </div>

          </aside>
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

    <MediaPreview :is-open="previewOpen" :items="previewItems" :start-index="previewIndex" @close="previewOpen = false" @media-deleted="loadFolder" @media-rotated="loadFolder" @media-replaced="loadFolder" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import MediaPreview from '../components/MediaPreview.vue'
import { api } from '../composables/useApi'
import { useToast } from '../composables/useToast'
import type { FolderDetail, MessageMediaItem, RepositoryFile } from '../types'
import { resolveMediaUrl, resolveThumb } from '../utils/media'

const props = defineProps<{ folderId: number }>()
const router = useRouter()
const toast = useToast()
const folder = ref<FolderDetail | null>(null)
const loading = ref(true)
const error = ref('')
const uploading = ref(false)
const uploadInput = ref<HTMLInputElement | null>(null)
const previewOpen = ref(false)
const previewItems = ref<MessageMediaItem[]>([])
const previewIndex = ref(0)
const fanartFallback = ref(false)
let loadRequest = 0

const fanartFile = computed(() => folder.value?.fanart_file ?? null)
const posterFile = computed(() => folder.value?.poster_file ?? null)
const primaryFolderId = computed(() => folder.value?.locations.find(location => location.role === 'PRIMARY')?.id ?? null)
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
    [fanartFile.value?.media_id, posterFile.value?.media_id].filter((id): id is number => id !== null && id !== undefined),
  )
  return allMediaFiles.value.filter(file => !artworkMediaIds.has(file.media_id!))
})
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
    duration_ms: file.duration_ms, starred: false, tags: [],
  } as unknown as MessageMediaItem))
}

async function loadFolder() {
  const request = ++loadRequest
  loading.value = true
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
    if (request === loadRequest) loading.value = false
  }
}

function openPreview(file: RepositoryFile) {
  previewItems.value = mapPreviewFiles(allMediaFiles.value)
  previewIndex.value = allMediaFiles.value.findIndex(item => item.media_id === file.media_id)
  if (previewIndex.value < 0) return
  previewOpen.value = true
}

function handleFanartError() {
  if (!fanartFallback.value) fanartFallback.value = true
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
  window.addEventListener('keydown', handleKeydown)
})

watch(() => props.folderId, loadFolder, { immediate: true })

onUnmounted(() => {
  loadRequest++
  window.removeEventListener('keydown', handleKeydown)
})
</script>
