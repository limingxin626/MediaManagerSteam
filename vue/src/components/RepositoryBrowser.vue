<template>
  <div class="h-full flex flex-col">
    <div class="shrink-0 border-b border-[var(--border-color)] px-4 sm:px-6 py-3 space-y-3">
      <div class="flex items-center gap-3 flex-wrap">
        <select
          v-model="selectedRepoId"
          class="max-w-xs rounded-lg bg-gray-100 dark:bg-white/10 px-3 py-2 text-sm text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-1 focus:ring-[var(--color-primary-500)]"
          aria-label="选择仓库"
        >
          <option v-for="repo in repositories" :key="repo.repo_id" :value="repo.repo_id">
            {{ repo.repo_id }}
          </option>
        </select>
        <span v-if="selectedRepository" class="text-xs text-[var(--text-muted)]">
          <span :class="selectedRepository.online ? 'text-emerald-500' : 'text-red-400'">
            {{ selectedRepository.online ? '在线' : '离线' }}
          </span>
          · {{ selectedRepository.folder_count }} 个文件夹
          · {{ selectedRepository.file_count }} 个文件
          <span v-if="selectedRepository.pending_count" class="text-amber-500">
            · {{ selectedRepository.pending_count }} 个处理中
          </span>
        </span>
      </div>

      <nav v-if="selectedRepoId" class="flex items-center gap-1 overflow-x-auto text-sm" aria-label="文件夹路径">
        <button class="shrink-0 text-[var(--color-primary-600)] hover:underline" @click="openFolder('')">
          {{ selectedRepoId }}
        </button>
        <template v-for="crumb in breadcrumbs" :key="crumb.path">
          <span class="text-[var(--text-muted)]">/</span>
          <button
            class="shrink-0 text-gray-700 dark:text-gray-200 hover:text-[var(--color-primary-600)] hover:underline"
            @click="openFolder(crumb.path)"
          >
            {{ crumb.name }}
          </button>
        </template>
      </nav>
    </div>

    <div class="flex-1 overflow-y-auto p-3 sm:p-4">
      <div v-if="error" class="py-16 text-center text-sm text-red-400">{{ error }}</div>
      <div v-else-if="loading && !browse" class="py-16 text-center text-sm text-[var(--text-muted)]">加载中…</div>
      <template v-else-if="browse">
        <div v-if="!browse.folders.length && !browse.files.length" class="py-20 text-center text-sm text-[var(--text-muted)]">
          此文件夹为空
        </div>
        <div v-else class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 lg:grid-cols-7 xl:grid-cols-8 gap-3">
          <button
            v-for="folder in browse.folders"
            :key="`folder:${folder.id}`"
            class="aspect-square rounded-xl border border-[var(--border-color)] bg-gray-50 dark:bg-white/5 p-3 flex flex-col items-center justify-center gap-2 hover:border-[var(--color-primary-500)] hover:bg-[var(--color-primary-500)]/5 transition-colors min-w-0"
            :title="folder.name"
            @click="openFolder(folder.rel_path)"
          >
            <svg class="w-12 h-12 text-amber-400" fill="currentColor" viewBox="0 0 24 24">
              <path d="M3 6a2 2 0 012-2h4l2 2h8a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V6z" />
            </svg>
            <span class="w-full truncate text-sm text-gray-800 dark:text-gray-100">{{ folder.name }}</span>
          </button>

          <button
            v-for="(file, index) in visibleFiles"
            :key="`file:${file.id}`"
            class="relative aspect-square rounded-xl overflow-hidden bg-gray-200 dark:bg-gray-900 text-left group"
            :title="file.name"
            @click="openPreview(index)"
          >
            <img
              v-if="file.thumb_url"
              :src="physicalUrl(file.thumb_url)"
              :alt="file.name"
              class="absolute inset-0 w-full h-full object-cover"
              loading="lazy"
            />
            <div v-else class="absolute inset-0 flex items-center justify-center text-gray-400">
              <svg class="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M7 3h7l5 5v13H7zM14 3v6h5" />
              </svg>
            </div>
            <div class="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/80 to-transparent px-2 pt-8 pb-2">
              <p class="truncate text-xs text-white">{{ file.name }}</p>
            </div>
            <span
              v-if="file.materialize_status !== 'done'"
              class="absolute top-1.5 right-1.5 rounded-full px-2 py-0.5 text-[10px] text-white"
              :class="file.materialize_status === 'failed' ? 'bg-red-500/90' : 'bg-amber-500/90'"
            >
              {{ file.materialize_status === 'failed' ? '失败' : '处理中' }}
            </span>
            <svg v-if="file.media_type === 'VIDEO'" class="absolute inset-0 m-auto w-9 h-9 text-white/90 drop-shadow" fill="currentColor" viewBox="0 0 24 24">
              <path d="M8 5v14l11-7z" />
            </svg>
          </button>
        </div>

        <div v-if="hasMoreFiles" class="py-6 text-center">
          <button
            class="rounded-full px-4 py-2 text-sm bg-gray-100 dark:bg-white/10 text-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-white/20"
            @click="loadMoreFiles"
          >
            加载更多
          </button>
        </div>
      </template>
      <div v-else-if="!repositories.length && !loading" class="py-20 text-center text-sm text-[var(--text-muted)]">
        没有配置媒体仓库
      </div>
    </div>

    <PhysicalMediaPreview
      :is-open="previewOpen"
      :items="visibleFiles"
      :start-index="previewStartIndex"
      :has-more="hasMoreFiles"
      @close="previewOpen = false"
      @load-more="loadMoreForPreview"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { API_BASE_URL } from '../utils/constants'
import { useRepositoryBrowser } from '../composables/useRepositoryBrowser'
import PhysicalMediaPreview from './PhysicalMediaPreview.vue'

const {
  repositories,
  selectedRepoId,
  selectedRepository,
  currentPath,
  browse,
  visibleFiles,
  hasMoreFiles,
  loading,
  error,
  openFolder,
  loadMoreFiles,
} = useRepositoryBrowser()

const breadcrumbs = computed(() => {
  const parts = currentPath.value.split('/').filter(Boolean)
  return parts.map((name, index) => ({ name, path: parts.slice(0, index + 1).join('/') }))
})

const previewOpen = ref(false)
const previewStartIndex = ref(0)

function physicalUrl(path: string) {
  if (/^(https?:|file:|data:|blob:)/i.test(path)) return path
  return `${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`
}

function openPreview(index: number) {
  previewStartIndex.value = index
  previewOpen.value = true
}

function loadMoreForPreview() {
  if (hasMoreFiles.value) loadMoreFiles()
}
</script>
