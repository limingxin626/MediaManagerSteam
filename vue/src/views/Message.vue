<template>
  <div class="min-h-screen transition-colors">
    <!-- Main Content -->
    <div class="w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 pb-24">
      <div class="mb-6">
        <div class="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
          <h2 class="text-3xl font-bold text-gray-900 dark:text-white">消息流</h2>
          <!-- Search -->
          <div class="relative flex-1 max-w-md">
            <input 
              v-model="searchQuery"
              type="text" 
              placeholder="搜索消息..." 
              class="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
            <svg class="absolute left-3 top-2.5 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>

          <div class="flex items-center gap-3">
            <!-- View Toggle -->
            <ViewToggle v-model="currentView" />
          </div>
        </div>
      </div>
      
      <!-- Messages Feed View -->
      <div v-if="filteredMessages.length > 0" class="flex flex-col gap-4 max-w-2xl mx-auto" ref="messagesContainer">
        <MessageCard
          v-for="message in filteredMessages" 
          :key="message.id"
          :message="message"
          :media-items="messageMediaMap[message.id]"
          @click="goToMessage"
        />
        <!-- 加载更多指示器 -->
        <div v-if="loading" class="col-span-full text-center py-8">
          <div class="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-indigo-500"></div>
          <p class="mt-2 text-sm text-gray-600 dark:text-gray-400">加载中...</p>
        </div>
        <!-- 没有更多数据提示 -->
        <div v-if="!loading && !hasMoreData" class="col-span-full text-center py-8">
          <p class="text-sm text-gray-500 dark:text-gray-400">已经到底了</p>
        </div>
      </div>

      <!-- Empty State -->
      <div v-if="filteredMessages.length === 0 && !loading" class="text-center py-12">
        <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
        <h3 class="mt-2 text-sm font-medium text-gray-900 dark:text-white">暂无消息</h3>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">还没有任何消息内容</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useTheme } from '../composables/useTheme'
import { type Message, type MessageDetail } from '../types'
import MessageCard from '../components/MessageCard.vue'
import ViewToggle from '../components/ViewToggle.vue'
import type { ViewMode } from '../components/ViewToggle.vue'
import { API_BASE_URL } from '../utils/constants'

defineOptions({
  name: 'Message'
})

const router = useRouter()
const { initTheme } = useTheme()

const messages = ref<Message[]>([])
const messageMediaMap = ref<Record<number, any[]>>({})
const loading = ref(false)
const searchQuery = ref('')
const currentView = ref<ViewMode>('grid')

const pageSize = ref(20)
const hasMoreData = ref(true)
const messagesContainer = ref<HTMLElement | null>(null)
const nextCursor = ref<string | null>(null)

const filteredMessages = computed(() => {
  const query = searchQuery.value.toLowerCase()
  if (!query) return messages.value
  return messages.value.filter(message => {
    const text = message.text || ''
    const actorName = message.actor_name || ''
    return text.toLowerCase().includes(query) ||
      actorName.toLowerCase().includes(query)
  })
})

const fetchMessages = async (isLoadingMore = false) => {
  if (loading.value || !hasMoreData.value) return
  
  loading.value = true
  try {
    let url = `${API_BASE_URL}/messages/with-detail?limit=${pageSize.value}`
    if (nextCursor.value) {
      url += `&cursor=${encodeURIComponent(nextCursor.value)}`
    }
    
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error('Failed to fetch messages')
    }
    const data = await response.json()
    
    hasMoreData.value = data.has_more
    nextCursor.value = data.next_cursor
    
    const previousScrollY = window.scrollY
    const previousHeight = document.body.scrollHeight
    
    if (isLoadingMore) {
      messages.value = [...data.items.reverse(), ...messages.value]
    } else {
      messages.value = data.items.reverse()
    }
    
    for (const message of data.items) {
      if (message.media_items) {
        messageMediaMap.value[message.id] = message.media_items
      }
    }
    
    if (!isLoadingMore) {
      setTimeout(() => {
        window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' })
      }, 100)
    } else {
      setTimeout(() => {
        const newHeight = document.body.scrollHeight
        const scrollDelta = newHeight - previousHeight
        window.scrollTo({ top: previousScrollY + scrollDelta, behavior: 'auto' })
      }, 100)
    }
  } catch (error) {
    console.error('Error fetching messages:', error)
    alert('获取消息数据失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const goToMessage = (messageId: number) => {
  router.push(`/message/${messageId}`)
}

// 记录上一次滚动位置
const lastScrollTop = ref(0)

// 节流函数
const throttle = (func: Function, delay: number) => {
  let lastCall = 0
  return function(...args: any[]) {
    const now = Date.now()
    if (now - lastCall < delay) {
      return
    }
    lastCall = now
    func.apply(this, args)
  }
}

const handleScroll = throttle(() => {
  const windowScrollTop = window.scrollY
  
  const isNearTop = windowScrollTop <= window.innerHeight * 2
  const isScrollingUp = windowScrollTop < lastScrollTop.value
  
  if (isNearTop && isScrollingUp && !loading.value && hasMoreData.value) {
    fetchMessages(true)
  }
  
  lastScrollTop.value = windowScrollTop
}, 300)

onMounted(() => {
  initTheme()
  fetchMessages()
  
  // 添加滚动事件监听
  if (messagesContainer.value) {
    messagesContainer.value.addEventListener('scroll', handleScroll)
  }
  // 也监听窗口滚动，以防容器本身不滚动
  window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  // 移除滚动事件监听
  if (messagesContainer.value) {
    messagesContainer.value.removeEventListener('scroll', handleScroll)
  }
  window.removeEventListener('scroll', handleScroll)
})

</script>