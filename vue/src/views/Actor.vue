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
                v-model="filterName"
                type="text"
                placeholder="搜索姓名..."
                class="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-xl bg-[var(--color-select-bg-dark)] text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                @keydown.enter="resetAndFetch"
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
      <div class="grid grid-cols-2 lg:grid-cols-4 xl:grid-cols-8 gap-4">
        <ActorCard
          v-for="item in actorsData"
          :key="item.id"
          :actor="item"
          @click="goToActorDetail"
          @edit="editActor"
          @delete="deleteActor"
        />
      </div>

      <!-- Loading -->
      <div v-if="loading" class="flex justify-center py-8">
        <div class="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-pink-500"></div>
      </div>

      <!-- End -->
      <div v-if="!loading && !hasMore && actorsData.length > 0" class="text-center py-8 text-sm text-gray-500 dark:text-gray-400">
        已经到底了
      </div>

      <!-- Empty -->
      <div v-if="!loading && actorsData.length === 0" class="flex flex-col items-center justify-center py-24 text-gray-500 dark:text-gray-400">
        <svg class="w-12 h-12 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        <p class="text-sm">暂无演员</p>
      </div>

      <!-- Scroll sentinel -->
      <div ref="sentinel" class="h-1"></div>
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
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import type { Actor } from '../types'
import ActorCard from '../components/ActorCard.vue'
import ActorEditModal from '../components/ActorEditModal.vue'
import FilterSelect from '../components/FilterSelect.vue'
import { api } from '../composables/useApi'
import { useToast } from '../composables/useToast'

defineOptions({ name: 'Actor' })

const router = useRouter()
const toast = useToast()

const pageSize = 30
const actorsData = ref<Actor[]>([])
const loading = ref(false)
const hasMore = ref(true)

const filterName = ref('')
const sortField = ref<string>('id')
const sortOrder = ref<'asc' | 'desc'>('desc')
const sortOptions = ref([
  { value: 'id', label: '按ID排序' },
  { value: 'name', label: '按姓名排序' },
])

const showModal = ref(false)
const editMode = ref(false)
const currentEditId = ref<number | null>(null)
const formData = ref({ name: '', description: '' })

const sentinel = ref<HTMLElement | null>(null)
let observer: IntersectionObserver | null = null

// --- Fetch ---

const fetchActors = async (reset = false) => {
  if (loading.value) return
  if (!reset && !hasMore.value) return

  if (reset) {
    actorsData.value = []
    hasMore.value = true
  }

  loading.value = true
  try {
    const data = await api.get<Actor[]>('/actors', {
      name: filterName.value || undefined,
      skip: actorsData.value.length,
      limit: pageSize,
      sort_by: sortField.value,
      sort_order: sortOrder.value,
    })

    actorsData.value.push(...data)
    hasMore.value = data.length === pageSize
  } catch (error) {
    toast.error('获取演员数据失败')
  } finally {
    loading.value = false
  }
}

const resetAndFetch = () => fetchActors(true)

// --- Sort & Filter ---

const handleSortChange = () => {
  sortOrder.value = 'asc'
  resetAndFetch()
}

const toggleSortOrder = () => {
  sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  resetAndFetch()
}

const resetFilters = () => {
  filterName.value = ''
  sortField.value = 'id'
  sortOrder.value = 'desc'
  resetAndFetch()
}

// --- CRUD ---

const openAddModal = () => {
  editMode.value = false
  currentEditId.value = null
  formData.value = { name: '', description: '' }
  showModal.value = true
}

const editActor = (item: Actor) => {
  editMode.value = true
  currentEditId.value = item.id
  formData.value = { name: item.name, description: item.description || '' }
  showModal.value = true
}

const saveActor = async (data: typeof formData.value) => {
  try {
    if (editMode.value && currentEditId.value) {
      await api.put(`/actors/${currentEditId.value}`, data)
    } else {
      await api.post('/actors', data)
    }
    await resetAndFetch()
    closeModal()
    toast.success('保存成功')
  } catch (error) {
    toast.error('保存演员数据失败')
  }
}

const deleteActor = async (id: number) => {
  if (!confirm('确定要删除这条记录吗?')) return
  try {
    await api.del(`/actors/${id}`)
    actorsData.value = actorsData.value.filter((a: Actor) => a.id !== id)
    toast.success('删除成功')
  } catch (error) {
    toast.error('删除演员数据失败')
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

// --- Infinite scroll ---

onMounted(() => {
  fetchActors(true)
  observer = new IntersectionObserver(
    (entries) => {
      if (entries[0].isIntersecting && !loading.value && hasMore.value) {
        fetchActors()
      }
    },
    { rootMargin: '200px' },
  )
  if (sentinel.value) observer.observe(sentinel.value)
})

onUnmounted(() => {
  observer?.disconnect()
})
</script>
