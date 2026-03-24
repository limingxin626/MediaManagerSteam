<template>
  <div class="min-h-screen transition-colors">
    <!-- Main Content -->
    <div class="w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 pb-24">
      <!-- Header with Actions -->
      <div class="mb-6">
        <div class="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
          <h2 class="text-3xl font-bold text-gray-900 dark:text-white">演员管理</h2>
          <!-- Search and Sort -->
          <div class="flex flex-wrap gap-4 items-center flex-1">
            <!-- Search -->
            <div class="relative flex-1 min-w-[200px] max-w-md">
              <input 
                v-model="filterParams.name"
                type="text" 
                placeholder="搜索姓名..." 
                class="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-xl bg-[var(--color-select-bg-dark)] text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
              <svg class="absolute left-3 top-2.5 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            
            <!-- Sort Select -->
            <FilterSelect
              v-model="sortField"
              :options="sortOptions"
              placeholder="排序"
              @change="handleSortChange"
            />
            
            <!-- Sort Order Toggle -->
            <button 
              @click="toggleSortOrder"
              class="flex items-center justify-center w-10 h-10 rounded-lg bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500"
              title="切换排序方向"
            >
              <svg class="w-4 h-4 text-gray-600 dark:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12" />
              </svg>
            </button>

            <!-- Apply Filter Button -->
            <button 
              @click="fetchActorsData"
              class="px-4 py-2 bg-pink-600 text-white rounded-lg hover:bg-pink-700 transition-colors flex-shrink-0"
            >
              应用
            </button>

            <!-- Reset Filter Button -->
            <button 
              @click="resetFilters"
              class="px-4 py-2 bg-gray-300 text-gray-700 dark:bg-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-400 dark:hover:bg-gray-600 transition-colors flex-shrink-0"
            >
              重置
            </button>
          </div>
          
          <!-- Add New Button -->
          <button 
            @click="openAddModal"
            class="bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700 transition-colors flex items-center gap-2 shadow-md flex-shrink-0"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Grid View -->
      <div class="grid grid-cols-2 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-10 gap-4">
        <ActorCard
          v-for="item in actorsData" 
          :key="item.id"
          :actor="item"
          @click="goToActorDetail"
          @edit="editActor"
          @delete="deleteActor"
        />
      </div>

      <!-- 高级分页导航条 -->
      <PaginationBar
        :current-page="currentPage"
        :total-pages="totalPages"
        :total-items="totalItems"
        :page-size="pageSize"
        @first="goToFirstPage"
        @prev="goToPreviousPage"
        @next="goToNextPage"
        @last="goToLastPage"
      />
    </div>

    <!-- Add/Edit Modal -->
    <ActorEditModal
      :is-open="showModal"
      :title="editMode ? '编辑数据' : '添加新数据'"
      :form-data="formData"
      @close="closeModal"
      @save="saveActor"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useTheme } from '../composables/useTheme'
import type { Actor } from '../types'
import ActorCard from '../components/ActorCard.vue'
import ActorEditModal from '../components/ActorEditModal.vue'
import PaginationBar from '../components/PaginationBar.vue'
import FilterSelect from '../components/FilterSelect.vue'
import { 
  API_BASE_URL, 
} from '../utils/constants'
import {
  Disclosure,
  DisclosureButton,
  DisclosurePanel,
} from '@headlessui/vue'

defineOptions({
  name: 'Actor'
})

const router = useRouter()
const { initTheme } = useTheme()

// 移除不再使用的searchQuery变量，改为使用filterParams.name
// const searchQuery = ref('')
const showModal = ref(false)
const editMode = ref(false)
const currentEditId = ref<number | null>(null)
// 移除视图切换功能，默认只使用网格视图
// const viewMode = ref<'table' | 'grid'>('table')

// 排序相关数据
const sortField = ref<string>('id')
const sortOrder = ref<'asc' | 'desc'>('desc')
const sortOptions = ref([
  { value: 'id', label: '按ID排序' },
  { value: 'name', label: '按姓名排序' },
  { value: 'country', label: '按国家排序' },
  { value: 'category', label: '按分类排序' },
  { value: 'score', label: '按评分排序' }
])

// 高级查询过滤条件
const filterParams = ref({
  name: '',
})

// 分页参数
const currentPage = ref(1)
const pageSize = ref(30)
const totalItems = ref(0)

const actorsData = ref<Actor[]>([])

// 分页计算属性
const totalPages = computed(() => {
  return Math.ceil(totalItems.value / pageSize.value)
})

// 分页方法
const goToPreviousPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--
    fetchActorsData()
  }
}

const goToNextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
    fetchActorsData()
  }
}

const goToFirstPage = () => {
  if (currentPage.value !== 1) {
    currentPage.value = 1
    fetchActorsData()
  }
}

const goToLastPage = () => {
  if (currentPage.value !== totalPages.value) {
    currentPage.value = totalPages.value
    fetchActorsData()
  }
}

const fetchActorsData = async () => {
  try {
    // 构建查询参数
    const params = new URLSearchParams()
    
    // 添加过滤参数
    if (filterParams.value.name) {
      params.append('name', filterParams.value.name)
    }
    // 添加分页参数
    const skip = (currentPage.value - 1) * pageSize.value
    params.append('skip', skip.toString())
    params.append('limit', pageSize.value.toString())
    
    // 添加排序参数
    params.append('sort_by', sortField.value)
    params.append('sort_order', sortOrder.value)
    
    const response = await fetch(`${API_BASE_URL}/api/actor?${params.toString()}`)
    if (!response.ok) {
      throw new Error('Failed to fetch actors data')
    }
    
    // 假设后端返回的数据结构包含 items 和 total
    const data = await response.json()
    actorsData.value = data.items
    totalItems.value = data.total
  } catch (error) {
    console.error('Error fetching actors data:', error)
  }
}

onMounted(() => {
  initTheme()
  fetchActorsData()
})



const formData = ref({
  name: '',
  description: '',
})


const openAddModal = () => {
  editMode.value = false
  currentEditId.value = null
  formData.value = {
    name: '',
    description: '',
  }
  showModal.value = true
}

const editActor = (item: Actor) => {
  editMode.value = true
  currentEditId.value = item.id
  formData.value = { ...item }
  showModal.value = true
}

const saveActor = async (data: typeof formData.value) => {
  try {
    let response
    if (editMode.value && currentEditId.value) {
      // Update existing item
      response = await fetch(`${API_BASE_URL}/api/actor/${currentEditId.value}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      })
    } else {
      // Create new item
      response = await fetch(`${API_BASE_URL}/api/actor/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      })
    }
    
    if (!response.ok) {
      throw new Error('Failed to save actor data')
    }
    
    // Get the saved actor data
    const savedActor = await response.json()
    
    // Refresh data after save
    await fetchActorsData()
    closeModal()
    
    // If creating a new actor, navigate to its detail page
    if (!editMode.value) {
      goToActorDetail(savedActor.id)
    }
  } catch (error) {
    console.error('Error saving actor data:', error)
  }
}

const deleteActor = async (id: number) => {
  if (confirm('确定要删除这条记录吗?')) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/actor/${id}`, {
        method: 'DELETE'
      })
      
      if (!response.ok) {
        throw new Error('Failed to delete actor data')
      }
      
      // Refresh data after delete
      await fetchActorsData()
    } catch (error) {
      console.error('Error deleting actor data:', error)
    }
  }
}

const closeModal = () => {
  showModal.value = false
  editMode.value = false
  currentEditId.value = null
}

const goToActorDetail = (id: number) => {
  router.push(`/actor/${id}`)
}

// 排序相关函数
const handleSortChange = () => {
  // 当排序字段改变时，重置排序方向为升序
  sortOrder.value = 'asc'
  fetchActorsData()
}

const toggleSortOrder = () => {
  // 切换排序方向
  sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  fetchActorsData()
}

// 重置过滤条件
const resetFilters = () => {
  filterParams.value = {
    name: '',
  }
  fetchActorsData()
}
</script>
