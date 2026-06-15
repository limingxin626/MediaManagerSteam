<template>
  <div class="h-screen overflow-y-auto pb-24 md:pb-8">
    <div class="max-w-7xl w-full mx-auto px-4 pt-6 space-y-4">
      <div class="flex items-center justify-between flex-wrap gap-3">
        <h1 class="text-xl font-bold text-gray-900 dark:text-white">记账</h1>

        <!-- 月份选择 -->
        <div class="flex items-center gap-2">
          <label class="text-xs text-gray-500 dark:text-gray-400">月份</label>
          <select
            v-model="selectedYM"
            class="text-sm rounded-lg border border-[var(--border-color)] bg-white/60 dark:bg-[#3d3d3d] text-gray-900 dark:text-white px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-[var(--color-primary-500)]"
          >
            <option v-for="m in months" :key="`${m.year}-${m.month}`" :value="`${m.year}-${m.month}`">
              {{ m.year }}-{{ String(m.month).padStart(2, '0') }} ({{ m.count }} 笔)
            </option>
            <option v-if="!months.length" value="">(暂无数据)</option>
          </select>
        </div>
      </div>

      <!-- 汇总卡 -->
      <section class="bg-white/30 dark:bg-[var(--bg-card)] backdrop-blur rounded-2xl p-4 border border-[var(--border-color)]">
        <div v-if="summaryLoading" class="text-center py-6 text-gray-500 text-sm">加载中…</div>
        <template v-else-if="summary">
          <div class="flex items-baseline gap-3 mb-4 flex-wrap">
            <span class="text-xs text-gray-500 dark:text-gray-400">{{ summary.year }}年{{ summary.month }}月 计入支出</span>
            <span class="text-3xl font-bold text-gray-900 dark:text-white">¥ {{ formatAmount(summary.total) }}</span>
            <span class="text-xs text-gray-500 dark:text-gray-400">{{ categorySorted.length }} 个分类</span>
          </div>

          <!-- 堆叠条 -->
          <div v-if="summary.total > 0" class="h-3 rounded-full overflow-hidden flex bg-gray-200/40 dark:bg-gray-700/40 mb-3">
            <div
              v-for="(c, i) in categorySorted"
              :key="c.name"
              :style="{ width: `${(c.amount / summary.total) * 100}%`, background: colorFor(i) }"
              :title="`${c.name}：¥${formatAmount(c.amount)}`"
              class="h-full"
            ></div>
          </div>

          <!-- 分类明细 -->
          <div v-if="categorySorted.length" class="space-y-1.5">
            <div
              v-for="(c, i) in categorySorted"
              :key="c.name"
              class="flex items-center gap-3 text-sm"
            >
              <span class="inline-block w-3 h-3 rounded shrink-0" :style="{ background: colorFor(i) }"></span>
              <span class="text-gray-700 dark:text-gray-200 flex-1 truncate">{{ c.name }}</span>
              <span class="text-xs text-gray-500 dark:text-gray-400 tabular-nums">{{ c.count }} 笔</span>
              <span class="text-gray-900 dark:text-white tabular-nums w-24 text-right">¥ {{ formatAmount(c.amount) }}</span>
              <span class="text-xs text-gray-500 dark:text-gray-400 tabular-nums w-12 text-right">{{ ((c.amount / summary.total) * 100).toFixed(1) }}%</span>
            </div>
          </div>
          <div v-else class="text-center py-6 text-gray-500 text-sm">本月无计入支出</div>
        </template>
        <div v-else class="text-center py-6 text-gray-500 text-sm">暂无数据</div>
      </section>

      <!-- 过滤栏 -->
      <div class="flex flex-wrap items-center gap-2">
        <button
          v-for="opt in directionOpts"
          :key="opt.value"
          @click="setDirection(opt.value)"
          :class="[
            'px-3 py-1 text-xs rounded-full border transition-colors',
            filterDirection === opt.value
              ? 'bg-[var(--color-primary-600)] text-white border-transparent'
              : 'bg-white/40 dark:bg-[#3d3d3d] text-gray-600 dark:text-gray-300 border-[var(--border-color)] hover:bg-gray-100 dark:hover:bg-white/10'
          ]"
        >
          {{ opt.label }}
        </button>

        <select
          v-model="filterCategory"
          @change="resetList"
          class="text-xs rounded-full border border-[var(--border-color)] bg-white/40 dark:bg-[#3d3d3d] text-gray-700 dark:text-gray-200 px-3 py-1 focus:outline-none focus:ring-2 focus:ring-[var(--color-primary-500)]"
        >
          <option value="">全部分类</option>
          <option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
        </select>

        <label class="flex items-center gap-1.5 text-xs text-gray-600 dark:text-gray-300 ml-2 cursor-pointer">
          <input type="checkbox" v-model="includeExcluded" @change="resetList" class="rounded" />
          含已排除(退款/0元)
        </label>

        <!-- 排序 -->
        <div class="ml-auto flex items-center gap-1">
          <span class="text-xs text-gray-500 dark:text-gray-400 mr-1">排序</span>
          <button
            v-for="opt in sortOpts"
            :key="opt.field"
            @click="toggleSort(opt.field)"
            :class="[
              'inline-flex items-center gap-1 px-3 py-1 text-xs rounded-full border transition-colors',
              sortField === opt.field
                ? 'bg-[var(--color-primary-600)] text-white border-transparent'
                : 'bg-white/40 dark:bg-[#3d3d3d] text-gray-600 dark:text-gray-300 border-[var(--border-color)] hover:bg-gray-100 dark:hover:bg-white/10'
            ]"
            :title="sortField === opt.field ? (sortOrder === 'desc' ? '降序,点击切升序' : '升序,点击切降序') : '点击按此排序'"
          >
            {{ opt.label }}
            <span v-if="sortField === opt.field" class="text-[10px] leading-none">
              {{ sortOrder === 'desc' ? '↓' : '↑' }}
            </span>
          </button>
        </div>
      </div>

      <!-- 流水列表 -->
      <section class="bg-white/30 dark:bg-[var(--bg-card)] backdrop-blur rounded-2xl border border-[var(--border-color)] overflow-hidden">
        <div v-if="listLoading && !items.length" class="text-center py-10 text-gray-500 text-sm">加载中…</div>
        <div v-else-if="!items.length" class="text-center py-10 text-gray-500 text-sm">无符合条件的流水</div>

        <template v-else>
          <div
            v-for="(t, idx) in items"
            :key="t.id"
            class="px-4 py-3 flex items-center gap-3 hover:bg-gray-100/40 dark:hover:bg-white/5 transition-colors"
            :class="idx > 0 ? 'border-t border-[var(--border-color)]' : ''"
          >
            <!-- 来源徽章 -->
            <span
              :class="t.source === 'alipay'
                ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300'
                : 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300'"
              class="text-[10px] px-1.5 py-0.5 rounded font-medium shrink-0"
            >
              {{ t.source === 'alipay' ? '支付宝' : '微信' }}
            </span>

            <!-- 主体 -->
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <span class="text-sm font-medium text-gray-900 dark:text-white truncate">
                  {{ t.counterparty || '(无对方)' }}
                </span>
                <span v-if="t.category" class="text-[10px] px-1.5 py-0.5 rounded bg-[var(--color-primary-500)]/15 text-[var(--color-primary-600)] dark:text-[var(--color-primary-500)] shrink-0">
                  {{ t.category }}
                </span>
              </div>
              <div class="text-xs text-gray-500 dark:text-gray-400 truncate">
                {{ t.product || t.raw_type || '—' }}
                <span class="ml-1.5">· {{ formatDateTime(t.txn_time) }}</span>
                <span v-if="t.excluded" class="ml-1.5 text-orange-500">· 不计统计</span>
              </div>
            </div>

            <!-- 金额 -->
            <span
              class="text-sm font-semibold tabular-nums shrink-0"
              :class="amountColor(t)"
            >
              {{ directionSign(t) }}{{ formatAmount(t.amount) }}
            </span>
          </div>

          <!-- 加载更多 sentinel -->
          <div ref="sentinel" class="h-1"></div>
          <div v-if="listLoading" class="text-center py-3 text-xs text-gray-500">加载中…</div>
          <div v-else-if="!hasMore" class="text-center py-3 text-xs text-gray-400">已经到底了</div>
        </template>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { api, useInfiniteScroll } from '../composables/useApi'
import { useToast } from '../composables/useToast'
import { formatDateTime } from '../utils/date'

defineOptions({ name: 'Transactions' })

interface Txn {
  id: number
  source: string
  biz_no: string
  txn_time: string
  direction: 'expense' | 'income' | 'neutral'
  amount: number
  counterparty: string | null
  product: string | null
  category: string | null
  raw_type: string | null
  raw_origin: string | null
  status: string | null
  excluded: number
}

interface MonthBucket {
  year: number
  month: number
  count: number
  total_expense: number
}

interface CategorySlot { count: number; amount: number }

interface Summary {
  year: number
  month: number
  total: number
  by_category: Record<string, CategorySlot>
}

const toast = useToast()

const months = ref<MonthBucket[]>([])
const selectedYM = ref<string>('')
const summary = ref<Summary | null>(null)
const summaryLoading = ref(false)
const categories = ref<string[]>([])

const filterDirection = ref<'' | 'expense' | 'income' | 'neutral'>('expense')
const filterCategory = ref<string>('')
const includeExcluded = ref(false)

type SortField = 'time' | 'amount'
type SortOrder = 'asc' | 'desc'
const sortField = ref<SortField>('time')
const sortOrder = ref<SortOrder>('desc')

const sortOpts: { field: SortField; label: string }[] = [
  { field: 'time', label: '时间' },
  { field: 'amount', label: '金额' },
]

const directionOpts = [
  { value: 'expense' as const, label: '支出' },
  { value: 'income' as const, label: '收入' },
  { value: '' as const, label: '全部' },
]

const sentinel = ref<HTMLElement | null>(null)

const parsedYM = computed(() => {
  if (!selectedYM.value) return { year: null as number | null, month: null as number | null }
  const [y, m] = selectedYM.value.split('-')
  return { year: Number(y), month: Number(m) }
})

const { items, loading: listLoading, hasMore, reset, setupObserver } = useInfiniteScroll<Txn>({
  fetchFn: async ({ cursor, limit }) => {
    const { year, month } = parsedYM.value
    if (year == null || month == null) {
      return { items: [], next_cursor: null, has_more: false }
    }
    return await api.get<{ items: Txn[]; next_cursor: string | null; has_more: boolean }>(
      '/transactions',
      {
        cursor: cursor || undefined,
        limit,
        year,
        month,
        direction: filterDirection.value || undefined,
        category: filterCategory.value || undefined,
        excluded: includeExcluded.value ? undefined : 0,
        sort: sortField.value,
        order: sortOrder.value,
      },
    )
  },
  sentinel,
  limit: 50,
})

const categorySorted = computed(() => {
  if (!summary.value) return []
  return Object.entries(summary.value.by_category)
    .map(([name, slot]) => ({ name, ...slot }))
    .sort((a, b) => b.amount - a.amount)
})

const palette = [
  '#a78bfa', '#60a5fa', '#34d399', '#fbbf24', '#f87171',
  '#fb923c', '#22d3ee', '#f472b6', '#a3e635', '#94a3b8',
]
const colorFor = (i: number) => palette[i % palette.length]

const formatAmount = (v: number) =>
  v.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

const directionSign = (t: Txn) => (t.direction === 'income' ? '+' : t.direction === 'expense' ? '-' : '')
const amountColor = (t: Txn) => {
  if (t.excluded) return 'text-gray-400 dark:text-gray-500 line-through'
  if (t.direction === 'income') return 'text-green-600 dark:text-green-400'
  if (t.direction === 'expense') return 'text-gray-900 dark:text-white'
  return 'text-gray-500 dark:text-gray-400'
}

const setDirection = (v: '' | 'expense' | 'income' | 'neutral') => {
  filterDirection.value = v
  resetList()
}

const toggleSort = (field: SortField) => {
  if (sortField.value === field) {
    sortOrder.value = sortOrder.value === 'desc' ? 'asc' : 'desc'
  } else {
    sortField.value = field
    sortOrder.value = field === 'time' ? 'desc' : 'desc'
  }
  resetList()
}

const resetList = () => {
  reset()
}

const fetchSummary = async () => {
  const { year, month } = parsedYM.value
  if (year == null || month == null) {
    summary.value = null
    return
  }
  summaryLoading.value = true
  try {
    summary.value = await api.get<Summary>('/transactions/summary/monthly', { year, month })
  } catch (e) {
    toast.error(`加载月度汇总失败：${(e as Error).message}`)
    summary.value = null
  } finally {
    summaryLoading.value = false
  }
}

watch(selectedYM, () => {
  fetchSummary()
  resetList()
})

onMounted(async () => {
  setupObserver()
  try {
    const [ms, cats] = await Promise.all([
      api.get<MonthBucket[]>('/transactions/months'),
      api.get<string[]>('/transactions/categories'),
    ])
    months.value = ms
    categories.value = cats
    if (ms.length && !selectedYM.value) {
      selectedYM.value = `${ms[0]!.year}-${ms[0]!.month}`
      // 触发 watch → fetchSummary + resetList
    }
  } catch (e) {
    toast.error(`加载记账数据失败：${(e as Error).message}`)
  }
})
</script>
