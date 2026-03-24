<template>
  <div class="flex h-screen overflow-hidden">
    <!-- Left: Media List -->
    <div class="flex-1 overflow-hidden flex flex-col">
      <div id="main-content" class="flex-1 overflow-y-auto transition-colors w-full mx-auto px-2 sm:px-6 lg:px-8 py-8 pb-24">
        <div class="mb-6">
          <div class="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
            <!-- Search and Sort -->
            <h2 class="text-3xl font-bold text-gray-900 dark:text-white">媒体管理</h2>
            <!-- Search and Filter -->
            <div class="flex flex-col sm:flex-row gap-4 w-full sm:w-auto">
              <div class="flex flex-1 max-w-md">
                <div class="relative flex-1">
                  <input
                    v-model="searchInput"
                    type="text"
                    placeholder="搜索媒体名称..."
                    @keyup.enter="handleSearch"
                    class="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-l-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  />
                  <svg class="absolute left-3 top-2.5 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>
                <button
                  @click="handleSearch"
                  class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-r-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
                >
                  搜索
                </button>
              </div>
              
              <!-- Media Type Filter -->
              <FilterSelect
                v-model="selectedMediaType"
                :options="mediaTypeOptions"
                placeholder="所有类型"
                @change="handleMediaTypeChange"
              />
              
              <!-- Sort Field -->
              <FilterSelect
                v-model="sortField"
                :options="sortFieldOptions"
                placeholder="排序"
                @change="handleSortChange"
              />
              
              <!-- Sort Order -->
              <FilterSelect
                v-model="sortOrder"
                :options="sortOrderOptions"
                placeholder="排序方式"
                @change="handleSortChange"
              />
            </div>
          </div>
        </div>

        <!-- Media Grid -->
        <div v-if="media.length > 0" :class="[selectedMediaId ? 'grid-cols-2 md:grid-cols-2 lg:grid-cols-4 gap-3' : 'grid-cols-2 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-10 gap-3', 'grid']">
          <MediaCard
            v-for="mediaItem in media"
            :key="mediaItem.id"
            :media="mediaItem"
            @click="selectMedia"
            @edit="editMedia"
            @delete="deleteMedia"
            @set-avatar="setAvatar"
            @contextmenu="handleContextMenu"
          />
        </div>

        <!-- Context Menu Backdrop -->
        <div
          v-if="contextMenuVisible"
          class="fixed inset-0 z-499 bg-transparent"
          @click="hideContextMenu"
        ></div>

        <!-- Global Context Menu -->
        <div
          v-if="contextMenuVisible"
          ref="contextMenuRef"
          class="fixed z-500 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 py-1 min-w-[140px]"
          :style="{ left: menuPosition.x + 'px', top: menuPosition.y + 'px' }"
          @click.stop
        >
          <button
            @click="handleMenuEdit"
            class="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            编辑
          </button>
          <button
            @click="handleMenuSetAvatar"
            class="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            设为头像
          </button>
          <button
            @click="handleMenuDelete"
            class="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            删除
          </button>
        </div>

        <!-- 高级分页导航条 -->
        <PaginationBar
          :current-page="currentPage"
          :total-pages="totalPages"
          :total-items="totalItems"
          :page-size="pageSize"
          :is-split-view="!!selectedMediaId"
          @first="goToFirstPage"
          @prev="goToPrevPage"
          @next="goToNextPage"
          @last="goToLastPage"
        />
      </div>
    </div>

    <!-- Right: Media Detail -->
    <div v-if="selectedMediaId" class="w-2/3 border-l border-gray-200 dark:border-gray-700 flex flex-col h-full">
      <MediaDetail :media-id="selectedMediaId" @close="closeDetail" @select-media="selectMedia" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useTheme } from '../composables/useTheme'
import MediaCard from '../components/MediaCard.vue'
import PaginationBar from '../components/PaginationBar.vue'
import FilterSelect from '../components/FilterSelect.vue'
import MediaDetail from '../views/MediaDetail.vue'
import { API_BASE_URL } from '../utils/constants'

defineOptions({
  name: 'Media'
})

const router = useRouter()
const { initTheme } = useTheme()

const media = ref<Media[]>([])
const searchQuery = ref('')
const searchInput = ref('')

const currentPage = ref(1)
const pageSize = ref(40)
const totalItems = ref(0)

const sortField = ref('rating')
const sortOrder = ref('desc')

// 媒体类型筛选
const selectedMediaType = ref('')

// 当前选中的媒体ID
const selectedMediaId = ref<number | null>(null)

// FilterSelect 选项
const mediaTypeOptions = [
  { value: '', label: '所有类型' },
  { value: 'VIDEO', label: '视频' },
  { value: 'IMAGE', label: '图片' },
  { value: 'PREVIEW', label: '预览' }
]

const sortFieldOptions = [
  { value: 'rating', label: '评分' },
  { value: 'name', label: '名称' },
  { value: 'file_size', label: '文件大小' },
  { value: 'view_count', label: '查看次数' },
  { value: 'date', label: '日期' },
  { value: 'duration', label: '时长' },
  { value: 'id', label: 'ID' }
]

const sortOrderOptions = [
  { value: 'desc', label: '降序' },
  { value: 'asc', label: '升序' }
]

// 右键菜单状态
const contextMenuVisible = ref(false)
const contextMenuRef = ref<HTMLElement | null>(null)
const menuPosition = ref({ x: 0, y: 0 })
const currentMediaItem = ref<Media | null>(null)

// 处理媒体类型筛选变化
const handleMediaTypeChange = () => {
  currentPage.value = 1 // 筛选时重置到第一页
  fetchMedia()
}

// 处理排序变化
const handleSortChange = () => {
  currentPage.value = 1 // 排序时重置到第一页
  fetchMedia()
}

// 处理搜索按钮点击
const handleSearch = () => {
  searchQuery.value = searchInput.value
  currentPage.value = 1 // 搜索时重置到第一页
  fetchMedia()
}

interface MediaPagination {
  items: Media[]
  total: number
  skip: number
  limit: number
}

interface Media {
  id: number
  name: string
  type: 'VIDEO' | 'IMAGE'
  thumbnail_path: string | null
  duration: number | null
  rating: number | null
}



// API 调用函数
const fetchMedia = async () => {
  try {
    // 计算 skip 值
    const skip = (currentPage.value - 1) * pageSize.value
    
    // 构建查询参数
    const params = new URLSearchParams({
      skip: skip.toString(),
      limit: pageSize.value.toString(),
      sort_by: sortField.value,
      sort_order: sortOrder.value
    })
    
    // 如果有搜索查询，添加 name 参数（模糊查询）
    if (searchQuery.value) {
      params.append('name', searchQuery.value)
    }
    
    // 如果选择了媒体类型，添加 type 参数
    if (selectedMediaType.value) {
      params.append('type', selectedMediaType.value)
    }
    
    const response = await fetch(`${API_BASE_URL}/api/media?${params.toString()}`)
    if (!response.ok) {
      throw new Error('获取媒体数据失败')
    }
    const data: MediaPagination = await response.json()
    
    // 更新媒体数据和分页信息
    media.value = data.items
    totalItems.value = data.total
  } catch (error) {
    console.error('获取媒体失败:', error)
  }
}

const deleteMediaItem = async (id: number) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/media/${id}`, {
      method: 'DELETE'
    })
    
    if (!response.ok) {
      throw new Error('删除媒体失败')
    }
    
    await fetchMedia()
    return true
  } catch (error) {
    console.error('删除媒体失败:', error)
    return false
  }
}

const deleteMedia = async (id: number) => {
  if (confirm('确定要删除这个媒体吗?')) {
    await deleteMediaItem(id)
  }
}

// 编辑媒体
const editMedia = (mediaItem: Media) => {
  router.push({
    path: `/media/${mediaItem.id}/edit`,
  })
}

// 设置头像
const setAvatar = async (id: number) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/media/${id}/set-avatar`, {
      method: 'POST'
    })
    if (response.ok) {
      alert('头像设置成功')
    } else {
      alert('头像设置失败')
    }
  } catch (error) {
    console.error('设置头像失败:', error)
    alert('设置头像失败')
  }
}

const totalPages = computed(() => {
  return Math.ceil(totalItems.value / pageSize.value)
})

const goToPage = (page: number) => {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
    fetchMedia()
  }
}

const goToPrevPage = () => {
  if (currentPage.value > 1) {
    goToPage(currentPage.value - 1)
  }
}

const goToNextPage = () => {
  if (currentPage.value < totalPages.value) {
    goToPage(currentPage.value + 1)
  }
}

const goToFirstPage = () => {
  goToPage(1)
}

const goToLastPage = () => {
  goToPage(totalPages.value)
}

const selectMedia = (id: number) => {
  selectedMediaId.value = id
}

const closeDetail = () => {
  selectedMediaId.value = null
}

// 阻止滚动事件
const preventScroll = (event: Event) => {
  event.preventDefault()
}

// 阻止键盘滚动事件
const preventKeyScroll = (e: KeyboardEvent) => {
  // 阻止方向键和空格键滚动
  if ([32, 33, 34, 35, 36, 37, 38, 39, 40].includes(e.keyCode)) {
    e.preventDefault()
  }
}

// 处理右键菜单事件
const handleContextMenu = (event: MouseEvent, mediaItem: Media) => {
  event.stopPropagation()
  event.preventDefault()
  
  // 计算菜单位置，确保不超出视口
  const x = Math.min(event.clientX, window.innerWidth - 150)
  const y = Math.min(event.clientY, window.innerHeight - 100)
  
  menuPosition.value = { x, y }
  currentMediaItem.value = mediaItem
  contextMenuVisible.value = true
  
  // 禁止页面滚动（使用事件监听，保持滚动条可见）
  document.addEventListener('wheel', preventScroll, { passive: false })
  document.addEventListener('touchmove', preventScroll, { passive: false })
  document.addEventListener('keydown', preventKeyScroll)
}

// 隐藏右键菜单
const hideContextMenu = () => {
  contextMenuVisible.value = false
  currentMediaItem.value = null
  
  // 恢复页面滚动
  document.removeEventListener('wheel', preventScroll)
  document.removeEventListener('touchmove', preventScroll)
  document.removeEventListener('keydown', preventKeyScroll)
}

// 处理菜单编辑
const handleMenuEdit = () => {
  if (currentMediaItem.value) {
    editMedia(currentMediaItem.value)
    hideContextMenu()
  }
}

// 处理菜单设为头像
const handleMenuSetAvatar = () => {
  if (currentMediaItem.value) {
    setAvatar(currentMediaItem.value.id)
    hideContextMenu()
  }
}

// 处理菜单删除
const handleMenuDelete = () => {
  if (currentMediaItem.value) {
    deleteMedia(currentMediaItem.value.id)
    hideContextMenu()
  }
}

// 点击外部关闭菜单
const handleClickOutside = (event: MouseEvent) => {
  hideContextMenu()
}

// 处理菜单项点击，阻止事件冒泡
const handleMenuItemClick = (event: MouseEvent) => {
  event.stopPropagation()
}

onMounted(() => {
  initTheme()
  fetchMedia()
  document.addEventListener('contextmenu', hideContextMenu)
  // 监听键盘事件，按 ESC 键关闭菜单
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      hideContextMenu()
    }
  })
})

onUnmounted(() => {
  document.removeEventListener('contextmenu', hideContextMenu)
  document.removeEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      hideContextMenu()
    }
  })
})

</script>
