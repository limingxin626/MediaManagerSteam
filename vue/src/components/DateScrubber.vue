<template>
  <div
    ref="barRef"
    class="date-scrubber absolute right-0 top-0 bottom-0 z-30 flex items-stretch select-none"
    :class="dragging ? 'w-8' : 'w-5 hover:w-8'"
    @mousedown.prevent="onPointerDown"
    @touchstart.prevent="onTouchStart"
    @mouseenter="hovering = true"
    @mouseleave="onMouseLeave"
    @mousemove="onHoverMove"
  >
    <!-- Track background -->
    <div class="relative flex-1">
      <!-- Density bars -->
      <div
        v-for="seg in segments"
        :key="`${seg.year}-${seg.month}`"
        class="absolute left-0 right-0"
        :style="{ top: seg.top + '%', height: seg.height + '%' }"
      >
        <div class="h-full w-full rounded-sm" :style="{ backgroundColor: `rgba(139, 92, 246, ${seg.opacity})` }"></div>
      </div>

      <!-- Year labels -->
      <div
        v-for="label in yearLabels"
        :key="label.year"
        class="absolute right-1 text-[9px] text-gray-400 pointer-events-none leading-none"
        :style="{ top: label.top + '%', transform: 'translateY(-50%)' }"
      >{{ label.year }}</div>

      <!-- Current position indicator -->
      <div
        class="absolute left-0 right-0 h-0.5 bg-white rounded pointer-events-none transition-[top] duration-150"
        :style="{ top: indicatorTop + '%' }"
      ></div>
    </div>

    <!-- Tooltip -->
    <div
      v-if="(hovering || dragging) && tooltipDate"
      class="absolute right-full mr-2 px-2 py-1 rounded bg-black/80 text-white text-xs whitespace-nowrap pointer-events-none"
      :style="{ top: tooltipY + 'px', transform: 'translateY(-50%)' }"
    >{{ tooltipLabel }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue'

export interface TimelineEntry {
  year: number
  month: number
  count: number
}

const props = defineProps<{
  timeline: TimelineEntry[]
  minDate: Date
  maxDate: Date
  currentDate: Date
}>()

const emit = defineEmits<{
  jump: [date: Date]
}>()

const barRef = ref<HTMLElement | null>(null)
const dragging = ref(false)
const hovering = ref(false)
const tooltipY = ref(0)
const tooltipDate = ref<Date | null>(null)

const totalRange = computed(() => props.maxDate.getTime() - props.minDate.getTime())

function dateToPercent(d: Date): number {
  if (totalRange.value <= 0) return 0
  return ((props.maxDate.getTime() - d.getTime()) / totalRange.value) * 100
}

function percentToDate(pct: number): Date {
  const t = props.maxDate.getTime() - (pct / 100) * totalRange.value
  return new Date(t)
}

function yToPercent(y: number): number {
  const bar = barRef.value
  if (!bar) return 0
  const rect = bar.getBoundingClientRect()
  return Math.max(0, Math.min(100, ((y - rect.top) / rect.height) * 100))
}

const indicatorTop = computed(() => dateToPercent(props.currentDate))

const tooltipLabel = computed(() => {
  if (!tooltipDate.value) return ''
  const d = tooltipDate.value
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日`
})

// Density segments
const segments = computed(() => {
  if (!props.timeline.length || totalRange.value <= 0) return []
  const maxCount = Math.max(...props.timeline.map(t => t.count))
  return props.timeline.map(t => {
    const start = new Date(t.year, t.month - 1, 1)
    const end = new Date(t.year, t.month, 0, 23, 59, 59)
    const top = dateToPercent(end)
    const bottom = dateToPercent(start)
    return {
      year: t.year,
      month: t.month,
      top,
      height: Math.max(bottom - top, 0.5),
      opacity: 0.15 + (t.count / maxCount) * 0.55,
    }
  })
})

// Year labels
const yearLabels = computed(() => {
  if (!props.timeline.length) return []
  const years = new Set<number>()
  const labels: { year: number; top: number }[] = []
  for (const t of props.timeline) {
    if (!years.has(t.year)) {
      years.add(t.year)
      const mid = new Date(t.year, 6, 1)
      labels.push({ year: t.year, top: Math.max(0, Math.min(100, dateToPercent(mid))) })
    }
  }
  return labels
})

function handleMove(clientY: number) {
  const pct = yToPercent(clientY)
  tooltipDate.value = percentToDate(pct)
  const bar = barRef.value
  if (bar) {
    const rect = bar.getBoundingClientRect()
    tooltipY.value = clientY - rect.top
  }
}

function handleJump(clientY: number) {
  const pct = yToPercent(clientY)
  const date = percentToDate(pct)
  emit('jump', date)
}

let lastJumpY = 0

function onPointerDown(e: MouseEvent) {
  dragging.value = true
  lastJumpY = e.clientY
  handleMove(e.clientY)
  document.addEventListener('mousemove', onDocMouseMove)
  document.addEventListener('mouseup', onDocMouseUp)
}

function onDocMouseMove(e: MouseEvent) {
  if (!dragging.value) return
  lastJumpY = e.clientY
  handleMove(e.clientY)
}

function onDocMouseUp() {
  if (dragging.value) handleJump(lastJumpY)
  dragging.value = false
  document.removeEventListener('mousemove', onDocMouseMove)
  document.removeEventListener('mouseup', onDocMouseUp)
}

function onTouchStart(e: TouchEvent) {
  dragging.value = true
  const t = e.touches[0]
  lastJumpY = t.clientY
  handleMove(t.clientY)
  document.addEventListener('touchmove', onTouchMove, { passive: false })
  document.addEventListener('touchend', onTouchEnd)
}

function onTouchMove(e: TouchEvent) {
  e.preventDefault()
  const t = e.touches[0]
  lastJumpY = t.clientY
  handleMove(t.clientY)
}

function onTouchEnd() {
  if (dragging.value) handleJump(lastJumpY)
  dragging.value = false
  document.removeEventListener('touchmove', onTouchMove)
  document.removeEventListener('touchend', onTouchEnd)
}

function onHoverMove(e: MouseEvent) {
  if (!dragging.value) handleMove(e.clientY)
}

function onMouseLeave() {
  if (!dragging.value) {
    hovering.value = false
    tooltipDate.value = null
  }
}

onUnmounted(() => {
  document.removeEventListener('mousemove', onDocMouseMove)
  document.removeEventListener('mouseup', onDocMouseUp)
  document.removeEventListener('touchmove', onTouchMove)
  document.removeEventListener('touchend', onTouchEnd)
})
</script>

<style scoped>
.date-scrubber {
  cursor: pointer;
  transition: width 0.15s ease;
  background: linear-gradient(to bottom, rgba(0,0,0,0.1), rgba(0,0,0,0.2));
  border-radius: 4px 0 0 4px;
}
</style>
