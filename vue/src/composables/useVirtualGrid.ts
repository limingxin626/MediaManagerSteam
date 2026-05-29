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
  day: number
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
  day: number
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
const RENDER_OVERSCAN_PX = 400
const DWELL_MS = 150
const MAX_CONCURRENT = 6
const DEFAULT_HEADER_H = 44

export interface VisibleCell {
  bucket: BucketLayout
  idx: number
  top: number
  left: number
  size: number
}

interface Options {
  container: Ref<HTMLElement | null>
  measureEl: Ref<HTMLElement | null>
  filters: Ref<MediaFilters>
}

function pad(n: number) {
  return String(n).padStart(2, '0')
}

function bucketKey(year: number, month: number, day: number) {
  return `${year}-${pad(month)}-${pad(day)}`
}

function dayStartIso(year: number, month: number, day: number) {
  return `${year}-${pad(month)}-${pad(day)}T00:00:00`
}

function nextDayStartIso(year: number, month: number, day: number) {
  const d = new Date(year, month - 1, day + 1)
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T00:00:00`
}

function bucketStartCursor(year: number, month: number, day: number) {
  return `${nextDayStartIso(year, month, day)}|2147483647`
}

export function useVirtualGrid(opts: Options) {
  const { container, measureEl, filters } = opts

  const timeline = ref<TimelineEntry[]>([])
  const loadingTimeline = ref(false)
  const cols = ref(3)
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
        key: bucketKey(t.year, t.month, t.day),
        year: t.year,
        month: t.month,
        day: t.day,
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

  const visibleCells = computed<VisibleCell[]>(() => {
    const cs = cellSize.value
    const c = cols.value
    if (cs <= 0 || c <= 0) return []
    const top = scrollTop.value - RENDER_OVERSCAN_PX
    const bottom = scrollTop.value + viewportH.value + RENDER_OVERSCAN_PX
    const rowStride = cs + GAP
    const out: VisibleCell[] = []
    for (const b of buckets.value) {
      if (b.endOffset < top || b.headerOffset > bottom) continue
      const firstRow = Math.max(0, Math.floor((top - b.gridOffset) / rowStride))
      const lastRow = Math.min(
        b.rows - 1,
        Math.floor((bottom - b.gridOffset) / rowStride),
      )
      if (lastRow < 0 || firstRow > b.rows - 1) continue
      const startIdx = firstRow * c
      const endIdx = Math.min(b.count, (lastRow + 1) * c)
      for (let idx = startIdx; idx < endIdx; idx++) {
        const row = Math.floor(idx / c)
        const col = idx % c
        out.push({
          bucket: b,
          idx,
          top: b.gridOffset + row * rowStride,
          left: col * rowStride,
          size: cs,
        })
      }
    }
    return out
  })

  const currentDate = computed(() => {
    const arr = buckets.value
    if (!arr.length) return new Date()
    const top = scrollTop.value
    for (const b of arr) {
      if (b.endOffset > top) {
        return new Date(b.year, b.month - 1, b.day)
      }
    }
    const last = arr[arr.length - 1]
    return new Date(last.year, last.month - 1, last.day)
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

  function viewportCenter() {
    return scrollTop.value + viewportH.value / 2
  }

  function bucketDistance(key: string) {
    const b = buckets.value.find((x) => x.key === key)
    if (!b) return Number.POSITIVE_INFINITY
    const center = viewportCenter()
    if (center < b.headerOffset) return b.headerOffset - center
    if (center > b.endOffset) return center - b.endOffset
    return 0
  }

  function enqueue(key: string, priority: 'normal' | 'urgent' = 'normal') {
    const existing = queue.indexOf(key)
    if (existing !== -1) queue.splice(existing, 1)
    if (priority === 'urgent') {
      queue.unshift(key)
    } else {
      queue.push(key)
    }
    queue.sort((a, b) => bucketDistance(a) - bucketDistance(b))
  }

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
      const cursor = entry.nextCursor ?? bucketStartCursor(b.year, b.month, b.day)
      const data = await api.get<CursorResponse<Media>>('/media', {
        cursor,
        limit: PAGE_LIMIT,
        ...paramsObj(),
      })
      const dayStart = dayStartIso(b.year, b.month, b.day)
      const inDay: Media[] = []
      let spilled = false
      for (const m of data.items) {
        if (m.created_at >= dayStart) inDay.push(m)
        else {
          spilled = true
          break
        }
      }
      entry.items.push(...inDay)
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
        enqueue(key, 'normal')
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
    enqueue(key, 'urgent')
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

  function scrollToBucket(year: number, month: number, day: number) {
    const key = bucketKey(year, month, day)
    const b = buckets.value.find((x) => x.key === key)
    if (!b || !container.value) return
    container.value.scrollTo({ top: b.headerOffset, behavior: 'auto' })
    scrollTop.value = b.headerOffset
    loadBucketNow(key)
  }

  function scrollToDate(date: Date) {
    const b = findBucketByDate(date)
    if (!b || !container.value) return
    container.value.scrollTo({ top: b.headerOffset, behavior: 'auto' })
    scrollTop.value = b.headerOffset
    loadBucketNow(b.key)
  }

  function findBucketByDate(date: Date): BucketLayout | null {
    const target = date.getFullYear() * 10000 + (date.getMonth() + 1) * 100 + date.getDate()
    const arr = buckets.value
    for (const b of arr) {
      const bi = b.year * 10000 + b.month * 100 + b.day
      if (bi <= target) return b
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
    const tlIdx = timeline.value.findIndex((t) => bucketKey(t.year, t.month, t.day) === found.key)
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

  const TARGET_CELL = 220
  const MIN_COLS_MOBILE = 3
  const MIN_COLS_DESKTOP = 4

  function recomputeCellSize() {
    const el = measureEl.value
    if (!el) return
    const w = el.clientWidth
    if (w <= 0) return
    const minCols = window.innerWidth >= 640 ? MIN_COLS_DESKTOP : MIN_COLS_MOBILE
    const newCols = Math.max(minCols, Math.round(w / TARGET_CELL))
    if (newCols !== cols.value) cols.value = newCols
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
    visibleCells,
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
