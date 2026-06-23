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
            <template v-if="!minimal">
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
              @click="triggerReplace"
              :disabled="isReplacing"
              class="p-2 text-white hover:bg-white/10 rounded-full transition-colors disabled:opacity-50"
              title="替换文件"
            >
              <svg v-if="!isReplacing" class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
              </svg>
              <svg v-else class="w-6 h-6 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
            <input
              ref="fileInput"
              type="file"
              accept="video/mp4,image/jpeg,image/png,image/gif"
              class="hidden"
              @change="onFileSelected"
            />
            <button
              v-if="currentItem"
              @click="openSuggestDrawer"
              class="p-2 text-white hover:bg-white/10 rounded-full transition-colors"
              title="智能 tag 建议"
            >
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5a2 2 0 011.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A2 2 0 013 12V7a4 4 0 014-4z" />
              </svg>
            </button>
            <button
              v-if="currentItem"
              @click="emitFindSimilar"
              class="p-2 text-white hover:bg-white/10 rounded-full transition-colors"
              title="查找相似媒体"
            >
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3l2 3h7a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V5z" />
                <circle cx="12" cy="13" r="3" stroke-width="2" />
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
            </template>

            <!-- 精简模式:详情(metadata) -->
            <button
              v-if="minimal && currentItem"
              @click="emit('info', currentItem)"
              class="p-2 text-white hover:bg-white/10 rounded-full transition-colors"
              title="详情"
            >
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </button>
            <!-- 精简模式:删除(含源文件,宿主确认) -->
            <button
              v-if="minimal && currentItem"
              @click="emit('delete', currentItem)"
              class="p-2 text-white/70 hover:text-red-400 hover:bg-white/10 rounded-full transition-colors"
              title="删除(含源文件)"
            >
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
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
            <Transition :name="transitionName" mode="out-in">
              <div class="relative" :key="currentItem?.id ?? -1">
                <video
                  v-if="currentItem && isVideo(currentItem.mime_type) && !showFallback"
                  ref="videoRef"
                  :src="getMediaUrl(currentItem)"
                  class="max-w-[90vw] max-h-[70vh] rounded-lg shadow-2xl"
                  :style="mediaTransformStyle"
                  controls
                  playsinline
                  loop
                  autoplay
                  @error="handleMediaError"
                ></video>

                <img
                  v-else-if="currentItem && isImage(currentItem.mime_type) && !showFallback"
                  :src="getMediaUrl(currentItem)"
                  :alt="`Media ${currentIndex + 1}`"
                  class="max-w-[90vw] max-h-[70vh] object-contain rounded-lg shadow-2xl"
                  :style="mediaTransformStyle"
                  @error="handleMediaError"
                />

                <!-- 文件无法访问时,展示缩略图 -->
                <div v-else-if="currentItem && showFallback" class="relative">
                  <img
                    :src="resolveThumb(currentItem)"
                    :alt="`Media ${currentIndex + 1} (缩略图)`"
                    class="max-w-[90vw] max-h-[70vh] object-contain rounded-lg shadow-2xl"
                    :style="mediaTransformStyle"
                  />
                  <div class="absolute bottom-2 left-1/2 -translate-x-1/2 px-3 py-1 bg-black/60 text-white/90 text-xs rounded-full backdrop-blur-sm">
                    文件无法访问,显示缩略图
                  </div>
                </div>
              </div>
            </Transition>

            <!-- Media tags -->
            <div v-if="currentItem && !minimal" class="flex items-center gap-1.5 flex-wrap justify-center">
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
        <div v-if="items.length >= 1" class="px-4 pb-4 pt-2 relative z-10 flex justify-center">
          <TransitionGroup
            tag="div"
            name="thumb"
            class="relative overflow-hidden"
            :style="{ width: thumbStripWidth, height: '48px' }"
          >
            <button
              v-for="entry in visibleThumbs"
              :key="entry.item.id"
              :ref="(el) => entry.kind === 'current' && setThumbRef(entry.idx, el as HTMLElement | null)"
              @click="onThumbClick(entry)"
              class="absolute top-0 w-12 h-12 rounded-md overflow-hidden border-2 transition-all duration-200"
              :style="{ left: `${(thumbOffset(entry) + THUMB_WINDOW) * 54}px` }"
              :class="entry.kind === 'current' && entry.idx === currentIndex
                ? 'border-white scale-110 shadow-lg shadow-white/20 z-10'
                : entry.kind === 'current'
                  ? 'border-transparent opacity-50 hover:opacity-80'
                  : 'border-transparent opacity-25 hover:opacity-60 scale-90'"
              :title="entry.kind === 'peek-prev' ? '上一个消息' : entry.kind === 'peek-next' ? '下一个消息' : ''"
            >
              <img
                v-if="isImage(entry.item.mime_type)"
                :src="resolveThumb(entry.item)"
                class="w-full h-full object-cover"
              />
              <div
                v-else-if="isVideo(entry.item.mime_type)"
                class="w-full h-full relative bg-gray-800"
              >
                <img
                  :src="resolveThumb(entry.item)"
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
          </TransitionGroup>
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
  <!-- Smart tag suggestion drawer -->
  <TagSuggestDrawer
    :is-open="suggestDrawerOpen"
    :media-id="suggestDrawerMediaId"
    @close="suggestDrawerOpen = false"
    @tags-applied="onSmartTagsApplied"
  />
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import type { MessageMediaItem, TagWithCount, TagItem, Media } from '../types'
import { isVideo, isImage, resolveThumb, resolveMediaUrl, rotateMedia } from '../utils/media'
import { api } from '../composables/useApi'
import { useToast } from '../composables/useToast'
import TagPickerPopover from './TagPickerPopover.vue'
import TagSuggestDrawer from './TagSuggestDrawer.vue'

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
  prevPeekItems?: MessageMediaItem[]
  nextPeekItems?: MessageMediaItem[]
  /**
   * 精简模式:隐藏所有针对 Media 资产的操作(收藏/删除/旋转/替换/智能 tag/找相似/详情页/标签编辑),
   * 只保留 导航 + 预览 + 打开文件位置 + 关闭。用于 Scan 这类基于 fs_entry 的只读浏览
   * —— 此时 item.id 是 fs_entry id 而非 media id,打 /media 接口是错的。
   */
  minimal?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  startIndex: 0,
  starred: false,
  minimal: false,
  allTags: () => [],
  prevPeekItems: () => [],
  nextPeekItems: () => [],
})

const emit = defineEmits<{
  close: []
  'navigate-prev': []
  'navigate-next': []
  'toggle-star': [mediaId: number]
  'media-deleted': [mediaId: number]
  'media-rotated': [mediaId: number]
  'media-replaced': [mediaId: number]
  'media-tags-changed': [mediaId: number, tags: TagItem[]]
  'find-similar': [mediaId: number]
  /** 精简模式下点「详情」按钮 —— 宿主自行决定展示什么(如 ScanDetailModal) */
  info: [item: MessageMediaItem]
  /** 精简模式下点「删除」按钮 —— 宿主自行确认 + 调用对应删除接口(如 /scan/{id}) */
  delete: [item: MessageMediaItem]
}>()

const currentIndex = ref(props.startIndex)
const videoRef = ref<HTMLVideoElement | null>(null)
const thumbRefs = ref<Map<number, HTMLElement>>(new Map())
const transitionName = ref<'slide-left' | 'slide-right'>('slide-left')
const THUMB_WINDOW = 5
const previewStarBounce = ref(false)
const showDeleteConfirm = ref(false)
const deleteSourceFile = ref(false)
const rotationDegrees = ref(0)
const isRotating = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)
const isReplacing = ref(false)
const mediaCacheBust = ref<Record<number, number>>({})
const suggestDrawerOpen = ref(false)
const suggestDrawerMediaId = ref<number | null>(null)
// per-item 跟踪加载失败:用于 file:// / HTTP 媒体文件无法访问时回退到缩略图
const loadFailedIds = ref<Set<number>>(new Set())

function handleMediaError(e: Event) {
  if (!currentItem.value) return
  console.warn('[MediaPreview] 媒体加载失败,回退到缩略图:', currentItem.value.id, e)
  const next = new Set(loadFailedIds.value)
  next.add(currentItem.value.id)
  loadFailedIds.value = next
}

const showFallback = computed(() => {
  if (!currentItem.value) return false
  return loadFailedIds.value.has(currentItem.value.id)
})

function openSuggestDrawer() {
  if (!currentItem.value) return
  suggestDrawerMediaId.value = currentItem.value.id
  suggestDrawerOpen.value = true
}

function emitFindSimilar() {
  if (!currentItem.value) return
  emit('find-similar', currentItem.value.id)
  emit('close')
}

function onSmartTagsApplied(mediaId: number, tags: TagItem[]) {
  if (currentItem.value && currentItem.value.id === mediaId) {
    currentItem.value.tags = tags
  }
  emit('media-tags-changed', mediaId, tags)
}

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
    const path = (currentItem.value as any).local_file_path
    if (!path) {
      alert('文件未在已知 repository 中,无法打开文件夹')
      return
    }
    window.electronAPI.showItemInFolder(path)
  } else {
    // 提供更友好的用户提示
    alert('无法打开文件位置：Electron shell API 不可用')
  }
}

function handleRotate() {
  rotationDegrees.value = (rotationDegrees.value + 90) % 360
}

function triggerReplace() {
  if (isReplacing.value) return
  fileInput.value?.click()
}

async function onFileSelected(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file || !currentItem.value) return

  isReplacing.value = true
  const mediaId = currentItem.value.id
  try {
    const form = new FormData()
    form.append('file', file)
    const updated = await api.post<Media>(`/media/${mediaId}/replace`, form)
    const target = props.items[currentIndex.value]
    if (target && target.id === mediaId) {
      const ts = Date.now()
      target.id = updated.id
      target.file_path = updated.file_path
      ;(target as any).repo_id = (updated as any).repo_id
      ;(target as any).local_file_path = (updated as any).local_file_path
      ;(target as any).local_thumb_path = (updated as any).local_thumb_path
      target.file_url = updated.file_url
      target.thumb_url = (updated.thumb_url || '').split('?')[0] + `?t=${ts}`
      target.mime_type = updated.mime_type
      target.width = updated.width
      target.height = updated.height
      target.duration_ms = updated.duration_ms
      mediaCacheBust.value = { ...mediaCacheBust.value, [updated.id]: ts }
    }
    emit('media-replaced', mediaId)
    if (updated.id !== mediaId) {
      toast.success('替换成功（已合并到已有媒体）')
    } else {
      toast.success('替换成功')
    }
  } catch (err: any) {
    toast.error(err?.message || '替换失败')
  } finally {
    isReplacing.value = false
  }
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
  // 优先用本机绝对路径(Electron file://),HTTP URL 兜底
  const url = resolveMediaUrl(item)
  if (!url) return ''
  const bust = mediaCacheBust.value[item.id]
  return bust ? `${url}${url.includes('?') ? '&' : '?'}t=${bust}` : url
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
    transitionName.value = 'slide-right'
    currentIndex.value--
  } else {
    emit('navigate-prev')
  }
}

const next = () => {
  if (canGoNext.value) {
    transitionName.value = 'slide-left'
    currentIndex.value++
  } else {
    emit('navigate-next')
  }
}

const goToIndex = (idx: number) => {
  if (idx === currentIndex.value) return
  transitionName.value = idx > currentIndex.value ? 'slide-left' : 'slide-right'
  currentIndex.value = idx
}

const thumbOffset = (entry: ThumbEntry): number => {
  if (entry.kind === 'current') return entry.idx - currentIndex.value
  return entry.offset
}

const onThumbClick = (entry: ThumbEntry) => {
  if (entry.kind === 'current') {
    goToIndex(entry.idx)
  } else if (entry.kind === 'peek-prev') {
    emit('navigate-prev')
  } else {
    emit('navigate-next')
  }
}

type ThumbEntry =
  | { kind: 'current'; item: MessageMediaItem; idx: number }
  | { kind: 'peek-prev'; item: MessageMediaItem; offset: number }
  | { kind: 'peek-next'; item: MessageMediaItem; offset: number }

const PEEK_GAP = 2

const visibleThumbs = computed<ThumbEntry[]>(() => {
  const out: ThumbEntry[] = []
  const len = props.items.length
  for (let off = -THUMB_WINDOW; off <= THUMB_WINDOW; off++) {
    const idx = currentIndex.value + off
    if (idx >= 0 && idx < len) {
      out.push({ kind: 'current', item: props.items[idx], idx })
    }
  }
  // peek-prev: 占用最左侧槽位，与当前 items 至少留 PEEK_GAP 空白
  const leftCurrentMost = -Math.min(currentIndex.value, THUMB_WINDOW)
  const peekPrevStart = leftCurrentMost - PEEK_GAP - 1
  for (let s = 0; peekPrevStart - s >= -THUMB_WINDOW; s++) {
    const offset = peekPrevStart - s
    const peekIdx = props.prevPeekItems.length - 1 - s
    if (peekIdx < 0) break
    out.push({ kind: 'peek-prev', item: props.prevPeekItems[peekIdx], offset })
  }
  const rightCurrentMost = Math.min(len - 1 - currentIndex.value, THUMB_WINDOW)
  const peekNextStart = rightCurrentMost + PEEK_GAP + 1
  for (let s = 0; peekNextStart + s <= THUMB_WINDOW; s++) {
    const offset = peekNextStart + s
    const peekIdx = s
    if (peekIdx >= props.nextPeekItems.length) break
    out.push({ kind: 'peek-next', item: props.nextPeekItems[peekIdx], offset })
  }
  return out
})

// 48px thumb + 6px gap; (2*WINDOW+1) slots 固定宽度，当前 thumb 始终居中。
const thumbStripWidth = computed(() => {
  const slots = THUMB_WINDOW * 2 + 1
  return `${slots * 48 + (slots - 1) * 6}px`
})

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

watch(() => props.startIndex, (newIndex) => {
  if (!props.isOpen) return
  const clamped = Math.max(0, Math.min(newIndex, props.items.length - 1))
  transitionName.value = clamped > currentIndex.value ? 'slide-left' : 'slide-right'
  currentIndex.value = clamped
}, { flush: 'post' })

watch(() => props.isOpen, async (newValue) => {
  if (newValue) {
    currentIndex.value = props.startIndex
    transitionName.value = 'slide-left'
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

.slide-left-enter-active,
.slide-left-leave-active,
.slide-right-enter-active,
.slide-right-leave-active {
  transition: transform 180ms ease-out, opacity 180ms ease-out;
}
.slide-left-enter-from {
  transform: translateX(24px);
  opacity: 0;
}
.slide-left-leave-to {
  transform: translateX(-24px);
  opacity: 0;
}
.slide-right-enter-from {
  transform: translateX(-24px);
  opacity: 0;
}
.slide-right-leave-to {
  transform: translateX(24px);
  opacity: 0;
}

.thumb-enter-active,
.thumb-leave-active {
  transition: opacity 200ms ease-out, transform 200ms ease-out, left 200ms ease-out;
}
.thumb-leave-active {
  pointer-events: none;
}
.thumb-enter-from {
  opacity: 0;
  transform: translateX(24px) scale(0.7);
}
.thumb-leave-to {
  opacity: 0;
  transform: translateX(-24px) scale(0.7);
}
</style>
