<template>
  <div class="min-h-screen transition-colors">
    <!-- Main Content -->
    <div class="w-full mx-auto px-2 sm:px-6 lg:px-8 py-8">
      <!-- Back Button -->
      <button 
        @click="router.back()" 
        class="inline-flex items-center gap-2 text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-300 mb-6 transition-colors"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
        </svg>
        返回上一级
      </button>

      <!-- 加载状态 -->
      <div v-if="loading" class="text-center py-16">
        <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 dark:border-indigo-400"></div>
        <p class="mt-4 text-lg text-gray-500 dark:text-gray-400">加载演员数据中...</p>
      </div>

      <!-- 错误信息 -->
      <div v-else-if="error" class="text-center py-16 bg-white dark:bg-gray-800 rounded-xl">
        <svg class="mx-auto h-16 w-16 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <p class="mt-4 text-lg text-gray-500 dark:text-gray-400">{{ error }}</p>
        <button 
          @click="fetchActorData"
          class="mt-4 inline-block px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
        >
          重试
        </button>
      </div>

      <!-- 演员数据 -->
      <div v-else-if="actor">
        <!-- Actor Basic Information -->
        <div class="p-4 mb-8">
          <div class="flex items-center gap-6">
            <!-- Avatar -->
            <div class="w-24 h-24 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white text-3xl font-bold shadow-lg overflow-hidden">
              <img 
                :src="`${API_BASE_URL}/data/actor_cover/${actor.id}.webp`" 
                :alt="actor.name" 
                class="w-full h-full object-cover"
              />
            </div>
            
            <!-- Basic Info -->
            <div>
              <h1 class="text-xl font-bold text-gray-900 dark:text-white mb-2">{{ actor.name }}</h1>
              <div class="flex items-center gap-3 justify-between">
                <span class="px-3 py-1 text-sm font-semibold rounded-full bg-indigo-100 text-indigo-800 dark:bg-indigo-900/50 dark:text-indigo-300">
                  {{ actor.category }}
                </span>
                <!-- Edit Button -->
                <button 
                  @click="editActor"
                  class="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors flex items-center gap-2"
                  >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                </button>
                <!-- Scan Button -->
                <button 
                  @click="scanActor"
                  :disabled="scanning"
                  class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-green-400 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                >
                  <svg v-if="!scanning" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                  <svg v-else class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  <span>{{ scanning ? '扫描中...' : '扫描' }}</span>
                </button>
              </div>
            </div>

          <!-- 描述内容：强制长串字符换行，防止 URL 溢出 -->
          <p class="text-base text-gray-900 dark:text-white font-medium break-all">{{ actor.description }}</p>
        </div>

        <!-- Tab Navigation -->
        <div class="mb-6">
          <div class="flex gap-2 bg-gray-200 dark:bg-gray-700 p-1 rounded-lg">
            <button
              @click="activeTab = 'media'"
              :class="[
                'flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all',
                activeTab === 'media'
                  ? 'bg-white dark:bg-gray-600 text-indigo-600 dark:text-indigo-400 shadow-sm'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
              ]"
            >
              媒体
            </button>
            <button
              @click="activeTab = 'Messages'"
              :class="[
                'flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all',
                activeTab === 'Messages'
                  ? 'bg-white dark:bg-gray-600 text-indigo-600 dark:text-indigo-400 shadow-sm'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
              ]"
            >
              组合
            </button>
          </div>
        </div>

        <!-- Media Tab Content -->
        <div v-show="activeTab === 'media'">
          <div v-if="actorMedia.length > 0" class="grid grid-cols-2 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-10 gap-2">
            <MediaCard
              v-for="media in actorMedia"
              :key="media.id"
              :media="media"
              @click="goToMedia"
            />
          </div>

          <div v-else class="text-center py-16 rounded-xl">
            <svg class="mx-auto h-16 w-16 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z" />
            </svg>
            <p class="mt-4 text-lg text-gray-500 dark:text-gray-400">该演员暂无媒体作品</p>
          </div>
        </div>

        <!-- Messages Tab Content -->
        <div v-show="activeTab === 'Messages'">
          <div v-if="actorMessages.length > 0" class="grid gap-2"
               :class="actor?.category === 'AV' ? 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4' : 'grid-cols-2 md:grid-cols-4 lg:grid-cols-8 xl:grid-cols-10'">
            <MessageCard
              v-for="message in actorMessages" 
              :key="message.id"
              :message="message"
              @click="goToGroup"
            />
          </div>

          <div v-else class="text-center py-16 rounded-xl">
            <svg class="mx-auto h-16 w-16 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
            <p class="mt-4 text-lg text-gray-500 dark:text-gray-400">该演员暂未加入任何分组</p>
          </div>
        </div>
      </div>

      <!-- Actor Not Found -->
      <div v-else class="text-center py-16">
        <svg class="mx-auto h-16 w-16 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <p class="mt-4 text-lg text-gray-500 dark:text-gray-400">未找到该演员信息</p>
        <router-link 
          to="/actor" 
          class="mt-4 inline-block px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
        >
          返回演员列表
        </router-link>
      </div>
    </div>

    <!-- Edit Modal -->
    <ActorEditModal
      :is-open="showEditModal"
      title="编辑演员信息"
      :form-data="formData"
      @close="closeEditModal"
      @save="saveActor"
    />

    <!-- Toast Container -->
    <Teleport to="body">
      <div class="fixed top-4 right-4 z-50 flex flex-col gap-2 max-w-md">
        <TransitionGroup name="toast">
          <div
            v-for="toast in toasts"
            :key="toast.id"
            :class="[
              'px-4 py-3 rounded-lg shadow-lg flex items-start gap-3 cursor-pointer transition-all',
              toast.type === 'success' ? 'bg-green-500 text-white' : '',
              toast.type === 'error' ? 'bg-red-500 text-white' : '',
              toast.type === 'info' ? 'bg-blue-500 text-white' : ''
            ]"
            @click="removeToast(toast.id)"
          >
            <!-- Icon -->
            <svg v-if="toast.type === 'success'" class="w-5 h-5 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
            <svg v-else-if="toast.type === 'error'" class="w-5 h-5 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
            <svg v-else class="w-5 h-5 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <!-- Message -->
            <span class="text-sm font-medium">{{ toast.message }}</span>
          </div>
        </TransitionGroup>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onActivated } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTheme } from '../composables/useTheme'
import ActorEditModal from '../components/ActorEditModal.vue'
import MediaCard from '../components/MediaCard.vue'
import MessageCard from '../components/MessageCard.vue'
import { API_BASE_URL } from '../utils/constants'

// 本地类型定义 - 匹配后端 schemas
interface Actor {
  id: number
  name: string
  description: string
  usage: number
  avatar: string
  avatar_path: string | null
}

interface ActorDetail extends Actor {
  Messages: message[]
  media: Media[]
}

interface message {
  id: number
  name: string
  description: string | null
  cover_image: string | null
  serial_number: string | null
  release_date: string | null
  rating: number | null
  actor_id: number
  size: number
  media_cnt: number
  created_at: string
  updated_at: string
}

interface Media {
  id: number
  name: string
  type: 'VIDEO' | 'IMAGE'
  thumbnail_path: string | null
  duration: number | null
  rating: number | null
}

interface ToastMessage {
  id: number
  type: 'success' | 'error' | 'info'
  message: string
}

interface ScanResult {
  success: boolean
  message: string
  folders_found: number
  groups_created: number
  media_added: number
  media_skipped: number
  media_failed: number
}

const route = useRoute()
const router = useRouter()
const { initTheme } = useTheme()

const showEditModal = ref(false)
const activeTab = ref<'media' | 'Messages'>('media')
const formData = ref({
  name: '',
  description: '',
  category: '默认',
  avatar: '',
  download_status: '未下载'
})

const actorId = computed(() => parseInt(route.params.id as string))
const currentId = ref<number | null>(null)

const loading = ref(false)
const error = ref('')
const actor = ref<Actor | null>(null)
const actorMessages = ref<message[]>([])
const actorMedia = ref<Media[]>([])
const scanning = ref(false)

// Toast 相关
const toasts = ref<ToastMessage[]>([])
let toastId = 0

const showToast = (type: ToastMessage['type'], message: string, duration = 4000) => {
  const id = ++toastId
  toasts.value.push({ id, type, message })
  setTimeout(() => {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }, duration)
}

const removeToast = (id: number) => {
  toasts.value = toasts.value.filter(t => t.id !== id)
}

// 从后端API获取演员详情数据（包含groups和media）
const fetchActorData = async () => {
  loading.value = true
  error.value = ''
  try {
    const response = await fetch(`${API_BASE_URL}/api/actor/${actorId.value}/detail`)
    if (!response.ok) {
      throw new Error('获取演员数据失败')
    }
    const data: ActorDetail = await response.json()
    actor.value = data
    actorMessages.value = data.Messages || []
    actorMedia.value = data.media || []
  } catch (err) {
    error.value = err instanceof Error ? err.message : '发生未知错误'
    console.error('获取演员数据时出错:', err)
  } finally {
    loading.value = false
  }
}

const goToGroup = (groupId: number) => {
  router.push(`/message/${groupId}`)
}

const goToMedia = (mediaId: number) => {
  router.push(`/media/${mediaId}`)
}

const editActor = () => {
  if (actor.value) {
    formData.value = {
      name: actor.value.name,
      description: actor.value.description,
      avatar: actor.value.avatar,
    }
    showEditModal.value = true
  }
}

// 扫描演员文件夹
const scanActor = async () => {
  if (!actor.value || scanning.value) return
  
  scanning.value = true
  try {
    const response = await fetch(`${API_BASE_URL}/api/actor/${actorId.value}/scan`, {
      method: 'POST'
    })
    
    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || '扫描失败')
    }
    
    const result: ScanResult = await response.json()
    
    // 显示扫描结果
    showToast(
      'success',
      `扫描完成！文件夹: ${result.folders_found} | 创建分组: ${result.groups_created} | 添加: ${result.media_added} | 跳过: ${result.media_skipped} | 失败: ${result.media_failed}`,
      6000
    )
    fetchActorData()
    
  } catch (err) {
    const message = err instanceof Error ? err.message : '扫描时发生未知错误'
    showToast('error', `扫描失败: ${message}`)
    console.error('扫描演员文件夹时出错:', err)
  } finally {
    scanning.value = false
  }
}

// 保存演员数据到后端API
const saveActor = async (data: typeof formData.value) => {
  if (actor.value) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/actor/${actorId.value}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      })
      
      if (!response.ok) {
        throw new Error('保存演员数据失败')
      }
      
      // 更新本地数据
      const updatedActor = await response.json()
      actor.value = updatedActor
      closeEditModal()
    } catch (err) {
      error.value = err instanceof Error ? err.message : '发生未知错误'
      console.error('保存演员数据时出错:', err)
    }
  }
}

const closeEditModal = () => {
  showEditModal.value = false
}

defineOptions({
  name: 'ActorDetail'
})

onMounted(() => {
  initTheme()
  fetchActorData()
  // 更新当前的actor id
  currentId.value = actorId.value
})

// 当组件从缓存中激活时，检查actorId是否变化
onActivated(() => {
  console.log('ActorDetail activated, currentId:', currentId.value, 'actorId:', actorId.value)
  if (actorId.value !== currentId.value) {
    fetchActorData()
    currentId.value = actorId.value
  }
})
</script>

<style scoped>
/* Toast 过渡动画 */
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(100%);
}

.toast-move {
  transition: transform 0.3s ease;
}
</style>
