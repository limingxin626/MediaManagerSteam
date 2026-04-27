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
              @click="handleStarClick()"
              class="p-2 rounded-full transition-colors"
              :class="isCurrentStarred
                ? 'text-yellow-400 hover:bg-white/10'
                : 'text-white/70 hover:text-yellow-400 hover:bg-white/10'"
              :title="isCurrentStarred ? '取消收藏' : '收藏'"
            >
              <svg class="w-6 h-6" :class="{ 'star-bounce': previewStarBounce }" :fill="isCurrentStarred ? 'currentColor' : 'none'" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
              </svg>
            </button>
            <button
              v-if="currentItem"
              @click="showDeleteConfirm = true"
              class="p-2 text-white hover:bg-white/10 rounded-full transition-colors"
              title="删除媒体"
            >
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
            <button
              v-if="currentItem && rotationDegrees !== 0"
              @click="confirmRotation"
              :disabled="isRotating"
              class="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-full transition-colors disabled:opacity-50"
            >
              {{ isRotating ? '旋转中...' : '确认旋转' }}
            </button>
            <button
              v-if="currentItem"
              @click="handleRotate"
              class="p-2 text-white hover:bg-white/10 rounded-full transition-colors"
              :class="{ 'text-blue-400': rotationDegrees !== 0 }"
              title="旋转 90°"
            >
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
            <button
              v-if="currentItem"
              @click="openDetailPage"
              class="p-2 text-white hover:bg-white/10 rounded-full transition-colors"
              title="打开详情页"
            >
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
              </svg>
            </button>
            <button
              v-if="currentItem"
              @click="openFileLocation"
              class="p-2 text-white hover:bg-white/10 rounded-full transition-colors"
              title="打开文件位置"
            >
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" />
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

          <div class="flex flex-col items-center gap-2 max-w-[90vw] max-h-[80vh]">
            <div class="relative">
              <video
                v-if="currentItem && isVideo(currentItem.mime_type)"
                ref="videoRef"
                :src="getMediaUrl(currentItem)"
                class="max-w-[90vw] max-h-[70vh] rounded-lg shadow-2xl"
                :style="mediaTransformStyle"
                controls
                playsinline
                loop
                autoplay
              ></video>

              <img
                v-else-if="currentItem && isImage(currentItem.mime_type)"
                :src="getMediaUrl(currentItem)"
                :alt="`Media ${currentIndex + 1}`"
                class="max-w-[90vw] max-h-[70vh] object-contain rounded-lg shadow-2xl"
                :style="mediaTransformStyle"
              />
            </div>

            <!-- Media tags -->
            <div v-if="currentItem" class="flex items-center gap-1.5 flex-wrap justify-center">
              <span
                v-for="tag in (currentItem.tags || [])"
                :key="tag.id"
                @click.stop="removeMediaTag(tag.id)"
                class="px-2 py-0.5 text-xs rounded-full bg-white/15 text-white/90 hover:bg-red-500/40 hover:line-through cursor-pointer transition-colors"
              >
                #{{ tag.name }}
              </span>
              <TagPickerPopover
                v-if="allTags.length"
                :all-tags="allTags"
                :message-tags="currentItem.tags || []"
                @select="addMediaTag"
              />
            </div>
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

  <!-- Delete confirmation dialog -->
  <Transition name="fade">
    <div v-if="showDeleteConfirm" class="fixed inset-0 z-[200] flex items-center justify-center">
      <div class="absolute inset-0 bg-black/70 backdrop-blur-sm" @click="showDeleteConfirm = false"></div>
      <div class="relative bg-gray-900 rounded-lg p-6 max-w-md w-full mx-4 shadow-2xl">
        <h3 class="text-xl font-semibold text-white mb-4">确认删除</h3>
        <p class="text-gray-300 mb-6">确定要删除此媒体吗？</p>
        <div class="flex items-center mb-6">
          <input
            type="checkbox"
            id="deleteSource"
            v-model="deleteSourceFile"
            class="mr-2 h-4 w-4 rounded border-gray-600 text-blue-500 focus:ring-blue-500"
          />
          <label for="deleteSource" class="text-gray-300">同时删除源文件</label>
        </div>
        <div class="flex gap-3 justify-end">
          <button
            @click="showDeleteConfirm = false"
            class="px-4 py-2 rounded-md bg-gray-700 text-white hover:bg-gray-600 transition-colors"
          >
            取消
          </button>
          <button
            @click="confirmDelete"
            class="px-4 py-2 rounded-md bg-red-600 text-white hover:bg-red-700 transition-colors"
          >
            删除
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import type { MessageMediaItem, TagWithCount, TagItem } from '../types'
import { isVideo, isImage, resolveUrl, rotateMedia } from '../utils/media'
import { api } from '../composables/useApi'
import { useToast } from '../composables/useToast'
import TagPickerPopover from './TagPickerPopover.vue'

const toast = useToast()
const router = useRouter()

// 扩展 Window 接口以包含 Electron API
declare global {
  interface Window {
    electronAPI?: {
      openFileDialog: (options: any) => Promise<any>
      showItemInFolder: (path: string) => void
    }
  }
}

interface Props {
  isOpen: boolean
  items: MessageMediaItem[]
  startIndex?: number
  starred?: boolean
  messageId?: number
  allTags?: TagWithCount[]
}

const props = withDefaults(defineProps<Props>(), {
  startIndex: 0,
  starred: false,
  allTags: () => [],
})

const emit = defineEmits<{
  close: []
  'navigate-prev': []
  'navigate-next': []
  'toggle-star': [mediaId: number]
  'media-deleted': [mediaId: number]
  'media-rotated': [mediaId: number]
  'media-tags-changed': [mediaId: number, tags: TagItem[]]
}>()

const currentIndex = ref(props.startIndex)
const videoRef = ref<HTMLVideoElement | null>(null)
const thumbRefs = ref<Map<number, HTMLElement>>(new Map())
const previewStarBounce = ref(false)
const showDeleteConfirm = ref(false)
const deleteSourceFile = ref(false)
const rotationDegrees = ref(0)
const isRotating = ref(false)

function handleStarClick() {
  if (!currentItem.value) return
  previewStarBounce.value = true
  setTimeout(() => previewStarBounce.value = false, 300)
  emit('toggle-star', currentItem.value.id)
}

async function confirmDelete() {
  if (!currentItem.value) return
  const mediaId = currentItem.value.id
  try {
    const params: Record<string, any> = { delete_source: deleteSourceFile.value }
    if (props.messageId) params.message_id = props.messageId
    const res = await api.del<{ unlinked: boolean }>(`/media/${mediaId}`, params)
    emit('media-deleted', mediaId)

    toast.success(res.unlinked ? '已从当前消息移除' : '媒体已删除')
  } catch (error) {
    console.error('删除媒体失败:', error)
    toast.error('删除失败')
  }
  showDeleteConfirm.value = false
  deleteSourceFile.value = false
}

function openDetailPage() {
  if (!currentItem.value) return
  const id = currentItem.value.id
  emit('close')
  router.push(`/media/${id}`)
}

function openFileLocation() {
  if (!currentItem.value) return
  
  // 使用 Electron 的 shell API 打开文件位置
  if (window.electronAPI && window.electronAPI.showItemInFolder) {
    window.electronAPI.showItemInFolder(currentItem.value.file_path)
  } else {
    // 提供更友好的用户提示
    alert('无法打开文件位置：Electron shell API 不可用')
  }
}

function handleRotate() {
  rotationDegrees.value = (rotationDegrees.value + 90) % 360
}

async function confirmRotation() {
  if (!currentItem.value || rotationDegrees.value === 0) return
  isRotating.value = true
  try {
    await rotateMedia(currentItem.value.id, rotationDegrees.value)
    emit('media-rotated', currentItem.value.id)
    toast.success('旋转成功')
    rotationDegrees.value = 0
  } catch {
    toast.error('旋转失败')
  } finally {
    isRotating.value = false
  }
}

async function addMediaTag(tag: TagWithCount) {
  if (!currentItem.value) return
  const existing = currentItem.value.tags || []
  if (existing.some(t => t.id === tag.id)) return
  const newTags = [...existing, { id: tag.id, name: tag.name, category: tag.category }]
  try {
    await api.put(`/media/${currentItem.value.id}/tags`, { tag_ids: newTags.map(t => t.id) })
    currentItem.value.tags = newTags
    emit('media-tags-changed', currentItem.value.id, newTags)
  } catch {
    toast.error('添加标签失败')
  }
}

async function removeMediaTag(tagId: number) {
  if (!currentItem.value) return
  const newTags = (currentItem.value.tags || []).filter(t => t.id !== tagId)
  try {
    await api.put(`/media/${currentItem.value.id}/tags`, { tag_ids: newTags.map(t => t.id) })
    currentItem.value.tags = newTags
    emit('media-tags-changed', currentItem.value.id, newTags)
  } catch {
    toast.error('移除标签失败')
  }
}

const mediaTransformStyle = computed(() => {
  if (rotationDegrees.value === 0) return {}
  const isSwapped = rotationDegrees.value === 90 || rotationDegrees.value === 270
  return {
    transform: `rotate(${rotationDegrees.value}deg)${isSwapped ? ' scale(0.75)' : ''}`,
    transition: 'transform 0.2s ease',
  }
})

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

const isCurrentStarred = computed(() => currentItem.value?.starred ?? props.starred)

const totalItems = computed(() => props.items.length)

const canGoPrev = computed(() => {
  return currentIndex.value > 0
})

const canGoNext = computed(() => {
  return currentIndex.value < props.items.length - 1
})

const getMediaUrl = (item: MessageMediaItem) => {
  // 对 URL 进行编码处理，特别是对 # 字符进行编码
  return item.file_path.replace(/#/g, '%23')
}

const close = () => {
  if (videoRef.value) {
    videoRef.value.pause()
  }
  rotationDegrees.value = 0
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

watch(() => props.items.length, (newLen) => {
  if (newLen === 0) {
    close()
  } else if (currentIndex.value >= newLen) {
    currentIndex.value = newLen - 1
  }
})

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
  rotationDegrees.value = 0
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
