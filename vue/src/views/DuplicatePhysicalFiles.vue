<template>
  <section>
      <div class="mb-6">
        <h2 class="text-xl font-semibold text-[var(--text-primary)]">重复文件</h2>
        <p class="mt-1 text-sm text-[var(--text-muted)]">默认勾选非当前主路径副本；删除磁盘文件后，逻辑媒体、缩略图和关联数据会保留。</p>
      </div>

      <div v-if="loading && !groups.length" class="py-20 text-center text-[var(--text-muted)]">加载中...</div>
      <div v-else-if="error" class="py-20 text-center text-red-500">{{ error }}</div>
      <div v-else-if="!groups.length" class="py-20 text-center text-[var(--text-muted)]">没有重复物理文件</div>

      <div class="space-y-4">
        <article v-for="group in groups" :key="group.media_id" class="rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] overflow-hidden">
          <div class="flex gap-4 p-4 border-b border-[var(--border-color)]">
            <img :src="resolveThumb(group)" :alt="String(group.media_id)" class="w-24 h-24 shrink-0 rounded-lg object-cover bg-gray-200 dark:bg-gray-800" />
            <div class="min-w-0 flex-1">
              <div class="font-medium text-[var(--text-primary)]">Media #{{ group.media_id }}</div>
              <div class="mt-1 text-xs text-[var(--text-muted)] truncate" :title="`${group.repo_id}/${group.file_path}`">{{ group.repo_id }}/{{ group.file_path }}</div>
              <div class="mt-2 text-sm text-[var(--text-secondary)]">{{ group.files.length }} 个物理文件</div>
            </div>
          </div>

          <div class="divide-y divide-[var(--border-color)]">
            <label v-for="file in group.files" :key="file.id" class="flex items-start gap-3 px-4 py-3 hover:bg-[var(--bg-secondary)] cursor-pointer">
              <input type="checkbox" class="mt-1" :checked="isSelected(file.id)" :disabled="deleting" @change="toggleFile(file.id)" />
              <div class="min-w-0 flex-1">
                <div class="flex items-center gap-2">
                  <span class="text-sm text-[var(--text-primary)] break-all">{{ file.repo_id }}/{{ file.rel_path }}</span>
                  <span v-if="file.is_canonical" class="shrink-0 px-2 py-0.5 rounded-full text-xs bg-amber-500/15 text-amber-600 dark:text-amber-300">当前主路径</span>
                </div>
                <div class="mt-1 text-xs text-[var(--text-muted)]">{{ formatSize(file.file_size) }} · {{ formatMtime(file.mtime) }}</div>
              </div>
            </label>
          </div>

          <div class="px-4 py-3 flex justify-between bg-[var(--bg-secondary)]">
            <button @click="selectAll(group)" class="text-sm text-[var(--color-primary-600)] hover:underline">{{ allSelected(group) ? '取消全选' : '全选本组' }}</button>
            <span class="text-xs text-[var(--text-muted)]">允许删除全部副本；逻辑 Media 会继续保留</span>
          </div>
        </article>
      </div>

      <div v-if="hasMore" class="pt-6 pb-24 text-center">
        <button @click="loadMore" :disabled="loading || deleting" class="px-4 py-2 rounded-lg bg-[var(--color-primary-600)] text-white disabled:opacity-50">{{ loading ? '加载中...' : '加载更多' }}</button>
      </div>
      <div v-else class="h-20"></div>

      <div class="fixed z-40 bottom-20 md:bottom-6 left-4 right-4 md:left-20 pointer-events-none">
        <div class="max-w-7xl mx-auto flex justify-end">
          <button
            @click="deleteSelected"
            :disabled="!selectedIds.size || deleting"
            class="pointer-events-auto px-5 py-3 text-sm font-medium rounded-xl bg-red-600 text-white shadow-lg hover:bg-red-700 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {{ deleting ? '删除中...' : `删除所选 (${selectedIds.size})` }}
          </button>
        </div>
      </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api } from '../composables/useApi'
import { useConfirm } from '../composables/useConfirm'
import { useToast } from '../composables/useToast'
import { formatMtime, formatSize, resolveThumb } from '../utils/media'

interface PhysicalFile {
  id: number
  repo_id: string
  rel_path: string
  local_file_path: string
  file_size: number | null
  mtime: number
  is_canonical: boolean
}

interface DuplicateGroup {
  media_id: number
  repo_id: string
  file_path: string
  mime_type: string | null
  width: number | null
  height: number | null
  duration_ms: number | null
  thumb_url: string
  local_thumb_path: string
  files: PhysicalFile[]
}

interface CursorResponse {
  items: DuplicateGroup[]
  next_cursor: number | null
  has_more: boolean
}

interface DeleteResponse {
  deleted_ids: number[]
  missing_ids: number[]
  failures: { id: number; message: string }[]
  remaining_count: number
}

const groups = ref<DuplicateGroup[]>([])
const selectedIds = ref(new Set<number>())
const nextCursor = ref<number | null>(null)
const hasMore = ref(false)
const loading = ref(false)
const error = ref('')
const deleting = ref(false)
const { confirm } = useConfirm()
const toast = useToast()

function isSelected(id: number) { return selectedIds.value.has(id) }
function allSelected(group: DuplicateGroup) { return group.files.every(file => isSelected(file.id)) }

function toggleFile(id: number) {
  if (deleting.value) return
  const next = new Set(selectedIds.value)
  next.has(id) ? next.delete(id) : next.add(id)
  selectedIds.value = next
}

function selectAll(group: DuplicateGroup) {
  if (deleting.value) return
  const next = new Set(selectedIds.value)
  const shouldClear = allSelected(group)
  for (const file of group.files) shouldClear ? next.delete(file.id) : next.add(file.id)
  selectedIds.value = next
}

async function fetchGroups(reset = false, allowDuringDelete = false) {
  if (loading.value || (deleting.value && !allowDuringDelete)) return
  loading.value = true
  error.value = ''
  try {
    const data = await api.get<CursorResponse>('/repositories/duplicate-files', {
      cursor: reset ? undefined : nextCursor.value,
      limit: 20,
    })
    groups.value = reset ? data.items : [...groups.value, ...data.items]
    selectedIds.value = new Set([
      ...(reset ? [] : selectedIds.value),
      ...data.items.flatMap(group => group.files.filter(file => !file.is_canonical).map(file => file.id)),
    ])
    nextCursor.value = data.next_cursor
    hasMore.value = data.has_more
  } catch (e: any) {
    error.value = e?.message || '加载重复文件失败'
  } finally {
    loading.value = false
  }
}

async function loadMore() { await fetchGroups(false) }

async function deleteSelected() {
  const selections = groups.value
    .map(group => ({
      group,
      files: group.files.filter(file => isSelected(file.id)),
    }))
    .filter(selection => selection.files.length)
  if (!selections.length || deleting.value) return

  const selected = selections.flatMap(selection => selection.files)
  const size = selected.reduce((sum, file) => sum + (file.file_size || 0), 0)
  const includesCanonical = selected.some(file => file.is_canonical)
  const deletesWholeGroup = selections.some(({ group, files }) => files.length === group.files.length)
  const warning = deletesWholeGroup
    ? '其中有媒体会失去全部物理文件，之后原文件将不可访问。'
    : includesCanonical
      ? '其中包含当前主路径，删除后会自动切换到剩余副本。'
      : ''
  const accepted = await confirm({
    title: '删除所选物理文件',
    message: `将永久删除 ${selected.length} 个文件（${formatSize(size)}）。${warning} 逻辑 Media、缩略图和关联数据仍会保留。`,
    confirmText: '永久删除',
    danger: true,
  })
  if (!accepted) return

  deleting.value = true
  try {
    const results = await Promise.allSettled(
      selections.map(({ group, files }) =>
        api.delWithBody<DeleteResponse>(`/repositories/duplicate-files/${group.media_id}`, {
          repository_file_ids: files.map(file => file.id),
        }),
      ),
    )
    const processedIds = new Set<number>()
    const failedIds = new Set<number>()
    results.forEach((result, index) => {
      if (result.status === 'rejected') {
        for (const file of selections[index].files) failedIds.add(file.id)
        return
      }
      for (const id of [...result.value.deleted_ids, ...result.value.missing_ids]) processedIds.add(id)
      for (const failure of result.value.failures) failedIds.add(failure.id)
    })

    nextCursor.value = null
    hasMore.value = false
    await fetchGroups(true, true)
    selectedIds.value = failedIds

    if (!failedIds.size) toast.success(`已删除 ${processedIds.size} 个物理文件`)
    else if (!processedIds.size) toast.error(`${failedIds.size} 个文件删除失败`)
    else toast.error(`已删除 ${processedIds.size} 个文件，${failedIds.size} 个删除失败`)
  } finally {
    deleting.value = false
  }
}

onMounted(() => fetchGroups(true))
</script>
