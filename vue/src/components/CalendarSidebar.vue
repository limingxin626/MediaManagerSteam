<template>
  <div class="calendar-sidebar">
    <h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">日历</h3>
    <VCalendar
  :attributes="calendarAttributes"
  :is-dark="true"
  borderless
  transparent
  expanded
  title-position="left"
  @dayclick="onDayClick"
/>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { Calendar as VCalendar } from 'v-calendar'
import 'v-calendar/style.css'
import { api } from '../composables/useApi'
import type { MessageDateCount } from '../types'

const props = defineProps<{
  activeFilters?: {
    queryText?: string | null
    mediaId?: number | null
  }
}>()

const emit = defineEmits<{
  'date-selected': [date: string]
}>()

const dateCounts = ref<MessageDateCount[]>([])
const currentYear = ref(new Date().getFullYear())
const currentMonth = ref(new Date().getMonth() + 1)

const calendarAttributes = computed(() => {
  const attrs: any[] = []

  for (const d of dateCounts.value) {
    attrs.push({
      key: d.date,
      dot: { color: 'indigo' },
      dates: new Date(d.date + 'T00:00:00'),
      popover: { label: `${d.count} 条消息` },
    })
  }

  // Highlight today
  attrs.push({
    key: 'today',
    highlight: {
      color: 'gray',
      fillMode: 'light',
    },
    dates: new Date(),
  })

  return attrs
})

const fetchDates = async () => {
  console.log('fetchDates called with:', currentYear.value, currentMonth.value)
  try {
    const data = await api.get<{ dates: MessageDateCount[] }>('/messages/dates', {
      year: currentYear.value,
      month: currentMonth.value,
      query_text: props.activeFilters?.queryText || undefined,
      media_id: props.activeFilters?.mediaId ?? undefined,
    })
    dateCounts.value = data.dates
  } catch {
    dateCounts.value = []
  }
}

const onDayClick = (day: any) => {
  const dateStr = day.id // v-calendar day.id is "YYYY-MM-DD"
  const hasMessages = dateCounts.value.some(d => d.date === dateStr)
  if (hasMessages) {
    emit('date-selected', dateStr)
  }
}

onMounted(() => {
  fetchDates()
})
</script>

<style scoped>
.calendar-sidebar :deep(.vc-container) {
  --vc-bg: transparent;
  font-family: inherit;
}

.calendar-sidebar :deep(.vc-header) {
  padding: 8px 0;
}

.calendar-sidebar :deep(.vc-title) {
  font-size: 0.875rem;
  font-weight: 600;
}

/* Dark mode overrides - always active */
.calendar-sidebar :deep(.vc-container) {
  --vc-text-color: var(--color-gray-100);
  --vc-bg: transparent;
}
</style>
