<template>
  <div
    ref="barRef"
    class="date-scrubber absolute right-0 top-0 bottom-0 z-30 flex select-none"
    :class="[dragging ? 'is-dragging' : '', 'w-[28px] md:w-[40px]']"
    @mousedown.prevent="onPointerDown"
    @touchstart.prevent="onTouchStart"
    @mouseenter="hovering = true"
    @mouseleave="onMouseLeave"
    @mousemove="onHoverMove"
    @wheel.passive="onWheel"
  >
    <!-- Left label column (year labels + floating month capsule) -->
    <div class="relative hidden md:block" style="width: 26px">
      <!-- Year labels -->
      <div
        v-for="label in yearLabels"
        :key="`yl-${label.year}`"
        class="absolute left-0 right-1 text-right text-[10px] font-medium text-gray-500 dark:text-gray-400 pointer-events-none leading-none whitespace-nowrap tabular-nums"
        :style="{ top: label.top + '%', transform: `translateY(${label.anchor})` }"
      >{{ label.year }}</div>

      <!-- Floating current month capsule -->
      <div
        v-if="showCapsule"
        class="scrubber-capsule absolute right-3 hidden sm:flex items-center pointer-events-none whitespace-nowrap px-2 py-0.5 rounded-full text-[11px] font-medium backdrop-blur-md bg-black/70 text-white dark:bg-white/15 dark:text-white border border-white/10 shadow"
        :style="{ top: indicatorTop + '%', transform: 'translateY(-50%)' }"
      >{{ capsuleLabel }}</div>
    </div>

    <!-- Right tick track -->
    <div class="relative flex-1">
      <!-- Center axis line -->
      <div class="absolute right-1.5 top-0 bottom-0 w-px bg-gray-300/50 dark:bg-white/15 pointer-events-none"></div>

      <!-- Month ticks (short) -->
      <div
        v-for="tick in monthTicks"
        :key="`m-${tick.year}-${tick.month}`"
        class="absolute right-1.5 h-px w-1.5 bg-gray-400/60 dark:bg-white/30 pointer-events-none"
        :style="{ top: tick.top + '%' }"
      ></div>

      <!-- Year ticks (long) -->
      <div
        v-for="tick in yearTicks"
        :key="`y-${tick.year}`"
        class="absolute right-1.5 h-px w-3 bg-gray-500 dark:bg-white/70 pointer-events-none"
        :style="{ top: tick.top + '%' }"
      ></div>

      <!-- Indicator: leader line + dot -->
      <div
        class="scrubber-leader absolute right-3 h-px w-3 bg-[var(--color-primary-500)] pointer-events-none"
        :style="{ top: `calc(${indicatorTop}% - 0.5px)` }"
      ></div>
      <div
        class="scrubber-dot absolute right-1 w-1.5 h-1.5 rounded-full bg-[var(--color-primary-500)] pointer-events-none shadow-[0_0_8px_var(--color-primary-500)]"
        :style="{ top: `calc(${indicatorTop}% - 3px)` }"
      ></div>
    </div>

    <!-- Drag/hover tooltip (frosted glass) -->
    <div
      v-if="(hovering || dragging) && tooltipDate"
      class="absolute right-full mr-2 px-2 py-1 rounded-md text-xs whitespace-nowrap pointer-events-none backdrop-blur-md bg-black/60 text-white dark:bg-black/50 border border-white/15 shadow-lg"
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
  'jump-final': [date: Date]
  wheel: [deltaY: number]
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

const showCapsule = computed(() => props.timeline.length >= 2)

const capsuleLabel = computed(() => {
  const d = props.currentDate
  return `${d.getFullYear()}年${d.getMonth() + 1}月`
})

const tooltipLabel = computed(() => {
  if (!tooltipDate.value) return ''
  const d = tooltipDate.value
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日`
})

const monthTicks = computed(() => {
  if (!props.timeline.length || totalRange.value <= 0) return []
  return props.timeline.map(t => ({
    year: t.year,
    month: t.month,
    top: dateToPercent(new Date(t.year, t.month - 1, 15)),
  }))
})

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

// Year labels — collapse adjacent labels (<8% apart) keeping the newer (smaller top%) one.
// All year ticks above still render; only the text label is folded.
const yearLabels = computed(() => {
  if (!props.timeline.length || totalRange.value <= 0) return []
  const minY = props.minDate.getFullYear()
  const maxY = props.maxDate.getFullYear()
  type Lbl = { year: number; top: number; anchor: string }
  const raw: Lbl[] = []
  for (let y = minY; y <= maxY; y++) {
    const anchor = new Date(y, 0, 1)
    const clamped = anchor < props.minDate ? props.minDate : anchor > props.maxDate ? props.maxDate : anchor
    const top = Math.max(0, Math.min(100, dateToPercent(clamped)))
    let translate = '-50%'
    if (top > 92) translate = '-100%'
    else if (top < 8) translate = '0%'
    raw.push({ year: y, top, anchor: translate })
  }
  // Sort by top asc (newer years first since maxDate -> 0%).
  raw.sort((a, b) => a.top - b.top)
  const kept: Lbl[] = []
  for (const l of raw) {
    const last = kept[kept.length - 1]
    if (last && l.top - last.top < 8) continue
    kept.push(l)
  }
  return kept
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
  emit('jump', percentToDate(pct))
}

function handleJumpFinal(clientY: number) {
  const pct = yToPercent(clientY)
  emit('jump-final', percentToDate(pct))
}

let rafPending = false
function scheduleJump(clientY: number) {
  if (rafPending) return
  rafPending = true
  requestAnimationFrame(() => {
    rafPending = false
    handleJump(clientY)
  })
}

let lastJumpY = 0

function onPointerDown(e: MouseEvent) {
  dragging.value = true
  lastJumpY = e.clientY
  handleMove(e.clientY)
  handleJump(e.clientY)
  document.addEventListener('mousemove', onDocMouseMove)
  document.addEventListener('mouseup', onDocMouseUp)
}

function onDocMouseMove(e: MouseEvent) {
  if (!dragging.value) return
  lastJumpY = e.clientY
  handleMove(e.clientY)
  scheduleJump(e.clientY)
}

function onDocMouseUp() {
  if (dragging.value) handleJumpFinal(lastJumpY)
  dragging.value = false
  document.removeEventListener('mousemove', onDocMouseMove)
  document.removeEventListener('mouseup', onDocMouseUp)
}

function onTouchStart(e: TouchEvent) {
  dragging.value = true
  const t = e.touches[0]
  lastJumpY = t.clientY
  handleMove(t.clientY)
  handleJump(t.clientY)
  document.addEventListener('touchmove', onTouchMove, { passive: false })
  document.addEventListener('touchend', onTouchEnd)
}

function onTouchMove(e: TouchEvent) {
  e.preventDefault()
  const t = e.touches[0]
  lastJumpY = t.clientY
  handleMove(t.clientY)
  scheduleJump(t.clientY)
}

function onTouchEnd() {
  if (dragging.value) handleJumpFinal(lastJumpY)
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

function onWheel(e: WheelEvent) {
  if (dragging.value) return
  emit('wheel', e.deltaY)
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
  background: transparent;
}
.date-scrubber.is-dragging {
  cursor: grabbing;
  background: linear-gradient(to left, rgba(0, 0, 0, 0.05), transparent);
}
.dark .date-scrubber.is-dragging {
  background: linear-gradient(to left, rgba(255, 255, 255, 0.04), transparent);
}

.scrubber-dot,
.scrubber-leader,
.scrubber-capsule {
  transition: top 200ms ease-out;
}

@media (prefers-reduced-motion: reduce) {
  .scrubber-dot,
  .scrubber-leader,
  .scrubber-capsule {
    transition: none;
  }
}
</style>
