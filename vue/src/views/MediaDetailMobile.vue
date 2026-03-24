<template>
    <div class="fixed inset-0 bg-black overflow-hidden">
    <!-- Loading State -->
    <div v-if="isLoading" class="absolute inset-0 flex items-center justify-center bg-black">
        <svg class="animate-spin h-12 w-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
    </div>
    
    <!-- Media Content -->
    <div v-else-if="mediaItem" class="absolute inset-0 transition-opacity duration-300 opacity-100 bg-black">
      <div class="absolute inset-0 overflow-hidden transition-transform duration-100" 
           @mousedown="handleMouseDown"
           :style="dragTransform">
        <!-- Back Button -->
        <div class="absolute top-4 left-4 z-50">
          <button 
            @click="goBack"
            class="w-12 h-12 bg-white/20 backdrop-blur-sm rounded-full flex items-center justify-center text-white hover:bg-white/30 transition-colors"
            title="返回"
            style="touch-action: manipulation;"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
          </button>
        </div>
        
        <!-- Media Content (Full Screen) -->
        <div ref="playerContainer" class="absolute inset-0 w-full overflow-hidden bg-black z-10">
          
          <div v-if="mediaItem.type === 'video'" class="absolute inset-0 bg-black w-full">
            <media-player 
              :src="videoSrc" 
              class="w-full h-full" 
              style="object-fit: cover; display: block;" 
              autoplay 
              playsinline 
              loop
              @ready="onPlayerReady"
            >
              <media-provider></media-provider>
              <media-controls class="absolute inset-0 z-10 flex flex-col-reverse pb-0 opacity-100 visibility-visible transition-none">
                
                <div class="w-full px-0">
                  <media-time-slider
                    class="group relative mx-[7.5px] inline-flex h-10 w-full cursor-pointer touch-none select-none items-center outline-none aria-hidden:hidden"
                    @click="onProgressBarClick"
                  >
                    <!-- Track -->
                    <div
                      class="relative h-[5px] w-full rounded-sm bg-white/30 ring-sky-400 group-data-[focus]:ring-[3px]"
                    >
                      <!-- Track Fill -->
                      <div
                        class="absolute h-full w-[var(--slider-fill)] rounded-sm bg-indigo-400 will-change-[width]"
                      ></div>
                      <!-- Progress -->
                      <div
                        class="absolute z-10 h-full w-[var(--slider-progress)] rounded-sm bg-white/50 will-change-[width]"
                      ></div>
                    </div>
                    <!-- Thumb -->
                    <div
                      class="absolute left-[var(--slider-fill)] top-1/2 z-20 h-[15px] w-[15px] -translate-x-1/2 -translate-y-1/2 rounded-full border border-[#cacaca] bg-white opacity-0 ring-white/40 transition-opacity will-change-[left] group-data-[active]:opacity-100 group-data-[dragging]:ring-4"
                    ></div>
                  </media-time-slider>
                </div>
              </media-controls>
            </media-player>

          </div>

          <!-- Image Display -->
          <div v-else-if="mediaItem.type === 'image'" class="absolute inset-0 bg-black w-full">
            <img 
              :src="imageSrc" 
              :alt="mediaItem.name"
              class="w-full h-full object-contain"
              @error="handleImageError"
              @dragstart.prevent
            />
          </div>
        </div>
        
        <!-- Media Information (Overlay) -->
        <div class="absolute inset-0 p-4 md:p-12 flex flex-col justify-end z-20" style="touch-action: manipulation;">
          <!-- Left Bottom: Name and Description -->
          <div class="mb-8">
            <div class="flex items-center gap-3 mb-3">
              <h1 class="text-lg font-bold text-white">{{ mediaItem.name }}</h1>
            </div>
            <p class="text-md text-gray-200 max-w-2xl">
              {{ mediaItem.description }}
            </p>
          </div>

          <!-- Right Side: Other Information (Group, Date, Tags) -->
          <div class="absolute right-2 bottom-20 flex flex-col gap-6 items-end">
            <!-- Tags -->
            <div class="flex flex-col items-end gap-3">
              <div class="flex flex-col gap-1 items-end">
                <div 
                  v-for="tag in currentMediaTags" 
                  :key="tag.id"
                  class="inline-flex items-center gap-1 px-2 py-1.5 rounded-full text-sm font-medium bg-white/20 backdrop-blur-sm text-white group"
                >
                  <span>{{ tag.name }}</span>
                  <button
                    @click="removeTag(tag.id)"
                    class="p-0.5 rounded-full hover:bg-white/30 transition-colors"
                    title="删除标签"
                  >
                    <svg class="w-.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
                <button
                  @click="showAddTagModal = true"
                  class="inline-flex items-center gap-1 px-3 py-1.5 rounded-full text-sm font-medium border-2 border-dashed border-white/30 text-white hover:border-white/50 transition-colors"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                  </svg>
                </button>
              </div>
            </div>

            <!-- Group -->
            <div class="flex flex-col items-center gap-2">
              <div class="w-8 h-8 rounded-lg bg-indigo-100/80 dark:bg-indigo-900/50 flex items-center justify-center flex-shrink-0">
                <svg class="w-4 h-4 text-indigo-500 dark:text-indigo-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
              </div>
              <div class="text-center">
                <p class="text-sm text-white font-medium">{{ mediaGroup?.name || '未知分组' }}</p>
              </div>
            </div>

            <!-- Edit Button -->
            <button @click="editMedia"
              class="px-4 py-2 bg-white/20 backdrop-blur-sm text-white rounded-lg hover:bg-white/30 transition-colors flex items-center gap-2 min-w-[44px] min-h-[44px] justify-center"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </button>
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
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTheme } from '../composables/useTheme'
import { API_BASE_URL } from '../utils/constants'
import MediaEditModal from '../components/MediaEditModal.vue'
import MediaTagModal from '../components/MediaTagModal.vue'
import 'vidstack/bundle';

// 控制移动端状态栏和导航栏颜色
const updateMobileUI = () => {
  // 添加黑色状态栏和导航栏的样式
  document.documentElement.classList.add('mobile-ui-black');
  
  // 动态创建或更新 theme-color meta 标签
  let themeMeta = document.querySelector<HTMLMetaElement>('meta[name="theme-color"]');
  if (themeMeta) {
    themeMeta.setAttribute('content', '#000000');
  } else {
    themeMeta = document.createElement('meta');
    themeMeta.name = 'theme-color';
    themeMeta.content = '#000000';
    document.head.appendChild(themeMeta);
  }
  
  // 为 iOS Safari 添加状态栏样式
  let appleMeta = document.querySelector<HTMLMetaElement>('meta[name="apple-mobile-web-app-status-bar-style"]');
  if (appleMeta) {
    appleMeta.setAttribute('content', 'black');
  } else {
    appleMeta = document.createElement('meta');
    appleMeta.name = 'apple-mobile-web-app-status-bar-style';
    appleMeta.content = 'black';
    document.head.appendChild(appleMeta);
  }
};

// 恢复默认状态栏和导航栏颜色
const restoreMobileUI = () => {
  document.documentElement.classList.remove('mobile-ui-black');
  
  // 恢复默认的 theme-color
  const themeMeta = document.querySelector<HTMLMetaElement>('meta[name="theme-color"]');
  if (themeMeta) {
    themeMeta.setAttribute('content', '#ffffff'); // 默认颜色，根据实际情况调整
  }
  
  // 恢复默认的 iOS Safari 状态栏样式
  const appleMeta = document.querySelector<HTMLMetaElement>('meta[name="apple-mobile-web-app-status-bar-style"]');
  if (appleMeta) {
    appleMeta.setAttribute('content', 'default');
  }
};

// 接口定义
interface Group {
  id: number
  name: string
  description: string
}

interface Media {
  id: number
  name: string
  type: 'video' | 'image'
  description: string
  path: string
  file_path: string
  size: number
  usage: number
  rate: number
  height: number | null
  width: number | null
  ratio: number | null
  date: string
  created_at: string
  updated_at: string
  timestamp: string | null
  startTime: string | null
  endTime: string | null
  duration: number | null
  hash: string | null
  parent_id: number | null
  actor_id: number | null
  group_id: number
}

interface Tag {
  id: number
  name: string
  type: string
}


// API 调用函数
const fetchMediaById = async (id: number): Promise<Media | null> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/media/${id}`)
    if (!response.ok) {
      throw new Error('获取媒体数据失败')
    }
    return await response.json()
  } catch (error) {
    console.error('获取媒体失败:', error)
    return null
  }
}

const fetchGroupById = async (id: number): Promise<Group | null> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/group/${id}`)
    if (!response.ok) {
      throw new Error('获取分组数据失败')
    }
    return await response.json()
  } catch (error) {
    console.error('获取分组失败:', error)
    return null
  }
}

// 获取上一个媒体ID
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

// 获取下一个媒体ID
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



const fetchTagsByMediaId = async (mediaId: number): Promise<Tag[]> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/media/${mediaId}/tags`)
    if (!response.ok) {
      throw new Error('获取媒体标签数据失败')
    }
    return await response.json()
  } catch (error) {
    console.error('获取媒体标签失败:', error)
    return []
  }
}



const updateMedia = async (id: number, data: { name: string; description: string; type: string; group_id: number | null }): Promise<boolean> => {
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

// /media/{media_id}/add/{tag_id}
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

// /media/{media_id}/remove/{tag_id}
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
  group_id: null as number | null
})

// 响应式数据
const mediaId = computed(() => parseInt(route.params.id as string))
const mediaItem = ref<Media | null>(null)
const mediaGroup = ref<Group | null>(null)
const currentMediaTags = ref<Tag[]>([])
const isLoading = ref(true) // 添加加载状态

// 鼠标拖动相关状态
const isDragging = ref(false) // 是否正在拖动
const startY = ref(0) // 拖动开始时的Y坐标
const currentY = ref(0) // 当前拖动的Y坐标
const dragDistance = ref(0) // 拖动距离

// 计算属性：拖动时的视觉反馈样式
const dragTransform = computed(() => {
  if (!isDragging.value) return ''
  
  // 根据拖动距离计算平移距离，最多平移50px
  const maxTranslate = 50
  let translate = dragDistance.value
  
  if (translate > maxTranslate) translate = maxTranslate
  if (translate < -maxTranslate) translate = -maxTranslate
  
  return `transform: translateY(${translate}px);`
})

// 数据获取函数
const loadMediaData = async () => {
  isLoading.value = true
  try {
    // 1. 获取媒体详情
    const mediaData = await fetchMediaById(mediaId.value)
    mediaItem.value = mediaData
    
    // 2. 获取分组信息
    if (mediaData) {
      const groupData = await fetchGroupById(mediaData.group_id)
      mediaGroup.value = groupData
      
      // 3. 获取媒体标签
      const tagsData = await fetchTagsByMediaId(mediaData.id)
      currentMediaTags.value = tagsData
    }
  } finally {
    isLoading.value = false
  }
}

// 视频源 - 使用后端代理文件路径
const videoSrc = computed(() => {
  if (!mediaItem.value) return ''
  return `${API_BASE_URL}/${mediaItem.value.path}`
})

// 视频播放器引用
const playerRef = ref<HTMLMediaElement | null>(null)

// 进度条相关变量
const progressPercent = ref(0)
const bufferedPercent = ref(0)

// 图片源 - 使用后端代理文件路径
const imageSrc = computed(() => {
  if (!mediaItem.value) return ''
  return `${API_BASE_URL}/${mediaItem.value.path}`
})

// 视频进度更新函数
const updateProgress = () => {
  if (!playerRef.value) return
  
  // 更新播放进度
  const currentTime = playerRef.value.currentTime
  const duration = playerRef.value.duration
  if (duration > 0) {
    progressPercent.value = (currentTime / duration) * 100
  }
  
  // 更新缓冲进度
  if (playerRef.value.buffered.length > 0) {
    const bufferedEnd = playerRef.value.buffered.end(playerRef.value.buffered.length - 1)
    bufferedPercent.value = (bufferedEnd / duration) * 100
  }
}

// 进度条点击事件处理函数
const onProgressBarClick = (event: MouseEvent) => {
  if (!playerRef.value) return
  
  const bar = event.currentTarget as HTMLElement
  const rect = bar.getBoundingClientRect()
  const clickPosition = (event.clientX - rect.left) / rect.width
  
  // 设置视频进度
  const duration = playerRef.value.duration
  if (duration > 0) {
    playerRef.value.currentTime = duration * clickPosition
  }
}

// 视频播放器准备就绪事件处理函数
const onPlayerReady = () => {
  // 获取视频元素引用
  const playerElement = document.querySelector('.vds-media') as HTMLMediaElement
  if (playerElement) {
    playerRef.value = playerElement
    
    // 添加视频事件监听器
    playerRef.value.addEventListener('timeupdate', updateProgress)
    playerRef.value.addEventListener('progress', updateProgress)
    
    // 初始化进度
    updateProgress()
  }
}

// 清理视频播放器事件监听器
const cleanupPlayer = () => {
  if (playerRef.value) {
    playerRef.value.removeEventListener('timeupdate', updateProgress)
    playerRef.value.removeEventListener('progress', updateProgress)
    playerRef.value = null
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
      group_id: mediaItem.value.group_id
    }
    showEditModal.value = true
  }
}

const handleSaveMedia = async (data: any) => {
  if (mediaItem.value) {
    const success = await updateMedia(mediaItem.value.id, data)
    if (success) {
      // 更新本地数据
      mediaItem.value.name = data.name
      mediaItem.value.type = data.type
      mediaItem.value.description = data.description
      mediaItem.value.group_id = data.group_id as number
      showEditModal.value = false
    }
  }
}

const addTag = async (tagId: number) => {
  if (!mediaItem.value) return
  
  const success = await addTagToMedia(mediaItem.value.id, tagId)
  if (success) {
    // 获取最新标签列表
    const tagsData = await fetchTagsByMediaId(mediaItem.value.id)
    currentMediaTags.value = tagsData
  }
  
  showAddTagModal.value = false
}

// 批量处理标签操作
const handleSaveTags = async (tagIds: number[]) => {
  if (!mediaItem.value) return
  
  // 获取当前标签ID集合
  const currentTagIds = new Set(currentMediaTags.value.map(tag => tag.id))
  // 新选中的标签ID集合
  const newTagIds = new Set(tagIds)
  
  // 需要添加的标签（新选中但当前没有的）
  const tagsToAdd = Array.from(newTagIds).filter(tagId => !currentTagIds.has(tagId))
  // 需要删除的标签（当前有但新选中没有的）
  const tagsToRemove = Array.from(currentTagIds).filter(tagId => !newTagIds.has(tagId))
  
  // 批量添加标签
  for (const tagId of tagsToAdd) {
    await addTagToMedia(mediaItem.value.id, tagId)
  }
  
  // 批量删除标签
  for (const tagId of tagsToRemove) {
    await removeTagFromMedia(mediaItem.value.id, tagId)
  }
  
  // 获取最新标签列表
  const tagsData = await fetchTagsByMediaId(mediaItem.value.id)
  currentMediaTags.value = tagsData
  
  showAddTagModal.value = false
}

const removeTag = async (tagId: number) => {
  if (!mediaItem.value) return
  
  const success = await removeTagFromMedia(mediaItem.value.id, tagId)
  if (success) {
    // 更新本地标签列表
    const tagsData = await fetchTagsByMediaId(mediaItem.value.id)
    currentMediaTags.value = tagsData
  }
}

// 切换到上一个媒体
const goToPreviousMedia = async () => {
  if (!mediaItem.value) return
  
  const previousId = await fetchPreviousMediaId(mediaItem.value.id)
  if (previousId) {
    router.replace(`/media/${previousId}`)
  }
}

// 切换到下一个媒体
const goToNextMedia = async () => {
  if (!mediaItem.value) return
  
  const nextId = await fetchNextMediaId(mediaItem.value.id)
  if (nextId) {
    router.replace(`/media/${nextId}`)
  }
}

// 返回上一个页面
const goBack = () => {
  router.back()
}

// 非响应式变量，用于优化拖动性能
let isDraggingNonReactive = false
let startYNonReactive = 0
let currentDragDistance = 0
let requestId: number | null = null

// 拖动开始处理函数
const startDrag = (y: number) => {
  isDragging.value = true
  isDraggingNonReactive = true
  startY.value = y
  startYNonReactive = y
  currentY.value = y
  dragDistance.value = 0
  currentDragDistance = 0
}

// 拖动移动处理函数
const handleDragMove = (y: number) => {
  if (!isDraggingNonReactive) return
  
  // 更新非响应式变量，减少响应式系统的更新频率
  currentDragDistance = y - startYNonReactive
  
  // 如果还没有请求动画帧，就请求一个
  if (!requestId) {
    requestId = requestAnimationFrame(updateDragPosition)
  }
}

// 拖动结束处理函数
const endDrag = async () => {
  if (!isDragging.value) return
  
  isDragging.value = false
  isDraggingNonReactive = false
  
  // 清除动画帧请求
  if (requestId) {
    cancelAnimationFrame(requestId)
    requestId = null
  }
  
  // 拖动阈值，超过50px才切换媒体
  const threshold = 50
  
  if (dragDistance.value > threshold) {
    // 向下拖动，切换到下一个媒体
    await goToPreviousMedia()
  } else if (dragDistance.value < -threshold) {
    // 向上拖动，切换到上一个媒体
    await goToNextMedia()
  }
  
  // 重置拖动状态
  dragDistance.value = 0
  currentDragDistance = 0
}

// 鼠标拖动事件处理函数
const handleMouseDown = (event: MouseEvent) => {
  // 检查点击目标是否为可点击元素，如果是则不启动拖动
  const target = event.target as HTMLElement;
  if (target.closest('button, [role="button"], a, [href]')) {
    return;
  }
  
  startDrag(event.clientY)
}

// 使用requestAnimationFrame更新拖动状态
const updateDragPosition = () => {
  if (!isDraggingNonReactive) return
  
  // 更新响应式变量
  dragDistance.value = currentDragDistance
  
  // 继续下一帧
  requestId = requestAnimationFrame(updateDragPosition)
}

// 鼠标移动处理函数
const handleMouseMove = (event: MouseEvent) => {
  handleDragMove(event.clientY)
}

const handleMouseUp = async () => {
  await endDrag()
}

// 触摸事件处理函数
const handleTouchStart = (event: TouchEvent) => {
  // 检查触摸目标是否为可点击元素，如果是则不启动拖动
  const target = event.target as HTMLElement;
  if (target.closest('button, [role="button"], a, [href]')) {
    return;
  }
  
  // 只处理第一个触摸点
  const touch = event.touches[0]
  if (touch) {
    startDrag(touch.clientY)
    
    // 阻止默认的触摸行为，避免页面滚动
    event.preventDefault()
  }
}

const handleTouchMove = (event: TouchEvent) => {
  // 只有在正在拖动时才处理移动事件
  if (!isDraggingNonReactive) return;
  
  // 只处理第一个触摸点
  const touch = event.touches[0]
  if (touch) {
    handleDragMove(touch.clientY)
    
    // 阻止默认的触摸行为，避免页面滚动
    event.preventDefault()
  }
}

const handleTouchEnd = async () => {
  await endDrag()
}

const handleTouchCancel = async () => {
  await endDrag()
}

// 保存主内容区域引用
let mainContentWrapper: HTMLElement | null = null


// 监听路由参数变化，重新加载数据
watch(
  () => route.params.id,
  (newId, oldId) => {
    if (newId !== oldId) {
      loadMediaData()
    }
  }
)

onMounted(() => {
  initTheme()
  loadMediaData()
  
  // 设置移动端黑色状态栏和导航栏
  updateMobileUI()
  
  // 隐藏导航栏
  const navbar = document.querySelector('aside.fixed')
  if (navbar) {
    navbar.classList.add('hidden')
  }
  
  // 移除主内容区域的 padding-left
  mainContentWrapper = document.querySelector('div.pl-64')
  if (mainContentWrapper) {
    mainContentWrapper.classList.remove('pl-64')
  }
  
  // 添加鼠标拖动事件监听器
  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', handleMouseUp)
  document.addEventListener('mouseleave', handleMouseUp) // 防止鼠标移出窗口时状态异常
  
  // 添加触摸事件监听器
  document.addEventListener('touchstart', handleTouchStart, { passive: false })
  document.addEventListener('touchmove', handleTouchMove, { passive: false })
  document.addEventListener('touchend', handleTouchEnd)
  document.addEventListener('touchcancel', handleTouchCancel)
})

onUnmounted(() => {
  // 恢复默认的状态栏和导航栏颜色
  restoreMobileUI()
  
  // 恢复导航栏
  const navbar = document.querySelector('aside.fixed')
  if (navbar) {
    navbar.classList.remove('hidden')
  }
  
  // 恢复主内容区域的 padding-left
  if (mainContentWrapper) {
    mainContentWrapper.classList.add('pl-64')
  }
  
  // 移除鼠标拖动事件监听器
  document.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('mouseup', handleMouseUp)
  document.removeEventListener('mouseleave', handleMouseUp)
  
  // 移除触摸事件监听器
  document.removeEventListener('touchstart', handleTouchStart)
  document.removeEventListener('touchmove', handleTouchMove)
  document.removeEventListener('touchend', handleTouchEnd)
  document.removeEventListener('touchcancel', handleTouchCancel)
  
  // 清理视频播放器事件监听器
  cleanupPlayer()
})
</script>

<style scoped>
/* 强制覆盖 Vidstack 的默认隐藏逻辑 */
media-controls {
  display: flex !important;
  opacity: 1 !important;
  visibility: visible !important;
  pointer-events: none; /* 让点击穿透到视频，如果不穿透则不会触发切换 */
  z-index: 10 !important;
}

media-time-slider {
  pointer-events: auto; /* 允许点击进度条进行拖动 */
}

/* 移除 Vidstack 默认的点击黑影/动画特效 */
media-player::part(gesture) {
  display: none;
}
</style>

<style>
/* 移动端黑色状态栏和导航栏样式 */
.mobile-ui-black {
  /* 确保页面内容不会被系统UI遮挡 */
  padding: env(safe-area-inset-top) env(safe-area-inset-right) env(safe-area-inset-bottom) env(safe-area-inset-left);
}

/* 针对不同浏览器的黑色系统UI样式 */
@supports (-webkit-touch-callout: none) {
  /* Safari iOS */
  .mobile-ui-black {
    -webkit-background-color: #000000;
    background-color: #000000;
  }
}

@supports not (-webkit-touch-callout: none) {
  /* Chrome/Edge Android */
  .mobile-ui-black {
    background-color: #000000;
  }
}

/* 确保页面内容全屏显示 */
.mobile-ui-black body {
  margin: 0;
  padding: 0;
  overflow: hidden;
}
</style>