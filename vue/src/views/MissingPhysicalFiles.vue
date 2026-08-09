<template>
  <section>
    <div class="flex items-start justify-between gap-4 mb-6">
      <div>
        <h2 class="text-xl font-semibold text-[var(--text-primary)]">文件缺失</h2>
        <p class="mt-1 text-sm text-[var(--text-muted)]">
          列出仓库扫描记录中没有已物化副本的媒体；离线仓库中已有记录的文件仍视为存在。
        </p>
      </div>
      <div class="shrink-0 flex items-center gap-2">
        <button
          class="px-3 py-2 text-sm rounded-lg bg-red-600 text-white hover:bg-red-700 disabled:opacity-40 disabled:cursor-not-allowed"
          :disabled="!selectedIds.size || loading || deleting"
          @click="deleteSelected"
        >
          {{ deleting ? '删除中...' : `删除全部 (${selectedIds.size})` }}
        </button>
        <button
          class="px-3 py-2 text-sm rounded-lg bg-[var(--bg-card)] border border-[var(--border-color)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] disabled:opacity-50"
          :disabled="loading || deleting"
          @click="refresh"
        >
          {{ loading ? '刷新中...' : '刷新' }}
        </button>
      </div>
    </div>

    <div v-if="loading && !items.length" class="py-20 text-center text-[var(--text-muted)]">加载中...</div>
    <div v-else-if="error && !items.length" class="py-20 text-center">
      <p class="text-red-500">{{ error }}</p>
      <button class="mt-3 text-sm text-[var(--color-primary-600)] hover:underline" @click="refresh">重试</button>
    </div>
    <div v-else-if="!items.length" class="py-20 text-center text-[var(--text-muted)]">没有缺失物理文件的媒体</div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      <article
        v-for="item in items"
        :key="item.id"
        class="relative rounded-xl border bg-[var(--bg-card)] transition-colors"
        :class="isSelected(item.id) ? 'border-red-500' : 'border-[var(--border-color)] hover:border-[var(--border-strong)]'"
      >
        <label class="absolute top-3 left-3 z-10 flex items-center justify-center w-8 h-8 rounded-lg bg-[var(--bg-card)]/90 shadow cursor-pointer" @click.stop>
          <input
            type="checkbox"
            :checked="isSelected(item.id)"
            :disabled="deleting"
            @change="toggleItem(item.id)"
          />
        </label>
        <RouterLink :to="`/media/${item.id}`" class="flex gap-4 p-4 pl-14">
          <img
            :src="resolveThumb(item)"
            :alt="String(item.id)"
            class="w-24 h-24 shrink-0 rounded-lg object-cover bg-gray-200 dark:bg-gray-800"
          />
          <div class="min-w-0 flex-1">
            <div class="flex items-center justify-between gap-2">
              <span class="font-medium text-[var(--text-primary)]">Media #{{ item.id }}</span>
              <span class="shrink-0 px-2 py-0.5 rounded-full text-xs bg-red-500/10 text-red-600 dark:text-red-400">无物理副本</span>
            </div>
            <p class="mt-2 text-sm text-[var(--text-secondary)] break-all">{{ mediaPath(item) }}</p>
            <p class="mt-2 text-xs text-[var(--text-muted)]">{{ mediaSummary(item) }}</p>
          </div>
        </RouterLink>
      </article>
    </div>

    <p v-if="error && items.length" class="mt-4 text-center text-sm text-red-500">{{ error }}</p>
    <div v-if="hasMore" class="py-6 text-center">
      <button
        class="px-4 py-2 rounded-lg bg-[var(--color-primary-600)] text-white disabled:opacity-50"
        :disabled="loading || deleting"
        @click="loadMore"
      >
        {{ loading ? '加载中...' : '加载更多' }}
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api } from '../composables/useApi'
import { useConfirm } from '../composables/useConfirm'
import { useToast } from '../composables/useToast'
import type { CursorResponse, Media } from '../types'
import { formatDuration, formatSize, resolveThumb } from '../utils/media'

const items = ref<Media[]>([])
const selectedIds = ref(new Set<number>())
const nextCursor = ref<string | null>(null)
const hasMore = ref(false)
const loading = ref(false)
const deleting = ref(false)
const error = ref('')
const { confirm } = useConfirm()
const toast = useToast()

function isSelected(id: number) {
  return selectedIds.value.has(id)
}

function toggleItem(id: number) {
  if (deleting.value) return
  const next = new Set(selectedIds.value)
  next.has(id) ? next.delete(id) : next.add(id)
  selectedIds.value = next
}

function mediaPath(item: Media) {
  return [item.repo_id, item.file_path].filter(Boolean).join('/')
}

function mediaSummary(item: Media) {
  const parts = [item.mime_type || '未知类型']
  const size = formatSize(item.file_size)
  if (size) parts.push(size)
  const duration = formatDuration(item.duration_ms)
  if (duration) parts.push(duration)
  return parts.join(' · ')
}

async function fetchItems(reset = false) {
  if (loading.value || deleting.value) return
  loading.value = true
  error.value = ''
  try {
    const data = await api.get<CursorResponse<Media>>('/media', {
      cursor: reset ? undefined : nextCursor.value,
      limit: 50,
      has_physical_file: false,
    })
    items.value = reset ? data.items : [...items.value, ...data.items]
    selectedIds.value = new Set([
      ...(reset ? [] : selectedIds.value),
      ...data.items.map(item => item.id),
    ])
    nextCursor.value = data.next_cursor
    hasMore.value = data.has_more
  } catch (e: any) {
    error.value = e?.message || '加载缺失文件失败'
  } finally {
    loading.value = false
  }
}

async function refresh() {
  if (deleting.value) return
  selectedIds.value = new Set()
  nextCursor.value = null
  hasMore.value = false
  await fetchItems(true)
}

async function loadMore() {
  await fetchItems(false)
}

async function deleteSelected() {
  const ids = [...selectedIds.value]
  if (!ids.length || deleting.value) return

  const accepted = await confirm({
    title: '删除缺失媒体',
    message: `将永久删除 ${ids.length} 条已勾选的逻辑 Media 及其关联数据。此操作不可恢复。`,
    confirmText: '删除全部',
    danger: true,
  })
  if (!accepted) return

  deleting.value = true
  try {
    const results = await Promise.allSettled(
      ids.map(id => api.del(`/media/${id}`, { delete_source: false })),
    )
    const deletedIds = new Set(
      ids.filter((_, index) => results[index].status === 'fulfilled'),
    )
    const failedCount = ids.length - deletedIds.size

    items.value = items.value.filter(item => !deletedIds.has(item.id))
    selectedIds.value = new Set(ids.filter(id => !deletedIds.has(id)))

    if (!failedCount) toast.success(`已删除 ${deletedIds.size} 条媒体`)
    else if (!deletedIds.size) toast.error(`${failedCount} 条媒体删除失败`)
    else toast.error(`已删除 ${deletedIds.size} 条，${failedCount} 条删除失败`)
  } finally {
    deleting.value = false
  }
}

onMounted(refresh)
</script>
