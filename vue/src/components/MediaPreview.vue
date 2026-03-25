<template>
  <Transition name="fade">
    <div v-if="isOpen" class="fixed inset-0 z-[100]">
      <div class="absolute inset-0 bg-black/90 backdrop-blur-sm" @click="close"></div>
      <div class="relative w-full h-full flex flex-col">
        <div class="flex items-center justify-between p-4">
          <div class="text-white text-sm font-medium">
            {{ currentIndex + 1 }} / {{ totalItems }}
          </div>
          <button 
            @click="close"
            class="p-2 text-white hover:bg-white/10 rounded-full transition-colors"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div class="flex-1 flex items-center justify-center px-4 pb-4 relative">
          <div class="relative max-w-[95vw] max-h-[85vh]">
            <video
              v-if="currentItem && isVideo(currentItem.mime_type)"
              ref="videoRef"
              :src="getMediaUrl(currentItem)"
              class="max-w-[95vw] max-h-[85vh] rounded-lg shadow-2xl"
              controls
              playsinline
              loop
              autoplay
            ></video>
            
            <img
              v-else-if="currentItem && isImage(currentItem.mime_type)"
              :src="getMediaUrl(currentItem)"
              :alt="`Media ${currentIndex + 1}`"
              class="max-w-[95vw] max-h-[85vh] object-contain rounded-lg shadow-2xl"
            />
          </div>
        </div>

        <div class="flex items-center justify-center gap-4 p-4 relative z-10">
          <button 
            @click.stop="prev"
            :disabled="!canGoPrev"
            class="p-3 text-white hover:bg-white/10 rounded-full transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" />
            </svg>
          </button>
          
          <button 
            @click.stop="next"
            :disabled="!canGoNext"
            class="p-3 text-white hover:bg-white/10 rounded-full transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import type { MessageMediaItem } from '../types'

interface Props {
  isOpen: boolean
  items: MessageMediaItem[]
  startIndex?: number
}

const props = withDefaults(defineProps<Props>(), {
  startIndex: 0
})

const emit = defineEmits<{
  close: []
  'navigate-prev': []
  'navigate-next': []
}>()

const currentIndex = ref(props.startIndex)
const videoRef = ref<HTMLVideoElement | null>(null)

const currentItem = computed(() => {
  if (props.items.length === 0) return null
  return props.items[currentIndex.value]
})

const totalItems = computed(() => props.items.length)

const canGoPrev = computed(() => {
  return currentIndex.value > 0
})

const canGoNext = computed(() => {
  return currentIndex.value < props.items.length - 1
})

const isVideo = (mimeType: string) => {
  return mimeType?.startsWith('video/')
}

const isImage = (mimeType: string) => {
  return mimeType?.startsWith('image/')
}

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
</style>
