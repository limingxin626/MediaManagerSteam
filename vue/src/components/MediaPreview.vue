<template>
  <Transition name="fade">
    <div v-if="isOpen" class="fixed inset-0 z-[100]">
      <div class="absolute inset-0 bg-black/90 backdrop-blur-sm" @click="close"></div>
      <div class="relative w-full h-full flex flex-col">
        <div class="flex items-center justify-between p-4">
          <div class="text-white text-sm font-medium">
            {{ currentIndex + 1 }} / {{ totalItems }}
          </div>
          <div class="flex items-center gap-2">
            <button
              v-if="currentItem"
              @click="emit('toggle-star')"
              class="p-2 rounded-full transition-colors"
              :class="isCurrentStarred
                ? 'text-yellow-400 hover:bg-white/10'
                : 'text-white/70 hover:text-yellow-400 hover:bg-white/10'"
              :title="isCurrentStarred ? '取消收藏' : '收藏'"
            >
              <svg class="w-6 h-6" :fill="isCurrentStarred ? 'currentColor' : 'none'" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
              </svg>
            </button>
            <button
              @click="close"
              class="p-2 text-white hover:bg-white/10 rounded-full transition-colors"
            >
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Main preview area with left/right nav -->
        <div class="flex-1 flex items-center justify-center px-4 pb-2 relative min-h-0">
          <!-- Prev button (left) -->
          <button
            @click.stop="prev"
            :disabled="!canGoPrev"
            class="absolute left-2 z-10 p-2 text-white/70 hover:text-white hover:bg-white/10 rounded-full transition-colors disabled:opacity-0 disabled:pointer-events-none"
          >
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
            </svg>
          </button>

          <div class="relative max-w-[90vw] max-h-[80vh]">
            <video
              v-if="currentItem && isVideo(currentItem.mime_type)"
              ref="videoRef"
              :src="getMediaUrl(currentItem)"
              class="max-w-[90vw] max-h-[80vh] rounded-lg shadow-2xl"
              controls
              playsinline
              loop
              autoplay
            ></video>

            <img
              v-else-if="currentItem && isImage(currentItem.mime_type)"
              :src="getMediaUrl(currentItem)"
              :alt="`Media ${currentIndex + 1}`"
              class="max-w-[90vw] max-h-[80vh] object-contain rounded-lg shadow-2xl"
            />
          </div>

          <!-- Next button (right) -->
          <button
            @click.stop="next"
            :disabled="!canGoNext"
            class="absolute right-2 z-10 p-2 text-white/70 hover:text-white hover:bg-white/10 rounded-full transition-colors disabled:opacity-0 disabled:pointer-events-none"
          >
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>

        <!-- Thumbnail strip -->
        <div v-if="items.length > 1" class="px-4 pb-4 pt-2 relative z-10">
          <div
            ref="thumbStripRef"
            class="flex items-center gap-1.5 overflow-x-auto justify-center scrollbar-hide"
          >
            <button
              v-for="(item, idx) in items"
              :key="item.id"
              :ref="(el) => setThumbRef(idx, el as HTMLElement | null)"
              @click="currentIndex = idx"
              class="shrink-0 w-12 h-12 rounded-md overflow-hidden border-2 transition-all duration-200"
              :class="idx === currentIndex
                ? 'border-white scale-110 shadow-lg shadow-white/20'
                : 'border-transparent opacity-50 hover:opacity-80'"
            >
              <img
                v-if="isImage(item.mime_type)"
                :src="resolveUrl(item.thumb_url)"
                class="w-full h-full object-cover"
              />
              <div
                v-else-if="isVideo(item.mime_type)"
                class="w-full h-full relative bg-gray-800"
              >
                <img
                  :src="resolveUrl(item.thumb_url)"
                  class="w-full h-full object-cover"
                />
                <svg class="absolute inset-0 m-auto w-4 h-4 text-white/80" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M8 5v14l11-7z" />
                </svg>
              </div>
              <div v-else class="w-full h-full bg-gray-700 flex items-center justify-center">
                <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                </svg>
              </div>
            </button>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import type { MessageMediaItem } from '../types'
import { isVideo, isImage, resolveUrl } from '../utils/media'

interface Props {
  isOpen: boolean
  items: MessageMediaItem[]
  startIndex?: number
  starred?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  startIndex: 0,
  starred: false,
})

const emit = defineEmits<{
  close: []
  'navigate-prev': []
  'navigate-next': []
  'toggle-star': []
}>()

const currentIndex = ref(props.startIndex)
const videoRef = ref<HTMLVideoElement | null>(null)
const thumbStripRef = ref<HTMLElement | null>(null)
const thumbRefs = ref<Map<number, HTMLElement>>(new Map())

const setThumbRef = (idx: number, el: HTMLElement | null) => {
  if (el) {
    thumbRefs.value.set(idx, el)
  } else {
    thumbRefs.value.delete(idx)
  }
}

const currentItem = computed(() => {
  if (props.items.length === 0) return null
  return props.items[currentIndex.value]
})

const isCurrentStarred = computed(() => props.starred)

const totalItems = computed(() => props.items.length)

const canGoPrev = computed(() => {
  return currentIndex.value > 0
})

const canGoNext = computed(() => {
  return currentIndex.value < props.items.length - 1
})

const getMediaUrl = (item: MessageMediaItem) => {
  return item.file_path
}

const close = () => {
  if (videoRef.value) {
    videoRef.value.pause()
  }
  emit('close')
}

const prev = () => {
  if (canGoPrev.value) {
    currentIndex.value--
  } else {
    emit('navigate-prev')
  }
}

const next = () => {
  if (canGoNext.value) {
    currentIndex.value++
  } else {
    emit('navigate-next')
  }
}

const handleKeydown = (e: KeyboardEvent) => {
  if (!props.isOpen) return
  
  switch (e.key) {
    case 'Escape':
      close()
      break
    case 'ArrowLeft':
    case 'ArrowUp':
      prev()
      break
    case 'ArrowRight':
    case 'ArrowDown':
      next()
      break
  }
}

watch(() => props.isOpen, async (newValue) => {
  if (newValue) {
    currentIndex.value = props.startIndex
    await nextTick()
    if (videoRef.value) {
      videoRef.value.play().catch(() => {})
    }
  }
})

watch(currentIndex, async () => {
  await nextTick()
  if (videoRef.value) {
    videoRef.value.play().catch(() => {})
  }
  // Scroll active thumbnail into view
  const thumb = thumbRefs.value.get(currentIndex.value)
  if (thumb) {
    thumb.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' })
  }
})

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
.scrollbar-hide::-webkit-scrollbar {
  display: none;
}
</style>
