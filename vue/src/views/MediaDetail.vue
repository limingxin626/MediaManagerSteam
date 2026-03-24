<template>
  <div class="flex flex-1 h-full overflow-hidden">
    <!-- Loading State -->
    <div v-if="isLoading" class="flex-1 flex items-center justify-center bg-gray-50 dark:bg-dark-bg">
      <svg class="animate-spin h-12 w-12 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
      </svg>
    </div>

    <!-- Main Content -->
    <div v-else-if="mediaItem" class="flex flex-1 h-full overflow-hidden">
      <!-- Left: Video/Image Player -->
      <div class="flex-1 relative">
        <!-- Floating Header -->
        <div class="absolute top-0 left-0 right-0 z-20 bg-gradient-to-b p-4">
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
            <h1 class="text-xl font-semibold text-white">{{ mediaItem.name }}</h1>
            <div class="w-16"></div>
          </div>
        </div>

        <!-- Video/Image Player -->
        <div class="w-full h-full flex items-center justify-center relative group">
          <!-- Previous Button -->
          <button 
            @click="goToPreviousMedia"
            class="absolute left-4 top-1/2 -translate-y-1/2 z-30 w-12 h-12 bg-black/50 hover:bg-black/70 backdrop-blur-sm rounded-full flex items-center justify-center text-white transition-all opacity-0 group-hover:opacity-100"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
            </svg>
          </button>

          <!-- Video Player -->
          <div 
            v-if="mediaItem.type === 'VIDEO'"
            class="w-full h-full flex items-center justify-center plyr-container"
          >
            <video 
              ref="videoPlayer"
              class="w-full h-full"
              playsinline
              controls
              crossorigin="anonymous"
            >
              <source :src="videoSrc" type="video/mp4" />
            </video>
          </div>

          <!-- Image Display -->
          <img 
            v-else-if="mediaItem.type === 'IMAGE' || mediaItem.type === 'PREVIEW'"
            :src="imageSrc"
            :alt="mediaItem.name"
            class="w-full h-full object-contain"
            @error="handleImageError"
          />

          <!-- Next Button -->
          <button 
            @click="goToNextMedia"
            class="absolute right-4 top-1/2 -translate-y-1/2 z-30 w-12 h-12 bg-black/50 hover:bg-black/70 backdrop-blur-sm rounded-full flex items-center justify-center text-white transition-all opacity-0 group-hover:opacity-100"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Middle: Previews Panel -->
      <div class="w-72 border-gray-200 dark:border-gray-700 overflow-y-auto">
        <div class="p-4">
          <h3 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">预览 ({{ mediaItem.previews?.length || 0 }})</h3>
          <div v-if="mediaItem.previews && mediaItem.previews.length > 0" class="space-y-3">
            <PreviewCard
              v-for="preview in mediaItem.previews" 
              :key="preview.id"
              :preview="preview"
              @click="goToPreview"
            />
          </div>
        </div>
      </div>

      <!-- Right: Information Panel -->
      <div class="w-80 overflow-y-auto">
        <div class="p-6 space-y-6">
          <!-- Action Buttons -->
          <div class="space-y-3">
            <!-- Edit Button -->
            <button 
              @click="editMedia"
              class="w-full flex items-center justify-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
              编辑
            </button>
            
            <!-- Open Folder Button -->
            <button 
              @click="openMediaFolder"
              class="w-full flex items-center justify-center gap-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
              </svg>
              打开文件夹
            </button>
          </div>

          <!-- Description -->
          <div v-if="mediaItem.description" class="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4">
            <h3 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">描述</h3>
            <p class="text-gray-900 dark:text-white text-sm leading-relaxed">{{ mediaItem.description }}</p>
          </div>

          <!-- Basic Info Section -->
          <div>
            <h3 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">基本信息</h3>
            <div class="space-y-3">
              <!-- ID -->
              <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-lg bg-gray-100 dark:bg-gray-900/50 flex items-center justify-center flex-shrink-0">
                  <svg class="w-4 h-4 text-gray-600 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />
                  </svg>
                </div>
                <div class="min-w-0 flex-1">
                  <p class="text-xs text-gray-500 dark:text-gray-400">ID</p>
                  <p class="text-sm font-medium text-gray-900 dark:text-white truncate">{{ mediaItem.id }}</p>
                </div>
              </div>

              <!-- Group Information -->
              <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-lg bg-indigo-100 dark:bg-indigo-900/50 flex items-center justify-center flex-shrink-0">
                  <svg class="w-4 h-4 text-indigo-600 dark:text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                </div>
                <div class="min-w-0 flex-1">
                  <p class="text-xs text-gray-500 dark:text-gray-400">分组</p>
                  <p class="text-sm font-medium text-gray-900 dark:text-white truncate">{{ mediaGroup?.name || '未知分组' }}</p>
                </div>
              </div>

              <!-- Actor Information -->
              <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-lg bg-pink-100 dark:bg-pink-900/50 flex items-center justify-center flex-shrink-0">
                  <svg class="w-4 h-4 text-pink-600 dark:text-pink-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                </div>
                <div class="min-w-0 flex-1">
                  <p class="text-xs text-gray-500 dark:text-gray-400">演员</p>
                  <p class="text-sm font-medium text-gray-900 dark:text-white truncate">{{ mediaItem.actor?.name || '未知演员' }}</p>
                </div>
              </div>

              <!-- Rating -->
              <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-lg bg-yellow-100 dark:bg-yellow-900/50 flex items-center justify-center flex-shrink-0">
                  <svg class="w-4 h-4 text-yellow-600 dark:text-yellow-400" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                  </svg>
                </div>
                <div class="min-w-0 flex-1">
                  <p class="text-xs text-gray-500 dark:text-gray-400">评分</p>
                  <p class="text-sm font-medium text-gray-900 dark:text-white truncate">{{ mediaItem.rating !== null ? mediaItem.rating : '未评分' }}</p>
                </div>
              </div>

              <!-- Date -->
              <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-lg bg-green-100 dark:bg-green-900/50 flex items-center justify-center flex-shrink-0">
                  <svg class="w-4 h-4 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
                <div class="min-w-0 flex-1">
                  <p class="text-xs text-gray-500 dark:text-gray-400">日期</p>
                  <p class="text-sm font-medium text-gray-900 dark:text-white truncate">{{ mediaItem.date || '未知' }}</p>
                </div>
              </div>
            </div>
          </div>

          <!-- File Information -->
          <div>
            <h3 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">文件信息</h3>
            <div class="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4 space-y-2">
              <div class="flex justify-between items-center">
                <span class="text-xs text-gray-500 dark:text-gray-400">文件大小</span>
                <span class="text-sm font-medium text-gray-900 dark:text-white">{{ formatFileSize(mediaItem.file_size) }}</span>
              </div>
              <div v-if="mediaItem.width && mediaItem.height" class="flex justify-between items-center">
                <span class="text-xs text-gray-500 dark:text-gray-400">分辨率</span>
                <span class="text-sm font-medium text-gray-900 dark:text-white">{{ mediaItem.width }} x {{ mediaItem.height }}</span>
              </div>
              <div v-if="mediaItem.duration" class="flex justify-between items-center">
                <span class="text-xs text-gray-500 dark:text-gray-400">时长</span>
                <span class="text-sm font-medium text-gray-900 dark:text-white">{{ formatDuration(mediaItem.duration) }}</span>
              </div>
              <div class="flex flex-col gap-1">
                <span class="text-xs text-gray-500 dark:text-gray-400">文件路径</span>
                <span class="text-xs font-medium text-gray-900 dark:text-white break-all">{{ mediaItem.file_path }}</span>
              </div>
            </div>
          </div>

          <!-- Tags -->
          <div>
            <div class="flex items-center justify-between mb-3">
              <h3 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">标签</h3>
              <button
                @click="showAddTagModal = true"
                class="text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 dark:hover:text-indigo-300 text-xs font-medium"
              >
                + 添加
              </button>
            </div>
            <div class="flex flex-wrap gap-2">
              <div 
                v-for="tag in currentMediaTags" 
                :key="tag.id"
                class="inline-flex items-center gap-1 px-3 py-1.5 rounded-full text-sm font-medium bg-indigo-100 dark:bg-indigo-900/50 text-indigo-800 dark:text-indigo-300"
              >
                <span>{{ tag.name }}</span>
                <button
                  @click="removeTag(tag.id)"
                  class="ml-1 p-0.5 rounded-full hover:bg-indigo-200 dark:hover:bg-indigo-800 transition-colors"
                  title="删除标签"
                >
                  <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <p v-if="currentMediaTags.length === 0" class="text-sm text-gray-500 dark:text-gray-400">暂无标签</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Edit Modal -->
    <MediaEditModal
      :is-open="showEditModal"
      title="编辑媒体信息"
      :form-data="formData"
      @close="showEditModal = false"
      @save="handleSaveMedia"
    />

    <!-- Add Tag Modal -->
    <MediaTagModal
      :is-open="showAddTagModal"
      :current-tags="currentMediaTags"
      @close="showAddTagModal = false"
      @add-tag="addTag"
      @save-tags="handleSaveTags"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTheme } from '../composables/useTheme'
import { API_BASE_URL } from '../utils/constants'
import MediaEditModal from '../components/MediaEditModal.vue'
import MediaTagModal from '../components/MediaTagModal.vue'
import PreviewCard from '../components/PreviewCard.vue'
import Plyr from 'plyr'
import 'plyr/dist/plyr.css'

interface Props {
  mediaId: number
}

const props = defineProps<Props>()
const emit = defineEmits<{
  close: []
  selectMedia: [id: number]
}>()

interface Group {
  id: number
  name: string
  description: string
}

interface Actor {
  id: number
  name: string
  description: string
  avatar: string
}

interface Preview {
  id: number
  name: string
  start_time: number | null
  end_time: number | null
  timestamp: number | null
}

interface Media {
  id: number
  name: string
  type: 'VIDEO' | 'IMAGE' | "PREVIEW"
  description: string
  file_path: string
  file_size: number
  duration: number | null
  resolution: string | null
  thumbnail_path: string | null
  file_hash: string | null
  width: number | null
  height: number | null
  rating: number | null
  view_count: number
  group_id: number
  timestamp: number | null
  start_time: number | null
  end_time: number | null
  date: string
  parent_id: number | null
  actor_id: number | null
  created_at: string
  updated_at: string
  actor: Actor | null
  group: Group | null
  tags: Tag[]
  previews: Preview[]
}

interface Tag {
  id: number
  name: string
  category: string
}

const fetchMediaDetail = async (id: number): Promise<Media | null> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/media/${id}/detail`)
    if (!response.ok) {
      throw new Error('获取媒体详情失败')
    }
    return await response.json()
  } catch (error) {
    console.error('获取媒体详情失败:', error)
    return null
  }
}

const fetchPreviousMediaId = async (mediaId: number): Promise<number | null> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/media/${mediaId}/prev`)
    if (!response.ok) {
      throw new Error('获取上一个媒体失败')
    }
    const data = await response.json()
    return data.id || null
  } catch (error) {
    console.error('获取上一个媒体失败:', error)
    return null
  }
}

const fetchNextMediaId = async (mediaId: number): Promise<number | null> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/media/${mediaId}/next`)
    if (!response.ok) {
      throw new Error('获取下一个媒体失败')
    }
    const data = await response.json()
    return data.id || null
  } catch (error) {
    console.error('获取下一个媒体失败:', error)
    return null
  }
}

const updateMedia = async (id: number, data: { name: string; description: string; group_name: string }): Promise<boolean> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/media/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    })
    if (!response.ok) {
      throw new Error('更新媒体失败')
    }
    return true
  } catch (error) {
    console.error('更新媒体失败:', error)
    return false
  }
}

const addTagToMedia = async (mediaId: number, tagId: number): Promise<boolean> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/media/${mediaId}/add/${tagId}`, {
      method: 'POST',
    })
    if (!response.ok) {
      throw new Error('添加标签失败')
    }
    return true
  } catch (error) {
    console.error('添加标签失败:', error)
    return false
  }
}

const removeTagFromMedia = async (mediaId: number, tagId: number): Promise<boolean> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/media/${mediaId}/remove/${tagId}`, {
      method: 'DELETE'
    })
    if (!response.ok) {
      throw new Error('删除标签失败')
    }
    return true
  } catch (error) {
    console.error('删除标签失败:', error)
    return false
  }
}

const route = useRoute()
const router = useRouter()
const { initTheme } = useTheme()

const showEditModal = ref(false)
const showAddTagModal = ref(false)
const formData = ref({
  name: '',
  description: '',
  group_name: ''
})

const videoPlayer = ref<HTMLVideoElement | null>(null)
const player = ref<Plyr | null>(null)

const mediaId = computed(() => props.mediaId)
const mediaItem = ref<Media | null>(null)
const mediaGroup = ref<Group | null>(null)
const currentMediaTags = ref<Tag[]>([])
const isLoading = ref(true)

const loadMediaData = async () => {
  isLoading.value = true
  try {
    const mediaData = await fetchMediaDetail(mediaId.value)
    console.log('Media data loaded:', mediaData)
    if (mediaData) {
      mediaItem.value = mediaData
      mediaGroup.value = mediaData.group
      currentMediaTags.value = mediaData.tags || []
    }
  } finally {
    isLoading.value = false
  }
}

const videoSrc = computed(() => {
  if (!mediaItem.value) return ''
  return `file://${mediaItem.value.file_path}`
})

const imageSrc = computed(() => {
  if (!mediaItem.value) return ''
  return `file://${mediaItem.value.file_path}`
})

const closeDetail = () => {
  emit('close')
}

const goToPreviousMedia = async () => {
  if (!mediaItem.value) return
  
  const previousId = await fetchPreviousMediaId(mediaItem.value.id)
  if (previousId) {
    emit('selectMedia', previousId)
  }
}

const goToNextMedia = async () => {
  if (!mediaItem.value) return
  
  const nextId = await fetchNextMediaId(mediaItem.value.id)
  if (nextId) {
    emit('selectMedia', nextId)
  }
}

const goToPreview = (preview: Preview) => {
  if (mediaItem.value?.type === 'VIDEO' && preview.start_time !== null) {
    if (videoPlayer.value) {
      videoPlayer.value.currentTime = preview.start_time
      videoPlayer.value.play()
    }
  }
}

const openMediaFolder = () => {
  if (!mediaItem.value) return
  
  try {
    // 提取文件路径
    const filePath = mediaItem.value.file_path
    
    // 使用 Electron 的 shell 模块在文件夹中显示文件
    if (window.require) {
      const { shell } = window.require('electron')
      // 直接在文件夹中显示文件（会自动打开文件夹）
      shell.showItemInFolder(filePath)
    } else {
      // 降级方案：尝试使用 file:// URL
      const folderPath = filePath.substring(0, filePath.lastIndexOf('\\'))
      const folderUrl = `file://${folderPath}`
      window.open(folderUrl)
    }
  } catch (error) {
    console.error('打开文件夹失败:', error)
  }
}

const handleImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  img.src = `https://via.placeholder.com/800x600/6366f1/ffffff?text=Image+Not+Found`
}

const editMedia = () => {
  if (mediaItem.value) {
    formData.value = {
      name: mediaItem.value.name,
      description: mediaItem.value.description,
      group_name: mediaItem.value.group?.name || ''
    }
    showEditModal.value = true
  }
}

const handleSaveMedia = async (data: any) => {
  if (mediaItem.value) {
    const success = await updateMedia(mediaItem.value.id, data)
    if (success) {
      mediaItem.value.name = data.name
      mediaItem.value.description = data.description
      if (mediaItem.value.group) {
        mediaItem.value.group.name = data.group_name
      }
      
      showEditModal.value = false
    }
  }
}

const addTag = async (tagId: number) => {
  if (!mediaItem.value) return
  
  const success = await addTagToMedia(mediaItem.value.id, tagId)
  if (success) {
    // 本地更新标签列表，避免重新请求
    // 从所有可用标签中查找新增标签的完整信息
    const response = await fetch(`${API_BASE_URL}/api/tag`)
    if (response.ok) {
      const allTags: Tag[] = await response.json()
      const addedTag = allTags.find(tag => tag.id === tagId)
      if (addedTag) {
        currentMediaTags.value = [...currentMediaTags.value, addedTag]
      }
    }
  }
  
  showAddTagModal.value = false
}

const handleSaveTags = async (tagIds: number[]) => {
  if (!mediaItem.value) return
  
  const currentTagIds = new Set(currentMediaTags.value.map(tag => tag.id))
  const newTagIds = new Set(tagIds)
  
  const tagsToAdd = Array.from(newTagIds).filter(tagId => !currentTagIds.has(tagId))
  const tagsToRemove = Array.from(currentTagIds).filter(tagId => !newTagIds.has(tagId))
  
  // 并行执行所有添加和删除操作
  await Promise.all([
    ...tagsToAdd.map(tagId => addTagToMedia(mediaItem.value!.id, tagId)),
    ...tagsToRemove.map(tagId => removeTagFromMedia(mediaItem.value!.id, tagId))
  ])
  
  // 本地更新标签列表，避免重新请求
  // 需要获取新增标签的完整信息
  if (tagsToAdd.length > 0) {
    // 从所有可用标签中查找新增标签的完整信息
    const response = await fetch(`${API_BASE_URL}/api/tag`)
    if (response.ok) {
      const allTags: Tag[] = await response.json()
      const addedTags = allTags.filter(tag => tagsToAdd.includes(tag.id))
      currentMediaTags.value = [...currentMediaTags.value, ...addedTags]
    }
  }
  
  // 移除已删除的标签
  if (tagsToRemove.length > 0) {
    currentMediaTags.value = currentMediaTags.value.filter(tag => !tagsToRemove.includes(tag.id))
  }
}

const removeTag = async (tagId: number) => {
  if (!mediaItem.value) return
  
  const success = await removeTagFromMedia(mediaItem.value.id, tagId)
  if (success) {
    // 本地更新标签列表，避免重新请求
    currentMediaTags.value = currentMediaTags.value.filter(tag => tag.id !== tagId)
  }
}

const handleKeydown = (event: KeyboardEvent) => {
  if (!player.value || mediaItem.value?.type !== 'VIDEO') return
  
  const skipTime = 5
  
  switch (event.key) {
    case 'ArrowLeft':
      event.preventDefault()
      player.value.rewind(skipTime)
      break
    case 'ArrowRight':
      event.preventDefault()
      player.value.forward(skipTime)
      break
  }
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

const formatDuration = (seconds: number): string => {
  if (!seconds) return '0:00'
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)
  
  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }
  return `${minutes}:${secs.toString().padStart(2, '0')}`
}

onMounted(() => {
  initTheme()
  loadMediaData()
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
  if (player.value) {
    player.value.destroy()
    player.value = null
  }
})

watch(mediaId, () => {
  loadMediaData()
})

// 监听 isLoading，当加载完成且是视频时初始化 Plyr
watch(isLoading, async (newValue) => {
  console.log('isLoading watch triggered:', newValue, 'mediaItem:', mediaItem.value?.type, 'videoPlayer:', videoPlayer.value)
  if (!newValue && mediaItem.value?.type === 'VIDEO') {
    console.log('isLoading changed to false, initializing Plyr')
    
    // 等待 DOM 更新
    await nextTick()
    console.log('After nextTick, videoPlayer:', videoPlayer.value)
    
    if (!videoPlayer.value) {
      console.error('Video player element is still null after nextTick')
      return
    }
    
    // 销毁旧的播放器
    if (player.value) {
      player.value.destroy()
      player.value = null
    }
    
    try {
      player.value = new Plyr(videoPlayer.value, {
        controls: ['play-large', 'play', 'progress', 'current-time', 'mute', 'volume', 'captions', 'settings', 'pip', 'airplay', 'fullscreen'],
        speed: { selected: 1, options: [0.5, 0.75, 1, 1.25, 1.5, 2] },
        autoplay: true,
        hideControls: false,
        clickToPlay: false
      })
      
      console.log('Plyr initialized successfully in watch', player.value)
      
      // 自动播放
      player.value.play().catch((error: any) => {
        console.log('自动播放被阻止:', error)
      })
      
      player.value.on('play', () => console.log('开始播放'))
    } catch (error) {
      console.error('Failed to initialize Plyr in watch:', error)
    }
  }
})
</script>

<style scoped>
.plyr-container {
  width: 100%;
  height: 100%;
}

.plyr-container :deep(.plyr) {
  width: 100%;
  height: 100%;
  border-radius: 0;
}

/* 控制条永久显示 */
.plyr-container :deep(.plyr--video .plyr__controls) {
  opacity: 1 !important;
  visibility: visible !important;
  transform: translateY(0) !important;
}

.plyr-container :deep(.plyr--video.plyr--hide-controls .plyr__controls) {
  opacity: 1 !important;
  visibility: visible !important;
  transform: translateY(0) !important;
}
</style>
