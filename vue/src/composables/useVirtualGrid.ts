import {
  ref,
  computed,
  shallowRef,
  triggerRef,
  watch,
  onMounted,
  onUnmounted,
  type Ref,
} from 'vue'
import { api } from './useApi'
import type { Media, CursorResponse } from '../types'

export interface TimelineEntry {
  year: number
  month: number
  count: number
}

export interface MediaFilters {
  starred?: boolean
  type?: string
  tag_id?: number | null
  actor_id?: number | null
}

export interface BucketLayout {
  key: string
  year: number
  month: number
  count: number
  rows: number
  headerOffset: number
  gridOffset: number
  height: number
  endOffset: number
}

export interface BucketCacheEntry {
  status: 'idle' | 'loading' | 'partial' | 'complete' | 'error'
  items: Media[]
  nextCursor: string | null
  loadedCount: number
}

const GAP = 4
const WINDOW_GAP = 16
const PAGE_LIMIT = 100
const PREFETCH_PX = 800
const DWELL_MS = 150
const MAX_CONCURRENT = 2
const DEFAULT_HEADER_H = 44

interface Options {
  container: Ref<HTMLElement | null>
  measureEl: Ref<HTMLElement | null>
  filters: Ref<MediaFilters>
}

function pad(n: number) {
  return String(n).padStart(2, '0')
}

function bucketKey(year: number, month: number) {
  return `${year}-${pad(month)}`
}

function monthStartIso(year: number, month: number) {
  return `${year}-${pad(month)}-01T00:00:00`
}

function nextMonthStartIso(year: number, month: number) {
  if (month === 12) return `${year + 1}-01-01T00:00:00`
  return `${year}-${pad(month + 1)}-01T00:00:00`
}

function bucketStartCursor(year: number, month: number) {
  return `${nextMonthStartIso(year, month)}|2147483647`
}

export function useVirtualGrid(opts: Options) {
  const { container, measureEl, filters } = opts

  const timeline = ref<TimelineEntry[]>([])
  const loadingTimeline = ref(false)
  const cols = ref(window.innerWidth >= 640 ? 4 : 3)
  const cellSize = ref(0)
  const monthHeaderH = ref(DEFAULT_HEADER_H)
  const scrollTop = ref(0)
  const viewportH = ref(0)

  const cacheRef = shallowRef(new Map<string, BucketCacheEntry>())
  const dispatchPaused = ref(false)

  function bumpCache() {
    triggerRef(cacheRef)
  }

  const buckets = computed<BucketLayout[]>(() => {
    if (!timeline.value.length || cellSize.value <= 0) return []
    const out: BucketLayout[] = []
    let cursor = 0
    const headerH = monthHeaderH.value
    const cs = cellSize.value
    const c = cols.value
    for (const t of timeline.value) {
      const rows = Math.max(1, Math.ceil(t.count / c))
      const gridH = rows * cs + (rows - 1) * GAP
      const height = headerH + gridH
      out.push({
        key: bucketKey(t.year, t.month),
        year: t.year,
        month: t.month,
        count: t.count,
        rows,
        headerOffset: cursor,
        gridOffset: cursor + headerH,
        height,
        endOffset: cursor + height + WINDOW_GAP,
      })
      cursor += height + WINDOW_GAP
    }
    return out
  })

  const totalHeight = computed(() => {
    const arr = buckets.value
    return arr.length ? arr[arr.length - 1].endOffset : 0
  })

  const visibleBuckets = computed(() => {
    const top = scrollTop.value - PREFETCH_PX
    const bottom = scrollTop.value + viewportH.value + PREFETCH_PX
    return buckets.value.filter((b) => b.endOffset >= top && b.headerOffset <= bottom)
  })

  const currentDate = computed(() => {
    const arr = buckets.value
    if (!arr.length) return new Date()
    const top = scrollTop.value
    for (const b of arr) {
      if (b.endOffset > top) {
        return new Date(b.year, b.month - 1, 1)
      }
    }
    const last = arr[arr.length - 1]
    return new Date(last.year, last.month - 1, 1)
  })

  function paramsObj() {
    const f = filters.value
    return {
      starred: f.starred || undefined,
      type: f.type || undefined,
      tag_id: f.tag_id ?? undefined,
      actor_id: f.actor_id ?? undefined,
    }
  }

  function getOrInit(key: string): BucketCacheEntry {
    let e = cacheRef.value.get(key)
    if (!e) {
      e = { status: 'idle', items: [], nextCursor: null, loadedCount: 0 }
      cacheRef.value.set(key, e)
    }
    return e
  }

  async function loadTimeline() {
    loadingTimeline.value = true
    try {
      timeline.value = await api.get<TimelineEntry[]>('/media/timeline', paramsObj())
    } finally {
      loadingTimeline.value = false
    }
  }

  let inFlight = 0
  const dwellTimers = new Map<string, ReturnType<typeof setTimeout>>()
  const queue: string[] = []

  function pumpQueue() {
    while (inFlight < MAX_CONCURRENT && queue.length) {
      const key = queue.shift()!
      const entry = cacheRef.value.get(key)
      if (!entry || entry.status === 'loading' || entry.status === 'complete') continue
      void runLoad(key)
    }
  }

  async function runLoad(key: string) {
    const entry = getOrInit(key)
    const b = buckets.value.find((x) => x.key === key)
    if (!b) return
    entry.status = 'loading'
    bumpCache()
    inFlight++
    try {
      const cursor = entry.nextCursor ?? bucketStartCursor(b.year, b.month)
      const data = await api.get<CursorResponse<Media>>('/media', {
        cursor,
        limit: PAGE_LIMIT,
        ...paramsObj(),
      })
      const monthStart = monthStartIso(b.year, b.month)
      const inMonth: Media[] = []
      let spilled = false
      for (const m of data.items) {
        if (m.created_at >= monthStart) inMonth.push(m)
        else {
          spilled = true
          break
        }
      }
      entry.items.push(...inMonth)
      entry.loadedCount = entry.items.length

      if (entry.loadedCount >= b.count || spilled || !data.has_more) {
        entry.status = 'complete'
        entry.nextCursor = null
      } else {
        entry.status = 'partial'
        entry.nextCursor = data.next_cursor
      }
    } catch {
      entry.status = 'error'
    } finally {
      inFlight--
      bumpCache()
      pumpQueue()
    }
  }

  function scheduleLoad(key: string) {
    const entry = cacheRef.value.get(key)
    if (entry && (entry.status === 'loading' || entry.status === 'complete')) return
    if (dwellTimers.has(key)) return
    const t = setTimeout(() => {
      dwellTimers.delete(key)
      const stillVisible = visibleBuckets.value.some((b) => b.key === key)
      if (!stillVisible) return
      const e = getOrInit(key)
      if (e.status === 'idle' || e.status === 'partial' || e.status === 'error') {
        if (!queue.includes(key)) queue.push(key)
        pumpQueue()
      }
    }, DWELL_MS)
    dwellTimers.set(key, t)
  }

  function cancelLoad(key: string) {
    const t = dwellTimers.get(key)
    if (t) {
      clearTimeout(t)
      dwellTimers.delete(key)
    }
  }

  function dispatchFetches() {
    if (dispatchPaused.value) return
    const visibleKeys = new Set(visibleBuckets.value.map((b) => b.key))
    for (const k of dwellTimers.keys()) {
      if (!visibleKeys.has(k)) cancelLoad(k)
    }
    for (const b of visibleBuckets.value) {
      const e = cacheRef.value.get(b.key)
      if (!e || e.status === 'idle' || e.status === 'partial') {
        scheduleLoad(b.key)
      }
    }
  }

  function setDispatchPaused(v: boolean) {
    dispatchPaused.value = v
    if (v) {
      for (const t of dwellTimers.values()) clearTimeout(t)
      dwellTimers.clear()
    } else {
      dispatchFetches()
    }
  }

  function loadBucketNow(key: string) {
    cancelLoad(key)
    const e = getOrInit(key)
    if (e.status === 'loading' || e.status === 'complete') return
    if (!queue.includes(key)) queue.push(key)
    pumpQueue()
  }

  function loadedItem(b: BucketLayout, idx: number): Media | undefined {
    const e = cacheRef.value.get(b.key)
    return e?.items[idx]
  }

  function itemPosition(b: BucketLayout, idx: number) {
    const c = cols.value
    const cs = cellSize.value
    const row = Math.floor(idx / c)
    const col = idx % c
    return {
      top: b.gridOffset + row * (cs + GAP),
      left: col * (cs + GAP),
      size: cs,
    }
  }

  function scrollToBucket(year: number, month: number) {
    const key = bucketKey(year, month)
    const b = buckets.value.find((x) => x.key === key)
    if (!b || !container.value) return
    container.value.scrollTo({ top: b.headerOffset, behavior: 'auto' })
  }

  function scrollToDate(date: Date) {
    const b = findBucketByDate(date)
    if (!b || !container.value) return
    // Fraction of month elapsed (newer = top, so day 1 → bottom of month)
    const daysInMonth = new Date(b.year, b.month, 0).getDate()
    const day = date.getFullYear() === b.year && date.getMonth() + 1 === b.month
      ? Math.min(daysInMonth, Math.max(1, date.getDate()))
      : daysInMonth
    const frac = (daysInMonth - day) / daysInMonth
    const top = b.headerOffset + frac * b.height
    container.value.scrollTo({ top, behavior: 'auto' })
  }

  function findBucketByDate(date: Date): BucketLayout | null {
    const y = date.getFullYear()
    const m = date.getMonth() + 1
    const arr = buckets.value
    for (const b of arr) {
      if (b.year < y || (b.year === y && b.month <= m)) return b
    }
    return arr[arr.length - 1] ?? null
  }

  function resetAll() {
    cacheRef.value = new Map()
    timeline.value = []
    for (const t of dwellTimers.values()) clearTimeout(t)
    dwellTimers.clear()
    queue.length = 0
    if (container.value) container.value.scrollTop = 0
    void loadTimeline()
  }

  function onScroll() {
    const el = container.value
    if (!el) return
    scrollTop.value = el.scrollTop
    viewportH.value = el.clientHeight
    dispatchFetches()
  }

  function findItemBucketAndIndex(id: number): { key: string; idx: number } | null {
    for (const [key, entry] of cacheRef.value.entries()) {
      const idx = entry.items.findIndex((m) => m.id === id)
      if (idx !== -1) return { key, idx }
    }
    return null
  }

  function updateItem(id: number, mutator: (m: Media) => void) {
    const found = findItemBucketAndIndex(id)
    if (!found) return
    const entry = cacheRef.value.get(found.key)!
    mutator(entry.items[found.idx])
    bumpCache()
  }

  function removeItem(id: number) {
    const found = findItemBucketAndIndex(id)
    if (!found) return
    const entry = cacheRef.value.get(found.key)!
    entry.items.splice(found.idx, 1)
    entry.loadedCount = entry.items.length
    const tlIdx = timeline.value.findIndex((t) => bucketKey(t.year, t.month) === found.key)
    if (tlIdx !== -1) {
      const t = timeline.value[tlIdx]
      if (t.count > 0) {
        timeline.value.splice(tlIdx, 1, { ...t, count: t.count - 1 })
      }
    }
    bumpCache()
  }

  let resizeObserver: ResizeObserver | null = null
  let measuredHeader = false

  function recomputeCellSize() {
    const el = measureEl.value
    if (!el) return
    const w = el.clientWidth
    if (w <= 0) return
    const c = cols.value
    cellSize.value = Math.max(1, Math.floor((w - (c - 1) * GAP) / c))
  }

  function measureHeaderHeight() {
    if (measuredHeader) return
    const el = measureEl.value
    if (!el) return
    const probe = document.createElement('div')
    probe.style.cssText =
      'position:absolute;visibility:hidden;left:0;right:0;padding:8px 0;'
    probe.innerHTML = '<span class="text-sm font-medium">YYYY年MM月</span>'
    el.appendChild(probe)
    const h = probe.getBoundingClientRect().height
    el.removeChild(probe)
    if (h > 0) monthHeaderH.value = Math.ceil(h)
    measuredHeader = true
  }

  function onWindowResize() {
    const newCols = window.innerWidth >= 640 ? 4 : 3
    if (newCols !== cols.value) cols.value = newCols
    recomputeCellSize()
    if (container.value) viewportH.value = container.value.clientHeight
  }

  watch(filters, () => resetAll(), { deep: true })

  watch(visibleBuckets, () => dispatchFetches())

  onMounted(() => {
    if (measureEl.value) {
      resizeObserver = new ResizeObserver(() => {
        recomputeCellSize()
      })
      resizeObserver.observe(measureEl.value)
    }
    window.addEventListener('resize', onWindowResize)
    measureHeaderHeight()
    recomputeCellSize()
    if (container.value) viewportH.value = container.value.clientHeight
    void loadTimeline().then(() => {
      dispatchFetches()
    })
  })

  onUnmounted(() => {
    resizeObserver?.disconnect()
    resizeObserver = null
    window.removeEventListener('resize', onWindowResize)
    for (const t of dwellTimers.values()) clearTimeout(t)
    dwellTimers.clear()
  })

  return {
    timeline,
    loadingTimeline,
    cols,
    cellSize,
    monthHeaderH,
    buckets,
    totalHeight,
    cache: cacheRef,
    scrollTop,
    viewportH,
    visibleBuckets,
    currentDate,
    onScroll,
    scrollToBucket,
    scrollToDate,
    setDispatchPaused,
    findBucketByDate,
    loadBucketNow,
    loadedItem,
    itemPosition,
    resetAll,
    updateItem,
    removeItem,
    findItemBucketAndIndex,
  }
}
