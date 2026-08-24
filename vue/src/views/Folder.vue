<template>
  <div class="flex h-full min-h-0 bg-[var(--bg-primary)] text-[var(--text-primary)]">
    <aside
      class="w-full shrink-0 flex-col border-r border-[var(--border-color)] bg-[var(--sidebar-bg)] md:flex md:w-72"
      :class="selectedFolderId ? 'hidden' : 'flex'"
    >
      <header class="flex h-16 shrink-0 items-center justify-between border-b border-[var(--border-color)] px-5">
        <div>
          <h1 class="text-lg font-semibold">目录</h1>
          <p class="text-xs text-[var(--text-muted)]">{{ folders.length }} 个已加载</p>
        </div>
        <button
          class="grid h-9 w-9 place-items-center rounded-lg text-[var(--text-muted)] hover:bg-[var(--bg-card)] hover:text-[var(--text-primary)]"
          title="刷新"
          :disabled="loadingFolders"
          @click="loadFolders(true)"
        >
          <svg class="h-5 w-5" :class="{ 'animate-spin': loadingFolders }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
            <path d="M20 7v5h-5M4 17v-5h5M6.1 8.2A7 7 0 0 1 18.5 7M17.9 15.8A7 7 0 0 1 5.5 17" />
          </svg>
        </button>
      </header>

      <div class="min-h-0 flex-1 overflow-y-auto p-2">
        <div v-if="loadingFolders && !folders.length" class="py-16 text-center text-sm text-[var(--text-muted)]">加载中...</div>
        <div v-else-if="folderError && !folders.length" class="px-4 py-16 text-center">
          <p class="text-sm text-red-500">{{ folderError }}</p>
          <button class="mt-3 text-sm text-[var(--color-primary-600)]" @click="loadFolders(true)">重试</button>
        </div>
        <div v-else-if="!folders.length" class="py-16 text-center text-sm text-[var(--text-muted)]">暂无目录</div>

        <button
          v-for="folder in folders"
          :key="folder.id"
          class="mb-1 flex w-full items-center gap-3 rounded-lg px-3 py-3 text-left transition-colors hover:bg-[var(--bg-card)]"
          :class="selectedFolderId === folder.id ? 'bg-[var(--bg-card)] shadow-[var(--shadow-sm)]' : ''"
          @click="selectFolder(folder.id)"
        >
          <span class="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-amber-500/12 text-amber-600 dark:text-amber-400">
            <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
              <path d="M3.5 6.5h6l2 2h9v10h-17z" />
            </svg>
          </span>
          <span class="min-w-0 flex-1">
            <span class="flex items-center gap-1.5">
              <span class="truncate text-sm font-medium">{{ folder.name }}</span>
              <svg v-if="folder.starred" class="h-3.5 w-3.5 shrink-0 text-amber-500" viewBox="0 0 24 24" fill="currentColor"><path d="m12 2.8 2.8 5.7 6.3.9-4.6 4.4 1.1 6.3-5.6-3-5.6 3 1.1-6.3-4.6-4.4 6.3-.9z" /></svg>
            </span>
            <span class="mt-0.5 block truncate text-xs text-[var(--text-muted)]" :title="folderPath(folder)">{{ folderPath(folder) }}</span>
          </span>
          <span class="shrink-0 text-xs tabular-nums text-[var(--text-muted)]">{{ folder.media_count }}</span>
        </button>

        <button
          v-if="hasMore"
          class="my-2 w-full rounded-lg py-2 text-sm text-[var(--color-primary-600)] hover:bg-[var(--bg-card)] disabled:opacity-50"
          :disabled="loadingFolders"
          @click="loadFolders(false)"
        >
          {{ loadingFolders ? '加载中...' : '加载更多' }}
        </button>
      </div>
    </aside>

    <main class="min-w-0 flex-1 flex-col" :class="selectedFolderId ? 'flex' : 'hidden md:flex'">
      <div v-if="loadingDetail && !detail" class="grid flex-1 place-items-center text-sm text-[var(--text-muted)]">加载中...</div>
      <div v-else-if="detailError" class="grid flex-1 place-items-center px-6 text-center">
        <div>
          <p class="text-sm text-red-500">{{ detailError }}</p>
          <button class="mt-3 text-sm text-[var(--color-primary-600)]" @click="reloadDetail">重试</button>
        </div>
      </div>
      <div v-else-if="detail" class="flex min-h-0 flex-1 flex-col">
        <header class="shrink-0 border-b border-[var(--border-color)] bg-[var(--bg-card)] px-4 py-4 md:px-7">
          <div class="flex items-start gap-3">
            <button
              class="grid h-9 w-9 shrink-0 place-items-center rounded-lg text-[var(--text-muted)] hover:bg-[var(--bg-secondary)] md:hidden"
              title="返回目录列表"
              @click="closeMobileDetail"
            >
              <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="m15 5-7 7 7 7" /></svg>
            </button>
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-2">
                <h2 class="truncate text-xl font-semibold">{{ detail.name }}</h2>
                <span v-if="detail.starred" class="text-amber-500" title="已收藏">★</span>
              </div>
              <p class="mt-1 truncate text-xs text-[var(--text-muted)]" :title="folderPath(detail)">{{ folderPath(detail) }}</p>
            </div>
            <input ref="uploadInput" class="hidden" type="file" multiple accept="video/mp4,image/jpeg,image/png,image/gif" @change="uploadFiles" />
            <button
              class="inline-flex h-9 shrink-0 items-center gap-2 rounded-lg bg-[var(--color-primary-600)] px-3 text-sm font-medium text-white hover:bg-[var(--color-primary-700)] disabled:opacity-50"
              :disabled="uploading"
              @click="uploadInput?.click()"
            >
              <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 16V4m0 0-4 4m4-4 4 4M5 15v4h14v-4" /></svg>
              <span class="hidden sm:inline">{{ uploading ? '上传中...' : '上传' }}</span>
            </button>
          </div>

          <div class="mt-4 flex flex-wrap items-center gap-2 text-xs text-[var(--text-secondary)]">
            <span class="rounded-md bg-[var(--bg-secondary)] px-2 py-1">{{ detail.media_count }} 个媒体</span>
            <span class="rounded-md bg-[var(--bg-secondary)] px-2 py-1">{{ detail.files.length }} 个文件</span>
            <span v-if="detail.collection_name" class="rounded-md bg-[var(--color-accent-soft)] px-2 py-1 text-[var(--color-primary-600)]">{{ detail.collection_name }}</span>
            <span v-if="detail.issue_title" class="rounded-md bg-[var(--bg-secondary)] px-2 py-1">{{ detail.issue_title }}</span>
          </div>

          <div v-if="detail.locations.length > 1" class="mt-3 flex gap-2 overflow-x-auto pb-1">
            <span
              v-for="location in detail.locations"
              :key="location.id"
              class="max-w-sm shrink-0 truncate rounded-md border border-[var(--border-color)] px-2 py-1 text-xs text-[var(--text-muted)]"
              :title="`${location.repo_id}/${location.rel_path}`"
            >
              {{ location.role === 'PRIMARY' ? '主目录' : '镜像' }} · {{ location.repo_id }}/{{ location.rel_path }}
            </span>
          </div>
        </header>

        <div class="min-h-0 flex-1 overflow-y-auto p-3 pb-24 md:p-6 md:pb-6">
          <div v-if="!detail.files.length" class="grid h-full min-h-64 place-items-center text-sm text-[var(--text-muted)]">目录中没有媒体文件</div>
          <div v-else class="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6">
            <button
              v-for="(file, index) in detail.files"
              :key="file.id"
              class="group relative aspect-square min-w-0 overflow-hidden rounded-lg bg-[var(--bg-secondary)] text-left"
              :class="file.media_id ? 'cursor-pointer' : 'cursor-default'"
              :disabled="!file.media_id"
              @click="openPreview(file, index)"
            >
              <img
                v-if="file.media_id && resolveThumb(file)"
                :src="resolveThumb(file)"
                :alt="file.name"
                class="h-full w-full object-cover transition-transform duration-200 group-hover:scale-[1.02]"
                loading="lazy"
              />
              <div v-else class="grid h-full place-items-center text-[var(--text-muted)]">
                <svg class="h-9 w-9" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M4 5h16v14H4zM7 15l3-3 2 2 2-2 3 3" /></svg>
              </div>
              <div class="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/75 to-transparent px-2 pb-2 pt-8">
                <p class="truncate text-xs text-white" :title="file.name">{{ file.name }}</p>
              </div>
              <span v-if="file.media_type === 'VIDEO'" class="absolute left-2 top-2 grid h-7 w-7 place-items-center rounded-full bg-black/55 text-white">
                <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="currentColor"><path d="m8 5 11 7-11 7z" /></svg>
              </span>
              <span
                v-if="file.materialize_status !== 'done'"
                class="absolute right-2 top-2 rounded-md bg-black/60 px-1.5 py-1 text-[10px] text-white"
              >
                {{ statusLabel(file.materialize_status) }}
              </span>
            </button>
          </div>
        </div>
      </div>

      <div v-else class="grid flex-1 place-items-center text-[var(--text-muted)]">
        <div class="text-center">
          <svg class="mx-auto h-12 w-12 opacity-40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M3.5 6.5h6l2 2h9v10h-17z" /></svg>
          <p class="mt-3 text-sm">选择一个目录</p>
        </div>
      </div>
    </main>

    <MediaPreview
      :is-open="previewOpen"
      :items="previewItems"
      :start-index="previewIndex"
      @close="previewOpen = false"
      @media-deleted="handleMediaChanged"
      @media-rotated="handleMediaChanged"
      @media-replaced="handleMediaChanged"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { api } from '../composables/useApi'
import { useToast } from '../composables/useToast'
import MediaPreview from '../components/MediaPreview.vue'
import type { Folder, FolderDetail, MessageMediaItem, RepositoryFile } from '../types'
import { resolveThumb } from '../utils/media'

interface FolderCursorResponse {
  items: Folder[]
  next_cursor: number | null
  has_more: boolean
}

const folders = ref<Folder[]>([])
const selectedFolderId = ref<number | null>(null)
const detail = ref<FolderDetail | null>(null)
const nextCursor = ref<number | null>(null)
const hasMore = ref(false)
const loadingFolders = ref(false)
const loadingDetail = ref(false)
const uploading = ref(false)
const folderError = ref('')
const detailError = ref('')
const uploadInput = ref<HTMLInputElement | null>(null)
const previewOpen = ref(false)
const previewIndex = ref(0)
const toast = useToast()
let detailRequest = 0

const materializedFiles = computed(() => detail.value?.files.filter(file => file.media_id !== null) ?? [])
const previewItems = computed<MessageMediaItem[]>(() => materializedFiles.value.map(file => ({
  id: file.media_id!,
  repo_id: file.repo_id,
  file_path: file.file_path,
  file_url: file.file_url,
  thumb_url: file.thumb_url,
  local_file_path: file.local_file_path,
  local_thumb_path: file.local_thumb_path,
  mime_type: file.mime_type,
  width: file.width,
  height: file.height,
  duration_ms: file.duration_ms,
  starred: false,
  tags: [],
} as unknown as MessageMediaItem)))

function folderPath(folder: Folder) {
  if (!folder.primary_repo_id) return '位置不可用'
  return `${folder.primary_repo_id}/${folder.primary_folder_path || ''}`.replace(/\/$/, '')
}

function statusLabel(status: RepositoryFile['materialize_status']) {
  if (status === 'pending') return '处理中'
  if (status === 'failed') return '失败'
  return ''
}

async function loadFolders(reset = false) {
  if (loadingFolders.value) return
  loadingFolders.value = true
  folderError.value = ''
  try {
    const data = await api.get<FolderCursorResponse>('/folders', {
      cursor: reset ? undefined : nextCursor.value,
      limit: 40,
    })
    folders.value = reset ? data.items : [...folders.value, ...data.items]
    nextCursor.value = data.next_cursor
    hasMore.value = data.has_more
    if (!selectedFolderId.value && folders.value[0] && window.matchMedia('(min-width: 768px)').matches) {
      await selectFolder(folders.value[0].id)
    }
  } catch (error: any) {
    folderError.value = error?.message || '加载目录失败'
  } finally {
    loadingFolders.value = false
  }
}

async function selectFolder(folderId: number) {
  selectedFolderId.value = folderId
  detail.value = null
  detailError.value = ''
  loadingDetail.value = true
  const request = ++detailRequest
  try {
    const data = await api.get<FolderDetail>(`/folders/${folderId}`)
    if (request === detailRequest) detail.value = data
  } catch (error: any) {
    if (request === detailRequest) detailError.value = error?.message || '加载目录详情失败'
  } finally {
    if (request === detailRequest) loadingDetail.value = false
  }
}

async function reloadDetail() {
  if (selectedFolderId.value) await selectFolder(selectedFolderId.value)
}

function closeMobileDetail() {
  selectedFolderId.value = null
  detail.value = null
  detailError.value = ''
}

function openPreview(file: RepositoryFile, _fileIndex: number) {
  if (!file.media_id) return
  const index = materializedFiles.value.findIndex(item => item.id === file.id)
  if (index < 0) return
  previewIndex.value = index
  previewOpen.value = true
}

async function uploadFiles(event: Event) {
  const input = event.target as HTMLInputElement
  const files = Array.from(input.files ?? [])
  if (!selectedFolderId.value || !files.length || uploading.value) return
  uploading.value = true
  try {
    for (const file of files) {
      const form = new FormData()
      form.append('file', file)
      await api.post(`/folders/${selectedFolderId.value}/files`, form)
    }
    toast.success(`已上传 ${files.length} 个文件`)
    await Promise.all([reloadDetail(), loadFolders(true)])
  } catch (error: any) {
    toast.error(error?.message || '上传失败')
  } finally {
    uploading.value = false
    input.value = ''
  }
}

async function handleMediaChanged() {
  await Promise.all([reloadDetail(), loadFolders(true)])
}

onMounted(() => loadFolders(true))
</script>