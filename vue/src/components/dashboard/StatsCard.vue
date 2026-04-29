<template>
  <section class="bg-white/30 dark:bg-black/20 backdrop-blur rounded-2xl p-4 border border-[var(--border-color)]">
    <h2 class="text-base font-bold text-gray-900 dark:text-white mb-3">📊 统计</h2>
    <div v-if="loading" class="text-center py-4 text-gray-500 text-sm">加载中…</div>
    <div v-else class="grid grid-cols-2 gap-3">
      <Stat label="消息总数" :value="stats.message_count" />
      <Stat label="媒体总数" :value="stats.media_count" />
      <Stat label="本月新增媒体" :value="stats.media_this_month" />
      <Stat label="进行中 Todo" :value="stats.todo_doing_count" />
    </div>
  </section>
</template>

<script setup lang="ts">
import { h, onMounted, ref, defineComponent } from 'vue'
import { api } from '../../composables/useApi'
import { useToast } from '../../composables/useToast'
import type { DashboardStats } from '../../types'

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
const stats = ref<DashboardStats>({
  message_count: 0,
  media_count: 0,
  media_this_month: 0,
  todo_doing_count: 0,
})

onMounted(async () => {
  try {
    stats.value = await api.get<DashboardStats>('/api/dashboard/stats')
  } catch (e) {
    toast.error(`加载统计失败：${(e as Error).message}`)
  } finally {
    loading.value = false
  }
})
</script>
