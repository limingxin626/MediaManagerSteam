<template>
  <section class="bg-white/30 dark:bg-black/20 backdrop-blur rounded-2xl p-4 border border-[var(--border-color)]">
    <div class="flex items-center justify-between mb-3">
      <h2 class="text-base font-bold text-gray-900 dark:text-white">📊 活跃概览</h2>
      <span v-if="!loading" class="text-xs text-gray-500 dark:text-gray-400">
        过去一年共 {{ totalCount }} 条消息
      </span>
    </div>
    <div v-if="loading" class="text-center py-6 text-gray-500 text-sm">加载中…</div>
    <template v-else>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
        <Stat label="消息总数" :value="stats.message_count" />
        <Stat label="媒体总数" :value="stats.media_count" />
        <Stat label="本月新增媒体" :value="stats.media_this_month" />
        <Stat label="进行中 Todo" :value="stats.todo_doing_count" />
      </div>
      <div class="overflow-x-auto">
      <div class="inline-flex gap-[3px]">
        <!-- 周标签列 -->
        <div class="flex flex-col gap-[3px] pr-1 text-[10px] text-gray-500 dark:text-gray-400 select-none">
          <div class="h-[11px]"></div>
          <div class="h-[11px] leading-[11px]">一</div>
          <div class="h-[11px]"></div>
          <div class="h-[11px] leading-[11px]">三</div>
          <div class="h-[11px]"></div>
          <div class="h-[11px] leading-[11px]">五</div>
          <div class="h-[11px]"></div>
        </div>
        <!-- 周列 -->
        <div class="flex flex-col">
          <!-- 月份标签 -->
          <div class="flex gap-[3px] mb-1 text-[10px] text-gray-500 dark:text-gray-400 select-none h-[12px]">
            <div
              v-for="(label, i) in monthLabels"
              :key="i"
              class="w-[11px]"
              :style="label ? `min-width:11px` : ''"
            >
              <span v-if="label" class="whitespace-nowrap">{{ label }}</span>
            </div>
          </div>
          <div class="flex gap-[3px]">
            <div v-for="(week, wi) in weeks" :key="wi" class="flex flex-col gap-[3px]">
              <div
                v-for="(cell, di) in week"
                :key="di"
                :class="[
                  'w-[11px] h-[11px] rounded-[2px]',
                  cell ? levelClass(cell.count) : 'bg-transparent',
                ]"
                :title="cell ? `${cell.date}：${cell.count} 条` : ''"
              ></div>
            </div>
          </div>
        </div>
      </div>
      <!-- 图例 -->
      <div class="flex items-center justify-end gap-1 mt-2 text-[10px] text-gray-500 dark:text-gray-400">
        <span>少</span>
        <div class="w-[11px] h-[11px] rounded-[2px]" :class="levelClass(0)"></div>
        <div class="w-[11px] h-[11px] rounded-[2px]" :class="levelClass(1)"></div>
        <div class="w-[11px] h-[11px] rounded-[2px]" :class="levelClass(3)"></div>
        <div class="w-[11px] h-[11px] rounded-[2px]" :class="levelClass(6)"></div>
        <div class="w-[11px] h-[11px] rounded-[2px]" :class="levelClass(10)"></div>
        <span>多</span>
      </div>
    </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, h, onMounted, ref, defineComponent } from 'vue'
import { api } from '../../composables/useApi'
import { useToast } from '../../composables/useToast'
import type { DashboardStats } from '../../types'

interface HeatmapDay { date: string; count: number }
interface HeatmapResponse { start_date: string; end_date: string; days: HeatmapDay[] }

const Stat = defineComponent({
  props: { label: { type: String, required: true }, value: { type: Number, required: true } },
  setup(props) {
    return () =>
      h('div', { class: 'rounded-lg border border-[var(--border-color)] bg-white/50 dark:bg-gray-800/50 p-3' }, [
        h('div', { class: 'text-2xl font-bold text-gray-900 dark:text-white' }, String(props.value)),
        h('div', { class: 'text-xs text-gray-500 dark:text-gray-400 mt-1' }, props.label),
      ])
  },
})

const toast = useToast()
const loading = ref(true)
const days = ref<HeatmapDay[]>([])
const stats = ref<DashboardStats>({
  message_count: 0,
  media_count: 0,
  media_this_month: 0,
  todo_doing_count: 0,
})

const totalCount = computed(() => days.value.reduce((s, d) => s + d.count, 0))

// 按周分列（周日为列首）
const weeks = computed<(HeatmapDay | null)[][]>(() => {
  if (!days.value.length) return []
  const first = new Date(days.value[0].date + 'T00:00:00')
  const padStart = first.getDay() // 0=周日
  const cells: (HeatmapDay | null)[] = Array(padStart).fill(null).concat(days.value)
  const result: (HeatmapDay | null)[][] = []
  for (let i = 0; i < cells.length; i += 7) {
    const week = cells.slice(i, i + 7)
    while (week.length < 7) week.push(null)
    result.push(week)
  }
  return result
})

const monthLabels = computed<string[]>(() => {
  return weeks.value.map(week => {
    const firstDay = week.find(c => c) as HeatmapDay | undefined
    if (!firstDay) return ''
    const d = new Date(firstDay.date + 'T00:00:00')
    return d.getDate() <= 7 ? `${d.getMonth() + 1}月` : ''
  })
})

const levelClass = (count: number) => {
  if (count === 0) return 'bg-gray-200/60 dark:bg-gray-700/40'
  if (count <= 2) return 'bg-purple-200 dark:bg-purple-900'
  if (count <= 5) return 'bg-purple-400 dark:bg-purple-700'
  if (count <= 9) return 'bg-purple-500 dark:bg-purple-500'
  return 'bg-purple-600 dark:bg-purple-300'
}

onMounted(async () => {
  try {
    const [heatmap, statsData] = await Promise.all([
      api.get<HeatmapResponse>('/api/dashboard/heatmap'),
      api.get<DashboardStats>('/api/dashboard/stats'),
    ])
    days.value = heatmap.days
    stats.value = statsData
  } catch (e) {
    toast.error(`加载活跃概览失败：${(e as Error).message}`)
  } finally {
    loading.value = false
  }
})
</script>
