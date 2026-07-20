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
        <template v-for="row in rows" :key="row.kind === 'folder' ? row.key : `m:${row.item.id}`">
          <!-- 名称排序时的文件夹分隔行(占满整行) -->
          <div
            v-if="row.kind === 'folder'"
            class="col-span-full flex items-center gap-1.5 px-1 pt-3 pb-1 text-xs font-medium text-gray-500 dark:text-gray-400 truncate"
          >
            <svg class="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7a2 2 0 012-2h4l2 2h8a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V7z" />
            </svg>
            <span class="truncate">{{ row.dir || '(根目录)' }}</span>
            <span class="shrink-0 text-gray-400 dark:text-gray-500">· {{ row.count }}</span>
          </div>
          <ScanCell
            v-else
            :item="row.item"
            @open="openPreview(row.idx)"
          />
        </template>
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
      @delete="(it) => deleteEntry(it as unknown as FsEntry)"
    />

    <ScanDetailModal :item="detailItem" @close="detailItem = null" />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, computed } from 'vue'
import FilterSelect from '../components/FilterSelect.vue'
import ScanCell from '../components/ScanCell.vue'
import ScanDetailModal from '../components/ScanDetailModal.vue'
import MediaPreview from '../components/MediaPreview.vue'
import { api, useInfiniteScroll } from '../composables/useApi'
import { useToast } from '../composables/useToast'
import { dirname } from '../utils/media'
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
  { value: 'folder_count', label: '文件夹数量' },
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

const { items, loading, hasMore, load, reset, setupObserver, seedItems } = useInfiniteScroll<FsEntry>({
  sentinel,
  limit: 60,
  rootMargin: '300px',
  fetchFn: ({ cursor, limit }) =>
    api.get<CursorResponse<FsEntry>>('/scan', {
      // folder_count 是纯前端排序,后端不认;此模式走 loadByFolderCount 全量加载,不经此 fetchFn
      sort: sort.value,
      order: order.value,
      type: type.value || undefined,
      repo_id: repoId.value || undefined,
      cursor: cursor || undefined,
      limit,
    }),
})

// folder_count 模式:后端不支持该排序键。以 name 序全量拉取(同文件夹天然连续),
// 前端按「文件夹内 media 数」对文件夹分组重排,再 seed 回列表。放弃无限滚动(库不大时可接受)。
async function loadByFolderCount() {
  if (loading.value) return
  loading.value = true
  // 先清空:避免 await 期间 rows 用「旧排序的 items」按分组布局渲染,切出错误/重复的文件夹分隔行
  seedItems([], null, false)
  try {
    const all: FsEntry[] = []
    let cursor: string | null = null
    // 以 name 升序全量翻页,拿到所有条目
    do {
      const data: CursorResponse<FsEntry> = await api.get<CursorResponse<FsEntry>>('/scan', {
        sort: 'name',
        order: 'asc',
        type: type.value || undefined,
        repo_id: repoId.value || undefined,
        cursor: cursor || undefined,
        limit: 200,
      })
      all.push(...data.items)
      cursor = data.has_more ? data.next_cursor : null
    } while (cursor)

    // 按目录分组,组内保持 name 升序
    const groups = new Map<string, FsEntry[]>()
    for (const it of all) {
      const dir = dirname(it.rel_path)
      const g = groups.get(dir)
      if (g) g.push(it)
      else groups.set(dir, [it])
    }
    // 文件夹按 media 数排序;desc = 多的在前。数量相同按目录名稳定排序
    const dirs = [...groups.keys()].sort((a, b) => {
      const d = (groups.get(b)!.length - groups.get(a)!.length)
      const signed = order.value === 'desc' ? d : -d
      return signed !== 0 ? signed : a.localeCompare(b)
    })
    const ordered = dirs.flatMap((d) => groups.get(d)!)
    seedItems(ordered, null, false)  // 无 cursor、无更多:一次性全量
  } finally {
    loading.value = false
  }
}

function openPreview(idx: number) {
  previewStartIndex.value = idx
  previewOpen.value = true
}

// 渲染行:按名称 / 文件夹数量排序时,于每个文件夹的第一条前插入分隔行。
// item 行携带其在 items 中的原始索引,供 openPreview / MediaPreview 使用。
type Row =
  | { kind: 'folder'; dir: string; count: number; key: string }
  | { kind: 'item'; item: FsEntry; idx: number }

const groupByFolder = computed(() => sort.value === 'name' || sort.value === 'folder_count')

const rows = computed<Row[]>(() => {
  if (!groupByFolder.value) {
    return items.value.map((item, idx) => ({ kind: 'item', item, idx }))
  }
  const out: Row[] = []
  let header: { kind: 'folder'; dir: string; count: number; key: string } | null = null
  let lastDir: string | null = null
  items.value.forEach((item, idx) => {
    const dir = dirname(item.rel_path)
    if (dir !== lastDir) {
      // key 用首个成员的 id,保证唯一(dir 字符串可能因数据未连续而重复出现)
      header = { kind: 'folder', dir, count: 0, key: `d:${item.id}` }
      out.push(header)
      lastDir = dir
    }
    header!.count++
    out.push({ kind: 'item', item, idx })
  })
  return out
})

// 预览翻到已加载列表末尾时,追加下一页;MediaPreview 监听 items 增长后即可继续 next。
async function loadMoreForPreview() {
  if (loading.value || !hasMore.value) return
  await load()
}

// 删除一条扫描条目(连同磁盘源文件)。确认已在 MediaPreview 精简模式内完成(Del/Enter/Esc)。
// MediaPreview 监听 items 变化自动 clamp/关闭。
async function deleteEntry(it: FsEntry) {
  try {
    await api.del(`/scan/${it.id}`)
    const idx = items.value.findIndex((x) => x.id === it.id)
    if (idx !== -1) items.value.splice(idx, 1)
    if (items.value.length === 0) previewOpen.value = false
    toast.success('已删除')
  } catch (e: any) {
    toast.error(e?.message || '删除失败')
  }
}

watch([sort, order, type, repoId], () => reload())

// 统一入口:folder_count 走前端全量重排,其余走后端 keyset 分页
async function reload() {
  if (sort.value === 'folder_count') {
    await loadByFolderCount()
  } else {
    await reset()
  }
}

let pollTimer: number | undefined
async function pollStatus() {
  try {
    status.value = await api.get<ScanStatus>('/scan/status')
  } catch { /* ignore */ }
  clearTimeout(pollTimer)
  // 还有 pending(worker 在补缩略图/metadata)→ 3s 后刷新 grid + 再轮询
  if ((status.value?.pending ?? 0) > 0 || status.value?.running) {
    pollTimer = window.setTimeout(() => {
      reload()
      pollStatus()
    }, 3000)
  }
}

async function refresh() {
  scanning.value = true
  try {
    await api.post('/scan/rescan')
    await reload()
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
  reload()
  pollStatus()
})

onUnmounted(() => clearTimeout(pollTimer))
</script>
