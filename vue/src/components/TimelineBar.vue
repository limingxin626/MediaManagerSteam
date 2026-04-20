<template>
  <div class="timeline-bar fixed right-1 top-1/2 -translate-y-1/2 z-30 flex flex-col items-center select-none max-h-[70vh] rounded-lg bg-black/30 backdrop-blur-sm py-2"
    :class="compact ? 'w-6' : 'w-12'"
  >
    <div class="flex-1 overflow-y-auto scrollbar-none w-full">
      <div
        v-for="item in timeline"
        :key="`${item.year}-${item.month}`"
        class="flex flex-col items-center cursor-pointer py-0.5 transition-colors hover:bg-white/10"
        :class="isActive(item) ? 'text-[var(--color-primary-400)] font-bold' : 'text-gray-400 dark:text-gray-500'"
        @click="$emit('jump', item)"
      >
        <template v-if="compact">
          <span v-if="isFirstOfYear(item)" class="text-[9px] leading-tight">{{ item.year }}</span>
          <span class="text-[10px] leading-tight">{{ item.month }}</span>
        </template>
        <template v-else>
          <span v-if="isFirstOfYear(item)" class="text-[10px] leading-tight mb-0.5 text-gray-500">{{ item.year }}</span>
          <span class="text-xs leading-tight">{{ item.month }}月</span>
          <span class="text-[9px] leading-tight text-gray-500">{{ item.count }}</span>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

export interface TimelineEntry {
  year: number
  month: number
  count: number
}

const props = defineProps<{
  timeline: TimelineEntry[]
  currentYear: number
  currentMonth: number
  compact?: boolean
}>()

defineEmits<{
  jump: [item: TimelineEntry]
}>()

const isActive = (item: TimelineEntry) =>
  item.year === props.currentYear && item.month === props.currentMonth

const isFirstOfYear = (item: TimelineEntry) => {
  const idx = props.timeline.indexOf(item)
  return idx === 0 || props.timeline[idx - 1].year !== item.year
}
</script>

<style scoped>
.scrollbar-none::-webkit-scrollbar { display: none; }
.scrollbar-none { scrollbar-width: none; }
</style>
