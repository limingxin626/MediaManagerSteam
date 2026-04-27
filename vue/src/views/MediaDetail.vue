<template>
  <div class="fixed inset-0 z-[90] flex bg-black overflow-hidden">
    <!-- Loading -->
    <div v-if="isLoading" class="flex-1 flex items-center justify-center">
      <svg class="animate-spin h-12 w-12 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
      </svg>
    </div>

    <template v-else-if="mediaItem">
      <!-- Left: Player -->
      <div class="flex-1 relative min-w-0">
        <!-- Floating Header -->
        <div class="absolute top-0 left-0 right-0 z-20 bg-gradient-to-b from-black/70 to-transparent p-4">
          <div class="flex items-center justify-between">
            <button
              @click="closeDetail"
              class="flex items-center gap-2 text-white hover:text-gray-300 transition-colors"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              <span>关闭</span>
            </button>
            <h1 class="text-lg font-semibold text-white truncate max-w-[60%]">{{ displayName }}</h1>
            <div class="w-16"></div>
          </div>
        </div>

        <!-- Video / Image -->
        <div class="w-full h-full flex items-center justify-center">
          <div
            v-if="isVideo(mediaItem.mime_type)"
            class="w-full h-full plyr-container"
          >
            <video
              ref="videoPlayer"
              class="w-full h-full"
              playsinline
              controls
              crossorigin="anonymous"
            >
              <source :src="mediaSrc" :type="mediaItem.mime_type || 'video/mp4'" />
            </video>
          </div>

          <img
            v-else-if="isImage(mediaItem.mime_type)"
            :src="mediaSrc"
            :alt="displayName"
            class="max-w-full max-h-full object-contain"
          />
        </div>
      </div>

      <!-- Middle: Previews -->
      <div class="w-64 border-l border-gray-800 overflow-y-auto bg-gray-950">
        <div class="p-4">
          <h3 class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">预览片段</h3>
          <VideoPreviewStrip
            v-if="isVideo(mediaItem.mime_type)"
            :video-media-id="mediaItem.id"
            :previews="previews"
            :video-el="videoPlayer"
            @update:previews="previews = $event"
          />
          <p v-else class="text-sm text-gray-500">仅视频支持预览片段</p>
        </div>
      </div>

      <!-- Right: Info Panel -->
      <div class="w-80 overflow-y-auto bg-gray-950 border-l border-gray-800">
        <div class="p-6 space-y-6">
          <!-- Action Buttons -->
          <div class="space-y-3">
            <button
              @click="openMediaFolder"
              class="w-full flex items-center justify-center gap-2 px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-colors"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
              </svg>
              打开文件夹
            </button>
          </div>

          <!-- Basic Info -->
          <div>
            <h3 class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">基本信息</h3>
            <div class="space-y-3">
              <div class="flex justify-between items-center">
                <span class="text-xs text-gray-400">ID</span>
                <span class="text-sm font-medium text-white truncate ml-3">{{ mediaItem.id }}</span>
              </div>
              <div class="flex justify-between items-center">
                <span class="text-xs text-gray-400">评分</span>
                <span class="text-sm font-medium text-white truncate ml-3">{{ mediaItem.rating }}</span>
              </div>
              <div class="flex justify-between items-center">
                <span class="text-xs text-gray-400">收藏</span>
                <span class="text-sm font-medium text-white truncate ml-3">{{ mediaItem.starred ? '是' : '否' }}</span>
              </div>
              <div class="flex justify-between items-center">
                <span class="text-xs text-gray-400">浏览次数</span>
                <span class="text-sm font-medium text-white truncate ml-3">{{ mediaItem.view_count }}</span>
              </div>
              <div class="flex justify-between items-center">
                <span class="text-xs text-gray-400">创建时间</span>
                <span class="text-sm font-medium text-white truncate ml-3">{{ formatDate(mediaItem.created_at) }}</span>
              </div>
            </div>
          </div>

          <!-- File Info -->
          <div>
            <h3 class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">文件信息</h3>
            <div class="bg-gray-900 rounded-xl p-4 space-y-2">
              <div class="flex justify-between items-center">
                <span class="text-xs text-gray-400">文件大小</span>
                <span class="text-sm font-medium text-white">{{ formatFileSize(mediaItem.file_size) }}</span>
              </div>
              <div v-if="mediaItem.width && mediaItem.height" class="flex justify-between items-center">
                <span class="text-xs text-gray-400">分辨率</span>
                <span class="text-sm font-medium text-white">{{ mediaItem.width }} × {{ mediaItem.height }}</span>
              </div>
              <div v-if="mediaItem.duration_ms" class="flex justify-between items-center">
                <span class="text-xs text-gray-400">时长</span>
                <span class="text-sm font-medium text-white">{{ formatDuration(mediaItem.duration_ms) }}</span>
              </div>
              <div v-if="mediaItem.mime_type" class="flex justify-between items-center">
                <span class="text-xs text-gray-400">类型</span>
                <span class="text-sm font-medium text-white">{{ mediaItem.mime_type }}</span>
              </div>
              <div class="flex flex-col gap-1 pt-2 border-t border-gray-800">
                <span class="text-xs text-gray-400">文件路径</span>
                <span class="text-xs font-mono text-gray-200 break-all">{{ mediaItem.file_path }}</span>
              </div>
            </div>
          </div>

          <!-- Tags -->
          <div>
            <div class="flex items-center justify-between mb-3">
              <h3 class="text-xs font-semibold text-gray-400 uppercase tracking-wider">标签</h3>
              <TagPickerPopover
                v-if="allTags.length"
                :all-tags="allTags"
                :message-tags="mediaItem.tags || []"
                @select="addMediaTag"
              />
            </div>
            <div class="flex flex-wrap gap-2">
              <span
                v-for="tag in (mediaItem.tags || [])"
                :key="tag.id"
                @click="removeMediaTag(tag.id)"
                class="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium bg-indigo-900/50 text-indigo-200 hover:bg-red-500/40 hover:line-through cursor-pointer transition-colors"
                title="点击移除"
              >
                #{{ tag.name }}
              </span>
              <p v-if="!mediaItem.tags?.length" class="text-sm text-gray-500">暂无标签</p>
            </div>
          </div>

          <!-- Screenshot Capture (videos only) -->
          <VideoScreenshotCapture
            v-if="isVideo(mediaItem.mime_type)"
            :video-media-id="mediaItem.id"
            :video-el="videoPlayer"
            @preview-added="onPreviewAdded"
          />
        </div>
      </div>
    </template>

    <!-- Not found -->
    <div v-else class="flex-1 flex items-center justify-center text-white">
      媒体不存在
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import type { Media, TagWithCount, VideoPreviewItem } from '../types'
import { api } from '../composables/useApi'
import { useToast } from '../composables/useToast'
import { isVideo, isImage, resolveUrl, formatDuration } from '../utils/media'
import TagPickerPopover from '../components/TagPickerPopover.vue'
import VideoPreviewStrip from '../components/VideoPreviewStrip.vue'
import VideoScreenshotCapture from '../components/VideoScreenshotCapture.vue'
import Plyr from 'plyr'
import 'plyr/dist/plyr.css'

const props = defineProps<{ mediaId: number }>()

const router = useRouter()
const toast = useToast()

const mediaItem = ref<Media | null>(null)
const isLoading = ref(true)
const allTags = ref<TagWithCount[]>([])
const previews = ref<VideoPreviewItem[]>([])
const videoPlayer = ref<HTMLVideoElement | null>(null)
const player = ref<Plyr | null>(null)

const displayName = computed(() => {
  const path = mediaItem.value?.file_path || ''
  const m = path.match(/[^\\/]+$/)
  return m ? m[0] : ''
})

const mediaSrc = computed(() => {
  if (!mediaItem.value) return ''
  return resolveUrl(mediaItem.value.file_url)
})

const formatFileSize = (bytes: number | null): string => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

const formatDate = (iso: string): string => {
  try {
    return new Date(iso).toLocaleString('zh-CN')
  } catch {
    return iso
  }
}

const loadMedia = async () => {
  isLoading.value = true
  try {
    mediaItem.value = await api.get<Media>(`/media/${props.mediaId}`)
  } catch {
    mediaItem.value = null
    toast.error('加载媒体失败')
  } finally {
    isLoading.value = false
  }
}

const loadPreviews = async () => {
  if (!mediaItem.value || !isVideo(mediaItem.value.mime_type)) {
    previews.value = []
    return
  }
  try {
    previews.value = await api.get<VideoPreviewItem[]>(`/media/${mediaItem.value.id}/previews`)
  } catch {
    previews.value = []
  }
}

const loadTags = async () => {
  try {
    allTags.value = await api.get<TagWithCount[]>('/tags?has_media=true')
  } catch { /* ignore */ }
}

const closeDetail = () => {
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push('/media')
  }
}

const openMediaFolder = () => {
  if (!mediaItem.value) return
  if (window.electronAPI?.showItemInFolder) {
    window.electronAPI.showItemInFolder(mediaItem.value.file_path)
  } else {
    toast.info('Electron 环境下才能打开文件夹')
  }
}

const addMediaTag = async (tag: TagWithCount) => {
  if (!mediaItem.value) return
  const existing = mediaItem.value.tags || []
  if (existing.some(t => t.id === tag.id)) return
  const newTags = [...existing, { id: tag.id, name: tag.name, category: tag.category }]
  try {
    await api.put(`/media/${mediaItem.value.id}/tags`, { tag_ids: newTags.map(t => t.id) })
    mediaItem.value.tags = newTags
  } catch {
    toast.error('添加标签失败')
  }
}

const removeMediaTag = async (tagId: number) => {
  if (!mediaItem.value) return
  const newTags = (mediaItem.value.tags || []).filter(t => t.id !== tagId)
  try {
    await api.put(`/media/${mediaItem.value.id}/tags`, { tag_ids: newTags.map(t => t.id) })
    mediaItem.value.tags = newTags
  } catch {
    toast.error('移除标签失败')
  }
}

const onPreviewAdded = (item: VideoPreviewItem) => {
  previews.value = [...previews.value, item].sort((a, b) => a.frame_ms - b.frame_ms)
}

const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Escape') {
    e.preventDefault()
    closeDetail()
    return
  }
  if (!player.value || !mediaItem.value || !isVideo(mediaItem.value.mime_type)) return
  const skip = 5
  if (e.key === 'ArrowLeft') {
    e.preventDefault()
    player.value.rewind(skip)
  } else if (e.key === 'ArrowRight') {
    e.preventDefault()
    player.value.forward(skip)
  }
}

const destroyPlayer = () => {
  if (player.value) {
    try { player.value.destroy() } catch { /* ignore */ }
    player.value = null
  }
}

const initPlayer = async () => {
  destroyPlayer()
  await nextTick()
  if (!videoPlayer.value) return
  player.value = new Plyr(videoPlayer.value, {
    controls: ['play-large', 'play', 'progress', 'current-time', 'mute', 'volume', 'settings', 'pip', 'fullscreen'],
    speed: { selected: 1, options: [0.5, 0.75, 1, 1.25, 1.5, 2] },
    autoplay: true,
    clickToPlay: true,
  })
  player.value.play()?.catch(() => { /* autoplay 可能被阻止 */ })
}

watch([isLoading, () => mediaItem.value?.mime_type], async ([loading, mime]) => {
  if (!loading && isVideo(mime ?? null)) {
    await initPlayer()
    loadPreviews()
  } else {
    destroyPlayer()
    previews.value = []
  }
})

watch(() => props.mediaId, () => {
  loadMedia()
})

onMounted(() => {
  loadMedia()
  loadTags()
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  destroyPlayer()
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.plyr-container {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.plyr-container :deep(.plyr) {
  width: 100%;
  height: 100%;
  max-height: 100vh;
  border-radius: 0;
}

.plyr-container :deep(.plyr video) {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
</style>
