<template>
  <div class="fixed inset-0 z-[95] flex flex-col bg-[var(--bg-primary)]">
    <div v-if="loading" class="grid flex-1 place-items-center">
      <div class="h-8 w-8 animate-spin rounded-full border-2 border-[var(--border-color)] border-t-[var(--color-primary-500)]"></div>
    </div>

    <template v-else-if="folder">
      <div class="flex-1 overflow-y-auto">
        <main class="mx-auto flex w-full max-w-[1600px] flex-col gap-6 px-4 py-6 sm:px-6 lg:flex-row lg:gap-8 lg:px-8 lg:py-10 xl:px-10">
          <article class="min-w-0 flex-1">
            <div v-if="mediaFiles.length" class="grid grid-cols-2 gap-2.5 rounded-[var(--radius-lg)] border border-[var(--border-color)] bg-[var(--bg-card)] p-2.5 shadow-[var(--shadow-sm)] sm:grid-cols-3 xl:grid-cols-4">
              <button
                v-for="(file, index) in mediaFiles"
                :key="file.id"
                class="group relative aspect-square overflow-hidden rounded-[var(--radius-md)] bg-[#181818]"
                @click="openPreview(index)"
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
            <div v-else class="grid min-h-72 place-items-center rounded-[var(--radius-lg)] border border-[var(--border-color)] bg-[var(--bg-card)] text-sm text-[var(--text-muted)]">
              暂无媒体
            </div>
          </article>

          <aside class="w-full shrink-0 self-start overflow-hidden rounded-[var(--radius-lg)] border border-[var(--border-color)] bg-[var(--bg-card)] shadow-[var(--shadow-sm)] lg:sticky lg:top-10 lg:w-72 xl:w-80">
            <div class="border-b border-[var(--border-color)] p-3">
              <button class="flex w-full items-center gap-2 rounded-[var(--radius-md)] px-2.5 py-2 text-sm font-medium text-[var(--text-secondary)] transition-colors hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)]" title="返回目录 (Esc)" @click="close">
                <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 19 3 12l7-7M3 12h18" /></svg>
                返回目录
              </button>
            </div>

            <div class="border-b border-[var(--border-color)] p-5">
              <div class="flex items-start gap-3">
                <span class="grid h-10 w-10 shrink-0 place-items-center rounded-[var(--radius-md)] bg-amber-500/12 text-amber-600 dark:text-amber-400">
                  <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M3.5 6.5h6l2 2h9v10h-17z" /></svg>
                </span>
                <div class="min-w-0">
                  <h1 class="truncate text-base font-semibold text-[var(--text-primary)]">{{ folder.name }}</h1>
                  <p class="mt-1 break-all text-xs leading-5 text-[var(--text-muted)]">{{ folderPath }}</p>
                </div>
              </div>
            </div>

            <div class="border-b border-[var(--border-color)] p-5">
              <h2 class="mb-3 text-xs font-semibold uppercase text-[var(--text-secondary)]">标签</h2>
              <div v-if="folder.tags.length" class="flex flex-wrap gap-2">
                <span v-for="tag in folder.tags" :key="tag.id" class="tag-chip">#{{ tag.name }}</span>
              </div>
              <p v-else class="text-sm text-[var(--text-muted)]">暂无标签</p>
            </div>

            <div class="border-b border-[var(--border-color)] p-5">
              <h2 class="mb-3 text-xs font-semibold uppercase text-[var(--text-secondary)]">基本信息</h2>
              <div class="space-y-2.5 text-sm">
                <div class="flex justify-between gap-3"><span class="text-[var(--text-muted)]">媒体数量</span><span>{{ folder.media_count }}</span></div>
                <div class="flex justify-between gap-3"><span class="text-[var(--text-muted)]">位置数量</span><span>{{ folder.location_count }}</span></div>
                <div v-if="folder.collection_name" class="flex justify-between gap-3"><span class="text-[var(--text-muted)]">合集</span><span class="truncate">{{ folder.collection_name }}</span></div>
                <div v-if="folder.issue_title" class="flex justify-between gap-3"><span class="text-[var(--text-muted)]">Issue</span><span class="truncate">{{ folder.issue_title }}</span></div>
              </div>
            </div>

            <div class="bg-[var(--bg-secondary)]/45 p-4">
              <input ref="uploadInput" class="hidden" type="file" multiple accept="video/mp4,image/jpeg,image/png,image/gif" @change="uploadFiles" />
              <button class="flex w-full items-center justify-center gap-2 rounded-[var(--radius-md)] bg-[var(--color-primary-600)] px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-[var(--color-primary-700)] disabled:opacity-50" :disabled="uploading" @click="uploadInput?.click()">
                <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 16V4m0 0-4 4m4-4 4 4M5 15v4h14v-4" /></svg>
                {{ uploading ? '上传中' : '上传文件' }}
              </button>
            </div>
          </aside>
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
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import MediaPreview from '../components/MediaPreview.vue'
import { api } from '../composables/useApi'
import { useToast } from '../composables/useToast'
import type { FolderDetail, MessageMediaItem, RepositoryFile } from '../types'
import { resolveThumb } from '../utils/media'

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

const mediaFiles = computed(() => folder.value?.files.filter(file => file.media_id !== null) ?? [])
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
  loading.value = true
  error.value = ''
  try {
    folder.value = await api.get<FolderDetail>(`/folders/${props.folderId}`)
  } catch (caught: any) {
    folder.value = null
    error.value = caught?.message || '加载目录失败'
  } finally {
    loading.value = false
  }
}

function openPreview(index: number) {
  previewItems.value = mapPreviewFiles(mediaFiles.value)
  previewIndex.value = index
  previewOpen.value = true
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
  loadFolder()
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => window.removeEventListener('keydown', handleKeydown))
</script>
