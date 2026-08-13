<template>
  <Transition name="fade">
    <div v-if="isOpen && currentItem" class="fixed inset-0 z-[100]">
      <div class="absolute inset-0 bg-black/90 backdrop-blur-sm" @click="close"></div>
      <div class="relative w-full h-full flex flex-col">
        <div class="shrink-0 flex items-center justify-between p-4 text-white">
          <div class="min-w-0 mr-4">
            <p class="truncate text-sm font-medium">{{ currentItem.name }}</p>
            <p class="truncate text-xs text-white/50">{{ currentItem.rel_path }}</p>
          </div>
          <button class="p-2 rounded-full hover:bg-white/10 transition-colors" aria-label="关闭" @click="close">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div class="flex-1 min-h-0 flex items-center justify-center px-14 pb-2 relative">
          <button
            class="absolute left-3 z-10 p-2 text-white/70 hover:text-white hover:bg-white/10 rounded-full transition-colors disabled:opacity-0 disabled:pointer-events-none"
            :disabled="!canGoPrev"
            aria-label="上一个"
            @click.stop="previous"
          >
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" /></svg>
          </button>

          <Transition :name="transitionName" mode="out-in">
            <div :key="currentItem.id" class="relative max-w-full max-h-full flex items-center justify-center">
              <video
                v-if="currentItem.media_type === 'VIDEO' && !showFallback"
                ref="videoRef"
                :src="mediaUrl(currentItem)"
                class="max-w-full max-h-[72vh] rounded-lg shadow-2xl"
                controls
                autoplay
                playsinline
                loop
                @error="showFallback = true"
              />
              <img
                v-else-if="!showFallback"
                :src="mediaUrl(currentItem)"
                :alt="currentItem.name"
                class="max-w-full max-h-[72vh] object-contain rounded-lg shadow-2xl"
                @error="showFallback = true"
              />
              <div v-else class="relative">
                <img
                  v-if="thumbUrl(currentItem)"
                  :src="thumbUrl(currentItem)"
                  :alt="`${currentItem.name}（缩略图）`"
                  class="max-w-full max-h-[72vh] object-contain rounded-lg shadow-2xl"
                />
                <div v-else class="w-64 h-64 rounded-lg bg-gray-800 flex items-center justify-center text-gray-500">
                  <svg class="w-16 h-16" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M7 3h7l5 5v13H7zM14 3v6h5" /></svg>
                </div>
                <div class="absolute bottom-2 left-1/2 -translate-x-1/2 whitespace-nowrap px-3 py-1 bg-black/60 text-white/90 text-xs rounded-full backdrop-blur-sm">
                  文件无法访问，显示缩略图
                </div>
              </div>
            </div>
          </Transition>

          <button
            class="absolute right-3 z-10 p-2 text-white/70 hover:text-white hover:bg-white/10 rounded-full transition-colors disabled:opacity-0 disabled:pointer-events-none"
            :disabled="!canGoNext"
            aria-label="下一个"
            @click.stop="next"
          >
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" /></svg>
          </button>
        </div>

        <div class="shrink-0 text-center text-xs text-white/60">{{ currentIndex + 1 }} / {{ items.length }}</div>

        <div class="shrink-0 px-4 pb-4 pt-2 relative z-10 flex justify-center">
          <TransitionGroup tag="div" name="thumb" class="relative overflow-hidden" :style="{ width: thumbStripWidth, height: '48px' }">
            <button
              v-for="entry in visibleThumbs"
              :key="`${entry.kind}-${entry.item.id}`"
              class="absolute top-0 w-12 h-12 rounded-md overflow-hidden border-2 transition-all duration-200"
              :style="{ left: `${(thumbOffset(entry) + THUMB_WINDOW) * 54}px` }"
              :class="entry.kind === 'current' && entry.idx === currentIndex
                ? 'border-white scale-110 shadow-lg shadow-white/20 z-10'
                : entry.kind === 'current'
                  ? 'border-transparent opacity-50 hover:opacity-80'
                  : 'border-transparent opacity-25 hover:opacity-60 scale-90'"
              :title="entry.item.name"
              @click="onThumbClick(entry)"
            >
              <img v-if="thumbUrl(entry.item)" :src="thumbUrl(entry.item)" :alt="entry.item.name" class="w-full h-full object-cover" />
              <div v-else class="w-full h-full bg-gray-800 flex items-center justify-center">
                <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg>
              </div>
              <svg v-if="entry.item.media_type === 'VIDEO'" class="absolute inset-0 m-auto w-4 h-4 text-white/80" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z" /></svg>
            </button>
          </TransitionGroup>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import type { RepositoryFile } from '../types'
import { API_BASE_URL, IS_ELECTRON } from '../utils/constants'

const props = withDefaults(defineProps<{
  isOpen: boolean
  items: RepositoryFile[]
  startIndex?: number
  hasMore?: boolean
  hasPrev?: boolean
  hasNext?: boolean
  prevPeekItems?: RepositoryFile[]
  nextPeekItems?: RepositoryFile[]
}>(), {
  startIndex: 0,
  hasMore: false,
  hasPrev: false,
  hasNext: false,
  prevPeekItems: () => [],
  nextPeekItems: () => [],
})

const emit = defineEmits<{
  close: []
  'load-more': []
  'navigate-prev': []
  'navigate-next': []
}>()

const currentIndex = ref(props.startIndex)
const pendingAdvance = ref(false)
const transitionName = ref<'slide-left' | 'slide-right'>('slide-left')
const showFallback = ref(false)
const videoRef = ref<HTMLVideoElement | null>(null)
const THUMB_WINDOW = 5
const PEEK_GAP = 2

const currentItem = computed(() => props.items[currentIndex.value] ?? null)
const canGoPrev = computed(() => currentIndex.value > 0 || props.hasPrev)
const canGoNext = computed(() => currentIndex.value < props.items.length - 1 || props.hasNext || props.hasMore)

function absoluteUrl(path: string) {
  if (!path || /^(https?:|file:|data:|blob:)/i.test(path)) return path
  return `${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`
}

function mediaUrl(item: RepositoryFile) {
  const path = IS_ELECTRON && item.local_file_path ? item.local_file_path : item.file_url
  return absoluteUrl(path)
}

function thumbUrl(item: RepositoryFile) {
  const path = IS_ELECTRON && item.local_thumb_path ? item.local_thumb_path : item.thumb_url
  return absoluteUrl(path)
}

function pauseVideo() {
  videoRef.value?.pause()
}

function close() {
  pauseVideo()
  emit('close')
}

function previous() {
  if (currentIndex.value > 0) {
    transitionName.value = 'slide-right'
    currentIndex.value--
  } else if (props.hasPrev) {
    transitionName.value = 'slide-right'
    emit('navigate-prev')
  }
}

function next() {
  if (currentIndex.value < props.items.length - 1) {
    transitionName.value = 'slide-left'
    currentIndex.value++
  } else if (props.hasNext) {
    transitionName.value = 'slide-left'
    emit('navigate-next')
  } else if (props.hasMore) {
    pendingAdvance.value = true
    emit('load-more')
  }
}

function goToIndex(index: number) {
  if (index === currentIndex.value) return
  transitionName.value = index > currentIndex.value ? 'slide-left' : 'slide-right'
  currentIndex.value = index
}

type ThumbEntry =
  | { kind: 'current'; item: RepositoryFile; idx: number }
  | { kind: 'peek-prev'; item: RepositoryFile; offset: number }
  | { kind: 'peek-next'; item: RepositoryFile; offset: number }

const visibleThumbs = computed<ThumbEntry[]>(() => {
  const result: ThumbEntry[] = []
  const length = props.items.length
  for (let offset = -THUMB_WINDOW; offset <= THUMB_WINDOW; offset++) {
    const index = currentIndex.value + offset
    if (index >= 0 && index < length) result.push({ kind: 'current', item: props.items[index], idx: index })
  }
  const leftMost = -Math.min(currentIndex.value, THUMB_WINDOW)
  const prevStart = leftMost - PEEK_GAP - 1
  for (let step = 0; prevStart - step >= -THUMB_WINDOW; step++) {
    const index = props.prevPeekItems.length - 1 - step
    if (index < 0) break
    result.push({ kind: 'peek-prev', item: props.prevPeekItems[index], offset: prevStart - step })
  }
  const rightMost = Math.min(length - 1 - currentIndex.value, THUMB_WINDOW)
  const nextStart = rightMost + PEEK_GAP + 1
  for (let step = 0; nextStart + step <= THUMB_WINDOW; step++) {
    if (step >= props.nextPeekItems.length) break
    result.push({ kind: 'peek-next', item: props.nextPeekItems[step], offset: nextStart + step })
  }
  return result
})

function thumbOffset(entry: ThumbEntry) {
  return entry.kind === 'current' ? entry.idx - currentIndex.value : entry.offset
}

function onThumbClick(entry: ThumbEntry) {
  if (entry.kind === 'current') {
    goToIndex(entry.idx)
  } else if (entry.kind === 'peek-prev') {
    transitionName.value = 'slide-right'
    emit('navigate-prev')
  } else {
    transitionName.value = 'slide-left'
    emit('navigate-next')
  }
}

const thumbStripWidth = computed(() => {
  const slots = THUMB_WINDOW * 2 + 1
  return `${slots * 48 + (slots - 1) * 6}px`
})

function onKeydown(event: KeyboardEvent) {
  if (!props.isOpen) return
  if (event.key.startsWith('Arrow')) {
    event.preventDefault()
  }
  if (event.key === 'Escape') {
    event.stopImmediatePropagation()
    close()
  } else if (event.key === 'ArrowLeft') {
    previous()
  } else if (event.key === 'ArrowRight') {
    next()
  }
}

watch(() => props.startIndex, (index) => {
  if (!props.isOpen) return
  const clamped = Math.max(0, Math.min(index, props.items.length - 1))
  currentIndex.value = clamped
}, { flush: 'post' })

watch(() => props.isOpen, (open) => {
  if (open) {
    currentIndex.value = props.startIndex
    transitionName.value = 'slide-left'
    showFallback.value = false
  }
})

watch(() => props.items.length, (length, previousLength) => {
  if (pendingAdvance.value && length > previousLength) {
    transitionName.value = 'slide-left'
    currentIndex.value = previousLength
    pendingAdvance.value = false
  } else if (length && currentIndex.value >= length) {
    currentIndex.value = length - 1
  }
})

watch(currentIndex, async () => {
  pauseVideo()
  showFallback.value = false
  await nextTick()
  videoRef.value?.play().catch(() => {})
})

onMounted(() => window.addEventListener('keydown', onKeydown))
onUnmounted(() => window.removeEventListener('keydown', onKeydown))
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from,
.fade-leave-to { opacity: 0; }

.slide-left-enter-active,
.slide-left-leave-active,
.slide-right-enter-active,
.slide-right-leave-active {
  transition: transform 180ms ease-out, opacity 180ms ease-out;
}
.slide-left-enter-from { transform: translateX(24px); opacity: 0; }
.slide-left-leave-to { transform: translateX(-24px); opacity: 0; }
.slide-right-enter-from { transform: translateX(-24px); opacity: 0; }
.slide-right-leave-to { transform: translateX(24px); opacity: 0; }

.thumb-enter-active,
.thumb-leave-active { transition: opacity 200ms ease-out, transform 200ms ease-out, left 200ms ease-out; }
.thumb-leave-active { pointer-events: none; }
.thumb-enter-from { opacity: 0; transform: translateX(24px) scale(0.7); }
.thumb-leave-to { opacity: 0; transform: translateX(-24px) scale(0.7); }

@media (prefers-reduced-motion: reduce) {
  .fade-enter-active,
  .fade-leave-active,
  .slide-left-enter-active,
  .slide-left-leave-active,
  .slide-right-enter-active,
  .slide-right-leave-active,
  .thumb-enter-active,
  .thumb-leave-active { transition-duration: 0.01ms; }
}
</style>
