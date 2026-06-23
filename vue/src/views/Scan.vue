<template>
  <div class="h-screen flex flex-col">
    <!-- 工具栏 -->
    <div class="shrink-0 border-b border-[var(--border-color)] px-4 py-3 flex items-center gap-3 flex-wrap">
      <h1 class="text-lg font-semibold text-gray-900 dark:text-white mr-2">磁盘扫描</h1>

      <FilterSelect v-model="sort" :options="sortOptions" />
      <FilterSelect v-model="order" :options="orderOptions" />
      <FilterSelect v-model="type" :options="typeOptions" />
      <FilterSelect v-if="repoOptions.length > 1" v-model="repoId" :options="repoOptions" />

      <button
        @click="refresh"
        :disabled="scanning"
        class="flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm bg-[var(--color-primary-600)] text-white hover:opacity-90 transition disabled:opacity-50"
        title="重新扫描磁盘"
      >
        <svg class="w-4 h-4" :class="{ 'animate-spin': scanning }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        {{ scanning ? '扫描中…' : '刷新' }}
      </button>

      <span v-if="status" class="text-xs text-gray-500 dark:text-gray-400 ml-auto">
        {{ status.done }}/{{ status.total }}
        <span v-if="status.pending"> · {{ status.pending }} 处理中</span>
        <span v-if="status.failed" class="text-red-400"> · {{ status.failed }} 失败</span>
      </span>
    </div>

    <!-- grid -->
    <div class="flex-1 overflow-y-auto p-3">
      <div v-if="items.length === 0 && !loading" class="text-center text-gray-400 py-20 text-sm">
        没有扫描到媒体文件。点击「刷新」扫描注册目录。
      </div>
      <div class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8 gap-1.5">
        <ScanCell
          v-for="(it, idx) in items"
          :key="it.id"
          :item="it"
          @open="openPreview(idx)"
        />
      </div>
      <div ref="sentinel" class="h-10"></div>
      <div v-if="loading" class="text-center text-gray-400 py-4 text-sm">加载中…</div>
    </div>

    <!-- 全屏预览(复用 MediaPreview 的精简模式) -->
    <MediaPreview
      :is-open="previewOpen"
      :items="(items as unknown as MessageMediaItem[])"
      :start-index="previewStartIndex"
      minimal
      @close="previewOpen = false"
      @navigate-next="loadMoreForPreview"
      @info="(it) => (detailItem = it as unknown as FsEntry)"
    />

    <ScanDetailModal :item="detailItem" @close="detailItem = null" />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import FilterSelect from '../components/FilterSelect.vue'
import ScanCell from '../components/ScanCell.vue'
import ScanDetailModal from '../components/ScanDetailModal.vue'
import MediaPreview from '../components/MediaPreview.vue'
import { api, useInfiniteScroll } from '../composables/useApi'
import { useToast } from '../composables/useToast'
import type { FsEntry, ScanStatus, CursorResponse, MessageMediaItem } from '../types'

defineOptions({ name: 'Scan' })

const toast = useToast()

const sort = ref('mtime')
const order = ref('desc')
const type = ref('')
const repoId = ref('')

const sortOptions = [
  { value: 'mtime', label: '修改时间' },
  { value: 'size', label: '大小' },
  { value: 'name', label: '名称' },
]
const orderOptions = [
  { value: 'desc', label: '降序' },
  { value: 'asc', label: '升序' },
]
const typeOptions = [
  { value: '', label: '全部' },
  { value: 'video', label: '视频' },
  { value: 'image', label: '图片' },
]
const repoOptions = ref<{ value: string; label: string }[]>([{ value: '', label: '全部仓库' }])

const sentinel = ref<HTMLElement | null>(null)
const detailItem = ref<FsEntry | null>(null)
const status = ref<ScanStatus | null>(null)
const scanning = ref(false)

// 全屏预览状态(MediaPreview 直接复用 items 数组,索引即可)
const previewOpen = ref(false)
const previewStartIndex = ref(0)

const { items, loading, hasMore, load, reset, setupObserver } = useInfiniteScroll<FsEntry>({
  sentinel,
  limit: 60,
  rootMargin: '300px',
  fetchFn: ({ cursor, limit }) =>
    api.get<CursorResponse<FsEntry>>('/scan', {
      sort: sort.value,
      order: order.value,
      type: type.value || undefined,
      repo_id: repoId.value || undefined,
      cursor: cursor || undefined,
      limit,
    }),
})

function openPreview(idx: number) {
  previewStartIndex.value = idx
  previewOpen.value = true
}

// 预览翻到已加载列表末尾时,追加下一页;MediaPreview 监听 items 增长后即可继续 next。
async function loadMoreForPreview() {
  if (loading.value || !hasMore.value) return
  await load()
}

watch([sort, order, type, repoId], () => reset())

let pollTimer: number | undefined
async function pollStatus() {
  try {
    status.value = await api.get<ScanStatus>('/scan/status')
  } catch { /* ignore */ }
  clearTimeout(pollTimer)
  // 还有 pending(worker 在补缩略图/metadata)→ 3s 后刷新 grid + 再轮询
  if ((status.value?.pending ?? 0) > 0 || status.value?.running) {
    pollTimer = window.setTimeout(() => {
      reset()
      pollStatus()
    }, 3000)
  }
}

async function refresh() {
  scanning.value = true
  try {
    await api.post('/scan/rescan')
    await reset()
    pollStatus()
  } catch (e: any) {
    toast.error(e?.message || '扫描失败')
  } finally {
    scanning.value = false
  }
}

onMounted(async () => {
  try {
    const repos = await api.get<{ repo_id: string }[]>('/scan/repos')
    repoOptions.value = [
      { value: '', label: '全部仓库' },
      ...repos.map((r) => ({ value: r.repo_id, label: r.repo_id })),
    ]
  } catch { /* ignore */ }
  setupObserver()
  reset()
  pollStatus()
})

onUnmounted(() => clearTimeout(pollTimer))
</script>
