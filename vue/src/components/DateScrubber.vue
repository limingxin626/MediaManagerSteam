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
      <!-- Center axis line -->
      <div class="absolute right-1.5 top-0 bottom-0 w-px bg-gray-300/40 dark:bg-white/15 pointer-events-none"></div>

      <!-- Month ticks (short) -->
      <div
        v-for="tick in monthTicks"
        :key="`m-${tick.year}-${tick.month}`"
        class="absolute right-1.5 h-px w-1.5 bg-gray-400/50 dark:bg-white/30 pointer-events-none"
        :style="{ top: tick.top + '%' }"
      ></div>

      <!-- Year ticks (long) -->
      <div
        v-for="tick in yearTicks"
        :key="`y-${tick.year}`"
        class="absolute right-1.5 h-px w-3 bg-gray-500 dark:bg-white/70 pointer-events-none"
        :style="{ top: tick.top + '%' }"
      ></div>

      <!-- Year labels -->
      <div
        v-for="label in yearLabels"
        :key="label.year"
        class="absolute right-5 text-[10px] font-medium text-gray-500 dark:text-gray-400 pointer-events-none leading-none whitespace-nowrap"
        :style="{ top: label.top + '%', transform: `translateY(${label.anchor})` }"
      >{{ label.year }}</div>

      <!-- Current position indicator -->
      <div
        class="absolute right-0 w-3 h-0.5 bg-[var(--color-primary-500)] rounded-sm pointer-events-none transition-[top] duration-150 shadow"
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

// Month ticks — one per month present in timeline
const monthTicks = computed(() => {
  if (!props.timeline.length || totalRange.value <= 0) return []
  return props.timeline.map(t => ({
    year: t.year,
    month: t.month,
    top: dateToPercent(new Date(t.year, t.month - 1, 15)),
  }))
})

// Year ticks — at Jan 1 of each year spanned by the range
const yearTicks = computed(() => {
  if (!props.timeline.length || totalRange.value <= 0) return []
  const minY = props.minDate.getFullYear()
  const maxY = props.maxDate.getFullYear()
  const ticks: { year: number; top: number }[] = []
  for (let y = minY; y <= maxY; y++) {
    const d = new Date(y, 0, 1)
    if (d < props.minDate || d > props.maxDate) continue
    ticks.push({ year: y, top: dateToPercent(d) })
  }
  return ticks
})

// Year labels — positioned at year tick (Jan 1)
const yearLabels = computed(() => {
  if (!props.timeline.length || totalRange.value <= 0) return []
  const minY = props.minDate.getFullYear()
  const maxY = props.maxDate.getFullYear()
  const labels: { year: number; top: number; anchor: string }[] = []
  for (let y = minY; y <= maxY; y++) {
    const anchor = new Date(y, 0, 1)
    const clamped = anchor < props.minDate ? props.minDate : anchor > props.maxDate ? props.maxDate : anchor
    const top = Math.max(0, Math.min(100, dateToPercent(clamped)))
    let translate = '-50%'
    if (top > 92) translate = '-100%'
    else if (top < 8) translate = '0%'
    labels.push({ year: y, top, anchor: translate })
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
  background: transparent;
}
.date-scrubber:hover,
.date-scrubber.dragging {
  background: linear-gradient(to bottom, rgba(0,0,0,0.04), rgba(0,0,0,0.08));
}
</style>
